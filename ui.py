import streamlit as st
from app import DrowsinessSystem

st.set_page_config(
    page_title="Drowsy Driver",
    layout="wide",
)

# Initialize system
if "system" not in st.session_state:
    st.session_state.system = DrowsinessSystem()

system = st.session_state.system

st.title("🚗 Drowsy Driver")
st.markdown("### Driver Drowsiness Monitoring System")
st.markdown("---")
