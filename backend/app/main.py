from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.dependencies import dependency_status, overall_status
from app.routes import config as config_routes
from app.routes import findings as findings_routes
from app.routes import scans as scans_routes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AppSec Review Workbench", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_routes.router)
app.include_router(scans_routes.router)
app.include_router(findings_routes.router)


@app.get("/health")
def health():
    dependencies = dependency_status()
    return {
        "status": overall_status(dependencies),
        "dependencies": dependencies,
    }
