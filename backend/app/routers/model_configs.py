from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.post("/model-configs", response_model=schemas.ModelConfigRead)
def create_model_config(payload: schemas.ModelConfigCreate, db: Session = Depends(get_db)):
    return crud.create_model_config(db, payload)


@router.get("/model-configs", response_model=list[schemas.ModelConfigRead])
def list_model_configs(
    status: str = Query("default"),
    db: Session = Depends(get_db),
):
    if status != "default" and status not in schemas.LIST_STATUS_FILTER_VALUES:
        raise HTTPException(status_code=400, detail="invalid status filter")
    return crud.list_model_configs_by_status(db, status)


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


@router.put("/model-configs/{model_config_id}/status", response_model=schemas.ModelConfigRead)
def update_model_config_status(
    model_config_id: int,
    payload: schemas.StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    row = crud.get_model_config(db, model_config_id)
    if not row:
        raise HTTPException(status_code=404, detail="model config not found")
    return crud.update_model_config_status(db, row, payload.status)


@router.delete("/model-configs/{model_config_id}", response_model=schemas.ModelConfigRead)
def soft_delete_model_config(model_config_id: int, db: Session = Depends(get_db)):
    row = crud.get_model_config(db, model_config_id)
    if not row:
        raise HTTPException(status_code=404, detail="model config not found")
    return crud.update_model_config_status(db, row, "deleted")
