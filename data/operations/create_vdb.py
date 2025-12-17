import json
from collections import defaultdict
from langchain_core.documents import Document

# from app.core.src.models import RetrieverConfig
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

ge_path = "data/chroma_documents/chroma_documents_ge.json"
es_path = "data/chroma_documents/chroma_documents_es.json"
specialization_path = "data/chroma_documents/chroma_documents_specializations.json"


def convert_to_documents(documents_list):
    """Convert dicts to LangChain Document objects."""
    documents = []
    for doc in documents_list:
        document = Document(
            page_content=json.dumps(doc.get("page_content", {}), ensure_ascii=False),
            metadata=doc.get("metadata", {}),
        )
        documents.append(document)
    return documents


def create_vectorstore(persist_directory):
    model_name = "intfloat/multilingual-e5-large-instruct"
    model_kwargs = {"device": "cpu", "trust_remote_code": True}
    encode_kwargs = {"normalize_embeddings": False}

    # loadd Grande Ecole programs
    with open(ge_path, "r", encoding="utf-8") as f:
        ge_programs_raw = json.load(f)

    # load Ecole Spécialisée programs
    with open(es_path, "r", encoding="utf-8") as f:
        es_programs_raw = json.load(f)

    # Load specialization documents
    with open(specialization_path, "r", encoding="utf-8") as f:
        specializations_raw = json.load(f)

    # Convert to Document objects
    ge_documents = convert_to_documents(ge_programs_raw)
    es_documents = convert_to_documents(es_programs_raw)
    specializations_documents = convert_to_documents(specializations_raw)

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )
    print(f"embeddings loaded: {embeddings}")

    ge_collection = Chroma(
        collection_name="grande_ecole",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    es_collection = Chroma(
        collection_name="ecole_specialisee",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    specializations_collection = Chroma(
        collection_name="specialization",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    # Add documents if collections are empty
    if len(ge_collection.get()["ids"]) == 0:
        print(f"adding {len(ge_documents)} Grande Ecole programs")
        ge_collection.add_documents(documents=ge_documents)
        print("Grande Ecole programs added")

    if len(es_collection.get()["ids"]) == 0:
        print(f"adding {len(es_documents)} Ecole Spécialisée programs")
        es_collection.add_documents(documents=es_documents)
        print("Ecole Spécialisée programs added")

    if len(specializations_collection.get()["ids"]) == 0:
        print(f"adding {len(specializations_documents)} specializations")
        specializations_collection.add_documents(documents=specializations_documents)
        print("Specializations added")

    return ge_collection, es_collection, specializations_collection


if __name__ == "__main__":
    print("CREATING VECTOR STORES")

    ge_coll, es_coll, spec_coll = create_vectorstore(
        persist_directory="data/vector_store/combined_collections"
    )

    print(f"\nGrande Ecole programs indexed: {len(ge_coll.get()['ids'])}")
    print(f"Ecole Spécialisée programs indexed: {len(es_coll.get()['ids'])}")
    print(f"Specialization documents indexed: {len(spec_coll.get()['ids'])}")
    print("Vector stores created successfully!")
