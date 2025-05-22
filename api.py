import requests
import streamlit as st

@st.cache_data(show_spinner="🔍 Consultando ViaCEP...")
def buscar_cep(cep: str):
    cep = cep.replace("-", "").strip()
    if len(cep) != 8 or not cep.isdigit():
        return {"erro": "CEP inválido."}
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("erro"):
            return {"erro": "CEP não encontrado."}
        return data
    except Exception as e:
        return {"erro": f"Erro ao buscar CEP: {e}"}

@st.cache_data(show_spinner="🌍 Geocodificando endereço...")
def geocodificar_endereco(endereco: str, api_key: str):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={endereco}&key={api_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] != "OK":
            return {"erro": f"Erro na geocodificação: {data['status']}"}
        loc = data["results"][0]["geometry"]["location"]
        return {"latitude": loc["lat"], "longitude": loc["lng"]}
    except Exception as e:
        return {"erro": f"Erro ao geocodificar: {e}"}

def load_api_keys():
    gemini_key = st.secrets.get("GOOGLE_API_KEY")
    geocoding_key = st.secrets.get("geocoding_api_key")
    if not gemini_key:
        st.warning("GOOGLE_API_KEY não configurada.")
    if not geocoding_key:
        st.warning("geocoding_api_key não configurada.")
    return gemini_key, geocoding_key