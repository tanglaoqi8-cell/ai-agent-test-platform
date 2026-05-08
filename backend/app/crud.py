import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_test_target(db: Session, payload: schemas.TestTargetCreate) -> models.TestTarget:
    obj = models.TestTarget(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_test_targets(db: Session) -> list[models.TestTarget]:
    return db.query(models.TestTarget).order_by(models.TestTarget.id.desc()).all()


def get_test_target(db: Session, target_id: int) -> Optional[models.TestTarget]:
    return db.query(models.TestTarget).filter(models.TestTarget.id == target_id).first()


def create_test_suite(db: Session, name: str, description: Optional[str], case_count: int) -> models.TestSuite:
    obj = models.TestSuite(name=name, description=description, case_count=case_count)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_test_cases(db: Session, suite_id: int, cases: list[schemas.ParsedCsvCase]) -> None:
    db_cases = [
        models.TestCase(
            suite_id=suite_id,
            case_id=case.case_id,
            case_name=case.case_name,
            input_text=case.input_text,
            assert_type=case.assert_type,
            expected_value=case.expected_value,
        )
        for case in cases
    ]
    db.add_all(db_cases)
    db.commit()


def list_test_suites(db: Session) -> list[models.TestSuite]:
    return db.query(models.TestSuite).order_by(models.TestSuite.id.desc()).all()


def list_suite_cases(db: Session, suite_id: int) -> list[models.TestCase]:
    return (
        db.query(models.TestCase)
        .filter(models.TestCase.suite_id == suite_id)
        .order_by(models.TestCase.id.asc())
        .all()
    )


def get_test_suite(db: Session, suite_id: int) -> Optional[models.TestSuite]:
    return db.query(models.TestSuite).filter(models.TestSuite.id == suite_id).first()


def create_test_run(
    db: Session,
    target_id: int,
    suite_id: int,
    status: str,
    total: int,
    passed: int,
    failed: int,
) -> models.TestRun:
    obj = models.TestRun(
        target_id=target_id,
        suite_id=suite_id,
        status=status,
        total=total,
        passed=passed,
        failed=failed,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_test_results(db: Session, results: list[models.TestResult]) -> None:
    db.add_all(results)
    db.commit()


def list_test_runs(db: Session) -> list[models.TestRun]:
    return db.query(models.TestRun).order_by(models.TestRun.id.desc()).all()


def list_run_results(db: Session, run_id: int) -> list[models.TestResult]:
    return (
        db.query(models.TestResult)
        .filter(models.TestResult.run_id == run_id)
        .order_by(models.TestResult.id.asc())
        .all()
    )


def create_prompt_version(db: Session, payload: schemas.PromptVersionCreate) -> models.PromptVersion:
    obj = models.PromptVersion(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_prompt_versions(db: Session) -> list[models.PromptVersion]:
    return db.query(models.PromptVersion).order_by(models.PromptVersion.id.desc()).all()


def list_prompt_versions_by_status(db: Session, status_filter: str) -> list[models.PromptVersion]:
    query = db.query(models.PromptVersion)
    if status_filter == "all":
        return query.order_by(models.PromptVersion.id.desc()).all()
    if status_filter in {"active", "inactive", "deleted"}:
        return query.filter(models.PromptVersion.status == status_filter).order_by(models.PromptVersion.id.desc()).all()
    return (
        query.filter(models.PromptVersion.status.in_(["active", "inactive"]))
        .order_by(models.PromptVersion.id.desc())
        .all()
    )


def get_prompt_version(db: Session, prompt_version_id: int) -> Optional[models.PromptVersion]:
    return db.query(models.PromptVersion).filter(models.PromptVersion.id == prompt_version_id).first()


def update_prompt_version(
    db: Session,
    prompt_version: models.PromptVersion,
    payload: schemas.PromptVersionUpdate,
) -> models.PromptVersion:
    prompt_version.prompt_name = payload.prompt_name
    prompt_version.version = payload.version
    prompt_version.prompt_content = payload.prompt_content
    prompt_version.is_baseline = payload.is_baseline
    prompt_version.baseline_version_id = payload.baseline_version_id
    prompt_version.status = payload.status
    prompt_version.remark = payload.remark
    prompt_version.updated_at = datetime.utcnow()

    db.add(prompt_version)
    db.commit()
    db.refresh(prompt_version)
    return prompt_version


def update_prompt_version_status(
    db: Session,
    prompt_version: models.PromptVersion,
    status: str,
) -> models.PromptVersion:
    prompt_version.status = status
    prompt_version.updated_at = datetime.utcnow()
    db.add(prompt_version)
    db.commit()
    db.refresh(prompt_version)
    return prompt_version


def create_model_config(db: Session, payload: schemas.ModelConfigCreate) -> models.ModelConfig:
    obj = models.ModelConfig(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_model_configs(db: Session) -> list[models.ModelConfig]:
    return db.query(models.ModelConfig).order_by(models.ModelConfig.id.desc()).all()


def list_model_configs_by_status(db: Session, status_filter: str) -> list[models.ModelConfig]:
    query = db.query(models.ModelConfig)
    if status_filter == "all":
        return query.order_by(models.ModelConfig.id.desc()).all()
    if status_filter in {"active", "inactive", "deleted"}:
        return query.filter(models.ModelConfig.status == status_filter).order_by(models.ModelConfig.id.desc()).all()
    return (
        query.filter(models.ModelConfig.status.in_(["active", "inactive"]))
        .order_by(models.ModelConfig.id.desc())
        .all()
    )


def get_model_config(db: Session, model_config_id: int) -> Optional[models.ModelConfig]:
    return db.query(models.ModelConfig).filter(models.ModelConfig.id == model_config_id).first()


def update_model_config(
    db: Session,
    model_config: models.ModelConfig,
    payload: schemas.ModelConfigUpdate,
) -> models.ModelConfig:
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(model_config, key, value)

    model_config.updated_at = datetime.utcnow()
    db.add(model_config)
    db.commit()
    db.refresh(model_config)
    return model_config


def update_model_config_status(
    db: Session,
    model_config: models.ModelConfig,
    status: str,
) -> models.ModelConfig:
    model_config.status = status
    model_config.updated_at = datetime.utcnow()
    db.add(model_config)
    db.commit()
    db.refresh(model_config)
    return model_config


def create_prompt_test_run(
    db: Session,
    prompt_version_id: int,
    model_config_id: int,
    input_text: str,
    prompt_content_snapshot: str,
    model_config_snapshot: str,
    status: str,
    repeat_count: int = 1,
) -> models.PromptTestRun:
    obj = models.PromptTestRun(
        prompt_version_id=prompt_version_id,
        model_config_id=model_config_id,
        input_text=input_text,
        prompt_content_snapshot=prompt_content_snapshot,
        model_config_snapshot=model_config_snapshot,
        repeat_count=repeat_count,
        status=status,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_prompt_test_run(
    db: Session,
    run: models.PromptTestRun,
    status: str,
    duration_ms: int,
    error_message: Optional[str],
) -> models.PromptTestRun:
    run.status = status
    run.duration_ms = duration_ms
    run.finished_at = datetime.utcnow()
    run.error_message = error_message
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def create_prompt_test_result(
    db: Session,
    run_id: int,
    actual_output: str,
    raw_response: Optional[str],
    error_message: Optional[str],
    duration_ms: int,
    repeat_index: int = 1,
) -> models.PromptTestResult:
    obj = models.PromptTestResult(
        run_id=run_id,
        repeat_index=repeat_index,
        actual_output=actual_output,
        raw_response=raw_response,
        error_message=error_message,
        duration_ms=duration_ms,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_prompt_test_run(db: Session, run_id: int) -> Optional[models.PromptTestRun]:
    return db.query(models.PromptTestRun).filter(models.PromptTestRun.id == run_id).first()


def list_prompt_test_runs(db: Session) -> list[models.PromptTestRun]:
    return db.query(models.PromptTestRun).order_by(models.PromptTestRun.id.desc()).all()


def get_prompt_test_result_by_run_id(db: Session, run_id: int) -> Optional[models.PromptTestResult]:
    return (
        db.query(models.PromptTestResult)
        .filter(models.PromptTestResult.run_id == run_id)
        .order_by(models.PromptTestResult.id.asc())
        .first()
    )


def list_prompt_test_results_by_run_id(db: Session, run_id: int) -> list[models.PromptTestResult]:
    return (
        db.query(models.PromptTestResult)
        .filter(models.PromptTestResult.run_id == run_id)
        .order_by(models.PromptTestResult.repeat_index.asc(), models.PromptTestResult.id.asc())
        .all()
    )


def create_prompt_test_assertion_result(
    db: Session,
    run_id: int,
    result_id: int,
    assert_type: Optional[str],
    expected_value: Optional[str],
    assertion_status: str,
    assertion_passed: Optional[bool],
    assertion_reason: str,
) -> models.PromptTestAssertionResult:
    obj = models.PromptTestAssertionResult(
        run_id=run_id,
        result_id=result_id,
        assert_type=assert_type,
        expected_value=expected_value,
        assertion_status=assertion_status,
        assertion_passed=assertion_passed,
        assertion_reason=assertion_reason,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_prompt_test_assertion_by_run_id(db: Session, run_id: int) -> Optional[models.PromptTestAssertionResult]:
    return (
        db.query(models.PromptTestAssertionResult)
        .filter(models.PromptTestAssertionResult.run_id == run_id)
        .order_by(models.PromptTestAssertionResult.id.asc())
        .first()
    )


def list_prompt_test_assertions_by_run_id(db: Session, run_id: int) -> list[models.PromptTestAssertionResult]:
    return (
        db.query(models.PromptTestAssertionResult)
        .filter(models.PromptTestAssertionResult.run_id == run_id)
        .order_by(models.PromptTestAssertionResult.id.asc())
        .all()
    )



def create_prompt_test_input_snapshot(
    db: Session,
    run_id: int,
    input_text: Optional[str],
    input_variables_json: Optional[str],
    rendered_prompt: str,
) -> models.PromptTestInputSnapshot:
    obj = models.PromptTestInputSnapshot(
        run_id=run_id,
        input_text=input_text,
        input_variables_json=input_variables_json,
        rendered_prompt=rendered_prompt,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_prompt_test_input_snapshot_by_run_id(db: Session, run_id: int) -> Optional[models.PromptTestInputSnapshot]:
    return (
        db.query(models.PromptTestInputSnapshot)
        .filter(models.PromptTestInputSnapshot.run_id == run_id)
        .order_by(models.PromptTestInputSnapshot.id.asc())
        .first()
    )


def parse_input_variables_json(input_variables_json: Optional[str]) -> Optional[dict]:
    if not input_variables_json:
        return None
    try:
        parsed = json.loads(input_variables_json)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def create_prompt_score_result(
    db: Session,
    run_id: int,
    result_id: int,
    scorer_model_config_id: int,
    scoring_template_id: str,
    expected_behavior: Optional[str],
    dimension_scores_json: Optional[str],
    total_score: Optional[float],
    score_reason: Optional[str],
    problem_points_json: Optional[str],
    suggestion: Optional[str],
    raw_response: Optional[str],
    status: str,
    error_message: Optional[str],
    duration_ms: int,
    remark: Optional[str],
) -> models.PromptScoreResult:
    obj = models.PromptScoreResult(
        run_id=run_id,
        result_id=result_id,
        scorer_model_config_id=scorer_model_config_id,
        scoring_template_id=scoring_template_id,
        expected_behavior=expected_behavior,
        dimension_scores_json=dimension_scores_json,
        total_score=total_score,
        score_reason=score_reason,
        problem_points_json=problem_points_json,
        suggestion=suggestion,
        raw_response=raw_response,
        status=status,
        error_message=error_message,
        duration_ms=duration_ms,
        remark=remark,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_prompt_scores_by_run_id(db: Session, run_id: int) -> list[models.PromptScoreResult]:
    return (
        db.query(models.PromptScoreResult)
        .filter(models.PromptScoreResult.run_id == run_id)
        .order_by(models.PromptScoreResult.id.desc())
        .all()
    )


def get_latest_prompt_score_by_run_id(db: Session, run_id: int) -> Optional[models.PromptScoreResult]:
    return (
        db.query(models.PromptScoreResult)
        .filter(models.PromptScoreResult.run_id == run_id)
        .order_by(models.PromptScoreResult.id.desc())
        .first()
    )


def parse_json_dict(json_text: Optional[str]) -> Optional[dict]:
    if not json_text:
        return None
    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def parse_json_list(json_text: Optional[str]) -> Optional[list]:
    if not json_text:
        return None
    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        return None
    return None


def create_prompt_manual_review(
    db: Session,
    run_id: int,
    result_id: int,
    manual_status: str,
    manual_remark: Optional[str],
    reviewer: Optional[str],
) -> models.PromptManualReview:
    obj = models.PromptManualReview(
        run_id=run_id,
        result_id=result_id,
        manual_status=manual_status,
        manual_remark=manual_remark,
        reviewer=reviewer,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_prompt_manual_reviews_by_run_id(db: Session, run_id: int) -> list[models.PromptManualReview]:
    return (
        db.query(models.PromptManualReview)
        .filter(models.PromptManualReview.run_id == run_id)
        .order_by(models.PromptManualReview.id.desc())
        .all()
    )


def get_latest_prompt_manual_review_by_run_id(db: Session, run_id: int) -> Optional[models.PromptManualReview]:
    return (
        db.query(models.PromptManualReview)
        .filter(models.PromptManualReview.run_id == run_id)
        .order_by(models.PromptManualReview.id.desc())
        .first()
    )

