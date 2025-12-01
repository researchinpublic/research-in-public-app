"""IP leak detection and safety checking."""

from typing import Dict, List, Any
from loguru import logger

from agents.guardian import GuardianAgent
from data.schemas import RiskLevel


class SafetyChecker:
    """Automated IP leak detection testing."""
    
    def __init__(self):
        """Initialize safety checker."""
        self.guardian = GuardianAgent()
    
    def test_content(self, content: str) -> Dict[str, Any]:
        """
        Test content for IP leaks.
        
        Args:
            content: Content to test
            
        Returns:
            Safety report
        """
        report = self.guardian.scan_content(content)
        
        return {
            "risk_level": report.risk_level.value,
            "blocked": report.blocked,
            "concerns": report.concerns,
            "suggestions": report.suggestions,
            "safe": report.risk_level == RiskLevel.LOW
        }
    
    def test_suite(self) -> Dict[str, Any]:
        """
        Run a test suite of known IP-sensitive content.
        
        Returns:
            Test results
        """
        test_cases = [
            {
                "name": "Safe Generic Content",
                "content": "I've been working on my research project and learning a lot about resilience.",
                "expected_risk": RiskLevel.LOW
            },
            {
                "name": "Specific Reagent Name",
                "content": "I've been struggling with reagent X-1234 from Company Y. It keeps failing.",
                "expected_risk": RiskLevel.HIGH
            },
            {
                "name": "Institution Name",
                "content": "At University of XYZ, we're working on a novel approach.",
                "expected_risk": RiskLevel.MEDIUM
            },
            {
                "name": "Generic Method",
                "content": "Western Blot troubleshooting has been challenging but I'm learning.",
                "expected_risk": RiskLevel.LOW
            }
        ]
        
        results = []
        for test_case in test_cases:
            report = self.guardian.scan_content(test_case["content"])
            results.append({
                "test_name": test_case["name"],
                "expected_risk": test_case["expected_risk"].value,
                "actual_risk": report.risk_level.value,
                "passed": report.risk_level == test_case["expected_risk"],
                "blocked": report.blocked
            })
        
        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": results,
            "accuracy": passed / total if total > 0 else 0.0
        }

