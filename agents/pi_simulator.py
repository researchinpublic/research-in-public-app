"""PI Simulator Agent - Grant critique and mentorship."""

from typing import Optional
from loguru import logger

from agents.base_agent import BaseAgent
from config.prompts import PI_SIMULATOR_SYSTEM_PROMPT
from data.schemas import ConversationSession, ConversationMessage
from services.gemini_service import gemini_service


class PISimulatorAgent(BaseAgent):
    """PI Simulator Agent - Domain Specificity (Day 4)."""
    
    def __init__(self):
        """Initialize PI Simulator agent."""
        super().__init__(
            name="PI Simulator",
            system_prompt=PI_SIMULATOR_SYSTEM_PROMPT
        )
    
    def critique_grant(self, grant_text: str) -> str:
        """
        Provide critique on a grant proposal.
        
        Args:
            grant_text: Grant proposal text
            
        Returns:
            Constructive critique
        """
        try:
            prompt = f"""Review this grant proposal and provide constructive feedback:

{grant_text}

Provide:
1. Strengths of the proposal
2. Areas for improvement
3. Specific, actionable suggestions
4. How to strengthen broader impacts
5. Overall assessment

Be supportive but honest, like a good mentor."""

            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="pro",
                system_instruction=self.system_prompt,
                temperature=0.7
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in PI Simulator critique: {str(e)}")
            return "I'd be happy to review your grant proposal. Please share the text and I'll provide constructive feedback."
    
    def process(
        self,
        message: str,
        session: ConversationSession,
        **kwargs
    ) -> str:
        """
        Process message and provide PI-style feedback.
        
        Args:
            message: User message (grant proposal or research question)
            session: Conversation session
            **kwargs: Additional parameters
            
        Returns:
            PI-style feedback
        """
        try:
            # Provide general mentorship with clarity scoring
            messages = self.get_conversation_history(session)
            messages.append({
                "role": "user",
                "content": message
            })
            
            response = gemini_service.chat_completion(
                messages=messages,
                model_type="pro",
                system_instruction=self.system_prompt,
                temperature=0.7
            )
            
            # Metadata parsing is handled by orchestrator
            
            return response
            
        except Exception as e:
            logger.error(f"Error in PI Simulator: {str(e)}")
            return "I'm here to help with your research questions and grant proposals. What would you like feedback on?"

