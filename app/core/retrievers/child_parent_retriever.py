from langchain_chroma import Chroma
from app.core.retrievers.child_parent_splitter import ChildParentSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from functools import lru_cache
from app.core.src.models import RetrieverConfig, State

# Caches for embeddings models and vectorstores
_EMBEDDINGS_CACHE = {}
_VECTORSTORE_CACHE = {}

heading = "## 📅 Detailed Program Information"


@lru_cache(maxsize=5)  # Cache the last 5 embedding model configurations
def get_embeddings(model_name: str):
    """Get embeddings model, using cache if available."""
    if model_name not in _EMBEDDINGS_CACHE:
        print(f"Loading embeddings model: {model_name}")
        _EMBEDDINGS_CACHE[model_name] = HuggingFaceEmbeddings(model_name=model_name)
    return _EMBEDDINGS_CACHE[model_name]


def get_vectorstore(
    chroma_documents_path,
    persist_directory: str,
    embedding_function,
    child_parent_splitter: bool = True,
):
    """Get vectorstore, using cache if available."""
    cache_key = f"{persist_directory}_{id(embedding_function)}"
    if cache_key not in _VECTORSTORE_CACHE:
        if child_parent_splitter:
            splitter = ChildParentSplitter(chroma_documents_path, heading)
            splitter.create_child_documents()
            print(f"Loading vectorstore from: {persist_directory}")
            _VECTORSTORE_CACHE[cache_key] = splitter.create_vectorstore(
                persist_directory
            )
        else:
            print(
                f"Loading vectorstore without child-parent splitting from: {persist_directory}"
            )
            _VECTORSTORE_CACHE[cache_key] = Chroma(
                embedding_function=embedding_function,
                persist_directory=persist_directory,
            )
    return _VECTORSTORE_CACHE[cache_key]


def create_child_retriever(state: State):
    """
    Create a retriever that splits documents into parent and child documents based on a specified heading.
    """
    config = RetrieverConfig()
    filter_keyword = state.get("program_type")
    print(filter_keyword)

    # Use dynamic k if available, otherwise fall back to config k, then default
    dynamic_k = state.get("dynamic_k")
    k_value = dynamic_k if dynamic_k is not None else (config.k if config.k else 5)

    print(f"Using k value: {k_value} (dynamic: {dynamic_k is not None})")

    embeddings = get_embeddings(config.embeddings_name)
    vectorstore = get_vectorstore(config.persist_directory, embeddings)

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
    return retriever


def create_filtered_retriever(
    persist_directory: str,
    state: State,
    excluder: bool = False,
    exclude_ids: list = None,
    child_parent_splitter: bool = True,
):
    """
    Create a retriever for Grande Ecole documents.
    """
    config = RetrieverConfig()
    embeddings = get_embeddings(config.embeddings_name)
    vectorstore = get_vectorstore(
        "data/processed/chroma_documents.json",
        persist_directory,
        embeddings,
        child_parent_splitter,
    )
    filter_keyword = state.get("program_type")
    price_campus_info = state.get("price_campus_info")

    # Use dynamic k if available, otherwise fall back to config k, then default
    dynamic_k = state.get("dynamic_k")
    k_value = dynamic_k if dynamic_k is not None else (config.k if config.k else 10)

    if filter_keyword and not excluder :
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": k_value,
                "filter": {"program_type": {"$in": filter_keyword}},
            },
        )
    else:
        filter_conditions = []

        if exclude_ids and excluder:
            filter_conditions.append({"id": {"$nin": exclude_ids}})

        if filter_keyword:
            filter_conditions.append({"program_type": {"$in": filter_keyword}})
        
        if price_campus_info['price']:
            if price_campus_info['price_condition'] == 'gt':
                filter_conditions.append({"price": {"$gt": price_campus_info['price']}})
            elif price_campus_info['price_condition'] == 'lte':
                filter_conditions.append({"price": {"$lte": price_campus_info['price']}})

        if price_campus_info['campus']:
            filter_conditions.append({"campus": {"$in": price_campus_info['campus']}})

        # Only apply filter if there are actual filter criteria
        if filter_conditions:
            # If multiple conditions, use $and operator for ChromaDB
            if len(filter_conditions) > 1:
                filters = {"$and": filter_conditions}
            else:
                filters = filter_conditions[0]

            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "k": k_value,
                    "filter": filters,
                },
            )
        else:
            # No filters to apply, use basic retriever
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "k": k_value,
                },
            )
    return retriever
