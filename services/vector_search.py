"""Vertex AI Vector Search integration (for web app)."""

from typing import List, Dict, Optional
from loguru import logger

try:
    from google.cloud import aiplatform
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.warning("Vertex AI not available, will use local vector store")

from config.settings import settings
from data.schemas import PeerProfile, MatchResult
from services.embedding_service import embedding_service


class VectorSearchService:
    """Vertex AI Vector Search service."""
    
    def __init__(self):
        """Initialize vector search service."""
        self.index_endpoint = None
        self.deployed_index_id = settings.vertex_ai_matching_engine_deployed_index
        self.initialized = False
        
        if settings.use_local_vector_store or not VERTEX_AI_AVAILABLE:
            logger.info("Using local vector store instead of Vertex AI")
            self.use_local = True
        else:
            self.use_local = False
            self._initialize_vertex_ai()
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI Vector Search."""
        try:
            if not settings.google_cloud_project_id:
                logger.warning("Google Cloud Project ID not set, using local store")
                self.use_local = True
                return
            
            if not settings.vertex_ai_matching_engine_endpoint or not self.deployed_index_id:
                logger.warning("Vertex AI endpoint or deployed index ID missing; falling back to local store")
                self.use_local = True
                return
            
            aiplatform.init(
                project=settings.google_cloud_project_id,
                location=settings.google_cloud_region
            )
            self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=settings.vertex_ai_matching_engine_endpoint
            )
            self.initialized = True
            logger.info("Vertex AI Matching Engine initialized")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {str(e)}")
            self.use_local = True
    
    def add_peer_profile(self, profile: PeerProfile):
        """Add a peer profile to the vector index."""
        if self.use_local:
            logger.warning("Local vector store not implemented in this service. Use vector_search_local.py")
            return
        
        # Vertex AI implementation would go here
        # This is a placeholder for the full implementation
        pass
    
    def search_similar(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[MatchResult]:
        """
        Search for similar peer profiles.
        
        Args:
            query_text: Query text to find similar struggles
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of match results
        """
        if self.use_local:
            logger.warning("Use vector_search_local.py for local search")
            return []
        
        if not self.initialized or not self.index_endpoint:
            logger.error("Vertex AI index endpoint not initialized")
            return []
        
        try:
            embedding = embedding_service.generate_embedding(query_text)
            query = {
                "datapoint": {
                    "datapoint_id": "query",
                    "feature_vector": embedding,
                },
                "neighbor_count": top_k,
            }
            
            response = self.index_endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[query]
            )
            
            if not response:
                return []
            
            neighbors = response[0].neighbors
            matches: List[MatchResult] = []
            
            for neighbor in neighbors:
                datapoint = getattr(neighbor, "datapoint", None)
                distance = getattr(neighbor, "distance", 0.0) or 0.0
                similarity = max(0.0, 1.0 - distance)
                
                if similarity < threshold:
                    continue
                
                profile_id = getattr(datapoint, "datapoint_id", "unknown") if datapoint else "unknown"
                
                restricts = getattr(datapoint, "restricts", None) or []
                if restricts and getattr(restricts[0], "allow_tokens", None):
                    match_reason = restricts[0].allow_tokens[0]
                else:
                    match_reason = "Similar struggle detected via Vertex AI"
                
                matches.append(MatchResult(
                    profile_id=profile_id,
                    similarity_score=similarity,
                    match_reason=match_reason,
                    suggested_connection=True
                ))
            
            return matches
        except Exception as e:
            logger.error(f"Vertex AI vector search failed: {str(e)}")
            return []

