import streamlit as st
from app import DrowsinessSystem

# Page config
st.set_page_config(
    page_title="Drowsy Driver",
    layout="wide",
)

# Initialize system
if "system" not in st.session_state:
    st.session_state.system = DrowsinessSystem()

system = st.session_state.system

# Dark theme styling
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
    .stButton>button {
        background-color: #00C853;
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("🚗 Drowsy Driver")
st.markdown("### Driver Drowsiness Monitoring System")
st.markdown("---")

# Layout
col1, col2 = st.columns([2, 1])

# ======================
# LEFT: DASHBOARD
# ======================
with col1:
    st.subheader("📊 Live Status")

    status = system.get_status()

    ear = status.get("ear", 0)
    state = status.get("state", "NORMAL")
    running = status.get("running", False)

    st.markdown(f"### EAR Value: {ear:.2f}")

    # Color logic
    if state == "NORMAL":
        color = "#00C853"
    elif state == "WARNING":
        color = "#FFD600"
    else:
        color = "#FF1744"

    # State display
    st.markdown(
        f"<h2 style='color:{color}; text-align:center;'>{state}</h2>",
        unsafe_allow_html=True
    )

    # Running status
    if running:
        st.success("System Running")
    else:
        st.error("System Stopped")

# ======================
# RIGHT: CONTROLS
# ======================
with col2:
    st.subheader("🎛 Controls")

    start = st.button("▶ Start System")
    stop = st.button("⏹ Stop System")

    if start:
        system.start_system()

    if stop:
        system.stop_system()