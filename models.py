from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import json

class UserMessage(BaseModel):
    """User message with validation"""
    content: str = Field(..., min_length=1, max_length=1000, description="User's message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class ConfidenceAssessment(BaseModel):
    """Assessment results from AI analysis"""
    confidence_level: int = Field(..., ge=1, le=10, description="Confidence level 1-10")
    emotional_state: str = Field(..., description="Current emotional state")
    main_challenge: str = Field(..., description="Primary challenge they're facing")
    hidden_strengths: str = Field(..., description="Strengths they might not see")
    best_approach: str = Field(..., description="Most effective coaching approach")
    
    @classmethod
    def from_json_string(cls, json_str: str):
        """Parse JSON response from AI"""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback if JSON parsing fails
            return cls(
                confidence_level=5,
                emotional_state="uncertain",
                main_challenge="general confidence",
                hidden_strengths="resilience and self-awareness",
                best_approach="supportive encouragement"
            )

class AIResponse(BaseModel):
    """Complete AI response with all components"""
    response: str = Field(..., description="Main conversational response")
    confidence_level: int = Field(..., ge=1, le=10)
    confidence_tips: List[str] = Field(default=[], description="Actionable confidence tips")
    next_steps: List[str] = Field(default=[], description="Specific next actions")
    assessment: Optional[ConfidenceAssessment] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def extract_tips_and_steps(self):
        """Extract tips and steps from response text if not provided separately"""
        if not self.confidence_tips:
            # Look for numbered lists or bullet points in response
            lines = self.response.split('\n')
            tips = []
            steps = []
            
            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith(('1.', '2.', '3.', '•', '-', '→')):
                    if any(word in clean_line.lower() for word in ['try', 'practice', 'do', 'start']):
                        steps.append(clean_line.lstrip('123456789.•-→ '))
                    else:
                        tips.append(clean_line.lstrip('123456789.•-→ '))
            
            self.confidence_tips = tips[:3]  # Limit to 3 tips
            self.next_steps = steps[:3]  # Limit to 3 steps

class ChatSession(BaseModel):
    """Track entire chat session data"""
    messages: List[dict] = Field(default=[])
    confidence_history: List[int] = Field(default=[])
    start_time: datetime = Field(default_factory=datetime.now)
    total_messages: int = Field(default=0)
    
    def add_message(self, role: str, content: str, confidence_level: Optional[int] = None):
        """Add a message to the session"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence_level": confidence_level
        })
        self.total_messages += 1
        
        if confidence_level and role == "assistant":
            self.confidence_history.append(confidence_level)
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence level"""
        if not self.confidence_history:
            return 5.0
        return round(sum(self.confidence_history) / len(self.confidence_history), 1)
    
    def get_confidence_trend(self) -> List[int]:
        """Get confidence levels for charting"""
        if len(self.confidence_history) < 2:
            return [5, 6]  # Default trend
        return self.confidence_history[-10:]  # Last 10 data points
    
    def get_session_summary(self) -> dict:
        """Get session analytics"""
        return {
            "total_messages": self.total_messages,
            "average_confidence": self.get_average_confidence(),
            "confidence_trend": self.get_confidence_trend(),
            "session_duration": str(datetime.now() - self.start_time).split('.')[0],
            "latest_confidence": self.confidence_history[-1] if self.confidence_history else 5
        }

class PromptData(BaseModel):
    """Structure for organizing prompt data"""
    system_prompt: str
    user_message: str
    confidence_level: int
    context: str = ""
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"