from fastapi import FastAPI

from app.routes.api_router import router as api_router

app = FastAPI(
    title="Face Search API",
    description="Find photos containing similar faces in a permitted collection.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")
