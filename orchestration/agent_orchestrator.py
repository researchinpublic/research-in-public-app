"""Agent orchestrator - coordinates multiple specialized agents."""

from typing import List, Dict, Any, Optional
from loguru import logger
import uuid
import json
import re
from datetime import datetime

from data.schemas import ConversationSession, ConversationMessage
from agents.vent_validator import VentValidatorAgent
from agents.semantic_matchmaker import SemanticMatchmakerAgent
from agents.scribe import ScribeAgent
from agents.guardian import GuardianAgent
from agents.pi_simulator import PISimulatorAgent
from services.vector_search_local import LocalVectorSearch
from services.gemini_service import gemini_service
from orchestration.intent_classifier import IntentClassifier
from config.settings import settings


class AgentOrchestrator:
    """Orchestrates multiple agents to handle user interactions."""
    
    def __init__(self, vector_store: Optional[LocalVectorSearch] = None):
        self.vent_validator = VentValidatorAgent()
        self.matchmaker = SemanticMatchmakerAgent(vector_store) if vector_store else None
        self.scribe = ScribeAgent()
        self.guardian = GuardianAgent()
        self.pi_simulator = PISimulatorAgent()
        self.intent_classifier = IntentClassifier()
        self.vector_store = vector_store
        
        logger.info("Agent orchestrator initialized")
    
    def create_session(self, user_id: str) -> ConversationSession:
        return ConversationSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            messages=[],
            created_at=datetime.now(),
            context={}
        )
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """Parse metadata from agent response and return clean text."""
        metadata = {}
        clean_response = response
        
        emotional_pattern = r"\[\[\s*EMOTIONAL_ANALYSIS\s*\]\]\s*(.*?)\s*\[\[\s*END_EMOTIONAL_ANALYSIS\s*\]\]"
        match = re.search(emotional_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                content = match.group(1).strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx+1]
                    data = json.loads(json_str)
                    metadata.update(data)
                    logger.info(f"Successfully parsed emotional analysis: {metadata}")
                else:
                    logger.warning(f"Could not find JSON object in emotional analysis block: {content[:100]}")
                
                clean_response = clean_response.replace(match.group(0), "").strip()
            except Exception as e:
                logger.warning(f"Failed to parse emotional analysis JSON: {e}")
                logger.debug(f"Raw content was: {match.group(1)[:200] if match else 'No match'}")

        clarity_pattern = r"\[\[\s*CLARITY_SCORE\s*\]\]\s*(.*?)\s*\[\[\s*END_CLARITY_SCORE\s*\]\]"
        match_pi = re.search(clarity_pattern, clean_response, re.DOTALL | re.IGNORECASE)
        if match_pi:
            try:
                content = match_pi.group(1).strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx+1]
                    data = json.loads(json_str)
                    if "clarity" in data: metadata["clarity_score"] = data["clarity"]
                    if "logic" in data: metadata["logic_score"] = data["logic"]
                    if "focus" in data: metadata["critique_focus"] = data["focus"]
                    logger.info(f"Successfully parsed clarity score: {metadata}")
                else:
                    logger.warning(f"Could not find JSON object in clarity score block: {content[:100]}")
                
                clean_response = clean_response.replace(match_pi.group(0), "").strip()
            except Exception as e:
                logger.warning(f"Failed to parse clarity score JSON: {e}")
                logger.debug(f"Raw content was: {match_pi.group(1)[:200] if match_pi else 'No match'}")
                
        return {"metadata": metadata, "clean_response": clean_response}

    def process_message(
        self,
        message: str,
        session: ConversationSession,
        agent_mode: str = "auto",
        force_matchmaker: bool = False
    ) -> Dict[str, Any]:
        responses = {
            "main_response": "",
            "peer_matches": "",
            "social_draft": "",
            "guardian_report": None,
            "agent_metadata": {},
            "agent_used": ""
        }
        
        try:
            intent = None
            if agent_mode == "auto":
                intent_result = self.intent_classifier.classify(message)
                intent = intent_result["intent"]
                agent_mode = self.intent_classifier.get_agent_mode(intent)
                logger.info(f"Detected intent: {intent}, routing to: {agent_mode}")
            
            if agent_mode == "vent":
                agent_output = self.vent_validator.process(message, session)
                
                if hasattr(agent_output, 'analysis') and hasattr(agent_output, 'response_text'):
                    responses["main_response"] = agent_output.response_text
                    responses["agent_metadata"] = agent_output.analysis.model_dump() if hasattr(agent_output.analysis, 'model_dump') else agent_output.analysis.dict()
                    responses["agent_used"] = "Vent Validator"
                else:
                    responses["main_response"] = str(agent_output)
                    responses["agent_used"] = "Vent Validator"
                
                self._capture_user_struggle(message, session, "emotional")
            elif agent_mode == "matchmaker":
                if self.matchmaker:
                    logger.info("Matchmaker mode: Running Semantic Matchmaker")
                    match_result = self.matchmaker.process(message, session, force=True)
                    
                    if isinstance(match_result, dict):
                        peer_matches = match_result.get("text", "")
                        matches_data = match_result.get("matches", [])
                    else:
                        peer_matches = match_result
                        matches_data = []
                        
                    if peer_matches:
                        responses["main_response"] = peer_matches
                        responses["agent_used"] = "Semantic Matchmaker"
                        if matches_data:
                            responses["agent_metadata"]["matches"] = matches_data
                    else:
                        responses["main_response"] = "I couldn't find any matching peers for your message. Try rephrasing or sharing more details about your research journey."
                        responses["agent_used"] = "Semantic Matchmaker"
                    
                    self._capture_user_struggle(message, session, "emotional")
                else:
                    responses["main_response"] = "Matchmaker service is not available."
                    responses["agent_used"] = "Semantic Matchmaker"
            elif agent_mode == "pi":
                raw_response = self.pi_simulator.process(message, session)
                parsed = self._parse_agent_response(raw_response)
                responses["main_response"] = parsed["clean_response"]
                responses["agent_metadata"] = parsed["metadata"]
                responses["agent_used"] = "PI Simulator"
            elif agent_mode == "scribe":
                scribe_response = self.scribe.process(message, session)
                if scribe_response:
                    responses["main_response"] = scribe_response
                    responses["agent_used"] = "The Scribe"
                    
                    guardian_report = self.guardian.scan_content(scribe_response)
                    responses["guardian_report"] = guardian_report
                    
                    if guardian_report.blocked:
                        responses["main_response"] = (
                            scribe_response +
                            f"\n\n⚠️ **Guardian Alert:** {guardian_report.risk_level} risk detected. "
                            f"Concerns: {', '.join(guardian_report.concerns)}"
                        )
                else:
                    responses["main_response"] = "I'm here to help you craft professional content. Share your thoughts and I'll transform them into shareable stories."
                    responses["agent_used"] = "The Scribe"
            else:
                if agent_mode == "auto":
                    if intent:
                        if intent == "emotional":
                            agent_output = self.vent_validator.process(message, session)
                            if hasattr(agent_output, 'analysis'):
                                responses["main_response"] = agent_output.response_text
                                responses["agent_metadata"] = agent_output.analysis.model_dump()
                                responses["agent_used"] = "Vent Validator"
                            else:
                                responses["main_response"] = str(agent_output)
                                responses["agent_used"] = "Vent Validator"
                        elif intent in ["technical", "grant"]:
                            raw_response = self.pi_simulator.process(message, session)
                            parsed = self._parse_agent_response(raw_response)
                            responses["main_response"] = parsed["clean_response"]
                            responses["agent_metadata"] = parsed["metadata"]
                            responses["agent_used"] = "PI Simulator"
                        elif intent == "shareable":
                            scribe_response = self.scribe.process(message, session)
                            if scribe_response:
                                responses["main_response"] = scribe_response
                                responses["agent_used"] = "The Scribe"
                                
                                guardian_report = self.guardian.scan_content(scribe_response)
                                responses["guardian_report"] = guardian_report
                                
                                if guardian_report.blocked:
                                    responses["main_response"] = (
                                        scribe_response +
                                        f"\n\n⚠️ **Guardian Alert:** {guardian_report.risk_level} risk detected. "
                                        f"Concerns: {', '.join(guardian_report.concerns)}"
                                    )
                            else:
                                responses["main_response"] = "I'm here to help you craft professional content. Share your thoughts and I'll transform them into shareable stories."
                                responses["agent_used"] = "The Scribe"
                        else:
                            agent_output = self.vent_validator.process(message, session)
                            if hasattr(agent_output, 'analysis'):
                                responses["main_response"] = agent_output.response_text
                                responses["agent_metadata"] = agent_output.analysis.model_dump()
                                responses["agent_used"] = "Vent Validator"
                            else:
                                responses["main_response"] = str(agent_output)
                                responses["agent_used"] = "Vent Validator"
                    else:
                        agent_output = self.vent_validator.process(message, session)
                        if hasattr(agent_output, 'analysis'):
                            responses["main_response"] = agent_output.response_text
                            responses["agent_metadata"] = agent_output.analysis.model_dump()
                            responses["agent_used"] = "Vent Validator"
                        else:
                            responses["main_response"] = str(agent_output)
                            responses["agent_used"] = "Vent Validator"
                
                if self.matchmaker and agent_mode == "auto":
                    is_emotional = False
                    if intent:
                        is_emotional = (intent == "emotional")
                    if not is_emotional:
                        is_emotional = self.matchmaker.is_emotional_struggle(message)
                    
                    if is_emotional:
                        logger.info("Auto mode: Running Semantic Matchmaker for emotional struggle")
                        match_result = self.matchmaker.process(message, session, force=False)
                        
                        # Handle dictionary return format
                        if isinstance(match_result, dict):
                            peer_matches_text = match_result.get("text", "")
                            matches_data = match_result.get("matches", [])
                        else:
                            peer_matches_text = match_result
                            matches_data = []
                        
                        if peer_matches_text:
                            responses["peer_matches"] = peer_matches_text
                            if matches_data:
                                if "matches" not in responses["agent_metadata"]:
                                    responses["agent_metadata"]["matches"] = []
                                responses["agent_metadata"]["matches"].extend(matches_data)
                            logger.info("Semantic Matchmaker found peer matches")
                        
                        self._capture_user_struggle(message, session, intent)
                
                if agent_mode == "auto" and intent != "shareable":
                    scribe_response = self.scribe.process(message, session)
                    if scribe_response:
                        responses["social_draft"] = scribe_response
                        
                        guardian_report = self.guardian.scan_content(scribe_response)
                        responses["guardian_report"] = guardian_report
                        
                        if guardian_report.blocked:
                            responses["social_draft"] = (
                                scribe_response +
                                f"\n\n⚠️ **Guardian Alert:** {guardian_report.risk_level} risk detected. "
                                f"Concerns: {', '.join(guardian_report.concerns)}"
                            )
            
            return responses
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Full traceback:\n{error_trace}")
            
            # Check if it's a Gemini API key issue
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str or "gemini" in error_str:
                logger.error("⚠️ GEMINI API KEY ISSUE DETECTED - Check Cloud Run secret configuration")
                responses["main_response"] = "I'm experiencing a configuration issue. Please check the backend logs for details."
            else:
                responses["main_response"] = f"I encountered an error: {str(e)[:200]}. Please check the backend logs."
            return responses
    
    def get_session_summary(self, session: ConversationSession) -> Dict[str, Any]:
        return {
            "session_id": session.session_id,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
            "agents_used": list(set([
                msg.agent for msg in session.messages if msg.agent
            ]))
        }
    
    def _extract_struggle_metadata(self, message: str, session: ConversationSession) -> Dict[str, Any]:
        metadata = {
            "academic_stage": None,
            "research_area": None,
            "emotional_tags": []
        }
        
        emotional_keywords = {
            "frustrated": "frustration",
            "anxious": "anxiety",
            "worried": "anxiety",
            "stressed": "stress",
            "imposter": "imposter_syndrome",
            "alone": "isolation",
            "isolated": "isolation",
            "rejected": "rejection",
            "disappointed": "disappointment",
            "overwhelmed": "overwhelm",
            "burnout": "burnout",
            "toxic": "toxic_environment",
            "failed": "failure",
            "struggling": "struggle"
        }
        
        message_lower = message.lower()
        for keyword, tag in emotional_keywords.items():
            if keyword in message_lower and tag not in metadata["emotional_tags"]:
                metadata["emotional_tags"].append(tag)
        
        stage_keywords = {
            "1st year": "1st year PhD",
            "first year": "1st year PhD",
            "2nd year": "2nd year PhD",
            "second year": "2nd year PhD",
            "3rd year": "3rd year PhD",
            "third year": "3rd year PhD",
            "4th year": "4th year PhD",
            "fourth year": "4th year PhD",
            "5th year": "5th year PhD",
            "fifth year": "5th year PhD",
            "postdoc": "Postdoc",
            "post-doc": "Postdoc",
            "post doc": "Postdoc"
        }
        
        for keyword, stage in stage_keywords.items():
            if keyword in message_lower:
                metadata["academic_stage"] = stage
                break
        
        if session.context and "research_area" in session.context:
            metadata["research_area"] = session.context.get("research_area")
        
        return metadata
    
    def _capture_user_struggle(
        self,
        message: str,
        session: ConversationSession,
        intent: Optional[str] = None
    ):
        if not settings.enable_real_user_data or not self.vector_store:
            return
        
        if intent != "emotional" and not self.matchmaker.is_emotional_struggle(message):
            return
        
        try:
            metadata = self._extract_struggle_metadata(message, session)
            
            profile_id = self.vector_store.add_peer_profile_from_session(
                struggle_text=message,
                user_id=session.user_id,
                academic_stage=metadata["academic_stage"],
                research_area=metadata["research_area"],
                emotional_tags=metadata["emotional_tags"]
            )
            
            if profile_id:
                logger.info(f"Captured user struggle: {profile_id}")
        except Exception as e:
            logger.error(f"Error capturing user struggle: {str(e)}")
