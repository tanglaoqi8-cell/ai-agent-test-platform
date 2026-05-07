from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/model-configs", response_model=schemas.ModelConfigRead)
def create_model_config(payload: schemas.ModelConfigCreate, db: Session = Depends(get_db)):
    return crud.create_model_config(db, payload)


@router.get("/model-configs", response_model=list[schemas.ModelConfigRead])
def list_model_configs(db: Session = Depends(get_db)):
    return crud.list_model_configs(db)


@router.get("/model-configs/{model_config_id}", response_model=schemas.ModelConfigRead)
def get_model_config(model_config_id: int, db: Session = Depends(get_db)):
    row = crud.get_model_config(db, model_config_id)
    if not row:
        raise HTTPException(status_code=404, detail="model config not found")
    return row


@router.put("/model-configs/{model_config_id}", response_model=schemas.ModelConfigRead)
def update_model_config(
    model_config_id: int,
    payload: schemas.ModelConfigUpdate,
    db: Session = Depends(get_db),
):
    row = crud.get_model_config(db, model_config_id)
    if not row:
        raise HTTPException(status_code=404, detail="model config not found")
    return crud.update_model_config(db, row, payload)
