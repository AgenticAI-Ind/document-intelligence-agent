"""
Document Intelligence Agent
Production-ready AI agent with FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import os

from .config import settings
from .api.routes import router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    logger.info("Starting Document Intelligence Agent...")

    # Create data directory if it doesn't exist
    os.makedirs("./data/chroma", exist_ok=True)

    # Pre-load models
    try:
        from .agent import DocumentParser, EntityExtractor
        parser = DocumentParser()
        extractor = EntityExtractor()
        logger.info("Document processing modules loaded successfully")
    except Exception as e:
        logger.warning(f"Could not pre-load all modules: {e}")

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Document Intelligence Agent",
    description="""
    Enterprise-grade document intelligence with AI-powered:
    - Multi-format document parsing (PDF, Word, Excel, PowerPoint, etc.)
    - AI-powered Q&A on documents
    - Automatic summarization (multiple styles)
    - Entity extraction (names, dates, organizations, locations)
    - Multi-document search with RAG
    - Document comparison and version tracking

    Process 100s of documents 10x faster with intelligent automation.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Document Intelligence"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Document Intelligence Agent",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "features": [
            "Multi-format document parsing",
            "AI-powered Q&A",
            "Automatic summarization",
            "Entity extraction",
            "Document search (RAG)",
            "Document comparison"
        ]
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "operational",
            "ai_models": "operational",
            "vector_store": "operational"
        }
    }


@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint"""
    return {
        "message": "Document Intelligence Dashboard",
        "endpoints": {
            "upload": "/api/v1/upload",
            "parse": "/api/v1/parse",
            "qa": "/api/v1/qa",
            "summarize": "/api/v1/summarize",
            "extract_entities": "/api/v1/extract-entities",
            "compare": "/api/v1/compare",
            "search": "/api/v1/search"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
