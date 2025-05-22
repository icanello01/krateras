import streamlit as st

def next_step():
    steps = ["start", "form", "resultado"]
    index = steps.index(st.session_state.step)
    if index < len(steps) - 1:
        st.session_state.step = steps[index + 1]
        st.rerun()

def prev_step():
    steps = ["start", "form", "resultado"]
    index = steps.index(st.session_state.step)
    if index > 0:
        st.session_state.step = steps[index - 1]
        st.rerun()

def force_rerun_ia_analysis():
    if "analise" in st.session_state:
        del st.session_state["analise"]
    st.session_state.step = "form"
    st.rerun()