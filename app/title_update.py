from app.core.agents.llms import llm_google_flash
from app.api.services.message_services import MessageService
from app.core.src.prompts import pull_prompt_from_langsmith

# database import
# import the function that pull the prompt from langsmith "title-update-prompt"
# TODO: using it in the new api structure


def update_conversation_title_optimized(conversation_id, user_email):
    """Optimized version for API use"""
    message_service = MessageService()
    content = []
    for message in message_service.get_conversation_messages(
        conversation_id, user_email
    ):
        if message["role"] == "user":
            content.append(message["content"])

    content = content[:4]

    llm = llm_google_flash

    try:
        prompt = pull_prompt_from_langsmith("title-update-prompt")
        combined_prompt = prompt.format_messages(conversation_text=content)
        title = llm.invoke(combined_prompt).content
        return title if title != "No Title Yet" else "New Conversation"

    except Exception as e:
        return "New Conversation"
