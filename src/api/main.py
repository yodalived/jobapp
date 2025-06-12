# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
# TODO: Import routers once created
# from src.api.routers import applications, scraper, generator

app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Include routers once created
# app.include_router(applications.router, prefix=f"{settings.api_v1_prefix}/applications")
# app.include_router(scraper.router, prefix=f"{settings.api_v1_prefix}/scraper")
# app.include_router(generator.router, prefix=f"{settings.api_v1_prefix}/generator")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Resume Automation API", "version": "0.1.0"}
