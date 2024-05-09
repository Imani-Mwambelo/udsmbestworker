from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine
from .nomination import compute_results


router=APIRouter(tags=['Votes'])

@router.post("/votes/", response_model=schemas.Vote)
def create_vote(vote:schemas.Vote, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):


    t=False

    

    top_workers=compute_results(db=db, category=vote.category)

    print(top_workers)




    vote_exist = db.query(models.Vote).filter_by(voter_id=current_user['id'], category=vote.category).first()


    if vote_exist is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Already voted in this category")
    
    votee = db.query(models.Worker).filter_by(id=vote.votee_id, category=vote.category).first()

    if votee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"votee is not of {vote.category} category ")
    
    for result in top_workers:
            if result['email'] ==votee.email :
                 t=True

    if not t:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not eligible to be voted')
    new_vote=models.Vote(**vote.model_dump(), voter_id=current_user['id'], department_id=current_user['department_id']) 

    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    return new_vote


@router.get("/votes/")
def getVotes(db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    votes = db.query(models.Vote).all()
    return votes


@router.get("/results/{category}")
def compute_vote_results(category: str, db: Session = Depends(get_db)):

    # Step 1: Retrieve the total number of workers of votes in the specified category
    total_votes = db.query(models.Vote).filter(category==category).count()
                     
    # Step 3: Calculate results for each worker in the specified category
    for worker_id, worker_total_points in db.query(models.Vote.votee_id, func.count(models.Vote))\
                                             .join(models.Worker, models.Vote.votee_id == models.Worker.id)\
                                             .filter(models.Worker.category == category)\
                                             .group_by(models.Vote.votee_id)\
                                             .all():
        # Calculate percentage for the worker
        percentage = round((worker_total_points / total_votes) * 100, 2) if total_votes != 0 else 0

        # Store the result in the database
        db_result = models.VoteResult(worker_id=worker_id, percentage=percentage)
        db.add(db_result)

    db.commit()

    # Step 4: Retrieve results along with worker information for the specified category
    results = db.query(models.VoteResult, models.Worker.email, models.Worker.category)\
                .join(models.Worker, models.VoteResult.worker_id == models.Worker.id, isouter=True)\
                .filter(models.Worker.category == category)\
                .group_by(models.VoteResult.id, models.VoteResult.worker_id, models.Worker.email, models.Worker.category)\
                .order_by(models.VoteResult.percentage.desc()).limit(3)\
                .all()

    # Format results into a structured format
    formatted_results = []

    for result, email, worker_category in results:
        formatted_results.append({
            "category": worker_category,
            "email": email,
            "percentage": result.percentage,
            
            
        }) 


    return formatted_results

