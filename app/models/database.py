from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON, Enum, Text, Boolean, Integer, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
import uuid
from datetime import datetime
import enum
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatasetStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    processing = "processing"
    published = "published"
    failed = "failed"

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), index=True)
    slug = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False, default="")
    short_description = Column(String(500))
    category_id = Column(UUID(as_uuid=True), nullable=False)
    satellite_id = Column(UUID(as_uuid=True), nullable=False)
    band_type = Column(String)
    data_type = Column(String, default='archive')
    pass_id = Column(UUID(as_uuid=True))
    spatial_coverage = Column(Geometry('POLYGON', srid=4326), nullable=False)
    resolution_meters = Column(Float, nullable=False)
    temporal_start = Column(Date)
    temporal_end = Column(Date)
    revisit_frequency_hours = Column(Integer)
    cloud_cover_pct = Column(Float)
    sun_elevation_deg = Column(Float)
    bands = Column(JSONB, default=list)
    file_format = Column(String(50))
    file_size_mb = Column(Float)
    price_usd = Column(Float)
    subscription_price_usd = Column(Float)
    license_type = Column(String(100))
    license_details = Column(Text)
    preview_thumbnail_url = Column(Text)
    preview_cog_url = Column(Text)
    sample_data_url = Column(Text)
    tags = Column(ARRAY(String))
    status = Column(Enum(DatasetStatus), default=DatasetStatus.draft)
    is_featured = Column(Boolean, default=False)
    total_purchases = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    avg_rating = Column(Float)
    review_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSONB, default=dict)
    product_vertical = Column(String(50), default='marketplace')
    provider_user_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    product_id = Column(UUID(as_uuid=True))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()