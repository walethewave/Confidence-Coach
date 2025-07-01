from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
import uuid

class UserMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ConfidenceLevel(BaseModel):
    level: int = Field(..., ge=1, le=10, description="Confidence level from 1-10")
    area: str = Field(..., description="Specific area of confidence")
    
class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[dict] = Field(default_factory=list)
    confidence_tracking: List[ConfidenceLevel] = Field(default_factory=list)
    user_goals: Optional[List[str]] = None
    session_start: datetime = Field(default_factory=datetime.now)

class ConfidenceResponse(BaseModel):
    response: str
    confidence_tips: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    motivation_score: int = Field(..., ge=1, le=10)
    emotional_tone: Literal["supportive", "encouraging", "empowering", "gentle", "energetic"]