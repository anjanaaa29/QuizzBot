import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

# Load Groq API key
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if groq_api_key:
    client = Groq(api_key=groq_api_key)
else:
    st.error("GROQ_API_KEY not found. Please set it in your environment variables.")
    st.stop()

st.set_page_config(page_title="QuizBot", page_icon=":robot_face:")
st.title("QuizBot")

# Custom CSS for chatbot interface
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
        padding: 1rem;
    }
    
    # /* Header styling */
    # .header {
    #     background-color: #456882
    #     padding: 1rem;
    #     border-radius: 0.5rem;
    #     box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    #     margin-bottom: 1rem;
    #     text-align: center;
    #     font-weight: bold;
    #     font-size: 1.2rem;
    # }
    
    /* Chat container */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 6rem;
        padding: 1rem;
    }
    
    /* Message styling */
    .message {
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        max-width: 70%;
        word-wrap: break-word;
        line-height: 1.4;
    }
    
    /* Bot message styling */
    .bot-message {
        background-color: #234C6A;
        align-self: flex-start;
        border-bottom-left-radius: 0.25rem;
        margin-right: auto;
    }
    
    /* User message styling */
    .user-message {
        background-color: #456882;
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 0.25rem;
        margin-left: auto;
    }
    
    /* Sender label styling */
    .sender {
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.3rem;
        color: #6c757d;
    }
    
    /* Input area styling */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #234C6A;
        z-index: 999;
        padding: 1rem;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Button container styling */
    .button-container {
        display: flex;
        gap: 0.5rem;
        justify-content: center;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Hide the input when not needed */
    .hidden-input {
        display: none;
    }
    
    /* Custom button styling */
    .stButton > button {
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "topic" not in st.session_state:
    st.session_state.topic = None
if "difficulty" not in st.session_state:
    st.session_state.difficulty = None
if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = set()
if "bot_welcome_sent" not in st.session_state:
    st.session_state.bot_welcome_sent = False
if "ask_more" not in st.session_state:
    st.session_state.ask_more = False
if "quiz_ended" not in st.session_state:
    st.session_state.quiz_ended = False

# --- Welcome message ---
if not st.session_state.bot_welcome_sent:
    welcome_msg = "Hi! I'm QuizBot. I can help you create quizzes on any topic. Please enter the topic you want to quiz on."
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    st.session_state.bot_welcome_sent = True

# --- Display header ---
# st.markdown('<div class="header">QuizBot</div>', unsafe_allow_html=True)

# --- Display chat messages with custom styling ---
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown('<div class="sender">QuizBot</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="message bot-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="sender" style="text-align: right;">You</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Function to generate questions ---
def generate_questions(topic, difficulty, existing_questions, count=3):
    try:
        prompt_text = f"""
        Generate {count} {difficulty} level questions on the topic {topic}.
        {f"Do not repeat these previous questions: {list(existing_questions)}" if existing_questions else ""}
        Format them as a numbered list with each question on a new line.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="llama-3.3-70b-versatile"
        )
        questions_text = chat_completion.choices[0].message.content.strip()
        questions = [q for q in questions_text.split("\n") if q.strip() and q[0].isdigit()]
        return questions, questions_text
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return [], "Sorry, I encountered an error generating questions. Please try again."

# --- Function to reset quiz ---
def reset_quiz():
    st.session_state.topic = None
    st.session_state.difficulty = None
    st.session_state.asked_questions = set()
    st.session_state.ask_more = False
    st.session_state.quiz_ended = False
    st.session_state.messages = [
        {"role": "assistant", "content": "Let's start a new quiz! Please enter a topic."}
    ]
    st.rerun()

# --- Step 1: Topic input ---
if st.session_state.topic is None and not st.session_state.quiz_ended:
    input_placeholder = st.empty()
    with input_placeholder:
        if prompt := st.chat_input("Enter a topic (e.g., Solar System, Maths, Science, General Knowledge)..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # --- Strict topic validation ---
            words = prompt.strip().split()
            is_invalid = False
            response = None

            if prompt.endswith("?"):
                response = "❌ Please enter a topic name, not a question. Example: 'Solar System'."
                is_invalid = True
            elif len(words) > 4:
                response = "❌ That looks like a sentence. Please enter only a short topic name (e.g., 'Maths', 'Science')."
                is_invalid = True
            elif len(prompt.strip()) < 3:
                response = "❌ That topic name is too short. Try something like 'Maths' or 'Science'."
                is_invalid = True

            if is_invalid:
                # Show error and do NOT set topic
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # ✅ Accept valid topic
                st.session_state.topic = prompt.strip()
                response = f"Great! You chose '{st.session_state.topic}'. Now select a difficulty level:"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()


# --- Step 2: Difficulty selection ---
if st.session_state.topic and st.session_state.difficulty is None and not st.session_state.quiz_ended:
    # Display difficulty options as buttons
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Basic"):
            st.session_state.difficulty = "basic"
    with col2:
        if st.button("Intermediate"):
            st.session_state.difficulty = "intermediate"
    with col3:
        if st.button("Advanced"):
            st.session_state.difficulty = "advanced"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.difficulty:
        st.session_state.messages.append({"role": "user", "content": st.session_state.difficulty.capitalize()})
        
        # Generate initial questions
        questions, questions_text = generate_questions(
            st.session_state.topic, 
            st.session_state.difficulty, 
            st.session_state.asked_questions
        )
        
        if questions:
            st.session_state.asked_questions.update(questions)
            response = f"Here are your {st.session_state.difficulty} questions about {st.session_state.topic}:\n\n{questions_text}\n\nDo you want more questions?"
        else:
            response = questions_text
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.ask_more = True
        st.rerun()

# --- Step 3: "Do you want more?" buttons ---
if st.session_state.ask_more and not st.session_state.quiz_ended:
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    more_selected = None
    
    with col1:
        if st.button("Yes, more questions"):
            more_selected = "yes"
    with col2:
        if st.button("No, that's enough"):
            more_selected = "no"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if more_selected:
        st.session_state.messages.append({"role": "user", "content": more_selected.capitalize()})
        
        if more_selected == "yes":
            # Generate more questions
            questions, questions_text = generate_questions(
                st.session_state.topic, 
                st.session_state.difficulty, 
                st.session_state.asked_questions
            )
            
            if questions:
                st.session_state.asked_questions.update(questions)
                response = f"Here are more questions:\n\n{questions_text}\n\nDo you want more questions?"
            else:
                response = questions_text
                
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            # End the quiz
            response = f"Okay, ending the quiz on {st.session_state.topic}. You answered {len(st.session_state.asked_questions)} questions. Thanks for playing! 🎯"
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.ask_more = False
            st.session_state.quiz_ended = True
        
        st.rerun()

# --- Restart button ---
if st.session_state.quiz_ended:
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    if st.button("Start a new quiz"):
        reset_quiz()
    st.markdown('</div>', unsafe_allow_html=True)

# Hide the input when not needed
if st.session_state.topic is not None or st.session_state.quiz_ended:
    st.markdown("""
    <style>
        .stChatInput {
            display: none;
        }
    </style>

    """, unsafe_allow_html=True)
