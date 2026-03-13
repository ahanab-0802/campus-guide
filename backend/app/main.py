"""
main.py
-------
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, SessionLocal
from app.models.user import Base
from app.routes import auth, resume, pyq

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Campus Guide API",
    description="AI-powered resume optimization and campus placement preparation platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(pyq.router)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        from app.routes.pyq import seed_pyq_data
        seed_pyq_data(db)
    finally:
        db.close()

@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "app": "Campus Guide API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
