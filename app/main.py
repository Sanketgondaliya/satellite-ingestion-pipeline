from fastapi import FastAPI
from app.api import ingestion
from app.models.database import engine, Base

# Create database tables (Disabled - tables are already created)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Satellite Ingestion Pipeline", version="1.0")

app.include_router(ingestion.router, prefix="/api/v1", tags=["ingestion"])

@app.get("/health")
def health_check():
    return {"status": "ok"}