from utils.formatting_utils import chat_formatter


# Re-export for backward compatibility
def get_summarized_chat_history(conversation_id: str):
    """Get chat history with summaries for more efficient context usage"""
    return chat_formatter.get_summarized_chat_history(conversation_id)


def summarize_response(response_content: str) -> str:
    """
    Summarize a response using the LLM.
    """
    return chat_formatter.summarize_response(response_content)
