from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from app.worker.ingestion_task import start_ingestion
from app.models.database import get_db, Dataset, DatasetStatus
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Optional
import uuid

router = APIRouter()

@router.post("/ingest")
async def ingest_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    satellite_id: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Save upload temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Generate mock UUIDs if not provided
    dataset_id = uuid.uuid4()
    t_id = uuid.UUID(tenant_id) if tenant_id else uuid.uuid4()
    
    # Fetch a valid category and satellite if not provided
    from sqlalchemy import text
    if not category_id:
        existing_c = db.execute(text("SELECT id FROM dataset_categories LIMIT 1")).scalar()
        c_id = existing_c if existing_c else uuid.uuid4()
    else:
        c_id = uuid.UUID(category_id)
        
    if not satellite_id:
        existing_s = db.execute(text("SELECT id FROM satellites LIMIT 1")).scalar()
        s_id = existing_s if existing_s else uuid.uuid4()
    else:
        s_id = uuid.UUID(satellite_id)
        
    p_id = uuid.UUID(product_id) if product_id else None
    
    # Create a pending dataset record
    dataset = Dataset(
        id=dataset_id,
        tenant_id=t_id,
        slug=f"{file.filename.split('.')[0]}-{str(dataset_id)[:8]}".lower(),
        title=file.filename,
        category_id=c_id,
        satellite_id=s_id,
        product_id=p_id,
        spatial_coverage="SRID=4326;POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))", # Dummy, replaced by worker
        resolution_meters=0.0, # Dummy, replaced by worker
        status=DatasetStatus.pending
    )
    db.add(dataset)
    db.commit()
    
    # Start async ingestion (Celery task)
    start_ingestion.delay(str(dataset.id), temp_path, str(s_id))
    
    return {"dataset_id": str(dataset.id), "status": "processing"}

@router.get("/ingest/{dataset_id}/status")
def get_status(dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"status": dataset.status, "cog_url": dataset.preview_cog_url}