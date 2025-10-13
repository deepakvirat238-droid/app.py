import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import re
import time
import io
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os
import json

# Page configuration
st.set_page_config(
    page_title="TestBook Pro - PDF Quiz Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced TestBook-like CSS
st.markdown("""
<style>
    /* TestBook Professional Theme */
    .stApp {
        background: #f8f9fa;
    }
    
    /* Header Styles */
    .testbook-header {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 1rem 2rem;
        border-radius: 0 0 15px 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .testbook-logo {
        font-size: 2.5rem;
        font-weight: 800;
        color: #f39c12;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Control Panel */
    .control-panel {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #3498db;
    }
    
    /* Timer Styles */
    .timer-danger {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        font-family: 'Courier New', monospace;
        animation: pulse 1s infinite;
    }
    
    .timer-warning {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        font-family: 'Courier New', monospace;
    }
    
    .timer-normal {
        background: linear-gradient(135deg, #27ae60, #2ecc71);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        font-family: 'Courier New', monospace;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    /* Question Palette */
    .question-palette {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 0.5rem;
        margin: 1rem 0;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .q-palette-btn {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        border: 2px solid #ddd;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .q-palette-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .q-palette-btn.answered {
        background: #27ae60;
        color: white;
        border-color: #27ae60;
    }
    
    .q-palette-btn.current {
        background: #3498db;
        color: white;
        border-color: #3498db;
        transform: scale(1.1);
    }
    
    .q-palette-btn.marked {
        background: #f39c12;
        color: white;
        border-color: #f39c12;
    }
    
    .q-palette-btn.not-visited {
        background: #ecf0f1;
        color: #7f8c8d;
        border-color: #bdc3c7;
    }
    
    /* Question Box */
    .question-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #3498db;
    }
    
    .option-btn {
        width: 100%;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: left;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        background: white;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .option-btn:hover {
        border-color: #3498db;
        background: #f8f9fa;
        transform: translateX(5px);
    }
    
    .option-btn.selected {
        background: #3498db;
        color: white;
        border-color: #2980b9;
    }
    
    .option-btn.correct {
        background: #27ae60;
        color: white;
        border-color: #219a52;
    }
    
    .option-btn.incorrect {
        background: #e74c3c;
        color: white;
        border-color: #c0392b;
    }
    
    /* Navigation Buttons */
    .nav-btn {
        padding: 0.8rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0 0.5rem;
    }
    
    .nav-btn-primary {
        background: #3498db;
        color: white;
    }
    
    .nav-btn-primary:hover {
        background: #2980b9;
        transform: translateY(-2px);
    }
    
    .nav-btn-secondary {
        background: #95a5a6;
        color: white;
    }
    
    .nav-btn-secondary:hover {
        background: #7f8c8d;
    }
    
    /* Results Card */
    .results-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* Sidebar */
    .sidebar-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* History Styles */
    .history-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    
    .history-good {
        border-left-color: #27ae60;
    }
    
    .history-average {
        border-left-color: #f39c12;
    }
    
    .history-poor {
        border-left-color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

class TestBookQuizApp:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        default_states = {
            'questions': [],
            'current_question': 0,
            'user_answers': {},
            'quiz_started': False,
            'quiz_completed': False,
            'quiz_mode': 'practice',  # 'practice' or 'exam'
            'exam_duration': 1800,  # 30 minutes in seconds
            'start_time': None,
            'time_left': 1800,
            'marked_questions': set(),
            'show_results': False,
            'uploaded_file_name': None,
            'sound_enabled': True,
            'auto_submit': True,
            'full_screen': False,
            'question_times': {},
            'quiz_analysis': {},
            'result_history': [],
            'current_quiz_id': None,
            'show_history': False,
            'detailed_analysis': False
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF with OCR support"""
        text = ""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                    else:
                        # OCR for scanned PDFs
                        try:
                            image = page.to_image()
                            img_bytes = io.BytesIO()
                            image.save(img_bytes, format='PNG')
                            img_bytes.seek(0)
                            ocr_text = pytesseract.image_to_string(Image.open(img_bytes))
                            text += ocr_text + "\n"
                        except:
                            continue
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
        
        return text
    
    def parse_questions_from_text(self, text):
        """Parse questions from extracted text"""
        questions = []
        
        # Split by question patterns
        question_patterns = [
            r'(?i)Q\d+\.',
            r'(?i)Question\s*\d+',
            r'\n\d+\.'
        ]
        
        for pattern in question_patterns:
            blocks = re.split(pattern, text)
            if len(blocks) > 1:
                break
        
        for i, block in enumerate(blocks[1:], 1):
            try:
                # Extract question text
                question_match = re.search(r'^(.*?)(?=A\)|B\)|C\)|D\)|E\)|Answer:|$)', block, re.DOTALL)
                if not question_match:
                    continue
                
                question_text = question_match.group(1).strip()
                
                # Extract options
                options = {}
                option_pattern = r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|\s*Answer:|$)'
                option_matches = re.findall(option_pattern, block)
                
                for opt_letter, opt_text in option_matches:
                    options[opt_letter] = opt_text.strip()
                
                # Create default options if none found
                if not options:
                    options = {
                        'A': 'Option A',
                        'B': 'Option B',
                        'C': 'Option C',
                        'D': 'Option D'
                    }
                
                # Extract correct answer
                answer_match = re.search(r'(?i)Answer:\s*([A-E])', block)
                correct_answer = answer_match.group(1) if answer_match else random.choice(list(options.keys()))
                
                questions.append({
                    'id': i,
                    'question': question_text,
                    'options': options,
                    'correct_answer': correct_answer,
                    'user_answer': None,
                    'time_spent': 0,
                    'difficulty': random.choice(['Easy', 'Medium', 'Hard']),
                    'is_marked': False
                })
                
            except Exception as e:
                continue
        
        return questions
    
    def save_quiz_result(self):
        """Save current quiz result to history"""
        if not st.session_state.questions:
            return
        
        quiz_result = {
            'quiz_id': f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': st.session_state.quiz_mode,
            'total_questions': len(st.session_state.questions),
            'correct_answers': st.session_state.quiz_analysis['correct_answers'],
            'incorrect_answers': st.session_state.quiz_analysis['incorrect_answers'],
            'unanswered': st.session_state.quiz_analysis['unanswered'],
            'accuracy': st.session_state.quiz_analysis['accuracy'],
            'time_taken': st.session_state.quiz_analysis['time_taken'],
            'score': st.session_state.quiz_analysis['correct_answers'],
            'percentage': st.session_state.quiz_analysis['accuracy'],
            'user_answers': st.session_state.user_answers.copy(),
            'questions': [
                {
                    'id': q['id'],
                    'question': q['question'],
                    'correct_answer': q['correct_answer'],
                    'user_answer': st.session_state.user_answers.get(q['id']),
                    'is_correct': st.session_state.user_answers.get(q['id']) == q['correct_answer'],
                    'options': q['options'],
                    'difficulty': q['difficulty']
                }
                for q in st.session_state.questions
            ]
        }
        
        st.session_state.result_history.append(quiz_result)
        
        # Keep only last 50 results to prevent memory issues
        if len(st.session_state.result_history) > 50:
            st.session_state.result_history = st.session_state.result_history[-50:]
    
    def render_header(self):
        """Render TestBook-like header"""
        st.markdown("""
        <div class="testbook-header">
            <div class="testbook-logo">📚 TestBook Pro</div>
            <div style="text-align: center; font-size: 1.2rem; opacity: 0.9;">
                AI-Powered PDF to Quiz Platform
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_control_panel(self):
        """Render control panel with timer and navigation"""
        if not st.session_state.quiz_started:
            return
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            mode_text = "🎯 Exam Mode" if st.session_state.quiz_mode == 'exam' else "💡 Practice Mode"
            st.markdown(f"<div style='font-size: 1.3rem; font-weight: bold;'>{mode_text}</div>", unsafe_allow_html=True)
        
        with col2:
            answered = len(st.session_state.user_answers)
            total = len(st.session_state.questions)
            st.metric("Answered", f"{answered}/{total}")
        
        with col3:
            marked = len(st.session_state.marked_questions)
            st.metric("Marked", marked)
        
        with col4:
            if st.session_state.quiz_mode == 'exam':
                self.render_exam_timer()
            else:
                elapsed = st.session_state.exam_duration - st.session_state.time_left
                minutes = elapsed // 60
                seconds = elapsed % 60
                st.metric("Time", f"{minutes:02d}:{seconds:02d}")
    
    def render_exam_timer(self):
        """Render exam timer with color coding"""
        time_left = st.session_state.time_left
        
        if time_left <= 300:  # 5 minutes
            timer_class = "timer-danger"
        elif time_left <= 600:  # 10 minutes
            timer_class = "timer-warning"
        else:
            timer_class = "timer-normal"
        
        minutes = time_left // 60
        seconds = time_left % 60
        
        st.markdown(f"""
        <div class="{timer_class}">
            {minutes:02d}:{seconds:02d}
        </div>
        """, unsafe_allow_html=True)
    
    def render_question_palette(self):
        """Render question navigation palette"""
        if not st.session_state.questions:
            return
        
        st.markdown("### 📋 Question Palette")
        
        # Create palette grid
        palette_html = "<div class='question-palette'>"
        
        for i in range(len(st.session_state.questions)):
            question = st.session_state.questions[i]
            btn_class = "q-palette-btn"
            
            if i == st.session_state.current_question:
                btn_class += " current"
            elif question['id'] in st.session_state.user_answers:
                btn_class += " answered"
            elif i in st.session_state.marked_questions:
                btn_class += " marked"
            else:
                btn_class += " not-visited"
            
            palette_html += f"""
            <div class='{btn_class}' onclick='selectQuestion({i})'>
                {i + 1}
            </div>
            """
        
        palette_html += "</div>"
        st.markdown(palette_html, unsafe_allow_html=True)
    
    def render_current_question(self):
        """Render current question with options"""
        if not st.session_state.questions:
            return
        
        question = st.session_state.questions[st.session_state.current_question]
        
        st.markdown(f"""
        <div class="question-box">
            <div style="font-size: 1.1rem; color: #2c3e50; margin-bottom: 1rem;">
                Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}
            </div>
            <div style="font-size: 1.3rem; font-weight: 600; line-height: 1.6; color: #34495e;">
                {question['question']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render options
        user_answer = st.session_state.user_answers.get(question['id'])
        
        for opt_letter, opt_text in question['options'].items():
            btn_class = "option-btn"
            if user_answer == opt_letter:
                btn_class += " selected"
            
            if st.button(
                f"{opt_letter}) {opt_text}",
                key=f"opt_{question['id']}_{opt_letter}",
                use_container_width=True
            ):
                st.session_state.user_answers[question['id']] = opt_letter
                st.rerun()
        
        # Mark for review button
        col1, col2 = st.columns([3, 1])
        with col2:
            is_marked = st.session_state.current_question in st.session_state.marked_questions
            mark_text = "✅ Unmark" if is_marked else "📌 Mark for Review"
            if st.button(mark_text, use_container_width=True):
                if is_marked:
                    st.session_state.marked_questions.remove(st.session_state.current_question)
                else:
                    st.session_state.marked_questions.add(st.session_state.current_question)
                st.rerun()
    
    def render_navigation(self):
        """Render question navigation buttons"""
        if not st.session_state.questions:
            return
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("⏮️ First", use_container_width=True, 
                        disabled=st.session_state.current_question == 0):
                st.session_state.current_question = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", use_container_width=True,
                        disabled=st.session_state.current_question == 0):
                st.session_state.current_question -= 1
                st.rerun()
        
        with col3:
            if st.button("Next ▶️", use_container_width=True,
                        disabled=st.session_state.current_question == len(st.session_state.questions) - 1):
                st.session_state.current_question += 1
                st.rerun()
        
        with col4:
            if st.button("Last ⏭️", use_container_width=True,
                        disabled=st.session_state.current_question == len(st.session_state.questions) - 1):
                st.session_state.current_question = len(st.session_state.questions) - 1
                st.rerun()
        
        # Submit button
        st.markdown("---")
        if st.button("🎯 Submit Answers", type="primary", use_container_width=True):
            self.calculate_results()
            self.save_quiz_result()  # Save to history
            st.session_state.quiz_completed = True
            st.session_state.show_results = True
            st.rerun()
    
    def calculate_results(self):
        """Calculate quiz results"""
        correct = 0
        total = len(st.session_state.questions)
        
        for question in st.session_state.questions:
            user_answer = st.session_state.user_answers.get(question['id'])
            if user_answer == question['correct_answer']:
                correct += 1
        
        accuracy = (correct / total) * 100 if total > 0 else 0
        time_taken = time.time() - st.session_state.start_time
        
        st.session_state.quiz_analysis = {
            'total_questions': total,
            'correct_answers': correct,
            'incorrect_answers': total - correct,
            'accuracy': accuracy,
            'time_taken': int(time_taken),
            'unanswered': total - len(st.session_state.user_answers)
        }
    
    def render_results(self):
        """Render quiz results"""
        analysis = st.session_state.quiz_analysis
        
        st.markdown(f"""
        <div class="results-card">
            <h1>🏆 Quiz Completed!</h1>
            <div style="font-size: 3rem; font-weight: bold; margin: 1rem 0;">
                {analysis['correct_answers']}/{analysis['total_questions']}
            </div>
            <div style="font-size: 2rem; margin-bottom: 1rem;">
                {analysis['accuracy']:.1f}% Accuracy
            </div>
            <div style="font-size: 1.2rem;">
                Time: {analysis['time_taken']//60:02d}:{analysis['time_taken']%60:02d}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Correct", analysis['correct_answers'])
        with col2:
            st.metric("Incorrect", analysis['incorrect_answers'])
        with col3:
            st.metric("Unanswered", analysis['unanswered'])
        with col4:
            st.metric("Accuracy", f"{analysis['accuracy']:.1f}%")
        
        # Detailed analysis toggle
        st.markdown("---")
        st.subheader("📊 Detailed Analysis")
        
        if st.button("🔍 View Question-wise Analysis"):
            st.session_state.detailed_analysis = True
            st.rerun()
        
        if st.session_state.detailed_analysis:
            self.render_detailed_analysis()
        
        # Action buttons
        col5, col6, col7 = st.columns(3)
        with col5:
            if st.button("🔄 Start New Quiz", use_container_width=True):
                self.initialize_session_state()
                st.rerun()
        with col6:
            if st.button("📚 View History", use_container_width=True):
                st.session_state.show_history = True
                st.rerun()
        with col7:
            if st.button("📥 Export Results", use_container_width=True):
                self.export_results()
    
    def render_detailed_analysis(self):
        """Render detailed question-wise analysis"""
        st.subheader("📝 Question-wise Performance")
        
        for i, question in enumerate(st.session_state.questions):
            user_answer = st.session_state.user_answers.get(question['id'])
            is_correct = user_answer == question['correct_answer']
            
            with st.expander(f"Q{i+1}: {question['question'][:100]}...", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Your Answer:** {user_answer if user_answer else 'Not Attempted'}")
                    st.write(f"**Correct Answer:** {question['correct_answer']}")
                    st.write(f"**Status:** {'✅ Correct' if is_correct else '❌ Incorrect' if user_answer else '⏭️ Not Attempted'}")
                    
                    # Show options with colors
                    for opt_letter, opt_text in question['options'].items():
                        if opt_letter == question['correct_answer']:
                            st.success(f"✅ {opt_letter}) {opt_text}")
                        elif opt_letter == user_answer and not is_correct:
                            st.error(f"❌ {opt_letter}) {opt_text}")
                        else:
                            st.write(f"{opt_letter}) {opt_text}")
                
                with col2:
                    if is_correct:
                        st.success("Correct")
                    elif user_answer:
                        st.error("Incorrect")
                    else:
                        st.warning("Not Attempted")
    
    def render_history(self):
        """Render quiz history"""
        st.title("📚 Quiz History")
        
        if not st.session_state.result_history:
            st.info("No quiz history available. Complete a quiz to see your results here.")
            return
        
        # Overall statistics
        total_quizzes = len(st.session_state.result_history)
        avg_accuracy = sum(result['accuracy'] for result in st.session_state.result_history) / total_quizzes
        best_score = max(result['accuracy'] for result in st.session_state.result_history)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Quizzes", total_quizzes)
        with col2:
            st.metric("Average Accuracy", f"{avg_accuracy:.1f}%")
        with col3:
            st.metric("Best Score", f"{best_score:.1f}%")
        with col4:
            exam_count = sum(1 for result in st.session_state.result_history if result['mode'] == 'exam')
            st.metric("Exams Taken", exam_count)
        
        # Progress chart
        if total_quizzes > 1:
            history_df = pd.DataFrame(st.session_state.result_history)
            history_df['date'] = pd.to_datetime(history_df['timestamp'])
            history_df = history_df.sort_values('date')
            
            fig = px.line(history_df, x='date', y='accuracy', 
                         title='Accuracy Progress Over Time',
                         labels={'accuracy': 'Accuracy (%)', 'date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Individual quiz results
        st.subheader("📋 Quiz Results")
        
        for result in reversed(st.session_state.result_history[-10:]):  # Show last 10 results
            accuracy_class = "history-good" if result['accuracy'] >= 70 else "history-average" if result['accuracy'] >= 50 else "history-poor"
            
            with st.container():
                st.markdown(f"<div class='history-card {accuracy_class}'>", unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{result['date']}**")
                    st.write(f"Mode: {result['mode'].title()}")
                
                with col2:
                    st.write(f"**Score**")
                    st.write(f"{result['correct_answers']}/{result['total_questions']}")
                
                with col3:
                    st.write(f"**Accuracy**")
                    st.write(f"{result['accuracy']:.1f}%")
                
                with col4:
                    st.write(f"**Time**")
                    st.write(f"{result['time_taken']//60:02d}:{result['time_taken']%60:02d}")
                
                with col5:
                    if st.button("View Details", key=f"view_{result['quiz_id']}"):
                        self.render_quiz_details(result)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    def render_quiz_details(self, result):
        """Render detailed view of a specific quiz result"""
        st.subheader(f"📊 Quiz Details - {result['date']}")
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Correct", result['correct_answers'])
        with col2:
            st.metric("Incorrect", result['incorrect_answers'])
        with col3:
            st.metric("Unanswered", result['unanswered'])
        with col4:
            st.metric("Accuracy", f"{result['accuracy']:.1f}%")
        
        # Question details
        st.subheader("📝 Question-wise Analysis")
        
        for i, q in enumerate(result['questions']):
            with st.expander(f"Q{i+1}: {q['question'][:100]}...", expanded=False):
                st.write(f"**Your Answer:** {q['user_answer'] if q['user_answer'] else 'Not Attempted'}")
                st.write(f"**Correct Answer:** {q['correct_answer']}")
                st.write(f"**Status:** {'✅ Correct' if q['is_correct'] else '❌ Incorrect' if q['user_answer'] else '⏭️ Not Attempted'}")
                
                # Show options
                for opt_letter, opt_text in q['options'].items():
                    if opt_letter == q['correct_answer']:
                        st.success(f"✅ {opt_letter}) {opt_text}")
                    elif opt_letter == q['user_answer'] and not q['is_correct']:
                        st.error(f"❌ {opt_letter}) {opt_text}")
                    else:
                        st.write(f"{opt_letter}) {opt_text}")
    
    def export_results(self):
        """Export results as CSV"""
        if not st.session_state.result_history:
            st.warning("No results to export")
            return
        
        # Create DataFrame for export
        export_data = []
        for result in st.session_state.result_history:
            export_data.append({
                'Date': result['date'],
                'Mode': result['mode'],
                'Total Questions': result['total_questions'],
                'Correct Answers': result['correct_answers'],
                'Incorrect Answers': result['incorrect_answers'],
                'Unanswered': result['unanswered'],
                'Accuracy (%)': result['accuracy'],
                'Time Taken (seconds)': result['time_taken']
            })
        
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"testbook_results_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    def update_timer(self):
        """Update exam timer"""
        if (st.session_state.quiz_started and 
            st.session_state.quiz_mode == 'exam' and 
            not st.session_state.quiz_completed):
            
            current_time = time.time()
            elapsed = current_time - st.session_state.start_time
            st.session_state.time_left = max(0, st.session_state.exam_duration - int(elapsed))
            
            # Auto-submit when time expires
            if st.session_state.time_left == 0 and st.session_state.auto_submit:
                self.calculate_results()
                self.save_quiz_result()
                st.session_state.quiz_completed = True
                st.session_state.show_results = True
                st.rerun()
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        with st.sidebar:
            st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
            st.header("🎯 Navigation")
            
            # Navigation options
            nav_options = ["🏠 Dashboard", "📚 History", "⚙️ Settings"]
            selected_nav = st.radio("Go to", nav_options, index=0)
            
            if selected_nav == "📚 History":
                st.session_state.show_history = True
            else:
                st.session_state.show_history = False
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not st.session_state.show_history:
                st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
                st.header("🎯 Quiz Settings")
                
                # Quiz mode selection
                mode = st.radio("Select Mode", ["Practice", "Exam"], index=0)
                st.session_state.quiz_mode = 'practice' if mode == "Practice" else 'exam'
                
                if st.session_state.quiz_mode == 'exam':
                    duration = st.selectbox("Exam Duration", 
                                          [900, 1800, 2700, 3600],  # 15, 30, 45, 60 minutes
                                          format_func=lambda x: f"{x//60} minutes",
                                          index=1)
                    st.session_state.exam_duration = duration
                    st.session_state.time_left = duration
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # File upload
                st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
                st.header("📁 Upload PDF")
                
                uploaded_file = st.file_uploader("Choose PDF file", type="pdf", label_visibility="collapsed")
                
                if uploaded_file and (st.session_state.uploaded_file_name != uploaded_file.name or not st.session_state.questions):
                    with st.spinner("Processing PDF..."):
                        text = self.extract_text_from_pdf(uploaded_file)
                        questions = self.parse_questions_from_text(text)
                        
                        if questions:
                            st.session_state.questions = questions
                            st.session_state.uploaded_file_name = uploaded_file.name
                            st.session_state.quiz_started = True
                            st.session_state.start_time = time.time()
                            st.success(f"✅ Loaded {len(questions)} questions!")
                        else:
                            st.error("❌ No questions found in PDF")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Quick actions
                if st.session_state.questions:
                    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
                    st.header("🚀 Quick Actions")
                    
                    if st.button("Start Practice", use_container_width=True):
                        st.session_state.quiz_mode = 'practice'
                        st.session_state.quiz_started = True
                        st.session_state.quiz_completed = False
                        st.session_state.show_results = False
                        st.session_state.start_time = time.time()
                        st.rerun()
                    
                    if st.button("Start Exam", use_container_width=True, type="primary"):
                        st.session_state.quiz_mode = 'exam'
                        st.session_state.quiz_started = True
                        st.session_state.quiz_completed = False
                        st.session_state.show_results = False
                        st.session_state.start_time = time.time()
                        st.session_state.time_left = st.session_state.exam_duration
                        st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    def main(self):
        """Main application loop"""
        self.render_header()
        self.render_sidebar()
        
        # Update timer
        self.update_timer()
        
        if st.session_state.show_history:
            self.render_history()
            return
        
        if not st.session_state.quiz_started and not st.session_state.show_results:
            # Welcome screen
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("""
                ## 🎯 Welcome to TestBook Pro
                
                **Transform your PDFs into interactive quizzes!**
                
                ### Features:
                - 📄 **PDF to Quiz Conversion** - Upload any PDF with questions
                - ⏰ **Real Exam Mode** - Timed tests with live countdown
                - 💡 **Practice Mode** - Learn at your own pace
                - 📊 **Detailed Analytics** - Performance insights
                - 🎨 **TestBook-like Interface** - Professional exam environment
                - 📚 **Result History** - Track your progress over time
                
                ### How to use:
                1. Upload a PDF file with questions
                2. Choose Practice or Exam mode
                3. Start your quiz session
                4. Get instant results and analytics
                5. View your history in the History section
                """)
            
            with col2:
                st.image("https://via.placeholder.com/300x400/3498db/ffffff?text=TestBook\nPro", use_column_width=True)
            
            return
        
        if st.session_state.show_results:
            self.render_results()
            return
        
        if not st.session_state.questions:
            st.info("📝 Please upload a PDF file to start the quiz")
            return
        
        # Main quiz interface
        self.render_control_panel()
        self.render_question_palette()
        self.render_current_question()
        self.render_navigation()

# Run the application
if __name__ == "__main__":
    app = TestBookQuizApp()
    app.main()
