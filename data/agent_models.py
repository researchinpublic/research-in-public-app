from pydantic import BaseModel, Field
from typing import Optional, List

class EmotionalAnalysis(BaseModel):
    """Analysis of user's emotional state."""
    emotional_spectrum: str = Field(
        description="The primary emotion detected, e.g., 'Happy', 'Joyful', 'Exhaustion', 'Anxiety', 'Frustration', 'Overwhelm', 'Stagnation'."
    )
    emotional_intensity: int = Field(
        description="Intensity of the emotion on a scale of 1-10 (1=mild, 10=extreme)."
    )
    grounding_technique: str = Field(
        description="A specific grounding technique suggested for this state, e.g., 'Box Breathing', 'Sensory Awareness'."
    )

class VentResponse(BaseModel):
    """Structured response from the Vent Validator agent."""
    analysis: EmotionalAnalysis
    response_text: str = Field(
        description="The empathetic, warm response to the user, in the voice of Mr. Rogers. Succinct (2-3 sentences)."
    )

class ClarityAnalysis(BaseModel):
    """Analysis of research clarity and logic."""
    clarity_score: int = Field(description="Clarity score 0-100.")
    logic_score: int = Field(description="Logic/coherence score 0-100.")
    critique_focus: str = Field(description="Primary focus of critique, e.g. 'Methodology', 'Significance'.")

class PIResponse(BaseModel):
    """Structured response from the PI Simulator agent."""
    analysis: ClarityAnalysis
    response_text: str = Field(
        description="The inspiring, supportive mentor response in the voice of Carl Sagan."
    )

