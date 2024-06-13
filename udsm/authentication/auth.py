from fastapi import FastAPI, Response, status, HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from udsm import models, schemas
from udsm.authentication import oauth2, utils
from udsm.database import get_db

router=APIRouter(tags=['Authentication'])

@router.post('/login', response_model=schemas.Token)
def login(user_cridentials:OAuth2PasswordRequestForm= Depends(), db: Session=Depends(get_db)):
      

      usr=db.query(models.Worker).filter(models.Worker.email==user_cridentials.username).first()
  
      
      if not usr:     
          raise HTTPException(status_code=status.HTTP_403_FORBIDDEN , detail=f"Invalid cridentials, wrong email or password")
    
      if not utils.verify(user_cridentials.password,usr.password):
          raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid cridentials, wrong email or password")
    
      access_token=oauth2.create_access_token(data={"id":usr.id, "category":usr.category, "department_id":usr.department_id,"unit_id":usr.unit_id})

      return {"access_token":access_token, "token_type":"bearer"}



