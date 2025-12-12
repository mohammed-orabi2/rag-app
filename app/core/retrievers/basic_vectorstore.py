from abc import ABC
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
import logging
import time
import hashlib
import os
from threading import Lock


class BasicVectorstore(ABC):
    _embedding_cache = {}
    _vectorstore_cache = {}  # Memory cache for vectorstores
    _cache_metadata = {}  # Metadata for cache validation
    _cache_lock = Lock()  # Thread safety

    # Class-level configuration
    MAX_CACHE_SIZE = 5  # Maximum number of vectorstores to keep in memory
    CACHE_TTL = 3600  # 1 hour TTL for memory cache

    def __init__(self, collection_name: str, embedding_name: str):
        self.cache_hits = 0
        self.cache_misses = 0
        self.collection_name = collection_name
        self.embedding_name = embedding_name
        self.cache_key = self._generate_cache_key()
        self.embedding_function = self._get_embeddings()
        self.vectorstore = self._get_vectorstore()

    def _generate_cache_key(self) -> str:
        """Generate a unique cache key based on collection name and embedding model"""
        key_string = f"{self.collection_name}_{self.embedding_name}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_embeddings(self):
        """Cache embedding models in memory with CPU device to avoid CUDA OOM"""
        if self.embedding_name not in self._embedding_cache:
            logging.info(f"Loading embedding model: {self.embedding_name}")
            # Force CPU usage to avoid CUDA out of memory with multiple workers
            model_kwargs = {"device": "cpu"}
            self._embedding_cache[self.embedding_name] = HuggingFaceEmbeddings(
                model_name=self.embedding_name, model_kwargs=model_kwargs
            )
        return self._embedding_cache[self.embedding_name]

    def _get_chroma_client(self):
        """Get Chroma client connected to server"""
        try:
            # Use environment variables directly or defaults
            chroma_host = os.getenv("CHROMA_HOST", "localhost")
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

            client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            # Test connection
            client.heartbeat()
            return client
        except Exception as e:
            chroma_host = os.getenv("CHROMA_HOST", "localhost")
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
            logging.error(
                f"Failed to connect to Chroma server at {chroma_host}:{chroma_port}: {e}"
            )
            raise ConnectionError(f"Chroma server connection failed: {e}")

    def _get_collection_hash(self) -> str:
        """Get hash based on collection name for cache validation"""
        # In client-server mode, use collection name as hash
        return hashlib.md5(self.collection_name.encode()).hexdigest()

    def _is_cache_valid(self) -> bool:
        """Check if cached vectorstore is still valid"""
        with self._cache_lock:
            if self.cache_key not in self._cache_metadata:
                return False

            metadata = self._cache_metadata[self.cache_key]
            current_time = time.time()

            # Check TTL
            if current_time - metadata["timestamp"] > self.CACHE_TTL:
                logging.info(f"Cache expired for {self.cache_key}")
                return False

            # Check if collection hash changed
            current_hash = self._get_collection_hash()
            if current_hash != metadata["collection_hash"]:
                logging.info(f"Collection changed for {self.cache_key}")
                return False

            return True

    def _cleanup_old_cache(self):
        """Remove old entries if cache is too large"""
        with self._cache_lock:
            if len(self._vectorstore_cache) >= self.MAX_CACHE_SIZE:
                # Remove oldest entry
                oldest_key = min(
                    self._cache_metadata.keys(),
                    key=lambda k: self._cache_metadata[k]["timestamp"],
                )

                logging.info(f"Removing old cache entry: {oldest_key}")
                del self._vectorstore_cache[oldest_key]
                del self._cache_metadata[oldest_key]

    def _get_vectorstore(self):
        """Get vectorstore with intelligent caching"""
        start_time = time.time()

        # Check memory cache first
        if self.cache_key in self._vectorstore_cache and self._is_cache_valid():
            self.cache_hits += 1
            logging.info(
                f"Memory cache hit for {self.cache_key} ({time.time() - start_time:.3f}s)"
            )
            return self._vectorstore_cache[self.cache_key]

        # Cache miss - load from server
        self.cache_misses += 1
        logging.info(f"Loading vectorstore from server: {self.collection_name}")

        try:
            # Clean up old cache entries if needed
            self._cleanup_old_cache()

            # Get Chroma client and verify collection exists
            client = self._get_chroma_client()
            # Create vectorstore
            vectorstore = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
            )

            # Cache the vectorstore
            with self._cache_lock:
                self._vectorstore_cache[self.cache_key] = vectorstore
                self._cache_metadata[self.cache_key] = {
                    "timestamp": time.time(),
                    "collection_hash": self._get_collection_hash(),
                    "collection_name": self.collection_name,
                    "embedding_name": self.embedding_name,
                }

            load_time = time.time() - start_time
            logging.info(f"Vectorstore loaded and cached in {load_time:.3f}s")

            return vectorstore

        except Exception as e:
            logging.error(
                f"Error loading vectorstore for collection {self.collection_name}: {e}"
            )
            raise e

    def get_vectorstore(self):
        """Public method to get the vectorstore"""
        return self.vectorstore

    def as_retriever(self, **kwargs):
        """Delegate as_retriever to the underlying vectorstore"""
        if self.vectorstore is None:
            raise ValueError("Vectorstore is not initialized")
        return self.vectorstore.as_retriever(**kwargs)

    @classmethod
    def clear_cache(cls):
        """Clear all cached vectorstores"""
        with cls._cache_lock:
            cls._vectorstore_cache.clear()
            cls._cache_metadata.clear()
            logging.info("Cleared all vectorstore caches")

    @classmethod
    def get_cache_stats(cls):
        """Get cache statistics"""
        with cls._cache_lock:
            return {
                "cached_vectorstores": len(cls._vectorstore_cache),
                "cache_keys": list(cls._cache_metadata.keys()),
                "total_hits": sum(
                    getattr(vs, "cache_hits", 0)
                    for vs in cls._vectorstore_cache.values()
                ),
                "total_misses": sum(
                    getattr(vs, "cache_misses", 0)
                    for vs in cls._vectorstore_cache.values()
                ),
            }
