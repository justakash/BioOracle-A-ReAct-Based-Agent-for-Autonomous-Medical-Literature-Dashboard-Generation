"""
BioOracle FastAPI Server
Main application entry point and middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api.routes import query, dashboard, export, health

app = FastAPI(
    title="BioOracle",
    description="ReAct-based agent for autonomous medical literature dashboard generation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.on_event("startup")
async def startup_event():
    logger.info("BioOracle API server starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("BioOracle API server shutting down...")
