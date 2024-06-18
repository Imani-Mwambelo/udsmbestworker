from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine
from ..unit import create_unit

router=APIRouter(tags=['College'])


@router.post("/colleges/")
def create_college(college: schemas.CollegeCreate, db: Session = Depends(get_db)):
    new_college = models.College(**college.model_dump())
    db.add(new_college)
    db.commit()
    create_unit(db,new_college)
    db.refresh(new_college)
    return new_college

@router.get("/colleges/{college_id}")
def retrieve_college(college_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(models.College).filter(models.College.id == college_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail=f"Unit with id {college_id} not found")
    return db_unit

@router.get("/colleges/")
def retrieve_all_colleges(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    colleges=db.query(models.College).offset(skip).limit(limit).all()
    if colleges is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No unit found")
    return colleges

@router.put("/colleges/{college_id}")
def update_college(college_id: int, unit: schemas.UnitCreate, db: Session = Depends(get_db)):
    college = db.query(models.College).filter(models.College.id == college_id).first()
    if college is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    for key, value in unit.model_dump().items():
        setattr(college, key, value)
    db.commit()
    db.refresh(college)
    return college

@router.delete("/colleges/{college_id}")
def delete_college(college_id: int, db: Session = Depends(get_db)):
    college = db.query(models.College).filter(models.College.id == college_id).first()
    if college is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(college)
    db.commit()
    return {"message": "Unit deleted successfully"}
