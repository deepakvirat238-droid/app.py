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
from datetime import datetime
import base64
import os
import json

# ========== NEW HISTORY FEATURE ==========
class ExamHistory:
    def __init__(self):
        self.history_file = "exam_history.json"
    
    def save_session(self, session_data):
        """Save exam session to history"""
        try:
            history = self.load_history()
            session_data['id'] = f"session_{int(time.time())}"
            session_data['timestamp'] = datetime.now().isoformat()
            history.append(session_data)
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            st.error(f"Error saving history: {e}")
    
    def load_history(self):
        """Load exam history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def clear_history(self):
        """Clear all history"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            return True
        except:
            return False

# Initialize history manager
exam_history = ExamHistory()

# Sound functions
def autoplay_audio(sound_type):
    """Play sound based on answer correctness"""
    if not st.session_state.get('sound_enabled', True):
        return
        
    if sound_type == "correct":
        sound_file = """
        <audio autoplay>
        <source src="https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3" type="audio/mpeg">
        </audio>
        """
    else:  # wrong
        sound_file = """
        <audio autoplay>
        <source src="https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3" type="audio/mpeg">
        </audio>
        """
    st.markdown(sound_file, unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF with OCR support for scanned PDFs"""
    text = ""
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Try to extract text directly first
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                else:
                    # If no text found, use OCR for scanned PDFs
                    try:
                        image = page.to_image()
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        ocr_text = pytesseract.image_to_string(Image.open(img_bytes))
                        text += ocr_text + "\n"
                    except:
                        st.warning("Some pages might not have readable text")
                        continue
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
    
    return text

def generate_ai_explanation(question, correct_answer, options):
    """Generate AI explanation for questions"""
    explanations = {
        "grammar": "This question tests your understanding of grammatical rules. The correct answer follows standard grammar conventions.",
        "vocabulary": "This vocabulary question requires understanding word meanings and contextual usage.",
        "comprehension": "This reading comprehension question tests your ability to understand and interpret written text.",
        "logic": "This logical reasoning question requires analytical thinking and deduction skills.",
        "general": "This question evaluates fundamental knowledge in the subject area."
    }
    
    # Simple AI logic to determine question type
    question_lower = question.lower()
    if any(word in question_lower for word in ['synonym', 'antonym', 'word', 'meaning']):
        exp_type = "vocabulary"
    elif any(word in question_lower for word in ['tense', 'grammar', 'sentence', 'verb']):
        exp_type = "grammar"
    elif any(word in question_lower for word in ['passage', 'read', 'comprehension']):
        exp_type = "comprehension"
    elif any(word in question_lower for word in ['logic', 'reason', 'deduce', 'infer']):
        exp_type = "logic"
    else:
        exp_type = "general"
    
    base_explanation = explanations[exp_type]
    detailed_explanation = f"""
{base_explanation}

**Why {correct_answer} is correct:**
- It accurately addresses the question's requirement
- It follows the rules of {exp_type}
- The other options contain common misconceptions

**Learning Tip:** Practice similar questions to strengthen your {exp_type} skills.
"""
    
    return detailed_explanation

def parse_pdf_content(pdf_file):
    questions = []
    text = extract_text_from_pdf(pdf_file)
    
    # More robust question splitting
    question_blocks = re.split(r'(?i)Q\d+\.|\n\d+\.', text)
    
    for i, block in enumerate(question_blocks[1:], 1):
        try:
            # Improved regex for question extraction
            question_match = re.search(r'^(.*?)(?=A\)|B\)|C\)|D\)|E\)|Answer:|$)', block, re.DOTALL)
            if not question_match: 
                continue
            
            question_text = question_match.group(1).strip()
            
            # Extract options with improved regex
            options = {}
            option_matches = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|\s*Answer:|$)', block)
            for opt_letter, opt_text in option_matches:
                options[opt_letter] = opt_text.strip()
            
            # If no options found, create default ones
            if not options:
                options = {
                    'A': 'Option A',
                    'B': 'Option B', 
                    'C': 'Option C',
                    'D': 'Option D'
                }
            
            # Extract answer with improved regex
            answer_match = re.search(r'(?i)Answer:\s*([A-E])', block)
            correct_answer = answer_match.group(1) if answer_match else random.choice(list(options.keys()))
            
            # Add AI explanation
            ai_explanation = generate_ai_explanation(question_text, correct_answer, options)
            
            questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "ai_explanation": ai_explanation,
                "difficulty": random.choice(["Easy", "Medium", "Hard"]),
                "time_spent": 0,
                "attempts": 0,
                "start_time": None,
                "question_timer": 0
            })
        except Exception as e:
            continue
    
    return questions

def main():
    st.set_page_config(
        page_title="PDF Quiz PRO", 
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="collapsed"  # Start with sidebar collapsed
    )
    
    # Enhanced CSS with Slide-out Sidebar
    st.markdown("""
    <style>
    /* Main Header */
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        background: linear-gradient(45deg, #2E86AB, #4BB3FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* History Section Styles */
    .history-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #2E86AB;
    }
    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .history-score {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2E86AB;
    }
    .history-date {
        color: #666;
        font-size: 0.9rem;
    }
    .history-stats {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .stat-box {
        text-align: center;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 5px;
    }
    .stat-value {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2E86AB;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #666;
    }
    
    /* Slide-out Sidebar */
    .sidebar-toggle {
        position: fixed;
        left: 10px;
        top: 10px;
        z-index: 999;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .sidebar-toggle:hover {
        transform: scale(1.1);
        background: #0056b3;
    }
    
    /* Sidebar Content */
    .sidebar-content {
        position: fixed;
        left: -350px;
        top: 0;
        width: 320px;
        height: 100vh;
        background: white;
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        transition: left 0.3s ease;
        z-index: 998;
        padding: 20px;
        overflow-y: auto;
    }
    .sidebar-content.open {
        left: 0;
    }
    .sidebar-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 997;
        display: none;
    }
    .sidebar-overlay.open {
        display: block;
    }
    
    /* Quick Jump Grid Styles */
    .quick-jump-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 0.5rem;
        margin: 1rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    .jump-btn {
        padding: 0.8rem 0.5rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        border: 2px solid #dee2e6;
        background: white;
    }
    .jump-btn.answered {
        background: #28a745;
        color: white;
        border-color: #28a745;
    }
    .jump-btn.current {
        background: #007bff;
        color: white;
        border-color: #007bff;
        transform: scale(1.1);
    }
    .jump-btn.marked {
        background: #ffc107;
        color: black;
        border-color: #ffc107;
    }
    .jump-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* AI Explanation Styles */
    .ai-explanation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        animation: slideIn 0.5s ease-out;
    }
    .ai-explanation h4 {
        margin-top: 0;
        color: #ffd700;
    }
    @keyframes slideIn {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    /* Grid View Styles - Bubble Layout */
    .grid-view-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .question-bubble {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 20px;
        padding: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .question-bubble:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        border-color: #007bff;
    }
    .question-bubble.answered {
        border-color: #28a745;
        background: #f8fff9;
    }
    .question-bubble.current {
        border-color: #007bff;
        background: #f0f8ff;
        transform: scale(1.02);
    }
    .question-bubble.marked {
        border-color: #ffc107;
        background: #fffbf0;
    }
    .question-number {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #2c3e50;
    }
    .question-status {
        font-size: 0.8rem;
        color: #666;
    }
    
    /* List View Styles */
    .list-view-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .question-item {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .question-item:hover {
        border-color: #007bff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .question-item.answered {
        border-left: 4px solid #28a745;
    }
    .question-item.current {
        border-left: 4px solid #007bff;
        background: #f0f8ff;
    }
    .question-item.marked {
        border-left: 4px solid #ffc107;
    }
    .question-preview {
        flex: 1;
        font-size: 0.9rem;
        color: #666;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* Timer Styles */
    .timer-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .timer-display {
        font-size: 2rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
    }
    .question-timer {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
    }
    
    /* Sound Toggle */
    .sound-toggle {
        position: fixed;
        right: 10px;
        top: 10px;
        z-index: 999;
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
    }
    
    /* Existing styles... */
    .time-left-box { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .bubble-option { background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 25px; border: 2px solid transparent; transition: all 0.3s ease; cursor: pointer; margin: 0.5rem 0; }
    .bubble-option:hover { border-color: #007bff; transform: scale(1.02); }
    .bubble-option.selected { background: #007bff; color: white; border-color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar Toggle Button
    st.markdown("""
    <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
    <div class="sidebar-content" id="sidebarContent">
        <div style="text-align: right; margin-bottom: 1rem;">
            <button onclick="toggleSidebar()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
        </div>
    </div>
    
    <script>
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebarContent');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebarContent');
        const overlay = document.getElementById('sidebarOverlay');
        const toggleBtn = document.querySelector('.sidebar-toggle');
        
        if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target) && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Sound Toggle
    st.markdown("""
    <button class="sound-toggle" onclick="toggleSound()" id="soundToggle">🔊</button>
    <script>
    function toggleSound() {
        const btn = document.getElementById('soundToggle');
        const currentState = btn.textContent === '🔊';
        btn.textContent = currentState ? '🔇' : '🔊';
        // This would communicate with Streamlit via session state
        fetch('/toggle_sound?state=' + !currentState);
    }
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🧠 PDF Quiz PRO - Ultimate Edition</div>', unsafe_allow_html=True)
    
    # ========== NEW HISTORY TAB ==========
    tab1, tab2 = st.tabs(["📝 Take Quiz", "📊 Exam History"])
    
    with tab1:
        # Your existing quiz code remains exactly the same
        # Initialize session state
        default_states = {
            'quiz_mode': "practice",
            'current_view': "question",
            'show_ai_explanation': {},
            'marked_review': set(),
            'user_answers': {},
            'current_q': 0,
            'quiz_started': False,
            'start_time': time.time(),
            'quiz_completed': False,
            'user_profile': {
                'level': 1,
                'xp': 0,
                'achievements': [],
                'streak': 0,
                'total_quizzes': 0
            },
            'ai_suggestions': {},
            'dark_mode': False,
            'questions': [],
            'sound_enabled': True,
            'question_start_time': None,
            'sidebar_open': False,
            'view_type': 'grid'  # 'grid' or 'list'
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # Handle sound toggle
        if st.query_params.get('toggle_sound'):
            st.session_state.sound_enabled = st.query_params.get('state') == 'true'
            st.rerun()
        
        # Sidebar Content (will be populated via JavaScript)
        with st.sidebar:
            st.header("🎯 Quiz Mode")
            
            mode_col1, mode_col2 = st.columns(2)
            with mode_col1:
                if st.button("💡 Practice", use_container_width=True, 
                            type="primary" if st.session_state.quiz_mode == "practice" else "secondary"):
                    st.session_state.quiz_mode = "practice"
                    st.rerun()
            with mode_col2:
                if st.button("📝 Exam", use_container_width=True,
                            type="primary" if st.session_state.quiz_mode == "exam" else "secondary"):
                    st.session_state.quiz_mode = "exam"
                    st.rerun()
            
            st.markdown("---")
            st.header("👀 View Mode")
            
            view_col1, view_col2 = st.columns(2)
            with view_col1:
                if st.button("📖 Question", use_container_width=True,
                            type="primary" if st.session_state.current_view == "question" else "secondary"):
                    st.session_state.current_view = "question"
                    st.rerun()
            with view_col2:
                if st.button("🔲 Overview", use_container_width=True,
                            type="primary" if st.session_state.current_view == "grid" else "secondary"):
                    st.session_state.current_view = "grid"
                    st.rerun()
            
            st.markdown("---")
            st.header("🎮 Display Style")
            
            style_col1, style_col2 = st.columns(2)
            with style_col1:
                if st.button("🔘 Grid", use_container_width=True,
                            type="primary" if st.session_state.view_type == 'grid' else "secondary"):
                    st.session_state.view_type = 'grid'
                    st.rerun()
            with style_col2:
                if st.button("📋 List", use_container_width=True,
                            type="primary" if st.session_state.view_type == 'list' else "secondary"):
                    st.session_state.view_type = 'list'
                    st.rerun()
            
            st.markdown("---")
            st.header("⚙️ Settings")
            
            # Sound Toggle in Sidebar
            sound_label = "🔊 Sound On" if st.session_state.sound_enabled else "🔇 Sound Off"
            if st.button(sound_label, use_container_width=True):
                st.session_state.sound_enabled = not st.session_state.sound_enabled
                st.rerun()
            
            st.markdown("---")
            st.header("📊 Progress")
            
            if st.session_state.questions:
                total = len(st.session_state.questions)
                answered = len(st.session_state.user_answers)
                correct = sum(1 for q in st.session_state.questions 
                             if st.session_state.user_answers.get(q['id']) == q['correct_answer'])
                
                st.metric("Questions", f"{answered}/{total}")
                st.metric("Correct", f"{correct}/{answered}" if answered > 0 else "0")
                st.metric("Accuracy", f"{(correct/answered*100 if answered > 0 else 0):.1f}%")
        
        # Main content area
        uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf", help="Upload a PDF file containing quiz questions")
        
        if uploaded_file:
            if not st.session_state.questions or st.session_state.get('uploaded_file') != uploaded_file.name:
                with st.spinner("🔍 Processing PDF with AI Analysis..."):
                    st.session_state.questions = parse_pdf_content(uploaded_file)
                    st.session_state.uploaded_file = uploaded_file.name
                    # Reset quiz state when new file is uploaded
                    st.session_state.user_answers = {}
                    st.session_state.current_q = 0
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_started = True
                    st.session_state.start_time = time.time()
                    st.session_state.question_start_time = time.time()
            
            questions = st.session_state.questions
            
            if not questions:
                st.error("❌ No questions found. Please check the PDF format.")
                st.info("""
                **Expected PDF format:**
                - Questions should start with 'Q1.', 'Q2.', etc.
                - Options should be labeled A), B), C), D)
                - Answers should be marked with 'Answer: A' format
                """)
                return
            
            st.success(f"✅ Found {len(questions)} questions! + 🤖 AI Explanations Ready")
            
            # Timer Display
            if st.session_state.quiz_mode == "exam":
                remaining_time = max(0, 3600 - (time.time() - st.session_state.start_time))
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                
                st.markdown(f"""
                <div class="timer-container">
                    <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">⏰ Exam Time Left</div>
                    <div class="timer-display">{minutes:02d}:{seconds:02d}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Practice mode timer (stopwatch)
                elapsed_time = time.time() - st.session_state.start_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                
                st.markdown(f"""
                <div class="timer-container">
                    <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">⏱️ Practice Time</div>
                    <div class="timer-display">{minutes:02d}:{seconds:02d}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Question timer
            if st.session_state.question_start_time:
                question_elapsed = time.time() - st.session_state.question_start_time
                q_minutes = int(question_elapsed // 60)
                q_seconds = int(question_elapsed % 60)
                
                st.markdown(f"""
                <div class="question-timer">
                    <strong>Current Question:</strong> {q_minutes:02d}:{q_seconds:02d}
                </div>
                """, unsafe_allow_html=True)
            
            # Quick Jump Grid
            st.subheader("🎯 Quick Navigation")
            
            # Create grid with 10 questions per row
            rows = (len(questions) + 9) // 10
            
            for row in range(rows):
                cols = st.columns(10)
                start_idx = row * 10
                end_idx = min(start_idx + 10, len(questions))
                
                for idx in range(start_idx, end_idx):
                    with cols[idx % 10]:
                        is_answered = questions[idx]['id'] in st.session_state.user_answers
                        is_current = idx == st.session_state.current_q
                        is_marked = idx in st.session_state.marked_review
                        
                        btn_text = f"Q{idx+1}"
                        if is_marked:
                            btn_text = f"📌{idx+1}"
                        
                        button_type = "primary" if is_current else "secondary"
                        if st.button(btn_text, key=f"jump_{idx}", use_container_width=True, type=button_type):
                            st.session_state.current_q = idx
                            st.session_state.question_start_time = time.time()
                            st.rerun()
            
            # Display based on view mode
            if st.session_state.current_view == "grid":
                # OVERVIEW VIEW (Grid or List)
                st.subheader("🔲 Questions Overview")
                
                # View type toggle
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔘 Bubble Grid View", use_container_width=True,
                               type="primary" if st.session_state.view_type == 'grid' else "secondary"):
                        st.session_state.view_type = 'grid'
                        st.rerun()
                with col2:
                    if st.button("📋 List View", use_container_width=True,
                               type="primary" if st.session_state.view_type == 'list' else "secondary"):
                        st.session_state.view_type = 'list'
                        st.rerun()
                
                if st.session_state.view_type == 'grid':
                    # BUBBLE GRID VIEW
                    st.markdown('<div class="grid-view-container">', unsafe_allow_html=True)
                    
                    # Display all questions in bubble grid
                    cols = st.columns(4)
                    for idx, question in enumerate(questions):
                        col_idx = idx % 4
                        with cols[col_idx]:
                            is_answered = question['id'] in st.session_state.user_answers
                            is_current = idx == st.session_state.current_q
                            is_marked = idx in st.session_state.marked_review
                            
                            bubble_class = "question-bubble"
                            if is_current:
                                bubble_class += " current"
                            if is_answered:
                                bubble_class += " answered"
                            if is_marked:
                                bubble_class += " marked"
                            
                            status = "✅ Answered" if is_answered else "⭕ Unanswered"
                            if is_marked:
                                status = "📌 Marked"
                            
                            st.markdown(f"""
                            <div class="{bubble_class}" onclick="selectQuestion({idx})">
                                <div class="question-number">Q{idx+1}</div>
                                <div class="question-status">{status}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"Open Q{idx+1}", key=f"bubble_{idx}", use_container_width=True):
                                st.session_state.current_q = idx
                                st.session_state.current_view = "question"
                                st.session_state.question_start_time = time.time()
                                st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    # LIST VIEW
                    st.markdown('<div class="list-view-container">', unsafe_allow_html=True)
                    
                    for idx, question in enumerate(questions):
                        is_answered = question['id'] in st.session_state.user_answers
                        is_current = idx == st.session_state.current_q
                        is_marked = idx in st.session_state.marked_review
                        
                        item_class = "question-item"
                        if is_current:
                            item_class += " current"
                        if is_answered:
                            item_class += " answered"
                        if is_marked:
                            item_class += " marked"
                        
                        status_icon = "✅" if is_answered else "⭕"
                        if is_marked:
                            status_icon = "📌"
                        
                        st.markdown(f"""
                        <div class="{item_class}" onclick="selectQuestion({idx})">
                            <div style="font-weight: bold; min-width: 50px;">Q{idx+1}</div>
                            <div style="min-width: 30px;">{status_icon}</div>
                            <div class="question-preview">
                                {question['question'][:100]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Open", key=f"list_{idx}", use_container_width=True):
                            st.session_state.current_q = idx
                            st.session_state.current_view = "question"
                            st.session_state.question_start_time = time.time()
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
            else:
                # QUESTION VIEW
                if not st.session_state.quiz_completed:
                    current_q = questions[st.session_state.current_q]
                    current_answer = st.session_state.user_answers.get(current_q['id'])
                    
                    # Question Display
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem; color: white;">
                        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;">Question {st.session_state.current_q + 1} of {len(questions)}</div>
                        <div style="font-size: 1.3rem; font-weight: 600; line-height: 1.6;">
                            {current_q['question']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Options
                    selected_option = None
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        if is_selected:
                            selected_option = opt_letter
                        
                        if st.button(
                            f"{opt_letter}) {opt_text}",
                            key=f"opt_{current_q['id']}_{opt_letter}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            # Check answer and play sound
                            if st.session_state.quiz_mode == "practice":
                                if opt_letter == current_q['correct_answer']:
                                    autoplay_audio("correct")
                                else:
                                    autoplay_audio("wrong")
                            st.rerun()
                    
                    # AI Explanation Section
                    st.markdown("---")
                    exp_col1, exp_col2 = st.columns([3, 1])
                    
                    with exp_col1:
                        st.subheader("🤖 AI Explanation")
                    
                    with exp_col2:
                        if st.button("🔍 Show AI Explanation", use_container_width=True):
                            st.session_state.show_ai_explanation[current_q['id']] = True
                    
                    if st.session_state.show_ai_explanation.get(current_q['id'], False):
                        st.markdown(f"""
                        <div class="ai-explanation">
                            <h4>🧠 AI Analysis</h4>
                            {current_q['ai_explanation']}
                            
                            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px;">
                                <strong>💡 Pro Tip:</strong> This question is rated <strong>{current_q['difficulty']}</strong> difficulty. 
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Navigation Buttons
                    if st.session_state.quiz_mode == "exam":
                        # Exam navigation
                        exam_col1, exam_col2, exam_col3 = st.columns(3)
                        with exam_col1:
                            if st.button("⏮️ Previous", use_container_width=True, disabled=st.session_state.current_q == 0):
                                if st.session_state.current_q > 0:
                                    st.session_state.current_q -= 1
                                    st.session_state.question_start_time = time.time()
                                    st.rerun()
                        with exam_col2:
                            mark_text = "📌 Mark" if st.session_state.current_q not in st.session_state.marked_review else "✅ Unmark"
                            if st.button(f"{mark_text}", use_container_width=True):
                                if st.session_state.current_q in st.session_state.marked_review:
                                    st.session_state.marked_review.remove(st.session_state.current_q)
                                else:
                                    st.session_state.marked_review.add(st.session_state.current_q)
                                st.rerun()
                        with exam_col3:
                            next_text = "💾 Save & Next" if st.session_state.current_q < len(questions) - 1 else "🏁 Finish Exam"
                            if st.button(next_text, use_container_width=True, type="primary"):
                                if st.session_state.current_q < len(questions) - 1:
                                    st.session_state.current_q += 1
                                    st.session_state.question_start_time = time.time()
                                else:
                                    st.session_state.quiz_completed = True
                                    # ========== SAVE TO HISTORY ==========
                                    correct_count = sum(1 for q in questions 
                                                      if st.session_state.user_answers.get(q['id']) == q['correct_answer'])
                                    session_data = {
                                        'mode': st.session_state.quiz_mode,
                                        'total_questions': len(questions),
                                        'correct_answers': correct_count,
                                        'score_percentage': (correct_count / len(questions)) * 100,
                                        'time_taken': time.time() - st.session_state.start_time,
                                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'filename': st.session_state.get('uploaded_file', 'Unknown')
                                    }
                                    exam_history.save_session(session_data)
                                st.rerun()
                    else:
                        # Practice navigation
                        practice_col1, practice_col2, practice_col3, practice_col4 = st.columns(4)
                        with practice_col1:
                            if st.button("◀ Previous", use_container_width=True, disabled=st.session_state.current_q == 0):
                                if st.session_state.current_q > 0:
                                    st.session_state.current_q -= 1
                                    st.session_state.question_start_time = time.time()
                                    st.rerun()
                        with practice_col2:
                            if st.session_state.current_q < len(questions) - 1:
                                if st.button("Next ▶", use_container_width=True):
                                    st.session_state.current_q += 1
                                    st.session_state.question_start_time = time.time()
                                    st.rerun()
                            else:
                                if st.button("Finish 🏁", use_container_width=True, type="primary"):
                                    st.session_state.quiz_completed = True
                                    # ========== SAVE TO HISTORY ==========
                                    correct_count = sum(1 for q in questions 
                                                      if st.session_state.user_answers.get(q['id']) == q['correct_answer'])
                                    session_data = {
                                        'mode': st.session_state.quiz_mode,
                                        'total_questions': len(questions),
                                        'correct_answers': correct_count,
                                        'score_percentage': (correct_count / len(questions)) * 100,
                                        'time_taken': time.time() - st.session_state.start_time,
                                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'filename': st.session_state.get('uploaded_file', 'Unknown')
                                    }
                                    exam_history.save_session(session_data)
                                    st.rerun()
                        with practice_col3:
                            if current_answer:
                                if st.button("✅ Check Answer", use_container_width=True, type="primary"):
                                    # Show correct answer
                                    correct_answer = current_q['correct_answer']
                                    if current_answer == correct_answer:
                                        st.success(f"🎉 Correct! Answer: {correct_answer}")
                                        autoplay_audio("correct")
                                        # Add XP for correct answer
                                        st.session_state.user_profile['xp'] += 10
                                    else:
                                        st.error(f"❌ Incorrect! Correct answer: {correct_answer}")
                                        autoplay_audio("wrong")
                            else:
                                st.button("✅ Check Answer", use_container_width=True, disabled=True)
                        with practice_col4:
                            if st.button("🔄 Restart", use_container_width=True):
                                for key in ['user_answers', 'current_q', 'quiz_completed', 'marked_review', 'show_ai_explanation']:
                                    if key in st.session_state:
                                        if key == 'show_ai_explanation':
                                            st.session_state[key] = {}
                                        elif key == 'marked_review':
                                            st.session_state[key] = set()
                                        else:
                                            st.session_state[key] = default_states[key]
                                st.session_state.quiz_started = True
                                st.session_state.start_time = time.time()
                                st.session_state.question_start_time = time.time()
                                st.rerun()
                
                else:
                    # Results screen
                    st.balloons()
                    st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
                    
                    # Calculate results
                    correct_count = 0
                    for q in questions:
                        if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                            correct_count += 1
                    
                    total_time = time.time() - st.session_state.start_time
                    score_percent = (correct_count / len(questions)) * 100
                    
                    # Update user profile
                    st.session_state.user_profile['total_quizzes'] += 1
                    st.session_state.user_profile['xp'] += correct_count * 5
                    if score_percent >= 90:
                        st.session_state.user_profile['achievements'].append("Quiz Master")
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;">
                        <h2>Your Score: {correct_count}/{len(questions)}</h2>
                        <h1>{score_percent:.1f}%</h1>
                        <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                        <p>{'🎯 Perfect Score!' if score_percent == 100 else '🌟 Excellent!' if score_percent >= 90 else '👍 Great Job!'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Performance chart
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = score_percent,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Performance Score"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90}}))
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Restart button
                    if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                        for key in ['user_answers', 'current_q', 'quiz_completed', 'marked_review', 'show_ai_explanation']:
                            if key in st.session_state:
                                if key == 'show_ai_explanation':
                                    st.session_state[key] = {}
                                elif key == 'marked_review':
                                    st.session_state[key] = set()
                                else:
                                    st.session_state[key] = default_states[key]
                        st.session_state.quiz_started = True
                        st.session_state.start_time = time.time()
                        st.session_state.question_start_time = time.time()
                        st.rerun()

        else:
            st.info("👆 Please upload a PDF file to start the quiz")
            st.markdown("""
            ### 📝 Expected PDF Format:
            ```
            Q1. What is the capital of France?
            A) London
            B) Berlin
            C) Paris
            D) Madrid
            Answer: C
            
            Q2. Which planet is known as the Red Planet?
            A) Venus
            B) Mars
            C) Jupiter
            D) Saturn
            Answer: B
            ```
            """)

    with tab2:
        # ========== HISTORY TAB CONTENT ==========
        st.markdown('<div class="main-header">📊 Exam History</div>', unsafe_allow_html=True)
        
        # Load and display history
        history_data = exam_history.load_history()
        
        if not history_data:
            st.info("📝 No exam history found. Complete a quiz to see your history here!")
        else:
            # Statistics
            total_sessions = len(history_data)
            avg_score = sum(session['score_percentage'] for session in history_data) / total_sessions
            best_score = max(session['score_percentage'] for session in history_data)
            total_time = sum(session['time_taken'] for session in history_data)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sessions", total_sessions)
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                st.metric("Best Score", f"{best_score:.1f}%")
            with col4:
                st.metric("Total Study Time", f"{int(total_time/60)}m")
            
            # Clear history button
            if st.button("🗑️ Clear All History", type="secondary"):
                if exam_history.clear_history():
                    st.success("History cleared successfully!")
                    st.rerun()
                else:
                    st.error("Failed to clear history")
            
            st.markdown("---")
            
            # Display each session
            for i, session in enumerate(reversed(history_data)):
                with st.container():
                    st.markdown(f"""
                    <div class="history-card">
                        <div class="history-header">
                            <h3>Session {total_sessions - i}</h3>
                            <div class="history-score">{session['score_percentage']:.1f}%</div>
                        </div>
                        <div class="history-date">
                            📅 {session['date']} | 📁 {session['filename']} | 🎯 {session['mode'].title()} Mode
                        </div>
                        <div class="history-stats">
                            <div class="stat-box">
                                <div class="stat-value">{session['correct_answers']}/{session['total_questions']}</div>
                                <div class="stat-label">Correct</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">{session['score_percentage']:.1f}%</div>
                                <div class="stat-label">Score</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">{int(session['time_taken']/60)}m {int(session['time_taken']%60)}s</div>
                                <div class="stat-label">Time</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-value">{session['mode'].title()}</div>
                                <div class="stat-label">Mode</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Progress chart
            if len(history_data) > 1:
                st.markdown("### 📈 Progress Over Time")
                chart_data = []
                for i, session in enumerate(history_data):
                    chart_data.append({
                        'Session': i + 1,
                        'Score': session['score_percentage'],
                        'Date': session['date'][:10],
                        'Mode': session['mode']
                    })
                
                df = pd.DataFrame(chart_data)
                fig = px.line(df, x='Session', y='Score', title='Score Progress', 
                             markers=True, color='Mode')
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
