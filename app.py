import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import json

# Page configuration
st.set_page_config(
    page_title="TestBook - Online Examination Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin: 1rem 0;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .question-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .timer-warning {
        color: #ff6b6b;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .timer-normal {
        color: #1f77b4;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .submit-btn {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 2rem;
        border: none;
        border-radius: 5px;
        font-size: 1.1rem;
    }
    .nav-btn {
        background-color: #6c757d;
        color: white;
        padding: 0.3rem 1rem;
        border: none;
        border-radius: 3px;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

class ExamSystem:
    def __init__(self):
        self.questions = self.load_questions()
        self.exam_duration = 3600  # 1 hour in seconds
        self.current_question = 0
        
    def load_questions(self):
        """Load sample questions for the exam"""
        questions = [
            {
                "id": 1,
                "question": "What is the time complexity of binary search?",
                "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
                "correct": 1,
                "type": "mcq",
                "marks": 2
            },
            {
                "id": 2,
                "question": "Which data structure uses LIFO principle?",
                "options": ["Queue", "Stack", "Tree", "Graph"],
                "correct": 1,
                "type": "mcq",
                "marks": 2
            },
            {
                "id": 3,
                "question": "Explain the concept of polymorphism in OOP.",
                "options": [],
                "correct": None,
                "type": "descriptive",
                "marks": 5
            },
            {
                "id": 4,
                "question": "What is the output of: print(2**3)?",
                "options": ["6", "8", "9", "5"],
                "correct": 1,
                "type": "mcq",
                "marks": 1
            },
            {
                "id": 5,
                "question": "Describe the ACID properties in DBMS.",
                "options": [],
                "correct": None,
                "type": "descriptive",
                "marks": 5
            }
        ]
        return questions
    
    def calculate_score(self, answers):
        """Calculate exam score"""
        score = 0
        for q_id, answer in answers.items():
            question = next((q for q in self.questions if q["id"] == q_id), None)
            if question and question["type"] == "mcq":
                if answer == question["correct"]:
                    score += question["marks"]
        return score
    
    def generate_report(self, answers, time_taken):
        """Generate detailed performance report"""
        score = self.calculate_score(answers)
        total_marks = sum(q["marks"] for q in self.questions)
        
        # Performance analysis
        correct_mcq = 0
        total_mcq = 0
        
        for q_id, answer in answers.items():
            question = next((q for q in self.questions if q["id"] == q_id), None)
            if question and question["type"] == "mcq":
                total_mcq += 1
                if answer == question["correct"]:
                    correct_mcq += 1
        
        accuracy = (correct_mcq / total_mcq * 100) if total_mcq > 0 else 0
        
        return {
            "score": score,
            "total_marks": total_marks,
            "percentage": (score / total_marks) * 100,
            "accuracy": accuracy,
            "time_taken": time_taken,
            "time_per_question": time_taken / len(self.questions) if self.questions else 0
        }

def initialize_session_state():
    """Initialize session state variables"""
    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
    if 'exam_finished' not in st.session_state:
        st.session_state.exam_finished = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'exam_system' not in st.session_state:
        st.session_state.exam_system = ExamSystem()
    if 'time_remaining' not in st.session_state:
        st.session_state.time_remaining = 3600

def display_timer():
    """Display real-time countdown timer"""
    if st.session_state.exam_started and not st.session_state.exam_finished:
        elapsed = time.time() - st.session_state.start_time
        remaining = st.session_state.exam_system.exam_duration - elapsed
        
        if remaining <= 0:
            st.session_state.exam_finished = True
            remaining = 0
        
        # Update time remaining
        st.session_state.time_remaining = max(0, int(remaining))
        
        # Format time
        hours = st.session_state.time_remaining // 3600
        minutes = (st.session_state.time_remaining % 3600) // 60
        seconds = st.session_state.time_remaining % 60
        
        # Display timer with color coding
        timer_color = "timer-warning" if st.session_state.time_remaining < 600 else "timer-normal"
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 10px;'>
            <span class='{timer_color}'>Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-submit when time expires
        if st.session_state.time_remaining <= 0:
            st.session_state.exam_finished = True
            st.rerun()

def display_question_navigation():
    """Display question navigation panel"""
    st.sidebar.markdown("### Question Navigation")
    
    cols = st.sidebar.columns(3)
    with cols[0]:
        if st.button("◀ Previous", use_container_width=True):
            if st.session_state.current_question > 0:
                st.session_state.current_question -= 1
                st.rerun()
    
    with cols[1]:
        st.markdown(f"**{st.session_state.current_question + 1}/{len(st.session_state.exam_system.questions)}**")
    
    with cols[2]:
        if st.button("Next ▶", use_container_width=True):
            if st.session_state.current_question < len(st.session_state.exam_system.questions) - 1:
                st.session_state.current_question += 1
                st.rerun()
    
    # Question palette
    st.sidebar.markdown("### Question Palette")
    questions_per_row = 5
    questions = st.session_state.exam_system.questions
    
    for i in range(0, len(questions), questions_per_row):
        cols = st.sidebar.columns(questions_per_row)
        for j, col in enumerate(cols):
            if i + j < len(questions):
                q_num = i + j
                answered = questions[q_num]["id"] in st.session_state.answers
                button_type = "primary" if answered else "secondary"
                
                if col.button(f"{q_num + 1}", use_container_width=True, type=button_type):
                    st.session_state.current_question = q_num
                    st.rerun()

def display_current_question():
    """Display current question with options"""
    questions = st.session_state.exam_system.questions
    current_q = questions[st.session_state.current_question]
    
    st.markdown(f"### Question {st.session_state.current_question + 1}")
    
    with st.container():
        st.markdown(f'<div class="question-container">', unsafe_allow_html=True)
        
        # Question text
        st.markdown(f"**{current_q['question']}**")
        st.markdown(f"*Marks: {current_q['marks']}*")
        
        # Answer input based on question type
        if current_q["type"] == "mcq":
            options = current_q["options"]
            current_answer = st.session_state.answers.get(current_q["id"], None)
            
            answer = st.radio(
                "Select your answer:",
                options,
                index=current_answer if current_answer is not None else None,
                key=f"q_{current_q['id']}"
            )
            
            if answer:
                answer_index = options.index(answer)
                st.session_state.answers[current_q["id"]] = answer_index
                
        else:  # descriptive
            current_answer = st.session_state.answers.get(current_q["id"], "")
            answer = st.text_area(
                "Write your answer:",
                value=current_answer,
                height=150,
                key=f"q_{current_q['id']}"
            )
            if answer:
                st.session_state.answers[current_q["id"]] = answer
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_results():
    """Display exam results and analytics"""
    time_taken = st.session_state.exam_system.exam_duration - st.session_state.time_remaining
    report = st.session_state.exam_system.generate_report(st.session_state.answers, time_taken)
    
    st.markdown('<div class="main-header">📊 Exam Results</div>', unsafe_allow_html=True)
    
    # Score cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Score", f"{report['score']}/{report['total_marks']}")
    
    with col2:
        st.metric("Percentage", f"{report['percentage']:.1f}%")
    
    with col3:
        st.metric("Accuracy", f"{report['accuracy']:.1f}%")
    
    with col4:
        st.metric("Time Taken", f"{report['time_taken']//60}m {report['time_taken']%60}s")
    
    # Detailed analysis
    st.markdown('<div class="section-header">Detailed Analysis</div>', unsafe_allow_html=True)
    
    # Performance chart
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = report['percentage'],
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Performance"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "red"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ]
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Question-wise review
    st.markdown('<div class="section-header">Question-wise Review</div>', unsafe_allow_html=True)
    
    review_data = []
    for question in st.session_state.exam_system.questions:
        user_answer = st.session_state.answers.get(question["id"])
        is_correct = False
        
        if question["type"] == "mcq":
            is_correct = user_answer == question["correct"]
        
        review_data.append({
            "Question": question["id"],
            "Type": question["type"].upper(),
            "Your Answer": user_answer,
            "Correct Answer": question["correct"] if question["type"] == "mcq" else "N/A",
            "Status": "Correct" if is_correct else "Incorrect" if user_answer is not None else "Not Attempted",
            "Marks": question["marks"] if is_correct else 0
        })
    
    review_df = pd.DataFrame(review_data)
    st.dataframe(review_df, use_container_width=True)

def main():
    initialize_session_state()
    
    # Main header
    st.markdown('<div class="main-header">📚 TestBook - Online Examination Platform</div>', unsafe_allow_html=True)
    
    if not st.session_state.exam_started and not st.session_state.exam_finished:
        # Welcome screen
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;'>
            <h2>Welcome to TestBook</h2>
            <p style='font-size: 1.2rem;'>Professional Online Examination Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("### Exam Instructions")
            st.markdown("""
            - Total Questions: 5
            - Total Marks: 15
            - Time Allotted: 1 Hour
            - Questions include both MCQ and Descriptive types
            - Use navigation panel to move between questions
            - Timer will be displayed during the exam
            - Auto-submit when time expires
            """)
            
            if st.button("🚀 Start Exam", use_container_width=True, type="primary"):
                st.session_state.exam_started = True
                st.session_state.start_time = time.time()
                st.rerun()
    
    elif st.session_state.exam_started and not st.session_state.exam_finished:
        # Exam in progress
        display_timer()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            display_current_question()
        
        with col2:
            display_question_navigation()
            
            st.sidebar.markdown("---")
            if st.sidebar.button("✅ Submit Exam", type="primary", use_container_width=True):
                st.session_state.exam_finished = True
                st.rerun()
    
    elif st.session_state.exam_finished:
        # Results screen
        display_results()
        
        if st.button("🔄 Take Another Test", use_container_width=True):
            # Reset session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
