import streamlit as st
import os
import joblib
import re
import pandas as pd
from datetime import datetime
from login import user_exists, create_user, login_user

# ====== PAGE CONFIG ======
st.set_page_config(page_title="SCOPE", layout="centered")
st.title("🧠 SCOPE — Mental Health Tracker")

# ====== CUSTOM FONT & THEME ======
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body, .stApp {
            font-family: 'Quicksand', sans-serif;
            background-color: #1e1e2f !important;
            color: #f5f5f5 !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
        }

        div.stButton > button {
            background-color: #a076f9;
            color: white;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.5em 1.2em;
            border: none;
            transition: 0.3s;
        }

        div.stButton > button:hover {
            background-color: #8c5fd9;
            transform: scale(1.02);
        }

        div.stTextInput > label,
        div.stSelectbox > label,
        div.stRadio > label,
        div.stTextArea > label {
            color: #dddddd !important;
            font-weight: 600;
        }

        textarea, input {
            background-color: #2b2b3c !important;
            color: #f5f5f5 !important;
            border-radius: 10px !important;
            border: none !important;
        }

        .stAlert {
            background-color: #3b3b4e;
            border-left: 5px solid #a076f9;
            color: #f5f5f5;
        }

        .stDataFrame, .stTable {
            background-color: #2b2b3c !important;
            color: #f5f5f5 !important;
        }

        .stSelectbox, .stRadio, .stTextInput, .stTextArea {
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)

# ====== POST-LOGIN RERUN HANDLER ======
if st.session_state.get("trigger_login_rerun"):
    st.session_state["user_id"] = st.session_state.pop("temp_user_id")
    st.session_state["name"] = st.session_state.pop("temp_name")
    st.session_state.pop("trigger_login_rerun")
    st.rerun()

# ====== LOGIN SYSTEM ======
if "user_id" not in st.session_state:
    st.subheader("🔐 Login / Register")
    user_id = st.text_input("Enter your User ID")
    name = st.text_input("Enter your Name")

    if st.button("Login / Register"):
        if not user_id or not name:
            st.warning("Please enter both fields.")
        else:
            if not user_exists(user_id):
                create_user(user_id, name)
                st.success(f"New user created: {name}")
            else:
                st.success(f"Welcome back, {name}!")

            st.session_state["temp_user_id"] = user_id
            st.session_state["temp_name"] = name
            st.session_state["trigger_login_rerun"] = True
            st.rerun()

# ====== AFTER LOGIN ======
else:
    st.success(f"Welcome, {st.session_state['name']}! Feel free to submit your journal entries below.")

    BASE_DIR = os.path.dirname(__file__)
    MODEL = joblib.load(os.path.join(BASE_DIR, "model.pkl"))
    VECTORIZER = joblib.load(os.path.join(BASE_DIR, "vectorizer.pkl"))
    log_file = os.path.join(BASE_DIR, "logs", f"{st.session_state['user_id']}.csv")

    # ====== FUNCTIONS ======
    def clean_text(text):
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"[^a-zA-Z\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.lower().strip()

    def generate_summary_binary(label_counts, count):
        ctrl = label_counts.get("0", 0)
        schiz = label_counts.get("1", 0)

        if schiz >= 0.6:
            return f"Across {count} entries, a strong portion appear schizophrenia-like. Consider exploring deeper mental health support."
        elif ctrl >= 0.8:
            return f"{count} entries appear grounded, coherent, and stable — no alarming signs detected."
        else:
            return f"Your entries show a mix of emotional states. Consider continuing to track them for patterns over time."

    def predict_schizophrenia_batch(entries):
        cleaned = [clean_text(e) for e in entries]
        vectors = VECTORIZER.transform(cleaned)
        probs = MODEL.predict_proba(vectors)
        predictions = MODEL.predict(vectors).astype(int)  # ✅ Fix: ensure numeric predictions

        label_counts = pd.Series(predictions).astype(str).value_counts(normalize=True).to_dict()
        summary = generate_summary_binary(label_counts, len(entries))

        avg_prob = probs[:, 1].mean() * 100
        top_label = int(predictions.mean() >= 0.5)

        return avg_prob, top_label, summary, cleaned, predictions, probs

    def save_user_log(user_id, entries, probability, label, mood, help_status):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label_name = "Control-like" if label == 0 else "Schizophrenic-like"

        data = {
            "timestamp": [timestamp] * len(entries),
            "mood": [mood] * len(entries),
            "help_status": [help_status] * len(entries),
            "entry": entries,
            "probability": [round(probability, 2)] * len(entries),
            "prediction": [label_name] * len(entries)
        }

        df = pd.DataFrame(data)
        if os.path.exists(log_file):
            df.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df.to_csv(log_file, index=False)

    # ====== JOURNAL ENTRY SECTION ======
    st.subheader("📝 Submit Journal Entries")

    mood = st.selectbox("How are you feeling today?", [
        "🙂 Happy", "😐 Neutral", "😔 Sad", "😰 Anxious", "😡 Frustrated", "😭 Overwhelmed"
    ])

    help_status = st.radio("Have you ever sought professional help for mental health?", [
        "Yes", "No", "Prefer not to say"
    ])

    entry_count = st.selectbox("How many journal entries do you want to add today?", [1, 2, 3, 4, 5], index=0)

    entries = []
    for i in range(entry_count):
        entry = st.text_area(f"Entry {i+1}", key=f"entry_{i}", height=150)
        if entry.strip():
            entries.append(entry.strip())

    if st.button("Analyze"):
        if len(entries) < entry_count:
            st.warning("Please fill in all the journal entries before analyzing.")
        else:
            avg_prob, label, summary, cleaned, predictions, probs = predict_schizophrenia_batch(entries)

            st.subheader("🔍 Analysis Result")
            st.write(f"**Prediction Score (Schizophrenia-like):** {avg_prob:.2f}%")
            st.write("**Summary:**", summary)

            # 🧾 Entry-wise results
            if len(entries) > 1:
                st.markdown("### 🧾 Entry-wise Analysis:")
                for i, (text, pred, prob) in enumerate(zip(entries, predictions, probs[:, 1])):
                    label_text = "Schizophrenic-like" if pred == 1 else "Control-like"
                    st.write(f"**Entry {i+1}:** *{label_text}* ({prob * 100:.2f}% confidence)")

            save_user_log(
                user_id=st.session_state["user_id"],
                entries=entries,
                probability=avg_prob,
                label=label,
                mood=mood,
                help_status=help_status
            )

    # ====== VIEW HISTORY SECTION ======
    st.subheader("📜 View My Journal History")

    if st.button("Show My Logs"):
        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
            df["entry"] = df["entry"].apply(lambda x: str(x)[:100] + "..." if len(str(x)) > 100 else str(x))
            st.dataframe(df[::-1], use_container_width=True)
        else:
            st.info("No logs found yet. Submit a journal entry to start tracking.")

    # ====== DOWNLOAD LOG BUTTON ======
    st.subheader("📥 Download My Journal Log")

    if os.path.exists(log_file):
        with open(log_file, "rb") as f:
            st.download_button(
                label="📄 Download CSV",
                data=f,
                file_name=f"{st.session_state['user_id']}_scope_log.csv",
                mime="text/csv"
            )
    else:
        st.info("No logs available to download.")

    # ====== PREDICTION TRENDLINE ======
    st.subheader("📈 Mental Health Prediction Trend")

    if os.path.exists(log_file):
        df_trend = pd.read_csv(log_file)
        df_trend["timestamp"] = pd.to_datetime(df_trend["timestamp"], dayfirst=True, errors='coerce')
        df_trend = df_trend.dropna(subset=["timestamp"])
        df_trend = df_trend.sort_values("timestamp")

        st.line_chart(
            df_trend[["timestamp", "probability"]].set_index("timestamp"),
            height=300
        )
    else:
        st.info("No data available yet to show trends.")
