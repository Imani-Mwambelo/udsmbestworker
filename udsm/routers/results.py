from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from .. import models
from .. import schemas
from ..database import get_db
from ..authentication import oauth2

router = APIRouter(tags=['Results'])

@router.get("/best_workers")
def get_best_workers(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    unit_id = current_user['unit_id']
    categories = ['junior', 'senior', 'administrative']

    best_workers = []

    for category in categories:
        # Retrieve all workers in the specified category and unit
        workers_in_category = db.query(models.Worker.id, models.Worker.name, models.Worker.email, models.Worker.category)\
                                .filter(models.Worker.category == category, models.Worker.unit_id == unit_id).all()

        if not workers_in_category:
            continue

        # Retrieve all results in the specified category and unit
        results_in_category = db.query(models.VoteResult.worker_id, models.VoteResult.percentage)\
                                .join(models.Worker, models.VoteResult.worker_id == models.Worker.id)\
                                .filter(models.Worker.category == category, models.Worker.unit_id == unit_id).all()

        if not results_in_category:
            continue

        # Find the worker with the highest win percentage
        best_worker = max(results_in_category, key=lambda x: x.percentage)

        worker_details = db.query(models.Worker.name, models.Worker.email)\
                           .filter(models.Worker.id == best_worker.worker_id).first()

        if not worker_details:
            continue

        best_workers.append({
            
            "name": worker_details.name,
            "email": worker_details.email,
            "category": category,
            "percentage": best_worker.percentage,
        })

    if not best_workers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No workers found for any category")

    return best_workers