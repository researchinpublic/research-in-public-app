"""Scribe Agent - Content drafting and sanitization."""

from typing import Optional, Dict, Any
from loguru import logger

from agents.base_agent import BaseAgent
from config.prompts import SCRIBE_SYSTEM_PROMPT
from data.schemas import ConversationSession, SocialDraft
from services.gemini_service import gemini_service
from tools.social_draft import draft_social_content


class ScribeAgent(BaseAgent):
    """Agent 3: The Scribe - Public Bridge."""
    
    def __init__(self):
        super().__init__(
            name="The Scribe",
            system_prompt=SCRIBE_SYSTEM_PROMPT
        )
    
    def detect_shareable_moment(self, conversation_text: str) -> bool:
        keywords = [
            "learned", "realized", "understood", "breakthrough",
            "finally worked", "figured out", "resolved", "overcame"
        ]
        
        text_lower = conversation_text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def extract_insight(self, conversation_text: str) -> Dict[str, str]:
        prompt = f"""Extract the key insight and emotional tone from this research conversation:

{conversation_text}

Provide:
1. Main topic/lesson learned (one sentence)
2. Emotional tone (e.g., resilient, reflective, hopeful, determined)

Format as:
Topic: [topic]
Mood: [mood]"""

        try:
            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="flash",
                temperature=0.5
            )
            
            # Parse response
            topic = ""
            mood = "reflective"
            
            for line in response.split("\n"):
                if line.startswith("Topic:"):
                    topic = line.replace("Topic:", "").strip()
                elif line.startswith("Mood:"):
                    mood = line.replace("Mood:", "").strip()
            
            return {
                "topic": topic or "Research resilience and learning",
                "mood": mood or "reflective"
            }
        except Exception as e:
            logger.error(f"Error extracting insight: {str(e)}")
            return {
                "topic": "Research resilience",
                "mood": "reflective"
            }
    
    def process(
        self,
        message: str,
        session: ConversationSession,
        **kwargs
    ) -> str:
        """
        Process conversation and draft public content if appropriate.
        
        Args:
            message: User message
            session: Conversation session
            **kwargs: Additional parameters
            
        Returns:
            Draft suggestion or empty string
        """
        try:
            message_lower = message.lower()
            explicit_request = any(kw in message_lower for kw in [
                "post", "draft", "help me draft", "create a post", 
                "write a post", "shareable", "public", "linkedin", "social media",
                "announce", "acceptance", "published", "share my", "share the", "news"
            ])
            
            recent_messages = session.messages[-5:]
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in recent_messages
            ])
            
            if not explicit_request and not self.detect_shareable_moment(conversation_text):
                return ""
            
            draft = None
            
            if explicit_request:
                from agents.guardian import GuardianAgent
                
                guardian = GuardianAgent()
                guardian_report = guardian.scan_content(conversation_text)
                
                draft = draft_social_content(
                    raw_text=conversation_text,
                    platform="linkedin",
                    guardian_findings=guardian_report
                )
            else:
                insight = self.extract_insight(conversation_text)
                
                draft = draft_social_content(
                    topic=insight["topic"],
                    mood=insight["mood"],
                    platform="linkedin"
                )
            
            if not draft or not draft.get('content'):
                logger.warning("Failed to generate draft content")
                return ""
            
            return (
                "\n\n**The Scribe has drafted a post for you:**\n\n" +
                f"{draft['content']}\n\n" +
                f"Hashtags: {' '.join(draft['hashtags'])}\n\n" +
                "Would you like to review and share this?"
            )
            
        except Exception as e:
            logger.error(f"Error in Scribe: {str(e)}")
            return ""

