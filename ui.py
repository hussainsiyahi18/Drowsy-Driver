import streamlit as st
import threading
from app import DrowsinessSystem

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Drowsy Driver",
    layout="wide",
)

# -----------------------------
# Session State Init
# -----------------------------
if "system" not in st.session_state:
    st.session_state.system = DrowsinessSystem()

if "thread" not in st.session_state:
    st.session_state.thread = None

system = st.session_state.system

# -----------------------------
# Styling (Premium Dark UI)
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    h1, h2, h3 {
        color: white;
        text-align: center;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Header
# -----------------------------
st.title("🚗 Drowsy Driver")
st.markdown("### Driver Drowsiness Monitoring System")
st.markdown("---")

# -----------------------------
# Layout
# -----------------------------
col1, col2 = st.columns([2, 1])

# ======================
# LEFT: DASHBOARD
# ======================
with col1:
    st.subheader("📊 Live Status")

    status = system.get_status()
    ear = status.get("ear", 0.0)
    state = status.get("state", "NORMAL")
    running = status.get("running", False)

    # EAR display
    st.markdown(f"### EAR Value: `{ear:.2f}`")

    # Color logic
    if state == "NORMAL":
        color = "#00C853"
    elif state == "WARNING":
        color = "#FFD600"
    else:
        color = "#FF1744"

    # State display
    st.markdown(
        f"<h1 style='color:{color};'>{state}</h1>",
        unsafe_allow_html=True
    )

    # Status indicator
    if running:
        st.success("🟢 System Running")
    else:
        st.error("🔴 System Stopped")

    # Alert messages
    if state == "WARNING":
        st.warning("Driver getting drowsy")
    elif state == "CRITICAL":
        st.error("Wake up!")
    elif state == "EMERGENCY":
        contact = system.get_emergency_contact() or "Emergency Contact"
        st.error(f"🚨 Calling {contact}")

# ======================
# RIGHT: CONTROLS
# ======================
with col2:
    st.subheader("🎛 Controls")

    start = st.button("▶ Start System")
    stop = st.button("⏹ Stop System")

    # Start system in background thread
    if start:
        if not running:
            system.start_system()

            def run_system():
                system.run()

            thread = threading.Thread(target=run_system)
            thread.daemon = True
            thread.start()

            st.session_state.thread = thread

    # Stop system
    if stop:
        system.stop_system()

    st.markdown("---")

    # ======================
    # SETTINGS
    # ======================
    st.subheader("⚙ Settings")

    ear = st.slider("EAR Threshold", 0.15, 0.35, 0.25, 0.01)
    warning = st.slider("Warning Frames", 10, 50, 25)
    critical = st.slider("Critical Frames", 20, 100, 50)
    emergency = st.slider("Emergency Frames", 40, 150, 90)

    if st.button("Apply Settings"):
        system.update_settings(ear, warning, critical, emergency)

    st.markdown("---")

    # ======================
    # CONTACT
    # ======================
    st.subheader("📞 Emergency Contact")

    contact_input = st.text_input("Enter Phone Number")

    if st.button("Save Contact"):
        system.set_emergency_contact(contact_input)

    current_contact = system.get_emergency_contact()
    if current_contact:
        st.success(f"Saved: {current_contact}")

    st.markdown("---")

    # ======================
    # SOUND TOGGLE
    # ======================
    st.subheader("🔊 Sound")

    sound_toggle = st.toggle("Enable Sound", value=True)

    system.set_sound(sound_toggle)

# -----------------------------
# Cloud Warning
# -----------------------------
st.markdown("---")
st.warning("⚠️ Live camera detection may not work on cloud. Run locally for full functionality.")