"""FastAPI server for Research In Public backend."""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

# Configure logging early
logger.add(
    lambda msg: print(msg, end=""),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level=os.getenv("LOG_LEVEL", "INFO").upper()
)

# Load environment variables
load_dotenv()

# Log startup immediately
logger.info("=" * 60)
logger.info("🚀 Research In Public API - Starting up...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
logger.info("=" * 60)

# Import backend components
from orchestration.agent_orchestrator import AgentOrchestrator
from services.vector_search_local import LocalVectorSearch
from data.schemas import ConversationSession, ConversationMessage, GuardianReport, SocialDraft
from services.gemini_service import gemini_service
from config.settings import settings

# Global state
orchestrator: Optional[AgentOrchestrator] = None
sessions: Dict[str, ConversationSession] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - handles startup and shutdown."""
    global orchestrator
    
    logger.info("Starting application initialization...")
    
    # Start server immediately, initialize in background
    # This allows health checks to pass while initialization completes
    import asyncio
    
    async def initialize_background():
        """Initialize orchestrator in background to avoid blocking server startup."""
        try:
            logger.info("Beginning background initialization...")
            data_path = Path(__file__).parent.parent / "data" / "dummy_struggles.json"
            
            logger.info("Creating vector store...")
            # Don't load persisted data on init to avoid blocking (embeddings are slow)
            vector_store = LocalVectorSearch(load_persisted_on_init=False)
            
            # Initialize orchestrator immediately (don't wait for dummy data)
            logger.info("Initializing agent orchestrator...")
            global orchestrator
            orchestrator = AgentOrchestrator(vector_store=vector_store)
            logger.info("✅ Agent orchestrator initialized successfully")
            
            # Load dummy data in background (non-blocking)
            if data_path.exists():
                logger.info(f"Loading dummy data from {data_path} in background...")
                try:
                    vector_store.load_from_json(str(data_path), skip_deduplication=True)
                    logger.info(f"✅ Loaded dummy data from {data_path}")
                except Exception as e:
                    logger.warning(f"Failed to load dummy data (non-critical): {e}")
            else:
                logger.info(f"Dummy data file not found at {data_path}, starting with empty vector store")
            
            # Pre-load persisted data in background to avoid blocking first request
            logger.info("Pre-loading persisted vector store data in background...")
            try:
                # Run synchronous loading in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, vector_store._load_persisted_data)
                logger.info("✅ Pre-loaded persisted vector store data")
            except Exception as e:
                logger.warning(f"Failed to pre-load persisted data (non-critical): {e}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}", exc_info=True)
            # Don't raise - allow server to start even if initialization fails
            # It can retry on first request
    
    # Start initialization in background task
    init_task = asyncio.create_task(initialize_background())
    
    # Yield immediately so server can start
    logger.info("✅ Server starting - initialization continuing in background")
    yield
    
    # Cancel background task if still running
    if not init_task.done():
        init_task.cancel()
        try:
            await init_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Shutting down...")


app = FastAPI(
    title="Research In Public API",
    description="Backend API for Research In Public - Agentic Support Ecosystem",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration: Allow browser requests from frontend
# Service-to-service requests don't need CORS (same-origin or authenticated)
cors_origins = settings.frontend_cors_origins.copy()

# In production, add Cloud Run frontend URL if available
if os.getenv("ENVIRONMENT") == "production":
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        cors_origins.append(frontend_url)
        logger.info(f"Added frontend URL to CORS: {frontend_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionRequest(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    main_response: str
    agent_used: str
    peer_matches: Optional[str] = None
    social_draft: Optional[str] = None
    guardian_report: Optional[Dict[str, Any]] = None
    agent_metadata: Optional[Dict[str, Any]] = None
    trace_id: str = ""


class ContentScanRequest(BaseModel):
    content: str
    content_type: str = "draft"


class GuardianReportResponse(BaseModel):
    risk_level: str
    concerns: List[str]
    blocked: bool
    suggestions: List[str]


class DraftPostRequest(BaseModel):
    memory_context: Optional[str] = None


class SocialDraftResponse(BaseModel):
    content: str
    platform: str
    hashtags: List[str]
    guardian_report: GuardianReportResponse


class SessionSummaryResponse(BaseModel):
    session_id: str
    message_count: int
    created_at: str
    agents_used: List[str]


class StruggleMapNode(BaseModel):
    id: str
    x: float
    y: float
    struggle: str
    color: str
    size: float
    cluster_id: Optional[int] = None
    semantic_label: Optional[str] = None


class StruggleMapCluster(BaseModel):
    id: int
    semantic_label: str
    center_x: float
    center_y: float
    color: str


class StruggleMapResponse(BaseModel):
    nodes: List[StruggleMapNode]
    clusters: List[StruggleMapCluster] = []


class AddProfileRequest(BaseModel):
    struggle_text: str
    academic_stage: Optional[str] = None
    research_area: Optional[str] = None
    emotional_tags: Optional[List[str]] = None


class AddProfileResponse(BaseModel):
    profile_id: str
    success: bool
    message: str


class VectorStoreStatsResponse(BaseModel):
    total_profiles: int
    total_embeddings: int
    using_faiss: bool
    persistence_path: str
    additions_since_save: int


# API Routes

@app.get("/")
async def root():
    """Root endpoint - basic health check."""
    return {"status": "ok", "message": "Research In Public API"}


@app.get("/health")
async def health_check():
    """Health check endpoint - responds immediately, even before full initialization."""
    return {
        "status": "ok",
        "service": "research-in-public-api",
        "orchestrator_ready": orchestrator is not None
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - indicates if service is fully ready to handle requests."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not ready - orchestrator not initialized")
    return {"status": "ready", "orchestrator_ready": True}


@app.post("/v1/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new conversation session."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    logger.info(f"[create_session] Creating session for user_id: {request.user_id}")
    session = orchestrator.create_session(request.user_id)
    sessions[session.session_id] = session
    logger.info(f"[create_session] Session created: {session.session_id}. Total sessions: {len(sessions)}")
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at.isoformat()
    )


@app.get("/v1/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session details."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at.isoformat()
    )


@app.get("/v1/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: str):
    """Get session summary."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    session = sessions[session_id]
    summary = orchestrator.get_session_summary(session)
    
    return SessionSummaryResponse(**summary)


class RecentSessionItem(BaseModel):
    session_id: str
    summary: str
    created_at: str
    message_count: int


class RecentSessionsResponse(BaseModel):
    sessions: List[RecentSessionItem]


@app.get("/v1/sessions", response_model=RecentSessionsResponse)
async def list_recent_sessions(
    user_id: str = Query(..., description="User ID to get sessions for"),
    limit: int = Query(3, description="Number of recent sessions to return")
):
    """Get recent sessions for a user."""
    user_sessions = [
        session for session in sessions.values()
        if session.user_id == user_id
    ]
    
    # Sort by created_at descending (most recent first)
    user_sessions.sort(key=lambda s: s.created_at, reverse=True)
    
    # Get recent sessions
    recent = user_sessions[:limit]
    
    # Generate summaries
    session_items = []
    for session in recent:
        # Generate one-sentence summary from first user message
        summary = "New conversation"
        if session.messages:
            first_user_msg = next(
                (msg for msg in session.messages if msg.role == "user"),
                None
            )
            if first_user_msg:
                # Use first 100 chars as summary
                text = first_user_msg.content
                if len(text) > 100:
                    text = text[:100] + "..."
                summary = text
        
        session_items.append(RecentSessionItem(
            session_id=session.session_id,
            summary=summary,
            created_at=session.created_at.isoformat(),
            message_count=len(session.messages)
        ))
    
    return RecentSessionsResponse(sessions=session_items)


async def stream_agent_response(
    session: ConversationSession,
    message: str,
    agent_mode: str,
    force_matchmaker: bool = False
):
    """Stream agent response using SSE."""
    try:
        logger.info(f"[stream_agent_response] Processing message: {message[:50]}... (agent_mode={agent_mode})")
        # Process message through orchestrator
        responses = orchestrator.process_message(
            message=message,
            session=session,
            agent_mode=agent_mode,
            force_matchmaker=force_matchmaker
        )
        
        logger.info(f"[stream_agent_response] Got response from orchestrator. Agent: {responses.get('agent_used', 'unknown')}, Response length: {len(responses.get('main_response', ''))}")
        
        # Stream the main response in chunks (not word-by-word to avoid repetition issues)
        main_response = responses.get("main_response", "")
        
        if not main_response:
            logger.warning("[stream_agent_response] Empty main_response! Sending error chunk.")
            error_chunk = {
                "type": "error",
                "error": "Agent returned empty response",
                "done": True
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            return
        # Split into sentences for better streaming
        import re
        sentences = re.split(r'([.!?]\s+)', main_response)
        # Recombine sentences with their punctuation
        chunks = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                chunks.append(sentences[i] + sentences[i + 1])
            else:
                chunks.append(sentences[i])
        
        # If no sentence breaks, split into reasonable chunks
        if len(chunks) == 1 and len(chunks[0]) > 100:
            # Split long text into ~50 char chunks
            text = chunks[0]
            chunks = [text[i:i+50] for i in range(0, len(text), 50)]
        
        logger.info(f"[stream_agent_response] Splitting into {len(chunks)} chunks")
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():  # Only send non-empty chunks
                chunk = {
                    "type": "text",
                    "text": chunk_text,
                    "done": False
                }
                logger.debug(f"[stream_agent_response] Sending chunk {i+1}/{len(chunks)}: {chunk_text[:50]}...")
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.03)  # Small delay for typing effect
        
        # Send final response with all metadata
        logger.info(f"[stream_agent_response] Sending final chunk with metadata")
        final_chunk = {
            "type": "complete",
            "main_response": responses.get("main_response", ""),
            "agent_used": responses.get("agent_used", ""),
            "peer_matches": responses.get("peer_matches"),
            "social_draft": responses.get("social_draft"),
            "guardian_report": responses.get("guardian_report").dict() if responses.get("guardian_report") else None,
            "agent_metadata": responses.get("agent_metadata"),
            "trace_id": session.session_id,
            "done": True
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        logger.info(f"[stream_agent_response] Stream completed successfully")
        
    except Exception as e:
        logger.error(f"[stream_agent_response] Error streaming response: {str(e)}", exc_info=True)
        error_chunk = {
            "type": "error",
            "error": str(e),
            "done": True
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


@app.post("/v1/sessions/{session_id}/messages")
async def process_message(
    session_id: str,
    message: MessageRequest,
    request: Request,
    agent_mode: str = Query("auto", regex="^(auto|vent|pi|scribe|matchmaker)$"),
    stream: bool = Query(False),
    force_matchmaker: bool = Query(False, description="Force Semantic Matchmaker to run")
):
    """Process a message through the agent system."""
    logger.info(f"[process_message] Received request for session_id: {session_id}, agent_mode: {agent_mode}, stream: {stream}")
    logger.info(f"[process_message] Current sessions: {list(sessions.keys())}")
    
    if session_id not in sessions:
        logger.error(f"[process_message] Session {session_id} not found. Available sessions: {list(sessions.keys())}")
        logger.error(f"[process_message] This usually means the server was restarted. Frontend should create a new session.")
        raise HTTPException(
            status_code=404, 
            detail=f"Session not found. The server may have restarted. Please refresh the page to create a new session."
        )
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    session = sessions[session_id]
    
    # Add user message to session
    session.messages.append(ConversationMessage(
        role="user",
        content=message.content,
        agent=None
    ))
    
    if stream:
        # Get force_matchmaker from query params
        force_matchmaker = request.query_params.get("force_matchmaker", "false").lower() == "true"
        # Return SSE stream
        return StreamingResponse(
            stream_agent_response(session, message.content, agent_mode, force_matchmaker),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    else:
        # Return complete response
        responses = orchestrator.process_message(
            message=message.content,
            session=session,
            agent_mode=agent_mode,
            force_matchmaker=False  # Non-streaming doesn't support force_matchmaker yet
        )
        
        # Add assistant message to session
        if responses.get("main_response"):
            session.messages.append(ConversationMessage(
                role="assistant",
                content=responses["main_response"],
                agent=responses.get("agent_used")
            ))
        
        return MessageResponse(
            main_response=responses.get("main_response", ""),
            agent_used=responses.get("agent_used", ""),
            peer_matches=responses.get("peer_matches"),
            social_draft=responses.get("social_draft"),
            guardian_report=responses.get("guardian_report").dict() if responses.get("guardian_report") else None,
            agent_metadata=responses.get("agent_metadata"),
            trace_id=session.session_id
        )


@app.post("/v1/content/scan", response_model=GuardianReportResponse)
async def scan_content(request: ContentScanRequest):
    """Scan content for IP risks using Guardian agent."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        guardian_report = orchestrator.guardian.scan_content(request.content)
        
        return GuardianReportResponse(
            risk_level=guardian_report.risk_level.value,
            concerns=guardian_report.concerns,
            blocked=guardian_report.blocked,
            suggestions=guardian_report.suggestions
        )
    except Exception as e:
        logger.error(f"Error scanning content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scan content: {str(e)}")


@app.post("/v1/scribe/draft", response_model=SocialDraftResponse)
async def draft_social_post(
    session_id: str = Query(...),
    request: Optional[DraftPostRequest] = None
):
    """Draft a social media post using The Scribe agent."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    session = sessions[session_id]
    
    try:
        # If memory_context is provided, use it directly (from ScribeTool)
        if request and request.memory_context:
            conversation_text = request.memory_context
            # Always allow drafting from direct input
            shareable = True
        else:
            # Get recent conversation context
            recent_messages = session.messages[-5:] if len(session.messages) > 5 else session.messages
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in recent_messages
            ])
            # Check if shareable moment
            shareable = orchestrator.scribe.detect_shareable_moment(conversation_text)
        
        if not shareable:
            raise HTTPException(
                status_code=400,
                detail="No shareable moment detected in conversation"
            )
        
        # Agentic flow: Guardian first, then Scribe
        # Step 1: Guardian scans raw text to identify sensitive info
        logger.info(f"[Scribe Draft] Step 1: Guardian scanning raw text (length: {len(conversation_text)})")
        initial_guardian_report = orchestrator.guardian.scan_content(conversation_text)
        logger.info(f"[Scribe Draft] Guardian scan complete. Risk: {initial_guardian_report.risk_level}, Concerns: {len(initial_guardian_report.concerns)}")
        
        # Step 2: Scribe rewrites into professional LinkedIn post
        # Pass Guardian's findings to ensure sensitive info is removed
        from tools.social_draft import draft_social_content
        
        if request and request.memory_context:
            # Two-step agentic flow: Guardian sanitizes, then Scribe rewrites
            # Pass raw text + Guardian findings to Scribe for professional rewrite
            logger.info(f"[Scribe Draft] Step 2: Calling Scribe to rewrite raw text into professional post")
            logger.info(f"[Scribe Draft] Raw text preview: {conversation_text[:100]}...")
            draft_dict = draft_social_content(
                raw_text=conversation_text,
                platform="linkedin",
                guardian_findings=initial_guardian_report
            )
            logger.info(f"[Scribe Draft] Scribe returned content (length: {len(draft_dict.get('content', ''))})")
        else:
            # Extract insight and draft from conversation
            insight = orchestrator.scribe.extract_insight(conversation_text)
            draft_dict = draft_social_content(
                topic=insight["topic"],
                mood=insight["mood"],
                platform="linkedin"
            )
        
        # Clean up the content - remove any "Here is..." type prefixes
        content = draft_dict.get("content", "").strip()
        
        # Validate content was generated
        if not content:
            logger.error("Scribe failed to generate content. draft_dict: %s", draft_dict)
            raise HTTPException(
                status_code=500,
                detail="Failed to generate professional draft. Please try again."
            )
        
        # Remove common introductory phrases
        import re
        content = re.sub(r'^(Here is|Of course|I\'ll help you|I can help|Let me|Sure, here|Here\'s|Here are|I\'ve|I have).*?(\n\n|\n|$)', '', content, flags=re.IGNORECASE | re.MULTILINE)
        content = content.strip()
        
        # Final validation - ensure we have content
        if not content:
            logger.error("Content is empty after cleanup. Original: %s", draft_dict.get("content", ""))
            raise HTTPException(
                status_code=500,
                detail="Generated content is empty. Please try again."
            )
        
        logger.info(f"Generated professional draft (length: {len(content)}): {content[:100]}...")
        
        # Step 3: Final Guardian scan on the professional draft
        guardian_report = orchestrator.guardian.scan_content(content)
        
        return SocialDraftResponse(
            content=content,
            platform=draft_dict.get("platform", "linkedin"),
            hashtags=draft_dict.get("hashtags", []),
            guardian_report=GuardianReportResponse(
                risk_level=guardian_report.risk_level.value,
                concerns=guardian_report.concerns,
                blocked=guardian_report.blocked,
                suggestions=guardian_report.suggestions
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error drafting post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to draft post: {str(e)}")


@app.post("/v1/vector-store/profiles", response_model=AddProfileResponse)
async def add_profile_to_vector_store(request: AddProfileRequest):
    """Manually add a profile to the vector store."""
    if not orchestrator or not orchestrator.vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    try:
        profile_id = orchestrator.vector_store.add_peer_profile_from_session(
            struggle_text=request.struggle_text,
            user_id="manual",
            academic_stage=request.academic_stage,
            research_area=request.research_area,
            emotional_tags=request.emotional_tags
        )
        
        if profile_id:
            return AddProfileResponse(
                profile_id=profile_id,
                success=True,
                message=f"Profile {profile_id} added successfully"
            )
        else:
            return AddProfileResponse(
                profile_id="",
                success=False,
                message="Profile rejected (duplicate or invalid)"
            )
    except Exception as e:
        logger.error(f"Error adding profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add profile: {str(e)}")


@app.get("/v1/vector-store/stats", response_model=VectorStoreStatsResponse)
async def get_vector_store_stats():
    """Get vector store statistics."""
    if not orchestrator or not orchestrator.vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    try:
        stats = orchestrator.vector_store.get_stats()
        return VectorStoreStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/v1/vector-store/reload")
async def reload_vector_store():
    """Reload vector store from persistence file."""
    if not orchestrator or not orchestrator.vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    try:
        # Reload persisted data
        orchestrator.vector_store._load_persisted_data()
        return {"success": True, "message": "Vector store reloaded from persistence"}
    except Exception as e:
        logger.error(f"Error reloading vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reload: {str(e)}")


@app.post("/v1/vector-store/save")
async def save_vector_store():
    """Manually save vector store to persistence file."""
    if not orchestrator or not orchestrator.vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    try:
        success = orchestrator.vector_store.save_to_json()
        if success:
            return {"success": True, "message": "Vector store saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save vector store")
    except Exception as e:
        logger.error(f"Error saving vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.get("/v1/users/{user_id}/struggles/nearby", response_model=StruggleMapResponse)
async def get_struggle_map(user_id: str):
    """Get struggle map visualization data with clustering and semantic labels."""
    if not orchestrator or not orchestrator.matchmaker:
        raise HTTPException(status_code=503, detail="Matchmaker not available")
    
    try:
        # Get user's recent messages to find similar struggles
        user_struggles = []
        for session in sessions.values():
            if session.user_id == user_id:
                for msg in session.messages[-3:]:  # Last 3 messages
                    if msg.role == "user":
                        user_struggles.append(msg.content)
        
        if not user_struggles:
            # Return empty map if no user struggles
            return StruggleMapResponse(nodes=[], clusters=[])
        
        # Use the most recent struggle as query
        query_text = user_struggles[-1]
        
        # Find similar peers
        matches = orchestrator.matchmaker.find_similar_peers(
            query_text=query_text,
            top_k=15,
            threshold=0.5  # Lower threshold for visualization
        )
        
        if not matches:
            return StruggleMapResponse(nodes=[], clusters=[])
        
        # Get embeddings for clustering
        vector_store = orchestrator.matchmaker.vector_store
        embeddings = []
        profiles = []
        for match in matches:
            profile = vector_store.profiles.get(match.profile_id)
            if profile and profile.embedding:
                embeddings.append(profile.embedding)
                profiles.append((match, profile))
        
        if not embeddings:
            return StruggleMapResponse(nodes=[], clusters=[])
        
        # Try to use sklearn for clustering and t-SNE, fallback to simple distribution
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            from sklearn.manifold import TSNE
            use_sklearn = True
        except ImportError:
            logger.warning("sklearn not available, using simple distribution")
            use_sklearn = False
        
        if not use_sklearn:
            # Fallback: improved distribution using similarity-based positioning
            import math
            nodes = []
            colors = ['#FF6B9D', '#5B4BFF', '#10B981', '#F59E0B', '#3B82F6', '#8B5CF6']
            
            # Use a spiral distribution for more natural look
            center_x, center_y = 50, 50
            angle_step = 2 * math.pi / len(profiles) if len(profiles) > 0 else 0
            
            for i, (match, profile) in enumerate(profiles):
                # Spiral out from center based on similarity (higher similarity = closer to center)
                distance = 20 + (1 - match.similarity_score) * 35  # Distance from center
                angle = i * angle_step
                
                x = center_x + distance * math.cos(angle)
                y = center_y + distance * math.sin(angle)
                
                # Ensure nodes stay within bounds
                x = max(10, min(90, x))
                y = max(10, min(90, y))
                
                nodes.append(StruggleMapNode(
                    id=match.profile_id,
                    x=float(x),
                    y=float(y),
                    struggle=profile.struggle_text[:50] + "..." if len(profile.struggle_text) > 50 else profile.struggle_text,
                    color=colors[i % len(colors)],
                    size=float(8 + (match.similarity_score * 12)),
                    cluster_id=0  # All in one cluster for fallback
                ))
            return StruggleMapResponse(nodes=nodes, clusters=[])
        
        # Use sklearn for clustering and t-SNE
        n_clusters = min(4, len(embeddings))
        if n_clusters < 2:
            n_clusters = 1
        
        # Use sklearn for clustering
        n_clusters = min(4, len(embeddings))
        if n_clusters < 2:
            n_clusters = 1
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Decide layout method based on data size
        # Use t-SNE only for larger datasets where it's stable
        if len(embeddings) >= 20:
            # Use t-SNE for 2D visualization
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
            coords_2d = tsne.fit_transform(embeddings)
            
            # Normalize coordinates
            x_min, x_max = coords_2d[:, 0].min(), coords_2d[:, 0].max()
            y_min, y_max = coords_2d[:, 1].min(), coords_2d[:, 1].max()
            x_range = x_max - x_min if x_max != x_min else 1
            y_range = y_max - y_min if y_max != y_min else 1
            padding = 10
            
            normalized_coords = []
            for i in range(len(coords_2d)):
                x = float(((coords_2d[i, 0] - x_min) / x_range) * (100 - 2 * padding) + padding)
                y = float(((coords_2d[i, 1] - y_min) / y_range) * (100 - 2 * padding) + padding)
                normalized_coords.append((x, y))
        else:
            # Use Sector/Spiral Layout for smaller datasets (clearer clustering)
            import math
            import random
            normalized_coords = [(0.0, 0.0)] * len(embeddings)
            center_x, center_y = 50.0, 50.0
            
            # Assign sectors to clusters
            sector_angle = 2 * math.pi / n_clusters
            
            for i, cluster_id in enumerate(cluster_labels):
                # Base angle for this cluster's sector
                base_angle = cluster_id * sector_angle
                
                # Random position within sector
                # Angle variation within sector (leaving some gap)
                angle_offset = random.uniform(0.2, sector_angle - 0.2)
                angle = base_angle + angle_offset
                
                # Distance from center (randomized but keeping away from absolute center)
                # Use similarity score to determine distance if available (closer = more similar)
                similarity = profiles[i][0].similarity_score
                dist = 15 + (1 - similarity) * 30 + random.uniform(-5, 5)
                
                x = center_x + dist * math.cos(angle)
                y = center_y + dist * math.sin(angle)
                
                # Clamp to bounds
                x = max(10, min(90, x))
                y = max(10, min(90, y))
                
                normalized_coords[i] = (x, y)
        
        # Generate semantic labels for clusters using Gemini
        cluster_labels_map = {}
        clusters_data = []
        colors = ['#FF6B9D', '#5B4BFF', '#CCFF00', '#FF9F43', '#00D4FF']
        
        for cluster_id in range(n_clusters):
            cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
            cluster_struggles = [profiles[i][1].struggle_text for i in cluster_indices]
            
            if cluster_struggles:
                # Generate semantic label for cluster
                try:
                    prompt = f"""Analyze these research struggles and provide a single semantic word or short phrase (2-3 words max) that captures their common theme:

Struggles:
{chr(10).join(cluster_struggles[:5])}

Respond with ONLY the semantic label, nothing else:"""
                    
                    semantic_label = gemini_service.generate_text(
                        prompt=prompt,
                        model_type="flash",
                        temperature=0.3
                    ).strip()
                    
                    # Clean up label
                    semantic_label = semantic_label.split('\n')[0].strip()
                    if len(semantic_label) > 20:
                        semantic_label = semantic_label[:20]
                except Exception as e:
                    logger.warning(f"Failed to generate semantic label for cluster {cluster_id}: {str(e)}")
                    semantic_label = f"Cluster {cluster_id + 1}"
                
                cluster_labels_map[cluster_id] = semantic_label
                
                # Calculate cluster center from actual node positions
                cluster_x_sum = sum(normalized_coords[i][0] for i in cluster_indices)
                cluster_y_sum = sum(normalized_coords[i][1] for i in cluster_indices)
                count = len(cluster_indices)
                
                clusters_data.append(StruggleMapCluster(
                    id=cluster_id,
                    semantic_label=semantic_label,
                    center_x=cluster_x_sum / count if count > 0 else 50.0,
                    center_y=cluster_y_sum / count if count > 0 else 50.0,
                    color=colors[cluster_id % len(colors)]
                ))
        
        # Convert to response nodes
        nodes = []
        for i, (match, profile) in enumerate(profiles):
            cluster_id = int(cluster_labels[i])
            semantic_label = cluster_labels_map.get(cluster_id, None)
            
            x, y = normalized_coords[i]
            
            nodes.append(StruggleMapNode(
                id=match.profile_id,
                x=x,
                y=y,
                struggle=profile.struggle_text[:50] + "..." if len(profile.struggle_text) > 50 else profile.struggle_text,
                color=colors[cluster_id % len(colors)],
                size=float(8 + (match.similarity_score * 12)),
                cluster_id=cluster_id,
                semantic_label=semantic_label
            ))
        
        return StruggleMapResponse(nodes=nodes, clusters=clusters_data)
        
    except Exception as e:
        logger.error(f"Error getting struggle map: {str(e)}")
        # Fallback to simple distribution
        try:
            matches = orchestrator.matchmaker.find_similar_peers(
                query_text=user_struggles[-1] if user_struggles else "",
                top_k=12,
                threshold=0.6
            )
            nodes = []
            colors = ['#FF6B9D', '#5B4BFF', '#CCFF00', '#FF9F43']
            for i, match in enumerate(matches):
                profile = orchestrator.matchmaker.vector_store.profiles.get(match.profile_id)
                if profile:
                    nodes.append(StruggleMapNode(
                        id=match.profile_id,
                        x=float((i * 7.5) % 100),
                        y=float((i * 11.3) % 100),
                        struggle=profile.struggle_text[:50] + "..." if len(profile.struggle_text) > 50 else profile.struggle_text,
                        color=colors[i % len(colors)],
                        size=float(10 + (match.similarity_score * 20))
                    ))
            return StruggleMapResponse(nodes=nodes, clusters=[])
        except:
            raise HTTPException(status_code=500, detail=f"Failed to get struggle map: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

