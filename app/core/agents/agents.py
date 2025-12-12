from multiprocessing import context
from app.core.src.models import *
from app.core.src.prompts import *
from app.core.retrievers.retrievers import *
from dotenv import load_dotenv
import asyncio
import os
from utils.logging_info import get_logger
from .llms import *
from utils.formatting_utils import streaming_helper, format_content
from app.config import vectorstore_config as config
from ..retrievers.search_params import child_parent_retriever_search_params
import re

logger = get_logger(__name__)
load_dotenv()

# Cache for ChildParentRetriever to avoid recreating it on every request
_child_parent_retriever_cache = None


def get_cached_child_parent_retriever():
    """
    Get or create a cached ChildParentRetriever instance.
    This avoids the expensive 8-9s initialization on every request.

    The first call will take ~9s (loading embeddings + initializing 3 vectorstores),
    but subsequent calls will be instant.
    """
    global _child_parent_retriever_cache

    if _child_parent_retriever_cache is None:
        logger.info("🔨 Creating new ChildParentRetriever instance (first time)")
        import time

        start = time.time()

        embeddings_name = config.embeddings_name
        json_dir = config.json_dir

        if not json_dir or not embeddings_name:
            logger.error("Missing configuration: json_dir or embeddings_name")
            raise ValueError("Configuration error: missing json_dir or embeddings_name")

        _child_parent_retriever_cache = ChildParentRetriever(
            os.getenv("grande_ecole"),
            os.getenv("ecole_specialisee"),
            os.getenv("specialization"),
            embeddings_name,
            json_dir,
        )

        elapsed = time.time() - start
        logger.info(f"✅ ChildParentRetriever cached (took {elapsed:.3f}s)")
    else:
        logger.info("✅ Using cached ChildParentRetriever instance (0.000s)")

    return _child_parent_retriever_cache


# Agents
# Each agent is implemented according to its specific order in the workflow.


async def rewrite_query_agent(state: State) -> dict:
    """
    Rewrite the query in the state based on the query type.
    """
    user_input = state.get("query", "")
    chat_history = state.get("messages", [])

    # formated_hist = convert_db_messages_to_langchain(chat_history)
    prompt = pull_prompt_from_langsmith("rewritten-query-prompt")
    combined_prompt = prompt.format_messages(
        user_input=user_input, chat_history=chat_history
    )

    try:
        rewritten_query = await llm_grok.ainvoke(combined_prompt)
        return {"rewritten_query": rewritten_query.content}
    except Exception as e:
        print(f"Error in rewrite_query: {e}")
        return None


async def query_classification_agent(state: State) -> dict:
    """
    Classify the user's query into four categories: program_selection, rules, follow_up, or general.
    Uses Gemini Flash - 5x faster than DeepSeek for classification tasks.
    """
    rewritten_query = state.get("rewritten_query", "")
    chat_history = state.get("messages", [])

    # ✅ Use fastest model for classification (Gemini Flash instead of DeepSeek)
    classifier_llm = deep_seek_chat.with_structured_output(FiveWayQueryClassifier)

    prompt = pull_prompt_from_langsmith("query-classifier-prompt-test")
    combined_prompt = prompt.format_messages(
        rewritten_query=rewritten_query, chat_history=chat_history
    )

    try:
        response = await classifier_llm.ainvoke(combined_prompt)
        return {"question_category": response.question_category}

    except Exception as e:
        print(f"Error in four_way_question_classifier_agent: {e}")
        return {"question_category": "general"}


async def general_question_agent(state: State) -> str:
    """
    Handle general questions by providing a logical response.
    """
    user_input = state.get("rewritten_query", "")
    chat_history = state.get("messages", [])

    prompt = pull_prompt_from_langsmith("general-question-prompt")
    combined_prompt = prompt.format_messages(
        user_input=user_input, chat_history=chat_history
    )
    try:
        full_response = await llm_4_1_mini.ainvoke(combined_prompt)
        return {"response": full_response}
    except Exception as e:
        print(f"Error in general_question_agent: {e}")
        return None


async def follow_up_agent(state: State) -> dict:
    """
    Handle follow-up questions and responses.
    """
    user_input = state.get("rewritten_query")
    chat_history = state.get("messages")
    prompt = pull_prompt_from_langsmith("follow-up-questions-prompt-test")
    combined_prompt = prompt.format_messages(
        user_input=user_input, chat_history=chat_history
    )
    try:
        full_response = await deep_seek_chat.ainvoke(combined_prompt)
        return {"response": full_response}
    except Exception as e:
        print(f"Error in follow_up_agent: {e}")
        return None


async def rules_agent(state: State) -> str:
    """
    Handle rules and system explanation questions.
    """
    user_input = state.get("rewritten_query", "")
    # chat_history = state.get("messages", [])

    # formatted_hist = convert_db_messages_to_langchain(chat_history)

    prompt = pull_prompt_from_langsmith("rules-agent-prompt")
    combined_prompt = prompt.format_messages(user_input=user_input)

    try:
        full_response = await deep_seek_chat.ainvoke(combined_prompt)
        return {"response": full_response}
    except Exception as e:
        logger.error(f"Error in rules_agent: {e}")
        return None


async def filter_parameters_extraction_agent(
    state: State,
) -> dict:
    """
    Async version: Run program extractor, price/campus extractor, retriever selection, and suggestion agents in parallel.
    Better for I/O-bound operations like API calls to LLMs.
    """
    user_input = state.get("rewritten_query", "")
    chat_history = state.get("messages", [])

    price_campus_extraction_prompt = pull_prompt_from_langsmith("price_prompt_test")
    price_campus_extraction_combined_prompt = (
        price_campus_extraction_prompt.format_messages(user_input=user_input)
    )
    price_campus_extraction_task = llm_4o_mini.with_structured_output(
        PriceCampusExtraction
    ).ainvoke(price_campus_extraction_combined_prompt)

    program_extraction_prompt = pull_prompt_from_langsmith("program-extraction-promopt-test") # TODO: test new prompt
    program_extraction_combined_prompt = program_extraction_prompt.format_messages(
        user_input=user_input
    )
    program_extraction_task = llm_4o_mini.with_structured_output(
        ProgramExtractionOutputV2
    ).ainvoke(program_extraction_combined_prompt)

    retriever_selection_prompt = pull_prompt_from_langsmith(
        "retriever-selection-prompt"
    )
    retriever_selection_combined_prompt = retriever_selection_prompt.format_messages(
        user_input=user_input, chat_history=chat_history
    )
    retriever_selection_task = llm_google_flash.with_structured_output(
        RetrieverIntentOutput
    ).ainvoke(retriever_selection_combined_prompt)

    entry_level = pull_prompt_from_langsmith("entry-level-prompt")
    entry_level_prompt = entry_level.format_messages(user_input=user_input)
    entry_level_task = llm_4o_mini.with_structured_output(
        EntryLevelPromptOutput
    ).ainvoke(entry_level_prompt)

    # ✅ Use optimized DeepSeek for extraction (512 tokens instead of 4048)

    (
        program_result,
        price_campus_result,
        retriever_result,
        entry_level_result,
    ) = await asyncio.gather(
        program_extraction_task,
        price_campus_extraction_task,
        retriever_selection_task,
        entry_level_task,
        return_exceptions=False,
    )

    combined_result = {}

    for name, result in {
        "program_type": {"program_type": program_result.program_type},
        "price_campus_info": {"price_campus_info": price_campus_result},
        "retriever_intent": {"retriever_intent": retriever_result.retriever_intent},
        "entry_level": {"entry_level": entry_level_result.entry_level},
    }.items():

        if isinstance(result, Exception):
            logger.error(f"{name} failed: {result}")
        elif result:
            combined_result.update(result)
    return combined_result


async def child_parent_retriever_agent(state: State) -> dict:
    """
    Two-Stage Retrieval: Retrieve 45 docs → Re-rank with LLM → Return top 12
    """
    try:
        json_dir = config.json_dir
        if not json_dir:
            logger.error("json_dir environment variable not set")
            return {"content": []}

        embeddings_name = config.embeddings_name
        if not embeddings_name:
            logger.error("embeddings_name environment variable not set")
            return {"content": []}

        rewritten_query = state.get("rewritten_query", "")
        program_type = state.get("program_type", [])
        excluded_ids = state.get("excluded_ids", [])
        price_campus_info = state.get("price_campus_info")
        entry_level = state.get("entry_level", [])

        # Retrieve 45 candidates (broad recall)
        k = 14
        retriever_intent = state.get("retriever_intent", "NEW")
        if retriever_intent == "NEW":
            exclude = True
        else:
            exclude = False

        # Use cached retriever instead of creating new one every time (saves 8-9s!)
        retriever = get_cached_child_parent_retriever()

        search_params = child_parent_retriever_search_params(
            program_type, k, excluded_ids, price_campus_info, entry_level, exclude
        )

        results = retriever.multiple_invoke(
            RetrieverConfig(
                rewritten_query=rewritten_query, search_params=search_params
            )
        )
        return {
            "content": results.get("content", [])
        }  # , "excluded_ids": results.get("ids")

    except Exception as e:
        logger.error(f"Error in child_parent_retriever_agent: {e}")
        return {"content": []}


async def sg_bot_agent(state: State) -> dict:
    """
    Handle SG Bot queries by providing a logical response with streaming support.
    This will work with your existing astream_events detection.
    """
    user_input = state.get("rewritten_query")
    chat_history = state.get("messages")
    content = state.get("content")
    formatted_content = format_content(content)

    prompt = pull_prompt_from_langsmith("system-prompt-test")

    combined_prompt = prompt.format_messages(
        user_input=user_input,
        chat_history=chat_history,
        content=formatted_content,
    )
    try:
        full_response = await streaming_helper.stream_llm_response(
            llm_grok,
            combined_prompt,
            config={"run_name": "SG Bot Query", "metadata": {"user_query": user_input}},
        )

        program_ids = re.findall(r"Program Id:\s*(\d+)", full_response)
        program_ids = [int(pid) for pid in program_ids]
        print(program_ids)
        return {"response": full_response, "excluded_ids": program_ids}

    except Exception as e:
        print(f"❌ Error in sg_bot_agent: {e}")
        # Return a fallback response instead of None
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try rephrasing your question or contact support if the issue persists.",
            "excluded_ids": [],
        }
