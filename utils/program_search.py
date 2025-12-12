#!/usr/bin/env python3
"""
Simple ChromaDB utility for the counselling bot.
Easy to use and integrate with existing systems.
"""

import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings


class ProgramSearcher:
    """Simple interface for searching educational programs."""

    def __init__(
        self,
        db_path: str = "./chroma_db",
        collection_name: str = "educational_programs",
    ):
        """Initialize the program searcher."""
        self.client = chromadb.Client(
            Settings(chroma_db_impl="duckdb+parquet", persist_directory=db_path)
        )
        self.collection_name = collection_name
        self.collection = None
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize or load the collection."""
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except:
            self.collection = self.client.create_collection(name=self.collection_name)

    def search(
        self,
        query: str,
        limit: int = 5,
        program_type: Optional[str] = None,
        school_type: Optional[str] = None,
        school_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for programs with optional filters.

        Args:
            query: Search query (e.g., "data science programs")
            limit: Maximum number of results to return
            program_type: Filter by program type (e.g., "MSc", "Bachelor")
            school_type: Filter by school type (e.g., "Grande Ecole")
            school_name: Filter by specific school

        Returns:
            List of matching programs with metadata and content
        """
        # Build filters
        filters = {}
        if program_type:
            filters["program_type"] = program_type
        if school_type:
            filters["school_type"] = school_type
        if school_name:
            filters["school_name"] = school_name

        # Perform search
        results = self.collection.query(
            query_texts=[query], n_results=limit, where=filters if filters else None
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            result = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity_score": 1
                - results["distances"][0][i],  # Convert distance to similarity
            }
            formatted_results.append(result)

        return formatted_results

    def get_program_types(self) -> List[str]:
        """Get all available program types."""
        # Get a sample of documents to extract program types
        sample = self.collection.get(limit=1000)  # Get more for better coverage
        program_types = set()

        for metadata in sample["metadatas"]:
            program_types.add(metadata.get("program_type", "Unknown"))

        return sorted(list(program_types))

    def get_school_types(self) -> List[str]:
        """Get all available school types."""
        sample = self.collection.get(limit=1000)
        school_types = set()

        for metadata in sample["metadatas"]:
            school_types.add(metadata.get("school_type", "Unknown"))

        return sorted(list(school_types))

    def count_programs(self) -> int:
        """Get total number of programs in the database."""
        return self.collection.count()


def setup_database(documents_json_file: str, db_path: str = "./chroma_db"):
    """
    One-time setup function to populate ChromaDB with program documents.

    Args:
        documents_json_file: Path to the JSON file with program documents
        db_path: Path where ChromaDB should store its data
    """
    print(f"🚀 Setting up ChromaDB with programs from {documents_json_file}")

    # Load documents
    with open(documents_json_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    # Initialize ChromaDB
    client = chromadb.Client(
        Settings(chroma_db_impl="duckdb+parquet", persist_directory=db_path)
    )

    # Create collection
    try:
        collection = client.get_collection(name="educational_programs")
        print("📂 Collection already exists, skipping setup")
        return
    except:
        collection = client.create_collection(name="educational_programs")
        print(f"🆕 Created new collection")

    # Add documents in batches
    batch_size = 100
    total_added = 0

    for i in range(0, len(documents), batch_size):
        batch_end = min(i + batch_size, len(documents))
        batch = documents[i:batch_end]

        ids = [doc["id"] for doc in batch]
        contents = [doc["page_content"] for doc in batch]
        metadatas = [doc["metadata"] for doc in batch]

        collection.add(documents=contents, metadatas=metadatas, ids=ids)

        total_added += len(batch)
        print(f"📥 Added {total_added}/{len(documents)} documents")

    print(f"✅ Database setup complete! Added {total_added} programs")


# Example usage functions
def search_examples():
    """Show example searches."""
    searcher = ProgramSearcher()

    print(f"📊 Database contains {searcher.count_programs()} programs")
    print(f"📚 Available program types: {searcher.get_program_types()}")
    print(f"🏫 Available school types: {searcher.get_school_types()}")

    # Example searches
    examples = [
        ("data science and AI", {"limit": 3}),
        ("business management", {"program_type": "MSc", "limit": 3}),
        ("fashion programs", {"limit": 3}),
        ("engineering", {"school_type": "Grande Ecole", "limit": 3}),
    ]

    for query, kwargs in examples:
        print(f"\n🔍 Searching: '{query}' with filters {kwargs}")
        results = searcher.search(query, **kwargs)

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['metadata']['school_name']}")
            print(f"     Type: {result['metadata']['program_type']}")
            print(f"     Similarity: {result['similarity_score']:.3f}")


if __name__ == "__main__":
    # Setup database (run once)
    documents_file = "/Users/omar/counselling-bot/data/processed/chroma_documents.json"
    setup_database(documents_file)

    # Show example searches
    search_examples()
