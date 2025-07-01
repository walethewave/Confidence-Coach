import streamlit as st
from chatbot import ConfidenceChatbot
from models import UserMessage
import plotly.graph_objects as go
import time

# Page config
st.set_page_config(
    page_title="ConfidenceAI - Your Personal Confidence Coach",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        animation: fadeIn 0.5s;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .confidence-meter {
        background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #0abde3);
        height: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(20px);}
        to {opacity: 1; transform: translateY(0);}
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = ConfidenceChatbot()
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Header
st.markdown("""
<div class="main-header">
    <h1>🌟 ConfidenceAI - Your Personal Confidence Coach</h1>
    <p>Empowering you to unlock your full potential through advanced AI coaching</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎯 Your Confidence Journey")
    
    # Session analytics
    session_data = st.session_state.chatbot.get_session_summary()
    
    if "total_messages" in session_data:
        st.metric("Messages Exchanged", session_data["total_messages"])
        st.metric("Average Confidence", f"{session_data['average_confidence']}/10")
        
        # Confidence trend chart
        if len(st.session_state.messages) > 0:
            confidence_data = [5, 6, 7, 8]  # Sample data - replace with actual tracking
            fig = go.Figure(data=go.Scatter(
                x=list(range(1, len(confidence_data) + 1)),
                y=confidence_data,
                mode='lines+markers',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Confidence Progress",
                xaxis_title="Sessions",
                yaxis_title="Confidence Level",
                height=200,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Quick confidence boosters
    st.subheader("⚡ Quick Confidence Boosters")
    if st.button("💪 Daily Affirmation"):
        st.success("You are capable of amazing things!")
    if st.button("🎯 Set Today's Goal"):
        st.info("What's one small win you can achieve today?")
    if st.button("🌟 Celebrate Progress"):
        st.balloons()
        st.success("Every step forward counts!")
    
    st.markdown("---")
    
    # GitHub link
    st.markdown("""
    ### 🚀 Built with Advanced AI
    
    **Features:**
    - Advanced Prompt Engineering
    - Pydantic Data Validation  
    - Real-time Confidence Tracking
    - Personalized Coaching
    
    [⭐ Star on GitHub](https://github.com/your-username/confidence-builder-chatbot)
    """)

# Main chat interface
st.subheader("💬 Chat with ConfidenceAI")

# Display chat messages
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>ConfidenceAI:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Show confidence tips if available
            if "tips" in message:
                with st.expander("💡 Confidence Tips"):
                    for tip in message["tips"]:
                        st.write(f"• {tip}")
            
            # Show next steps if available  
            if "next_steps" in message:
                with st.expander("🎯 Next Steps"):
                    for step in message["next_steps"]:
                        st.write(f"→ {step}")

# Chat input
user_input = st.chat_input("Share what's on your mind... I'm here to help build your confidence! 🌟")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Show user message immediately
    with st.container():
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {user_input}
        </div>
        """, unsafe_allow_html=True)
    
    # Generate response
    with st.spinner("ConfidenceAI is crafting a personalized response..."):
        user_message = UserMessage(content=user_input)
        response = st.session_state.chatbot.generate_response(user_message)
        
        # Add bot response
        bot_message = {
            "role": "assistant", 
            "content": response.response,
            "tips": response.confidence_tips,
            "next_steps": response.next_steps
        }
        st.session_state.messages.append(bot_message)
        
        # Display response with animation
        time.sleep(0.5)  # Small delay for effect
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Built with ❤️ using Streamlit, Gemini AI & Advanced Prompt Engineering</p>
    <p>Your confidence journey starts with a single conversation 🌟</p>
</div>
""", unsafe_allow_html=True)