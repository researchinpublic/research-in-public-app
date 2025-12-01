"""Empathy scoring evaluation."""

from typing import Dict, List, Any
from loguru import logger

from services.gemini_service import gemini_service


class EmpathyScorer:
    """Evaluate agent responses for empathy."""
    
    def __init__(self):
        """Initialize empathy scorer."""
        self.evaluation_prompt = """Evaluate this agent response for empathy on a scale of 1-5.

Response: {response}
User Message: {user_message}

Consider:
1. Does it acknowledge the user's emotions?
2. Is it validating without being dismissive?
3. Does it show understanding of the academic context?
4. Is the tone appropriate and supportive?

Provide score (1-5) and brief reasoning."""

    def score_response(
        self,
        user_message: str,
        agent_response: str
    ) -> Dict[str, Any]:
        """
        Score an agent response for empathy.
        
        Args:
            user_message: Original user message
            agent_response: Agent's response
            
        Returns:
            Dictionary with score and reasoning
        """
        try:
            prompt = self.evaluation_prompt.format(
                response=agent_response,
                user_message=user_message
            )
            
            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="flash",
                temperature=0.3
            )
            
            # Extract score (simple parsing)
            score = 3.0  # Default
            if "5" in response or "five" in response.lower():
                score = 5.0
            elif "4" in response or "four" in response.lower():
                score = 4.0
            elif "2" in response or "two" in response.lower():
                score = 2.0
            elif "1" in response or "one" in response.lower():
                score = 1.0
            
            return {
                "score": score,
                "reasoning": response,
                "user_message": user_message,
                "agent_response": agent_response
            }
            
        except Exception as e:
            logger.error(f"Error scoring empathy: {str(e)}")
            return {
                "score": 3.0,
                "reasoning": "Error during evaluation",
                "user_message": user_message,
                "agent_response": agent_response
            }
    
    def batch_evaluate(
        self,
        conversations: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple conversations.
        
        Args:
            conversations: List of dicts with 'user_message' and 'agent_response'
            
        Returns:
            List of evaluation results
        """
        results = []
        for conv in conversations:
            result = self.score_response(
                conv["user_message"],
                conv["agent_response"]
            )
            results.append(result)
        return results

