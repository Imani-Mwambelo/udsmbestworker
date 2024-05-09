from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine

router=APIRouter(tags=['Department'])


@router.post("/department/")
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    db_department = models.Department(**department.model_dump())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

@router.get("/department/{department_id}")
def read_department(department_id: int, db: Session = Depends(get_db)):
    db_department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department

@router.get("/department/", response_model=List[schemas.DepartmentOut])
def read_departments(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Department).offset(skip).limit(limit).all()

@router.put("/department/{department_id}")
def update_department(department_id: int, department: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    db_department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in department.model_dump().items():
        setattr(db_department, key, value)
    db.commit()
    db.refresh(db_department)
    return db_department

@router.delete("/department/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    db_department = db.query(models.Department).filter(models.Department.id == department_id).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(db_department)
    db.commit()
    return {"message": "Department deleted successfully"}
