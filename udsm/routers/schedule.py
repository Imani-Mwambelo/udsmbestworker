from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from udsm import models, schemas
from udsm.database import get_db
from typing import List
import pytz
from udsm.authentication.oauth2 import get_current_user

router = APIRouter(tags=['Admin Endpoints'])

def is_admin(current_user: schemas.CurrentUser):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")

@router.post("/schedule-nomination", response_model=schemas.NominationPeriodOut)
def create_nomination_period(period: schemas.NominationPeriodBase, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(get_current_user)):
    is_admin(current_user=current_user)
    # Parse the provided datetime strings and convert to UTC
    start_time = datetime.strptime(period.start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(period.end_time, "%Y-%m-%d %H:%M:%S")

    db_period = models.NominationPeriod(
        start_time=start_time,
        end_time=end_time
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return schemas.NominationPeriodOut(
        id=db_period.id,
        start_time=db_period.start_time.isoformat(),
        end_time=db_period.end_time.isoformat()
    )



@router.get("/schedule-nomination", response_model=List[schemas.NominationPeriodOut])
def get_nomination_period(db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(get_current_user)):
    is_admin(current_user=current_user)

    db_period = db.query(models.NominationPeriod).all()
    if not db_period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No nomination schedules yet")
    return db_period



@router.post("/schedule-voting", response_model=schemas.VotingPeriodOut)
def schedule_voting(period: schemas.VotingPeriodCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(get_current_user)):
    is_admin(current_user=current_user)
    # Parse the provided datetime strings and convert to UTC
    start_time = datetime.strptime(period.start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(period.end_time, "%Y-%m-%d %H:%M:%S")

    db_period = models.VotingPeriod(
        start_time=start_time,
        end_time=end_time
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return schemas.VotingPeriodOut(
        id=db_period.id,
        start_time=db_period.start_time.isoformat(),
        end_time=db_period.end_time.isoformat()
    )
    

@router.post("/schedule-nomination_result-release", response_model=schemas.ResultReleasePeriodOut)
def schedule_result_release(period: schemas.ResultReleasePeriodCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(get_current_user)):
    is_admin(current_user=current_user)
    # Parse the provided datetime strings and convert to UTC
    release_time = datetime.strptime(period.release_time, "%Y-%m-%d %H:%M:%S")

    db_period = models.NominationResultReleasePeriod(
        release_time=release_time
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return schemas.ResultReleasePeriodOut(
        id=db_period.id,
        release_time=db_period.release_time.isoformat(),
    )


@router.post("/schedule-vote_result-release", response_model=schemas.ResultReleasePeriodOut)
def schedule_result_release(period: schemas.ResultReleasePeriodCreate, db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(get_current_user)):
    is_admin(current_user=current_user)
    # Parse the provided datetime strings and convert to UTC
    release_time = datetime.strptime(period.release_time, "%Y-%m-%d %H:%M:%S")

    db_period = models.ResultReleasePeriod(
        release_time=release_time
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return schemas.ResultReleasePeriodOut(
        id=db_period.id,
        release_time=db_period.release_time.isoformat(),
    )
