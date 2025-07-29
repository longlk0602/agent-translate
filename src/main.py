"""
FastAPI Translation Service
Main entry point for the translation API
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import API components
from api.core.dependencies import init_translation_service
from api.v1.endpoints import translation_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""

    # Startup
    logger.info("Starting Translation API...")
    try:
        init_translation_service()
        logger.info("Translation service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize translation service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Translation API...")


# Create FastAPI app
app = FastAPI(
    title="Agent Translation API",
    description="Professional translation service with document processing capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )


# Include routers
app.include_router(translation_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Agent Translation API",
        "version": "1.0.0",
        "description": "Professional translation service with document processing",
        "docs": "/docs",
        "health": "/api/v1/translation/health",
        "timestamp": datetime.now().isoformat(),
    }


# Health check
@app.get("/health")
async def health_check():
    """Global health check"""
    return {
        "status": "healthy",
        "service": "Agent Translation API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


def main():
    """Main function to run the server"""
    print("🌐 Agent Translation API")
    print("=" * 50)

    # Check for required environment variables
    print("Environment Configuration:")
    print(
        f"  OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}"
    )
    print(f"  AZURE_API_KEY: {'✓ Set' if os.getenv('AZURE_API_KEY') else '✗ Not set'}")
    print(f"  AZURE_REGION: {'✓ Set' if os.getenv('AZURE_REGION') else '✗ Not set'}")
    print()

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")

    print(f"Server Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Reload: {reload}")
    print(f"  Log Level: {log_level}")
    print()

    print("Starting server...")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print(f"🚀 Ready to translate!")
    print()

    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()
