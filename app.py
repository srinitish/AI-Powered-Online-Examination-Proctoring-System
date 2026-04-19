import streamlit as st
import cv2
import pandas as pd
import time
from detector import ExamDetector

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="AI Exam Monitoring System",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Exam Monitoring System")

# ---------------------------
# Session State
# ---------------------------
if "exam_running" not in st.session_state:
    st.session_state.exam_running = False

if "detector" not in st.session_state:
    st.session_state.detector = ExamDetector()

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Exam Controls")

start_exam = st.sidebar.button("▶ Start Exam")
stop_exam = st.sidebar.button("⏹ Stop Exam")

if start_exam:
    st.session_state.exam_running = True

if stop_exam:
    st.session_state.exam_running = False

# ---------------------------
# Dashboard Layout
# ---------------------------
col1, col2 = st.columns(2)

status_box = col1.empty()
violation_box = col2.empty()

st.subheader("Live Monitoring")

frame_window = st.empty()

st.subheader("Violation Dashboard")

log_table = st.empty()

# ---------------------------
# Camera
# ---------------------------
if st.session_state.exam_running:

    cap = cv2.VideoCapture(0)

    while st.session_state.exam_running:

        ret, frame = cap.read()

        if not ret:
            st.error("Camera not detected")
            break

        detector = st.session_state.detector

        frame = detector.process(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame_window.image(rgb, channels="RGB")

        summary = detector.get_summary()

        status_box.metric(
            "Exam Status",
            summary["status"]
        )

        violation_box.metric(
            "Total Violations",
            summary["mal_count"]
        )

        if summary["violation_log"]:
            df = pd.DataFrame(summary["violation_log"])
            log_table.dataframe(df, use_container_width=True)

        time.sleep(0.03)

    cap.release()

else:
    st.info("Click **Start Exam** to begin monitoring.")