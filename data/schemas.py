"""Data schemas and models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """IP risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UserEntry(BaseModel):
    """User journal/vent entry."""
    user_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    entry_type: str = "vent"  # vent, log, journal
    metadata: Optional[Dict[str, Any]] = None


class PeerProfile(BaseModel):
    """Anonymized peer profile for matching."""
    profile_id: str
    embedding: List[float]
    struggle_text: str
    academic_stage: Optional[str] = None  # e.g., "3rd year PhD", "Postdoc"
    research_area: Optional[str] = None  # Generic area, not specific
    anonymized_metadata: Dict[str, Any] = Field(default_factory=dict)


class MatchResult(BaseModel):
    """Peer match result."""
    profile_id: str
    similarity_score: float
    match_reason: str
    suggested_connection: bool = True


class SocialDraft(BaseModel):
    """Social media content draft."""
    content: str
    platform: str  # "linkedin" or "twitter"
    hashtags: List[str] = Field(default_factory=list)
    sanitized: bool = True
    risk_level: RiskLevel = RiskLevel.LOW


class GuardianReport(BaseModel):
    """IP safety report from Guardian agent."""
    risk_level: RiskLevel
    concerns: List[str] = Field(default_factory=list)
    blocked: bool = False
    suggestions: List[str] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    """Conversation message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent: Optional[str] = None  # Which agent generated this


class AgentMetadata(BaseModel):
    """Metadata for agent responses (emotional analysis, clarity score, etc.)."""
    # Vent Validator Metadata
    emotional_spectrum: Optional[str] = None  # e.g., "Anxiety", "Calm", "Frustration"
    emotional_intensity: Optional[int] = None  # 1-10 scale
    grounding_technique: Optional[str] = None
    
    # PI Simulator Metadata
    clarity_score: Optional[int] = None  # 0-100
    logic_score: Optional[int] = None  # 0-100
    critique_focus: Optional[str] = None  # e.g., "Methodology", "Significance"
    
    # Matchmaker Metadata (if needed beyond peer_matches)
    connection_potential: Optional[int] = None


class ConversationSession(BaseModel):
    """Conversation session."""
    session_id: str
    user_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)  # Long-term memory

