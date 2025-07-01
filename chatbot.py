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
        self.model = genai.GenerativeModel('gemini-pro')
        self.prompt_engine = ConfidencePromptEngine()
        self.session = ChatSession()

    def generate_response(self, user_message: UserMessage) -> ConfidenceResponse:
        full_prompt = (
            self.prompt_engine.get_system_prompt()
            + "\n"
            + self.prompt_engine.get_few_shot_examples()
            + "\n"
            + self.prompt_engine.get_response_prompt(user_message.content)
        )

        print("🚀 Prompt sent to Gemini:\n", full_prompt[:500], "...")

        try:
            response = self.model.generate_content(full_prompt)
            text = response.text
            print("✅ Gemini raw response:\n", text)

            # Extract sections
            level_match = re.search(r'Confidence Level\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
            confidence_level = int(level_match.group(1)) if level_match else 5
            confidence_level = min(max(confidence_level, 1), 10)

            main_response_match = re.search(r'Main Response:\s*(.*?)(Confidence Tips:)', text, re.DOTALL | re.IGNORECASE)
            main_response = main_response_match.group(1).strip() if main_response_match else text.strip()

            tips_match = re.search(r'Confidence Tips:\s*(.*?)(Next Steps:)', text, re.DOTALL | re.IGNORECASE)
            tips_section = tips_match.group(1).strip() if tips_match else ""
            confidence_tips = re.findall(r'-\s*(.+)', tips_section)

            steps_match = re.search(r'Next Steps:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
            steps_section = steps_match.group(1).strip() if steps_match else ""
            next_steps = re.findall(r'-\s*(.+)', steps_section)

            # Log session
            self.session.messages.append({
                "user": user_message.content,
                "assistant": main_response,
                "confidence_level": confidence_level,
                "timestamp": user_message.timestamp.isoformat()
            })

            return ConfidenceResponse(
                response=main_response,
                confidence_tips=confidence_tips[:3],
                next_steps=next_steps[:3],
                motivation_score=min(confidence_level + 2, 10),
                emotional_tone="empowering"
            )

        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> ConfidenceResponse:
        return ConfidenceResponse(
            response="I believe in your ability to overcome any challenge! "
                     "Let's focus on one small step you can take today to grow your confidence.",
            confidence_tips=["You are stronger than you think", "Your journey is unique", "Progress over perfection"],
            next_steps=["Write one small win", "Speak kindly to yourself", "Celebrate daily effort"],
            motivation_score=7,
            emotional_tone="supportive"
        )

    def get_session_summary(self) -> dict:
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
