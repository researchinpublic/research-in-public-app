"""Semantic Matchmaker Agent - Peer matching using embeddings."""

from typing import List, Optional, Dict, Any
from loguru import logger

from agents.base_agent import BaseAgent
from config.prompts import MATCHMAKER_PROMPT
from data.schemas import ConversationSession, MatchResult
from services.vector_search_local import LocalVectorSearch
from services.embedding_service import embedding_service


class SemanticMatchmakerAgent(BaseAgent):
    """Agent 2: Semantic Matchmaker - Connection Engine."""
    
    def __init__(self, vector_store: LocalVectorSearch):
        super().__init__(
            name="Semantic Matchmaker",
            system_prompt=MATCHMAKER_PROMPT
        )
        self.vector_store = vector_store
    
    def find_similar_peers(
        self,
        query_text: str,
        top_k: int = 3,
        threshold: float = 0.7
    ) -> List[MatchResult]:
        try:
            matches = self.vector_store.search_similar(
                query_text=query_text,
                top_k=top_k,
                threshold=threshold
            )
            return matches
        except Exception as e:
            logger.error(f"Error finding similar peers: {str(e)}")
            return []
    
    def format_match_suggestion(self, matches: List[MatchResult]) -> str:
        if not matches:
            return ""
        
        top_matches = matches[:3]
        response_parts = []
        
        response_parts.append("Oh honey, I hear you. And you know what? You're not alone in this.")
        
        match_descriptions = []
        for match in top_matches:
            profile = self.vector_store.profiles.get(match.profile_id) if hasattr(self.vector_store, 'profiles') else None
            if profile and profile.academic_stage:
                match_descriptions.append(f"a {profile.academic_stage} researcher who {match.match_reason.lower()}")
            else:
                match_descriptions.append(f"a researcher who {match.match_reason.lower()}")
        
        if len(match_descriptions) == 1:
            response_parts.append(f"I found {match_descriptions[0]}. There's something powerful about knowing someone else has walked this path.")
        elif len(match_descriptions) == 2:
            response_parts.append(f"I found {match_descriptions[0]} and {match_descriptions[1]}. You know what? There's something healing about connecting with others who understand exactly what you're going through.")
        else:
            response_parts.append(f"I found {match_descriptions[0]}, {match_descriptions[1]}, and {match_descriptions[2]}. You're not the only one who's felt this way, and there's real power in that connection.")
        
        response_parts.append("Would you like me to help you connect with them? There's something beautiful about finding your tribe.")
        
        return "\n\n" + " ".join(response_parts)
    
    def get_matches_data(self, matches: List[MatchResult]) -> List[Dict[str, Any]]:
        enriched_matches = []
        for match in matches:
            profile = self.vector_store.profiles.get(match.profile_id) if hasattr(self.vector_store, 'profiles') else None
            if profile:
                emotional_tags = []
                if hasattr(profile, 'anonymized_metadata') and isinstance(profile.anonymized_metadata, dict):
                    emotional_tags = profile.anonymized_metadata.get('emotional_tags', [])
                
                enriched_matches.append({
                    "id": match.profile_id,
                    "similarity": match.similarity_score,
                    "reason": match.match_reason,
                    "role": profile.academic_stage or "Researcher",
                    "area": profile.research_area or "Unknown Field",
                    "struggle": profile.struggle_text,
                    "tags": emotional_tags
                })
        return enriched_matches

    def is_emotional_struggle(self, message: str) -> bool:
        """
        Check if message contains emotional struggle indicators.
        """
        emotional_keywords = [
            "struggling", "failed", "frustrated", "anxious", "worried", 
            "stressed", "difficult", "hard", "imposter", "alone", "isolated",
            "rejected", "disappointed", "overwhelmed", "burnout", "toxic"
        ]
        
        message_lower = message.lower()
        return any(kw in message_lower for kw in emotional_keywords)
    
    def process(
        self,
        message: str,
        session: ConversationSession,
        force: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process message and find peer matches.
        
        Returns:
            Dictionary containing 'text' response and 'matches' data.
        """
        result = {"text": "", "matches": []}
        
        try:
            # Only match peers for emotional struggles, unless forced
            if not force and not self.is_emotional_struggle(message):
                logger.info("Message is not an emotional struggle, skipping peer matching")
                return result
            
            # Find similar peers
            matches = self.find_similar_peers(message)
            
            if matches:
                result["text"] = self.format_match_suggestion(matches)
                result["matches"] = self.get_matches_data(matches)
            
            return result
                
        except Exception as e:
            logger.error(f"Error in Semantic Matchmaker: {str(e)}")
            return result

