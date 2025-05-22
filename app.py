import streamlit as st
from utils.api import load_api_keys, init_gemini_models
from utils.helpers import next_step, prev_step, force_rerun_ia_analysis
from utils.ia import process_all_analyses

# Configuração da página
st.set_page_config(page_title="Krateras 🚀✨🔒", page_icon="🚧", layout="wide", initial_sidebar_state="expanded")

# Carregando CSS customizado
with open("styles/theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inicialização
st.title("Krateras 🚀✨🔒")
st.subheader("O Especialista Robótico de Denúncia de Buracos")

# Inicialização de sessão
if "step" not in st.session_state:
    st.session_state.step = "start"

if st.session_state.step == "start":
    st.info("Bem-vindo ao Krateras! Vamos juntos melhorar as ruas da sua cidade.")
    if st.button("🚀 Iniciar Missão Denúncia!", use_container_width=True):
        st.success("Sistema inicializado com sucesso!")
        next_step()

# Outras etapas seriam chamadas dinamicamente