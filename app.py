import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import json
import pdfplumber
import re
import io
from typing import List, Dict, Any

# Page configuration
st.set_page_config(
    page_title="SmartQuiz Pro - AI Powered Test Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
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
        font-size: 1.3rem;
        text-align: center;
        padding: 0.5rem;
        background: #fff5f5;
        border-radius: 8px;
        border: 2px solid #ff6b6b;
    }
    .timer-normal {
        color: #1f77b4;
        font-weight: bold;
        font-size: 1.3rem;
        text-align: center;
        padding: 0.5rem;
        background: #f0f8ff;
        border-radius: 8px;
        border: 2px solid #1f77b4;
    }
    .correct-answer {
        background-color: #d4edda !important;
        border-left: 5px solid #28a745 !important;
    }
    .incorrect-answer {
        background-color: #f8d7da !important;
        border-left: 5px solid #dc3545 !important;
    }
    .marked-question {
        background-color: #fff3cd !important;
        border-left: 5px solid #ffc107 !important;
    }
    .nav-btn-active {
        background-color: #1f77b4 !important;
        color: white !important;
    }
    .quick-nav-btn {
        width: 40px;
        height: 40px;
        margin: 2px;
        border: 2px solid #1f77b4;
        border-radius: 5px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

class QuizGenerator:
    def __init__(self):
        self.mcq_pattern = r'(\d+\)\s*.*?\?)(.*?)(?=\d+\)|$)'
        self.option_pattern = r'([a-d])\)\s*(.*?)(?=[a-d]\)|$)'
        self.answer_pattern = r'[Aa]nswer:\s*([a-d])'
    
    def extract_mcqs_from_pdf(self, pdf_file) -> List[Dict[str, Any]]:
        """Extract MCQs from uploaded PDF"""
        questions = []
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            # Find all questions
            question_matches = re.finditer(self.mcq_pattern, text, re.DOTALL)
            
            for match in question_matches:
                question_text = match.group(1).strip()
                options_text = match.group(2).strip()
                
                # Extract options
                options = []
                option_matches = re.finditer(self.option_pattern, options_text, re.DOTALL)
                for opt_match in option_matches:
                    options.append(opt_match.group(2).strip())
                
                # Extract answer
                answer_match = re.search(self.answer_pattern, options_text)
                correct_answer = None
                if answer_match:
                    correct_answer = answer_match.group(1).lower()
                
                if len(options) == 4 and correct_answer:
                    questions.append({
                        'id': len(questions) + 1,
                        'question': question_text,
                        'options': options,
                        'correct_answer': correct_answer,
                        'correct_index': ord(correct_answer) - ord('a'),
                        'type': 'mcq',
                        'marks': 1
                    })
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
        
        return questions

class ExamSystem:
    def __init__(self):
        self.questions = []
        self.exam_duration = 1800  # 30 minutes default
        self.mode = "exam"  # "exam" or "practice"
        
    def load_sample_questions(self):
        """Load sample questions if no PDF uploaded"""
        self.questions = [
            {
                "id": 1,
                "question": "1) What is the time complexity of binary search algorithm?",
                "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
                "correct_answer": "b",
                "correct_index": 1,
                "type": "mcq",
                "marks": 1
            },
            {
                "id": 2,
                "question": "2) Which data structure uses LIFO principle?",
                "options": ["Queue", "Stack", "Tree", "Graph"],
                "correct_answer": "b",
                "correct_index": 1,
                "type": "mcq",
                "marks": 1
            },
            {
                "id": 3,
                "question": "3) What does CPU stand for?",
                "options": ["Central Processing Unit", "Computer Personal Unit", "Central Processor Unit", "Central Process Unit"],
                "correct_answer": "a",
                "correct_index": 0,
                "type": "mcq",
                "marks": 1
            },
            {
                "id": 4,
                "question": "4) Which language is primarily used for web development?",
                "options": ["Python", "Java", "JavaScript", "C++"],
                "correct_answer": "c",
                "correct_index": 2,
                "type": "mcq",
                "marks": 1
            },
            {
                "id": 5,
                "question": "5) What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct_answer": "c",
                "correct_index": 2,
                "type": "mcq",
                "marks": 1
            }
        ]
    
    def calculate_score(self, answers, question_times):
        """Calculate exam score with detailed analytics"""
        score = 0
        correct_count = 0
        total_attempted = 0
        
        for q_id, answer_data in answers.items():
            question = next((q for q in self.questions if q["id"] == q_id), None)
            if question and answer_data['answered']:
                total_attempted += 1
                if answer_data['answer'] == question["correct_index"]:
                    score += question["marks"]
                    correct_count += 1
        
        accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
        total_time = sum(question_times.values())
        avg_time = total_time / len(answers) if answers else 0
        
        return {
            "score": score,
            "total_marks": len(self.questions),
            "correct_count": correct_count,
            "total_attempted": total_attempted,
            "accuracy": accuracy,
            "total_time": total_time,
            "avg_time_per_question": avg_time
        }

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'exam_started': False,
        'exam_finished': False,
        'practice_mode': False,
        'start_time': None,
        'current_question': 0,
        'answers': {},
        'question_start_time': None,
        'question_times': {},
        'marked_questions': set(),
        'show_answers': False,
        'exam_system': ExamSystem(),
        'quiz_generator': QuizGenerator(),
        'session_history': [],
        'time_remaining': 1800,
        'total_exam_time': 1800
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def display_header():
    """Display main header with mode information"""
    mode_text = "Practice Mode" if st.session_state.practice_mode else "Exam Mode"
    mode_color = "#28a745" if st.session_state.practice_mode else "#dc3545"
    
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: linear-gradient(135deg, {mode_color}20 0%, #1f77b420 100%); border-radius: 10px; margin-bottom: 1rem;'>
        <h1 style='margin: 0; color: #1f77b4;'>🧠 SmartQuiz Pro</h1>
        <div style='background-color: {mode_color}; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold;'>
            {mode_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_timer():
    """Display real-time countdown timer with progress"""
    if st.session_state.exam_started and not st.session_state.exam_finished:
        if not st.session_state.practice_mode:
            elapsed = time.time() - st.session_state.start_time
            remaining = st.session_state.total_exam_time - elapsed
            
            if remaining <= 0:
                st.session_state.exam_finished = True
                remaining = 0
            
            st.session_state.time_remaining = max(0, int(remaining))
            
            # Format time
            hours = st.session_state.time_remaining // 3600
            minutes = (st.session_state.time_remaining % 3600) // 60
            seconds = st.session_state.time_remaining % 60
            
            # Progress calculation
            progress = (st.session_state.total_exam_time - st.session_state.time_remaining) / st.session_state.total_exam_time
            
            # Display timer with color coding
            timer_color = "timer-warning" if st.session_state.time_remaining < 300 else "timer-normal"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div class='{timer_color}'>
                    ⏰ Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}
                </div>
                """, unsafe_allow_html=True)
                st.progress(progress)
            
            with col2:
                # Current question timer
                if st.session_state.question_start_time:
                    q_elapsed = time.time() - st.session_state.question_start_time
                    st.metric("⏱️ Question Time", f"{int(q_elapsed)}s")
            
            # Auto-submit when time expires
            if st.session_state.time_remaining <= 0:
                st.session_state.exam_finished = True
                st.rerun()
        else:
            # Practice mode timer
            if st.session_state.question_start_time:
                q_elapsed = time.time() - st.session_state.question_start_time
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⏱️ Current Question", f"{int(q_elapsed)}s")
                with col2:
                    total_time = sum(st.session_state.question_times.values()) + int(q_elapsed)
                    st.metric("📊 Total Session", f"{total_time}s")

def display_question_navigation():
    """Display comprehensive question navigation panel"""
    st.sidebar.markdown("### 🧭 Navigation Panel")
    
    # Main navigation buttons
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if st.button("⏮️ Prev", use_container_width=True, disabled=st.session_state.current_question == 0):
            save_question_time()
            st.session_state.current_question -= 1
            st.session_state.question_start_time = time.time()
            st.rerun()
    
    with col2:
        st.markdown(f"**{st.session_state.current_question + 1}/{len(st.session_state.exam_system.questions)}**")
    
    with col3:
        if st.button("Next ⏭️", use_container_width=True, 
                    disabled=st.session_state.current_question == len(st.session_state.exam_system.questions) - 1):
            save_question_time()
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.rerun()
    
    # Mark question button
    current_q_id = st.session_state.exam_system.questions[st.session_state.current_question]["id"]
    is_marked = current_q_id in st.session_state.marked_questions
    
    mark_text = "✅ Unmark" if is_marked else "📌 Mark"
    if st.sidebar.button(mark_text, use_container_width=True):
        if is_marked:
            st.session_state.marked_questions.remove(current_q_id)
        else:
            st.session_state.marked_questions.add(current_q_id)
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔢 Quick Navigation")
    
    # Question palette with status
    questions_per_row = 5
    questions = st.session_state.exam_system.questions
    
    for i in range(0, len(questions), questions_per_row):
        cols = st.sidebar.columns(questions_per_row)
        for j, col in enumerate(cols):
            if i + j < len(questions):
                q_num = i + j
                q_id = questions[q_num]["id"]
                
                # Determine button style
                answered = q_id in st.session_state.answers and st.session_state.answers[q_id]['answered']
                marked = q_id in st.session_state.marked_questions
                current = q_num == st.session_state.current_question
                
                button_label = f"{q_num + 1}"
                button_type = "primary" if current else "secondary"
                
                if marked:
                    button_label = f"📍{q_num + 1}"
                
                if col.button(button_label, use_container_width=True, type=button_type):
                    save_question_time()
                    st.session_state.current_question = q_num
                    st.session_state.question_start_time = time.time()
                    st.rerun()

def save_question_time():
    """Save time taken for current question"""
    if (st.session_state.question_start_time and 
        st.session_state.exam_started and 
        not st.session_state.exam_finished):
        
        current_q_id = st.session_state.exam_system.questions[st.session_state.current_question]["id"]
        time_taken = time.time() - st.session_state.question_start_time
        st.session_state.question_times[current_q_id] = time_taken

def display_current_question():
    """Display current question with interactive options"""
    questions = st.session_state.exam_system.questions
    current_q = questions[st.session_state.current_question]
    current_q_id = current_q["id"]
    
    # Get current answer if exists
    current_answer_data = st.session_state.answers.get(current_q_id, {'answered': False, 'answer': None})
    
    # Apply CSS classes based on state
    container_class = "question-container"
    if st.session_state.exam_finished or st.session_state.show_answers:
        if current_answer_data['answered'] and current_answer_data['answer'] == current_q["correct_index"]:
            container_class += " correct-answer"
        elif current_answer_data['answered']:
            container_class += " incorrect-answer"
    elif current_q_id in st.session_state.marked_questions:
        container_class += " marked-question"
    
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Question header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### ❓ Question {st.session_state.current_question + 1}")
    with col2:
        st.markdown(f"**Marks: {current_q['marks']}**")
    
    # Question text
    st.markdown(f"**{current_q['question']}**")
    
    # Options with interactive selection
    options = current_q["options"]
    selected_index = current_answer_data['answer'] if current_answer_data['answered'] else None
    
    for i, option in enumerate(options):
        option_letter = chr(97 + i)  # a, b, c, d
        col1, col2 = st.columns([1, 20])
        
        with col1:
            # Show correct/incorrect indicators in review mode
            if st.session_state.exam_finished or st.session_state.show_answers:
                if i == current_q["correct_index"]:
                    st.success("✅")
                elif i == selected_index and i != current_q["correct_index"]:
                    st.error("❌")
                else:
                    st.write("○")
            else:
                if i == selected_index:
                    st.info("●")
                else:
                    st.write("○")
        
        with col2:
            if st.session_state.exam_finished:
                # Display only in finished mode
                st.write(f"**{option_letter})** {option}")
            else:
                # Interactive radio in active mode
                if st.radio(
                    f"Option {option_letter}",
                    [option],
                    key=f"opt_{current_q_id}_{i}",
                    index=0 if i == selected_index else None,
                    label_visibility="collapsed"
                ):
                    st.session_state.answers[current_q_id] = {
                        'answered': True,
                        'answer': i
                    }
                    st.rerun()
    
    # Show answer button in practice mode
    if st.session_state.practice_mode and not st.session_state.exam_finished:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Show Answer", use_container_width=True):
                st.session_state.show_answers = True
                st.rerun()
        with col2:
            if st.session_state.show_answers:
                correct_letter = chr(97 + current_q["correct_index"])
                st.info(f"**Correct Answer: {correct_letter}) {options[current_q['correct_index']]}**")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_results():
    """Display comprehensive results and analytics"""
    report = st.session_state.exam_system.calculate_score(
        st.session_state.answers, 
        st.session_state.question_times
    )
    
    # Save to history
    history_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'mode': 'Practice' if st.session_state.practice_mode else 'Exam',
        'score': report['score'],
        'total_marks': report['total_marks'],
        'accuracy': report['accuracy'],
        'total_time': report['total_time'],
        'total_questions': len(st.session_state.exam_system.questions)
    }
    st.session_state.session_history.append(history_entry)
    
    st.markdown('<div class="main-header">📊 Detailed Results</div>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Score", f"{report['score']}/{report['total_marks']}")
    
    with col2:
        st.metric("📈 Accuracy", f"{report['accuracy']:.1f}%")
    
    with col3:
        st.metric("⏱️ Total Time", f"{int(report['total_time'])}s")
    
    with col4:
        st.metric("📝 Attempted", f"{report['total_attempted']}/{len(st.session_state.exam_system.questions)}")
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Score distribution
        fig1 = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = report['accuracy'],
            title = {'text': "Accuracy"},
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
        fig1.update_layout(height=300)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Time analysis
        time_data = {
            'Metric': ['Total Time', 'Avg Time/Question'],
            'Seconds': [report['total_time'], report['avg_time_per_question']]
        }
        fig2 = px.bar(time_data, x='Metric', y='Seconds', title="Time Analysis")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Question-wise review
    st.markdown("### 📋 Question-wise Review")
    
    review_data = []
    for question in st.session_state.exam_system.questions:
        q_id = question["id"]
        answer_data = st.session_state.answers.get(q_id, {'answered': False, 'answer': None})
        time_taken = st.session_state.question_times.get(q_id, 0)
        
        status = "Not Attempted"
        if answer_data['answered']:
            if answer_data['answer'] == question["correct_index"]:
                status = "Correct"
            else:
                status = "Incorrect"
        
        review_data.append({
            "Q.No": question["id"],
            "Status": status,
            "Your Answer": chr(97 + answer_data['answer']) if answer_data['answered'] else "Not Attempted",
            "Correct Answer": chr(97 + question["correct_index"]),
            "Time Taken (s)": f"{int(time_taken)}s",
            "Marks": question["marks"] if status == "Correct" else 0
        })
    
    review_df = pd.DataFrame(review_data)
    st.dataframe(review_df, use_container_width=True)

def display_history():
    """Display session history"""
    if st.session_state.session_history:
        st.markdown("### 📜 Session History")
        
        history_df = pd.DataFrame(st.session_state.session_history)
        st.dataframe(history_df, use_container_width=True)
        
        # History chart
        if len(history_df) > 1:
            fig = px.line(history_df, x='timestamp', y='accuracy', 
                         title="Accuracy Trend Over Sessions")
            st.plotly_chart(fig, use_container_width=True)

def main():
    initialize_session_state()
    display_header()
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        if not st.session_state.exam_started:
            # Mode selection
            mode = st.radio("Select Mode:", ["Exam Mode", "Practice Mode"])
            st.session_state.practice_mode = (mode == "Practice Mode")
            
            # Time settings
            if not st.session_state.practice_mode:
                st.session_state.total_exam_time = st.slider(
                    "Exam Duration (minutes):",
                    min_value=5,
                    max_value=180,
                    value=30
                ) * 60
            
            # PDF upload for question generation
            st.markdown("### 📁 Upload Questions")
            pdf_file = st.file_uploader("Upload PDF with MCQs", type=['pdf'])
            
            if pdf_file is not None:
                if st.button("Extract Questions from PDF"):
                    with st.spinner("Extracting questions from PDF..."):
                        questions = st.session_state.quiz_generator.extract_mcqs_from_pdf(pdf_file)
                        if questions:
                            st.session_state.exam_system.questions = questions
                            st.success(f"✅ Extracted {len(questions)} questions!")
                        else:
                            st.error("❌ No questions found in PDF. Using sample questions.")
                            st.session_state.exam_system.load_sample_questions()
            else:
                if st.button("Use Sample Questions"):
                    st.session_state.exam_system.load_sample_questions()
            
            # Start button
            if st.session_state.exam_system.questions:
                start_text = "🚀 Start Practice Session" if st.session_state.practice_mode else "🚀 Start Exam"
                if st.button(start_text, type="primary", use_container_width=True):
                    st.session_state.exam_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.question_start_time = time.time()
                    st.rerun()
    
    # Main content area
    if not st.session_state.exam_system.questions:
        # Welcome screen
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;'>
            <h1>Welcome to SmartQuiz Pro! 🧠</h1>
            <p style='font-size: 1.3rem;'>AI-Powered Examination Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Features")
            st.markdown("""
            - **Automated Quiz Generation** from PDFs
            - **Exam & Practice Modes**
            - **Real-time Timer & Stopwatch**
            - **Smart Navigation** like TestBook
            - **Detailed Analytics & History**
            - **Question-wise Time Tracking**
            - **Answer Review & Performance Insights**
            """)
        
        with col2:
            st.markdown("### 📝 How to Use")
            st.markdown("""
            1. **Upload PDF** with MCQs or use sample questions
            2. **Select Mode**: Exam (timed) or Practice (flexible)
            3. **Configure Settings**: Time limits, etc.
            4. **Start Session** and begin answering
            5. **Review Results** with detailed analytics
            """)
    
    elif st.session_state.exam_started and not st.session_state.exam_finished:
        # Exam/Practice in progress
        display_timer()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            display_current_question()
        
        with col2:
            display_question_navigation()
            
            # Submit button
            st.sidebar.markdown("---")
            submit_text = "✅ Submit Practice" if st.session_state.practice_mode else "✅ Submit Exam"
            if st.sidebar.button(submit_text, type="primary", use_container_width=True):
                save_question_time()
                st.session_state.exam_finished = True
                st.rerun()
    
    elif st.session_state.exam_finished:
        # Results screen
        display_results()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Session", use_container_width=True):
                # Reset for new session
                st.session_state.exam_started = False
                st.session_state.exam_finished = False
                st.session_state.current_question = 0
                st.session_state.answers = {}
                st.session_state.question_times = {}
                st.session_state.marked_questions = set()
                st.session_state.show_answers = False
                st.session_state.question_start_time = None
                st.rerun()
        
        with col2:
            if st.button("📊 View History", use_container_width=True):
                display_history()
    
    # Always show history in sidebar if available
    if st.session_state.session_history:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 📈 Recent Performance")
            latest = st.session_state.session_history[-1]
            st.metric("Last Score", f"{latest['score']}/{latest['total_marks']}")
            st.metric("Last Accuracy", f"{latest['accuracy']:.1f}%")

if __name__ == "__main__":
    main()
