from langsmith import Client
from app.config import langsmith_config as config
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Global cache for prompts
_prompt_cache: Dict[str, any] = {}
_langsmith_client: Optional[Client] = None


def get_langsmith_client() -> Client:
    """Get or create LangSmith client singleton"""
    global _langsmith_client
    if _langsmith_client is None:
        _langsmith_client = Client(api_key=config.api_key)
    return _langsmith_client


def preload_all_prompts():
    """
    Pre-load all prompts from LangSmith at application startup.
    This eliminates repeated API calls during request processing.
    """
    prompt_names = [
        "rewritten-query-prompt",
        "query-classifier-prompt",
        "general-question-prompt",
        "follow-up-questions-prompt",
        "rules-agent-prompt",
        "program-extraction-prompt",
        "retriever-selection-prompt",
        "title-update-prompt",
        "ai-summarize-prompt",
        "price_prompt_test",
        "excluded_ids_test_prompt",
        "entry-level-prompt",
        "program-extraction-promopt-test",
        "system-prompt-test",
        "query-classifier-prompt-test",
        "follow-up-questions-prompt-test"
        ""
    ]

    logger.info("🔥 Pre-loading prompts from LangSmith...")
    client = get_langsmith_client()

    loaded_count = 0
    failed_prompts = []

    for prompt_name in prompt_names:
        try:
            prompt = client.pull_prompt(prompt_name)
            if prompt is None:
                raise ValueError("Prompt not found in LangSmith")
            _prompt_cache[prompt_name] = prompt
            loaded_count += 1
            logger.info(f"  ✅ Loaded: {prompt_name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to load {prompt_name}: {e}")
            failed_prompts.append(prompt_name)

    logger.info(
        f"✅ Prompt pre-loading complete: {loaded_count}/{len(prompt_names)} loaded"
    )

    if failed_prompts:
        logger.warning(f"⚠️  Failed to load prompts: {', '.join(failed_prompts)}")

    return loaded_count, failed_prompts


def get_prompt(prompt_name: str):
    """
    Get a cached prompt. Falls back to pulling from LangSmith if not cached.

    Args:
        prompt_name: Name of the prompt in LangSmith

    Returns:
        The prompt object from cache or LangSmith
    """
    # Check cache first
    if prompt_name in _prompt_cache:
        return _prompt_cache[prompt_name]

    # Cache miss - pull from LangSmith and cache it
    logger.warning(f"⚠️  Cache miss for prompt: {prompt_name} - fetching from LangSmith")
    try:
        client = get_langsmith_client()
        prompt = client.pull_prompt(prompt_name)
        _prompt_cache[prompt_name] = prompt
        return prompt
    except Exception as e:
        logger.error(f"❌ Error pulling prompt {prompt_name}: {e}")
        return None


def pull_prompt_from_langsmith(prompt_name: str):
    """
    Pull prompt from cache (or LangSmith if not cached).
    Maintained for backward compatibility.
    """
    return get_prompt(prompt_name)


def clear_prompt_cache():
    """Clear the prompt cache (useful for testing or reloading)"""
    global _prompt_cache
    _prompt_cache.clear()
    logger.info("🗑️  Prompt cache cleared")


def get_cache_stats():
    """Get statistics about the prompt cache"""
    return {
        "cached_prompts": len(_prompt_cache),
        "prompt_names": list(_prompt_cache.keys()),
    }
