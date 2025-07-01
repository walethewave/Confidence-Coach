import google.generativeai as genai
from models import UserMessage, ChatSession, ConfidenceResponse
from prompts import ConfidencePromptEngine
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

class ConfidenceChatbot:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        self.prompt_engine = ConfidencePromptEngine()
        self.session = ChatSession()
    
    def assess_confidence_level(self, message: str) -> int:
        """Assess user's confidence level from their message"""
        assessment_prompt = self.prompt_engine.get_confidence_assessment_prompt(message)
        
        try:
            response = self.model.generate_content(assessment_prompt)
            # Extract confidence level using regex
            confidence_match = re.search(r'confidence level.*?(\d+)', response.text.lower())
            if confidence_match:
                return min(max(int(confidence_match.group(1)), 1), 10)
            return 5  # Default middle confidence
        except:
            return 5
    
    def generate_response(self, user_message: UserMessage) -> ConfidenceResponse:
        """Generate confidence-building response"""
        
        # Assess confidence level
        confidence_level = self.assess_confidence_level(user_message.content)
        
        # Get conversation context
        context = self._get_context()
        
        # Create main prompt
        main_prompt = f"""
        {self.prompt_engine.get_system_prompt()}
        
        {self.prompt_engine.get_few_shot_examples()}
        
        {self.prompt_engine.get_response_prompt(user_message.content, confidence_level, context)}
        """
        
        try:
            response = self.model.generate_content(main_prompt)
            
            # Extract structured information
            tips = self._extract_tips(response.text)
            next_steps = self._extract_next_steps(response.text)
            
            # Store in session
            self.session.messages.append({
                "user": user_message.content,
                "assistant": response.text,
                "confidence_level": confidence_level,
                "timestamp": user_message.timestamp.isoformat()
            })
            
            return ConfidenceResponse(
                response=response.text,
                confidence_tips=tips,
                next_steps=next_steps,
                motivation_score=min(confidence_level + 2, 10),
                emotional_tone="empowering"
            )
            
        except Exception as e:
            return self._fallback_response(str(e))
    
    def _get_context(self) -> str:
        """Get conversation context from recent messages"""
        if len(self.session.messages) == 0:
            return "This is the start of our conversation."
        
        recent_messages = self.session.messages[-3:]  # Last 3 exchanges
        context = "Previous conversation:\n"
        for msg in recent_messages:
            context += f"User: {msg['user']}\nAssistant: {msg['assistant'][:100]}...\n"
        return context
    
    def _extract_tips(self, response: str) -> list:
        """Extract tips from response"""
        # Look for numbered lists or bullet points
        tips = re.findall(r'(?:\d+\.|•)\s*([^.\n]+)', response)
        return tips[:3] if tips else ["Focus on your strengths", "Take small steps", "Celebrate progress"]
    
    def _extract_next_steps(self, response: str) -> list:
        """Extract actionable next steps"""
        steps = re.findall(r'(?:step|action|do|try).*?:?\s*([^.\n]+)', response.lower())
        return steps[:3] if steps else ["Set one small goal", "Practice self-compassion", "Take action today"]
    
    def _fallback_response(self, error: str) -> ConfidenceResponse:
        """Provide fallback response if API fails"""
        return ConfidenceResponse(
            response="I believe in your ability to overcome any challenge! Sometimes the strongest people face the toughest moments, but that's exactly what makes you resilient. What's one small step you can take today toward feeling more confident?",
            confidence_tips=["You are stronger than you think", "Every expert was once a beginner", "Your worth isn't determined by perfection"],
            next_steps=["Take one small action", "Practice self-kindness", "Focus on growth, not perfection"],
            motivation_score=7,
            emotional_tone="supportive"
        )

    def get_session_summary(self) -> dict:
        """Get session analytics"""
        if not self.session.messages:
            return {"message": "No conversation yet"}
        
        confidence_levels = [msg.get("confidence_level", 5) for msg in self.session.messages]
        avg_confidence = sum(confidence_levels) / len(confidence_levels)
        
        return {
            "total_messages": len(self.session.messages),
            "average_confidence": round(avg_confidence, 1),
            "confidence_trend": "improving" if confidence_levels[-1] > confidence_levels[0] else "stable",
            "session_duration": "Active session"
        }