"""Configuration management for the application."""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Gemini API Configuration
    # Using documented models from https://ai.google.dev/gemini-api/docs/models
    # Strip whitespace/newlines from API key (Cloud Run secrets may have trailing newlines)
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() if os.getenv("GEMINI_API_KEY") else None
    gemini_model_flash: str = "gemini-2.5-flash"  # Stable, free tier compatible
    gemini_model_pro: str = "gemini-2.5-pro"  # Stable, free tier compatible
    
    # Google Cloud Configuration
    google_cloud_project_id: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    google_cloud_region: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    # Vertex AI Vector Search
    vertex_ai_vector_search_index: Optional[str] = os.getenv("VERTEX_AI_VECTOR_SEARCH_INDEX")
    vertex_ai_matching_engine_endpoint: Optional[str] = os.getenv("VERTEX_AI_ME_ENDPOINT_ID")
    vertex_ai_matching_engine_deployed_index: Optional[str] = os.getenv("VERTEX_AI_ME_DEPLOYED_INDEX_ID")
    use_local_vector_store: bool = os.getenv("USE_LOCAL_VECTOR_STORE", "True").lower() == "true"
    use_vertex_ai: bool = os.getenv("USE_VERTEX_AI", "False").lower() == "true"
    
    # Embedding Model
    embedding_model: str = "text-embedding-004"
    
    # Application Settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Vector Search Settings
    vector_search_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Vector Store Persistence Settings
    enable_real_user_data: bool = os.getenv("ENABLE_REAL_USER_DATA", "True").lower() == "true"
    vector_store_persistence_path: str = os.getenv("VECTOR_STORE_PERSISTENCE_PATH", "data/vector_store.json")
    auto_save_interval: int = int(os.getenv("AUTO_SAVE_INTERVAL", "10"))  # Save after N additions
    min_struggle_length: int = int(os.getenv("MIN_STRUGGLE_LENGTH", "20"))  # Minimum characters
    deduplication_threshold: float = float(os.getenv("DEDUPLICATION_THRESHOLD", "0.95"))  # Similarity threshold for duplicates

    # Frontend origins (CORS)
    frontend_cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context):
        """Allow comma-separated override via FRONTEND_CORS_ORIGINS."""
        origins = os.getenv("FRONTEND_CORS_ORIGINS")
        if origins:
            parsed = [origin.strip() for origin in origins.split(",") if origin.strip()]
            if parsed:
                self.frontend_cors_origins = parsed


# Global settings instance
settings = Settings()

