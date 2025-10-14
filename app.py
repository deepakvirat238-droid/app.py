import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import pdfplumber
import re
import json

# Page configuration
st.set_page_config(
    page_title="PDF Quiz Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .question-box {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .option-box {
        background: #f8f9fa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 2px solid #e9ecef;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .option-box:hover {
        background: #e9ecef;
        border-color: #1f77b4;
    }
    .option-selected {
        background: #1f77b4 !important;
        color: white !important;
        border-color: #1f77b4 !important;
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
        background: #1f77b4;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .nav-btn {
        width: 40px;
        height: 40px;
        margin: 2px;
        border: 2px solid #1f77b4;
        border-radius: 5px;
        background: white;
        color: #1f77b4;
        font-weight: bold;
    }
    .nav-btn:hover {
        background: #1f77b4;
        color: white;
    }
    .nav-btn-active {
        background: #1f77b4 !important;
        color: white !important;
    }
    .nav-btn-answered {
        background: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    .nav-btn-marked {
        background: #ffc107 !important;
        color: black !important;
        border-color: #ffc107 !important;
    }
</style>
""", unsafe_allow_html=True)

class PDFQuizExtractor:
    def __init__(self):
        pass
    
    def extract_questions_from_pdf(self, pdf_file):
        """Extract questions from PDF"""
        questions = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            
            # Simple question extraction logic
            lines = full_text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line and ('?' in line or line.endswith('?')):
                    # Found a question
                    question_text = line
                    options = []
                    answer = None
                    
                    # Look for options in next lines
                    for j in range(i+1, min(i+10, len(lines))):
                        opt_line = lines[j].strip()
                        if opt_line.startswith(('A)', 'B)', 'C)', 'D)', 'a)', 'b)', 'c)', 'd)')):
                            options.append(opt_line)
                        elif 'answer' in opt_line.lower():
                            # Extract answer
                            if 'A' in opt_line.upper() or 'a)' in opt_line.lower():
                                answer = 'A'
                            elif 'B' in opt_line.upper() or 'b)' in opt_line.lower():
                                answer = 'B'
                            elif 'C' in opt_line.upper() or 'c)' in opt_line.lower():
                                answer = 'C'
                            elif 'D' in opt_line.upper() or 'd)' in opt_line.lower():
                                answer = 'D'
                    
                    if len(options) >= 2 and answer:
                        # Clean options
                        clean_options = []
                        for opt in options[:4]:  # Take first 4 options
                            clean_opt = re.sub(r'^[A-Da-d][\)\.]\s*', '', opt)
                            clean_options.append(clean_opt)
                        
                        # Add question
                        questions.append({
                            'id': len(questions) + 1,
                            'question': question_text,
                            'options': clean_options,
                            'correct_answer': answer.upper(),
                            'correct_index': ord(answer.upper()) - ord('A'),
                            'type': 'mcq',
                            'marks': 1
                        })
                
                i += 1
            
            return questions
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return []

class QuizManager:
    def __init__(self):
        self.questions = []
        self.session_history = []
    
    def load_sample_questions(self):
        """Load sample questions"""
        self.questions = [
            {
                'id': 1,
                'question': "What is the first prime number?",
                'options': ["1", "2", "3", "4"],
                'correct_answer': "B",
                'correct_index': 1,
                'type': 'mcq',
                'marks': 1
            },
            {
                'id': 2,
                'question': "Which language is used for web development?",
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

def initialize_session_state():
    """Initialize session state"""
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_finished' not in st.session_state:
        st.session_state.quiz_finished = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'marked_questions' not in st.session_state:
        st.session_state.marked_questions = set()
    if 'show_answers' not in st.session_state:
        st.session_state.show_answers = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
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

def main():
    initialize_session_state()
    
    st.markdown('<div class="main-header">📚 PDF Quiz Pro</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        if not st.session_state.quiz_started:
            # Time settings
            st.session_state.total_time = st.slider(
                "Exam Duration (minutes):",
                min_value=5,
                max_value=180,
                value=30
            ) * 60
            
            # PDF upload
            st.markdown("### 📁 Upload Questions")
            pdf_file = st.file_uploader("Upload PDF with MCQs", type=['pdf'])
            
            if pdf_file is not None:
                if st.button("Extract Questions from PDF"):
                    with st.spinner("Extracting questions from PDF..."):
                        questions = st.session_state.pdf_extractor.extract_questions_from_pdf(pdf_file)
                        if questions:
                            st.session_state.quiz_manager.questions = questions
                            st.success(f"✅ Extracted {len(questions)} questions!")
                        else:
                            st.error("❌ No questions found. Using sample questions.")
                            st.session_state.quiz_manager.load_sample_questions()
            else:
                if st.button("Use Sample Questions"):
                    st.session_state.quiz_manager.load_sample_questions()
                    st.success("✅ Sample questions loaded!")
            
            # Start button
            if st.session_state.quiz_manager.questions:
                if st.button("🚀 Start Exam", type="primary", use_container_width=True):
                    st.session_state.quiz_started = True
                    st.session_state.start_time = time.time()
                    st.rerun()

    # Main content
    if not st.session_state.quiz_manager.questions:
        st.info("👆 Please upload a PDF or use sample questions to start the quiz.")
        
    elif st.session_state.quiz_started and not st.session_state.quiz_finished:
        # Timer
        if st.session_state.quiz_started:
            elapsed = time.time() - st.session_state.start_time
            remaining = st.session_state.total_time - elapsed
            
            if remaining <= 0:
                st.session_state.quiz_finished = True
                remaining = 0
            
            st.session_state.time_remaining = max(0, int(remaining))
            
            minutes = st.session_state.time_remaining // 60
            seconds = st.session_state.time_remaining % 60
            
            st.markdown(f'''
            <div class="timer-box">
                ⏰ Time Remaining: {minutes:02d}:{seconds:02d}
            </div>
            ''', unsafe_allow_html=True)
            
            if st.session_state.time_remaining <= 0:
                st.session_state.quiz_finished = True
                st.rerun()
        
        # Question navigation
        st.sidebar.markdown("### 🧭 Navigation")
        
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            if st.button("⏮️", use_container_width=True, disabled=st.session_state.current_question == 0):
                st.session_state.current_question -= 1
                st.rerun()
        with col2:
            st.markdown(f"**{st.session_state.current_question + 1}/{len(st.session_state.quiz_manager.questions)}**")
        with col3:
            if st.button("⏭️", use_container_width=True, 
                        disabled=st.session_state.current_question == len(st.session_state.quiz_manager.questions) - 1):
                st.session_state.current_question += 1
                st.rerun()
        
        # Question palette
        st.sidebar.markdown("### 🔢 Questions")
        questions = st.session_state.quiz_manager.questions
        cols = st.sidebar.columns(5)
        
        for i in range(len(questions)):
            col_idx = i % 5
            with cols[col_idx]:
                q_id = questions[i]['id']
                answered = q_id in st.session_state.answers
                marked = q_id in st.session_state.marked_questions
                current = i == st.session_state.current_question
                
                btn_type = "primary" if current else "secondary"
                label = str(i + 1)
                
                if marked:
                    label = f"📍{i+1}"
                
                if cols[col_idx].button(label, key=f"nav_{i}", use_container_width=True, type=btn_type):
                    st.session_state.current_question = i
                    st.rerun()
        
        # Submit button
        st.sidebar.markdown("---")
        if st.sidebar.button("✅ Submit Exam", type="primary", use_container_width=True):
            st.session_state.quiz_finished = True
            st.rerun()
        
        # Current question
        current_q = st.session_state.quiz_manager.questions[st.session_state.current_question]
        current_q_id = current_q['id']
        
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"### ❓ Question {st.session_state.current_question + 1}")
        st.markdown(f"**{current_q['question']}**")
        
        # Options
        current_answer = st.session_state.answers.get(current_q_id, None)
        options = current_q['options']
        
        for i, option in enumerate(options):
            option_letter = chr(65 + i)
            option_class = "option-box"
            
            if st.session_state.quiz_finished:
                if i == current_q['correct_index']:
                    option_class += " option-correct"
                elif current_answer == i:
                    option_class += " option-incorrect"
            elif current_answer == i:
                option_class += " option-selected"
            
            if st.button(f"{option_letter}) {option}", key=f"opt_{current_q_id}_{i}", 
                        use_container_width=True):
                st.session_state.answers[current_q_id] = i
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mark question button
        is_marked = current_q_id in st.session_state.marked_questions
        mark_text = "✅ Unmark Question" if is_marked else "📍 Mark Question"
        if st.button(mark_text, use_container_width=True):
            if is_marked:
                st.session_state.marked_questions.remove(current_q_id)
            else:
                st.session_state.marked_questions.add(current_q_id)
            st.rerun()
    
    elif st.session_state.quiz_finished:
        # Calculate results
        score = 0
        for q_id, answer in st.session_state.answers.items():
            question = next((q for q in st.session_state.quiz_manager.questions if q['id'] == q_id), None)
            if question and answer == question['correct_index']:
                score += 1
        
        # Save to history
        history_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'score': score,
            'total': len(st.session_state.quiz_manager.questions),
            'percentage': (score / len(st.session_state.quiz_manager.questions)) * 100
        }
        st.session_state.session_history.append(history_entry)
        
        # Display results
        st.markdown('<div class="main-header">📊 Quiz Results</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{score}/{len(st.session_state.quiz_manager.questions)}")
        with col2:
            st.metric("Percentage", f"{(score/len(st.session_state.quiz_manager.questions))*100:.1f}%")
        with col3:
            st.metric("Time Taken", f"{int((st.session_state.total_time - st.session_state.time_remaining)/60)}m")
        
        # Question review
        st.markdown("### 📋 Question Review")
        for i, question in enumerate(st.session_state.quiz_manager.questions):
            q_id = question['id']
            user_answer = st.session_state.answers.get(q_id, None)
            is_correct = user_answer == question['correct_index']
            
            status = "✅ Correct" if is_correct else "❌ Incorrect" if user_answer is not None else "⏭️ Not Attempted"
            
            with st.expander(f"Question {i+1}: {status}"):
                st.write(f"**{question['question']}**")
                for j, option in enumerate(question['options']):
                    option_letter = chr(65 + j)
                    if j == question['correct_index']:
                        st.success(f"{option_letter}) {option} ✓")
                    elif j == user_answer:
                        st.error(f"{option_letter}) {option} ✗")
                    else:
                        st.write(f"{option_letter}) {option}")
        
        # Session History
        st.markdown("### 📜 Session History")
        if st.session_state.session_history:
            history_df = pd.DataFrame(st.session_state.session_history)
            st.dataframe(history_df, use_container_width=True)
            
            # Chart
            fig = px.line(history_df, x='timestamp', y='percentage', 
                         title="Performance Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No history available yet.")
        
        # Restart button
        if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['quiz_manager', 'pdf_extractor', 'session_history']:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
