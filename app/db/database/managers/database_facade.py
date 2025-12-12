from app.db.database.managers.conversation_manager import ConversationManager
from app.db.database.managers.message_manager import MessageManager
from app.db.database.managers.user_manager import UserManager
from bson import ObjectId
from typing import List, Optional
from utils.logging_info import get_logger
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.feedback_repository import FeedbackRepository


user_repo = UserRepository()
convo_repo = ConversationRepository()
message_repo = MessageRepository()
feedback_repo = FeedbackRepository()

# TODO: decide the flow of conversation title so it can be implmented


class DatabaseFacade:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.message_manager = MessageManager()
        self.user_manager = UserManager()
        self.logger = get_logger()

    # User Management
    def create_user(self, username: str, email: str) -> str:
        return self.user_manager.create_user(username, email, user_repo)

    def login_user(self, email: str) -> dict:
        return self.user_manager.login_user(email, user_repo)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        return self.user_manager.get_user_by_email(email, user_repo)

    def get_all_users(self) -> List[dict]:
        """Get all users."""
        return self.user_manager.get_all_users(user_repo)

    # Conversation Management
    def create_conversation(self, user_id: str, title: str = None) -> dict:
        return self.conversation_manager.create_conversation(user_id, convo_repo, title)

    def get_user_conversations(self, user_id: str) -> dict:
        """Get all conversations for a user."""
        return self.conversation_manager.get_user_conversations(user_id, convo_repo)

    def get_conversation(self, conversation_id: str, user_id: str) -> dict:
        """Get a specific conversation for a user."""
        return self.conversation_manager.get_conversation(
            conversation_id, user_id, convo_repo
        )

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its messages."""
        return self.conversation_manager.delete_conversation(
            conversation_id, user_id, convo_repo
        )

    # Message Management
    def send_message(
        self, conversation_id: str, role: str, content: str, **kwargs
    ) -> dict:
        return self.message_manager.send_message(
            message_repo, conversation_id, role, content, **kwargs
        )

    def update_message_summary(self, message_id: str, summary: str) -> bool:
        """Update the summary of a message."""
        return self.message_manager.update_message_summary(
            message_id, summary, message_repo
        )

    def update_message_content(self, message_id: str, content: str) -> bool:
        """Update the content of a message."""
        return self.message_manager.update_message_content(
            message_id, content, message_repo
        )

    # operations requires two managers

    def create_new_chat(self, user_email: str, title: str = "New Chat") -> dict:
        """Create a new conversation for the user."""
        user = self.get_user_by_email(user_email)
        if not user:
            return {"success": False, "message": "User not found"}

        result = self.create_conversation(user["_id"], title)

        if result["success"]:
            return {
                "success": True,
                "conversation_id": result["conversation_id"],
                "message": result["message"],
            }

        return {"success": False, "message": "Failed to create conversation"}

    def load_conversation(self, conversation_id: str, user_email: str) -> dict:
        """Load a specific conversation with its metadata."""
        try:
            # Get user first
            user = self.get_user_by_email(user_email)
            if not user:
                return {"success": False, "message": "User not found"}
            # Get conversation metadata
            conversation = self.conversation_manager.get_conversation(
                conversation_id, user["_id"], convo_repo
            )
            if not conversation:
                return {
                    "success": False,
                    "message": "Conversation not found or access denied",
                }

            # Convert ObjectId to string for JSON serialization
            conversation["_id"] = str(conversation["_id"])

            return {"success": True, "conversation": conversation}
        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return {"success": False, "message": "Error loading conversation"}

    def get_user_dashboard(self, email: str) -> dict:
        """Get user info and conversations for dashboard."""
        user = self.get_user_by_email(email)
        if not user:
            return {"success": False, "message": "User not found"}

        conversations = self.conversation_manager.get_user_conversations(
            user["_id"], convo_repo
        )

        return {"success": True, "user": user, "conversations": conversations}

    def get_conversation_messages(
        self, conversation_id: str, user_id: str
    ) -> List[dict]:
        """Get all messages for a conversation if user owns it."""
        try:
            conversation = self.conversation_manager.get_conversation(
                conversation_id, user_id, convo_repo
            )
            if not conversation:
                return []

            # Get messages
            messages = self.message_manager.get_conversation_messages(
                conversation_id, message_repo
            )

            # Convert ObjectId to string for JSON serialization
            for msg in messages:
                if isinstance(msg.get("_id"), ObjectId):
                    msg["_id"] = str(msg["_id"])

            return messages
        except Exception as e:
            self.logger.error(f"Error getting messages: {e}")
            return []

    def _maybe_update_conversation_title(
        self, conversation_id: str, first_message: str, user_id: str
    ):
        """Update conversation title based on first message if title is default."""
        try:
            # Check if the conversation has the default title
            conversation = self.conversation_manager.get_conversation(
                conversation_id, user_id, convo_repo
            )
            if not conversation:
                return

            default_titles = ["New Chat", "New Session", "New Conversation"]
            if conversation.get("title") in default_titles:
                # Generate a simple title from the first few words of the message
                words = first_message.split()[:4]  # Take first 4 words
                new_title = " ".join(words)
                if len(new_title) > 50:
                    new_title = new_title[:47] + "..."

                # Ensure we have a non-empty title
                if new_title.strip():
                    self.conversation_manager.update_conversation_title(
                        conversation_id, user_id, new_title, convo_repo
                    )
                    self.logger.info(f"Updated conversation title to: {new_title}")
        except Exception as e:
            self.logger.error(f"Error updating conversation title: {e}")


database_facade = DatabaseFacade()


print("Database object IDs:")
# print(f"ConversationManager DB: {id(database_facade.conversation_manager.db)}")
# print(f"MessageManager DB:      {id(database_facade.message_manager.db)}")
# print(f"UserManager DB:         {id(database_facade.user_manager.db)}")
