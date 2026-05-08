from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/prompt-versions", response_model=schemas.PromptVersionRead)
def create_prompt_version(payload: schemas.PromptVersionCreate, db: Session = Depends(get_db)):
    return crud.create_prompt_version(db, payload)


@router.get("/prompt-versions", response_model=list[schemas.PromptVersionRead])
def list_prompt_versions(
    status: str = Query("default"),
    db: Session = Depends(get_db),
):
    if status != "default" and status not in schemas.LIST_STATUS_FILTER_VALUES:
        raise HTTPException(status_code=400, detail="invalid status filter")
    return crud.list_prompt_versions_by_status(db, status)


@router.get("/prompt-versions/{prompt_version_id}", response_model=schemas.PromptVersionRead)
def get_prompt_version(prompt_version_id: int, db: Session = Depends(get_db)):
    row = crud.get_prompt_version(db, prompt_version_id)
    if not row:
        raise HTTPException(status_code=404, detail="prompt version not found")
    return row


@router.put("/prompt-versions/{prompt_version_id}", response_model=schemas.PromptVersionRead)
def update_prompt_version(
    prompt_version_id: int,
    payload: schemas.PromptVersionUpdate,
    db: Session = Depends(get_db),
):
    row = crud.get_prompt_version(db, prompt_version_id)
    if not row:
        raise HTTPException(status_code=404, detail="prompt version not found")
    return crud.update_prompt_version(db, row, payload)


@router.put("/prompt-versions/{prompt_version_id}/status", response_model=schemas.PromptVersionRead)
def update_prompt_version_status(
    prompt_version_id: int,
    payload: schemas.StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    row = crud.get_prompt_version(db, prompt_version_id)
    if not row:
        raise HTTPException(status_code=404, detail="prompt version not found")
    return crud.update_prompt_version_status(db, row, payload.status)


@router.delete("/prompt-versions/{prompt_version_id}", response_model=schemas.PromptVersionRead)
def soft_delete_prompt_version(prompt_version_id: int, db: Session = Depends(get_db)):
    row = crud.get_prompt_version(db, prompt_version_id)
    if not row:
        raise HTTPException(status_code=404, detail="prompt version not found")
    return crud.update_prompt_version_status(db, row, "deleted")
