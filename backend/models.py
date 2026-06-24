from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
import uuid

@dataclass
class ConversationState:
    """Manages the memory, context, and escalation metrics."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    history: List[Dict[str, str]] = field(default_factory=list)
    detected_language: str = "en"
    
    # State Tracking Upgrades
    saved_order_id: Optional[str] = None
    waiting_for_order_id: bool = False
    
    # Escalation Upgrades
    frustration_count: int = 0
    is_escalated: bool = False
    human_turn_counter: int = 0

class NLUAnalysis(BaseModel):
    """Structured Output Schema (Upgraded with Scoring and Confidence)."""
    intent: Literal["track_order", "return_policy", "product_faq", "human_handoff", "general_chat"]
    sentiment: Literal["positive", "neutral", "angry"]
    satisfaction_score: int = Field(description="1 for angry, 3 for neutral, 5 for positive.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    order_id: Optional[str] = Field(None, description="Extracted order ID (e.g., ORD1001).")

def calculate_satisfaction_score(sentiment: str) -> int:
    """Helper for mock fallback scoring."""
    mapping = {"positive": 5, "neutral": 3, "angry": 1}
    return mapping.get(sentiment, 3)