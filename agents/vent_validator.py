"""Vent Validator Agent - Emotional support and active listening."""

from typing import Optional
from loguru import logger

from agents.base_agent import BaseAgent
from config.prompts import VENT_VALIDATOR_SYSTEM_PROMPT
from data.schemas import ConversationSession, ConversationMessage
from services.gemini_service import gemini_service
from data.agent_models import VentResponse


class VentValidatorAgent(BaseAgent):
    """Agent 1: Vent Validator - Emotional Core."""
    
    def __init__(self):
        super().__init__(
            name="Vent Validator",
            system_prompt=VENT_VALIDATOR_SYSTEM_PROMPT
        )
    
    def process(
        self,
        message: str,
        session: ConversationSession,
        **kwargs
    ) -> str:
        try:
            messages = self.get_conversation_history(session)
            
            system_instruction = None
            if messages and messages[0].get("role") == "system":
                system_instruction = messages[0]["content"]
                messages = messages[1:]
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            structured_response = gemini_service.generate_structured(
                messages=messages,
                response_schema=VentResponse,
                model_type="flash",
                system_instruction=system_instruction,
                temperature=0.7
            )
            
            if isinstance(structured_response, VentResponse):
                return structured_response
            
            if isinstance(structured_response, dict):
                 return VentResponse(**structured_response)
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in Vent Validator: {str(e)}")
            return "I'm here to listen. Could you tell me more about what you're experiencing?"

