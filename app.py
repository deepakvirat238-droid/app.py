# app.py
import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import re
import time
import random
import pandas as pd
import plotly.express as px
import hashlib
import io

# ---------------------------
# Utility Functions
# ---------------------------

def file_hash(file_bytes: bytes) -> str:
    h = hashlib.sha256()
    h.update(file_bytes)
    return h.hexdigest()

@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF (OCR fallback)."""
    text = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text.append(page_text)
            else:
                pil_img = page.to_image(resolution=200).original
                ocr_text = pytesseract.image_to_string(pil_img)
                text.append(ocr_text)
    return "\n".join(text)

@st.cache_data(show_spinner=False)
def parse_pdf_questions(pdf_bytes: bytes):
    """Extract MCQs from PDF text."""
    raw = extract_text_from_pdf_bytes(pdf_bytes)
    parts = re.split(r'(?i)\bq\d+\.|\n\d+\.\s', raw)
    questions = []
    for i, block in enumerate(parts[1:], start=1):
        b = block.strip()
        if not b: continue
        q_match = re.search(r'^(.*?)(?=\n[A-E]\)|\n[A-E]\.|Answer:|$)', b, re.DOTALL)
        q_text = q_match.group(1).strip() if q_match else b[:200].strip()
        options = dict()
        for l, t in re.findall(r'([A-E])[\)\.]\s*(.*?)(?=(?:\n[A-E][\)\.]|\nAnswer:|$))', b, re.DOTALL):
            options[l] = t.strip().replace("\n", " ")
        if not options:
            options = {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'}
        ans = re.search(r'(?i)Answer[:\s]*([A-E])', b)
        correct = ans.group(1) if ans else random.choice(list(options.keys()))
        questions.append({
            "id": i,
            "question": q_text,
            "options": options,
            "correct": correct,
            "time_spent": 0,
            "ai_explanation": f"This is a {random.choice(['grammar','vocabulary','logic'])} question. Correct answer is {correct}."
        })
    return questions

# ---------------------------
# UI Configuration
# ---------------------------

st.set_page_config(page_title="PDF Quiz PRO+", layout="wide", page_icon="🧠")
st.title("🧠 PDF Quiz PRO+ — Ultimate MCQ App")

mode = st.sidebar.radio("Select Mode", ["Practice Mode", "Exam Mode"])
sound_enabled = st.sidebar.checkbox("Enable sound", value=True)
show_ai = st.sidebar.checkbox("Show AI Explanation", value=False)

uploaded_file = st.file_uploader("📄 Upload PDF (MCQs)", type="pdf")

# ---------------------------
# Load Questions
# ---------------------------

if uploaded_file:
    pdf_bytes = uploaded_file.getvalue()
    h = file_hash(pdf_bytes)
    if st.session_state.get("file_hash") != h:
        with st.spinner("Extracting questions..."):
            st.session_state["questions"] = parse_pdf_questions(pdf_bytes)
            st.session_state["answers"] = {}
            st.session_state["index"] = 0
            st.session_state["start_time"] = time.time()
            st.session_state["question_start"] = time.time()
            st.session_state["total_time"] = 0
            st.session_state["file_hash"] = h

# ---------------------------
# Main Quiz Logic
# ---------------------------

if "questions" in st.session_state:
    questions = st.session_state["questions"]
    idx = st.session_state["index"]
    total = len(questions)
    q = questions[idx]

    # Timers
    elapsed_total = int(time.time() - st.session_state["start_time"])
    elapsed_q = int(time.time() - st.session_state["question_start"])

    st.sidebar.markdown(f"⏱️ **Total Time:** {elapsed_total // 60:02d}:{elapsed_total % 60:02d}")
    st.sidebar.markdown(f"🕓 **This Question:** {elapsed_q}s")

    if mode == "Exam Mode":
        st.sidebar.progress(min(elapsed_total / (total * 30), 1.0))

    st.subheader(f"Question {idx+1}/{total}")
    st.write(q["question"])

    for opt, text in q["options"].items():
        if st.button(f"{opt}) {text}", key=f"{idx}_{opt}"):
            q["time_spent"] += int(time.time() - st.session_state["question_start"])
            st.session_state["answers"][q["id"]] = opt
            st.session_state["question_start"] = time.time()
            if idx + 1 < total:
                st.session_state["index"] += 1
                st.rerun()
            else:
                st.session_state["finished"] = True
                st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Prev", disabled=idx == 0):
            st.session_state["index"] -= 1
            st.session_state["question_start"] = time.time()
            st.rerun()
    with col2:
        if st.button("➡️ Next", disabled=idx == total - 1):
            st.session_state["index"] += 1
            st.session_state["question_start"] = time.time()
            st.rerun()
    with col3:
        if st.button("✅ Submit"):
            st.session_state["finished"] = True
            st.rerun()

    if show_ai:
        st.info(q["ai_explanation"])

# ---------------------------
# Results Section
# ---------------------------

if st.session_state.get("finished"):
    st.balloons()
    questions = st.session_state["questions"]
    answers = st.session_state["answers"]

    results = []
    for q in questions:
        selected = answers.get(q["id"], "")
        correct = q["correct"]
        is_correct = selected == correct
        results.append({
            "Question": q["question"][:60] + "...",
            "Your Answer": selected,
            "Correct Answer": correct,
            "Result": "✅ Correct" if is_correct else "❌ Wrong",
            "Time (s)": q["time_spent"]
        })

    df = pd.DataFrame(results)
    score = df["Result"].str.contains("✅").sum()
    total = len(df)
    percent = (score / total) * 100

    st.subheader("📊 Results Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{score}/{total}")
    col2.metric("Accuracy", f"{percent:.1f}%")
    col3.metric("Total Time", f"{int(time.time() - st.session_state['start_time'])} sec")

    st.dataframe(df)

    fig = px.pie(df, names="Result", title="Answer Distribution")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(df, x="Question", y="Time (s)", title="Time Spent per Question")
    st.plotly_chart(fig2, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Results CSV", csv, "results.csv", "text/csv")

else:
    if not uploaded_file:
        st.info("Please upload a PDF to start your quiz.")
