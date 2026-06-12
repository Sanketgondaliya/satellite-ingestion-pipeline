from celery import Celery
from app.services.metadata_extractor import extract_metadata
from app.services.cog_generator import generate_cog
from app.services.s3_service import upload_to_raw_bucket, upload_cog_to_s3
from app.services.preview_generator import generate_thumbnail, upload_thumbnail_to_s3
from app.models.database import SessionLocal, Dataset, DatasetStatus
from config import REDIS_URL
import os
import uuid
from datetime import datetime

celery_app = Celery("ingestion", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def start_ingestion(dataset_id: str, local_temp_path: str, satellite_id: str = None):
    db = SessionLocal()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return
    
    try:
        # Update status
        dataset.status = DatasetStatus.processing
        db.commit()
        
        # 1. Upload raw file to S3
        raw_key = f"raw/{dataset_id}/{os.path.basename(local_temp_path)}"
        raw_s3_url = upload_to_raw_bucket(local_temp_path, raw_key)
        dataset.sample_data_url = raw_s3_url
        
        # 2. Extract metadata using GDAL
        metadata = extract_metadata(local_temp_path)
        dataset.resolution_meters = metadata.get("resolution_meters") or 10.0
        dataset.cloud_cover_pct = metadata.get("cloud_cover_pct", 0.0)
        
        if metadata.get("spatial_coverage_wkt"):
            dataset.spatial_coverage = f"SRID=4326;{metadata['spatial_coverage_wkt']}"
            
        dataset.metadata_ = metadata
        
        # 3. Generate COG
        cog_local = f"/tmp/{dataset_id}_cog.tif"
        generate_cog(local_temp_path, cog_local)
        
        # 4. Upload COG to S3
        cog_s3_url = upload_cog_to_s3(cog_local, str(dataset.id))
        dataset.preview_cog_url = cog_s3_url
        
        # 5. Generate thumbnail & preview
        thumb_bytes = generate_thumbnail(cog_local)
        thumb_url = upload_thumbnail_to_s3(thumb_bytes, str(dataset.id))
        dataset.preview_thumbnail_url = thumb_url
        
        # 7. Mark as published
        dataset.status = DatasetStatus.published
        dataset.published_at = datetime.utcnow()
        db.commit()
        
        # Clean temp files
        os.remove(local_temp_path)
        os.remove(cog_local)
        
    except Exception as e:
        dataset.status = DatasetStatus.failed
        db.commit()
        raise e
    finally:
        db.close()