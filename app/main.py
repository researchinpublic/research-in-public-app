"""Streamlit web application for Research In Public."""

import streamlit as st
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from orchestration.agent_orchestrator import AgentOrchestrator
from services.vector_search_local import LocalVectorSearch
from data.schemas import ConversationSession
from evaluation.empathy_scorer import EmpathyScorer
from evaluation.safety_checker import SafetyChecker


# Page configuration
st.set_page_config(
    page_title="Research In Public",
    page_icon="🔬",
    layout="wide"
)

# Initialize session state
if "orchestrator" not in st.session_state:
    # Load dummy struggles data
    data_path = Path(__file__).parent.parent / "data" / "dummy_struggles.json"
    
    # Initialize vector store
    vector_store = LocalVectorSearch()
    if data_path.exists():
        vector_store.load_from_json(str(data_path))
    
    # Initialize orchestrator
    st.session_state.orchestrator = AgentOrchestrator(vector_store=vector_store)
    st.session_state.sessions = {}

if "current_session" not in st.session_state:
    user_id = "demo_user"
    st.session_state.current_session = st.session_state.orchestrator.create_session(user_id)
    st.session_state.sessions[st.session_state.current_session.session_id] = st.session_state.current_session

if "messages" not in st.session_state:
    st.session_state.messages = []


def main():
    """Main application."""
    
    # Header
    st.title("🔬 Research In Public")
    st.markdown("### Agentic Support Ecosystem for PhD Students & Researchers")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🤖 Agents")
        st.markdown("""
        - **Vent Validator**: Emotional support & active listening
        - **Semantic Matchmaker**: Find peers with similar struggles
        - **The Scribe**: Draft public content from your journey
        - **The Guardian**: IP safety & compliance
        - **PI Simulator**: Grant critique & mentorship
        """)
        
        st.header("⚙️ Settings")
        agent_mode = st.selectbox(
            "Agent Mode",
            ["auto", "vent", "pi", "scribe"],
            help="Choose which agent to use, or 'auto' to let the system decide"
        )
        
        if st.button("🔄 New Session"):
            user_id = "demo_user"
            st.session_state.current_session = st.session_state.orchestrator.create_session(user_id)
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🧪 Run Safety Tests"):
            safety_checker = SafetyChecker()
            results = safety_checker.test_suite()
            
            st.subheader("Safety Test Results")
            st.metric("Accuracy", f"{results['accuracy']*100:.1f}%")
            st.metric("Passed", f"{results['passed']}/{results['total_tests']}")
            
            for result in results["results"]:
                status = "✅" if result["passed"] else "❌"
                st.write(f"{status} {result['test_name']}: {result['actual_risk']}")
    
    # Main chat interface
    st.header("💬 Chat")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "agent" in message and message["agent"]:
                st.caption(f"Agent: {message['agent']}")
    
    # Chat input
    if prompt := st.chat_input("Share your research struggles, questions, or insights..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process through orchestrator
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                responses = st.session_state.orchestrator.process_message(
                    prompt,
                    st.session_state.current_session,
                    agent_mode=agent_mode
                )
            
            # Display main response
            if responses["main_response"]:
                st.markdown(responses["main_response"])
                st.caption(f"Agent: {responses['agent_used']}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": responses["main_response"],
                    "agent": responses["agent_used"]
                })
            
            # Display peer matches
            if responses["peer_matches"]:
                st.markdown(responses["peer_matches"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": responses["peer_matches"],
                    "agent": "Semantic Matchmaker"
                })
            
            # Display social draft
            if responses["social_draft"]:
                st.markdown(responses["social_draft"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": responses["social_draft"],
                    "agent": "The Scribe"
                })
            
            # Display guardian report if high risk
            if responses["guardian_report"] and responses["guardian_report"].blocked:
                st.warning(f"⚠️ Guardian Alert: {responses['guardian_report'].risk_level} risk detected")
    
    # Session info
    with st.expander("📊 Session Info"):
        summary = st.session_state.orchestrator.get_session_summary(st.session_state.current_session)
        st.json(summary)
        
        # Empathy scoring (optional)
        if st.button("📈 Score Empathy"):
            if len(st.session_state.messages) >= 2:
                scorer = EmpathyScorer()
                user_msg = st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else ""
                agent_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
                
                if user_msg and agent_msg:
                    score_result = scorer.score_response(user_msg, agent_msg)
                    st.metric("Empathy Score", f"{score_result['score']}/5.0")
                    st.write("Reasoning:", score_result["reasoning"])


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ GEMINI_API_KEY not found. Please set it in your environment variables or .env file.")
        st.stop()
    
    main()

