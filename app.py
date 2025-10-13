import streamlit as st
import pandas as pd
import time
import json
import base64
import random
from datetime import datetime, timedelta
import plotly.express as px
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from typing import List, Dict

# Page configuration
st.set_page_config(
    page_title="TestBook - Causative Verbs Master",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .st-emotion-cache-1y4p8pa {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .css-1d391kg {
        background: linear-gradient(135deg, #2c3e50, #34495e);
    }
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
    }
    .question-palette {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    .q-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #ecf0f1;
        color: #2c3e50;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-weight: bold;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .q-circle.visited {
        background: #3498db;
        color: white;
    }
    .q-circle.answered {
        background: #27ae60;
        color: white;
    }
    .q-circle.current {
        border-color: #f39c12;
        transform: scale(1.1);
    }
    .quiz-header {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

class PDFProcessor:
    def extract_text(self, pdf_file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            text_content = ""
            
            # Method 1: Using PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except:
                pass
            
            # Method 2: Using pdfplumber
            if not text_content.strip():
                try:
                    pdf_file.seek(0)
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                text_content += text + "\n"
                except:
                    pass
            
            # Method 3: Using PyMuPDF
            if not text_content.strip():
                try:
                    pdf_file.seek(0)
                    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
                    for page in doc:
                        text_content += page.get_text() + "\n"
                    doc.close()
                except:
                    pass
            
            return text_content if text_content.strip() else "No text could be extracted"
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

class QuizGenerator:
    def __init__(self):
        self.sample_questions = self._load_sample_questions()
    
    def _load_sample_questions(self) -> List[Dict]:
        return [
            {
                "question": "Which causative verb is used to give permission?",
                "options": ["A) have", "B) get", "C) make", "D) let"],
                "correct_answer": "D",
                "explanation": "'Let' is used for giving permission."
            },
            {
                "question": "She ______ her hair cut every month.",
                "options": ["A) have", "B) has", "C) getting", "D) made"],
                "correct_answer": "B",
                "explanation": "'Has' is correct third person form."
            },
            {
                "question": "Convert to passive: 'She makes him wash the car.'",
                "options": [
                    "A) She gets the car washed by him",
                    "B) He is made to wash the car", 
                    "C) The car is washed by him",
                    "D) She made him wash the car"
                ],
                "correct_answer": "A",
                "explanation": "In passive causative, 'get' is used with object + V3."
            },
            {
                "question": "I will have the mechanic ______ my bike.",
                "options": ["A) repair", "B) to repair", "C) repairing", "D) repaired"],
                "correct_answer": "A",
                "explanation": "After 'have' in active voice, use base form (V1)."
            },
            {
                "question": "My parents don't ______ me go out at night.",
                "options": ["A) have", "B) get", "C) make", "D) let"],
                "correct_answer": "D",
                "explanation": "'Let' is used for permission."
            },
            {
                "question": "He got his friend ______ him with the project.",
                "options": ["A) help", "B) to help", "C) helping", "D) helped"],
                "correct_answer": "B",
                "explanation": "After 'get', use 'to + V1'."
            },
            {
                "question": "The teacher made the students ______ the assignment.",
                "options": ["A) complete", "B) to complete", "C) completing", "D) completed"],
                "correct_answer": "A",
                "explanation": "After 'make', use base form without 'to'."
            },
            {
                "question": "We should have our house ______ next month.",
                "options": ["A) paint", "B) to paint", "C) painting", "D) painted"],
                "correct_answer": "D",
                "explanation": "In passive causative, use past participle."
            },
            {
                "question": "She let her children ______ outside.",
                "options": ["A) play", "B) to play", "C) playing", "D) played"],
                "correct_answer": "A",
                "explanation": "After 'let', use base form without 'to'."
            },
            {
                "question": "They had the chef ______ a special dinner.",
                "options": ["A) prepare", "B) to prepare", "C) preparing", "D) prepared"],
                "correct_answer": "A",
                "explanation": "After 'have', use base form for active voice."
            }
        ]
    
    def generate_from_text(self, text: str) -> Dict:
        return {
            "title": "Causative Verbs Quiz from PDF",
            "description": "Generated from your uploaded PDF",
            "questions": self.sample_questions,
            "total_questions": len(self.sample_questions),
            "difficulty": "Medium"
        }
    
    def get_sample_quiz(self) -> Dict:
        return {
            "title": "Causative Verbs Practice Quiz",
            "description": "Master causative verbs with this practice session",
            "questions": self.sample_questions,
            "total_questions": len(self.sample_questions),
            "difficulty": "Beginner"
        }
    
    def get_sample_exam(self) -> Dict:
        exam_questions = self.sample_questions * 2
        random.shuffle(exam_questions)
        return {
            "title": "Causative Verbs Certification Exam",
            "description": "Timed exam - 20 questions - 30 minutes",
            "questions": exam_questions[:20],
            "total_questions": 20,
            "difficulty": "Advanced"
        }

class TestBookInterface:
    def start_practice_session(self, quiz_data, timer_minutes=None, show_hints=True):
        st.session_state.current_session = {
            'mode': 'practice',
            'quiz_data': quiz_data,
            'start_time': datetime.now(),
            'timer_minutes': timer_minutes,
            'show_hints': show_hints,
            'current_question': 0,
            'user_answers': [None] * len(quiz_data['questions']),
            'question_start_times': [datetime.now()] * len(quiz_data['questions'])
        }
    
    def start_exam_session(self, quiz_data, duration_minutes, negative_marking=False, questions_count=20, shuffle=True):
        questions = quiz_data['questions'][:questions_count]
        if shuffle:
            random.shuffle(questions)
            
        st.session_state.current_session = {
            'mode': 'exam',
            'quiz_data': {**quiz_data, 'questions': questions},
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(minutes=duration_minutes),
            'duration_minutes': duration_minutes,
            'negative_marking': negative_marking,
            'current_question': 0,
            'user_answers': [None] * len(questions),
            'question_start_times': [datetime.now()] * len(questions),
            'strict_mode': True
        }
    
    def render_quiz_interface(self):
        if 'current_session' not in st.session_state:
            st.warning("No active session. Please start a practice or exam session from dashboard.")
            return
        
        session = st.session_state.current_session
        
        # Header
        self._render_quiz_header(session)
        
        # Question palette
        self._render_question_palette(session)
        
        # Current question
        self._render_current_question(session)
        
        # Navigation
        self._render_navigation_controls(session)
        
        # Auto-submit if time expires
        if session['mode'] == 'exam' and datetime.now() >= session['end_time']:
            self._submit_session(session)
            st.rerun()
    
    def _render_quiz_header(self, session):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.subheader(f"🎯 {session['quiz_data']['title']}")
            st.caption(session['quiz_data']['description'])
        
        with col2:
            if session['mode'] == 'exam':
                time_left = session['end_time'] - datetime.now()
                if time_left.total_seconds() > 0:
                    minutes = int(time_left.total_seconds() // 60)
                    seconds = int(time_left.total_seconds() % 60)
                    st.metric("⏰ Time Left", f"{minutes:02d}:{seconds:02d}")
                else:
                    st.error("⏰ Time's Up!")
            else:
                st.metric("📝 Mode", "Practice")
        
        with col3:
            progress = (session['current_question'] + 1) / len(session['user_answers'])
            st.metric("📊 Progress", f"{int(progress * 100)}%")
        
        with col4:
            answered = sum(1 for ans in session['user_answers'] if ans is not None)
            st.metric("✅ Answered", f"{answered}/{len(session['user_answers'])}")
    
    def _render_question_palette(self, session):
        st.markdown("### 📋 Question Palette")
        
        cols = st.columns(10)
        for i in range(len(session['user_answers'])):
            with cols[i % 10]:
                status = "✅" if session['user_answers'][i] is not None else "⏳"
                if i == session['current_question']:
                    btn_style = "primary"
                else:
                    btn_style = "secondary"
                
                if st.button(f"{status}{i+1}", key=f"palette_{i}", 
                           use_container_width=True, type=btn_style):
                    session['current_question'] = i
                    session['question_start_times'][i] = datetime.now()
                    st.rerun()
    
    def _render_current_question(self, session):
        st.markdown("---")
        
        current_q = session['current_question']
        question_data = session['quiz_data']['questions'][current_q]
        
        st.markdown(f"### ❓ Question {current_q + 1}")
        st.markdown(f"**{question_data['question']}**")
        
        # Options
        selected_option = session['user_answers'][current_q]
        options = question_data['options']
        
        for i, option in enumerate(options):
            col1, col2 = st.columns([1, 20])
            with col1:
                option_key = option[0]  # A, B, C, D
                is_selected = selected_option == option_key
                
                if st.radio(
                    f"Select option for Q{current_q + 1}",
                    [option_key],
                    key=f"opt_{current_q}_{option_key}",
                    index=0 if is_selected else None,
                    label_visibility="collapsed"
                ):
                    session['user_answers'][current_q] = option_key
                    session['question_start_times'][current_q] = datetime.now()
            
            with col2:
                st.write(option)
        
        # Hints for practice mode
        if session['mode'] == 'practice' and session.get('show_hints', True):
            with st.expander("💡 Hint & Explanation"):
                st.info(question_data.get('explanation', 'No explanation available.'))
    
    def _render_navigation_controls(self, session):
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("⏮️ First", use_container_width=True, disabled=session['current_question'] == 0):
                session['current_question'] = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", use_container_width=True, disabled=session['current_question'] == 0):
                session['current_question'] -= 1
                st.rerun()
        
        with col3:
            if st.button("Next ▶️", use_container_width=True, 
                        disabled=session['current_question'] == len(session['user_answers']) - 1):
                session['current_question'] += 1
                st.rerun()
        
        with col4:
            if st.button("⏭️ Last", use_container_width=True, 
                        disabled=session['current_question'] == len(session['user_answers']) - 1):
                session['current_question'] = len(session['user_answers']) - 1
                st.rerun()
        
        # Submit button
        st.markdown("---")
        col5, col6 = st.columns([3, 1])
        with col6:
            if st.button("🎯 Submit Answers", type="primary", use_container_width=True):
                self._submit_session(session)
                st.rerun()
    
    def _submit_session(self, session):
        score = self._calculate_score(session)
        time_taken = datetime.now() - session['start_time']
        
        # Store in history
        result = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'mode': session['mode'],
            'score': score,
            'time_taken': round(time_taken.total_seconds() / 60, 1),
            'total_questions': len(session['user_answers']),
            'correct_answers': sum(1 for i, ans in enumerate(session['user_answers']) 
                                 if ans == session['quiz_data']['questions'][i]['correct_answer'])
        }
        
        st.session_state.quiz_history.append(result)
        
        # Update user stats
        st.session_state.user_data['exams_taken'] += 1
        if st.session_state.user_data['exams_taken'] == 1:
            st.session_state.user_data['average_score'] = score
        else:
            st.session_state.user_data['average_score'] = (
                (st.session_state.user_data['average_score'] * (st.session_state.user_data['exams_taken'] - 1) + score) 
                / st.session_state.user_data['exams_taken']
            )
        st.session_state.user_data['best_score'] = max(st.session_state.user_data['best_score'], score)
        
        # Show results
        st.session_state.show_results = True
        st.session_state.current_session = None
        
        st.balloons()
        st.success(f"🎉 Session completed! Score: {score}%")
    
    def _calculate_score(self, session) -> float:
        correct = 0
        total = len(session['user_answers'])
        
        for i, user_answer in enumerate(session['user_answers']):
            if user_answer == session['quiz_data']['questions'][i]['correct_answer']:
                correct += 1
        
        return round((correct / total) * 100, 1)

class CausativeQuizApp:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.quiz_generator = QuizGenerator()
        self.testbook_interface = TestBookInterface()
        
        # Initialize session state
        if 'user_data' not in st.session_state:
            st.session_state.user_data = {
                'name': 'Student',
                'email': '',
                'exams_taken': 0,
                'average_score': 0,
                'best_score': 0
            }
        
        if 'current_quiz' not in st.session_state:
            st.session_state.current_quiz = None
            
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
            
        if 'show_results' not in st.session_state:
            st.session_state.show_results = False

    def main(self):
        load_css()
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        if 'current_session' in st.session_state and st.session_state.current_session:
            self.testbook_interface.render_quiz_interface()
        elif st.session_state.get('show_results', False):
            self.render_results()
        else:
            self.render_dashboard()

    def render_sidebar(self):
        with st.sidebar:
            st.markdown("""
            <div style="text-align: center;">
                <h1 style="color: #f39c12; margin-bottom: 0;">TestBook</h1>
                <p style="color: white; margin-top: 0;">Causative Verbs Master</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            
            # User profile
            st.subheader("👤 User Profile")
            st.session_state.user_data['name'] = st.text_input("Name", value=st.session_state.user_data['name'])
            st.session_state.user_data['email'] = st.text_input("Email", value=st.session_state.user_data['email'])
            
            st.markdown("---")
            st.subheader("📈 Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tests", st.session_state.user_data['exams_taken'])
            with col2:
                st.metric("Best", f"{st.session_state.user_data['best_score']}%")
            
            st.metric("Average", f"{st.session_state.user_data['average_score']:.1f}%")
            
            st.markdown("---")
            # PDF Upload
            st.subheader("📤 Upload PDF")
            uploaded_file = st.file_uploader("Choose PDF file", type='pdf', label_visibility="collapsed")
            if uploaded_file:
                self.process_uploaded_pdf(uploaded_file)
            
            st.markdown("---")
            # Quick actions
            st.subheader("🚀 Quick Start")
            if st.button("📝 Practice Session", use_container_width=True):
                if not st.session_state.current_quiz:
                    st.session_state.current_quiz = self.quiz_generator.get_sample_quiz()
                self.testbook_interface.start_practice_session(st.session_state.current_quiz)
                st.rerun()
                
            if st.button("🎯 Take Exam", use_container_width=True):
                if not st.session_state.current_quiz:
                    st.session_state.current_quiz = self.quiz_generator.get_sample_exam()
                self.testbook_interface.start_exam_session(st.session_state.current_quiz, duration_minutes=30)
                st.rerun()

    def process_uploaded_pdf(self, uploaded_file):
        with st.spinner("📄 Processing PDF and generating quiz..."):
            text_content = self.pdf_processor.extract_text(uploaded_file)
            quiz_data = self.quiz_generator.generate_from_text(text_content)
            
            if quiz_data:
                st.session_state.current_quiz = quiz_data
                st.success(f"✅ Generated {len(quiz_data['questions'])} questions from PDF!")

    def render_dashboard(self):
        st.title("🏠 TestBook - Causative Verbs Master")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎯 Welcome to Your Learning Dashboard")
            
            # Mode selection
            st.markdown("### 🚀 Choose Your Learning Mode")
            
            tab1, tab2, tab3 = st.tabs(["📝 Practice Mode", "🎯 Exam Mode", "📊 Analytics"])
            
            with tab1:
                st.markdown("""
                **Practice Mode Features:**
                - 💡 Hints and explanations
                - ⏰ Flexible timing
                - 🔄 Unlimited attempts
                - 📚 Learn at your own pace
                """)
                if st.button("Start Practice Session", key="practice_btn", use_container_width=True):
                    if not st.session_state.current_quiz:
                        st.session_state.current_quiz = self.quiz_generator.get_sample_quiz()
                    self.testbook_interface.start_practice_session(st.session_state.current_quiz)
                    st.rerun()
            
            with tab2:
                st.markdown("""
                **Exam Mode Features:**
                - ⏰ Strict timing
                - 📋 Real exam environment
                - 📊 Detailed analytics
                - 🎯 Performance tracking
                """)
                col_a, col_b = st.columns(2)
                with col_a:
                    duration = st.selectbox("Duration", [15, 30, 45, 60], index=1)
                with col_b:
                    questions = st.slider("Questions", 5, 20, 10)
                
                if st.button("Start Exam", key="exam_btn", use_container_width=True):
                    if not st.session_state.current_quiz:
                        st.session_state.current_quiz = self.quiz_generator.get_sample_exam()
                    self.testbook_interface.start_exam_session(
                        st.session_state.current_quiz, 
                        duration_minutes=duration,
                        questions_count=questions
                    )
                    st.rerun()
            
            with tab3:
                self.render_analytics()
                
        with col2:
            st.subheader("📊 Progress Overview")
            
            if st.session_state.quiz_history:
                scores = [q['score'] for q in st.session_state.quiz_history]
                fig = px.line(
                    x=range(1, len(scores)+1), 
                    y=scores, 
                    title="Your Progress Over Time",
                    labels={'x': 'Attempt Number', 'y': 'Score (%)'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Recent tests
                st.markdown("**Recent Tests:**")
                for test in st.session_state.quiz_history[-3:]:
                    st.write(f"- {test['date']}: {test['score']}% ({test['mode']})")
            else:
                st.info("📈 Complete your first quiz to see progress analytics!")
                
            # Current quiz info
            if st.session_state.current_quiz:
                st.markdown("---")
                st.subheader("📚 Available Quiz")
                st.write(f"**{st.session_state.current_quiz['title']}**")
                st.write(f"Questions: {st.session_state.current_quiz['total_questions']}")
                st.write(f"Difficulty: {st.session_state.current_quiz['difficulty']}")

    def render_analytics(self):
        if not st.session_state.quiz_history:
            st.info("Complete your first quiz to see detailed analytics!")
            return
        
        df = pd.DataFrame(st.session_state.quiz_history)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Performance Metrics")
            st.metric("Total Tests", len(df))
            st.metric("Best Score", f"{df['score'].max()}%")
            st.metric("Average Score", f"{df['score'].mean():.1f}%")
            st.metric("Average Time", f"{df['time_taken'].mean():.1f} min")
        
        with col2:
            st.subheader("📊 Score Distribution")
            fig = px.histogram(df, x='score', title="Your Score Distribution", nbins=10)
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Test History")
        st.dataframe(df[['date', 'mode', 'score', 'time_taken', 'correct_answers', 'total_questions']], 
                    use_container_width=True)

    def render_results(self):
        if not st.session_state.quiz_history:
            return
            
        latest_result = st.session_state.quiz_history[-1]
        
        st.title("🎉 Test Results")
        
        # Score card
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Score", f"{latest_result['score']}%")
        with col2:
            st.metric("Correct Answers", f"{latest_result['correct_answers']}/{latest_result['total_questions']}")
        with col3:
            st.metric("Time Taken", f"{latest_result['time_taken']} min")
        
        st.markdown("---")
        
        # Detailed review
        st.subheader("📋 Detailed Review")
        
        if st.session_state.get('last_session_answers'):
            session = st.session_state.last_session_answers
            for i, (user_ans, question_data) in enumerate(zip(session['user_answers'], session['quiz_data']['questions'])):
                is_correct = user_ans == question_data['correct_answer']
                
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**Q{i+1}:** {question_data['question']}")
                        st.write(f"**Your answer:** {user_ans if user_ans else 'Not attempted'}")
                        st.write(f"**Correct answer:** {question_data['correct_answer']}")
                    with col2:
                        if is_correct:
                            st.success("✅ Correct")
                        else:
                            st.error("❌ Incorrect")
                    
                    with st.expander("View Explanation"):
                        st.info(question_data.get('explanation', 'No explanation available.'))
                    
                    st.markdown("---")
        
        # Actions
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()
        with col5:
            if st.button("🔄 Take Again", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()
        with col6:
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()

if __name__ == "__main__":
    app = CausativeQuizApp()
    app.main()
