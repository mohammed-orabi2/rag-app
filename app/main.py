from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

from app.api.controllers import (
    user_router,
    conversation_router,
    message_router,
    health_router,
)
from app.db.database.connection import db_manager
import logging

logger = logging.getLogger(__name__)


def preload_embedding_model():
    """
    Pre-load the embedding model at startup to avoid 8-second delay on first request.
    This loads the HuggingFace model into memory and caches it.

    IMPORTANT: When using gunicorn with preload_app=True, this runs in the MASTER process
    before forking workers. All workers inherit the loaded model via Copy-on-Write,
    reducing memory usage from 8x to ~1.2x the model size.

    The model is forced to use CPU to avoid CUDA out of memory errors when multiple
    workers are forked (each worker would try to initialize its own CUDA context).
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from app.config import vectorstore_config as config

        logger.info("🔥 Pre-loading embedding model at startup...")
        import time

        start = time.time()

        embedding_name = config.embeddings_name

        # Force CPU usage to avoid CUDA OOM with multiple workers
        model_kwargs = {"device": "cpu"}
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_name, model_kwargs=model_kwargs
        )

        # Test the model by encoding a dummy text
        _ = embeddings.embed_query("warmup")

        elapsed = time.time() - start
        logger.info(f"✅ Embedding model pre-loaded successfully in {elapsed:.2f}s")
        logger.info(f"   Model: {embedding_name}")
        logger.info(
            f"   Device: CPU (shared across {os.getenv('WORKERS', 'N')} workers)"
        )

    except Exception as e:
        logger.error(f"⚠️ Failed to pre-load embedding model: {e}")
        logger.error("   First request will experience 8s delay")


def preload_retrievers():
    """
    Pre-initialize all retrievers and vectorstores at startup.
    This eliminates the 8-9s initialization delay on the first request.
    """
    try:
        from app.core.agents.agents import get_cached_child_parent_retriever

        logger.info("🔥 Pre-loading retrievers and vectorstores...")
        import time

        start = time.time()

        # This will initialize all 3 FilterRetrievers and their vectorstores
        retriever = get_cached_child_parent_retriever()

        elapsed = time.time() - start
        logger.info(f"✅ Retrievers pre-loaded successfully in {elapsed:.2f}s")
        logger.info("   All vectorstores are now cached and ready")

    except Exception as e:
        logger.error(f"⚠️ Failed to pre-load retrievers: {e}")
        logger.error("   First request will experience initialization delay")


def preload_prompts():
    """
    Pre-load all prompts from LangSmith at startup.
    This eliminates repeated API calls during request processing.
    """
    try:
        from app.core.src.prompts import preload_all_prompts

        loaded_count, failed_prompts = preload_all_prompts()

        if failed_prompts:
            logger.warning(
                f"⚠️  Some prompts failed to load: {', '.join(failed_prompts)}"
            )

    except Exception as e:
        logger.error(f"⚠️ Failed to pre-load prompts: {e}")
        logger.error("   Prompts will be loaded on-demand during requests")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    logger.info("🚀 Starting application...")

    # Startup: Connect to database
    logger.info("📊 Connecting to database...")
    await db_manager.connect()

    # Pre-load prompts from LangSmith (fast, just API calls)
    preload_prompts()

    # Pre-load embedding model to avoid first-request delay
    preload_embedding_model()

    # Pre-load all retrievers (uses the cached embedding model)
    preload_retrievers()

    logger.info("✅ Application startup complete!")

    yield

    # Shutdown: Disconnect from database
    logger.info("🛑 Shutting down application...")
    await db_manager.disconnect()

    # Close HTTP connection pools
    try:
        from app.core.agents.llms import cleanup_http_clients

        await cleanup_http_clients()
    except Exception as e:
        logger.error(f"⚠️ Failed to cleanup HTTP clients: {e}")

    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Chatbot API",
    description="API for managing chatbots and conversations with LangSmith feedback system",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Root endpoint for API health check
@app.get("/")
async def root():
    return {
        "status": "API is running",
        "message": "Counselling Bot API",
        "version": "1.0.0",
    }


# Add a simple API health check
@app.get("/api")
async def api_health():
    return {"status": "API is running", "message": "Counselling Bot API"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*",  # Allow all origins for debugging
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api", tags=["Authentication", "Users"])
app.include_router(conversation_router, prefix="/api", tags=["Conversations"])
app.include_router(message_router, prefix="/api", tags=["Messages"])
app.include_router(health_router, prefix="/api", tags=["Health"])
