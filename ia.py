import google.generativeai as genai
import streamlit as st

@st.cache_resource
def init_gemini_models(api_key):
    if not api_key:
        return None, None
    genai.configure(api_key=api_key)
    try:
        model_text = genai.GenerativeModel("gemini-1.5-flash-latest")
        model_vision = genai.GenerativeModel("gemini-pro-vision")
        return model_text, model_vision
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {e}")
        return None, None

def process_all_analyses(image_bytes, text_model, vision_model):
    result = {"imagem": "Não analisada", "insights": "Não gerado"}
    if vision_model and image_bytes:
        try:
            resp = vision_model.generate_content([
                "Descreva o buraco nesta imagem para um relatório técnico.",
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            result["imagem"] = resp.text
        except Exception as e:
            result["imagem"] = f"Erro: {e}"
    if text_model:
        try:
            resp = text_model.generate_content("Gere um resumo para equipe de obras.")
            result["insights"] = resp.text
        except Exception as e:
            result["insights"] = f"Erro: {e}"
    return result