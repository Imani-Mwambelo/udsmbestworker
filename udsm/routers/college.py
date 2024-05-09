from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine

router=APIRouter(tags=['College'])


@router.post("/college/")
def create_college(college: schemas.CollegeCreate, db: Session = Depends(get_db)):
    db_college = models.College(**college.model_dump())
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college

@router.get("/college/{college_id}")
def read_college(college_id: int, db: Session = Depends(get_db)):
    db_college = db.query(models.College).filter(models.College.id == college_id).first()
    if db_college is None:
        raise HTTPException(status_code=404, detail="College not found")
    return db_college

@router.get("/college/")
def read_colleges(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.College).offset(skip).limit(limit).all()

@router.put("/college/{college_id}")
def update_college(college_id: int, college: schemas.CollegeCreate, db: Session = Depends(get_db)):
    db_college = db.query(models.College).filter(models.College.id == college_id).first()
    if db_college is None:
        raise HTTPException(status_code=404, detail="College not found")
    for key, value in college.model_dump().items():
        setattr(db_college, key, value)
    db.commit()
    db.refresh(db_college)
    return db_college

@router.delete("/college/{college_id}")
def delete_college(college_id: int, db: Session = Depends(get_db)):
    db_college = db.query(models.College).filter(models.College.id == college_id).first()
    if db_college is None:
        raise HTTPException(status_code=404, detail="College not found")
    db.delete(db_college)
    db.commit()
    return {"message": "College deleted successfully"}
