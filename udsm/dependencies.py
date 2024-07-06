from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from udsm import models
import pytz

def check_nomination_period(db: Session):
    # Get the current time in UTC using pytz
    now_utc = datetime.now(pytz.timezone('Africa/Nairobi'))
    print(now_utc)

    # Fetch the most recent nomination period
    period = db.query(models.NominationPeriod).order_by(models.NominationPeriod.created_at.desc()).first()

    if period:
        # Ensure the period times are in UTC
        start_time_utc = period.start_time.astimezone(pytz.timezone('Africa/Nairobi'))
        end_time_utc = period.end_time.astimezone(pytz.timezone('Africa/Nairobi'))
        print(period.end_time)
    else:
        start_time_utc = end_time_utc = None

    if not period or not (start_time_utc <= now_utc <= end_time_utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nominations are not allowed at this time")

    

def check_voting_period(db: Session):
     # Get the current time in UTC using pytz
    now_utc = datetime.now(pytz.timezone('Africa/Nairobi'))
    print(now_utc)

    # Fetch the most recent nomination period
    period = db.query(models.VotingPeriod).order_by(models.VotingPeriod.created_at.desc()).first()

    if period:
        # Ensure the period times are in UTC
        start_time_utc = period.start_time.astimezone(pytz.timezone('Africa/Nairobi'))
        end_time_utc = period.end_time.astimezone(pytz.timezone('Africa/Nairobi'))
        print(period.end_time)
    else:
        start_time_utc = end_time_utc = None

    if not period or not (start_time_utc <= now_utc <= end_time_utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voting is not allowed at this time")

def check_result_release_period(db: Session):
    now_utc = datetime.now(pytz.timezone('Africa/Nairobi'))


    # Fetch the most recent nomination period
    period = db.query(models.ResultReleasePeriod).order_by(models.ResultReleasePeriod.created_at.desc()).first()

    if period:
        # Ensure the period times are in UTC
        release_time_utc = period.release_time.astimezone(pytz.timezone('Africa/Nairobi'))
        
    

    if not period or not (now_utc <= release_time_utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Results are not yet released")
    
def check_nom_result_release_period(db: Session):
    now_utc = datetime.now(pytz.timezone('Africa/Nairobi'))


    # Fetch the most recent nomination period
    period = db.query(models.NominationResultReleasePeriod).order_by(models.NominationResultReleasePeriod.created_at.desc()).first()

    if period:
        # Ensure the period times are in UTC
        release_time_utc = period.release_time.astimezone(pytz.timezone('Africa/Nairobi'))
        
    

    if not period or not (now_utc <= release_time_utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nomination results are not yet released")