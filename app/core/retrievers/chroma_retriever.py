from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.src.models import RetrieverConfig, State
from functools import lru_cache
import chromadb
from app.config.vectorstore_config import VectorStoreConfig

# Caches for embeddings models and vectorstores
_EMBEDDINGS_CACHE = {}
_VECTORSTORE_CACHE = {}
_CHROMA_CLIENT = None


@lru_cache(maxsize=5)  # Cache the last 5 embedding model configurations
def get_embeddings(model_name: str):
    """Get embeddings model, using cache if available."""
    if model_name not in _EMBEDDINGS_CACHE:
        print(f"Loading embeddings model: {model_name}")
        _EMBEDDINGS_CACHE[model_name] = HuggingFaceEmbeddings(model_name=model_name)
    return _EMBEDDINGS_CACHE[model_name]


def get_chroma_client():
    """Get Chroma client, using cache if available."""
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        try:
            _CHROMA_CLIENT = chromadb.HttpClient(
                host=VectorStoreConfig.CHROMA_HOST, port=VectorStoreConfig.CHROMA_PORT
            )
            # Test connection
            _CHROMA_CLIENT.heartbeat()
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Chroma server at {VectorStoreConfig.CHROMA_HOST}:{VectorStoreConfig.CHROMA_PORT}: {e}"
            )
    return _CHROMA_CLIENT


def get_vectorstore(collection_name: str, embedding_function):
    """Get vectorstore, using cache if available."""
    cache_key = f"{collection_name}_{id(embedding_function)}"
    if cache_key not in _VECTORSTORE_CACHE:
        print(f"Connecting to Chroma collection: {collection_name}")
        client = get_chroma_client()

        try:
            # Verify collection exists
            client.get_collection(name=collection_name)
        except Exception:
            raise ValueError(
                f"Collection '{collection_name}' does not exist on Chroma server"
            )

        _VECTORSTORE_CACHE[cache_key] = Chroma(
            client=client,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )
    return _VECTORSTORE_CACHE[cache_key]


def create_retriever(state: State):
    """
    Function to create retriever with filter criteria.
    ARGS:
        config: RetrieverConfig object containing configuration parameters
    RETURNS:
        retriever: A retriever instance configured with the specified parameters.
    """
    config = RetrieverConfig()
    filter_keyword = state.get("program_type")
    print(filter_keyword)

    # Use dynamic k if available, otherwise fall back to config k, then default
    dynamic_k = state.get("dynamic_k")
    k_value = dynamic_k if dynamic_k is not None else (config.k if config.k else 5)

    print(f"Using k value: {k_value} (dynamic: {dynamic_k is not None})")

    # Use cached embeddings and vectorstore instead of creating new instances
    embeddings = get_embeddings(config.embeddings_name)
    vectorstore = get_vectorstore(config.collection_name, embeddings)
    if config.apply_filter:
        # Case 1: Use filter_keyword if provided
        if filter_keyword:
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": k_value,
                    "filter": {"program_type": {"$in": filter_keyword}},
                    "lambda_mult": 0.7,
                },
            )
        # Case 2: No filter criteria but apply_filter is True
        else:
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "filter": {
                        "program_type": {
                            "$in": [
                                "less selective master",
                                "Mastère Spécialisé®",
                                "MSc",
                                "BBA",
                                "Other",
                                "Bachelor",
                                "MBA",
                                "Cycle Préparatoire",
                                "BTS",
                            ]
                        }
                    },
                    "k": k_value,
                }
            )
    # Case 3: No filtering at all
    else:
        retriever = vectorstore.as_retriever(
            search_kwargs={"filter": {"program_type": {"$eq": ""}}, "k": k_value}
        )
    return retriever
