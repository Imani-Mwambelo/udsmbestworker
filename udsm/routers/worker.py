from fastapi import status, HTTPException,Depends, APIRouter

from sqlalchemy.orm import Session
from .. import models, schemas
from udsm.authentication import utils
from ..database import  get_db

router=APIRouter(tags=['Workers'],)


@router.post("/workers", response_model=schemas.WorkerOut)
def create_worker(worker:schemas.Worker, db: Session=Depends(get_db)):
        

        usr=db.query(models.Worker).filter(models.Worker.email==worker.email).first()
        if not usr:
             
             #Hashing user password
             hashed_password=utils.hash_password(worker.password)
             worker.password=hashed_password
             new_worker=models.Worker(**worker.model_dump())
             db.add(new_worker)
             db.commit()
             db.refresh(new_worker)
             return new_worker
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"the email already exist, it should be unique")

@router.get("/workers/{id}",response_model=schemas.WorkerOut)
def get_user(id:int, db: Session=Depends(get_db)):
    worker=db.query(models.Worker).filter(models.Worker.id==id).first()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Worker with id {id} do not exist")
        
    return worker

