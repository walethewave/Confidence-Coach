import streamlit as st
from chatbot import ConfidenceChatbot
from models import UserMessage
import plotly.graph_objects as go
import time
from dotenv import load_dotenv
from datetime import datetime
import logging
from typing import List, Dict, Any

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 500
DEFAULT_CONFIDENCE_LEVEL = 5
CONFIDENCE_COLORS = ['#ff6b6b', '#feca57', '#48dbfb', '#0abde3']

# Page config
st.set_page_config(
    page_title="ConfidenceAI - Your Personal Confidence Coach",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_custom_css() -> str:
    """Load and return custom CSS styles"""
    return """
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .chat-message {
            padding: 1.2rem;
            border-radius: 12px;
            margin: 1rem 0;
            animation: fadeIn 0.6s ease-out;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .user-message {
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border-left: 4px solid #2196f3;
        }
        .bot-message {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 4px solid #9c27b0;
        }
        .confidence-meter {
            background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #0abde3);
            height: 25px;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        .quick-action-btn {
            width: 100%;
            margin: 0.3rem 0;
            padding: 0.5rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .error-message {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(20px);}
            to {opacity: 1; transform: translateY(0);}
        }
        @keyframes pulse {
            0% {transform: scale(1);}
            50% {transform: scale(1.05);}
            100% {transform: scale(1);}
        }
        .pulse-animation {
            animation: pulse 0.5s ease-in-out;
        }
    </style>
    """

def initialize_session_state():
    """Initialize all session state variables"""
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = ConfidenceChatbot()
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            st.error("Failed to initialize ConfidenceAI. Please refresh the page.")
            return False
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'confidence_history' not in st.session_state:
        st.session_state.confidence_history = []
    
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = datetime.now()
    
    if 'daily_goals' not in st.session_state:
        st.session_state.daily_goals = []
    
    return True

def validate_user_input(text: str) -> tuple[bool, str]:
    """Validate user input"""
    if not text or not text.strip():
        return False, "Please enter a message"
    
    if len(text) > MAX_MESSAGE_LENGTH:
        return False, f"Message too long. Please keep it under {MAX_MESSAGE_LENGTH} characters."
    
    # Basic content filtering
    inappropriate_words = ['spam', 'test123', 'asdf']  # Add more as needed
    if any(word in text.lower() for word in inappropriate_words):
        return False, "Please enter a meaningful message"
    
    return True, ""

def create_confidence_chart(confidence_data: List[float]) -> go.Figure:
    """Create an enhanced confidence progress chart"""
    if not confidence_data:
        confidence_data = [DEFAULT_CONFIDENCE_LEVEL]
    
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=list(range(1, len(confidence_data) + 1)),
        y=confidence_data,
        mode='lines+markers',
        line=dict(color='#667eea', width=4, shape='spline'),
        marker=dict(size=10, color='#764ba2', line=dict(width=2, color='white')),
        name='Confidence Level',
        hovertemplate='Session %{x}<br>Confidence: %{y}/10<extra></extra>'
    ))
    
    # Add trend line if enough data points
    if len(confidence_data) > 2:
        from numpy import polyfit, poly1d
        try:
            x_vals = list(range(1, len(confidence_data) + 1))
            z = polyfit(x_vals, confidence_data, 1)
            p = poly1d(z)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=[p(x) for x in x_vals],
                mode='lines',
                line=dict(color='rgba(255, 107, 107, 0.5)', width=2, dash='dash'),
                name='Trend',
                hoverinfo='skip'
            ))
        except:
            pass  # Skip trend line if numpy not available
    
    fig.update_layout(
        title=dict(text="Your Confidence Journey", font=dict(size=16, color='#333')),
        xaxis_title="Session Number",
        yaxis_title="Confidence Level (1-10)",
        height=250,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 10], gridcolor='rgba(200,200,200,0.3)'),
        xaxis=dict(gridcolor='rgba(200,200,200,0.3)'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

def render_sidebar():
    """Render the enhanced sidebar"""
    with st.sidebar:
        st.markdown("### 🎯 Your Confidence Dashboard")
        
        try:
            session_data = st.session_state.chatbot.get_session_summary()
            
            # Session metrics with enhanced styling
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Messages", 
                    session_data.get("total_messages", len(st.session_state.messages)),
                    delta=None if len(st.session_state.messages) == 0 else "+1"
                )
            with col2:
                avg_confidence = session_data.get("average_confidence", DEFAULT_CONFIDENCE_LEVEL)
                st.metric(
                    "Avg Confidence", 
                    f"{avg_confidence:.1f}/10",
                    delta=f"+{avg_confidence - DEFAULT_CONFIDENCE_LEVEL:.1f}" if avg_confidence > DEFAULT_CONFIDENCE_LEVEL else None
                )
            
            # Session duration
            if 'session_start_time' in st.session_state:
                duration = datetime.now() - st.session_state.session_start_time
                minutes = int(duration.total_seconds() / 60)
                st.metric("Session Time", f"{minutes} min")
            
            # Enhanced confidence chart
            if st.session_state.confidence_history:
                fig = create_confidence_chart(st.session_state.confidence_history)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Start chatting to see your confidence progress!")
        
        except Exception as e:
            logger.error(f"Error rendering session data: {e}")
            st.warning("Unable to load session analytics")
        
        st.markdown("---")
        
        # Enhanced quick actions
        st.markdown("### ⚡ Instant Confidence Boosters")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💪 Affirmation", key="affirmation", help="Get a daily affirmation"):
                affirmations = [
                    "You are capable of amazing things!",
                    "Every challenge is an opportunity to grow!",
                    "Your potential is limitless!",
                    "You have everything you need to succeed!",
                    "Progress, not perfection, is the goal!"
                ]
                import random
                st.success(random.choice(affirmations))
                st.balloons()
        
        with col2:
            if st.button("🎯 Set Goal", key="goal", help="Set a daily goal"):
                goal_input = st.text_input("What's your goal for today?", key="daily_goal_input")
                if goal_input:
                    st.session_state.daily_goals.append({
                        'goal': goal_input,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'completed': False
                    })
                    st.success("Goal added! You've got this! 🌟")
        
        # Display active goals
        if st.session_state.daily_goals:
            st.markdown("### 📋 Today's Goals")
            for i, goal in enumerate(st.session_state.daily_goals[-3:]):  # Show last 3 goals
                if st.checkbox(goal['goal'], key=f"goal_{i}"):
                    st.success("🎉 Goal completed!")
        
        st.markdown("---")
        
        # Enhanced project info
        with st.expander("🚀 About ConfidenceAI"):
            st.markdown("""
            **Advanced Features:**
            - 🧠 AI-Powered Coaching
            - 📊 Real-time Progress Tracking  
            - 🎯 Personalized Goal Setting
            - 💡 Dynamic Confidence Tips
            - 🔒 Privacy-First Design
            
            **Tech Stack:**
            - Streamlit + Python
            - Advanced Prompt Engineering
            - Pydantic Validation
            - Plotly Visualizations
            
            [⭐ Star on GitHub](https://github.com/walethewave/Confidence-Coach)
            """)

def render_chat_message(message: Dict[str, Any], message_index: int):
    """Render individual chat message with enhanced styling"""
    try:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🙋‍♀️ You:</strong> {message["content"]}
                <div style="font-size: 0.8em; color: #666; margin-top: 0.5rem;">
                    {datetime.now().strftime("%H:%M")}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 ConfidenceAI:</strong> {message["content"]}
                <div style="font-size: 0.8em; color: #666; margin-top: 0.5rem;">
                    {datetime.now().strftime("%H:%M")}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced expandable sections
            col1, col2 = st.columns(2)
            with col1:
                if "tips" in message and message["tips"]:
                    with st.expander("💡 Confidence Tips", expanded=False):
                        for i, tip in enumerate(message["tips"], 1):
                            st.markdown(f"**{i}.** {tip}")
            
            with col2:
                if "next_steps" in message and message["next_steps"]:
                    with st.expander("🎯 Next Steps", expanded=False):
                        for i, step in enumerate(message["next_steps"], 1):
                            st.markdown(f"**{i}.** {step}")
    
    except Exception as e:
        logger.error(f"Error rendering message {message_index}: {e}")
        st.error("Error displaying message")

def process_user_input(user_input: str) -> bool:
    """Process user input and generate response"""
    try:
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Generate response with error handling
        user_message = UserMessage(content=user_input)
        
        with st.spinner("🤖 ConfidenceAI is crafting your personalized response..."):
            response = st.session_state.chatbot.generate_response(user_message)
            
            # Extract confidence level if available
            confidence_level = getattr(response, 'confidence_level', DEFAULT_CONFIDENCE_LEVEL)
            st.session_state.confidence_history.append(confidence_level)
            
            # Add bot response
            bot_message = {
                "role": "assistant",
                "content": response.response,
                "tips": getattr(response, 'confidence_tips', []),
                "next_steps": getattr(response, 'next_steps', []),
                "confidence_level": confidence_level,
                "timestamp": datetime.now()
            }
            st.session_state.messages.append(bot_message)
            
            return True
            
    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        st.error("Sorry, I encountered an error processing your message. Please try again.")
        return False

def main():
    """Main application function"""
    # Load custom CSS
    st.markdown(load_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    if not initialize_session_state():
        return
    
    # Header with enhanced styling
    st.markdown("""
    <div class="main-header">
        <h1>🌟 ConfidenceAI - Your Personal Confidence Coach</h1>
        <p>Empowering you to unlock your full potential through advanced AI coaching</p>
        <div style="margin-top: 1rem;">
            <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; margin: 0 0.2rem;">
                🧠 AI-Powered
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; margin: 0 0.2rem;">
                📊 Progress Tracking
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; margin: 0 0.2rem;">
                🎯 Personalized
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Main chat interface
    st.markdown("### 💬 Chat with ConfidenceAI")
    st.markdown("*Share your thoughts, challenges, or goals. I'm here to help build your confidence!*")
    
    # Chat container with max height
    chat_container = st.container()
    with chat_container:
        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            render_chat_message(message, i)
    
    # Chat input with validation
    user_input = st.chat_input(
        "Share what's on your mind... I'm here to help build your confidence! 🌟",
        max_chars=MAX_MESSAGE_LENGTH
    )
    
    if user_input:
        # Validate input
        is_valid, error_message = validate_user_input(user_input)
        if not is_valid:
            st.error(error_message)
            return
        
        # Process input
        if process_user_input(user_input):
            st.rerun()
    
    # Footer with additional info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔒 Privacy First**")
        st.caption("Your conversations are secure and private")
    
    with col2:
        st.markdown("**⚡ Real-time Coaching**")
        st.caption("Instant personalized guidance")
    
    with col3:
        st.markdown("**📈 Track Progress**")
        st.caption("Visualize your confidence journey")
    
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>Built with ❤️ using Streamlit, Advanced AI & Modern Web Technologies</p>
        <p><em>Your confidence journey starts with a single conversation</em> 🌟</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()