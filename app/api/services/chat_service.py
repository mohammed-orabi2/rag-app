from app.core.src.workflow import bot
from typing import Optional
import json
from app.api.services.conversation_services import ConversationService
from app.api.services.message_services import MessageService
from utils.formatting_utils import summarize_response


class ChatService:
    def __init__(self, conversation_id: str):
        self.bot = bot
        self.conversation_id = conversation_id
        self.conversation_service = ConversationService()
        self.message_service = MessageService()

    async def _get_conversation_messages(self):
        """Async helper to get conversation messages."""
        return await self.message_service.get_conversation_messages(
            self.conversation_id
        )

    async def _save_excluded_ids(self, agent_excluded_ids):
        try:
            await self.conversation_service.update_excluded_ids(
                self.conversation_id, agent_excluded_ids
            )

        except Exception as e:
            print(f"Error saving excluded_ids: {e}")
            return False

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        summary: Optional[str],
        rewritten_query: Optional[str] = None,
    ):
        try:
            await self.message_service.save_message(
                conversation_id, role, content, summary, rewritten_query
            )
        except Exception as e:
            pass

    async def _get_excluded_ids(self):
        result = await self.conversation_service.get_conversation(self.conversation_id)
        return result["conversation"].get("excluded_ids", [])

    async def stream_chat(self, user_input: str, username: str = None):
        full_response = ""
        try:
            # Get conversation messages asynchronously
            conversation_messages = await self._get_conversation_messages()
            excluded_ids = await self._get_excluded_ids()

            async for chunk in bot.stream_workflow(
                user_input, excluded_ids, conversation_messages, username=username
            ):
                if isinstance(chunk, str):
                    # Regular text chunk
                    full_response += chunk
                    escaped_chunk = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {escaped_chunk}\n\n"
                elif isinstance(chunk, dict):
                    # Skip internal control dict
                    if "__stream_complete__" not in chunk:
                        # Pass all other dicts to frontend (including metadata)
                        yield f"data: {json.dumps(chunk)}\n\n"

            # Get final metadata for saving to DB
            metadata = bot.get_stream_metadata()

            if metadata.get("completed"):
                rewritten_query = metadata.get("rewritten_query")
                agent_excluded_ids = metadata.get("excluded_ids")

                await self._save_excluded_ids(agent_excluded_ids)

                await self._save_message(
                    conversation_id=self.conversation_id,
                    role="user",
                    content=user_input,
                    summary=None,
                    rewritten_query=rewritten_query,
                )

                if full_response.strip():
                    try:
                        summary = summarize_response(full_response)
                    except Exception as e:
                        summary = (
                            full_response[:200] + "..."
                            if len(full_response) > 200
                            else full_response
                        )

                    await self._save_message(
                        conversation_id=self.conversation_id,
                        role="assistant",
                        content=full_response,
                        summary=summary,
                        rewritten_query=None,
                    )

            # Send completion signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_data = {"error": "Stream interrupted", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"
