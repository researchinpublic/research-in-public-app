"""Gemini API service wrapper."""

import google.generativeai as genai
from typing import Optional, List, Dict, Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Try to import newer Client API if available
try:
    from google import genai as genai_client_module
    HAS_CLIENT_API = True
except ImportError:
    HAS_CLIENT_API = False
    logger.debug("Newer genai.Client API not available, using GenerativeModel API")

# Try to import Vertex AI SDK for server-to-server auth
try:
    import vertexai
    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False
    logger.debug("Vertex AI SDK not installed; skipping vertexai.init()")

from config.settings import settings


class GeminiService:
    """Service for interacting with Google Gemini models."""
    
    def __init__(self):
        # Ensure API key is stripped of whitespace (Cloud Run secrets may have trailing newlines)
        api_key = settings.gemini_api_key.strip() if settings.gemini_api_key else None
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Check for common API key issues
        if len(api_key) < 20:
            logger.warning(f"⚠️ API key seems too short ({len(api_key)} chars). Expected ~39 characters.")
        if '\n' in api_key or '\r' in api_key:
            logger.warning("⚠️ API key contains newline characters - stripping them")
            api_key = api_key.replace('\n', '').replace('\r', '').strip()
        
        # Store cleaned API key as instance variable
        self.api_key = api_key
        
        # Log API key status (without exposing the key)
        logger.info(f"GEMINI_API_KEY loaded (length: {len(api_key)}, starts with: {api_key[:10]}...)")
        
        self.use_vertex_ai = (
            settings.use_vertex_ai
            and bool(settings.google_cloud_project_id)
            and HAS_VERTEX_AI
        )
        
        if self.use_vertex_ai:
            try:
                vertexai.init(
                    project=settings.google_cloud_project_id,
                    location=settings.google_cloud_region
                )
                logger.info("Vertex AI initialized for Gemini service")
            except Exception as vertex_err:
                logger.warning(f"Failed to initialize Vertex AI, falling back to API key auth: {vertex_err}")
                self.use_vertex_ai = False
        
        genai.configure(api_key=self.api_key)
        
        # Disable Client API on Cloud Run - it tries to use OAuth2 instead of API keys
        # The GenerativeModel API properly supports API keys
        import os
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        self.use_client_api = False
        if HAS_CLIENT_API and not is_production:
            try:
                self.client = genai_client_module.Client(api_key=self.api_key)
                # Skip test call during initialization to avoid blocking startup
                # Will test on first actual use
                self.use_client_api = True
                logger.info("Using newer genai.Client API (will test on first use)")
            except Exception as e:
                logger.debug(f"Client API not available or failed: {e}, using GenerativeModel API")
                self.use_client_api = False
        elif is_production:
            logger.info("Production environment detected - using GenerativeModel API (Client API requires OAuth2 on Cloud Run)")
            self.use_client_api = False
        
        flash_model_names = [
            "gemini-2.5-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-exp",
        ]
        
        self.flash_model = None
        self.flash_model_name = None
        for model_name in flash_model_names:
            try:
                # Try newer Client API first if available (for gemini-2.0+ models)
                if self.use_client_api and (model_name.startswith("gemini-2.0") or model_name.startswith("gemini-2.5") or model_name.startswith("gemini-3")):
                    # Skip test call during initialization to avoid blocking startup
                    self.flash_model_name = model_name
                    logger.info(f"Initialized Flash model via Client API: {model_name} (will test on first use)")
                    break
                
                # Fall back to GenerativeModel API
                test_model = genai.GenerativeModel(model_name)
                # Skip API test call during initialization to avoid blocking startup
                # Model will be tested on first actual use
                self.flash_model = test_model
                self.flash_model_name = model_name
                logger.info(f"Initialized Flash model: {model_name} (will test on first use)")
                break
            except Exception as e:
                logger.debug(f"Failed to initialize {model_name}: {e}")
                continue
        
        if self.flash_model is None and self.flash_model_name is None:
            raise ValueError(f"Could not initialize Flash model with any of: {flash_model_names}. Please check your API key and model availability.")
        
        # Using documented models from https://ai.google.dev/gemini-api/docs/models
        # Prioritize stable models (free tier compatible) first
        pro_model_names = [
            "gemini-2.5-pro",  # Stable, free tier compatible (default)
            "gemini-3-pro-preview",  # Preview version (newest)
        ]
        
        self.pro_model = None
        self.pro_model_name = None
        for model_name in pro_model_names:
            try:
                # Try newer Client API first if available (for gemini-2.0+ models)
                if self.use_client_api and (model_name.startswith("gemini-2.0") or model_name.startswith("gemini-2.5") or model_name.startswith("gemini-3")):
                    # Skip test call during initialization to avoid blocking startup
                    self.pro_model_name = model_name
                    logger.info(f"Initialized Pro model via Client API: {model_name} (will test on first use)")
                    break
                
                # Fall back to GenerativeModel API
                test_model = genai.GenerativeModel(model_name)
                # Skip API test call during initialization to avoid blocking startup
                # Model will be tested on first actual use
                self.pro_model = test_model
                self.pro_model_name = model_name
                logger.info(f"Initialized Pro model: {model_name} (will test on first use)")
                break
            except Exception as e:
                logger.debug(f"Failed to initialize {model_name}: {e}")
                continue
        
        if self.pro_model is None and self.pro_model_name is None:
            # Fallback: use flash model for pro if pro fails
            logger.warning("Could not initialize Pro model, using Flash as fallback")
            self.pro_model = self.flash_model
            self.pro_model_name = self.flash_model_name
        
        logger.info("Gemini service initialized")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_type: str = "flash",
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_type: 'flash' or 'pro'
            system_instruction: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters
            
        Returns:
            Generated response text
        """
        model = self.flash_model if model_type == "flash" else self.pro_model
        model_name = self.flash_model_name if model_type == "flash" else self.pro_model_name
        
        # Convert messages format for Gemini
        # Gemini uses parts format
        history = []
        user_message = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                if user_message:
                    history.append({"role": "user", "parts": [user_message]})
                user_message = content
            elif role == "assistant":
                if user_message:
                    history.append({"role": "user", "parts": [user_message]})
                    user_message = ""
                history.append({"role": "model", "parts": [content]})
        
        # Try Client API first if available (simpler for chat, for gemini-2.0+ models)
        if self.use_client_api and model_name and (model_name.startswith("gemini-2.0") or model_name.startswith("gemini-2.5") or model_name.startswith("gemini-3")):
            try:
                # Convert messages to simple string format for Client API
                conversation_text = "\n".join([
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                    for msg in messages
                ])
                if user_message:
                    conversation_text += f"\nUser: {user_message}"
                
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=conversation_text
                )
                return response.text
            except Exception as client_e:
                logger.debug(f"Client API chat failed, falling back to GenerativeModel: {client_e}")
        
        # Use GenerativeModel API for chat
        if model is None:
            raise ValueError(f"Model {model_name} not properly initialized for chat")
        
        # Prepare generation config
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
        )
        if max_tokens:
            generation_config.max_output_tokens = max_tokens
        
        # Try primary model first
        try:
            # Create model with system instruction if provided
            # System instruction must be set when creating the model, not in start_chat()
            if system_instruction:
                # Get the actual working model name
                try:
                    model_with_system = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    chat = model_with_system.start_chat(history=history)
                except Exception as e:
                    logger.warning(f"Failed to create model with system instruction, using fallback: {e}")
                    # Fallback: include system instruction in the user message
                    if user_message:
                        user_message = f"{system_instruction}\n\n{user_message}"
                    elif history and history[0]["role"] == "user":
                        history[0]["parts"][0] = f"{system_instruction}\n\n{history[0]['parts'][0]}"
                    chat = model.start_chat(history=history)
            else:
                chat = model.start_chat(history=history)
            
            # Generate response
            if user_message:
                response = chat.send_message(
                    user_message,
                    generation_config=generation_config
                )
            else:
                # If no user message, use the last message
                last_content = messages[-1]["content"] if messages else ""
                response = chat.send_message(
                    last_content,
                    generation_config=generation_config
                )
            
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            # If 404 error, try alternative model names
            if "404" in error_str or "not found" in error_str:
                logger.warning(f"Model {model_name} not found in chat_completion, trying alternatives...")
                # Try alternative model names (documented models only)
                alt_names = ["gemini-2.5-flash", "gemini-2.0-flash-001", "gemini-2.0-flash"] if model_type == "flash" else ["gemini-2.5-pro", "gemini-3-pro-preview"]
                
                for alt_name in alt_names:
                    if alt_name == model_name:
                        continue
                    try:
                        alt_model = genai.GenerativeModel(alt_name)
                        if system_instruction:
                            alt_model_with_system = genai.GenerativeModel(
                                model_name=alt_name,
                                system_instruction=system_instruction
                            )
                            chat = alt_model_with_system.start_chat(history=history)
                        else:
                            chat = alt_model.start_chat(history=history)
                        
                        if user_message:
                            response = chat.send_message(user_message, generation_config=generation_config)
                        else:
                            last_content = messages[-1]["content"] if messages else ""
                            response = chat.send_message(last_content, generation_config=generation_config)
                        
                        logger.info(f"Successfully used alternative model in chat: {alt_name}")
                        # Update stored model for future use
                        if model_type == "flash":
                            self.flash_model = alt_model
                            self.flash_model_name = alt_name
                        else:
                            self.pro_model = alt_model
                            self.pro_model_name = alt_name
                        return response.text
                    except Exception as alt_e:
                        logger.debug(f"Alternative model {alt_name} also failed: {alt_e}")
                        continue
                
                # If all alternatives fail, raise original error
                logger.error(f"All model alternatives failed for {model_type} in chat_completion")
                raise
            else:
                # For non-404 errors, raise immediately
                logger.error(f"Error in chat_completion: {str(e)}")
                raise
    
    def generate_text(
        self,
        prompt: str,
        model_type: str = "flash",
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            model_type: 'flash' or 'pro'
            system_instruction: System prompt
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        # Try with current model, fallback to alternatives if 404 error
        model = self.flash_model if model_type == "flash" else self.pro_model
        model_name = self.flash_model_name if model_type == "flash" else self.pro_model_name
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            **kwargs
        )
        
        # Try primary model first
        try:
            # Use Client API if available and model supports it (for gemini-2.0+ models)
            if self.use_client_api and model_name and (model_name.startswith("gemini-2.0") or model_name.startswith("gemini-2.5") or model_name.startswith("gemini-3")):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return response.text
                except Exception as client_e:
                    logger.debug(f"Client API failed, falling back to GenerativeModel: {client_e}")
            
            # Use GenerativeModel API (only if model object exists)
            if model is None:
                raise ValueError(f"Model {model_name} not properly initialized")
            
            # Create model with system instruction if provided
            # System instruction must be set when creating the model, not in generate_content()
            if system_instruction:
                try:
                    model_with_system = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    response = model_with_system.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                except Exception as e:
                    logger.warning(f"Failed to create model with system instruction, prepending to prompt: {e}")
                    # Fallback: prepend system instruction to prompt
                    enhanced_prompt = f"{system_instruction}\n\n{prompt}"
                    response = model.generate_content(
                        enhanced_prompt,
                        generation_config=generation_config
                    )
            else:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            return response.text
        except Exception as e:
            error_str = str(e).lower()
            # If 404 error, try alternative model names
            if "404" in error_str or "not found" in error_str:
                logger.warning(f"Model {model_name} not found, trying alternatives...")
                # Try alternative model names (documented models only)
                alt_names = ["gemini-2.5-flash", "gemini-2.0-flash-001", "gemini-2.0-flash"] if model_type == "flash" else ["gemini-2.5-pro", "gemini-3-pro-preview"]
                
                for alt_name in alt_names:
                    if alt_name == model_name:
                        continue
                    try:
                        alt_model = genai.GenerativeModel(alt_name)
                        if system_instruction:
                            try:
                                alt_model_with_system = genai.GenerativeModel(
                                    model_name=alt_name,
                                    system_instruction=system_instruction
                                )
                                response = alt_model_with_system.generate_content(
                                    prompt,
                                    generation_config=generation_config
                                )
                            except Exception as e:
                                # Fallback: prepend system instruction to prompt
                                enhanced_prompt = f"{system_instruction}\n\n{prompt}"
                                response = alt_model.generate_content(
                                    enhanced_prompt,
                                    generation_config=generation_config
                                )
                        else:
                            response = alt_model.generate_content(
                                prompt,
                                generation_config=generation_config
                            )
                        logger.info(f"Successfully used alternative model: {alt_name}")
                        # Update stored model for future use
                        if model_type == "flash":
                            self.flash_model = alt_model
                            self.flash_model_name = alt_name
                        else:
                            self.pro_model = alt_model
                            self.pro_model_name = alt_name
                        return response.text
                    except Exception as alt_e:
                        logger.debug(f"Alternative model {alt_name} also failed: {alt_e}")
                        continue
                
                # If all alternatives fail, raise original error
                logger.error(f"All model alternatives failed for {model_type}")
                raise
            else:
                # For non-404 errors, raise immediately
                logger.error(f"Error in generate_text: {str(e)}")
                raise
    
    def generate_with_function_calling(
        self,
        prompt: str,
        tools: List[Any],
        model_type: str = "pro",
        **kwargs
    ) -> Any:
        """
        Generate response with function calling support.
        
        Args:
            prompt: Input prompt
            tools: List of function definitions
            model_type: 'flash' or 'pro'
            **kwargs: Additional parameters
            
        Returns:
            Response with potential function calls
        """
        try:
            model = self.flash_model if model_type == "flash" else self.pro_model
            
            response = model.generate_content(
                prompt,
                tools=tools,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in generate_with_function_calling: {str(e)}")
            raise

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Any,
        model_type: str = "flash",
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Any:
        """
        Generate a structured JSON response using the given schema.
        
        Args:
            messages: List of message dicts
            response_schema: Pydantic model or schema dict
            model_type: 'flash' or 'pro'
            system_instruction: System prompt
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Parsed object matching the schema
        """
        model_name = self.flash_model_name if model_type == "flash" else self.pro_model_name
        
        # Configure generation to use JSON mode
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            **kwargs
        )
        
        # Convert messages to Gemini format
        history = []
        user_message = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                if user_message:
                    history.append({"role": "user", "parts": [user_message]})
                user_message = content
            elif role == "assistant":
                if user_message:
                    history.append({"role": "user", "parts": [user_message]})
                    user_message = ""
                history.append({"role": "model", "parts": [content]})
        
        try:
            # Use Client API if available (preferred for structured output)
            if self.use_client_api and model_name and (model_name.startswith("gemini-2.0") or model_name.startswith("gemini-2.5") or model_name.startswith("gemini-3")):
                try:
                    # Convert messages to content list
                    contents = []
                    for msg in messages:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append(genai_client_module.types.Content(
                            role=role,
                            parts=[genai_client_module.types.Part(text=msg.get("content", ""))]
                        ))
                    
                    # Use generate_content with response_schema
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=genai_client_module.types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            temperature=temperature,
                            system_instruction=system_instruction
                        )
                    )
                    
                    # With Client API and Pydantic schema, response.parsed is already the object
                    return response.parsed
                except Exception as client_e:
                    logger.debug(f"Client API structured gen failed: {client_e}, falling back")
            
            # Fallback to GenerativeModel
            model = self.flash_model if model_type == "flash" else self.pro_model
            
            # Handle system instruction
            if system_instruction:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                except:
                    # Prepend to prompt if model init fails
                    if user_message:
                        user_message = f"{system_instruction}\n\n{user_message}"
            
            chat = model.start_chat(history=history)
            
            if user_message:
                response = chat.send_message(user_message, generation_config=generation_config)
            else:
                response = chat.send_message(messages[-1]["content"], generation_config=generation_config)
            
            # For GenerativeModel, we get a JSON string text.
            # If response_schema was a Pydantic class, we need to parse it manually
            import json
            json_text = response.text
            parsed_dict = json.loads(json_text)
            
            # If a Pydantic model class was passed, instantiate it
            if hasattr(response_schema, 'model_validate'):
                return response_schema.model_validate(parsed_dict)
            return parsed_dict
            
        except Exception as e:
            logger.error(f"Error in generate_structured: {str(e)}")
            raise


# Global instance - initialize lazily to avoid blocking server startup
_gemini_service_instance: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the global Gemini service instance (lazy initialization)."""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        logger.info("Initializing Gemini service (lazy initialization)...")
        try:
            _gemini_service_instance = GeminiService()
            logger.info("✅ Gemini service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini service: {e}")
            import traceback
            logger.error(f"Error traceback:\n{traceback.format_exc()}")
            # Check if API key is accessible
            if not settings.gemini_api_key:
                logger.error("⚠️ GEMINI_API_KEY is not set in environment variables!")
            else:
                logger.info(f"GEMINI_API_KEY is set (length: {len(settings.gemini_api_key)})")
            raise
    return _gemini_service_instance


# Try to initialize at import time, but don't fail if it doesn't work
# This allows the server to start even if Gemini init fails
try:
    gemini_service = GeminiService()
    logger.info("Gemini service initialized at import time")
except Exception as e:
    logger.warning(f"Gemini service initialization failed at import time: {e}")
    logger.info("Will use lazy initialization - server can still start")
    import traceback
    logger.debug(f"Initialization error traceback:\n{traceback.format_exc()}")
    # Create a proxy that initializes on first use
    class LazyGeminiService:
        def __getattr__(self, name):
            try:
                return getattr(get_gemini_service(), name)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service on first use: {e}")
                import traceback
                logger.error(f"Error traceback:\n{traceback.format_exc()}")
                # Check if it's an API key issue
                if "api key" in str(e).lower() or "GEMINI_API_KEY" in str(e):
                    logger.error("⚠️ CRITICAL: GEMINI_API_KEY is missing or invalid!")
                    raise ValueError(f"Gemini API key configuration error: {e}. Please check Cloud Run secrets.")
                raise
    gemini_service = LazyGeminiService()

