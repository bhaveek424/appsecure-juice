from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import dependency_status, overall_status
from app.routes import config as config_routes

app = FastAPI(title="AppSec Review Workbench")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_routes.router)


@app.get("/health")
def health():
    dependencies = dependency_status()
    return {
        "status": overall_status(dependencies),
        "dependencies": dependencies,
    }
