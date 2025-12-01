"""Local vector search using FAISS (for Kaggle notebook)."""

from typing import List, Dict, Optional, Any
import json
import numpy as np
from pathlib import Path
from loguru import logger
import uuid
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available, falling back to simple cosine similarity")

from config.settings import settings
from data.schemas import PeerProfile, MatchResult
from services.embedding_service import embedding_service
from services.vector_persistence import JSONFilePersistence


class LocalVectorSearch:
    """Local vector search using FAISS or simple cosine similarity."""
    
    def __init__(self, persistence_path: Optional[str] = None, load_persisted_on_init: bool = False):
        self.profiles: Dict[str, PeerProfile] = {}
        self.embeddings: List[List[float]] = []
        self.profile_ids: List[str] = []
        self.index = None
        self.use_faiss = FAISS_AVAILABLE
        
        self.persistence_path = persistence_path or settings.vector_store_persistence_path
        self.persistence = JSONFilePersistence()
        self.additions_since_save = 0
        self._persisted_data_loaded = False
        
        if self.use_faiss:
            logger.info("Using FAISS for vector search")
        else:
            logger.info("Using simple cosine similarity for vector search")
        
        # Only load persisted data if explicitly requested (to avoid blocking startup)
        if load_persisted_on_init:
            self._load_persisted_data()
        else:
            logger.info("Skipping persisted data load on init (will load lazily if needed)")
    
    def add_peer_profile(self, profile: PeerProfile, skip_deduplication: bool = False) -> bool:
        if not self._validate_profile(profile):
            logger.debug(f"Rejected profile {profile.profile_id}: validation failed (text too short or missing embedding)")
            return False
        
        if not skip_deduplication:
            if self._is_duplicate(profile):
                logger.debug(f"Rejected profile {profile.profile_id}: duplicate (similarity above threshold)")
                return False
        
        self.profiles[profile.profile_id] = profile
        self.embeddings.append(profile.embedding)
        self.profile_ids.append(profile.profile_id)
        
        if self.use_faiss and self.embeddings:
            self._build_faiss_index()
        
        self.additions_since_save += 1
        if self.additions_since_save >= settings.auto_save_interval:
            self.save_to_json()
            self.additions_since_save = 0
        
        return True
    
    def add_profiles_batch(self, profiles: List[PeerProfile], skip_deduplication: bool = False):
        added_count = 0
        for profile in profiles:
            if self.add_peer_profile(profile, skip_deduplication=skip_deduplication):
                added_count += 1
        
        logger.info(f"Added {added_count} profiles (skipped {len(profiles) - added_count} duplicates/invalid)")
        
        if added_count > 0:
            self.save_to_json()
            self.additions_since_save = 0
    
    def _build_faiss_index(self):
        if not self.use_faiss or not self.embeddings:
            return
        
        try:
            dimension = len(self.embeddings[0])
            self.index = faiss.IndexFlatIP(dimension)
            
            embeddings_array = np.array(self.embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            
            self.index.add(embeddings_array)
            logger.info(f"FAISS index built with {len(self.embeddings)} vectors")
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            self.use_faiss = False
    
    def search_similar(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[MatchResult]:
        # Don't block on lazy loading - return empty results if data isn't ready yet
        # Persisted data should be loaded during initialization
        if not self._persisted_data_loaded:
            logger.debug("Persisted data not loaded yet, skipping lazy load to avoid blocking request")
            # Return empty results instead of blocking
            if not self.embeddings:
                return []
        
        if not self.embeddings:
            return []
        
        # Generate embedding for query
        query_embedding = embedding_service.generate_embedding(query_text)
        
        if self.use_faiss and self.index:
            return self._search_faiss(query_embedding, top_k, threshold)
        else:
            return self._search_cosine(query_embedding, top_k, threshold)
    
    def _search_faiss(
        self,
        query_embedding: List[float],
        top_k: int,
        threshold: float
    ) -> List[MatchResult]:
        """Search using FAISS."""
        try:
            # Normalize query embedding
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)
            
            # Search
            k = min(top_k, len(self.profiles))
            similarities, indices = self.index.search(query_array, k)
            
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= threshold and idx < len(self.profile_ids):
                    profile_id = self.profile_ids[idx]
                    profile = self.profiles[profile_id]
                    
                    results.append(MatchResult(
                        profile_id=profile_id,
                        similarity_score=float(similarity),
                        match_reason=f"Similar struggle: {profile.struggle_text[:100]}...",
                        suggested_connection=True
                    ))
            
            return results
        except Exception as e:
            logger.error(f"Error in FAISS search: {str(e)}")
            return self._search_cosine(query_embedding, top_k, threshold)
    
    def _search_cosine(
        self,
        query_embedding: List[float],
        top_k: int,
        threshold: float
    ) -> List[MatchResult]:
        """Search using cosine similarity."""
        similarities = []
        
        for i, profile_embedding in enumerate(self.embeddings):
            similarity = embedding_service.cosine_similarity(
                query_embedding,
                profile_embedding
            )
            if similarity >= threshold:
                similarities.append((similarity, i))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Get top_k results
        results = []
        for similarity, idx in similarities[:top_k]:
            profile_id = self.profile_ids[idx]
            profile = self.profiles[profile_id]
            
            results.append(MatchResult(
                profile_id=profile_id,
                similarity_score=similarity,
                match_reason=f"Similar struggle: {profile.struggle_text[:100]}...",
                suggested_connection=True
            ))
        
        return results
    
    def load_from_json(self, json_path: str, skip_deduplication: bool = True):
        """
        Load profiles from JSON file and generate embeddings.
        
        Args:
            json_path: Path to JSON file
            skip_deduplication: If True, skip duplicate check (for initial loading)
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            profiles = []
            for item in data:
                # Generate embedding for struggle text
                embedding = embedding_service.generate_embedding(item['struggle_text'])
                
                profile = PeerProfile(
                    profile_id=item['profile_id'],
                    embedding=embedding,
                    struggle_text=item['struggle_text'],
                    academic_stage=item.get('academic_stage'),
                    research_area=item.get('research_area'),
                    anonymized_metadata={
                        'emotional_tags': item.get('emotional_tags', [])
                    }
                )
                profiles.append(profile)
            
            self.add_profiles_batch(profiles, skip_deduplication=skip_deduplication)
            logger.info(f"Loaded {len(profiles)} profiles from {json_path}")
        except Exception as e:
            logger.error(f"Error loading profiles from JSON: {str(e)}")
            raise
    
    def save_to_json(self, path: Optional[str] = None) -> bool:
        """
        Save current profiles to JSON file.
        
        Args:
            path: Optional custom path, uses default if not provided
            
        Returns:
            True if successful, False otherwise
        """
        save_path = path or self.persistence_path
        profiles_list = list(self.profiles.values())
        return self.persistence.save(profiles_list, save_path)
    
    def _load_persisted_data(self):
        """Load persisted data if persistence file exists (lazy - only if not already loaded)."""
        if self._persisted_data_loaded:
            return
        
        try:
            file_path = Path(self.persistence_path)
            if file_path.exists():
                logger.info(f"Loading persisted data from {self.persistence_path}...")
                data = self.persistence.load(self.persistence_path)
                if data:
                    # Convert to profiles and add (skip deduplication for initial load)
                    # Generate embeddings in batches to avoid blocking too long
                    profiles = []
                    batch_size = 3  # Smaller batches for faster response
                    for i, item in enumerate(data):
                        try:
                            embedding = embedding_service.generate_embedding(item['struggle_text'])
                            profile = PeerProfile(
                                profile_id=item['profile_id'],
                                embedding=embedding,
                                struggle_text=item['struggle_text'],
                                academic_stage=item.get('academic_stage'),
                                research_area=item.get('research_area'),
                                anonymized_metadata=item.get('anonymized_metadata', {})
                            )
                            profiles.append(profile)
                            
                            # Add profile immediately and rebuild index incrementally
                            self.profiles[profile.profile_id] = profile
                            self.embeddings.append(profile.embedding)
                            self.profile_ids.append(profile.profile_id)
                            
                            # Rebuild index periodically to make it available sooner
                            if (i + 1) % batch_size == 0 or (i + 1) == len(data):
                                if self.use_faiss and self.embeddings:
                                    self._build_faiss_index()
                                
                                if (i + 1) % 5 == 0:
                                    logger.info(f"Generated embeddings for {i + 1}/{len(data)} profiles...")
                        except Exception as e:
                            logger.warning(f"Failed to load profile {item.get('profile_id', 'unknown')}: {e}")
                            continue
                    
                    logger.info(f"Loaded {len(profiles)} profiles from persistence file")
                    self._persisted_data_loaded = True
                else:
                    # No data in file, mark as loaded to avoid retrying
                    self._persisted_data_loaded = True
            else:
                # File doesn't exist, mark as loaded to avoid retrying
                self._persisted_data_loaded = True
        except Exception as e:
            logger.warning(f"Could not load persisted data: {str(e)}")
            self._persisted_data_loaded = True  # Mark as loaded even on error to avoid retrying
            logger.warning(f"Could not load persisted data: {str(e)}")
            self._persisted_data_loaded = True  # Mark as loaded even on error to avoid retrying
    
    def _validate_profile(self, profile: PeerProfile) -> bool:
        if len(profile.struggle_text.strip()) < settings.min_struggle_length:
            logger.debug(f"Profile {profile.profile_id} rejected: text too short")
            return False
        
        if not profile.embedding or len(profile.embedding) == 0:
            logger.debug(f"Profile {profile.profile_id} rejected: no embedding")
            return False
        
        return True
    
    def _is_duplicate(self, profile: PeerProfile) -> bool:
        if not self.embeddings:
            return False
        
        threshold = settings.deduplication_threshold
        
        for existing_embedding in self.embeddings:
            similarity = embedding_service.cosine_similarity(
                profile.embedding,
                existing_embedding
            )
            if similarity >= threshold:
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self.profiles),
            "total_embeddings": len(self.embeddings),
            "using_faiss": self.use_faiss,
            "persistence_path": self.persistence_path,
            "additions_since_save": self.additions_since_save
        }
    
    def add_peer_profile_from_session(
        self,
        struggle_text: str,
        user_id: str,
        academic_stage: Optional[str] = None,
        research_area: Optional[str] = None,
        emotional_tags: Optional[List[str]] = None
    ) -> Optional[str]:
        if not settings.enable_real_user_data:
            logger.debug("Real user data collection disabled")
            return None
        
        try:
            embedding = embedding_service.generate_embedding(struggle_text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
        
        profile_id = f"user_{uuid.uuid4().hex[:8]}"
        
        profile = PeerProfile(
            profile_id=profile_id,
            embedding=embedding,
            struggle_text=struggle_text,
            academic_stage=academic_stage,
            research_area=research_area,
            anonymized_metadata={
                'emotional_tags': emotional_tags or [],
                'source': 'user_session',
                'created_at': datetime.now().isoformat()
            }
        )
        
        if self.add_peer_profile(profile, skip_deduplication=False):
            logger.info(f"Added user profile from session: {profile_id}")
            return profile_id
        else:
            return None

