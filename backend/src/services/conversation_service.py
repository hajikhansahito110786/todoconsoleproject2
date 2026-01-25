from typing import List, Optional
from sqlmodel import Session, select
from ..models.conversation import Conversation, ConversationCreate, ConversationUpdate
from ..models.message import Message, MessageCreate


class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, conv_data: ConversationCreate, user_id: str) -> Conversation:
        """Create a new conversation for the given user"""
        conversation = Conversation(**conv_data.model_dump())
        conversation.user_id = user_id
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conv_id: str, user_id: str) -> Optional[Conversation]:
        """Get a specific conversation by ID for the given user"""
        conversation = self.session.exec(
            select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id)
        ).first()
        return conversation

    def get_conversations_by_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for the given user"""
        conversations = self.session.exec(
            select(Conversation).where(Conversation.user_id == user_id)
        ).all()
        return conversations

    def update_conversation(self, conv_id: str, conv_data: ConversationUpdate, user_id: str) -> Optional[Conversation]:
        """Update a specific conversation for the given user"""
        conversation = self.get_conversation_by_id(conv_id, user_id)
        if not conversation:
            return None
        
        update_data = conv_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def delete_conversation(self, conv_id: str, user_id: str) -> bool:
        """Delete a specific conversation for the given user"""
        conversation = self.get_conversation_by_id(conv_id, user_id)
        if not conversation:
            return False
        
        self.session.delete(conversation)
        self.session.commit()
        return True

    def add_message_to_conversation(self, conv_id: str, message_data: MessageCreate) -> Optional[Message]:
        """Add a message to a specific conversation"""
        # Verify the conversation exists and belongs to the user
        message = Message(**message_data.model_dump())
        message.conversation_id = conv_id
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def get_messages_for_conversation(self, conv_id: str, user_id: str) -> List[Message]:
        """Get all messages for a specific conversation belonging to the user"""
        messages = self.session.exec(
            select(Message)
            .join(Conversation)
            .where(Conversation.id == conv_id, Conversation.user_id == user_id)
        ).all()
        return messages