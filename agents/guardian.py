"""Guardian Agent - IP safety and compliance."""

from typing import Dict, Any, Optional
from loguru import logger

from agents.base_agent import BaseAgent
from config.prompts import GUARDIAN_SYSTEM_PROMPT
from data.schemas import ConversationSession, GuardianReport, RiskLevel
from services.gemini_service import gemini_service


class GuardianAgent(BaseAgent):
    """Agent 4: The Guardian - IP Safety Layer."""
    
    def __init__(self):
        """Initialize Guardian agent."""
        super().__init__(
            name="The Guardian",
            system_prompt=GUARDIAN_SYSTEM_PROMPT
        )
    
    def scan_content(self, content: str) -> GuardianReport:
        """
        Scan content for IP risks.
        
        Args:
            content: Content to scan
            
        Returns:
            Guardian report with risk assessment
        """
        try:
            prompt = f"""Analyze this content for IP safety risks:

{content}

Scan for:
1. Novel chemical structures or specific reagent names
2. Unpublished genomic sequences
3. Specific PI names or institution identifiers
4. Unpublished data or results
5. Proprietary information

Provide risk assessment in JSON format:
{{
    "risk_level": "LOW|MEDIUM|HIGH",
    "concerns": ["list of specific issues with details"],
    "blocked": true/false,
    "suggestions": ["suggested sanitizations"],
    "detected_items": {{
        "pi_names": ["list of detected PI names"],
        "reagent_names": ["list of detected reagent names"],
        "institutions": ["list of detected institution names"],
        "sequences": ["list of detected sequences"]
    }}
}}"""

            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="pro",
                system_instruction=GUARDIAN_SYSTEM_PROMPT,
                temperature=0.3  # Lower temperature for more consistent classification
            )
            
            # Parse response (simple extraction)
            risk_level = RiskLevel.LOW
            concerns = []
            blocked = False
            suggestions = []
            detected_items = {
                "pi_names": [],
                "reagent_names": [],
                "institutions": [],
                "sequences": []
            }
            
            # Try to parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*"risk_level"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    if "risk_level" in parsed:
                        risk_str = str(parsed["risk_level"]).upper()
                        if "HIGH" in risk_str:
                            risk_level = RiskLevel.HIGH
                            blocked = True
                        elif "MEDIUM" in risk_str:
                            risk_level = RiskLevel.MEDIUM
                    
                    if "concerns" in parsed and isinstance(parsed["concerns"], list):
                        concerns = parsed["concerns"]
                    
                    if "suggestions" in parsed and isinstance(parsed["suggestions"], list):
                        suggestions = parsed["suggestions"]
                    
                    if "detected_items" in parsed and isinstance(parsed["detected_items"], dict):
                        detected_items = parsed["detected_items"]
                except:
                    pass
            
            # Fallback: simple text parsing
            if not concerns:
                if "HIGH" in response.upper():
                    risk_level = RiskLevel.HIGH
                    blocked = True
                elif "MEDIUM" in response.upper():
                    risk_level = RiskLevel.MEDIUM
                
                # Extract specific detections from text
                content_lower = content.lower()
                
                # Check for PI names (common patterns: "Professor X", "Dr. X", "PI X")
                pi_patterns = re.findall(r'(?:professor|dr\.|pi)\s+([A-Z][a-z]+)', content, re.IGNORECASE)
                if pi_patterns:
                    detected_items["pi_names"] = list(set(pi_patterns))
                    concerns.append(f"Detected PI name(s): {', '.join(set(pi_patterns))}")
                
                # Check for reagent names (common patterns: "X-1234", "reagent X", "antibody X")
                reagent_patterns = re.findall(r'(?:reagent|antibody|compound)\s+([A-Z0-9-]+)', content, re.IGNORECASE)
                if reagent_patterns:
                    detected_items["reagent_names"] = list(set(reagent_patterns))
                    concerns.append(f"Detected reagent name(s): {', '.join(set(reagent_patterns))}")
                
                # Check for institutions (common patterns: "University X", "Lab X")
                inst_patterns = re.findall(r'(?:university|lab|institute)\s+([A-Z][a-z]+)', content, re.IGNORECASE)
                if inst_patterns:
                    detected_items["institutions"] = list(set(inst_patterns))
                    concerns.append(f"Detected institution name(s): {', '.join(set(inst_patterns))}")
                
                if not concerns and ("concern" in response.lower() or "issue" in response.lower()):
                    concerns.append("Potential IP-sensitive content detected")
            
            if blocked and not suggestions:
                suggestions.append("Remove specific reagent names, sequences, or institution identifiers")
            
            # Store detected items in concerns for frontend display
            report = GuardianReport(
                risk_level=risk_level,
                concerns=concerns if concerns else [],
                blocked=blocked,
                suggestions=suggestions
            )
            
            # Add detected items as metadata (we'll need to extend the schema)
            # For now, include in concerns
            if detected_items.get("pi_names"):
                report.concerns = [c for c in report.concerns if not c.startswith("Detected PI name")]
                report.concerns.insert(0, f"Detected PI name(s): {', '.join(detected_items['pi_names'])}")
            if detected_items.get("reagent_names"):
                report.concerns = [c for c in report.concerns if not c.startswith("Detected reagent name")]
                report.concerns.insert(0, f"Detected reagent name(s): {', '.join(detected_items['reagent_names'])}")
            if detected_items.get("institutions"):
                report.concerns = [c for c in report.concerns if not c.startswith("Detected institution name")]
                report.concerns.insert(0, f"Detected institution name(s): {', '.join(detected_items['institutions'])}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error in Guardian scan: {str(e)}")
            # Default to blocking on error (safer)
            return GuardianReport(
                risk_level=RiskLevel.MEDIUM,
                concerns=["Error during scan"],
                blocked=False,
                suggestions=["Please review content manually"]
            )
    
    def process(
        self,
        content: str,
        session: Optional[ConversationSession] = None,
        **kwargs
    ) -> GuardianReport:
        """
        Process content through Guardian scan.
        
        Args:
            content: Content to scan
            session: Optional conversation session
            **kwargs: Additional parameters
            
        Returns:
            Guardian report
        """
        return self.scan_content(content)

