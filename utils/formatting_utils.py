from pyexpat.errors import messages
from langchain_core.messages import HumanMessage, AIMessage


def convert_db_messages_to_langchain(messages):
    history = []
    for message in messages:
        message = dict(message)  # Ensure it's a dictionary
        if message["role"] == "user":
            history.append(f'\nuser: {message["content"]}\n')
        elif message["role"] == "assistant":
            history.append(f'\nassistant summary: {message["summary"]}\n')
        else:
            history.append(message)
    return "".join(history)


def summarize_response(response_content: str) -> str:
    from app.core.src.prompts import pull_prompt_from_langsmith
    from app.core.agents.llms import deep_seek_chat
    from langsmith.run_helpers import tracing_context

    with tracing_context(enabled=False):
        llm = deep_seek_chat

        prompt = pull_prompt_from_langsmith("ai-summarize-prompt")
        combined_prompt = prompt.format_messages(ai_response=response_content)

        try:
            response = llm.invoke(combined_prompt)
            return response.content
        except Exception as e:
            print(f"Error in summarize_response: {e}")
            return (
                response_content[:200] + "..."
                if len(response_content) > 200
                else response_content
            )


def format_content(content):
    """
    Format the content fo better readability.
    """
    return "\n\n----\n\n".join([f"{item}" for item in content])


class StreamingHelper:
    @staticmethod
    async def stream_llm_response(llm, messages, config=None):
        """
        Unified streaming pattern for LLM responses.
        Returns the full accumulated response.
        """
        full_response = ""

        async for chunk in llm.astream(messages, config=config):
            if hasattr(chunk, "content") and chunk.content:
                full_response += chunk.content

        return full_response.strip()


streaming_helper = StreamingHelper()
