"""Base agent class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger

from data.schemas import ConversationMessage, ConversationSession


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        logger.info(f"Initialized agent: {self.name}")
    
    @abstractmethod
    def process(
        self,
        message: str,
        session: ConversationSession,
        **kwargs
    ) -> str:
        pass
    
    def get_conversation_history(
        self,
        session: ConversationSession,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        messages = []
        
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        recent_messages = session.messages[-max_messages:]
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages

