import csv
import io
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..services.assertions import run_assertion
from ..services.runner import run_target

router = APIRouter()


@router.post("/test-runs", response_model=schemas.TestRunCreateResponse)
def create_test_run(payload: schemas.TestRunCreate, db: Session = Depends(get_db)):
    target = crud.get_test_target(db, payload.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="test_target not found")

    suite = crud.get_test_suite(db, payload.suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="test_suite not found")

    cases = crud.list_suite_cases(db, payload.suite_id)
    if not cases:
        raise HTTPException(status_code=400, detail="test_suite has no test_cases")

    result_rows: list[models.TestResult] = []
    passed = 0

    for case in cases:
        start = time.perf_counter()
        actual_output = run_target(target, case.input_text)

        if actual_output.startswith("HTTP_ERROR:"):
            ok = False
            reason = actual_output
        else:
            ok, reason = run_assertion(case.assert_type, case.expected_value, actual_output)

        latency_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            passed += 1

        result_rows.append(
            models.TestResult(
                run_id=0,
                case_id=case.case_id,
                case_name=case.case_name,
                input_text=case.input_text,
                actual_output=actual_output,
                assert_type=case.assert_type,
                expected_value=case.expected_value,
                passed=ok,
                reason=reason,
                latency_ms=latency_ms,
            )
        )

    total = len(result_rows)
    failed = total - passed
    status = "completed"
    run = crud.create_test_run(db, payload.target_id, payload.suite_id, status, total, passed, failed)

    for row in result_rows:
        row.run_id = run.id
    crud.create_test_results(db, result_rows)

    return schemas.TestRunCreateResponse(run_id=run.id, total=total, passed=passed, failed=failed)


@router.get("/test-runs", response_model=list[schemas.TestRunRead])
def list_test_runs(db: Session = Depends(get_db)):
    return crud.list_test_runs(db)


@router.get("/test-runs/{run_id}/results", response_model=list[schemas.TestResultRead])
def list_test_run_results(run_id: int, db: Session = Depends(get_db)):
    rows = crud.list_run_results(db, run_id)
    if not rows:
        raise HTTPException(status_code=404, detail="test_results not found for run_id")
    return rows


@router.get("/test-runs/{run_id}/export-csv")
def export_test_run_csv(run_id: int, db: Session = Depends(get_db)):
    run = db.query(models.TestRun).filter(models.TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="test run not found")

    rows = crud.list_run_results(db, run_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "run_id",
            "case_id",
            "case_name",
            "input_text",
            "actual_output",
            "assert_type",
            "expected_value",
            "passed",
            "reason",
            "latency_ms",
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row.run_id,
                row.case_id,
                row.case_name,
                row.input_text,
                row.actual_output,
                row.assert_type,
                row.expected_value,
                "通过" if row.passed else "失败",
                row.reason,
                row.latency_ms,
            ]
        )

    csv_bytes = buffer.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": 'attachment; filename="test_run_{0}_results.csv"'.format(run_id)
        },
    )
