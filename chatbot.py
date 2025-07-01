import google.generativeai as genai
from models import UserMessage, ChatSession, ConfidenceResponse
from prompts import ConfidencePromptEngine
import os
from dotenv import load_dotenv
import re

load_dotenv()


class ConfidenceChatbot:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"🔑 Loaded API key: {api_key[:4]}***" if api_key else "❌ GEMINI_API_KEY not found")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.prompt_engine = ConfidencePromptEngine()
        self.session = ChatSession()

    def generate_response(self, user_message: UserMessage) -> ConfidenceResponse:
        """Assess confidence + generate response in ONE call"""

        # Build unified prompt
        main_prompt = f"""
{self.prompt_engine.get_system_prompt()}

{self.prompt_engine.get_few_shot_examples()}

User message: "{user_message.content}"

Provide ALL of the following clearly:
1️⃣ Confidence Level (1-10): e.g. Confidence Level: 7
2️⃣ Main Response: a warm empowering answer using the CONFIDENCE framework (150-250 words)
3️⃣ 2-3 Confidence Tips: as bullet points
4️⃣ 2-3 Next Steps: as bullet points
"""

        try:
            print("🚀 Calling Gemini API...")
            response = self.model.generate_content(main_prompt)
            print("✅ Raw Gemini response:", response.text)

            text = response.text

            # Extract confidence level
            level_match = re.search(r'Confidence Level\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
            confidence_level = int(level_match.group(1)) if level_match else 5
            confidence_level = min(max(confidence_level, 1), 10)

            # Extract main response
            main_response = re.split(r'Confidence Tips|Tips|Next Steps', text, 1)[0].strip()

            # Extract tips
            tips = re.findall(r'[-•*]\s*(.+)', text)
            if len(tips) > 5:  # assume first 2-3 are tips, next 2-3 are steps
                tips_split = len(tips) // 2
                confidence_tips = tips[:tips_split]
                next_steps = tips[tips_split:]
            else:
                confidence_tips = tips[:3] if tips else ["Focus on your strengths"]
                next_steps = tips[3:6] if len(tips) > 3 else ["Take one small step"]

            # Log session
            self.session.messages.append({
                "user": user_message.content,
                "assistant": main_response,
                "confidence_level": confidence_level,
                "timestamp": user_message.timestamp.isoformat()
            })

            return ConfidenceResponse(
                response=main_response,
                confidence_tips=confidence_tips,
                next_steps=next_steps,
                motivation_score=min(confidence_level + 2, 10),
                emotional_tone="empowering"
            )

        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error: str) -> ConfidenceResponse:
        """Default fallback"""
        print(f"⚠️ Using fallback due to error: {error}")
        return ConfidenceResponse(
            response=(
                "I believe in your ability to overcome any challenge! "
                "Sometimes the strongest people face the toughest moments, "
                "but that's exactly what makes you resilient. "
                "What's one small step you can take today toward feeling more confident?"
            ),
            confidence_tips=[
                "You are stronger than you think",
                "Every expert was once a beginner",
                "Your worth isn't determined by perfection"
            ],
            next_steps=[
                "Take one small action",
                "Practice self-kindness",
                "Focus on growth, not perfection"
            ],
            motivation_score=7,
            emotional_tone="supportive"
        )

    def get_session_summary(self) -> dict:
        """Session stats"""
        if not self.session.messages:
            return {"message": "No conversation yet"}

        confidence_levels = [msg.get("confidence_level", 5) for msg in self.session.messages]
        avg_conf = sum(confidence_levels) / len(confidence_levels)

        return {
            "total_messages": len(self.session.messages),
            "average_confidence": round(avg_conf, 1),
            "confidence_trend": "improving" if confidence_levels[-1] > confidence_levels[0] else "stable",
            "session_duration": "Active session"
        }
