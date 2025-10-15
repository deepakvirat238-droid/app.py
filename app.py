import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import base64
from fpdf import FPDF
import os
import pdfplumber
import PyPDF2
import re
import io

# Page Configuration
st.set_page_config(
    page_title="MockTest Pro - Exam Preparation",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2e86ab;
        border-bottom: 3px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    .test-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .question-box {
        background: #f8f9fa;
        border-left: 5px solid #667eea;
        padding: 20px;
        margin: 15px 0;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .timer-red {
        color: #ff6b6b;
        font-weight: bold;
        font-size: 1.4rem;
    }
    .timer-green {
        color: #4ecdc4;
        font-weight: bold;
        font-size: 1.4rem;
    }
    .pdf-upload-box {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        background: #f8f9fa;
        margin: 20px 0;
    }
    .nav-button {
        width: 100%;
        margin: 5px 0;
    }
    .correct-answer {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 10px;
        border-radius: 5px;
    }
    .wrong-answer {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

class PDFQuizConverter:
    def __init__(self):
        self.question_patterns = [
            r'(?:Q\.?\s*\d+[\.\)]|Question\s*\d+|\d+\.\s*|\(\d+\))\s*(.*?)(?=(?:Q\.?\s*\d+[\.\)]|Question\s*\d+|\d+\.\s*|\(\d+\)|$))'
        ]
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from searchable PDF"""
        text = ""
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            st.error(f"PDF processing error: {e}")
        return text
    
    def parse_question_block(self, block):
        """Parse individual question block in your specific format"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if len(lines) < 3:
            return None
        
        question_data = {
            'question': '',
            'options': [],
            'correct_answer': None,
            'explanation': 'Auto-extracted from PDF'
        }
        
        # First line is question
        question_data['question'] = lines[0]
        
        # Parse options (lines starting with A., B., C., D.)
        option_lines = []
        answer_line = None
        
        for line in lines[1:]:
            if re.match(r'^[A-D]\.', line, re.IGNORECASE):
                option_lines.append(line)
            elif 'answer' in line.lower():
                answer_line = line
            elif re.match(r'^[A-D]\.', line[:3], re.IGNORECASE):
                option_lines.append(line)
        
        question_data['options'] = option_lines
        
        # Extract correct answer
        if answer_line:
            answer_match = re.search(r'[A-D]', answer_line, re.IGNORECASE)
            if answer_match:
                question_data['correct_answer'] = answer_match.group().upper()
        
        return question_data if question_data['question'] and len(question_data['options']) >= 2 else None
    
    def smart_question_parser(self, text):
        """Advanced parser for your specific PDF format"""
        questions = []
        
        # Split text into blocks (questions are separated by blank lines or question patterns)
        blocks = re.split(r'\n\s*\n', text)
        
        for block in blocks:
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            if len(lines) < 3:  # Need at least question + 2 options
                continue
            
            # Check if this looks like a question block
            first_line = lines[0].strip()
            if not (re.match(r'^(?:Q\.?|Question|\d+\.|\(?\d+\)?)', first_line, re.IGNORECASE) or 
                   '?' in first_line or 'which' in first_line.lower()):
                continue
            
            question_data = self.parse_question_block(block)
            if question_data:
                questions.append(question_data)
        
        return questions

class MockTestApp:
    def __init__(self):
        self.pdf_converter = PDFQuizConverter()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        defaults = {
            'bookmarks': [],
            'test_history': [],
            'practice_history': [],
            'progress': {},
            'current_test': None,
            'current_practice': None,
            'converted_questions': [],
            'language': 'English',
            'admin_mode': False
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def main(self):
        st.markdown('<div class="main-header">📚 MockTest Pro - Exam Preparation Platform</div>', unsafe_allow_html=True)
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("🎯 Navigation")
            app_mode = st.selectbox(
                "Choose Mode:",
                ["🏠 Dashboard", "📝 Exam Mode", "🔍 Practice Mode", "📚 Previous Year Papers", 
                 "📊 Performance Analysis", "⭐ Bookmarked Questions", "🔄 PDF to Quiz Converter", "⚙️ Admin Panel"]
            )
            
            st.session_state.language = st.radio(
                "Language / भाषा:",
                ["English", "Hindi"],
                horizontal=True
            )
            
            st.markdown("---")
            st.info(f"👤 User: Demo User | 🌐 {st.session_state.language}")
        
        # Route to different sections
        route_map = {
            "🏠 Dashboard": self.show_dashboard,
            "📝 Exam Mode": self.exam_mode,
            "🔍 Practice Mode": self.practice_mode,
            "📚 Previous Year Papers": self.previous_year_papers,
            "📊 Performance Analysis": self.performance_analysis,
            "⭐ Bookmarked Questions": self.bookmarked_questions,
            "🔄 PDF to Quiz Converter": self.pdf_to_quiz_converter,
            "⚙️ Admin Panel": self.admin_panel
        }
        
        route_map[app_mode]()

    # PDF to Quiz Converter (same as before)
    def pdf_to_quiz_converter(self):
        st.markdown('<div class="section-header">🔄 PDF to Quiz Converter</div>', unsafe_allow_html=True)
        
        st.info("📄 **Upload Searchable PDF** - Supports format: 'Q1. Question text\\nA. Option1\\nB. Option2\\nC. Option3\\nD. Option4\\nAnswer C'")
        
        uploaded_pdf = st.file_uploader("Choose a PDF file", type=['pdf'], key="pdf_uploader")
        
        if uploaded_pdf:
            file_size = uploaded_pdf.size / 1024
            st.success(f"✅ PDF Uploaded! Size: {file_size:.1f} KB")
            
            with st.spinner("🔍 Extracting questions from PDF..."):
                pdf_text = self.pdf_converter.extract_text_from_pdf(uploaded_pdf)
                
                if not pdf_text:
                    st.error("❌ No text extracted. Ensure it's searchable PDF.")
                    return
                
                with st.expander("📖 View Extracted Text"):
                    st.text_area("Extracted Content", pdf_text[:2000] + "..." if len(pdf_text) > 2000 else pdf_text, height=200)
                
                questions = self.pdf_converter.smart_question_parser(pdf_text)
                
                if questions:
                    st.session_state.converted_questions = questions
                    st.success(f"🎉 Extracted {len(questions)} questions!")
                    self.display_converted_questions(questions)
                    self.export_questions_options(questions)
                else:
                    st.warning("⚠️ No questions detected.")

    def display_converted_questions(self, questions):
        st.markdown("### 📋 Extracted Questions")
        
        for i, question in enumerate(questions[:10]):
            with st.expander(f"Q{i+1}: {question['question'][:100]}...", expanded=i<2):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    edited_question = st.text_area("Question", value=question['question'], key=f"q_{i}")
                    st.write("**Options:**")
                    edited_options = []
                    for j, opt in enumerate(question['options']):
                        edited_opt = st.text_input(f"Option {chr(65+j)}", value=opt, key=f"q_{i}_opt_{j}")
                        edited_options.append(edited_opt)
                
                with col2:
                    correct_ans = st.selectbox("Correct Answer", ['A','B','C','D','Not Set'], 
                                             index=0 if question['correct_answer'] else 4, key=f"q_{i}_ans")
                    topic = st.selectbox("Topic", ["General","Math","Reasoning","English","GK"], key=f"q_{i}_topic")
                    difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"], key=f"q_{i}_diff")
                
                questions[i].update({
                    'question': edited_question,
                    'options': edited_options,
                    'correct_answer': correct_ans if correct_ans != 'Not Set' else None,
                    'topic': topic,
                    'difficulty': difficulty
                })

    def export_questions_options(self, questions):
        st.markdown("### 💾 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Save to Bank", use_container_width=True):
                st.session_state.converted_questions = questions
                st.success(f"✅ {len(questions)} questions saved!")
        
        with col2:
            if st.button("📄 Export CSV", use_container_width=True):
                self.export_to_csv(questions)
        
        with col3:
            if st.button("🎯 Create Test", use_container_width=True):
                st.session_state.current_test = self.create_test_from_questions(questions)
                st.rerun()

    def export_to_csv(self, questions):
        csv_data = []
        for i, q in enumerate(questions):
            csv_data.append({
                'ID': i+1, 'Question': q['question'],
                'A': q['options'][0] if len(q['options']) > 0 else '',
                'B': q['options'][1] if len(q['options']) > 1 else '',
                'C': q['options'][2] if len(q['options']) > 2 else '',
                'D': q['options'][3] if len(q['options']) > 3 else '',
                'Answer': q['correct_answer'], 'Topic': q.get('topic','General'),
                'Difficulty': q.get('difficulty','Medium')
            })
        
        df = pd.DataFrame(csv_data)
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="questions.csv">📥 Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

    def create_test_from_questions(self, questions):
        return {
            'subject': 'PDF Import',
            'questions': questions,
            'total_questions': len(questions),
            'start_time': datetime.now(),
            'answers': {},
            'question_times': {},
            'current_question': 0,
            'marked_review': set(),
            'mode': 'exam'
        }

    # NEW: PRACTICE MODE WITH STOPWATCH
    def practice_mode(self):
        st.markdown('<div class="section-header">🔍 Practice Mode</div>', unsafe_allow_html=True)
        
        # Practice session controls
        col1, col2, col3 = st.columns(3)
        with col1:
            questions_source = st.selectbox("Questions From", ["PDF Import", "Sample Bank", "Bookmarked"])
        with col2:
            question_count = st.slider("Number of Questions", 5, 50, 10)
        with col3:
            if st.button("🚀 Start Practice Session", use_container_width=True):
                self.start_practice_session(question_count, questions_source)
        
        # Active practice session
        if st.session_state.current_practice:
            self.render_practice_interface()
        
        # Practice history
        if st.session_state.practice_history:
            st.markdown("### 📈 Recent Practice Sessions")
            for session in st.session_state.practice_history[-5:]:
                st.write(f"**{session['date']}** - Score: {session['score']}/{session['total']} | Time: {session['total_time']}s")

    def start_practice_session(self, count, source):
        questions = self.get_questions_for_practice(count, source)
        st.session_state.current_practice = {
            'questions': questions,
            'total_questions': len(questions),
            'start_time': datetime.now(),
            'current_question': 0,
            'answers': {},
            'question_start_times': {},
            'question_times': {},
            'show_answers': True,  # Quick answers in practice mode
            'mode': 'practice'
        }
        # Start timer for first question
        st.session_state.current_practice['question_start_times'][0] = datetime.now()

    def get_questions_for_practice(self, count, source):
        if source == "PDF Import" and st.session_state.converted_questions:
            return st.session_state.converted_questions[:count]
        else:
            # Sample questions
            return [
                {
                    'question': 'What is 15% of 200?',
                    'options': ['15', '30', '25', '20'],
                    'correct_answer': 'B',
                    'explanation': '15% of 200 = (15/100) × 200 = 30'
                },
                {
                    'question': 'Which is a prime number?',
                    'options': ['4', '9', '11', '15'],
                    'correct_answer': 'C',
                    'explanation': '11 is only divisible by 1 and itself'
                }
            ][:count]

    def render_practice_interface(self):
        practice = st.session_state.current_practice
        if not practice:
            return
        
        # Practice header with stopwatch
        col1, col2, col3, col4 = st.columns([2,1,1,1])
        
        with col1:
            st.subheader("🔍 Practice Session")
        with col2:
            # Session timer
            elapsed = (datetime.now() - practice['start_time']).seconds
            st.markdown(f'<div class="timer-green">⏱️ {elapsed}s</div>', unsafe_allow_html=True)
        with col3:
            # Current question timer
            if practice['current_question'] in practice['question_start_times']:
                q_elapsed = (datetime.now() - practice['question_start_times'][practice['current_question']]).seconds
                st.markdown(f'<div class="timer-green">⏰ {q_elapsed}s</div>', unsafe_allow_html=True)
        with col4:
            if st.button("📤 End Practice"):
                self.end_practice_session()
        
        # Quick navigation palette
        st.markdown("### Quick Navigation")
        cols = st.columns(10)
        for i in range(min(10, practice['total_questions'])):
            with cols[i]:
                status = "✅" if i in practice['answers'] else "⚪"
                if st.button(f"{status}{i+1}", key=f"p_nav_{i}", use_container_width=True):
                    # Save current question time
                    if practice['current_question'] in practice['question_start_times']:
                        start_time = practice['question_start_times'].get(practice['current_question'])
                        if start_time:
                            practice['question_times'][practice['current_question']] = (datetime.now() - start_time).seconds
                    
                    practice['current_question'] = i
                    practice['question_start_times'][i] = datetime.now()
                    st.rerun()
        
        # Current question
        current_q = practice['current_question']
        if current_q < len(practice['questions']):
            question_data = practice['questions'][current_q]
            self.display_practice_question(question_data, current_q)
        
        # Navigation buttons near question
        st.markdown("---")
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        with nav_col1:
            if st.button("⬅️ Previous", use_container_width=True) and current_q > 0:
                self.navigate_practice_question(-1)
        with nav_col2:
            if st.button("Next ➡️", use_container_width=True) and current_q < practice['total_questions'] - 1:
                self.navigate_practice_question(1)
        with nav_col3:
            if st.button("⭐ Bookmark", use_container_width=True):
                self.bookmark_question(question_data)
        with nav_col4:
            if st.button("🔍 Show Answer", use_container_width=True):
                practice['show_answers'] = True
                st.rerun()

    def navigate_practice_question(self, direction):
        practice = st.session_state.current_practice
        current = practice['current_question']
        
        # Save current question time
        if current in practice['question_start_times']:
            start_time = practice['question_start_times'][current]
            practice['question_times'][current] = (datetime.now() - start_time).seconds
        
        # Navigate
        new_index = current + direction
        if 0 <= new_index < practice['total_questions']:
            practice['current_question'] = new_index
            practice['question_start_times'][new_index] = datetime.now()
            practice['show_answers'] = False  # Hide answer when moving to new question
            st.rerun()

    def display_practice_question(self, question_data, q_index):
        practice = st.session_state.current_practice
        
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"**Q{q_index+1}. {question_data['question']}**")
        
        # Options
        selected_option = st.radio(
            "Select your answer:",
            question_data['options'],
            key=f"practice_q_{q_index}",
            index=practice['answers'].get(q_index, None)
        )
        
        # Save answer and provide immediate feedback in practice mode
        if selected_option:
            option_index = question_data['options'].index(selected_option)
            practice['answers'][q_index] = option_index
            
            # Immediate feedback in practice mode
            correct_index = ord(question_data['correct_answer']) - 65 if question_data['correct_answer'] else -1
            
            if option_index == correct_index:
                st.success("🎉 Correct! ✅")
                # Play success sound (visual feedback)
                st.markdown("🔊 *Correct sound*")
            else:
                st.error("❌ Incorrect")
                st.markdown("🔊 *Wrong sound*")
            
            # Show explanation if enabled
            if practice['show_answers']:
                with st.expander("📖 Explanation"):
                    st.write(question_data.get('explanation', 'No explanation available.'))
                    if question_data['correct_answer']:
                        st.write(f"**Correct answer: {question_data['correct_answer']}**")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def bookmark_question(self, question_data):
        if question_data not in st.session_state.bookmarks:
            st.session_state.bookmarks.append(question_data)
            st.success("✅ Question bookmarked!")

    def end_practice_session(self):
        practice = st.session_state.current_practice
        if not practice:
            return
        
        # Calculate results
        score = 0
        for q_index, user_answer in practice['answers'].items():
            if q_index < len(practice['questions']):
                correct_answer = practice['questions'][q_index]['correct_answer']
                if correct_answer and user_answer == (ord(correct_answer) - 65):
                    score += 1
        
        total_time = (datetime.now() - practice['start_time']).seconds
        
        # Save to history
        session_result = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'score': score,
            'total': practice['total_questions'],
            'total_time': total_time,
            'answers': practice['answers'].copy(),
            'questions': practice['questions'].copy(),
            'question_times': practice['question_times'].copy()
        }
        
        st.session_state.practice_history.append(session_result)
        
        # Show results and download option
        st.success("🏁 Practice Session Completed!")
        self.show_practice_results(session_result)
        
        st.session_state.current_practice = None

    def show_practice_results(self, result):
        st.markdown("### 📊 Practice Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Score", f"{result['score']}/{result['total']}")
        with col2:
            accuracy = (result['score'] / result['total']) * 100
            st.metric("Accuracy", f"{accuracy:.1f}%")
        with col3:
            st.metric("Total Time", f"{result['total_time']}s")
        with col4:
            avg_time = result['total_time'] / result['total'] if result['total'] > 0 else 0
            st.metric("Avg Time/Q", f"{avg_time:.1f}s")
        
        # Download PDF report
        if st.button("📄 Download Detailed Report PDF"):
            self.generate_practice_pdf_report(result)

    def generate_practice_pdf_report(self, result):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Header
        pdf.cell(200, 10, txt="Practice Session Report", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Date: {result['date']}", ln=1)
        pdf.cell(200, 10, txt=f"Score: {result['score']}/{result['total']}", ln=1)
        pdf.cell(200, 10, txt=f"Accuracy: {(result['score']/result['total'])*100:.1f}%", ln=1)
        pdf.cell(200, 10, txt=f"Total Time: {result['total_time']} seconds", ln=1)
        pdf.ln(10)
        
        # Questions and answers
        pdf.set_font("Arial", size=10)
        for i, question in enumerate(result['questions']):
            pdf.multi_cell(0, 8, txt=f"Q{i+1}. {question['question']}")
            
            # User's answer
            user_ans_index = result['answers'].get(i)
            user_ans = question['options'][user_ans_index] if user_ans_index is not None else "Not attempted"
            correct_ans = question['options'][ord(question['correct_answer'])-65] if question['correct_answer'] else "Not set"
            
            pdf.cell(0, 8, txt=f"Your answer: {user_ans}", ln=1)
            pdf.cell(0, 8, txt=f"Correct answer: {correct_ans}", ln=1)
            
            if user_ans_index == (ord(question['correct_answer'])-65 if question['correct_answer'] else -1):
                pdf.set_text_color(0, 128, 0)
                pdf.cell(0, 8, txt="Status: ✅ Correct", ln=1)
            else:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(0, 8, txt="Status: ❌ Incorrect", ln=1)
            
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
        
        # Save and provide download
        filename = f"practice_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename)
        
        with open(filename, "rb") as f:
            pdf_data = f.read()
        
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Download Practice Report PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        os.remove(filename)

    # EXAM MODE (Similar to previous mock test but with timing features)
    def exam_mode(self):
        st.markdown('<div class="section-header">📝 Exam Mode</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            test_type = st.selectbox("Test Type", ["Full Length", "Subject Wise"])
            subject = st.selectbox("Subject", ["Mathematics", "Reasoning", "English", "General Awareness"])
        with col2:
            duration = st.selectbox("Duration", ["30 minutes", "60 minutes", "90 minutes", "120 minutes"])
            total_questions = st.slider("Total Questions", 10, 100, 25)
        
        if st.button("🚀 Start Exam", type="primary"):
            self.start_exam_session(subject, total_questions, duration)
        
        if st.session_state.current_test and st.session_state.current_test.get('mode') == 'exam':
            self.render_exam_interface()

    def start_exam_session(self, subject, total_questions, duration):
        questions = self.get_questions_for_practice(total_questions, "Sample Bank")
        st.session_state.current_test = {
            'subject': subject,
            'questions': questions,
            'total_questions': total_questions,
            'duration': duration,
            'start_time': datetime.now(),
            'answers': {},
            'question_times': {},
            'question_start_times': {0: datetime.now()},
            'current_question': 0,
            'marked_review': set(),
            'mode': 'exam'
        }

    def render_exam_interface(self):
        # Similar to practice but without immediate answers
        # Implementation would be similar to practice mode but without show_answers
        pass

    # Other methods (dashboard, performance analysis, etc.) remain similar to previous implementation
    def show_dashboard(self):
        st.markdown('<div class="section-header">📊 Your Learning Dashboard</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tests Taken", len(st.session_state.test_history))
        with col2:
            st.metric("Practice Sessions", len(st.session_state.practice_history))
        with col3:
            st.metric("Bookmarks", len(st.session_state.bookmarks))
        with col4:
            st.metric("PDF Questions", len(st.session_state.converted_questions))

    def previous_year_papers(self):
        st.markdown('<div class="section-header">📚 Previous Year Papers</div>', unsafe_allow_html=True)
        st.info("PYQ section - would contain actual previous year papers")

    def performance_analysis(self):
        st.markdown('<div class="section-header">📊 Performance Analysis</div>', unsafe_allow_html=True)
        
        if st.session_state.practice_history:
            # Show practice performance charts
            history_df = pd.DataFrame(st.session_state.practice_history)
            fig = px.line(history_df, x='date', y='score', title='Practice Score Trend')
            st.plotly_chart(fig, use_container_width=True)

    def bookmarked_questions(self):
        st.markdown('<div class="section-header">⭐ Bookmarked Questions</div>', unsafe_allow_html=True)
        
        for i, question in enumerate(st.session_state.bookmarks):
            with st.expander(f"Bookmark {i+1}: {question['question'][:100]}..."):
                st.write(question['question'])
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.bookmarks.pop(i)
                    st.rerun()

    def admin_panel(self):
        st.markdown('<div class="section-header">⚙️ Admin Panel</div>', unsafe_allow_html=True)
        st.info("Admin features for question bank management")

# Run the app
if __name__ == "__main__":
    app = MockTestApp()
    app.main()
