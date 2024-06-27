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
def create_vote(
    vote: schemas.Vote,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user)
):
    # Check if the user has already voted in this category
    vote_exist = db.query(models.Vote).filter_by(voter_id=current_user['id'], category=vote.category).first()
    if vote_exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already voted in this category")
    
    # Check if the votee is valid
    votee = db.query(models.Worker).filter_by(id=vote.votee_id, category=vote.category, department_id=current_user['department_id'], unit_id=current_user['unit_id']).first()
    if not votee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Votee is not of {vote.category} category")
    
    # Compute results to get top workers in the category
    top_workers = compute_results(db=db, category=vote.category, current_user=current_user)
    print(top_workers)
    
    # Ensure the votee is among the top workers
    if not any(result['email'] == votee.email for result in top_workers):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Votee is not eligible to be voted")
    
    # Create and save the new vote
    new_vote = models.Vote(**vote.model_dump(), voter_id=current_user['id'], department_id=current_user['department_id'], unit_id=current_user['unit_id'])
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    return new_vote

@router.get("/votes/", response_model=List[schemas.VoteOut])
def get_votes(db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    votes = db.query(models.Vote).all()
    if not votes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No votes found")
    return votes

@router.get("/votes/by-voter/{voter_id}", response_model=List[schemas.VoteOut])
def get_votes_by_voter(voter_id: int, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    votes = db.query(models.Vote).filter_by(voter_id=voter_id).all()
    if not votes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No votes found for this voter")
    return votes


@router.get("/votes/by-category/{category}", response_model=List[schemas.VoteOut])
def get_votes_by_category(category: str, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    votes = db.query(models.Vote).filter_by(category=category, department_id=current_user['department_id'], unit_id=current_user['unit_id']).all()
    if not votes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No votes found for this category")
    return votes

@router.put("/votes/{vote_id}", response_model=schemas.Vote)
def update_vote(vote_id: int, vote: schemas.Vote, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    existing_vote = db.query(models.Vote).filter_by(id=vote_id, voter_id=current_user['id']).first()
    if not existing_vote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found or not authorized")

    # Ensure the new votee is valid and eligible
    votee = db.query(models.Worker).filter_by(id=vote.votee_id, category=vote.category).first()
    if not votee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Votee is not of {vote.category} category")
    
    top_workers = compute_results(db=db, category=vote.category, current_user=current_user)
    if not any(result['email'] == votee.email for result in top_workers):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Votee is not eligible to be voted")

    # Update the vote
    existing_vote.votee_id = vote.votee_id
    existing_vote.category = vote.category
    db.commit()
    db.refresh(existing_vote)
    return existing_vote


@router.delete("/votes/{vote_id}", response_model=dict)
def delete_vote(vote_id: int, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    vote = db.query(models.Vote).filter_by(id=vote_id, voter_id=current_user['id']).first()
    if not vote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found or not authorized")
    db.delete(vote)
    db.commit()
    return {"detail": "Vote successfully deleted"}



@router.get("/results")
def compute_vote_results(db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    try:
        # Clear the results table
        db.query(models.VoteResult).delete()
        db.commit()
    except OperationalError:
        # Handle exception if the table does not exist
        pass

    categories = ["junior", "senior", "administrative"]
    formatted_results = []

    for category in categories:
        # Step 1: Retrieve the total number of votes in the specified category
        total_votes = db.query(models.Vote).filter(models.Vote.category == category).count()
        print(total_votes)

        if total_votes == 0:
            formatted_results.append({
                "category": category,
                "message": "No votes found in this category"
            })
            continue

        # Step 3: Calculate results for each worker in the specified category
        vote_counts = db.query(
            models.Vote.votee_id, 
            func.count(models.Vote.votee_id).label('total_votee_votes')
        ).filter(
            models.Vote.category == category
        ).group_by(
            models.Vote.votee_id
        ).all()
        
        for votee_id, total_votee_votes in vote_counts:
            # Calculate percentage for the worker
            percentage = round((total_votee_votes / total_votes) * 100, 2)
            
            # Store the result in the database
            db_result = models.VoteResult(worker_id=votee_id, percentage=percentage)
            db.add(db_result)

        db.commit()

        # Step 4: Retrieve results along with worker information for the specified category
        results = db.query(
            models.VoteResult, 
            models.Worker.email, 
            models.Worker.category,
            models.Worker.name
        ).join(
            models.Worker, 
            models.VoteResult.worker_id == models.Worker.id, 
            isouter=True
        ).filter(
            models.Worker.category == category,
           
            models.Worker.unit_id == current_user['unit_id']
        ).group_by(
            models.VoteResult.id, 
            models.VoteResult.worker_id, 
            models.Worker.email, 
            models.Worker.category,
            models.Worker.name
        ).order_by(
            models.VoteResult.percentage.desc()
        ).all()

        # Append the winner to the formatted results
        if results:
            result, email, worker_category, name = results[0]
            formatted_results.append({
                "name": name,
                "category": worker_category,
                "email": email,
                "percentage": result.percentage,
            })
        else:
            formatted_results.append({
                "category": category,
                "message": "No results found in this category"
            })

    return formatted_results
