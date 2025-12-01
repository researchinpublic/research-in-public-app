"""Intent classifier to determine message type and appropriate agent."""

from typing import Dict, Literal
from loguru import logger

from services.gemini_service import gemini_service


class IntentClassifier:
    """Classifies user messages to determine appropriate agent routing."""
    
    INTENT_PROMPT = """Analyze this message and classify its intent. Consider:
1. Is this an emotional struggle or venting?
2. Is this a technical/academic discussion?
3. Is this a positive achievement or something to share?
4. Is this asking for grant/research feedback?

Message: "{message}"

Respond with ONLY one of these labels:
- "emotional": User is venting, struggling, or needs emotional support
- "technical": Technical discussion, asking questions, sharing knowledge
- "positive": Positive achievements, acceptance news, milestones (route to Scribe)
- "grant": Asking for grant/proposal feedback or mentorship
- "shareable": Contains insights or news that should be shared publicly

Label:"""

    def classify(self, message: str) -> Dict[str, any]:
        """
        Classify message intent.
        
        Args:
            message: User message
            
        Returns:
            Dictionary with intent label and confidence
        """
        try:
            prompt = self.INTENT_PROMPT.format(message=message)
            
            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="flash",
                temperature=0.3  # Lower temperature for more consistent classification
            )
            
            # Extract label (simple parsing)
            label = "emotional"  # Default fallback
            response_lower = response.lower().strip()
            
            if "technical" in response_lower:
                label = "technical"
            elif "positive" in response_lower or "neutral" in response_lower:
                label = "positive"
            elif "grant" in response_lower or "proposal" in response_lower:
                label = "grant"
            elif "shareable" in response_lower:
                label = "shareable"
            elif "emotional" in response_lower or "struggle" in response_lower or "vent" in response_lower:
                label = "emotional"
            
            # Also check keywords as fallback (prioritize in order)
            message_lower = message.lower()
            grant_keywords = ["grant proposal", "grant", "proposal", "research plan", "feedback on", "review my", "critique", "mentorship", "mentor"]
            scribe_keywords = ["post", "draft", "help me draft", "create a post", "write a post", "shareable", "public", "linkedin", "social media", "announce", "acceptance", "published", "share my", "share the", "news"]
            technical_keywords = ["semantic", "search", "debug", "agentic", "system", "code", "implementation", "algorithm", "method", "technique"]
            positive_keywords = ["swim", "talked", "discussed", "learned", "excited", "happy", "great", "good"]
            emotional_keywords = ["struggling", "failed", "frustrated", "anxious", "worried", "stressed", "difficult", "hard"]
            
            # Check for explicit requests in priority order (highest to lowest)
            if any(kw in message_lower for kw in grant_keywords):
                label = "grant"
            elif any(kw in message_lower for kw in scribe_keywords):
                label = "shareable"
            elif any(kw in message_lower for kw in technical_keywords) and not any(kw in message_lower for kw in emotional_keywords):
                label = "technical"
            elif any(kw in message_lower for kw in positive_keywords) and not any(kw in message_lower for kw in emotional_keywords):
                label = "positive"
            
            return {
                "intent": label,
                "confidence": "high",
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Fallback: check for obvious emotional keywords
            message_lower = message.lower()
            if any(kw in message_lower for kw in ["struggling", "failed", "frustrated", "anxious", "worried"]):
                return {"intent": "emotional", "confidence": "low", "raw_response": ""}
            return {"intent": "technical", "confidence": "low", "raw_response": ""}
    
    def should_match_peers(self, intent: str) -> bool:
        """
        Determine if peer matching should be triggered.
        
        Args:
            intent: Intent label
            
        Returns:
            True if peer matching is appropriate
        """
        # Only match peers for emotional struggles, not technical discussions
        return intent == "emotional"
    
    def get_agent_mode(self, intent: str) -> str:
        """
        Get appropriate agent mode based on intent.
        
        Args:
            intent: Intent label
            
        Returns:
            Agent mode string
        """
        mapping = {
            "emotional": "vent",
            "technical": "pi",        # Route technical to PI Simulator
            "positive": "scribe",     # Route positive achievements to Scribe
            "grant": "pi",
            "shareable": "scribe"
        }
        return mapping.get(intent, "vent")  # Default to vent if unknown

