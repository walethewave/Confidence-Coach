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
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        self.prompt_engine = ConfidencePromptEngine()
        self.session = ChatSession()

    def generate_response(self, user_message: UserMessage) -> ConfidenceResponse:
        prompt = (
            self.prompt_engine.get_system_prompt() +
            self.prompt_engine.get_few_shot_examples() +
            self.prompt_engine.get_main_prompt(user_message.content)
        )
    def generate_response(self, user_message: UserMessage) -> ConfidenceResponse:
        """Generate a confidence-building response using the CONFIDENCE framework"""

        # 1️⃣ --- Estimate or default confidence level ---
        # (You can replace this later with an actual analysis step if you want)
        confidence_level = 5  # Basic default

        # 2️⃣ --- Build the full master prompt properly ---
        main_prompt = (
            self.prompt_engine.get_system_prompt()
            + "\n"
            + self.prompt_engine.get_few_shot_examples()
            + "\n"
            + self.prompt_engine.get_response_prompt(
                user_message.content,
                confidence_level
            )
        )

        try:
            print("🚀 Calling Gemini API...")
            response = self.model.generate_content(main_prompt)
            print("✅ Raw Gemini response:", response.text)

            text = response.text

            # Extract confidence level if possible
            import re
            level_match = re.search(r'Confidence Level\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
            if level_match:
                confidence_level = int(level_match.group(1))
                confidence_level = min(max(confidence_level, 1), 10)

            # Basic split: tips and steps come from bullet points
            tips = re.findall(r'[-•*]\s*(.+)', text)
            if len(tips) > 5:
                split = len(tips) // 2
                confidence_tips = tips[:split]
                next_steps = tips[split:]
            else:
                confidence_tips = tips[:3] if tips else ["Keep believing in yourself."]
                next_steps = tips[3:6] if len(tips) > 3 else ["Take one small action today."]

            # Main response (remove tips/steps from text)
            main_response = re.split(r'(Confidence Tips|Tips|Next Steps)', text, 1)[0].strip()

            # Save to session
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
        print(f"⚠️ Fallback: {error}")
        return ConfidenceResponse(
            response="I believe in you! Let’s find one small step to build your confidence today.",
            confidence_tips=[
                "You are stronger than you think",
                "Take one small action",
                "Celebrate small wins"
            ],
            next_steps=[
                "Write down 1 thing you did well today",
                "Practice self-compassion",
                "Share your progress with a friend"
            ],
            motivation_score=7,
            emotional_tone="supportive"
        )

    def get_session_summary(self) -> dict:
        if not self.session.messages:
            return {"message": "No conversation yet"}

        levels = [msg.get("confidence_level", 5) for msg in self.session.messages]
        avg = sum(levels) / len(levels)

        return {
            "total_messages": len(self.session.messages),
            "average_confidence": round(avg, 1),
            "confidence_trend": "improving" if levels[-1] > levels[0] else "stable",
            "session_duration": "Active session"
        }
