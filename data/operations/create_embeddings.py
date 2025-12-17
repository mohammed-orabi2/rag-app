import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

with open("../data/processed/chroma_documents.json", "r", encoding="utf-8") as f:
    chroma_docs = json.load(f)

model_name = "intfloat/multilingual-e5-large-instruct"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": False}

embeddings = HuggingFaceEmbeddings(
    model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)


vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in chroma_docs
]
ids = [doc["id"] for doc in chroma_docs]

vector_store.add_documents(documents=documents, ids=ids)
