import json
from collections import defaultdict
from langchain_core.documents import Document

# from app.core.src.models import RetrieverConfig
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os


class ChildParentSplitter:
    """
    A class to split markdown content into parent and child documents based on headings.
    """

    def __init__(self, chroma_documents_path: str, heading: str):
        """
        Initialize the splitter with the path to the Chroma documents and the heading to split at.
        """
        self.heading = heading
        self.chroma_documents_path = chroma_documents_path
        self.chroma_documents = self._load_chroma_documents()
        self.full_content, self.children_content = self._split_markdown_at_heading()
        self.children_documents = list()
        # self.config = RetrieverConfig()

    def _load_chroma_documents(self):
        """
        Load Chroma documents from the specified path.
        """
        try:
            with open(self.chroma_documents_path, "r",encoding="utf-8") as f:
                return json.load(f)
            print(f"{self.chroma_documents_path} loaded successfully.")
        except FileNotFoundError:
            print(
                f"{self.chroma_documents_path} not found. Please ensure the file exists."
            )
            return []

    def _split_markdown_at_heading(self) -> str:
        """
        Split the markdown content at the specified heading and return everything before it.
        """

        full_content = defaultdict()
        children_content = defaultdict()
        for document in self.chroma_documents:
            markdown_content = document.get("page_content", "")
            doc_id = document.get("metadata", "")["id"]
            if not markdown_content:
                print(f"error: No page_content found in document {document}")
                break

            split_index = markdown_content.find(self.heading)
            full_content[doc_id] = markdown_content
            children_content[doc_id] = markdown_content[:split_index].strip()
        return full_content, children_content

    def create_child_documents(self):
        for original_document in self.chroma_documents:
            document = original_document.copy()
            id = original_document.get("metadata", "")["id"]
            document["page_content"] = self.children_content.get(id, "")
            self.children_documents.append(
                Document(
                    page_content=document["page_content"],
                    metadata=document.get("metadata", {}),
                )
            )

    def save_parent_documents(self, output_path: str):
        """
        Save the parent documents to the specified output path.
        Format: {"program_0001": "full content string", ...}
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.full_content, f, indent=4, ensure_ascii=False)

    def _convert_specializations_to_documents(self, specializations_list):
        """Convert specialization dicts to LangChain Document objects."""
        documents = []
        for spec in specializations_list:
            doc = Document(
                page_content=json.dumps(
                    spec.get("page_content", {}), ensure_ascii=False
                ),
                metadata=spec.get("metadata", {}),
            )
            documents.append(doc)
        return documents

    def create_vectorstore(self, persist_directory):
        model_name = "intfloat/e5-large"
        # model_name = self.config.embeddings_name
        model_kwargs = {"device": "cuda"}
        encode_kwargs = {"normalize_embeddings": False}

        # Use absolute path for specialization documents
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        spec_doc_path = os.path.join(
            project_root,
            "data",
            "chroma_documents",
            "specialization_chroma_documents.json",
        )

        with open(spec_doc_path, "r", encoding="utf-8") as f:
            specializations_raw = json.load(f)

        # Convert specializations to Document objects
        specializations_documents = self._convert_specializations_to_documents(
            specializations_raw
        )

        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        print(f"embeddings loaded: {embeddings}")

        programs_collection = Chroma(
            collection_name="program_selection",
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

        specializations_collection = Chroma(
            collection_name="specialization",
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

        # if collections are empty, add documents
        if len(programs_collection.get()["ids"]) == 0:
            print(
                f"adding {len(self.children_documents)} child documents to programs collection"
            )
            programs_collection.add_documents(documents=self.children_documents)
            print(f"child documents added to programs collection")

        if (
            specializations_documents
            and len(specializations_collection.get()["ids"]) == 0
        ):
            print(
                f"adding {len(specializations_documents)} specialization documents to specializations collection"
            )
            specializations_collection.add_documents(
                documents=specializations_documents
            )
            print(f"specialization documents added to specializations collection")

        return programs_collection, specializations_collection


if __name__ == "__main__":
    # Example usage
    print("\n" + "=" * 70)
    print("CHILD-PARENT DOCUMENT SPLITTER")
    print("=" * 70 + "\n")

    splitter = ChildParentSplitter(
        "data/chroma_documents/chroma_documents.json",
        "## 📅 Detailed Program Information",
    )
    splitter.create_child_documents()

    # Save parent documents for visual debugging
    splitter.save_parent_documents("data/parents/parent_documents.json")
    print(f"Saved {len(splitter.full_content)} parent documents")

    # Create vector store with both collections
    programs_coll, spec_coll = splitter.create_vectorstore(
        persist_directory="data/vector_store/combined_collections"
    )

    print(f"Child documents indexed: {len(programs_coll.get()['ids'])}")
    print(f"Specialization docs: {len(spec_coll.get()['ids'])}")
    print(f"Parent documents saved: data/parents/parent_documents.json")
