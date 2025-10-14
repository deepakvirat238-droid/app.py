import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pdfplumber
import re
import os
import json

# Page configuration
st.set_page_config(
    page_title="QuizMaster Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
        background: linear-gradient(45deg, #2E86AB, #A23B72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .question-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border-left: 6px solid #2E86AB;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .option-box {
        background: #f8f9fa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .option-box:hover {
        background: #e9ecef;
        border-color: #2E86AB;
    }
    .option-selected {
        background: #2E86AB !important;
        color: white !important;
        border-color: #2E86AB !important;
    }
    .option-correct {
        background: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    .option-incorrect {
        background: #dc3545 !important;
        color: white !important;
        border-color: #dc3545 !important;
    }
    .timer-box {
        background: linear-gradient(45deg, #2E86AB, #A23B72);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .nav-btn {
        width: 100%;
        margin: 0.2rem 0;
        padding: 0.7rem;
        border: none;
        border-radius: 8px;
        background: #6c757d;
        color: white;
        font-weight: bold;
    }
    .nav-btn:hover {
        background: #5a6268;
    }
    .nav-btn-active {
        background: #2E86AB !important;
    }
    .nav-btn-answered {
        background: #28a745 !important;
    }
    .nav-btn-marked {
        background: #ffc107 !important;
        color: black !important;
    }
    .stats-box {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class PDFQuizExtractor:
    def __init__(self):
        self.question_pattern = r'(\d+\.|Q\d+\.|\d+\)\s*)(.*?)\?'
        self.option_pattern = r'([A-Da-d])[\)\.]\s*(.*?)(?=\n[A-Da-d][\)\.]|\nAnswer|\n\n|$)'
        self.answer_pattern = r'[Aa]nswer\s*[:\-]?\s*([A-Da-d])'
    
    def extract_questions_from_pdf(self, pdf_file):
        """Extract questions from PDF with exact format matching"""
        questions = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            
            # Split by potential question boundaries
            sections = re.split(r'\n\s*\n', full_text)
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Look for question pattern
                question_match = re.search(self.question_pattern, section, re.DOTALL | re.IGNORECASE)
                if not question_match:
                    continue
                
                question_text = question_match.group(2).strip()
                
                # Extract options
                options = []
                option_matches = re.finditer(self.option_pattern, section, re.DOTALL)
                for match in option_matches:
                    option_text = match.group(2).strip()
                    if option_text and len(option_text) > 1:
                        options.append(option_text)
                
                # Extract answer
                answer_match = re.search(self.answer_pattern, section, re.IGNORECASE)
                correct_answer = None
                if answer_match:
                    correct_answer = answer_match.group(1).upper()
                    correct_index = ord(correct_answer) - ord('A')
                else:
                    continue
                
                if len(options) == 4 and correct_answer in ['A', 'B', 'C', 'D']:
                    questions.append({
                        'id': len(questions) + 1,
                        'question': f"{question_text}?",
                        'options': options,
                        'correct_answer': correct_answer,
                        'correct_index': correct_index,
                        'type': 'mcq',
                        'marks': 1
                    })
            
            return questions
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return []

class QuizManager:
    def __init__(self):
        self.questions = []
        self.session_history = []
    
    def load_sample_questions(self):
        """Load sample questions for demonstration"""
        self.questions = [
            {
                'id': 1,
                'question': "What is the first prime number?",
                'options': ["3", "2", "7", "9"],
                'correct_answer': "B",
                'correct_index': 1,
                'type': 'mcq',
                'marks': 1
            },
            {
                'id': 2,
                'question': "Which programming language is known for web development?",
                'options': ["Python", "Java", "JavaScript", "C++"],
                'correct_answer': "C",
                'correct_index': 2,
                'type': 'mcq',
                'marks': 1
            },
            {
                'id': 3,
                'question': "What does CPU stand for?",
                'options': ["Central Processing Unit", "Computer Personal Unit", "Central Processor Unit", "Central Process Unit"],
                'correct_answer': "A",
                'correct_index': 0,
                'type': 'mcq',
                'marks': 1
            },
            {
                'id': 4,
                'question': "Which data structure uses LIFO?",
                'options': ["Queue", "Stack", "Array", "Linked List"],
                'correct_answer': "B",
                'correct_index': 1,
                'type': 'mcq',
                'marks': 1
            },
            {
                'id': 5,
                'question': "What is the capital of France?",
                'options': ["London", "Berlin", "Paris", "Madrid"],
                'correct_answer': "C",
                'correct_index': 2,
                'type': 'mcq',
                'marks': 1
            }
        ]
    
    def calculate_score(self, answers, question_times):
        """Calculate detailed score analysis"""
        score = 0
        correct_count = 0
        attempted_count = 0
        
        for q_id, answer_data in answers.items():
            if answer_data['answered']:
                attempted_count += 1
                question = next((q for q in self.questions if q['id'] == q_id), None)
                if question and answer_data['answer'] == question['correct_index']:
                    score += question['marks']
                    correct_count += 1
        
        accuracy = (correct_count / attempted_count * 100) if attempted_count > 0 else 0
        total_time = sum(question_times.values()) if question_times else 0
        
        return {
            'score': score,
            'total_marks': len(self.questions),
            'correct_count': correct_count,
            'attempted_count': attempted_count,
            'accuracy': accuracy,
            'total_time': total_time,
            'avg_time': total_time / attempted_count if attempted_count > 0 else 0
        }

def initialize_session_state():
    """Initialize all session state variables"""
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_finished' not in st.session_state:
        st.session_state.quiz_finished = False
    if 'practice_mode' not in st.session_state:
        st.session_state.practice_mode = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'question_times' not in st.session_state:
        st.session_state.question_times = {}
    if 'marked_questions' not in st.session_state:
        st.session_state.marked_questions = set()
    if 'show_answers' not in st.session_state:
        st.session_state.show_answers = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = None
    if 'time_remaining' not in st.session_state:
        st.session_state.time_remaining = 1800
    if 'total_time' not in st.session_state:
        st.session_state.total_time = 1800
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()
    if 'pdf_extractor' not in st.session_state:
        st.session_state.pdf_extractor = PDFQuizExtractor()
    if 'session_history' not in st.session_state:
        st.session_state.session_history = []

def display_header():
    """Display main header"""
    st.markdown('<div class="main-header">🧠 QuizMaster Pro</div>', unsafe_allow_html=True)

def display_timer():
    """Display real-time timer"""
    if st.session_state.quiz_started and not st.session_state.quiz_finished:
        if not st.session_state.practice_mode:
            elapsed = time.time() - st.session_state.start_time
            remaining = st.session_state.total_time - elapsed
            
            if remaining <= 0:
                st.session_state.quiz_finished = True
                remaining = 0
            
            st.session_state.time_remaining = max(0, int(remaining))
            
            minutes = st.session_state.time_remaining // 60
            seconds = st.session_state.time_remaining % 60
            
            timer_color = "#ff4444" if st.session_state.time_remaining < 300 else "#2E86AB"
            st.markdown(f"""
            <div class="timer-box" style="background: linear-gradient(45deg, {timer_color}, #A23B72);">
                ⏰ Time Remaining: {minutes:02d}:{seconds:02d}
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.time_remaining <= 0:
                st.session_state.quiz_finished = True
                st.rerun()

def display_question_navigation():
    """Display question navigation panel"""
    st.sidebar.markdown("### 🧭 Navigation")
    
    # Navigation buttons
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if st.button("⏮️", use_container_width=True, 
                    disabled=st.session_state.current_question == 0,
                    help="Previous Question"):
            save_question_time()
            st.session_state.current_question -= 1
            st.session_state.question_start_time = time.time()
            st.rerun()
    
    with col2:
        st.markdown(f"**{st.session_state.current_question + 1}/{len(st.session_state.quiz_manager.questions)}**")
    
    with col3:
        if st.button("⏭️", use_container_width=True,
                    disabled=st.session_state.current_question == len(st.session_state.quiz_manager.questions) - 1,
                    help="Next Question"):
            save_question_time()
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.rerun()
    
    # Mark question button
    current_q_id = st.session_state.quiz_manager.questions[st.session_state.current_question]['id']
    is_marked = current_q_id in st.session_state.marked_questions
    
    mark_text = "✅ Unmark" if is_marked else "📍 Mark"
    if st.sidebar.button(mark_text, use_container_width=True):
        if is_marked:
            st.session_state.marked_questions.remove(current_q_id)
        else:
            st.session_state.marked_questions.add(current_q_id)
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔢 Question Palette")
    
    # Question grid
    questions = st.session_state.quiz_manager.questions
    cols_per_row = 5
    
    for i in range(0, len(questions), cols_per_row):
        cols = st.sidebar.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(questions):
                q_index = i + j
                q_id = questions[q_index]['id']
                
                # Determine button style
                answered = q_id in st.session_state.answers and st.session_state.answers[q_id]['answered']
                marked = q_id in st.session_state.marked_questions
                current = q_index == st.session_state.current_question
                
                button_type = "primary" if current else "secondary"
                label = f"{q_index + 1}"
                
                if marked:
                    label = f"📍{q_index + 1}"
                
                if col.button(label, key=f"nav_{q_index}", use_container_width=True, type=button_type):
                    save_question_time()
                    st.session_state.current_question = q_index
                    st.session_state.question_start_time = time.time()
                    st.rerun()

def save_question_time():
    """Save time taken for current question"""
    if (st.session_state.question_start_time and 
        st.session_state.quiz_started and 
        not st.session_state.quiz_finished):
        
        current_q_id = st.session_state.quiz_manager.questions[st.session_state.current_question]['id']
        time_taken = time.time() - st.session_state.question_start_time
        st.session_state.question_times[current_q_id] = time_taken

def display_current_question():
    """Display current question with options"""
    questions = st.session_state.quiz_manager.questions
    current_q = questions[st.session_state.current_question]
    current_q_id = current_q['id']
    
    # Get current answer
    current_answer = st.session_state.answers.get(current_q_id, {'answered': False, 'answer': None})
    
    st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
    
    # Question header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### ❓ Question {st.session_state.current_question + 1}")
    with col2:
        st.markdown(f"**Marks: {current_q['marks']}**")
    
    # Question text
    st.markdown(f"**{current_q['question']}**")
    
    # Display options
    options = current_q['options']
    selected_index = current_answer['answer'] if current_answer['answered'] else None
    
    for i, option in enumerate(options):
        option_letter = chr(65 + i)  # A, B, C, D
        
        # Determine CSS class
        option_class = "option-box"
        if st.session_state.quiz_finished or st.session_state.show_answers:
            if i == current_q['correct_index']:
                option_class += " option-correct"
            elif i == selected_index and i != current_q['correct_index']:
                option_class += " option-incorrect"
        elif i == selected_index:
            option_class += " option-selected"
        
        # Create option box
        if st.session_state.quiz_finished:
            st.markdown(f'''
            <div class="{option_class}">
                <strong>{option_letter})</strong> {option}
            </div>
            ''', unsafe_allow_html=True)
        else:
            if st.button(f"{option_letter}) {option}", key=f"opt_{current_q_id}_{i}", 
                        use_container_width=True, 
                        type="primary" if i == selected_index else "secondary"):
                st.session_state.answers[current_q_id] = {
                    'answered': True,
                    'answer': i
                }
                st.rerun()
    
    # Show answer button for practice mode
    if st.session_state.practice_mode and not st.session_state.quiz_finished:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Show Answer", use_container_width=True):
                st.session_state.show_answers = True
                st.rerun()
        with col2:
            if st.session_state.show_answers:
                correct_option = current_q['options'][current_q['correct_index']]
                st.info(f"**Correct Answer: {current_q['correct_answer']}) {correct_option}**")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_results():
    """Display comprehensive results"""
    report = st.session_state.quiz_manager.calculate_score(
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
        'total_time': int(report['total_time']),
        'correct_count': report['correct_count'],
        'attempted_count': report['attempted_count']
    }
    st.session_state.session_history.append(history_entry)
    
    st.markdown('<div class="main-header">📊 Quiz Results</div>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Score", f"{report['score']}/{report['total_marks']}")
    with col2:
        st.metric("📈 Accuracy", f"{report['accuracy']:.1f}%")
    with col3:
        st.metric("✅ Correct", f"{report['correct_count']}/{report['attempted_count']}")
    with col4:
        st.metric("⏱️ Time", f"{int(report['total_time'])}s")
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Accuracy gauge
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=report['accuracy'],
            title={'text': "Accuracy"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2E86AB"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ]
            }
        ))
        fig1.update_layout(height=300)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Score distribution
        labels = ['Correct', 'Incorrect', 'Unattempted']
        values = [
            report['correct_count'],
            report['attempted_count'] - report['correct_count'],
            len(st.session_state.quiz_manager.questions) - report['attempted_count']
        ]
        fig2 = px.pie(values=values, names=labels, title="Question Distribution")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed review
    st.markdown("### 📋 Question-wise Review")
    review_data = []
    for question in st.session_state.quiz_manager.questions:
        q_id = question['id']
        answer_data = st.session_state.answers.get(q_id, {'answered': False, 'answer': None})
        time_taken = st.session_state.question_times.get(q_id, 0)
        
        status = "Not Attempted"
        if answer_data['answered']:
            if answer_data['answer'] == question['correct_index']:
                status = "Correct"
            else:
                status = "Incorrect"
        
        review_data.append({
            "Q.No": question['id'],
            "Question": question['question'][:50] + "..." if len(question['question']) > 50 else question['question'],
            "Your Answer": chr(65 + answer_data['answer']) if answer_data['answered'] else "Not Attempted",
            "Correct Answer": question['correct_answer'],
            "Status": status,
            "Time (s)": f"{int(time_taken)}s",
            "Marks": "1" if status == "Correct" else "0"
        })
    
    review_df = pd.DataFrame(review_data)
    st.dataframe(review_df, use_container_width=True)

def display_history():
    """Display session history"""
    if st.session_state.session_history:
        st.markdown("### 📜 Session History")
        
        history_df = pd.DataFrame(st.session_state.session_history)
        
        # Display history table
        st.dataframe(history_df, use_container_width=True)
        
        # Performance trend
        if len(history_df) > 1:
            fig = px.line(history_df, x='timestamp', y='accuracy', 
                         title="Accuracy Trend Over Sessions", markers=True)
            st.plotly_chart(fig, use_container_width=True)

def main():
    initialize_session_state()
    display_header()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        if not st.session_state.quiz_started:
            # Mode selection
            mode = st.radio("Select Mode:", ["Exam Mode", "Practice Mode"])
            st.session_state.practice_mode = (mode == "Practice Mode")
            
            # Time settings for exam mode
            if not st.session_state.practice_mode:
                st.session_state.total_time = st.slider(
                    "Exam Duration (minutes):",
                    min_value=5,
                    max_value=180,
                    value=30
                ) * 60
            
            # PDF upload
            st.markdown("### 📁 Upload Questions")
            pdf_file = st.file_uploader("Upload PDF with MCQs", type=['pdf'], 
                                       help="Upload PDF with questions in format: Question? A) Option1 B) Option2 C) Option3 D) Option4 Answer: A")
            
            if pdf_file is not None:
                if st.button("Extract Questions from PDF", use_container_width=True):
                    with st.spinner("Extracting questions from PDF..."):
                        questions = st.session_state.pdf_extractor.extract_questions_from_pdf(pdf_file)
                        if questions:
                            st.session_state.quiz_manager.questions = questions
                            st.success(f"✅ Extracted {len(questions)} questions!")
                        else:
                            st.error("❌ No questions found. Using sample questions.")
                            st.session_state.quiz_manager.load_sample_questions()
            else:
                if st.button("Use Sample Questions", use_container_width=True):
                    st.session_state.quiz_manager.load_sample_questions()
                    st.success("✅ Sample questions loaded!")
            
            # Start quiz button
            if st.session_state.quiz_manager.questions:
                start_text = "🚀 Start Practice" if st.session_state.practice_mode else "🚀 Start Exam"
                if st.button(start_text, type="primary", use_container_width=True):
                    st.session_state.quiz_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.question_start_time = time.time()
                    st.rerun()
    
    # Main content area
    if not st.session_state.quiz_manager.questions:
        # Welcome screen
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 15px; color: white; margin: 2rem 0;'>
            <h1>Welcome to QuizMaster Pro! 🧠</h1>
            <p style='font-size: 1.3rem;'>Professional Quiz Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Features")
            st.markdown("""
            - **PDF Quiz Extraction** - Auto-generate from PDFs
            - **Dual Modes** - Exam & Practice
            - **Smart Timer** - Real-time countdown
            - **Question Navigation** - Easy navigation
            - **Performance Analytics** - Detailed insights
            - **Session History** - Track progress
            """)
        
        with col2:
            st.markdown("### 📝 How to Use")
            st.markdown("""
            1. **Upload PDF** with MCQs in standard format
            2. **Select Mode** - Exam (timed) or Practice
            3. **Configure** time settings
            4. **Start Quiz** and answer questions
            5. **Review Results** with analytics
            """)
    
    elif st.session_state.quiz_started and not st.session_state.quiz_finished:
        # Quiz in progress
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
                st.session_state.quiz_finished = True
                st.rerun()
    
    elif st.session_state.quiz_finished:
        # Results screen
        display_results()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 New Quiz", use_container_width=True):
                # Reset quiz state
                keys_to_keep = ['quiz_manager', 'pdf_extractor', 'session_history']
                new_state = {k: v for k, v in st.session_state.items() if k in keys_to_keep}
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                for k, v in new_state.items():
                    st.session_state[k] = v
                st.rerun()
        
        with col2:
            if st.button("📊 View History", use_container_width=True):
                display_history()
        
        with col3:
            if st.button("📝 Back to Start", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
