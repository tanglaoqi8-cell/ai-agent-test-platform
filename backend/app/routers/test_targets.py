from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/test-targets", response_model=schemas.TestTargetRead)
def create_test_target(payload: schemas.TestTargetCreate, db: Session = Depends(get_db)):
    obj = crud.create_test_target(db, payload)
    return obj


@router.get("/test-targets", response_model=list[schemas.TestTargetRead])
def get_test_targets(db: Session = Depends(get_db)):
    return crud.list_test_targets(db)


@router.get("/test-targets/{target_id}", response_model=schemas.TestTargetRead)
def get_test_target(target_id: int, db: Session = Depends(get_db)):
    obj = crud.get_test_target(db, target_id)
    if not obj:
        raise HTTPException(status_code=404, detail="test_target not found")
    return obj
