import google.generativeai as genai
import os
import json
import logging
from typing import Optional
from models import UserMessage, AIResponse, ConfidenceAssessment, ChatSession, PromptData
from prompts import ConfidencePromptEngine
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceChatbot:
    """
    Main chatbot class that handles confidence coaching conversations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chatbot with Gemini AI"""
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize session tracking
        self.session = ChatSession()
        self.prompt_engine = ConfidencePromptEngine()
        
        logger.info("ConfidenceChatbot initialized successfully")
    
    def _make_ai_request(self, prompt: str, max_retries: int = 3) -> str:
        """Make request to Gemini AI with error handling"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"AI request attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return self._get_fallback_response()
        
        return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Fallback response when AI fails"""
        return """I hear you, and I want you to know that reaching out takes courage. 🌟 

While I'm having a technical moment, here's what I want you to remember: every challenge you're facing right now is temporary, but your strength is permanent.

Take a deep breath. You've overcome difficulties before, and you have everything within you to handle whatever comes next.

What's one small thing you can do today to take care of yourself, make sure you do it till I'm back online?"""

    def _assess_confidence(self, user_message: str) -> ConfidenceAssessment:
        """Analyze user message for confidence indicators"""
        assessment_prompt = self.prompt_engine.get_confidence_assessment_prompt(user_message)
        
        try:
            response = self._make_ai_request(assessment_prompt)
            
            # Try to parse JSON response
            if response.strip().startswith('{'):
                return ConfidenceAssessment.from_json_string(response)
            else:
                # If not JSON, extract confidence level from text
                confidence_level = self._extract_confidence_from_text(response)
                return ConfidenceAssessment(
                    confidence_level=confidence_level,
                    emotional_state="processing",
                    main_challenge="general confidence",
                    hidden_strengths="self-awareness and courage to reach out",
                    best_approach="supportive encouragement"
                )
                
        except Exception as e:
            logger.error(f"Assessment failed: {str(e)}")
            return ConfidenceAssessment(
                confidence_level=5,
                emotional_state="uncertain",
                main_challenge="unknown",
                hidden_strengths="resilience",
                best_approach="gentle support"
            )
    
    def _extract_confidence_from_text(self, text: str) -> int:
        """Extract confidence level from text response"""
        # Look for numbers 1-10 in the text
        import re
        numbers = re.findall(r'\b([1-9]|10)\b', text)
        
        if numbers:
            return int(numbers[0])
        
        # Fallback based on keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ['very low', 'terrible', 'awful', 'hopeless']):
            return 2
        elif any(word in text_lower for word in ['low', 'down', 'struggling', 'difficult']):
            return 4
        elif any(word in text_lower for word in ['okay', 'fine', 'average', 'neutral']):
            return 5
        elif any(word in text_lower for word in ['good', 'positive', 'better', 'confident']):
            return 7
        elif any(word in text_lower for word in ['great', 'excellent', 'amazing', 'fantastic']):
            return 9
        
        return 5  
    
    def generate_response(self, user_message: UserMessage) -> AIResponse:
        """Generate a complete confidence coaching response"""
        try:
            
            assessment = self._assess_confidence(user_message.content)
            
            context = self._build_context()
            response_prompt = self.prompt_engine.get_response_prompt(
                user_message.content, 
                assessment.confidence_level, 
                context
            )
            
            # i added system prompt for consistency
            full_prompt = f"""
            {self.prompt_engine.get_system_prompt()}
            
            {response_prompt}
            """
            
            ai_response_text = self._make_ai_request(full_prompt)
            
             # structured response
            ai_response = AIResponse(
                response=ai_response_text,
                confidence_level=assessment.confidence_level,
                assessment=assessment
            )
            
            # Extract tips and steps from response
            ai_response.extract_tips_and_steps()
            
            # Update session tracking
            self.session.add_message("user", user_message.content)
            self.session.add_message("assistant", ai_response.response, assessment.confidence_level)
            
            logger.info(f"Generated response for confidence level: {assessment.confidence_level}")
            return ai_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            
            # Return fallback response
            fallback_response = AIResponse(
                response=self._get_fallback_response(),
                confidence_level=5,
                confidence_tips=[
                    "Take one small step forward today",
                    "Remember that setbacks are temporary",
                    "You're stronger than you think"
                ],
                next_steps=[
                    "Practice deep breathing for 2 minutes",
                    "Write down one thing you're grateful for",
                    "Reach out to someone who supports you"
                ]
            )
            
            self.session.add_message("user", user_message.content)
            self.session.add_message("assistant", fallback_response.response, 5)
            
            return fallback_response
    
    def _build_context(self) -> str:
        """Build context from recent conversation history"""
        if len(self.session.messages) < 2:
            return "This is the beginning of our conversation."
        
        # Get last few messages for context
        recent_messages = self.session.messages[-4:]  # Last 4 messages
        context_parts = []
        
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "You"
            context_parts.append(f"{role}: {msg['content'][:100]}...")
        
        return "Recent conversation context:\n" + "\n".join(context_parts)
    
    def get_session_summary(self) -> dict:
        """Get current session analytics"""
        return self.session.get_session_summary()
    
    def reset_session(self):
        """Reset the chat session"""
        self.session = ChatSession()
        logger.info("Session reset")
    
    def get_confidence_history(self) -> list:
        """Get confidence level history for charting"""
        return self.session.get_confidence_trend()
    
    def export_session(self) -> dict:
        """Export session data for analysis"""
        return {
            "session_summary": self.get_session_summary(),
            "full_conversation": self.session.messages,
            "confidence_progression": self.session.confidence_history
        }

# Helper function for testing
def create_test_chatbot() -> ConfidenceChatbot:
    """Create a chatbot instance for testing"""
    return ConfidenceChatbot()

if __name__ == "__main__":
    # Quick test
    try:
        bot = create_test_chatbot()
        test_message = UserMessage(content="I'm feeling nervous about my presentation tomorrow")
        response = bot.generate_response(test_message)
        print("Response:", response.response)
        print("Confidence Level:", response.confidence_level)
        print("Tips:", response.confidence_tips)
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure to set your GEMINI_API_KEY environment variable")