"""
FastAPI Slot Machine Game - Main Application
============================================

A probability theory research tool implementing a slot machine game
with configurable probabilities and detailed analytics.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
import sys
from pathlib import Path

# Add app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.routes import router as api_router
from app.core.config import (
    APP_NAME,
    APP_VERSION,
    DEBUG_MODE,
    API_PREFIX,
    logger
)
from app.core.database import init_database, close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    # Initialize database
    await init_database()
    logger.info("Database initialized")

    # Create static directories if they don't exist
    static_dir = Path("static")
    templates_dir = Path("templates")
    static_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_database()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Initialize FastAPI app
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description="A slot machine game for probability theory research",
        docs_url="/docs" if DEBUG_MODE else None,
        redoc_url="/redoc" if DEBUG_MODE else None,
        openapi_url="/openapi.json" if DEBUG_MODE else None,
        lifespan=lifespan
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if DEBUG_MODE else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include API routes
    app.include_router(
        api_router,
        prefix=API_PREFIX,
        tags=["Slot Machine API"]
    )

    # Mount static files
    if Path("static").exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")

    # Setup templates
    templates = None
    if Path("templates").exists():
        templates = Jinja2Templates(directory="templates")

    @app.get("/", tags=["Frontend"])
    async def read_root(request: Request):
        """
        Serve the main game interface.

        Returns:
            TemplateResponse or JSONResponse with game info
        """
        if templates:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "app_name": APP_NAME}
            )
        else:
            return {
                "message": f"Welcome to {APP_NAME}",
                "version": APP_VERSION,
                "docs_url": "/docs",
                "api_prefix": API_PREFIX
            }

    @app.get("/health", tags=["Health Check"])
    async def health_check():
        """
        Health check endpoint for monitoring.

        Returns:
            Dict with health status
        """
        return {
            "status": "healthy",
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "environment": "development" if DEBUG_MODE else "production"
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled errors.

        Args:
            request: The request object
            exc: The exception that occurred

        Returns:
            JSONResponse with error details
        """
        logger.error(f"Unhandled exception on {request.url}: {exc}")

        if DEBUG_MODE:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc),
                    "path": str(request.url)
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred"
                }
            )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle HTTP exceptions with proper formatting.

        Args:
            request: The request object
            exc: The HTTP exception

        Returns:
            JSONResponse with formatted error
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP {exc.status_code}",
                "message": exc.detail,
                "path": str(request.url)
            }
        )

    return app


# Create application instance
app = create_application()


def main():
    """
    Main function to run the application.
    Used when running with python main.py
    """
    logger.info(f"Starting {APP_NAME} server...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG_MODE,
        log_level="debug" if DEBUG_MODE else "info",
        access_log=DEBUG_MODE
    )


if __name__ == "__main__":
    main()