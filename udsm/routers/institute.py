from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine
from ..unit import create_unit

router=APIRouter(tags=['Institute'])


@router.post("/institutes/")
def create_inst(inst: schemas.CollegeCreate, db: Session = Depends(get_db)):
    new_inst = models.Institute(**inst.model_dump())
    db.add(new_inst)
    db.commit()
    create_unit(db,new_inst)
    db.refresh(new_inst)
    return new_inst

@router.get("/institutes/{inst_id}")
def retrieve_inst(inst_id: int, db: Session = Depends(get_db)):
    inst = db.query(models.Institute).filter(models.Institute.id == inst_id).first()
    if inst is None:
        raise HTTPException(status_code=404, detail=f"Unit with id {inst_id} not found")
    return inst

@router.get("/institutes/")
def retrieve_insts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    insts=db.query(models.Institute).offset(skip).limit(limit).all()
    if insts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unit found")
    return insts

@router.put("/institutes/{inst_id}")
def update_inst(inst_id: int, unit: schemas.UnitCreate, db: Session = Depends(get_db)):
    inst = db.query(models.Institute).filter(models.Institute.id == inst_id).first()
    if inst is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    for key, value in unit.model_dump().items():
        setattr(inst, key, value)
    db.commit()
    db.refresh(inst)
    return inst

@router.delete("/institutes/{inst_id}")
def delete_inst(inst_id: int, db: Session = Depends(get_db)):
    inst = db.query(models.Institute).filter(models.Institute.id == inst_id).first()
    if inst is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(inst)
    db.commit()
    return {"message": "Unit deleted successfully"}
