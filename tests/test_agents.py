"""Comprehensive tests for agents and all features."""

import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set test API key if not present
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "test_key"

# Check if we have a real API key for integration tests
HAS_API_KEY = os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "test_key"


# ============================================================================
# Basic Initialization Tests
# ============================================================================

def test_vent_validator_initialization():
    """Test Vent Validator agent initialization."""
    from agents.vent_validator import VentValidatorAgent
    
    agent = VentValidatorAgent()
    assert agent.name == "Vent Validator"
    assert agent.system_prompt is not None


def test_semantic_matchmaker_initialization():
    """Test Semantic Matchmaker initialization."""
    from agents.semantic_matchmaker import SemanticMatchmakerAgent
    from services.vector_search_local import LocalVectorSearch
    
    vector_store = LocalVectorSearch()
    agent = SemanticMatchmakerAgent(vector_store)
    assert agent.name == "Semantic Matchmaker"


def test_scribe_initialization():
    """Test Scribe agent initialization."""
    from agents.scribe import ScribeAgent
    
    agent = ScribeAgent()
    assert agent.name == "The Scribe"
    assert agent.system_prompt is not None


def test_guardian_initialization():
    """Test Guardian agent initialization."""
    from agents.guardian import GuardianAgent
    
    agent = GuardianAgent()
    assert agent.name == "The Guardian"
    assert agent.system_prompt is not None


def test_pi_simulator_initialization():
    """Test PI Simulator agent initialization."""
    from agents.pi_simulator import PISimulatorAgent
    
    agent = PISimulatorAgent()
    assert agent.name == "PI Simulator"
    assert agent.system_prompt is not None


def test_orchestrator_creation():
    """Test agent orchestrator creation."""
    from orchestration.agent_orchestrator import AgentOrchestrator
    from services.vector_search_local import LocalVectorSearch
    
    vector_store = LocalVectorSearch()
    orchestrator = AgentOrchestrator(vector_store=vector_store)
    
    assert orchestrator.vent_validator is not None
    assert orchestrator.matchmaker is not None
    assert orchestrator.scribe is not None
    assert orchestrator.guardian is not None
    assert orchestrator.pi_simulator is not None


# ============================================================================
# Scribe Detection Tests
# ============================================================================

def test_scribe_detection():
    """Test Scribe shareable moment detection."""
    from agents.scribe import ScribeAgent
    
    agent = ScribeAgent()
    
    # Should detect shareable moment
    shareable = "I finally learned why my experiments kept failing."
    assert agent.detect_shareable_moment(shareable) == True
    
    # Should not detect
    not_shareable = "My experiment failed again."
    assert agent.detect_shareable_moment(not_shareable) == False


def test_scribe_detection_keywords():
    """Test Scribe detection with various keywords."""
    from agents.scribe import ScribeAgent
    
    agent = ScribeAgent()
    
    shareable_moments = [
        "I finally learned why my experiments kept failing.",
        "I realized the solution was simple.",
        "I understood the problem after months of work.",
        "I had a breakthrough moment today.",
        "I figured out the issue.",
        "I resolved the problem.",
        "I overcame my fear of failure.",
    ]
    
    for moment in shareable_moments:
        assert agent.detect_shareable_moment(moment) == True, f"Should detect: {moment}"
    
    not_shareable = [
        "My experiment failed again.",
        "I'm still struggling.",
        "Nothing is working.",
    ]
    
    for moment in not_shareable:
        assert agent.detect_shareable_moment(moment) == False, f"Should not detect: {moment}"


# ============================================================================
# Intent Classification Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_intent_classification():
    """Test intent classifier with various message types."""
    from orchestration.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    test_cases = [
        ("I'm struggling with my research", "emotional"),
        ("How does semantic search work?", "technical"),
        ("I got my paper accepted!", "positive"),
        ("Can you review my grant?", "grant"),
    ]
    
    for message, expected in test_cases:
        result = classifier.classify(message)
        intent = result['intent']
        assert intent == expected, f"Expected {expected}, got {intent} for: {message}"


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_intent_classification_keywords():
    """Test intent classification with keyword fallback."""
    from orchestration.intent_classifier import IntentClassifier
    
    classifier = IntentClassifier()
    
    # Technical keywords
    technical_messages = [
        "I'm working on semantic search algorithms",
        "How do you debug agentic systems?",
        "What's the best implementation method?",
    ]
    
    for msg in technical_messages:
        result = classifier.classify(msg)
        assert result['intent'] == "technical", f"Should be technical: {msg}"
    
    # Positive keywords
    positive_messages = [
        "I swam with a friend today",
        "We discussed research methods",
        "I'm excited about my progress",
    ]
    
    for msg in positive_messages:
        result = classifier.classify(msg)
        assert result['intent'] in ["positive", "technical"], f"Should be positive/technical: {msg}"


# ============================================================================
# Guardian IP Safety Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_guardian_safe_content():
    """Test Guardian with safe content."""
    from agents.guardian import GuardianAgent
    
    agent = GuardianAgent()
    safe_content = "I've been working on my research and learning about resilience."
    
    report = agent.scan_content(safe_content)
    assert report is not None
    assert report.risk_level.value in ["LOW", "MEDIUM", "HIGH"]


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_guardian_risky_content():
    """Test Guardian with risky content."""
    from agents.guardian import GuardianAgent
    
    agent = GuardianAgent()
    risky_content = "I'm using reagent X-1234 from Company Y."
    
    report = agent.scan_content(risky_content)
    assert report is not None
    # Risky content should be flagged
    assert report.risk_level.value in ["MEDIUM", "HIGH"]


# ============================================================================
# Gemini Service Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_gemini_service_generate_text():
    """Test Gemini service text generation."""
    from services.gemini_service import gemini_service
    
    response = gemini_service.generate_text(
        prompt="Say 'Hello, World!'",
        model_type="flash",
        temperature=0.7
    )
    
    assert response is not None
    assert len(response) > 0
    assert "Hello" in response or "hello" in response.lower()


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_gemini_service_chat_completion():
    """Test Gemini service chat completion."""
    from services.gemini_service import gemini_service
    from data.schemas import ConversationSession, ConversationMessage
    
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    response = gemini_service.chat_completion(
        messages=messages,
        model_type="flash",
        temperature=0.7
    )
    
    assert response is not None
    assert len(response) > 0


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_gemini_service_with_system_instruction():
    """Test Gemini service with system instruction."""
    from services.gemini_service import gemini_service
    
    response = gemini_service.generate_text(
        prompt="What is your role?",
        model_type="flash",
        system_instruction="You are a helpful research assistant.",
        temperature=0.7
    )
    
    assert response is not None
    assert len(response) > 0


# ============================================================================
# Vector Search and Embeddings Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_embedding_service():
    """Test embedding service."""
    from services.embedding_service import EmbeddingService
    
    embedding_service = EmbeddingService()
    embedding = embedding_service.generate_embedding("Test text for embedding")
    
    assert embedding is not None
    assert len(embedding) > 0
    assert isinstance(embedding, list)


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_vector_search_similarity():
    """Test vector search similarity calculation."""
    from services.embedding_service import EmbeddingService
    
    embedding_service = EmbeddingService()
    
    text1 = "I'm struggling with my research"
    text2 = "I'm having difficulties with my work"
    text3 = "The weather is nice today"
    
    emb1 = embedding_service.generate_embedding(text1)
    emb2 = embedding_service.generate_embedding(text2)
    emb3 = embedding_service.generate_embedding(text3)
    
    # Calculate similarities
    sim_12 = embedding_service.cosine_similarity(emb1, emb2)
    sim_13 = embedding_service.cosine_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity
    assert sim_12 > sim_13, "Similar texts should have higher similarity"


# ============================================================================
# End-to-End Integration Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_orchestrator_emotional_message():
    """Test orchestrator with emotional message."""
    from orchestration.agent_orchestrator import AgentOrchestrator
    from services.vector_search_local import LocalVectorSearch
    from data.schemas import ConversationSession
    
    vector_store = LocalVectorSearch()
    orchestrator = AgentOrchestrator(vector_store=vector_store)
    session = ConversationSession(user_id="test_emotional")
    
    response = orchestrator.process_message(
        message="I'm frustrated with my research progress.",
        session=session,
        agent_mode="auto"
    )
    
    assert response is not None
    assert len(response) > 0
    # Should route to Vent Validator
    assert "vent" in response.lower() or "understand" in response.lower() or "feel" in response.lower()


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_orchestrator_technical_message():
    """Test orchestrator with technical message."""
    from orchestration.agent_orchestrator import AgentOrchestrator
    from services.vector_search_local import LocalVectorSearch
    from data.schemas import ConversationSession
    
    vector_store = LocalVectorSearch()
    orchestrator = AgentOrchestrator(vector_store=vector_store)
    session = ConversationSession(user_id="test_technical")
    
    response = orchestrator.process_message(
        message="How does semantic search work for debugging?",
        session=session,
        agent_mode="auto"
    )
    
    assert response is not None
    assert len(response) > 0
    # Should route to Academic Peer, not Vent Validator


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_orchestrator_grant_message():
    """Test orchestrator with grant review request."""
    from orchestration.agent_orchestrator import AgentOrchestrator
    from services.vector_search_local import LocalVectorSearch
    from data.schemas import ConversationSession
    
    vector_store = LocalVectorSearch()
    orchestrator = AgentOrchestrator(vector_store=vector_store)
    session = ConversationSession(user_id="test_grant")
    
    response = orchestrator.process_message(
        message="Can you review my grant proposal?",
        session=session,
        agent_mode="auto"
    )
    
    assert response is not None
    assert len(response) > 0
    # Should route to PI Simulator


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_conversation_history():
    """Test that conversation history is maintained."""
    from orchestration.agent_orchestrator import AgentOrchestrator
    from services.vector_search_local import LocalVectorSearch
    from data.schemas import ConversationSession
    
    vector_store = LocalVectorSearch()
    orchestrator = AgentOrchestrator(vector_store=vector_store)
    session = ConversationSession(user_id="test_history")
    
    # First message
    response1 = orchestrator.process_message(
        message="I'm working on semantic search.",
        session=session,
        agent_mode="auto"
    )
    
    # Second message that references the first
    response2 = orchestrator.process_message(
        message="Can you tell me more about that?",
        session=session,
        agent_mode="auto"
    )
    
    assert response1 is not None
    assert response2 is not None
    assert len(session.messages) >= 4  # At least 2 user + 2 assistant messages


# ============================================================================
# Evaluation Features Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_empathy_scorer():
    """Test empathy scoring."""
    from evaluation.empathy_scorer import EmpathyScorer
    
    scorer = EmpathyScorer()
    
    result = scorer.score_response(
        user_message="I'm struggling with my research",
        agent_response="I understand how frustrating that can be. Research is challenging."
    )
    
    assert result is not None
    assert 'score' in result
    assert 'reasoning' in result
    assert 1.0 <= result['score'] <= 5.0


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_safety_checker():
    """Test safety checker."""
    from evaluation.safety_checker import SafetyChecker
    
    checker = SafetyChecker()
    
    # Test safe content
    safe_result = checker.test_content("I've been working on my research.")
    assert safe_result is not None
    assert 'risk_level' in safe_result
    assert 'blocked' in safe_result
    
    # Test risky content
    risky_result = checker.test_content("I'm using reagent X-1234 from Company Y.")
    assert risky_result is not None
    assert risky_result['risk_level'] in ['MEDIUM', 'HIGH']


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_safety_checker_test_suite():
    """Test safety checker test suite."""
    from evaluation.safety_checker import SafetyChecker
    
    checker = SafetyChecker()
    results = checker.test_suite()
    
    assert results is not None
    assert 'total_tests' in results
    assert 'passed' in results
    assert 'failed' in results
    assert 'accuracy' in results
    assert results['total_tests'] > 0


# ============================================================================
# Agent-Specific Processing Tests
# ============================================================================

@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_vent_validator_processing():
    """Test Vent Validator message processing."""
    from agents.vent_validator import VentValidatorAgent
    from data.schemas import ConversationSession
    
    agent = VentValidatorAgent()
    session = ConversationSession(user_id="test_vent")
    
    response = agent.process(
        message="I'm struggling with my research and feel like giving up.",
        session=session
    )
    
    assert response is not None
    assert len(response) > 0
    assert len(session.messages) >= 2  # User message + response


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_pi_simulator_grant_critique():
    """Test PI Simulator grant critique."""
    from agents.pi_simulator import PISimulatorAgent
    
    agent = PISimulatorAgent()
    
    grant_text = """
    Title: Novel Approaches to Protein Folding
    Abstract: We propose to investigate protein folding mechanisms using novel computational methods.
    """
    
    critique = agent.critique_grant(grant_text)
    
    assert critique is not None
    assert len(critique) > 0


@pytest.mark.skipif(not HAS_API_KEY, reason="Requires valid API key")
def test_semantic_matchmaker_peer_matching():
    """Test Semantic Matchmaker peer finding."""
    from agents.semantic_matchmaker import SemanticMatchmakerAgent
    from services.vector_search_local import LocalVectorSearch
    from data.schemas import ConversationSession
    
    vector_store = LocalVectorSearch()
    agent = SemanticMatchmakerAgent(vector_store)
    session = ConversationSession(user_id="test_match")
    
    # Add some context
    from data.schemas import ConversationMessage
    session.messages.append(
        ConversationMessage(
            role='user',
            content='I\'m struggling with my experiments'
        )
    )
    
    matches = agent.find_similar_peers(
        message="I'm frustrated with my research progress.",
        session=session
    )
    
    assert matches is not None
    assert isinstance(matches, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
