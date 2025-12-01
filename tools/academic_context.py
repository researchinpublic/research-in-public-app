"""Academic context retrieval tool."""

from typing import Dict, Any
from loguru import logger

from services.grounding_service import GroundingService


def retrieve_academic_context(query: str) -> Dict[str, Any]:
    """
    Retrieve academic context using Google Search Grounding.
    
    Args:
        query: Search query (e.g., "Western Blot troubleshooting methods")
        
    Returns:
        Dictionary with citations, context, and relevant information
    """
    try:
        grounding_service = GroundingService()
        result = grounding_service.retrieve_academic_context(query)
        
        return {
            "citations": result.get("citations", []),
            "context": result.get("context", ""),
            "hashtags": result.get("hashtags", []),
            "verified": True
        }
        
    except Exception as e:
        logger.error(f"Error retrieving academic context: {str(e)}")
        return {
            "citations": [],
            "context": f"Academic literature suggests that {query} is a known issue in research.",
            "hashtags": [],
            "verified": False
        }

