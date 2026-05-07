from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/test-cases/upload", response_model=schemas.TestCaseUploadResponse)
async def upload_test_cases(
    file: UploadFile = File(...),
    suite_name: str = Form(default="Uploaded Test Suite"),
    description: str = Form(default="Uploaded from CSV"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV file is supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    try:
        cases = schemas.parse_csv_cases(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not suite_name.strip():
        suite_name = f"Test Suite {datetime.now().strftime('%Y%m%d%H%M%S')}"

    suite = crud.create_test_suite(db, suite_name.strip(), description, len(cases))
    crud.create_test_cases(db, suite.id, cases)

    return schemas.TestCaseUploadResponse(suite_id=suite.id, case_count=len(cases))


@router.get("/test-suites", response_model=list[schemas.TestSuiteRead])
def list_test_suites(db: Session = Depends(get_db)):
    return crud.list_test_suites(db)


@router.get("/test-suites/{suite_id}/cases", response_model=list[schemas.TestCaseRead])
def list_suite_cases(suite_id: int, db: Session = Depends(get_db)):
    suite = crud.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="test_suite not found")
    return crud.list_suite_cases(db, suite_id)
