from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.upload import router

app = FastAPI(
    title="MediExplain AI",
    description="AI Powered Prescription Explainer",
    version="1.0.0"
)

# Serve CSS and JS files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register routes
app.include_router(router)