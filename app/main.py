    """
    Main FastAPI application for the slot machine game.
    """

    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    import logging

    # from app.api.routes import router
    from app.core.config import DEBUG

    logger = logging.getLogger(__name__)

    # Create FastAPI application
    app = FastAPI(
        title="КАЗИК СУКА КАЗИК",
        description="Я пидорас и играю в казик",
        version="1.0.0",
        debug=DEBUG
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="./static"), name="static")

    # Include API routes
    # app.include_router(router, prefix="/api/v1", tags=["slot-machine"])

    # Root route
    @app.get("/")
    async def root():
        """Root endpoint that redirects to the game interface."""
        return FileResponse("./static/index.html")
        # return {"message": "Slot Machine API - Visit /static/index.html to play!"}


    if __name__ == "__main__":
        import uvicorn
        from app.core.config import HOST, PORT

        logger.info("Starting Slot Machine application...")
        uvicorn.run(
            "app.main:app",
            host=HOST,
            port=PORT,
            reload=DEBUG
        )
