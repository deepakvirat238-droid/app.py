# streamlit_pdf_quiz_pro.py
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
import hashlib
import json
import tempfile
from typing import List, Dict, Any

# ---------------------------
# Helpers & Caching
# ---------------------------

def file_hash(file_bytes: bytes) -> str:
    h = hashlib.sha256()
    h.update(file_bytes)
    return h.hexdigest()

@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text with pdfplumber first, fallback to pytesseract for scanned pages.
       This is cached by pdf bytes hash to speed repeated re-runs."""
    text = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text.append(page_text)
                else:
                    # fallback OCR on page image
                    try:
                        pil_img = page.to_image(resolution=200).original
                        ocr_text = pytesseract.image_to_string(pil_img)
                        text.append(ocr_text)
                    except Exception:
                        # if a page fails, append empty string but continue
                        text.append("")
    except Exception as e:
        raise RuntimeError(f"Failed to open/process PDF: {e}")
    return "\n".join(text)

def guess_question_type(question: str) -> str:
    q = question.lower()
    if any(word in q for word in ['synonym', 'antonym', 'word', 'meaning']):
        return "vocabulary"
    if any(word in q for word in ['tense', 'grammar', 'sentence', 'verb']):
        return "grammar"
    if any(word in q for word in ['passage', 'read', 'comprehension']):
        return "comprehension"
    if any(word in q for word in ['logic', 'reason', 'deduce', 'infer']):
        return "logic"
    return "general"

def generate_ai_explanation(question: str, correct_answer: str, options: Dict[str,str]) -> str:
    explanations = {
        "grammar": "This question tests your understanding of grammatical rules.",
        "vocabulary": "This vocabulary question requires understanding word meanings and contextual usage.",
        "comprehension": "This reading comprehension question tests your ability to understand and interpret written text.",
        "logic": "This logical reasoning question requires analytical thinking and deduction skills.",
        "general": "This question evaluates fundamental knowledge in the subject area."
    }
    etype = guess_question_type(question)
    base = explanations.get(etype, explanations["general"])
    tips = f"\n\nWhy {correct_answer} is correct:\n\n- It follows the rules of {etype}.\n- The other options contain common misconceptions.\n\nTip: Practice similar {etype} questions."
    return base + tips

@st.cache_data(show_spinner=False)
def parse_pdf_questions(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse questions out of raw PDF text. Returns list of question dicts."""
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    # Split heuristically on Q<number> or lines starting with number + dot
    parts = re.split(r'(?i)\bq\d+\.|\n\d+\.\s', raw_text)
    questions = []
    # First element before Q1 might be header -> skip if empty
    for idx, block in enumerate(parts[1:], start=1):
        b = block.strip()
        if not b:
            continue
        # Question text until options or Answer:
        question_match = re.search(r'^(.*?)(?=\n[A-E]\)|\n[A-E]\.|Answer:|ANSWER:|$)', b, re.DOTALL)
        question_text = question_match.group(1).strip() if question_match else b[:200].strip()

        # Extract option lines like A) text or A. text
        options_found = dict()
        for opt_letter, opt_text in re.findall(r'([A-E])[\)\.]\s*(.*?)(?=(?:\n[A-E][\)\.]|\nAnswer:|\nANSWER:|$))', b, re.DOTALL):
            options_found[opt_letter] = opt_text.strip().replace("\n", " ")

        if not options_found:
            # Try single-line options with uppercase letters
            # fallback default
            options_found = {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'}

        answer_match = re.search(r'(?i)Answer[:\s]*([A-E])', b)
        correct = answer_match.group(1) if answer_match else random.choice(list(options_found.keys()))

        ai_expl = generate_ai_explanation(question_text, correct, options_found)
        questions.append({
            "id": idx,
            "question": question_text,
            "options": options_found,
            "correct_answer": correct,
            "ai_explanation": ai_expl,
            "difficulty": random.choice(["Easy", "Medium", "Hard"]),
            "time_spent": 0,
            "attempts": 0
        })
    return questions

# Utility to convert questions to dataframe
def questions_to_df(questions: List[Dict[str,Any]]) -> pd.DataFrame:
    rows = []
    for q in questions:
        row = {
            "id": q["id"],
            "question": q["question"],
            "correct": q["correct_answer"],
            "difficulty": q.get("difficulty", ""),
        }
        for k,v in q["options"].items():
            row[f"opt_{k}"] = v
        rows.append(row)
    return pd.DataFrame(rows)

# ---------------------------
# UI / App
# ---------------------------

st.set_page_config(page_title="PDF Quiz PRO — Professional", layout="wide", page_icon="🚀")

# Top bar
st.markdown("""
<style>
/* small improvements for a polished header */
.header {
  display:flex; align-items:center; gap:16px;
}
.app-title {
  font-size:24px; font-weight:700;
}
.small-muted { color: #6c757d; font-size:13px; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,6,1])
with col1:
    st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/frontend/public/brand/streamlit-mark.svg", width=48)
with col2:
    st.markdown('<div class="header"><div class="app-title">PDF Quiz PRO — Professional</div><div class="small-muted">Upload. Parse. Practice. Analyze.</div></div>', unsafe_allow_html=True)
with col3:
    # Small profile / quick stats
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {"xp":0, "total_quizzes":0, "achievements":[]}

# Sidebar controls (streamlit-native)
st.sidebar.header("⚙️ Controls")
mode = st.sidebar.radio("Mode", ["Practice", "Exam"], index=0)
view = st.sidebar.radio("Default View", ["Question", "Overview"], index=0)
st.sidebar.markdown("---")
st.sidebar.header("Settings")
sound_enabled = st.sidebar.checkbox("Enable sounds", value=st.session_state.get("sound_enabled", True))
st.session_state["sound_enabled"] = sound_enabled
auto_show_ai = st.sidebar.checkbox("Auto show AI explanation after answer", value=False)
st.sidebar.markdown("---")
st.sidebar.header("Export / Persistence")
persist = st.sidebar.checkbox("Persist progress in memory (browser)", value=True)
if st.sidebar.button("Reset saved progress"):
    for k in ["user_answers", "current_q", "quiz_completed", "marked_review", "questions", "uploaded_file_hash"]:
        if k in st.session_state:
            del st.session_state[k]
    st.sidebar.success("Progress cleared")

# Upload area
st.markdown("### 📁 Upload your PDF")
uploaded_file = st.file_uploader("Upload a PDF with questions (Q1., options A) B) ..., Answer: X)", type="pdf")

# Local helper: save uploaded bytes
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    uploaded_hash = file_hash(file_bytes)
    st.session_state["uploaded_file_hash"] = uploaded_hash

    # If not parsed before or new file, parse and initialize
    if st.session_state.get("questions") is None or st.session_state.get("uploaded_file_hash") != uploaded_hash:
        try:
            with st.spinner("Processing PDF — extracting questions..."):
                questions = parse_pdf_questions(file_bytes)
                if not questions:
                    st.error("No questions detected — check PDF format.")
                    st.stop()
                st.session_state["questions"] = questions
                # initialize user state
                st.session_state["user_answers"] = {}  # id -> option
                st.session_state["current_q"] = 0
                st.session_state["quiz_completed"] = False
                st.session_state["marked_review"] = []
                st.session_state["start_time"] = time.time()
                st.session_state["question_start_time"] = time.time()
        except Exception as e:
            st.exception(e)
            st.stop()

# If questions loaded, show preview & main UI
if st.session_state.get("questions"):
    questions = st.session_state["questions"]
    totalq = len(questions)

    # show PDF first page preview (if possible)
    if uploaded_file:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                first_page = pdf.pages[0]
                pil_img = first_page.to_image(resolution=150).original
                st.image(pil_img, caption="PDF preview (first page)", use_column_width=False)
        except Exception:
            pass

    # Top quick stats
    answered = len(st.session_state["user_answers"])
    correct_count = sum(1 for q in questions if st.session_state["user_answers"].get(q["id"]) == q["correct_answer"])
    progress_col1, progress_col2, progress_col3, progress_col4 = st.columns([2,2,2,4])
    progress_col1.metric("Questions", f"{answered}/{totalq}")
    progress_col2.metric("Correct", f"{correct_count}/{answered}" if answered else "0/0")
    accuracy = (correct_count/answered*100) if answered else 0
    progress_col3.metric("Accuracy", f"{accuracy:.1f}%")
    # progress bar
    progress_col4.progress(int((answered/totalq)*100) if totalq else 0)

    # two-pane layout: left: quiz, right: analytics + editor
    left, right = st.columns([3,2])

    # ---------- LEFT: Quiz UI ----------
    with left:
        st.subheader("📝 Quiz Area")
        idx = st.session_state.get("current_q", 0)
        idx = max(0, min(idx, totalq-1))
        st.session_state["current_q"] = idx
        q = questions[idx]

        # Question card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg,#667eea,#764ba2); padding:16px; border-radius:12px; color:white;">
            <div style="font-weight:700">Question {idx+1} of {totalq} — Difficulty: {q.get('difficulty')}</div>
            <div style="margin-top:8px; font-size:16px;">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Options (buttons)
        st.write("")  # small spacer
        cols = st.columns(2)
        for i, (opt_letter, opt_text) in enumerate(q["options"].items()):
            col = cols[i % 2]
            is_selected = st.session_state["user_answers"].get(q["id"]) == opt_letter
            btn_label = f"{opt_letter}) {opt_text}"
            if col.button(btn_label, key=f"opt_{q['id']}_{opt_letter}", help=f"Select option {opt_letter}"):
                st.session_state["user_answers"][q["id"]] = opt_letter
                questions[idx]["attempts"] = questions[idx].get("attempts", 0) + 1
                # play sound: minimal safe HTML audio
                if st.session_state["sound_enabled"]:
                    if opt_letter == q["correct_answer"]:
                        st.audio("https://assets.mixkit.co/sfx/preview/mixkit-correct-answer-tone-2870.mp3")
                    else:
                        st.audio("https://assets.mixkit.co/sfx/preview/mixkit-wrong-answer-fail-notification-946.mp3")
                # auto reveal explanation if setting on
                if auto_show_ai:
                    st.session_state.setdefault("show_ai", {})[q["id"]] = True
                st.experimental_rerun()

        # Show check / navigation controls
        nav1, nav2, nav3, nav4 = st.columns([1,1,1,1])
        with nav1:
            if st.button("◀ Prev", disabled=idx==0):
                st.session_state["current_q"] = max(0, idx-1)
                st.session_state["question_start_time"] = time.time()
                st.experimental_rerun()
        with nav2:
            mark_text = "📌 Mark" if idx not in st.session_state["marked_review"] else "✅ Unmark"
            if st.button(mark_text):
                if idx in st.session_state["marked_review"]:
                    st.session_state["marked_review"].remove(idx)
                else:
                    st.session_state["marked_review"].append(idx)
                st.experimental_rerun()
        with nav3:
            if st.button("Next ▶", disabled=idx==totalq-1):
                st.session_state["current_q"] = min(totalq-1, idx+1)
                st.session_state["question_start_time"] = time.time()
                st.experimental_rerun()
        with nav4:
            if st.button("Finish"):
                st.session_state["quiz_completed"] = True
                st.experimental_rerun()

        # AI explanation
        if st.session_state.get("show_ai", {}).get(q["id"], False) or auto_show_ai:
            st.markdown("### 🤖 AI Explanation")
            st.info(q["ai_explanation"])

        # Inline question editor (quick edit)
        with st.expander("✏️ Edit question / options"):
            edited_q_text = st.text_area("Question text", value=q["question"], key=f"edit_q_{q['id']}")
            opts = q["options"].copy()
            edited_opts = {}
            for opt_letter in sorted(opts.keys()):
                edited_opts[opt_letter] = st.text_input(f"Option {opt_letter}", value=opts[opt_letter], key=f"edit_opt_{q['id']}_{opt_letter}")
            correct_sel = st.selectbox("Correct option", options=list(edited_opts.keys()), index=list(edited_opts.keys()).index(q["correct_answer"]))
            if st.button("Save edits", key=f"save_edit_{q['id']}"):
                questions[idx]["question"] = edited_q_text
                questions[idx]["options"] = edited_opts
                questions[idx]["correct_answer"] = correct_sel
                questions[idx]["ai_explanation"] = generate_ai_explanation(edited_q_text, correct_sel, edited_opts)
                st.success("Saved edits")

    # ---------- RIGHT: Analytics & Controls ----------
    with right:
        st.subheader("📊 Analytics & Actions")
        # Basic analytics: difficulty distribution, attempts
        df = questions_to_df(questions)
        # Difficulty pie
        fig1 = px.pie(df, names="difficulty", title="Difficulty distribution")
        st.plotly_chart(fig1, use_container_width=True)

        # Score gauge (live)
        if totalq:
            current_correct = sum(1 for q in questions if st.session_state["user_answers"].get(q["id"]) == q["correct_answer"])
            score_percent = (current_correct / totalq) * 100
        else:
            score_percent = 0
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score_percent,
            title={"text":"Current Score (%)"},
            gauge={"axis":{"range":[0,100]}, "bar":{"color":"darkblue"}}
        ))
        st.plotly_chart(gauge, use_container_width=True)

        # Export buttons
        st.markdown("---")
        st.markdown("### Export / Save")
        results_df = pd.DataFrame([{
            "id": q["id"],
            "question": q["question"],
            "selected": st.session_state["user_answers"].get(q["id"], ""),
            "correct": q["correct_answer"],
            "is_correct": st.session_state["user_answers"].get(q["id"], "") == q["correct_answer"]
        } for q in questions])
        csv = results_df.to_csv(index=False).encode("utf-8")
        json_export = json.dumps({"questions": questions, "answers": st.session_state["user_answers"]}, indent=2)
        st.download_button("Download results CSV", csv, file_name="quiz_results.csv", mime="text/csv")
        st.download_button("Download full JSON (questions+answers)", json_export, file_name="quiz_full.json", mime="application/json")

        # Save progress to local browser storage (via session_state persistence)
        if persist:
            st.success("Progress will persist via session state while the app is open")

        # Quick review list
        st.markdown("---")
        st.markdown("### Quick Review")
        marked = st.session_state.get("marked_review", [])
        st.write("Marked questions:", marked if marked else "None")

    # If quiz is completed show results screen
    if st.session_state.get("quiz_completed", False):
        st.balloons()
        st.markdown("## 🏁 Quiz Completed — Results")
        total = len(questions)
        correct = sum(1 for q in questions if st.session_state["user_answers"].get(q["id"]) == q["correct_answer"])
        st.metric("Score", f"{correct}/{total}", delta=f"{(correct/total*100):.1f}%")
        # show per-question breakdown
        st.dataframe(results_df)

        # Allow restart or new file
        col_a, col_b = st.columns(2)
        if col_a.button("🔄 Restart Quiz"):
            # reset answers but keep parsed questions
            st.session_state["user_answers"] = {}
            st.session_state["current_q"] = 0
            st.session_state["quiz_completed"] = False
            st.experimental_rerun()

        if col_b.button("🗑️ Clear and Upload New PDF"):
            for k in ["questions", "user_answers", "current_q", "quiz_completed", "marked_review", "uploaded_file_hash"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()

else:
    # No questions loaded
    st.info("Upload a PDF with questions structured like:\n\nQ1. What ...?\nA) ...\nB) ...\nAnswer: A")
    st.markdown("""
    **Tips for best parsing**
    - Use consistent labels: `Q1.` and `A)` or `A.` and `Answer: A`
    - Avoid multi-line options that contain `A)` inside.
    """)

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown("Built with ❤️ — PDF Quiz PRO. Pro tips: For scanned PDFs, OCR may take a while; be patient.")
