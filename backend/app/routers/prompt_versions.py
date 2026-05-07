from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/prompt-versions", response_model=schemas.PromptVersionRead)
def create_prompt_version(payload: schemas.PromptVersionCreate, db: Session = Depends(get_db)):
    return crud.create_prompt_version(db, payload)


@router.get("/prompt-versions", response_model=list[schemas.PromptVersionRead])
def list_prompt_versions(db: Session = Depends(get_db)):
    return crud.list_prompt_versions(db)


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
