"""Embedding service using text-embedding-004."""

import google.generativeai as genai
from typing import List, Union
import numpy as np
from loguru import logger

from config.settings import settings


class EmbeddingService:
    """Service for generating embeddings using Google's text-embedding-004."""
    
    def __init__(self):
        """Initialize embedding service."""
        # Ensure API key is stripped of whitespace (Cloud Run secrets may have trailing newlines)
        api_key = settings.gemini_api_key.strip() if settings.gemini_api_key else None
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Check for common API key issues
        if '\n' in api_key or '\r' in api_key:
            logger.warning("⚠️ API key contains newline characters - stripping them")
            api_key = api_key.replace('\n', '').replace('\r', '').strip()
        
        genai.configure(api_key=api_key)
        logger.info("Embedding service initialized")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"  # or "RETRIEVAL_QUERY"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            for text in texts:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0


# Global instance
embedding_service = EmbeddingService()

