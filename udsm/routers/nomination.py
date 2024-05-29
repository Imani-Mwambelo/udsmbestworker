
from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine
from sqlalchemy.exc import OperationalError

router=APIRouter(tags=['Nominations'])



class NominationsStaging:
    def __init__(self):
        self.nominations = []

    def stage_nomination(self, nomination: schemas.Nomination):
        if len(self.nominations) < 3:
            self.nominations.append(nomination)
        else:
            raise HTTPException(status_code=400, detail="You can only stage three nominations")

    def get_staged_nominations(self) -> List[schemas.Nomination]:
        return self.nominations

    def clear_staged_nominations(self):
        self.nominations = []

# Create an instance of the staging class
nominations_staging = NominationsStaging()



def ensure_three_nominations(db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    # Check the number of nominations created by the worker
    worker_nominations_count = db.query(models.Nomination).filter(
        models.Nomination.nominator_id == current_user['id']
    ).count()
    if worker_nominations_count != 3:
        raise HTTPException(status_code=400, detail="You must create exactly three nominations")

# Endpoint to submit nominations

@router.post("/college/{college_name}/department/{department_name}/nominate/", response_model=schemas.Nomination)
def create_nomination_for_department(
    nomination: schemas.Nomination,
    db: Session = Depends(get_db),
    current_user: schemas.CurrentUser = Depends(oauth2.get_current_user)
):
    department = db.query(models.Department).filter(
        models.Department.id == current_user['department_id']
    ).first()
    
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check if the nominated staff belongs to the same department
    if not db.query(models.Worker).filter(models.Worker.id == nomination.nominee_id, models.Worker.department_id == department.id).first():
        raise HTTPException(status_code=400, detail="Staff does not belong to the same department")

    nominee = db.query(models.Worker).filter_by(id=nomination.nominee_id).first()
    if not nominee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nominee does not exist in this department")

    # Check if the nominee is of the same category as specified in the nomination
    if nominee.category != nomination.category:
        raise HTTPException(status_code=400, detail=f"Nominee is not of {nomination.category} category")

    # Check for existing staged nominations
    for staged_nomination in nominations_staging.get_staged_nominations():
        if staged_nomination.nominee_id == nomination.nominee_id:
            raise HTTPException(status_code=400, detail="You have already nominated this candidate")
        if staged_nomination.weight == nomination.weight:
            raise HTTPException(status_code=400, detail="You can't nominate two candidates with the same weight")

    # Stage the nomination
    nominations_staging.stage_nomination(nomination)
    return nomination


@router.post("/commit-nominations/", response_model=List[schemas.Nomination])
def commit_nominations(db: Session = Depends(get_db), current_user: schemas.CurrentUser = Depends(oauth2.get_current_user)):
    staged_nominations = nominations_staging.get_staged_nominations()
    if len(staged_nominations) != 3:
        raise HTTPException(status_code=400, detail="You must stage exactly three nominations")

    # Commit staged nominations to the database
    for nomination in staged_nominations:
        db_nomination = models.Nomination(
            **nomination.model_dump(), 
            department_id=current_user['department_id'], 
            nominator_id=current_user['id']
        )
        db.add(db_nomination)
    db.commit()
    
    nominations_staging.clear_staged_nominations()
    my_noms = db.query(models.Nomination).filter(models.Nomination.nominator_id == current_user['id']).all()
    return my_noms


#getting all available nominations
@router.get("/nominations/")
def all_nominations(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nominations = db.query(models.Nomination).all()
    if not nominations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No nominations found")
    return nominations



#getting all nominations of a worker by using their id
@router.get("/nominations/{nominator_id}")
def my_nominations(nominator_id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nominations = db.query(models.Nomination).filter_by(nominator_id=nominator_id).all()
    if not nominations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No nominations found for this user")
    return nominations


#getting a single nomination of a worker using their id and nomination id
@router.get("/nominations/{nominator_id}/{nomination_id}")
def my_nomination(nominator_id: int, nomination_id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter_by(nominator_id=current_user['id'], id=nomination_id).first()
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nomination not found")
    return nomination




@router.delete("/nominations/{id}")
def delete_nomination(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter(models.Nomination.id == id).first()
       
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nomination with id {id} does not exist")

    if nomination.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")
        
    db.delete(nomination)
    db.commit()
    return {"detail": f"Nomination with id {id} was successfully deleted"}


@router.put("/nominations/{id}", response_model=schemas.Nomination)
def update_nomination(id: int, post: schemas.Nomination, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter(models.Nomination.id == id).first()
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nomination with id {id} does not exist")
    
    if nomination.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")
         
    for key, value in post.model_dump().items():
        setattr(nomination, key, value)
    db.commit()
    return nomination


@router.get("/nom_results/{category}")
def compute_results(category: str, db: Session = Depends(get_db)):
    try:
        # Clear the results table
        db.query(models.Result).delete()
        db.commit()
    except OperationalError:
        # Handle exception if the table does not exist
        pass

    # Retrieve the total number of workers who created nominations in the specified category
    total_workers = db.query(models.Nomination)\
                      .join(models.Worker, models.Nomination.nominator_id == models.Worker.id)\
                      .filter(models.Worker.category == category)\
                      .distinct(models.Nomination.nominator_id)\
                      .count()
    print(total_workers)

    if total_workers == 0:
        raise HTTPException(status_code=400, detail="No nominations found for the specified category")

    # Calculate the overall total points for the specified category
    overall_total_points = 6 * total_workers

    # Calculate results for each worker in the specified category
    for worker_id, worker_total_points in db.query(models.Nomination.nominee_id, func.sum(models.Nomination.weight))\
                                             .join(models.Worker, models.Nomination.nominee_id == models.Worker.id)\
                                             .filter(models.Worker.category == category)\
                                             .group_by(models.Nomination.nominee_id)\
                                             .all():
        percentage = round((worker_total_points / overall_total_points) * 100, 2) if overall_total_points != 0 else 0
        db_result = models.Result(worker_id=worker_id, percentage=percentage)
        db.add(db_result)

    db.commit()

    # Retrieve results along with worker information for the specified category
    results = db.query(models.Result, models.Worker.email, models.Worker.category)\
                .join(models.Worker, models.Result.worker_id == models.Worker.id, isouter=True)\
                .filter(models.Worker.category == category)\
                .group_by(models.Result.id, models.Result.worker_id, models.Worker.email, models.Worker.category)\
                .order_by(models.Result.percentage.desc()).limit(3)\
                .all()

    formatted_results = [
        {
            "category": worker_category,
            "email": email,
            "percentage": result.percentage,
        } 
        for result, email, worker_category in results
    ]

    return formatted_results








