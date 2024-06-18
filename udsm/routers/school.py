from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine
from ..unit import create_unit

router=APIRouter(tags=['School'])


@router.post("/schools/")
def create_inst(school: schemas.CollegeCreate, db: Session = Depends(get_db)):
    new_school = models.School(**school.model_dump())
    db.add(school)
    db.commit()
    create_unit(db,school)
    db.refresh(new_school)
    return new_school

@router.get("/schools/{school_id}")
def retrieve_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail=f"Unit with id {school_id} not found")
    return school

@router.get("/schools/")
def retrieve_school(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    schools=db.query(models.School).offset(skip).limit(limit).all()
    if schools is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unit found")
    return schools

@router.put("/schools/{school_id}")
def update_inst(school_id: int, unit: schemas.UnitCreate, db: Session = Depends(get_db)):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    for key, value in unit.model_dump().items():
        setattr(school, key, value)
    db.commit()
    db.refresh(school)
    return school

@router.delete("/schools/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if school is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(school)
    db.commit()
    return {"message": "Unit deleted successfully"}
