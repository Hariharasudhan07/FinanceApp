# app/main.py
from fastapi import FastAPI
from app.routes.expenses import router as expenses_router

app = FastAPI(title="Financial App Backend - MVP Phase 1")

# Register all routes
app.include_router(expenses_router, prefix="/api")

