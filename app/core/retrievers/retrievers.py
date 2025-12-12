from .retriever_interface import *
from .basic_vectorstore import BasicVectorstore
import json
import ast


def format_program_for_context(program_dict):
    """
    Format a program dictionary into a structured context for LLM.
    Separates program header from year details with clear dividers.
    Includes all year entries (even with program_intake: None) as they contain important info like price.
    """
    # Program Header
    program = program_dict.get("program", "Unknown")
    description = program_dict.get("program_description", "N/A")
    school = program_dict.get("school", "Unknown")
    accreditations = program_dict.get("school_accreditations", [])
    program_id = program_dict.get("program_id", "N/A")
    school_logo = program_dict.get("school_logo", "N/A")
    school_rank = program_dict.get("school_rank", "un ranked")
    program_name_header = f"Program: {program}\n\n"

    header = f"{{'school_logo': {school_logo}, 'program': '{program}', 'program_description': {description}, 'school': '{school}', 'school rank': '{school_rank}', 'school_accreditations': {accreditations}, 'program_id': {program_id}}}"

    formatted_parts = [program_name_header, header]

    # Get year_details
    year_details = program_dict.get("year_details", {})

    # Process each year
    for year_key in ["year_1", "year_2", "year_3", "year_4", "year_5"]:
        if year_key not in year_details:
            continue

        year_data = year_details[year_key]

        # Include ALL entries (no filtering) - they all contain important information
        # This includes entries with program_intake: None which still have price, campus, etc.
        if year_data:
            # Rename 'program_intake' to 'year_intake' in each entry
            modified_year_data = []
            for entry in year_data:
                entry_copy = entry.copy()
                if "program_intake" in entry_copy:
                    entry_copy["year_intake"] = entry_copy.pop("program_intake")
                modified_year_data.append(entry_copy)

            year_section = f"\n---------------------------------------------------------------------------------------------------------------------------\n\n'{year_key}': {modified_year_data}"
            formatted_parts.append(year_section)

    # Add remaining fields at the end
    footer_fields = [
        "campuses",
        "languages",
        "school_type",
        "field",
        "program_type",
        "program_link",
    ]
    footer = []
    for field in footer_fields:
        if field in program_dict:
            value = program_dict[field]
            if isinstance(value, str):
                footer.append(f"'{field}': '{value}'")
            else:
                footer.append(f"'{field}': {value}")

    if footer:
        formatted_parts.append(
            f"\n---------------------------------------------------------------------------------------------------------------------------\n\n{', '.join(footer)}"
        )

    return "".join(formatted_parts)


class FilterRetriever(RetrieverInterface):
    def __init__(
        self,
        collection_name: str,
        embedding_name: str,
    ):
        """
        a vector store wrapper.

        Args:
             - collection_name, str: name of the collection in vector store
             - embedding_name, str: name of embedding model
        """
        self.collection_name = collection_name
        self.embedding_name = embedding_name
        try:
            self.vectorstore_wrapper = BasicVectorstore(collection_name, embedding_name)
            self.vectorstore = (
                self.vectorstore_wrapper.get_vectorstore()
            )  # ✅ Get the actual Chroma vectorstore
        except Exception as e:
            print(f"⚠️ Warning: Failed to initialize vectorstore: {e}")
            self.vectorstore_wrapper = None
            self.vectorstore = None

    # ✅ Rest of the methods remain the same...
    def invoke(self, config: RetrieverConfig):
        """
        returns documents from retriever

        Args:
            - config, RetrieverConfig: holds the args for the retriever

        Returns:
            - {'content': result}, result is the output of the retriever
        """
        search_params = config.search_params
        rewritten_query = config.rewritten_query

        try:
            # get all keyword args from config and pass to retriever
            retriever = self.vectorstore.as_retriever(**search_params)

        except Exception as e:
            print(f"⚠️ Warning: Failed to create retriever: {e}")
            # Fallback to basic retriever without filters
            try:
                retriever = self.vectorstore.as_retriever(
                    search_kwargs={
                        "k": config.search_params.get("search_kwargs", {}).get("k", "")
                        or 10
                    }
                )
            except Exception as e2:
                print(f"⚠️ Warning: Failed to create basic retriever: {e2}")
                retriever = None

        if self.vectorstore is None or retriever is None:
            print("⚠️ Warning: Retriever not available, returning empty results")
            return {"content": []}

        try:
            results = retriever.invoke(rewritten_query)
            return {"content": results}
        except Exception as e:
            print(f"⚠️ Warning: Retrieval failed: {e}")
            return {"content": []}

    def multiple_invoke(self, config: RetrieverConfig):
        pass


class ChildParentRetriever(RetrieverInterface):
    def __init__(
        self,
        grande_ecole,
        ecole_specialisee,
        specialization,
        embedding_name,
        parent_json_dir,
    ):
        """
        Vector store wrapper with custom logic

        Args:
            - program_selection, str: name of the main program collection
            - specialization, str: name of the specialization collection
            - embedding_name, str: name of the embedding model
            - parent_json_dir, str: directory of the parent json file
            - specialization_collection, str: name of the specialization collection (optional)
        """
        self.grande_ecole = grande_ecole
        self.ecole_specialisee = ecole_specialisee
        self.specialization = specialization
        self.embedding_name = embedding_name

        self.grande_ecole_retriever = FilterRetriever(
            self.grande_ecole, self.embedding_name
        )
        self.ecole_specialisee_retriever = FilterRetriever(
            self.ecole_specialisee, self.embedding_name
        )
        self.specialization_retriever = FilterRetriever(
            self.specialization, self.embedding_name
        )
        self.parent_json_directory = parent_json_dir

    def invoke(self, config: RetrieverConfig):
        """
        Args:
            - config, RetrieverConfig: holds the args for the retriever

        Returns:
            - {'content': result}, result is the output of the retriever
        """
        rewritten_query = config.rewritten_query
        search_params = config.search_params

        try:
            children_result = self.full_retriever.invoke(
                RetrieverConfig(
                    rewritten_query=rewritten_query, search_params=search_params
                )
            )

            # Extract content from the result
            children_docs = (
                children_result.get("content", []) if children_result else []
            )

            with open(self.parent_json_directory, "r", encoding="utf-8") as f:
                parent_data = json.load(f)

            ids = [doc.metadata["program_id"] for doc in children_docs]

            results = []
            for doc_id, document in parent_data.items():
                if doc_id in ids:
                    # Format the program dictionary for better LLM context
                    formatted_program = format_program_for_context(document)
                    results.append(formatted_program)

            return {"content": results, "ids": ids}

        except Exception as e:
            print(f"⚠️ Warning: ChildParentRetriever invoke failed: {e}")
            return {"content": []}

    def multiple_invoke(self, config: RetrieverConfig):
        """
        Args:
             - config, RetrieverConfig: holds the args for the retriever: rewritten query, search type, and search kwargs

        Returns:
            - {'content': result}, result is the output of the retriever
        """
        rewritten_query = config.rewritten_query
        search_params = config.search_params

        try:
            grande_ecole_result = self.grande_ecole_retriever.invoke(
                RetrieverConfig(
                    rewritten_query=rewritten_query, search_params=search_params
                )
            )
            ecole_specialisee_result = self.ecole_specialisee_retriever.invoke(
                RetrieverConfig(
                    rewritten_query=rewritten_query, search_params=search_params
                )
            )
            specialization_result = self.specialization_retriever.invoke(
                RetrieverConfig(
                    rewritten_query=rewritten_query, search_params=search_params
                )
            )

            # Extract content from the results
            children_docs = (
                grande_ecole_result.get("content", []) if grande_ecole_result else []
            )
            children_docs.extend(
                specialization_result.get("content", [])
                if specialization_result
                else []
            )
            children_docs.extend(
                ecole_specialisee_result.get("content", [])
                if ecole_specialisee_result
                else []
            )

            with open(self.parent_json_directory, "r", encoding="utf-8") as f:
                parent_docs = json.load(f)

            ids = [str(doc.metadata["program_id"]) for doc in children_docs]

            results = []
            for doc_id, document in parent_docs.items():
                if doc_id in set(ids):
                    # Format the program dictionary for better LLM context
                    formatted_program = format_program_for_context(document)
                    results.append(formatted_program)

            return {"content": results, "ids": ids}

        except Exception as e:
            print(f"⚠️ Warning: ChildParentRetriever multiple_invoke failed: {e}")
            return {"content": []}
