from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.story import router as story_router

app = FastAPI(
    title="AI Chinese History Sandbox",
    version="0.1.0",
    description="FastAPI backend for a branching ancient-China history project.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:18422", "http://localhost:18422"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(story_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "AI Chinese History Sandbox backend is running.",
        "docs": "/docs",
    }

