"""Kaggle-specific utilities."""

import os
from typing import Optional


def get_kaggle_secret(secret_name: str) -> Optional[str]:
    """
    Get a secret from Kaggle User Secrets.
    
    Args:
        secret_name: Name of the secret
        
    Returns:
        Secret value or None
    """
    try:
        # Kaggle secrets are accessed via environment variables
        # Format: KAGGLE_USER_SECRETS_TOKEN or direct env var
        secret_value = os.getenv(secret_name)
        
        # Alternative: Try to read from Kaggle's secrets API if available
        try:
            from kaggle_secrets import UserSecretsClient
            client = UserSecretsClient()
            secret_value = client.get_secret(secret_name)
        except ImportError:
            pass
        
        return secret_value
    except Exception as e:
        print(f"Error getting Kaggle secret {secret_name}: {e}")
        return None


def setup_kaggle_environment():
    """Setup environment for Kaggle notebook."""
    # Set API key from Kaggle secrets
    api_key = get_kaggle_secret("GEMINI_API_KEY")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        print("✅ Gemini API key loaded from Kaggle secrets")
    else:
        print("⚠️ GEMINI_API_KEY not found in Kaggle secrets")
    
    # Force local vector store
    os.environ["USE_LOCAL_VECTOR_STORE"] = "True"
    print("✅ Using local vector store (FAISS)")

