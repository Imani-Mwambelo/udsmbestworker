from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from jose import jwt, JWSError
from fastapi.security.oauth2 import OAuth2PasswordBearer
from ..config import settings
from udsm import schemas


oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')
SECRET_KEY=settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data:dict):
    to_encode=data.copy()

    expire_time=datetime.now(tz=timezone.utc) +timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire_time})

    encoded_jwt=jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_access_token(token:str, cridentials_exception):

    try:
       payload= jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGORITHM )
       id=payload.get("id")
       category=payload.get("category")
       department_id=payload.get("department_id")
       unit_id=payload.get("unit_id")

       if id is None:
            raise cridentials_exception
       token_data={"id": id, "category": category, "department_id":department_id,"unit_id":unit_id}
    except JWSError:
        raise cridentials_exception
    return token_data


def get_current_user(token:str=Depends(oauth2_scheme)):
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"could not validate cridentials", headers={"WWW-Authenticate":"Bearer"})

    return verify_access_token(token=token, cridentials_exception=credentials_exception)
    