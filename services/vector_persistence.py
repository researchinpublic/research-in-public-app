"""Persistence interface for vector store."""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
import json
from loguru import logger

from data.schemas import PeerProfile


class VectorPersistence(ABC):
    """Abstract base class for vector store persistence."""
    
    @abstractmethod
    def save(self, profiles: List[PeerProfile], path: str) -> bool:
        """
        Save profiles to persistent storage.
        
        Args:
            profiles: List of peer profiles to save
            path: Storage path/location
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load(self, path: str) -> List[dict]:
        """
        Load profiles from persistent storage.
        
        Args:
            path: Storage path/location
            
        Returns:
            List of profile dictionaries (without embeddings, embeddings generated on load)
        """
        pass


class JSONFilePersistence(VectorPersistence):
    """JSON file-based persistence implementation."""
    
    def save(self, profiles: List[PeerProfile], path: str) -> bool:
        """
        Save profiles to JSON file.
        
        Args:
            profiles: List of peer profiles to save
            path: Path to JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert profiles to JSON-serializable format
            data = []
            for profile in profiles:
                profile_dict = {
                    "profile_id": profile.profile_id,
                    "struggle_text": profile.struggle_text,
                    "academic_stage": profile.academic_stage,
                    "research_area": profile.research_area,
                    "anonymized_metadata": profile.anonymized_metadata,
                }
                data.append(profile_dict)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(profiles)} profiles to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving profiles to {path}: {str(e)}")
            return False
    
    def load(self, path: str) -> List[dict]:
        """
        Load profiles from JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of profile dictionaries
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                logger.warning(f"Persistence file not found: {path}")
                return []
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} profiles from {path}")
            return data
        except Exception as e:
            logger.error(f"Error loading profiles from {path}: {str(e)}")
            return []

