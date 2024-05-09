
from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from udsm.authentication import oauth2
from ..database import get_db, engine

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
def submit_nomination_for_department(
    nomination: schemas.Nomination,
    db: Session = Depends(get_db),
    current_user:schemas.CurrentUser=Depends(oauth2.get_current_user)
    
):
    # Retrieve the department based on college and department name
    department=db.query(models.Department).filter(models.Department.id==current_user['department_id']).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    college_name=department.college.name
    department_name=department.name

    db_department = db.query(models.Department).filter(
        models.Department.college.has(name=college_name),
        models.Department.name == department_name
    ).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if the nominated staff belongs to the same department
    if nomination.nominee_id not in [worker.id for worker in db_department.workers]:
        raise HTTPException(status_code=400, detail="Staff does not belong to the same department")
    
    nominee=db.query(models.Worker).filter_by(id=nomination.nominee_id).first()

    if nominee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nominee does not exist in this dpt")


    # Check if the nominee is of the same category as specified in the nomination
    if nominee.category != nomination.category:
            raise HTTPException(status_code=400, detail=f"Nominee is not of {nomination.category} category ")

     # Check if the nomination already exists in the staging list for the same nominator and nominee
    for staged_nomination in nominations_staging.get_staged_nominations():
        if (staged_nomination.nominee_id == nomination.nominee_id 
            ):
            raise HTTPException(status_code=400, detail="You have already nominated this candidate")

    # Check if the nominator has already nominated another candidate with the same weight
    for staged_nomination in nominations_staging.get_staged_nominations():
        if ( 
            staged_nomination.weight == nomination.weight):
            raise HTTPException(status_code=400, detail="You can't nominate two candidates with the same weight")
    
    

    # Stage the nomination
    nominations_staging.stage_nomination(nomination)
    return nomination
@router.post("/commit-nominations/", response_model=List[schemas.Nomination])
def commit_nominations(db: Session = Depends(get_db), current_user:schemas.CurrentUser=Depends(oauth2.get_current_user)):
    # Ensure exactly three nominations are staged
    staged_nominations = nominations_staging.get_staged_nominations()
    if len(staged_nominations) != 3:
        raise HTTPException(status_code=400, detail="You must stage exactly three nominations")

    # Commit staged nominations to the database
    for nomination in staged_nominations:
         db_nomination = models.Nomination(**nomination.model_dump(), department_id=current_user['department_id'], nominator_id=current_user['id'])
         db.add(db_nomination)
    db.commit()
    
    nominations_staging.clear_staged_nominations()
    my_noms=db.query(models.Nomination).filter(models.Nomination.nominator_id==current_user['id']).all()
    return my_noms



    
    # # Create the nomination
    # db_nomination = models.Nomination(**nomination.model_dump(), department_id=db_department.id, nominator_id=current_user['id'])
    # db.add(db_nomination)
    # db.commit()
    # db.refresh(db_nomination)
    # return db_nomination

@router.post("/nominations/")
def create_nomination(nomination:schemas.Nomination, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    
    new_nomination=models.Nomination(**nomination.model_dump(), nominator_id=current_user['id'], department_id=current_user['department_id']) 

    # Fetch the nominated worker
    nom_exist = db.query(models.Nomination).filter_by(nominee_id=new_nomination.nominee_id, nominator_id=new_nomination.nominator_id).first()
    weight_exist = db.query(models.Nomination).filter_by(nominator_id=new_nomination.nominator_id, weight=new_nomination.weight).first()

    if nom_exist is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Already nominated this candidate")
    
    if weight_exist is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="you can't nominate two candidates with the same weight")
    
    
    cate_check = db.query(models.Worker).filter_by(id=nomination.nominee_id, category=nomination.category).first()

    if cate_check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nominee is not of {nomination.category} category ")

    db.add(new_nomination)
    db.commit()
    db.refresh(new_nomination)
    return new_nomination


#getting all available nominations
@router.get("/nominations/")
def all_nominations(db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    print(current_user['id'])
    nominations=db.query(models.Nomination).all()
    if not nominations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No any nomination yet")
    return nominations


#getting all nominations of a worker by using their id
@router.get("/nominations/{nominator_id}")
def my_nominations(nominator_id:int, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    nominations=db.query(models.Nomination).filter_by(nominator_id=nominator_id).all()
    if nominations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have no any nomination yet")
    return nominations

#getting a single nomination of a worker using their id and nomination id
@router.get("/nominations/{nominator_id}/{nomination_id}")
def my_nomination(nomination_id:int, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    nomination=db.query(models.Nomination).filter_by(nominator_id=current_user['id'], id=nomination_id).first()
    if nomination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have no this nomination yet")
    return nomination



@router.delete("/nominations/{id}")
def delete_nomination(id:int, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    nom_query=db.query(models.Nomination).filter(models.Nomination.id==id)
    nomination=nom_query.first()
       
    if nomination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Nomination with id {id} do not exist")

    if nomination.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform the requested action")
        
    nom_query.delete(synchronize_session=False)
    db.commit()
    raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,detail=f"Nomination with id {id} was successfully deleted")


@router.put("/nominations/{id}", response_model=schemas.Nomination)
def update_nomination(id:int,post:schemas.Nomination, db: Session=Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    nom_query=db.query(models.Nomination).filter(models.Nomination.id==id)
    updated_nom=nom_query.first()
    if updated_nom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Nomination with id {id} do not exist")
    
    if updated_nom.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform the requested action")
         
    nom_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    return updated_nom




@router.get("/nominationresults/{category}", response_model=List[schemas.Worker])
def get_top_workers(category: str, db: Session = Depends(get_db)):
    # Query workers with the given category and order them by points in descending order
    top_workers = db.query(models.Worker).filter_by(category==category).order_by(models.Worker.points.desc()).limit(3).all()
    return top_workers

@router.get("/n/{id}", response_model=List[schemas.WorkerOut])
def get_workers_with_nominations_count(dep_id:int, db: Session = Depends(get_db)):
    # Query to count the distinct nominator_ids from the nominations table
    dep_workers = db.query(models.Worker).filter_by(department_id=dep_id).all()
    return dep_workers



# @router.get("/results/{category}")
# def compute_results(category:str, db: Session = Depends(get_db)):
#     try:
#         # Clear the results table
#         db.query(models.Result).delete()
#         db.commit()
#     except OperationalError:
#         # Handle exception if the table does not exist
#         pass

#     # Step 1: Retrieve the total number of workers who created nominations
#     total_workers = db.query(models.Nomination).distinct(models.Nomination.nominator_id).count()

#     # Step 2: Calculate the overall total points
#     overall_total_points = 6 * total_workers

    

#     # Step 3: Calculate results for each worker
#     results = List[schemas.Result]
    
#     # Group nominations by worker ID and calculate total points and percentage
#     for worker_id, worker_total_points in db.query(models.Nomination.nominee_id, func.sum(models.Nomination.weight)).group_by(models.Nomination.nominee_id).all():
#         # Calculate percentage for the worker
#         percentage = (worker_total_points / overall_total_points) * 100 if overall_total_points != 0 else 0

#         # Store the result in the database
#         db_result = models.Result(worker_id=worker_id, percentage=percentage)
#         db.add(db_result)

#     db.commit()
    

#    # results=db.query(models.Result).order_by(models.Result.percentage.desc()).limit(3).all()
#     result_query=db.query(models.Result, models.Worker.email,models.Worker.category).join(models.Worker, models.Result.worker_id==models.Worker.id, isouter=True).group_by(models.Result.id, models.Result.worker_id)
#     results=result_query.all()

    
#     return results


from sqlalchemy.exc import OperationalError

@router.get("/results/{category}")
def compute_results(category: str, db: Session = Depends(get_db)):
    try:
        # Clear the results table
        db.query(models.Result).delete()
        db.commit()
    except OperationalError:
        # Handle exception if the table does not exist
        pass

    # Step 1: Retrieve the total number of workers who created nominations in the specified category
    total_workers = db.query(models.Nomination)\
                      .distinct(models.Nomination.nominator_id)\
                      .count()

    # Step 2: Calculate the overall total points for the specified category
    overall_total_points = 6 * total_workers

    # Step 3: Calculate results for each worker in the specified category
    for worker_id, worker_total_points in db.query(models.Nomination.nominee_id, func.sum(models.Nomination.weight))\
                                             .join(models.Worker, models.Nomination.nominee_id == models.Worker.id)\
                                             .filter(models.Worker.category == category)\
                                             .group_by(models.Nomination.nominee_id)\
                                             .all():
        # Calculate percentage for the worker
        percentage = round((worker_total_points / overall_total_points) * 100, 2) if overall_total_points != 0 else 0

        # Store the result in the database
        db_result = models.VoteResult(worker_id=worker_id, percentage=percentage)
        db.add(db_result)

    db.commit()

    # Step 4: Retrieve results along with worker information for the specified category
    results = db.query(models.Result, models.Worker.email, models.Worker.category)\
                .join(models.Worker, models.Result.worker_id == models.Worker.id, isouter=True)\
                .filter(models.Worker.category == category)\
                .group_by(models.Result.id, models.Result.worker_id, models.Worker.email, models.Worker.category)\
                .order_by(models.Result.percentage.desc()).limit(3)\
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




    
    

# Endpoint to get top candidates for voting
# @app.get("/top_candidates/")
# async def get_top_candidates(category: str):
#     category_nominations = [nom for nom in nominations_db if nom.category == category]
#     candidate_points = {}

#     for nomination in category_nominations:
#         if nomination.candidate_id not in candidate_points:
#             candidate_points[nomination.candidate_id] = 0
#         candidate_points[nomination.candidate_id] += nomination.weight

#     # Select top three candidates with highest points
#     top_candidates = sorted(candidate_points.items(), key=lambda x: x[1], reverse=True)[:3]
#     print(top_candidates)

#     return {"top_candidates": top_candidates}

# Mock endpoint for voting

