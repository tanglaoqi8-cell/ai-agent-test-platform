import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..services.assertion_evaluator import evaluate_assertion
from ..services.llm_scorer import score_prompt_run
from ..services.prompt_executor import execute_prompt_once
from ..services.prompt_renderer import render_prompt

router = APIRouter()
SUPPORTED_ASSERT_TYPES = {"contains", "regex", "json_valid"}
REPEAT_COUNT_MIN = 1
REPEAT_COUNT_MAX = 5
SUPPORTED_MANUAL_STATUS = {"passed", "failed", "pending"}
FAILURE_SUMMARY_MAX_ITEMS = 5
SUMMARY_TEXT_LIMIT = 200


def _build_model_config_snapshot(model_config):
    snapshot = {
        "id": model_config.id,
        "config_name": model_config.config_name,
        "provider": model_config.provider,
        "base_url": model_config.base_url,
        "model": model_config.model,
        "temperature": model_config.temperature,
        "top_p": model_config.top_p,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "status": model_config.status,
        "remark": model_config.remark,
    }
    return json.dumps(snapshot, ensure_ascii=False)


def _to_score_read(row):
    if not row:
        return None
    raw_response = row.raw_response if row.status == "failed" else None
    return schemas.PromptScoreRead(
        id=row.id,
        run_id=row.run_id,
        result_id=row.result_id,
        scorer_model_config_id=row.scorer_model_config_id,
        scoring_template_id=row.scoring_template_id,
        expected_behavior=row.expected_behavior,
        dimension_scores=crud.parse_json_dict(row.dimension_scores_json),
        total_score=row.total_score,
        score_reason=row.score_reason,
        problem_points=crud.parse_json_list(row.problem_points_json),
        suggestion=row.suggestion,
        raw_response=raw_response,
        status=row.status,
        error_message=row.error_message,
        duration_ms=row.duration_ms,
        remark=row.remark,
        created_at=row.created_at,
    )


def _to_assertion_read(row):
    if not row:
        return None
    return schemas.PromptAssertionRead(
        assert_type=row.assert_type,
        expected_value=row.expected_value,
        assertion_status=row.assertion_status,
        assertion_passed=row.assertion_passed,
        assertion_reason=row.assertion_reason,
    )


def _build_repeat_results_and_summary(result_rows, assertion_rows):
    assertion_by_result_id = {}
    for assertion_row in assertion_rows:
        assertion_by_result_id[assertion_row.result_id] = assertion_row

    items = []
    success_count = 0
    failed_count = 0
    assertion_passed_count = 0
    assertion_failed_count = 0
    assertion_skipped_count = 0

    for row in result_rows:
        item_status = "success" if not row.error_message else "failed"
        if item_status == "success":
            success_count += 1
        else:
            failed_count += 1

        assertion_row = assertion_by_result_id.get(row.id)
        assertion = _to_assertion_read(assertion_row)
        if assertion is not None:
            if assertion.assertion_status == "passed":
                assertion_passed_count += 1
            elif assertion.assertion_status == "failed":
                assertion_failed_count += 1
            elif assertion.assertion_status == "skipped":
                assertion_skipped_count += 1

        items.append(
            schemas.PromptRepeatResultItem(
                result_id=row.id,
                repeat_index=row.repeat_index,
                status=item_status,
                actual_output=row.actual_output,
                duration_ms=row.duration_ms,
                error_message=row.error_message,
                assertion=assertion,
            )
        )

    summary = schemas.PromptRunRepeatSummary(
        total=len(result_rows),
        success_count=success_count,
        failed_count=failed_count,
        assertion_passed_count=assertion_passed_count,
        assertion_failed_count=assertion_failed_count,
        assertion_skipped_count=assertion_skipped_count,
    )
    return items, summary


def _truncate_text(text, limit):
    if text is None:
        return ""
    text_str = str(text)
    if len(text_str) <= limit:
        return text_str
    return text_str[:limit] + "..."


def _build_manual_check_suggestion(run, failed_count, assertion_failed_count, latest_score, latest_manual_review):
    reasons = []
    if failed_count > 0:
        reasons.append("存在执行失败结果")
    if assertion_failed_count > 0:
        reasons.append("存在断言失败结果")
    if latest_score is None:
        reasons.append("当前 run 尚未进行 LLM 评分")
    if latest_manual_review is None:
        reasons.append("当前 run 尚未进行人工复核")
    if run.status != "success":
        reasons.append("当前 run 状态不是 success")
    return schemas.PromptManualCheckSuggestion(need_manual_check=len(reasons) > 0, reasons=reasons)


@router.post("/prompt-test-runs/run-once", response_model=schemas.PromptRunOnceResponse)
def run_prompt_once(payload: schemas.PromptRunOnceRequest, db: Session = Depends(get_db)):
    if not payload.input_text and payload.input_variables is None:
        raise HTTPException(status_code=400, detail="input_text or input_variables is required")
    if payload.input_variables is not None and not isinstance(payload.input_variables, dict):
        raise HTTPException(status_code=400, detail="input_variables must be an object")

    if payload.assert_type is not None:
        if payload.assert_type not in SUPPORTED_ASSERT_TYPES:
            raise HTTPException(status_code=400, detail="unsupported assert_type")
        if payload.assert_type in {"contains", "regex"} and not payload.expected_value:
            raise HTTPException(status_code=400, detail="expected_value is required for contains/regex")

    prompt_version = crud.get_prompt_version(db, payload.prompt_version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="prompt version not found")

    model_config = crud.get_model_config(db, payload.model_config_id)
    if not model_config:
        raise HTTPException(status_code=404, detail="model config not found")

    render_result = render_prompt(
        prompt_content=prompt_version.prompt_content,
        input_text=payload.input_text,
        input_variables=payload.input_variables,
    )
    if render_result["missing_variables"]:
        raise HTTPException(
            status_code=400,
            detail="missing prompt variables: {0}".format(", ".join(render_result["missing_variables"])),
        )

    run = crud.create_prompt_test_run(
        db=db,
        prompt_version_id=prompt_version.id,
        model_config_id=model_config.id,
        input_text=payload.input_text or "",
        prompt_content_snapshot=prompt_version.prompt_content,
        model_config_snapshot=_build_model_config_snapshot(model_config),
        status="running",
    )

    input_snapshot_row = crud.create_prompt_test_input_snapshot(
        db=db,
        run_id=run.id,
        input_text=payload.input_text,
        input_variables_json=render_result["input_variables_json"],
        rendered_prompt=render_result["rendered_prompt"],
    )

    exec_result = execute_prompt_once(
        rendered_prompt=render_result["rendered_prompt"],
        user_input_text=render_result["user_message_text"],
        model_config=model_config,
    )

    run = crud.update_prompt_test_run(
        db=db,
        run=run,
        status=exec_result["status"],
        duration_ms=exec_result["duration_ms"],
        error_message=exec_result["error_message"],
    )

    result = crud.create_prompt_test_result(
        db=db,
        run_id=run.id,
        actual_output=exec_result["actual_output"],
        raw_response=exec_result["raw_response"],
        error_message=exec_result["error_message"],
        duration_ms=exec_result["duration_ms"],
    )

    assertion_row = None
    if payload.assert_type is not None:
        if run.status != "success":
            assertion_row = crud.create_prompt_test_assertion_result(
                db=db,
                run_id=run.id,
                result_id=result.id,
                assert_type=payload.assert_type,
                expected_value=payload.expected_value,
                assertion_status="skipped",
                assertion_passed=None,
                assertion_reason="model execution failed, assertion skipped",
            )
        else:
            eval_result = evaluate_assertion(
                assert_type=payload.assert_type,
                expected_value=payload.expected_value or "",
                actual_output=result.actual_output,
            )
            assertion_row = crud.create_prompt_test_assertion_result(
                db=db,
                run_id=run.id,
                result_id=result.id,
                assert_type=payload.assert_type,
                expected_value=payload.expected_value,
                assertion_status=eval_result["assertion_status"],
                assertion_passed=eval_result["assertion_passed"],
                assertion_reason=eval_result["assertion_reason"],
            )

    return schemas.PromptRunOnceResponse(
        run_id=run.id,
        result_id=result.id,
        status=run.status,
        prompt_version_id=run.prompt_version_id,
        model_config_id=run.model_config_id,
        actual_output=result.actual_output,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        assertion=assertion_row,
        input_snapshot=schemas.PromptInputSnapshotRead(
            input_text=input_snapshot_row.input_text,
            input_variables=crud.parse_input_variables_json(input_snapshot_row.input_variables_json),
            rendered_prompt=input_snapshot_row.rendered_prompt,
        ),
    )


@router.post("/prompt-test-runs/run-repeat", response_model=schemas.PromptRunRepeatResponse)
def run_prompt_repeat(payload: schemas.PromptRunRepeatRequest, db: Session = Depends(get_db)):
    if payload.repeat_count < REPEAT_COUNT_MIN or payload.repeat_count > REPEAT_COUNT_MAX:
        raise HTTPException(status_code=400, detail="repeat_count must be between 1 and 5")
    if not payload.input_text and payload.input_variables is None:
        raise HTTPException(status_code=400, detail="input_text or input_variables is required")
    if payload.input_variables is not None and not isinstance(payload.input_variables, dict):
        raise HTTPException(status_code=400, detail="input_variables must be an object")

    if payload.assert_type is not None:
        if payload.assert_type not in SUPPORTED_ASSERT_TYPES:
            raise HTTPException(status_code=400, detail="unsupported assert_type")
        if payload.assert_type in {"contains", "regex"} and not payload.expected_value:
            raise HTTPException(status_code=400, detail="expected_value is required for contains/regex")

    prompt_version = crud.get_prompt_version(db, payload.prompt_version_id)
    if not prompt_version:
        raise HTTPException(status_code=404, detail="prompt version not found")

    model_config = crud.get_model_config(db, payload.model_config_id)
    if not model_config:
        raise HTTPException(status_code=404, detail="model config not found")

    render_result = render_prompt(
        prompt_content=prompt_version.prompt_content,
        input_text=payload.input_text,
        input_variables=payload.input_variables,
    )
    if render_result["missing_variables"]:
        raise HTTPException(
            status_code=400,
            detail="missing prompt variables: {0}".format(", ".join(render_result["missing_variables"])),
        )

    run = crud.create_prompt_test_run(
        db=db,
        prompt_version_id=prompt_version.id,
        model_config_id=model_config.id,
        input_text=payload.input_text or "",
        prompt_content_snapshot=prompt_version.prompt_content,
        model_config_snapshot=_build_model_config_snapshot(model_config),
        status="running",
        repeat_count=payload.repeat_count,
    )

    input_snapshot_row = crud.create_prompt_test_input_snapshot(
        db=db,
        run_id=run.id,
        input_text=payload.input_text,
        input_variables_json=render_result["input_variables_json"],
        rendered_prompt=render_result["rendered_prompt"],
    )

    result_rows = []
    assertion_rows = []
    total_duration_ms = 0

    for idx in range(1, payload.repeat_count + 1):
        exec_result = execute_prompt_once(
            rendered_prompt=render_result["rendered_prompt"],
            user_input_text=render_result["user_message_text"],
            model_config=model_config,
        )

        total_duration_ms += exec_result["duration_ms"]
        result_row = crud.create_prompt_test_result(
            db=db,
            run_id=run.id,
            actual_output=exec_result["actual_output"],
            raw_response=exec_result["raw_response"],
            error_message=exec_result["error_message"],
            duration_ms=exec_result["duration_ms"],
            repeat_index=idx,
        )
        result_rows.append(result_row)

        if payload.assert_type is not None:
            if exec_result["status"] != "success":
                assertion_row = crud.create_prompt_test_assertion_result(
                    db=db,
                    run_id=run.id,
                    result_id=result_row.id,
                    assert_type=payload.assert_type,
                    expected_value=payload.expected_value,
                    assertion_status="skipped",
                    assertion_passed=None,
                    assertion_reason="model execution failed, assertion skipped",
                )
            else:
                eval_result = evaluate_assertion(
                    assert_type=payload.assert_type,
                    expected_value=payload.expected_value or "",
                    actual_output=result_row.actual_output,
                )
                assertion_row = crud.create_prompt_test_assertion_result(
                    db=db,
                    run_id=run.id,
                    result_id=result_row.id,
                    assert_type=payload.assert_type,
                    expected_value=payload.expected_value,
                    assertion_status=eval_result["assertion_status"],
                    assertion_passed=eval_result["assertion_passed"],
                    assertion_reason=eval_result["assertion_reason"],
                )
            assertion_rows.append(assertion_row)

    success_count = len([row for row in result_rows if not row.error_message])
    if success_count == len(result_rows):
        run_status = "success"
        run_error_message = None
    elif success_count == 0:
        run_status = "failed"
        run_error_message = "all repeats failed"
    else:
        run_status = "partial_success"
        run_error_message = "partial repeats failed"

    run = crud.update_prompt_test_run(
        db=db,
        run=run,
        status=run_status,
        duration_ms=total_duration_ms,
        error_message=run_error_message,
    )

    results_response, summary = _build_repeat_results_and_summary(result_rows, assertion_rows)
    return schemas.PromptRunRepeatResponse(
        run_id=run.id,
        status=run.status,
        prompt_version_id=run.prompt_version_id,
        model_config_id=run.model_config_id,
        repeat_count=run.repeat_count,
        summary=summary,
        results=results_response,
        input_snapshot=schemas.PromptInputSnapshotRead(
            input_text=input_snapshot_row.input_text,
            input_variables=crud.parse_input_variables_json(input_snapshot_row.input_variables_json),
            rendered_prompt=input_snapshot_row.rendered_prompt,
        ),
    )


@router.post("/prompt-test-runs/{run_id}/score", response_model=schemas.PromptScoreRead)
def score_prompt_test_run(run_id: int, payload: schemas.PromptScoreRequest, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    result = crud.get_prompt_test_result_by_run_id(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="prompt test result not found")

    scorer_model = crud.get_model_config(db, payload.scorer_model_config_id)
    if not scorer_model:
        raise HTTPException(status_code=404, detail="model config not found")

    input_snapshot = crud.get_prompt_test_input_snapshot_by_run_id(db, run_id)
    assertion = crud.get_prompt_test_assertion_by_run_id(db, run_id)

    score_context = {
        "input_text": run.input_text,
        "input_variables": crud.parse_input_variables_json(input_snapshot.input_variables_json) if input_snapshot else None,
        "rendered_prompt": input_snapshot.rendered_prompt if input_snapshot else run.prompt_content_snapshot,
        "actual_output": result.actual_output,
        "expected_behavior": payload.expected_behavior,
        "assertion": {
            "assert_type": assertion.assert_type,
            "expected_value": assertion.expected_value,
            "assertion_status": assertion.assertion_status,
            "assertion_passed": assertion.assertion_passed,
            "assertion_reason": assertion.assertion_reason,
        }
        if assertion
        else None,
    }

    score_result = score_prompt_run(scorer_model, score_context)

    score_row = crud.create_prompt_score_result(
        db=db,
        run_id=run.id,
        result_id=result.id,
        scorer_model_config_id=payload.scorer_model_config_id,
        scoring_template_id=score_result["scoring_template_id"],
        expected_behavior=payload.expected_behavior,
        dimension_scores_json=json.dumps(score_result["dimension_scores"], ensure_ascii=False)
        if score_result["dimension_scores"] is not None
        else None,
        total_score=score_result["total_score"],
        score_reason=score_result["score_reason"],
        problem_points_json=json.dumps(score_result["problem_points"], ensure_ascii=False)
        if score_result["problem_points"] is not None
        else None,
        suggestion=score_result["suggestion"],
        raw_response=score_result["raw_response"],
        status=score_result["status"],
        error_message=score_result["error_message"],
        duration_ms=score_result["duration_ms"],
        remark=payload.remark,
    )

    return _to_score_read(score_row)


@router.get("/prompt-test-runs/{run_id}/scores", response_model=list[schemas.PromptScoreRead])
def list_prompt_test_run_scores(run_id: int, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    rows = crud.list_prompt_scores_by_run_id(db, run_id)
    return [_to_score_read(row) for row in rows]


@router.post("/prompt-test-runs/{run_id}/manual-review", response_model=schemas.PromptManualReviewRead)
def create_prompt_manual_review(run_id: int, payload: schemas.PromptManualReviewRequest, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    result = crud.get_prompt_test_result_by_run_id(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="prompt test result not found")

    if payload.manual_status not in SUPPORTED_MANUAL_STATUS:
        raise HTTPException(status_code=400, detail="unsupported manual_status")

    row = crud.create_prompt_manual_review(
        db=db,
        run_id=run.id,
        result_id=result.id,
        manual_status=payload.manual_status,
        manual_remark=payload.manual_remark,
        reviewer=payload.reviewer,
    )
    return row


@router.get("/prompt-test-runs/{run_id}/manual-reviews", response_model=list[schemas.PromptManualReviewRead])
def list_prompt_manual_reviews(run_id: int, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")
    return crud.list_prompt_manual_reviews_by_run_id(db, run_id)


@router.get("/prompt-test-runs", response_model=list[schemas.PromptTestRunRead])
def list_prompt_test_runs(db: Session = Depends(get_db)):
    return crud.list_prompt_test_runs(db)


@router.get("/prompt-test-runs/{run_id}", response_model=schemas.PromptTestRunDetailResponse)
def get_prompt_test_run(run_id: int, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    result = crud.get_prompt_test_result_by_run_id(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    assertion = crud.get_prompt_test_assertion_by_run_id(db, run_id)
    assertions = crud.list_prompt_test_assertions_by_run_id(db, run_id)
    input_snapshot = crud.get_prompt_test_input_snapshot_by_run_id(db, run_id)
    latest_score = crud.get_latest_prompt_score_by_run_id(db, run_id)
    latest_manual_review = crud.get_latest_prompt_manual_review_by_run_id(db, run_id)
    results = crud.list_prompt_test_results_by_run_id(db, run_id)
    result_rows_for_detail = results if results else [result]
    repeat_results, _ = _build_repeat_results_and_summary(result_rows_for_detail, assertions)
    input_snapshot_response = None
    if input_snapshot:
        input_snapshot_response = schemas.PromptInputSnapshotRead(
            input_text=input_snapshot.input_text,
            input_variables=crud.parse_input_variables_json(input_snapshot.input_variables_json),
            rendered_prompt=input_snapshot.rendered_prompt,
        )

    return schemas.PromptTestRunDetailResponse(
        run=run,
        result=result,
        results=repeat_results,
        assertion=assertion,
        input_snapshot=input_snapshot_response,
        latest_score=_to_score_read(latest_score),
        latest_manual_review=latest_manual_review,
    )


def _build_prompt_run_markdown_report(summary: schemas.PromptTestRunSummaryResponse) -> str:
    lines = []
    lines.append("# Prompt 测试执行报告")
    lines.append("")
    lines.append("## 1. 执行基本信息")
    lines.append("")
    lines.append("- Run ID: {0}".format(summary.run_id))
    lines.append("- 执行状态: {0}".format(summary.status))
    lines.append("- Prompt Version ID: {0}".format(summary.prompt_version_id))
    lines.append("- Model Config ID: {0}".format(summary.model_config_id))
    lines.append("- 开始时间: {0}".format(summary.run_info.started_at))
    lines.append("- 结束时间: {0}".format(summary.run_info.finished_at))
    lines.append("- 总耗时(ms): {0}".format(summary.run_info.duration_ms))
    lines.append("")

    lines.append("## 2. Prompt 版本信息")
    lines.append("")
    if summary.prompt_version:
        pv = summary.prompt_version
        lines.append("- Prompt 名称: {0}".format(pv.prompt_name))
        lines.append("- 版本号: {0}".format(pv.version))
        lines.append("- 是否基线版本: {0}".format(pv.is_baseline))
        lines.append("- 基线版本 ID: {0}".format(pv.baseline_version_id))
        lines.append("- 状态: {0}".format(pv.status))
    else:
        lines.append("- 暂无 Prompt 版本信息")
    lines.append("")

    lines.append("## 3. 模型配置信息")
    lines.append("")
    if summary.model_config_info:
        mc = summary.model_config_info
        lines.append("- 配置名称: {0}".format(mc.config_name))
        lines.append("- provider: {0}".format(mc.provider))
        lines.append("- base_url: {0}".format(mc.base_url))
        lines.append("- model: {0}".format(mc.model))
        lines.append("- temperature: {0}".format(mc.temperature))
        lines.append("- top_p: {0}".format(mc.top_p))
        lines.append("- max_tokens: {0}".format(mc.max_tokens))
        lines.append("- 状态: {0}".format(mc.status))
    else:
        lines.append("- 暂无模型配置信息")
    lines.append("")

    lines.append("## 4. 输入信息摘要")
    lines.append("")
    if summary.input_snapshot:
        input_variables_json = ""
        if summary.input_snapshot.input_variables is not None:
            input_variables_json = json.dumps(summary.input_snapshot.input_variables, ensure_ascii=False)
        rendered_prompt = summary.input_snapshot.rendered_prompt or ""
        rendered_prompt_limited = rendered_prompt
        if len(rendered_prompt) > 500:
            rendered_prompt_limited = rendered_prompt[:500] + "...（内容已截断）"

        lines.append("- input_text: {0}".format(summary.input_snapshot.input_text))
        lines.append("- input_variables_json: {0}".format(input_variables_json))
        lines.append("- rendered_prompt 摘要:")
        lines.append("")
        lines.append("```text")
        lines.append(rendered_prompt_limited)
        lines.append("```")
    else:
        lines.append("- 暂无输入快照")
    lines.append("")

    lines.append("## 5. 执行结果摘要")
    lines.append("")
    rs = summary.result_summary
    lines.append("- 总执行次数: {0}".format(rs.total))
    lines.append("- 成功次数: {0}".format(rs.success_count))
    lines.append("- 失败次数: {0}".format(rs.failed_count))
    lines.append("- 成功率: {0:.2%}".format(rs.success_rate))
    lines.append("- 断言通过数: {0}".format(rs.assertion_passed_count))
    lines.append("- 断言失败数: {0}".format(rs.assertion_failed_count))
    lines.append("- 断言跳过数: {0}".format(rs.assertion_skipped_count))
    lines.append("- 断言通过率: {0:.2%}".format(rs.assertion_pass_rate))
    lines.append("")

    lines.append("## 6. LLM 自动评分")
    lines.append("")
    if summary.latest_score:
        score = summary.latest_score
        dims = score.dimension_scores or {}
        lines.append("- total_score: {0}".format(score.total_score))
        lines.append("- relevance_score: {0}".format(dims.get("relevance")))
        lines.append("- completeness_score: {0}".format(dims.get("completeness")))
        lines.append("- format_correctness_score: {0}".format(dims.get("format_correctness")))
        lines.append("- constraint_following_score: {0}".format(dims.get("constraint_following")))
        lines.append("- stability_usability_score: {0}".format(dims.get("stability_usability")))
        lines.append("- score_reason: {0}".format(score.score_reason))
        lines.append(
            "- problem_points: {0}".format(
                json.dumps(score.problem_points, ensure_ascii=False) if score.problem_points is not None else "[]"
            )
        )
        lines.append("- suggestion: {0}".format(score.suggestion))
    else:
        lines.append("- 暂无 LLM 自动评分")
    lines.append("")

    lines.append("## 7. 人工复核")
    lines.append("")
    if summary.latest_manual_review:
        mr = summary.latest_manual_review
        lines.append("- manual_status: {0}".format(mr.manual_status))
        lines.append("- manual_remark: {0}".format(mr.manual_remark))
        lines.append("- reviewer: {0}".format(mr.reviewer))
        lines.append("- created_at: {0}".format(mr.created_at))
    else:
        lines.append("- 暂无人工复核记录")
    lines.append("")

    lines.append("## 8. 建议人工确认项")
    lines.append("")
    mcs = summary.manual_check_suggestion
    lines.append("- 是否建议人工确认: {0}".format(mcs.need_manual_check))
    if mcs.reasons:
        lines.append("- 原因列表:")
        for reason in mcs.reasons:
            lines.append("  - {0}".format(reason))
    else:
        lines.append("- 原因列表: 无")
    lines.append("")

    lines.append("## 9. 失败摘要")
    lines.append("")
    if summary.failure_summary:
        for idx, item in enumerate(summary.failure_summary, start=1):
            lines.append("### 失败项 {0}".format(idx))
            lines.append("- result_id: {0}".format(item.result_id))
            lines.append("- repeat_index: {0}".format(item.repeat_index))
            lines.append("- status: {0}".format(item.status))
            lines.append("- assertion_status: {0}".format(item.assertion_status))
            lines.append("- reason_summary: {0}".format(item.reason_summary))
            lines.append("- actual_output_summary: {0}".format(item.actual_output_summary))
            lines.append("")
    else:
        lines.append("- 暂无失败摘要")
        lines.append("")

    return "\n".join(lines)


@router.get("/prompt-test-runs/{run_id}/summary", response_model=schemas.PromptTestRunSummaryResponse)
def get_prompt_test_run_summary(run_id: int, db: Session = Depends(get_db)):
    run = crud.get_prompt_test_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="prompt test run not found")

    prompt_version = crud.get_prompt_version(db, run.prompt_version_id)
    model_config = crud.get_model_config(db, run.model_config_id)
    input_snapshot = crud.get_prompt_test_input_snapshot_by_run_id(db, run_id)
    latest_score = crud.get_latest_prompt_score_by_run_id(db, run_id)
    latest_manual_review = crud.get_latest_prompt_manual_review_by_run_id(db, run_id)
    results = crud.list_prompt_test_results_by_run_id(db, run_id)
    assertions = crud.list_prompt_test_assertions_by_run_id(db, run_id)

    assertion_by_result_id = {}
    for assertion_row in assertions:
        assertion_by_result_id[assertion_row.result_id] = assertion_row

    total = len(results)
    success_count = 0
    failed_count = 0
    assertion_passed_count = 0
    assertion_failed_count = 0
    assertion_skipped_count = 0
    failure_summary_items = []

    for row in results:
        result_status = "success" if not row.error_message else "failed"
        if result_status == "success":
            success_count += 1
        else:
            failed_count += 1

        assertion_row = assertion_by_result_id.get(row.id)
        assertion_status = assertion_row.assertion_status if assertion_row else None
        if assertion_status == "passed":
            assertion_passed_count += 1
        elif assertion_status == "failed":
            assertion_failed_count += 1
        elif assertion_status == "skipped":
            assertion_skipped_count += 1

        has_failure = (result_status != "success") or (assertion_status in {"failed", "skipped"})
        if has_failure and len(failure_summary_items) < FAILURE_SUMMARY_MAX_ITEMS:
            reason_parts = []
            if row.error_message:
                reason_parts.append(row.error_message)
            if assertion_row and assertion_row.assertion_reason:
                reason_parts.append(assertion_row.assertion_reason)
            if not reason_parts:
                reason_parts.append("execution or assertion not passed")

            failure_summary_items.append(
                schemas.PromptFailureSummaryItem(
                    result_id=row.id,
                    repeat_index=row.repeat_index,
                    status=result_status,
                    assertion_status=assertion_status,
                    reason_summary=_truncate_text(" | ".join(reason_parts), SUMMARY_TEXT_LIMIT),
                    actual_output_summary=_truncate_text(row.actual_output, SUMMARY_TEXT_LIMIT),
                )
            )

    assertion_total = assertion_passed_count + assertion_failed_count + assertion_skipped_count
    success_rate = float(success_count) / float(total) if total > 0 else 0.0
    assertion_pass_rate = float(assertion_passed_count) / float(assertion_total) if assertion_total > 0 else 0.0

    input_snapshot_response = None
    if input_snapshot:
        input_snapshot_response = schemas.PromptInputSnapshotRead(
            input_text=input_snapshot.input_text,
            input_variables=crud.parse_input_variables_json(input_snapshot.input_variables_json),
            rendered_prompt=input_snapshot.rendered_prompt,
        )

    prompt_version_summary = None
    if prompt_version:
        prompt_version_summary = schemas.PromptVersionSummary(
            id=prompt_version.id,
            prompt_name=prompt_version.prompt_name,
            version=prompt_version.version,
            is_baseline=prompt_version.is_baseline,
            baseline_version_id=prompt_version.baseline_version_id,
            status=prompt_version.status,
        )

    model_config_summary = None
    if model_config:
        model_config_summary = schemas.ModelConfigSummary(
            id=model_config.id,
            config_name=model_config.config_name,
            provider=model_config.provider,
            base_url=model_config.base_url,
            model=model_config.model,
            temperature=model_config.temperature,
            top_p=model_config.top_p,
            max_tokens=model_config.max_tokens,
            is_default=model_config.is_default,
            status=model_config.status,
        )

    return schemas.PromptTestRunSummaryResponse(
        run_id=run.id,
        status=run.status,
        prompt_version_id=run.prompt_version_id,
        model_config_id=run.model_config_id,
        run_info=schemas.PromptRunInfoSummary(
            id=run.id,
            status=run.status,
            prompt_version_id=run.prompt_version_id,
            model_config_id=run.model_config_id,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
            error_message=run.error_message,
        ),
        prompt_version=prompt_version_summary,
        model_config_info=model_config_summary,
        input_snapshot=input_snapshot_response,
        result_summary=schemas.PromptResultSummary(
            total=total,
            success_count=success_count,
            failed_count=failed_count,
            assertion_passed_count=assertion_passed_count,
            assertion_failed_count=assertion_failed_count,
            assertion_skipped_count=assertion_skipped_count,
            success_rate=success_rate,
            assertion_pass_rate=assertion_pass_rate,
        ),
        latest_score=_to_score_read(latest_score),
        latest_manual_review=latest_manual_review,
        manual_check_suggestion=_build_manual_check_suggestion(
            run=run,
            failed_count=failed_count,
            assertion_failed_count=assertion_failed_count,
            latest_score=latest_score,
            latest_manual_review=latest_manual_review,
        ),
        failure_summary=failure_summary_items,
    )


@router.get("/prompt-test-runs/{run_id}/report-markdown", response_class=PlainTextResponse)
def get_prompt_test_run_report_markdown(run_id: int, db: Session = Depends(get_db)):
    summary = get_prompt_test_run_summary(run_id=run_id, db=db)
    report_markdown = _build_prompt_run_markdown_report(summary)
    return PlainTextResponse(content=report_markdown, media_type="text/markdown; charset=utf-8")


@router.get("/prompt-test-runs/{run_id}/compare", response_model=schemas.PromptRunCompareResponse)
def compare_prompt_test_runs(run_id: int, baseline_run_id: int, db: Session = Depends(get_db)):
    if run_id == baseline_run_id:
        raise HTTPException(status_code=400, detail="run_id and baseline_run_id cannot be the same")

    current_summary = get_prompt_test_run_summary(run_id=run_id, db=db)
    baseline_summary = get_prompt_test_run_summary(run_id=baseline_run_id, db=db)

    success_rate_diff = current_summary.result_summary.success_rate - baseline_summary.result_summary.success_rate
    assertion_pass_rate_diff = (
        current_summary.result_summary.assertion_pass_rate - baseline_summary.result_summary.assertion_pass_rate
    )

    current_score = (
        current_summary.latest_score.total_score
        if current_summary.latest_score is not None and current_summary.latest_score.total_score is not None
        else None
    )
    baseline_score = (
        baseline_summary.latest_score.total_score
        if baseline_summary.latest_score is not None and baseline_summary.latest_score.total_score is not None
        else None
    )
    total_score_diff = None
    if current_score is not None and baseline_score is not None:
        total_score_diff = current_score - baseline_score

    comparison_reasons = []
    has_missing_critical_data = False
    if current_summary.result_summary.total == 0:
        comparison_reasons.append("当前 run 没有执行结果")
        has_missing_critical_data = True
    if baseline_summary.result_summary.total == 0:
        comparison_reasons.append("基线 run 没有执行结果")
        has_missing_critical_data = True
    if current_score is None:
        comparison_reasons.append("当前 run 缺少 LLM 评分")
        has_missing_critical_data = True
    if baseline_score is None:
        comparison_reasons.append("基线 run 缺少 LLM 评分")
        has_missing_critical_data = True

    if has_missing_critical_data:
        comparison_result = "need_manual_check"
    else:
        all_ge = (
            current_summary.result_summary.success_rate >= baseline_summary.result_summary.success_rate
            and current_summary.result_summary.assertion_pass_rate >= baseline_summary.result_summary.assertion_pass_rate
            and (current_score is not None and baseline_score is not None and current_score >= baseline_score)
        )
        any_gt = (
            current_summary.result_summary.success_rate > baseline_summary.result_summary.success_rate
            or current_summary.result_summary.assertion_pass_rate > baseline_summary.result_summary.assertion_pass_rate
            or (current_score is not None and baseline_score is not None and current_score > baseline_score)
        )
        any_lt = (
            current_summary.result_summary.success_rate < baseline_summary.result_summary.success_rate
            or current_summary.result_summary.assertion_pass_rate < baseline_summary.result_summary.assertion_pass_rate
            or (current_score is not None and baseline_score is not None and current_score < baseline_score)
        )
        if all_ge and any_gt:
            comparison_result = "better"
        elif any_lt:
            comparison_result = "worse"
        else:
            comparison_result = "equal"

    manual_check_reasons = []
    if comparison_result == "need_manual_check":
        manual_check_reasons.append("对比结果需要人工确认")
    if current_score is None:
        manual_check_reasons.append("当前 run 缺少 LLM 评分")
    if baseline_score is None:
        manual_check_reasons.append("基线 run 缺少 LLM 评分")
    if current_summary.latest_manual_review is None:
        manual_check_reasons.append("当前 run 缺少人工复核")
    if baseline_summary.latest_manual_review is None:
        manual_check_reasons.append("基线 run 缺少人工复核")
    if current_summary.result_summary.failed_count > 0:
        manual_check_reasons.append("当前 run 存在执行失败")
    if baseline_summary.result_summary.failed_count > 0:
        manual_check_reasons.append("基线 run 存在执行失败")
    if current_summary.result_summary.assertion_failed_count > 0:
        manual_check_reasons.append("当前 run 存在断言失败")
    if baseline_summary.result_summary.assertion_failed_count > 0:
        manual_check_reasons.append("基线 run 存在断言失败")
    if current_summary.model_config_id != baseline_summary.model_config_id:
        manual_check_reasons.append("当前 run 与基线 run 的模型配置不同")
    if current_summary.result_summary.total != baseline_summary.result_summary.total:
        manual_check_reasons.append("当前 run 与基线 run 的执行次数不一致")

    baseline_relation_matched = None
    current_prompt_version = current_summary.prompt_version
    if current_prompt_version is None or current_prompt_version.baseline_version_id is None:
        manual_check_reasons.append("当前 PromptVersion 未配置 baseline_version_id")
    else:
        baseline_relation_matched = baseline_summary.prompt_version_id == current_prompt_version.baseline_version_id
        if not baseline_relation_matched:
            manual_check_reasons.append("baseline_run_id 与当前 PromptVersion 的 baseline_version_id 不一致")

    # 去重并保持顺序
    dedup_reasons = []
    reason_set = set()
    for reason in manual_check_reasons:
        if reason not in reason_set:
            dedup_reasons.append(reason)
            reason_set.add(reason)

    return schemas.PromptRunCompareResponse(
        current_run_id=run_id,
        baseline_run_id=baseline_run_id,
        current_summary=current_summary,
        baseline_summary=baseline_summary,
        comparison=schemas.PromptRunComparison(
            success_rate_diff=success_rate_diff,
            assertion_pass_rate_diff=assertion_pass_rate_diff,
            total_score_diff=total_score_diff,
            result=comparison_result,
            reasons=comparison_reasons,
        ),
        manual_check_suggestion=schemas.PromptManualCheckSuggestion(
            need_manual_check=len(dedup_reasons) > 0,
            reasons=dedup_reasons,
        ),
        baseline_relation_matched=baseline_relation_matched,
    )
