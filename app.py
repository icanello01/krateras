# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v3.2 - Streamlit Interphase Edition Refined)

Bem-vindo à versão visual e aprimorada do Krateras, agora com um visual inspirado
no elegante template Interphase, com estilos CSS refinados para maior compatibilidade!

Tecnologias: Python, Streamlit, Google Gemini API (Vision & Pro), Google Geocoding API, ViaCEP, Google Street View Static API, CSS Custom.
Objetivo: Coletar dados estruturados e ricos de denúncias de buracos, analisar texto E imagem
com IA, obter visualização Street View, gerar relatórios detalhados, priorizados e acionáveis,
incluindo localização visual em mapa, imagem Street View e resumo inteligente.

Com design arrojado e a mais alta tecnologia, vamos juntos consertar essas ruas!
Iniciando sistemas visuais, robóticos e de inteligência artificial...
"""

import streamlit as st
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import re
import json
import pandas as pd
from PIL import Image # Para trabalhar com imagens carregadas pelo usuário
import io # Para ler bytes da imagem carregada

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Krateras 🚀✨🔒 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados (Inspirado no Template Interphase - REFINADO) ---
# Definindo variáveis CSS para as cores principais do tema Interphase
st.markdown("""
<style>
    :root {
        --color-primary: #4A90E2; /* Azul principal (similar ao template) */
        --color-secondary: #A569BD; /* Roxo secundário (adaptação do template) */
        --color-text: #333; /* Cor de texto mais escura */
        --color-light-text: #555; /* Cor de texto um pouco mais clara */
        --color-background-light: #F8F9FA; /* Fundo claro para seções */
        --color-background-mid: #E9ECEF; /* Fundo um pouco mais escuro para contraste */
        --color-border: #CED4DA; /* Cor de borda sutil */
        --color-success: #28A745; /* Verde Bootstrap */
        --color-warning: #FFC107; /* Amarelo Bootstrap */
        --color-error: #DC3545; /* Vermelho Bootstrap */
        --color-info: #17A2B8; /* Azul claro Bootstrap */
    }

    /* Importar fonte (Ex: Open Sans, popular em templates como o Interphase) */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        margin: 0;
        padding: 0;
        font-family: 'Open Sans', sans-serif;
        color: var(--color-text);
        background: linear-gradient(to bottom right, #4e54c8, #8f94fb) !important; /* Gradiente inspirado no template */
        background-attachment: fixed; /* Faz o gradiente cobrir a página inteira */
        min-height: 100vh; /* Garante que o background cubra a altura mínima */
        width: 100%;
        overflow-x: hidden; /* Evita scroll horizontal devido ao background fixo */
    }


    /* Target the main content block within the view container */
    /* This selector is more likely to target the actual content area receiving padding and background */
     [data-testid="stAppViewContainer"] > .st-emotion-cache-xyz { /* Note: xyz part is unstable, may need adjustment */
          /* Attempting to target a common intermediate div */
         background-color: rgba(255, 255, 255, 0.95); /* Fundo semi-transparente para o conteúdo */
         padding: 2rem 3rem;
         border-radius: 10px;
         box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
         margin-top: 2rem;
         margin-bottom: 2rem;
         max-width: 1000px; /* Limita a largura do conteúdo como em templates */
         margin-left: auto;
         margin-right: auto;
         box-sizing: border-box; /* Include padding and border in the element's total width and height */
     }
    /* Fallback/alternative selector for the main content if the above doesn't work */
     [data-testid="stVerticalBlock"] {
          box-sizing: border-box !important;
          /* Ensure this block gets padding and centered if the parent selector failed */
          /* Test and adjust these styles if the above selector doesn't apply */
     }


     /* Ajuste para o sidebar se ele existir */
     [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9); /* Fundo semi-transparente para o sidebar */
     }


    h1, h2, h3, h4 {
        color: var(--color-primary); /* Títulos com a cor primária */
        font-weight: 700; /* Bold */
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    h1 { font-size: 2.5em; }
    h2 { font-size: 1.8em; }
    h3 { font-size: 1.4em; }
    h4 { font-size: 1.1em; }


    /* Botões */
    /* Target base button container for consistency */
    [data-testid="baseButton-secondary"] button { /* Applies to st.button */
        background-color: var(--color-primary); /* Fundo com cor primária */
        color: white;
        font-weight: bold;
        border-radius: 25px; /* Mais arredondado */
        padding: 0.8rem 1.5rem; /* Padding maior */
        margin-top: 1.5rem; /* Margem maior */
        margin-right: 0.5rem;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        min-width: 150px; /* Ensure a minimum size */
        text-align: center;
    }
    [data-testid="baseButton-secondary"] button:hover {
        background-color: #3A7AD2; /* Um tone ligeiramente diferente no hover */
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    [data-testid="baseButton-secondary"] button:active {
         background-color: #2A5BA2;
         box-shadow: none;
    }
    /* Style for form submit button if it has a different testid */
     [data-testid="FormSubmitButton"] button {
         background-color: var(--color-secondary); /* Cor secundária para submeter form */
         /* Inherits other styles from baseButton if applied correctly */
     }
     [data-testid="FormSubmitButton"] button:hover {
         background-color: #8E44AD; /* Darker secondary on hover */
     }


    /* Inputs de Texto, Número, Área de Texto */
    /* Target the input/textarea elements directly */
    input[type="text"], input[type="number"], textarea {
        border-radius: 5px;
        padding: 0.8rem 1rem; /* Padding interno */
        border: 1px solid var(--color-border);
        width: 100%; /* Ocupa largura total */
        box-sizing: border-box; /* Inclui padding na largura */
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
     input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
         border-color: var(--color-primary); /* Borda primária no focus */
         box-shadow: 0 0 5px rgba(var(--color-primary-rgb, 74, 144, 226), 0.5); /* Sombra no focus */
         outline: none; /* Remove outline padrão */
     }
     /* Add rgb variables for shadow if needed */
     :root {
         --color-primary-rgb: 74, 144, 226;
     }


     /* Selectboxes e Radios */
     [data-testid="stSelectbox"] > div > div, [data-testid="stRadio"] > div {
         margin-bottom: 1rem;
     }
      [data-testid="stSelectbox"] > div > div > div { /* The box displaying selected value */
          border-radius: 5px;
          padding: 0.8rem 1rem;
          border: 1px solid var(--color-border);
          background-color: white;
          transition: border-color 0.2s ease-in-out;
      }
      [data-testid="stSelectbox"] > div > div:focus-within > div { /* Focus on selectbox */
          border-color: var(--color-primary);
      }
     [data-testid="stRadio"] label { /* Labels for radio buttons */
          margin-bottom: 0.5rem;
     }


    /* Feedback Boxes (Info, Success, Warning, Error) */
    /* These selectors are unstable! */
    .css-1aumqxt { border-left: 5px solid var(--color-info) !important; background-color: #E6F3FF; color: var(--color-light-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.info */
    .css-1r6cdft { border-left: 5px solid var(--color-warning) !important; background-color: #FFF8E1; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.warning */
    .css-t9s6qg { border-left: 5px solid var(--color-error) !important; background-color: #FFEBEE; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.error */
    .css-1u3jtzg { border-left: 5px solid var(--color-success) !important; background-color: #F1F8E9; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.success */


    /* Spinners */
    .stSpinner > div > div {
        border-top-color: var(--color-primary) !important;
    }

    /* Expanders (Menus Sanfona - estilizados como blocos) */
    .streamlit-expanderHeader {
        font-size: 1.2em !important;
        font-weight: bold !important;
        color: var(--color-primary) !important;
        background-color: var(--color-background-light); /* Fundo claro */
        border-radius: 8px;
        padding: 1rem;
        margin-top: 2rem;
        border: 1px solid var(--color-border);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease-in-out;
    }
    .streamlit-expanderHeader:hover {
         background-color: var(--color-background-mid); /* Leve escurecimento no hover */
    }
    .streamlit-expanderContent {
         background-color: #FFFFFF; /* Fundo branco para o conteúdo */
         padding: 1.5rem;
         border-left: 1px solid var(--color-border);
         border-right: 1px solid var(--color-border);
         border-bottom: 1px solid var(--color-border);
         border-radius: 0 0 8px 8px;
         margin-bottom: 1rem;
         box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08); /* Adiciona sombra também no conteúdo */
    }

    /* Separadores */
    hr {
        margin-top: 2em;
        margin-bottom: 2em;
        border: 0;
        border-top: 1px solid var(--color-border);
    }

    /* Imagem upload area */
    [data-testid="stFileUploader"] label {
        font-weight: bold;
        color: var(--color-light-text);
    }

    /* Centralizar imagens e mapas (using data-testid where available) */
     [data-testid="stImage"], [data-testid="stMap"], [data-testid="stDeckGlChart"] {
          display: block;
          margin-left: auto;
          margin-right: auto;
          max-width: 100%;
          margin-top: 1rem;
          margin-bottom: 1rem;
          border-radius: 8px; /* Arredonda cantos de imagens/mapas */
          overflow: hidden; /* Esconde partes fora do border-radius */
     }
     /* Ensure iframes inside components also respect max-width and are centered */
     [data-testid="stComponentsV1"] iframe {
          display: block;
          margin-left: auto;
          margin-right: auto;
          max-width: 100%;
          border-radius: 8px; /* Arredonda cantos do iframe */
          overflow: hidden;
     }


</style>
""", unsafe_allow_html=True)


# --- Inicialização de Estado da Sessão ---
# Gerencia o fluxo da aplicação web e os dados coletados/processados
if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'denuncia_completa' not in st.session_state:
    st.session_state.denuncia_completa = {}
if 'api_keys_loaded' not in st.session_state:
    st.session_state.api_keys_loaded = False
if 'gemini_pro_model' not in st.session_state: # Modelo para texto
    st.session_state.gemini_pro_model = None
if 'gemini_vision_model' not in st.session_state: # Modelo para visão
    st.session_state.gemini_vision_model = None
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
# Adicionado estado para Street View image data
if 'streetview_image_data' not in st.session_state:
    st.session_state.streetview_image_data = None


# --- 🔑 Gerenciamento de Chaves Secretas (Streamlit Secrets) ---
# Utiliza o .streamlit/secrets.toml para carregar chaves de forma segura

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    """
    Tenta obter as chaves de API do Google Gemini e Google Maps Geocoding de Streamlit Secrets.
    Retorna None se não encontradas.
    """
    # Chaves definidas no .streamlit/secrets.toml
    gemini_key = st.secrets.get('GOOGLE_API_KEY') # Usada para Gemini-Pro e Gemini-Vision
    geocoding_key = st.secrets.get('geocoding_api_key') # Usada para Geocoding, Embed e Street View Static

    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA do Gemini estarão desabilitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática, Visualização Google Maps Embed e Street View Static estarão desabilitadas.")
        st.info("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit (se ainda não existir a pasta `.streamlit`) com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\n**IMPORTANTE:** Não comite o arquivo `secrets.toml` para repositórios públicos no GitHub! O Streamlit Cloud tem uma interface segura para adicionar estes segredos.")
        st.info("❗ As APIs Google Maps (Geocoding, Embed, Street View Static) PODE gerar custos. Verifique a precificação do Google Cloud e habilite-as no seu projeto Google Cloud Platform (Console -> APIs & Services -> Library). O erro 'This API project is not authorized to use this API' geralmente significa que a API específica não está habilitada ou autorizada para a chave.")


    return gemini_key, geocoding_key

# --- Inicializar APIs (Cacheado para performance) ---

@st.cache_resource
def init_gemini_models(api_key: Optional[str]) -> tuple[Optional[genai.GenerativeModel], Optional[genai.GenerativeModel]]:
    """Inicializa os modelos Google Gemini (Pro e Vision) com cache."""
    if not api_key:
        return None, None # Retorna None para ambos se a chave não for fornecida

    model_pro = None
    model_vision = None

    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models()]

        # Inicializar Gemini-Pro (ou Flash) para texto
        preferred_text_models: list[str] = ['gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        text_model_name: Optional[str] = None
        for pref_model in preferred_text_models:
            if f'models/{pref_model}' in available_models:
                text_model_name = pref_model
                break
            if pref_model in available_models:
                 text_model_name = pref_model
                 break

        if text_model_name:
             model_pro = genai.GenerativeModel(text_model_name)
             st.success(f"✅ Conexão com Google Gemini (Texto) estabelecida usando modelo '{text_model_name}'.")
        else:
             st.warning("⚠️ Nenhum modelo de texto Gemini compatível encontrado na sua conta.")


        # Inicializar Gemini-Vision para análise de imagem
        vision_model_name = 'gemini-pro-vision'
        if f'models/{vision_model_name}' in available_models or vision_model_name in available_models:
            model_vision = genai.GenerativeModel(vision_model_name)
            st.success(f"✅ Conexão com Google Gemini (Visão) estabelecida usando modelo '{vision_model_name}'.")
        else:
            st.warning(f"⚠️ Modelo Gemini Vision ('{vision_model_name}') não encontrado ou compatível na sua conta. Análise de imagem desabilitada.")


        if model_pro or model_vision:
            st.info("A IA está online e pensativa!")

        return model_pro, model_vision

    except Exception as e:
        st.error(f"❌ ERRO no Painel de Controle Gemini: Falha na inicialização dos modelos Google Gemini. Verifique sua chave e status do serviço.")
        st.exception(e)
        return None, None


# --- Funções de API Call (Cacheado para resultados estáveis por sessão) ---

@st.cache_data(show_spinner="⏳ Interrogando o ViaCEP...")
def buscar_cep(cep: str) -> Dict[str, Any]:
    """Consulta a API ViaCEP para obter dados de endereço com tratamento de erros."""
    cep_limpo = cep.replace("-", "").replace(".", "").strip()
    if len(cep_limpo) != 8 or not cep_limpo.isdigit():
        return {"erro": "Formato de CEP inválido. Precisa de 8 dígitos, amigão!"}

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if 'erro' in data and data['erro'] is True:
            return {"erro": f"CEP '{cep_limpo}' não encontrado no ViaCEP. Ele se escondeu! 🧐"}
        if not data.get('logradouro') or not data.get('localidade') or not data.get('uf'):
             return {"erro": f"CEP '{cep_limpo}' encontrado, mas os dados de endereço estão incompletos. O ViaCEP só contou parte da história!"}
        return data
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao buscar o CEP '{cep_limpo}'. O ViaCEP não responde! 😴"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro na comunicação com o ViaCEP para o CEP '{cep_limpo}': {e}. Problemas na linha!"}
    except Exception as e:
         return {"erro": f"Ocorreu um erro inesperado ao buscar o CEP '{cep_limpo}': {e}. Isso não estava nos meus manuais!"}

# A geocodificação é chamada no fluxo principal, não cacheada separadamente
def geocodificar_endereco(rua: str, numero: str, cidade: str, estado: str, api_key: str) -> Dict[str, Any]:
    """Tenta obter coordenadas geográficas e link Google Maps via Google Maps Geocoding API."""
    if not api_key:
        return {"erro": "Chave de API de Geocodificação não fornecida."}
    if not rua or not numero or not cidade or not estado:
         return {"erro": "Dados de endereço insuficientes (requer rua, número, cidade, estado) para geocodificar."}

    address = f"{rua}, {numero}, {cidade}, {estado}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&key={api_key}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            status = data.get('status', 'STATUS DESCONHECIDO')
            error_msg = data.get('error_message', 'Sem mensagem adicional.')
            return {"erro": f"Geocodificação falhou. Status: {status}. Mensagem: {error_msg}"}
        if not data['results']:
             return {"erro": "Geocodificação falhou. Nenhum local exato encontrado para o endereço fornecido."}

        location = data['results'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = data['results'][0].get('formatted_address', address)

        # O link embed usa a mesma chave da Geocoding API, mas a Maps Embed API precisa estar habilitada
        google_embed_link = None
        if api_key: # Verifica se a chave existe antes de tentar gerar o link embed
             google_embed_link = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"

        return {
            "latitude": lat,
            "longitude": lng,
            "endereco_formatado_api": formatted_address,
            "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
            "google_embed_link_gerado": google_embed_link # Pode ser None se chave faltar/API desabilitada
        }
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao tentar geocodificar: {address}"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro na comunicação com a API de Geocodificação: {address}. Detalhes: {e}"}
    except Exception as e:
        return {"erro": f"Ocorreu um erro inesperado durante a geocodificação: {address}. Detalhes: {e}"}

# --- Função: Obter Imagem Street View ---
@st.cache_data(show_spinner="📸 Obtendo imagem Street View do local...")
def get_street_view_image(lat: float, lon: float, api_key: Optional[str], size: str = "600x400", heading: int = 0) -> Dict[str, Any]:
    """
    Tenta obter uma imagem Street View estática para as coordenadas fornecidas.
    Retorna os bytes da imagem ou um dicionário de erro.
    """
    if not api_key:
        return {"erro": "Chave de API de Geocodificação/Street View não fornecida."}

    # Construir a URL da Street View Static API
    location = f"{lat},{lon}"
    # Usamos um heading fixo (0=Norte) como padrão. Ajuste se necessário.

    url = f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={location}&heading={heading}&key={api_key}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status() # Lança exceção para status de erro (4xx ou 5xx)

        # A API Street View Static retorna uma imagem ou um erro 400/500 (404 para no coverage)
        if response.content and response.headers.get('Content-Type', '').startswith('image'):
             return {"image_bytes": response.content}
        else:
             try:
                  # Tenta ler o conteúdo como texto para mensagens de erro da API
                  error_text = response.text
                  if "No Street View images found" in error_text:
                      return {"erro": "Nenhuma imagem Street View encontrada para este local (Falta de cobertura?)."}
                  elif response.status_code == 403: # Forbidden - Chave não autorizada ou API não habilitada
                       return {"erro": f"Erro 403 (Forbidden): A chave de API não está autorizada a usar a Street View Static API. Verifique se a 'Street View Static API' está habilitada e autorizada para sua chave no Google Cloud."}
                  else:
                      return {"erro": f"Resposta da API Street View não é uma imagem. Status: {response.status_code}. Conteúdo: {error_text[:200]}..."}
             except Exception:
                  return {"erro": f"Resposta da API Street View inesperada. Status: {response.status_code}. (Não foi possível ler o conteúdo como texto)."}


    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao obter Street View para {location}."}
    except requests.exceptions.RequestException as e:
        # Captura 404 (Not Found) que geralmente significa sem cobertura Street View
        if e.response is not None and e.response.status_code == 404:
             return {"erro": "Nenhuma imagem Street View encontrada para este local (Erro 404 - Sem cobertura?)."}
        elif e.response is not None and e.response.status_code == 403:
             return {"erro": f"Erro 403 (Forbidden): A chave de API não está autorizada a usar a Street View Static API. Verifique se a 'Street View Static API' está habilitada e autorizada para sua chave no Google Cloud."}
        else:
             return {"erro": f"Erro na comunicação com a API Street View para {location}: {e}. Problemas na linha!"}
    except Exception as e:
         return {"erro": f"Ocorreu um erro inesperado durante a obtenção de Street View para {location}: {e}. Isso não estava nos meus manuais!"}


# --- Funções de Análise de IA (Cacheado para resultados estáveis por sessão, exceto análise de imagem) ---
# Safety settings configuradas para permitir discussões sobre perigos na rua
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Não cachear a análise de imagem diretamente aqui, será chamada no fluxo principal se houver imagem
def analyze_image_with_gemini_vision(image_bytes: bytes, model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini Vision para analisar uma imagem e extrair características do buraco."""
    if not model:
        return {"image_analysis": "🤖 Análise de imagem via IA indisponível (Motor Gemini Vision offline)."}
    if not image_bytes:
         return {"image_analysis": "🔍 Nenhuma imagem fornecida para análise de IA."}

    try:
        # O Gemini Vision aceita bytes da imagem
        image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}] # Assumindo que a imagem é JPG/JPEG

        prompt = [
            "Analise a imagem fornecida de um buraco em uma estrada. Descreva as características visíveis relevantes para um relatório de reparo de estrada. Concentre-se em:",
            "- Tamanho estimado (pequeno, médio, grande, diâmetro em relação a objetos comuns se visível)",
            "- Profundidade estimada (raso, fundo, em relação a objetos visíveis)",
            "- Presença de água ou umidade",
            "- Quaisquer perigos visíveis óbvios ou pistas de contexto na vizinhança imediata do próprio buraco (por exemplo, pavimento rachado ao redor, detritos)",
            "Forneça uma análise textual concisa baseada EXCLUSIVAMENTE no conteúdo da imagem.",
            image_parts[0] # Adiciona a imagem ao prompt
        ]

        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)

        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"image_analysis": f"❌ Análise de imagem bloqueada pelos protocolos de segurança do Gemini Vision. Motivo: {block_reason}"}

        return {"image_analysis": response.text.strip()}
    except Exception as e:
        return {"image_analysis": f"❌ Erro ao analisar a imagem com IA: {e}"}


@st.cache_data(show_spinner="🧠 Executando análise profunda dos dados do buraco com IA Gemini...")
def analisar_dados_com_gemini(_dados_buraco: Dict[str, Any], _image_analysis_ia: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini (texto) para analisar dados estruturados, observações e análise de imagem."""
    if not _model:
        return {"insights": "🤖 Análise de dados via IA indisponível (Motor Gemini Texto offline)."}

    # Formatar os dados estruturados e observações para o prompt
    structured_details = _dados_buraco.get('structured_details', {})
    observacoes_adicionais = _dados_buraco.get('observacoes_adicionais', 'Sem observações adicionais.')

    structured_text = "Detalhes Estruturados Fornecidos pelo Usuário:\n"
    for key, value in structured_details.items():
         # Trata listas (como perigos) para um formato legível
         if isinstance(value, list):
              value_str = ", ".join(value) if value else "Nenhum selecionado"
         else:
              value_str = value if value else "Não informado"
         # Traduz as chaves para o prompt de forma mais amigável (manter consistência com os inputs)
         key_translated = {
             'tamanho': 'Tamanho Estimado',
             'perigo': 'Nível de Perigo',
             'profundidade': 'Profundidade Estimada',
             'presenca_agua': 'Presença de Água',
             'contexto': 'Contexto/Histórico',
             'perigos_detalhados': 'Perigos e Impactos Detalhados (Selecionados)',
             'identificadores_visuais': 'Identificadores Visuais Adicionais',
         }.get(key, key) # Usa a chave original se não houver tradução

         # Só adiciona ao texto se o valor não for o padrão "Não Informado" ou vazio (para texto libre)
         if value and value != 'Não Informado':
             structured_text += f"- {key_translated}: {value_str}\n"
         elif isinstance(value, list) and value:
             structured_text += f"- {key_translated}: {value_str}\n"


    if structured_text == "Detalhes Estruturados Fornecidos pelo Usuário:\n":
         structured_text += "Nenhum detalhe estruturado relevante informado pelo usuário."


    # Adiciona a análise de imagem ao contexto da IA, se disponível
    image_analysis_text = _image_analysis_ia.get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    if "Análise de imagem via IA indisponível" in image_analysis_text or "Nenhuma imagem fornecida" in image_analysis_text or "Erro ao analisar a imagem" in image_analysis_text:
         image_context = "Nota: Análise de imagem do usuário não foi realizada ou está indisponível."
    else:
         image_context = f"Insights da Análise de Imagem do Usuário (IA Gemini Vision):\n{image_analysis_text}"


    prompt = f"""
    Analise os seguintes dados estruturados, observações adicionais e (se disponível) a análise de uma imagem carregada pelo usuário, todos relacionados a uma denúncia de um buraco em uma rua. Seu objetivo é extrair insights CRUCIAIS e gerar uma análise detalhada objetiva para um sistema de reparo público.

    {structured_text}

    Observações Adicionais do Usuário: "{observacoes_adicionais}"

    {image_context}

    Com base NESTAS informações (estruturadas, observações e análise de imagem do usuário), gere uma análise detalhada. Formate a saída como texto claro, usando marcadores (-) ou títulos. Se uma categoria NÃO PUDER ser confirmada com ALTA CONFIANÇA pelas informações fornecidas, indique "Não especificado/inferido".

    Categorias para Análise Detalhada:
    - Severidade/Tamanho Consolidado (Baseado em dados estruturados, observações e imagem): [Ex: Pequeno, Médio, Grande, Enorme, Crítico. Comente se os inputs divergem ou reforçam a mesma conclusão.]
    - Profundidade Consolidada: [Ex: Raso, Fundo, Muito Fundo. Comente se os inputs divergem ou reforçam.]
    - Presença de Água/Alagamento (Confirmado pelos inputs): [Sim/Não/Não mencionado/Não confirmado.]
    - Perigos Potenciais e Impactos Consolidado: [Liste riscos específicos citados nos inputs estruturados, observações e/ou visíveis na imagem. Consolide e destaque os mais graves.]
    - Contexto Adicional Relevante Consolidado: [Problema recorrente/antigo/novo, perto de local importante, em via movimentada, em curva, etc., conforme os inputs.]
    - Identificadores Visuais Adicionais (Conforme input): [Detalhes únicos próximos que ajudam a achar o buraco.]
    - Palavras-chave Principais: [Liste 3-7 palavras-chave que capturem a essência da denúncia e o problema principal.]

    Formate a resposta de forma limpa e estruturada.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"insights": f"❌ Análise de dados bloqueada pelos protocolos de segurança do Gemini. Motivo: {block_reason}"}

        return {"insights": response.text.strip()}
    except Exception as e:
        return {"insights": f"❌ Erro ao analisar os dados com IA: {e}"}


@st.cache_data(show_spinner="🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
def categorizar_urgencia_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir uma categoria de urgência com base em todos os dados e insights."""
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Texto offline)."}

    # Acessa todos os dados relevantes do dicionário completo
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível.')

    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    tipo_loc = localizacao_exata.get('tipo', 'Não informada')
    loc_contexto = f"Localização informada: Tipo: {tipo_loc}."
    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
        loc_contexto += f" Coordenadas: {localizacao_exata.get('latitude')}, {localizacao_exata.get('longitude')}. Link: {localizacao_exata.get('google_maps_link_gerado', 'Não disponível')}."
    elif tipo_loc == 'Descrição Manual Detalhada':
        loc_contexto += f" Descrição Manual: '{localizacao_exata.get('descricao_manual', 'Não informada')}'."
    if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
         loc_contexto += f" (Nota: Tentativa de Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior', 'Motivo desconhecido')})"


    # Formatar os detalhes estruturados para o prompt de urgência
    structured_urgency_factors = []
    if structured_details.get('tamanho') and structured_details['tamanho'] != 'Não Informado': structured_urgency_factors.append(f"Tamanho Estimado (User): {structured_details['tamanho']}")
    if structured_details.get('profundidade') and structured_details['profundidade'] != 'Não Informado': structured_urgency_factors.append(f"Profundidade Estimada (User): {structured_details['profundidade']}")
    if structured_details.get('perigo') and structured_details['perigo'] != 'Não Informado': structured_urgency_factors.append(f"Nível de Perigo (User): {structured_details['perigo']}")
    if structured_details.get('presenca_agua') and structured_details['presenca_agua'] != 'Não Informado': structured_urgency_factors.append(f"Presença de Água (User): {structured_details['presenca_agua']}")
    if structured_details.get('perigos_detalhados'): structured_urgency_factors.append(f"Perigos Detalhados (User): {', '.join(structured_details['perigos_detalhados'])}")
    if structured_details.get('contexto') and structured_details['contexto'] != 'Não Informado': structured_urgency_factors.append(f"Contexto/Histórico (User): {structured_details['contexto']}")
    structured_urgency_text = "Detalhes Estruturados: " + ("; ".join(structured_urgency_factors) if structured_urgency_factors else "Nenhum informado pelo usuário.")


    prompt = f"""
    Com base nas informações completas da denúncia (detalhes estruturados, observações, análise de imagem, análise detalhada) e na localização, sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade/tamanho, profundidade, PERIGOS POTENCIAIS e impactos mencionados/visíveis, e qualquer CONTEXTO ADICIONAL relevante (como ser recorrente, em área de alto tráfego/risco, perto de local importante). Dê peso especial aos PERIGOS mencionados ou visíveis na imagem ou descrição. Use as informações mais confiáveis disponíveis (input estruturado > análise de imagem > observações/análise detalhada, em geral).

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem perigo aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, perigo CLARO e/ou frequente (risco de acidente mais sério, dano significativo a veículo, perigo para motos/bikes/pedestres), em via movimentada ou área de risco (escola, hospital). Requer atenção RÁPIDA, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Informações Relevantes da Denúncia para Urgência:
    Localização Básica do Buraco: Rua {buraco.get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {buraco.get('numero_proximo', 'Não informado')}. Cidade: {buraco.get('endereco', {}).get('cidade_buraco', 'Não informada')}. {loc_contexto}
    {structured_urgency_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_text}
    Insights da Análise de Imagem (se disponível): {image_analysis_text}

    Com base nestes dados consolidados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 3 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais relevantes (tamanho, perigo, contexto, etc.) dos inputs ou análises que justificam a urgência.

    Formato de saída (muito importante seguir este formato):
    Categoria Sugerida: [Categoria Escolhida]
    Justificativa: [Justificativa Breve]
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"urgencia_ia": f"❌ Sugestão de urgência bloqueada pelos protocolos de segurança do Gemini. Motivo: {block_reason}"}

        return {"urgencia_ia": response.text.strip()}
    except Exception as e:
        return {"urgencia_ia": f"❌ Erro ao sugerir urgência com IA: {e}"}


@st.cache_data(show_spinner="🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
def sugerir_causa_e_acao_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir possíveis causas do buraco e ações de reparo com base nos dados e insights."""
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Texto offline)."}

    # Acessa todos os dados relevantes
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível.')

    structured_action_factors = []
    if structured_details.get('tamanho') and structured_details['tamanho'] != 'Não Informado': structured_action_factors.append(f"Tamanho Estimado (User): {structured_details['tamanho']}")
    if structured_details.get('profundidade') and structured_details['profundidade'] != 'Não Informado': structured_action_factors.append(f"Profundidade Estimada (User): {structured_details['profundidade']}")
    if structured_details.get('presenca_agua') and structured_details['presenca_agua'] != 'Não Informado': structured_action_factors.append(f"Presença de Água (User): {structured_details['presenca_agua']}")
    if structured_details.get('contexto') and structured_details['contexto'] != 'Não Informado': structured_action_factors.append(f"Contexto/Histórico (User): {structured_details['contexto']}")
    structured_action_text = "Detalhes Estruturados: " + ("; ".join(structured_action_factors) if structured_action_factors else "Nenhum informado pelo usuário.")


    prompt = f"""
    Com base nas informações completas da denúncia (dados estruturados, observações, análise de imagem e insights), tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico. Baseie-se em pistas nos inputs (ex: se é recorrente, se choveu muito - se mencionado nas observações/insights/imagem -, desgaste visível na imagem, etc.). Seja especulativo, mas baseado nos dados.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema. Baseie-se na severidade, profundidade, perigos e contexto. (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via).

    Baseie suas sugestões nos dados fornecidos. Se a informação for insuficiente, indique "Não especificado/inferido nos dados".

    Informações Relevantes para Causa e Ação:
    {structured_action_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_text}
    Insights da Análise de Imagem (se disponível): {image_analysis_text}

    Formato de saída:
    Possíveis Causas Sugeridas: [Lista de causas sugeridas baseadas nos dados ou 'Não especificado/inferido']
    Sugestões de Ação/Reparo Sugeridas: [Lista de ações sugeridas baseadas nos dados ou 'Não especificado/inferido']
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"sugestao_acao_ia": f"❌ Sugestão de causa/acao bloqueada pelos protocolos de segurança do Gemini. Motivo: {block_reason}"}

        return {"sugestao_acao_ia": response.text.strip()}
    except Exception as e:
        return {"sugestao_acao_ia": f"❌ Erro ao sugerir causa/ação com IA: {e}"}


@st.cache_data(show_spinner="🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para gerar um resumo narrativo inteligente da denúncia completa."""
    if not _model:
        return {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini Texto offline)."}

    # Acessa todos os dados coletados e resultados das IAs
    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})

    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')
    insights_ia = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível ou com erro.')
    urgencia_ia_text = _dados_denuncia_completa.get('urgencia_ia', {}).get('urgencia_ia', 'Sugestão de urgência não disponível ou com erro.')
    sugestao_acao_ia_text = _dados_denuncia_completa.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', 'Sugestões de causa/ação não disponíveis ou com erro.')
    streetview_status = _dados_denuncia_completa.get('streetview_image_data', {}).get('erro', 'OK') # Verifica se teve erro na Street View


    # Formatar a string de localização para o resumo
    loc_info_resumo = "Localização exata não especificada ou processada."
    tipo_loc_processada = localizacao_exata.get('tipo', 'Não informada')

    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         lat = localizacao_exata.get('latitude')
         lon = localizacao_exata.get('longitude')
         link_gerado = localizacao_exata.get('google_maps_link_gerado', 'Não disponível')
         loc_info_resumo = f"Localização: Coordenadas {lat}, {lon} (Obtida via: {tipo_loc_processada.replace(' (API)', ' API').replace('Manual', 'Manual').replace('Fornecidas/Extraídas', 'Manual')}). Link Google Maps: {link_gerado}."
         # Não inclui input original aqui para manter o resumo mais limpo, já que está no relatório completo

    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização via descrição manual detalhada: '{localizacao_exata.get('descricao_manual', 'Não informada')}'."

    elif localizacao_exata.get('input_original') and tipo_loc_processada == 'Não informada':
         loc_info_resumo = f"Localização informada (tipo não detectado): '{localizacao_exata.get('input_original')}'."

    # Não inclui motivo da falha da geocodificação no resumo para concisão, mas está no relatório completo.

    # Formatar os detalhes estruturados para inclusão no resumo
    structured_summary_items = []
    if structured_details.get('tamanho') and structured_details['tamanho'] != 'Não Informado': structured_summary_items.append(f"Tamanho: {structured_details['tamanho']}")
    if structured_details.get('profundidade') and structured_details['profundidade'] != 'Não Informado': structured_summary_items.append(f"Profundidade: {structured_details['profundidade']}")
    if structured_details.get('perigo') and structured_details['perigo'] != 'Não Informado': structured_summary_items.append(f"Perigo: {structured_details['perigo']}")
    if structured_details.get('presenca_agua') and structured_details['presenca_agua'] != 'Não Informado': structured_summary_items.append(f"Água: {structured_details['presenca_agua']}")
    if structured_details.get('perigos_detalhados'): structured_summary_items.append(f"Perigos Específicos: {', '.join(structured_details['perigos_detalhados'])}")
    if structured_details.get('contexto') and structured_details['contexto'] != 'Não Informado': structured_summary_items.append(f"Contexto: {structured_details['contexto']}")
    if structured_details.get('identificadores_visuais'): structured_summary_items.append(f"Identificadores Visuais: {structured_details['identificadores_visuais']}")

    structured_summary_text = " / ".join(structured_summary_items) if structured_summary_items else "Detalhes estruturados não fornecidos."

    # Adicionar informação sobre Street View ao resumo
    streetview_summary = ""
    if streetview_status == 'OK':
         streetview_summary = " Imagem Street View do local obtida."
    elif "Nenhuma imagem Street View encontrada" in streetview_status or "Sem cobertura" in streetview_status:
         streetview_summary = " Sem cobertura Street View disponível para o local."
    elif "Erro" in streetview_status:
         streetview_summary = " Falha ao obter imagem Street View do local."


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 8-10 frases) para a seguinte denúncia de buraco no aplicativo Krateras.
    Este resumo deve ser formal, objetivo e útil para equipes de manutenção ou gestão pública.
    Combine os dados do denunciante, detalhes estruturados do buraco, observações adicionais, localização exata processada e os resultados de TODAS as análises de IA (análise de imagem, análise detalhada, urgência, causa/ação). Mencione brevemente o status da imagem Street View.

    Inclua:
    - Denunciante (Nome, Cidade de Residência).
    - Localização base (Rua, Nº Próximo/Referência, Cidade do Buraco, Estado do Buraco).
    - Localização EXATA processada (mencione como foi obtida e os dados relevantes).
    - Resumo dos DETALHES ESTRUTURADOS e Observações Adicionais.
    - Breve resumo da ANÁLISE DE IMAGEM (se disponível).
    - Principais pontos da ANÁLISE DETALHADA.
    - A SUGESTÃO de Categoria de Urgência pela IA e sua Justificativa.
    - As SUGESTÕES de POSSÍVEIS CAUSAS e TIPOS DE AÇÃO/REPARO sugeridas pela IA (se disponíveis).
    - Status da imagem Street View.

    Dados da Denúncia Completa:
    Denunciante: {denunciante.get('nome', 'Não informado')}, de {denunciante.get('cidade_residencia', 'Não informada')}.
    Endereço do Buraco (Base): Rua {endereco.get('rua', 'Não informada')}, Nº Próximo: {buraco.get('numero_proximo', 'Não informado')}. Cidade: {endereco.get('cidade_buraco', 'Não informada')}, Estado: {endereco.get('estado_buraco', 'Não informado')}. CEP: {buraco.get('cep_informado', 'Não informado') if buraco.get('cep_informado') else 'Não informado'}.
    Lado da Rua: {buraco.get('lado_rua', 'Não informado')}.
    Localização Exata Coletada: {loc_info_resumo}
    Detalhes Estruturados do Buraco: {structured_summary_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"

    Insights da Análise de Imagem (se disponível): {image_analysis_text}
    Insights da Análise Detalhada (IA Texto): {insights_ia}
    Sugestão de Urgência (IA Texto): {urgencia_ia_text}
    Sugestões de Causa e Ação (IA Texto): {sugestao_acao_ia_text}
    Status Street View: {streetview_status}


    Gere o resumo em português. Comece com "Relatório Krateras: Denúncia de buraco..." ou algo similar. Use linguagem clara, formal e direta, focando nas informações mais relevantes para a ação de reparo.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"resumo_ia": f"❌ Geração de resumo bloqueada pelos protocolos de segurança do Gemini. Motivo: {block_reason}"}

        return {"resumo_ia": response.text.strip()}
    except Exception as e:
        return {"resumo_ia": f"❌ Erro ao gerar resumo completo com IA: {e}"}


# --- Funções de Navegação e Renderização de UI ---

def next_step():
    """Avança para o próximo passo no fluxo da aplicação."""
    steps = [
        'start',
        'collect_denunciante',
        'collect_buraco_address_method',
        'collect_buraco_address_cep',
        'collect_buraco_address_manual',
        'collect_buraco_details', # Esta etapa coleta o resto dos dados, foto e localização manual se geocoding falhar
        'processing_ia', # Nova etapa unificada para todas as análises IA (imagem + texto) E obtenção Street View
        'show_report'
    ]
    try:
        current_index = steps.index(st.session_state.step)
        if current_index < len(steps) - 1:
            st.session_state.step = steps[current_index + 1]
            st.rerun()
    except ValueError:
        st.session_state.step = steps[0]
        st.rerun()

def prev_step():
    """Volta para o passo anterior no fluxo da aplicação."""
    steps = [
        'start',
        'collect_denunciante',
        'collect_buraco_address_method',
        'collect_buraco_address_cep',
        'collect_buraco_address_manual',
        'collect_buraco_details',
        'processing_ia',
        'show_report'
    ]
    try:
        current_index = steps.index(st.session_state.step)
        if current_index > 0:
             # Lógica para pular passos de CEP/Manual se não foram usados ao voltar de 'collect_buraco_details'
             if st.session_state.step == 'collect_buraco_details':
                  if st.session_state.get('endereco_coletado_via') == 'cep':
                      st.session_state.step = 'collect_buraco_address_cep'
                  elif st.session_state.get('endereco_coletado_via') == 'manual':
                      st.session_state.step = 'collect_buraco_address_manual'
                  else: # Fallback seguro
                       st.session_state.step = steps[current_index - 1]
             elif st.session_state.step in ['collect_buraco_address_cep', 'collect_buraco_address_manual']:
                  st.session_state.step = 'collect_buraco_address_method'
             else:
                  st.session_state.step = steps[current_index - 1]

             st.rerun()
    except ValueError:
         st.session_state.step = steps[0]
         st.rerun()

# --- Layout Principal da Aplicação ---

st.title("Krateras 🚀✨🔒")
st.subheader("O Especialista Robótico de Denúncia de Buracos")

# --- Fluxo da Aplicação baseado no Estado ---

if st.session_state.step == 'start':
    st.write("""
    Olá! Krateras v3.2 entrando em órbita! Sua missão, caso aceite: denunciar buracos na rua
    para que possam ser consertados. A segurança dos seus dados e a precisão da denúncia
    são nossas prioridades máximas.

    Utilizamos inteligência artificial avançada (Google Gemini Pro para texto e Gemini Vision
    para análise de imagem) e APIs de localização (Google Geocoding, ViaCEP, Street View Static)
    para coletar, analisar, obter visualização do local e gerar um relatório detalhado e acionável
    para as autoridades competentes.

    Fui criado com o que há de mais avançado em Programação, IA, Design Inteligente,
    Matemática e Lógica Inabalável. Com acesso seguro às APIs, sou imparável.

    Clique em Iniciar para começarmos a coleta de dados.
    """)

    st.info("⚠️ Suas chaves de API do Google (Gemini e Geocoding/Embed/Street View Static) devem ser configuradas nos Streamlit Secrets (`.streamlit/secrets.toml`) para que as funcionalidades de IA, geocodificação e visualizações no mapa funcionem corretamente e de forma segura. Consulte o `README.md` ou as instruções ao lado para mais detalhes.")


    if st.button("Iniciar Missão Denúncia!"):
        # Carregar chaves e inicializar APIs antes de coletar dados
        gemini_api_key, geocoding_api_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_api_key # Armazena a chave de geocoding no estado
        st.session_state.gemini_pro_model, st.session_state.gemini_vision_model = init_gemini_models(gemini_api_key) # Inicializa os modelos Gemini (cacheados)
        st.session_state.api_keys_loaded = True # Marca que tentamos carregar as chaves
        next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Formulário para coletar dados do denunciante
    with st.form("form_denunciante"):
        nome = st.text_input("Seu nome completo:", key='nome_denunciante_input') # Added _input to avoid state key collision
        idade = st.number_input("Sua idade (aproximada, se preferir, sem pressão 😉):", min_value=1, max_value=120, value=30, key='idade_denunciante_input')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", key='cidade_residencia_denunciante_input')

        submitted = st.form_submit_button("Avançar (Dados Denunciante)")

        if submitted:
            if not nome or not cidade_residencia:
                st.error("❗ Nome e Cidade de residência são campos obrigatórios. Por favor, preencha-os.")
            else:
                st.session_state.denuncia_completa['denunciante'] = {
                    "nome": nome.strip(),
                    "idade": idade,
                    "cidade_residencia": cidade_residencia.strip()
                }
                st.success(f"Olá, {nome}! Dados coletados. Preparando para dados do buraco...")
                next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_method':
    st.header("--- 🚧 Detalhes do Buraco (Nosso Alvo!) ---")
    st.subheader("Como identificar a rua do buraco?")

    opcao_localizacao = st.radio(
        "Escolha o método:",
        ('Digitar nome manualmente', 'Buscar por CEP'),
        key='endereco_method_radio'
    )

    # Use um botão para confirmar a escolha e mover para o próximo sub-step
    if st.button("Selecionar Método"):
         if opcao_localizacao == 'Digitar nome manualmente':
              st.session_state.endereco_coletado_via = 'manual' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_manual'
         elif opcao_localizacao == 'Buscar por CEP':
              st.session_state.endereco_coletado_via = 'cep' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_cep'
         st.rerun()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_cep':
    st.header("--- 🚧 Detalhes do Buraco (Busca por CEP) ---")
    st.write("Digite o CEP do local do buraco.")

    with st.form("form_cep"):
        # Use um placeholder se veio do manual com CEP, ou vazio se for a primeira vez no CEP
        initial_cep = st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado', '')
        cep_input = st.text_input("Digite o CEP (apenas números):", value=initial_cep, max_chars=8, key='cep_buraco_input')
        buscar_button = st.form_submit_button("Buscar CEP")

        if buscar_button:
            if not cep_input:
                st.error("❗ Por favor, digite um CEP.")
            else:
                dados_cep = buscar_cep(cep_input.strip())

                if 'erro' in dados_cep:
                    st.error(f"❌ Falha na busca por CEP: {dados_cep['erro']}")
                    st.session_state.cep_search_error = True # Marca que houve erro no CEP
                    st.session_state.dados_cep_validos = None # Limpa dados válidos
                else:
                    st.session_state.dados_cep_validos = dados_cep # Armazena dados do CEP válidos
                    st.session_state.cep_search_error = False # Limpa erro
                    st.success("✅ Endereço Encontrado (ViaCEP):")
                    st.write(f"**Rua:** {dados_cep.get('logradouro', 'Não informado')}")
                    st.write(f"**Bairro:** {dados_cep.get('bairro', 'Não informado')}")
                    st.write(f"**Cidade:** {dados_cep.get('localidade', 'Não informado')}")
                    st.write(f"**Estado:** {dados_cep.get('uf', 'Não informado')}")
                    st.write(f"**CEP:** {cep_input.strip()}")
                    st.info("Por favor, confirme se estes dados parecem corretos. Se não, use o botão 'Corrigir Endereço Manualmente'.")
                    # Salva os dados básicos do CEP no buraco_data, mas ainda pode ser corrigido
                    st.session_state.denuncia_completa['buraco'] = {
                         'endereco': {
                             'rua': dados_cep.get('logradouro', ''),
                             'bairro': dados_cep.get('bairro', ''),
                             'cidade_buraco': dados_cep.get('localidade', ''),
                             'estado_buraco': dados_cep.get('uf', '')
                         },
                         'cep_informado': cep_input.strip()
                    }
                    # Forçar reload para exibir os botões de ação após a busca bem-sucedida
                    st.rerun()


    # Exibe botões de ação APENAS se tentou buscar CEP
    # Verifica se o formulário de busca foi processado e há um resultado (válido ou com erro)
    if 'cep_buraco_input' in st.session_state:
        if st.session_state.get('dados_cep_validos'): # Se dados do CEP foram encontrados e são válidos
            st.button("Confirmar Endereço e Avançar", on_click=next_step)
            if st.button("Corrigir Endereço Manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.rerun()

        elif st.session_state.get('cep_search_error'): # Se houve erro na busca por CEP
            st.warning("Não foi possível obter o endereço por CEP.")
            # Removido "Tentar novamente por CEP" pois basta digitar outro CEP no input e clicar buscar novamente
            if st.button("Digitar endereço manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.rerun()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_manual':
    st.header("--- 🚧 Detalhes do Buraco (Entrada Manual) ---")
    st.write("Digite os dados do endereço do buraco manualmente.")

    # Use os dados do CEP pré-preenchidos se veio dessa rota, ou use o que já foi digitado manualmente
    endereco_inicial = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})

    with st.form("form_manual_address"):
        rua_manual = st.text_input("Nome completo da rua:", value=endereco_inicial.get('rua', ''), key='rua_manual_buraco_input')
        bairro_manual = st.text_input("Bairro onde está o buraco (opcional):", value=endereco_inicial.get('bairro', ''), key='bairro_manual_buraco_input')
        cidade_manual = st.text_input("Cidade onde está o buraco:", value=endereco_inicial.get('cidade_buraco', ''), key='cidade_manual_buraco_input')
        estado_manual = st.text_input("Estado (UF) onde está o buraco:", value=endereco_inicial.get('estado_buraco', ''), max_chars=2, key='estado_manual_buraco_input')

        submitted = st.form_submit_button("Avançar (Endereço Manual)")

        if submitted:
            if not rua_manual or not cidade_manual or not estado_manual:
                st.error("❗ Rua, Cidade e Estado são campos obrigatórios para o endereço do buraco.")
            else:
                # Salva o endereço manual no dicionário buraco
                st.session_state.denuncia_completa['buraco'] = {
                    'endereco': {
                        'rua': rua_manual.strip(),
                        'bairro': bairro_manual.strip(),
                        'cidade_buraco': cidade_manual.strip(),
                        'estado_buraco': estado_manual.strip().upper()
                    },
                    # Mantém o CEP se ele foi informado na etapa anterior, mesmo usando entrada manual agora
                    'cep_informado': st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado', '')
                }
                next_step() # Move para a próxima etapa (coleta de detalhes + foto + localização exata)

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_details':
    st.header("--- 🚧 Detalhes Finais do Buraco ---")
    st.subheader("Informações cruciais para a localização, análise e reparo!")

    # Exibe o endereço básico já coletado para referência
    endereco_basico = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})
    st.write(f"**Endereço Base:** Rua {endereco_basico.get('rua', 'Não informada')}, {endereco_basico.get('cidade_buraco', 'Não informada')} - {endereco_basico.get('estado_buraco', 'Não informado')}")
    if endereco_basico.get('bairro'):
         st.write(f"**Bairro:** {endereco_basico.get('bairro')}")
    if st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado'):
         st.write(f"**CEP informado:** {st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado')}")

    st.markdown("---")

    with st.form("form_buraco_details_structured"):
        st.subheader("Detalhes Estruturados do Buraco")

        col1, col2 = st.columns(2)

        with col1:
            tamanho = st.radio(
                "**Tamanho Estimado:**",
                ['Não Informado', 'Pequeno (Cabe uma bola de futebol)', 'Médio (Cabe um pneu de carro)', 'Grande (Cabe uma pessoa sentada)', 'Enorme (Cobre a faixa)', 'Crítico (Cratera, afeta múltiplos veículos)'],
                key='tamanho_buraco'
            )
            profundidade = st.radio(
                "**Profundidade Estimada:**",
                ['Não Informado', 'Raso (Dá um susto, não danifica)', 'Médio (Pode furar pneu ou danificar suspensão)', 'Fundo (Causa dano considerável, pode entortar roda)', 'Muito Fundo (Causa acidentes graves, imobiliza veículo)'],
                key='profundidade_buraco'
            )
            presenca_agua = st.radio(
                 "**Presença de Água/Alagamento:**",
                 ['Não Informado', 'Sim (Acumula água)', 'Não (Está seco)'],
                 key='agua_buraco'
            )

        with col2:
             perigo = st.radio(
                 "**Nível de Perigo Aparente:**",
                 ['Não Informado', 'Baixo (Principalmente estético)', 'Médio (Pode causar dano menor)', 'Alto (Risco de acidente sério ou dano significativo)', 'Altíssimo (Risco grave e iminente, acidentes frequentes)'],
                 key='perigo_buraco'
             )
             contexto = st.selectbox(
                 "**Contexto ou Histórico do Local:**",
                 ['Não Informado', 'Via de Alto Tráfego', 'Via de Baixo Tráfego', 'Perto de Escola/Hospital', 'Em Curva', 'Na Esquina', 'Em Subida/Descida', 'Pouca Iluminação', 'Problema Recorrente', 'Obra Recente na Região'],
                 key='contexto_buraco'
             )
             perigos_detalhados = st.multiselect(
                 "**Perigos e Impactos Detalhados (Selecione todos que se aplicam):**",
                 ['Risco para Carros (Pneu/Suspensão/Roda)', 'Risco para Motos/Bikes', 'Risco para Pedestres', 'Dificulta Desvio', 'Perigoso à Noite', 'Perigoso na Chuva', 'Causa Lentidão no Trânsito', 'Já Causou Acidentes (Se souber)'],
                 key='perigos_detalhados_buraco'
             )


        identificadores_visuais = st.text_input(
             "**Identificadores Visuais Adicionais Próximos (Ex: Em frente ao poste X, perto da árvore Y):**",
             key='identificadores_visuais_buraco'
        )

        # Este input é movido para cá, pois é crucial para Geocoding e localização
        numero_proximo = st.text_input(
             "**Número do imóvel mais próximo ou ponto de referência (ESSENCIAL para precisão! Ex: 'Em frente ao 123', 'Esquina c/ Rua X'):**",
             key='numero_proximo_buraco' # Mantém a chave original
        )
        lado_rua = st.text_input(
             "**Lado da rua onde está o buraco (Ex: 'lado par', 'lado ímpar', 'lado direito', 'lado esquerdo'):**",
             key='lado_rua_buraco' # Mantém a chave original
        )


        st.markdown("---")
        st.subheader("Observações Adicionais (Texto Libre)")
        observacoes_adicionais = st.text_area(
            "Qualquer outra informação relevante sobre o buraco ou o local (Histórico, chuva recente, etc.):",
            key='observacoes_adicionais_buraco'
        )

        st.markdown("---")
        st.subheader("Adicionar Foto do Buraco")
        st.write("Anexe uma foto nítida do buraco (JPG, PNG). A IA Gemini Vision pode analisar a imagem para complementar a denúncia!")
        st.info("💡 Dica: Tire a foto de um ângulo que mostre o tamanho e profundidade do buraco, e também inclua um pouco do entorno (calçada, postes, referências) para ajudar a IA e as equipes de reparo a localizarem.")
        uploaded_image = st.file_uploader("Escolha uma imagem...", type=["jpg", "jpeg", "png"], key='uploader_buraco_image')

        if uploaded_image is not None:
             # Read image as bytes here, when the file is uploaded
             st.session_state.uploaded_image = uploaded_image.getvalue()
             try:
                 # To display, open from bytes using PIL
                 img_display = Image.open(io.BytesIO(st.session_state.uploaded_image))
                 st.image(img_display, caption="Foto do buraco carregada.", use_column_width=True)
             except Exception as e:
                  st.error(f"❌ Erro ao carregar a imagem para exibição: {e}")
                  st.session_state.uploaded_image = None # Clear state if display fails


        st.markdown("---")
        st.subheader("📍 Localização Exata (Coordenadas ou Descrição)")
        st.info("A MELHOR forma de garantir que o reparo vá ao local exato é fornecer Coordenadas (Lat,Long) ou um Link do Google Maps que as contenha. Tente obter isso tocando/clicando e segurando no local exato do buraco no Google Maps.")

        # --- Tentar Geocodificação Automática ao submeter ---
        # A geocodificação e a coleta manual de localização exata agora acontecem APÓS submeter este formulário
        # Movemos o input de localização manual para dentro deste formulário para simplificar o fluxo.

        # Input de localização manual (aparece sempre, mas o processamento depende do sucesso da geocodificação)
        localizacao_manual_input = st.text_input(
             "Alternativamente, ou para corrigir a Geocodificação, insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO Detalhada EXATA:",
             key='localizacao_manual_input'
        )


        submitted_details = st.form_submit_button("Finalizar Coleta e Analisar Denúncia!")

        if submitted_details:
            if not numero_proximo or not lado_rua: # Validação para campos movidos
                 st.error("❗ Número próximo/referência e Lado da rua são campos obrigatórios.")
                 # Recarrega o formulário sem avançar
                 st.stop() # Stop further execution until inputs are corrected and form is resubmitted

            # Armazena os detalhes estruturados e observações no dicionário buraco
            st.session_state.denuncia_completa['buraco'].update({
                'numero_proximo': numero_proximo.strip(), # Salvando campos movidos
                'lado_rua': lado_rua.strip(), # Salvando campos movidos
                'structured_details': {
                     'tamanho': tamanho,
                     'perigo': perigo,
                     'profundidade': profundidade,
                     'presenca_agua': presenca_agua,
                     'contexto': contexto,
                     'perigos_detalhados': perigos_detalhados,
                     'identificadores_visuais': identificadores_visuais.strip(),
                },
                'observacoes_adicionais': observacoes_adicionais.strip(),
                # A imagem já está no st.session_state.uploaded_image (bytes)
            })

            st.subheader("Processando Localização Exata...")

            st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"} # Reseta localização processada
            tentou_geocodificar = False
            geocodificacao_sucesso = False
            motivo_falha_geo = ""
            lat_final: Optional[float] = None
            lon_final: Optional[float] = None
            link_maps_final: Optional[str] = None
            embed_link_final: Optional[str] = None


            # --- Tentar Geocodificação Automática Primeiro ---
            rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
            cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
            estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')
            numero_proximo_geo = st.session_state.denuncia_completa['buraco'].get('numero_proximo') # Usa o numero_proximo para geocoding

            tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and numero_proximo_geo and cidade_buraco and estado_buraco)

            if tem_dados_para_geo:
                st.info("✅ Chave de Geocodificação e dados básicos de endereço completos encontrados. Tentando gerar a localização exata automaticamente...")
                tentou_geocodificar = True
                with st.spinner("⏳ Chamando Google Maps Geocoding API..."):
                    geo_resultado = geocodificar_endereco(
                        rua_buraco,
                        numero_proximo_geo.strip(),
                        cidade_buraco,
                        estado_buraco,
                        st.session_state.geocoding_api_key
                    )

                if 'erro' not in geo_resultado:
                    geocodificacao_sucesso = True
                    lat_final = geo_resultado['latitude']
                    lon_final = geo_resultado['longitude']
                    link_maps_final = geo_resultado['google_maps_link_gerado']
                    embed_link_final = geo_resultado.get('google_embed_link_gerado')
                    st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                        "tipo": "Geocodificada (API)",
                        "latitude": lat_final,
                        "longitude": lon_final,
                        "endereco_formatado_api": geo_resultado.get('endereco_formatado_api', ''),
                        "google_maps_link_gerado": link_maps_final,
                        "google_embed_link_gerado": embed_link_final
                    }
                    st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                else:
                    st.warning(f"❌ Falha na Geocodificação automática: {geo_resultado['erro']}")
                    motivo_falha_geo = f"Erro da API de Geocodificação: {geo_resultado.get('erro', 'Motivo desconhecido')}"
            elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes (precisa de Rua, Número Próximo, Cidade, Estado). Geocodificação automática NÃO tentada.")
                motivo_falha_geo = "Dados insuficientes para Geocodificação (requer Rua, Número Próximo, Cidade, Estado)."
            elif not st.session_state.geocoding_api_key:
                st.warning("⚠️ Chave de API de Geocodificação NON_PROVIDED. Geocodificação automática NÃO tentada.")
                motivo_falha_geo = "Chave de API de Geocodificação não fornecida."

            # --- Processar Localização Manual (se fornecida E Geocoding falhou ou não tentada) ---
            # O input 'localizacao_manual_input' já está no estado da sessão pois foi um widget no form
            input_original_manual = st.session_state.get('localizacao_manual_input', '').strip()

            if not geocodificacao_sucesso and input_original_manual:
                 st.info("⏳ Processando input manual de localização...")
                 # Tentar extrair coordenadas do input manual
                 lat_manual: Optional[float] = None
                 lon_manual: Optional[float] = None
                 tipo_manual_processado = "Descrição Manual Detalhada"

                 match_coords = re.search(r'(-?\d+\.?\d*)[,\s/]+(-?\d+\.?\d*)', input_original_manual)
                 if match_coords:
                     try:
                         teste_lat = float(match_coords.group(1))
                         teste_lon = float(match_coords.group(2))
                         if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                             lat_manual = teste_lat
                             lon_manual = teste_lon
                             tipo_manual_processado = "Coordenadas Fornecidas/Extraídas Manualmente"
                             st.info("✅ Coordenadas válidas detectadas no input manual!")
                         else:
                             st.warning("⚠️ Parece um formato de coordenadas no input manual, mas fora da faixa esperada. Tratando como descrição.")
                     except ValueError:
                         st.info("ℹ️ Input manual não parece ser coordenadas válidas. Tratando como descrição detalhada.")
                     except Exception as e:
                          st.info(f"ℹ️ Ocorreu um erro ao tentar processar as coordenadas/link no input manual: {e}. Tratando como descrição.")
                 elif input_original_manual.startswith("http"):
                      st.info("ℹ️ Input manual é um link. Tentando extrair coordenadas (sujeito a formato do link)...")
                      match_maps_link = re.search(r'/@(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual)
                      if match_maps_link:
                          try:
                              teste_lat = float(match_maps_link.group(1))
                              teste_lon = float(match_maps_link.group(2))
                              if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                                   lat_manual = teste_lat
                                   lon_manual = teste_lon
                                   tipo_manual_processado = "Coordenadas Extraídas de Link (Manual)"
                                   st.info("✅ Coordenadas extraídas de link do Maps no input manual!")
                              else:
                                   st.warning("⚠️ Coordenadas extraídas do link no input manual fora da faixa esperada. Tratando como descrição.")
                          except ValueError:
                             st.info("ℹ️ Valores no link não parecem coordenadas válidas. Tratando como descrição.")
                          except Exception as e:
                               st.info(f"ℹ️ Ocorreu um erro ao tentar processar o link no input manual: {e}. Tratando como descrição.")
                      else:
                           st.info("ℹ️ Não foi possível extrair coordenadas reconhecíveis do link fornecido manualmente.")
                 else:
                      st.info("ℹ️ Input manual não detectado como coordenadas ou link. Tratando como descrição detalhada.")

                 # Se coordenadas foram extraídas do input manual, elas substituem as da geocodificação (se houve, mas falhou)
                 if lat_manual is not None and lon_manual is not None:
                     lat_final = lat_manual
                     lon_final = lon_manual
                     link_maps_final = f"https://www.google.com/maps/search/?api=1&query={lat_final},{lon_final}"
                     # Tenta gerar link embed APENAS se tiver a chave Geocoding (necessária para o Embed API)
                     embed_link_final = f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_final},{lon_final}" if st.session_state.geocoding_api_key else None

                     st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                          "tipo": tipo_manual_processado,
                          "input_original": input_original_manual,
                          "latitude": lat_final,
                          "longitude": lon_final,
                          "google_maps_link_gerado": link_maps_final,
                          "google_embed_link_gerado": embed_link_final
                     }
                     if st.session_state.geocoding_api_key and embed_link_final is None:
                          st.warning("⚠️ Não foi possível gerar o link Google Maps Embed com a chave fornecida. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")

                 # Se não extraiu coordenadas do input manual (é só descrição ou formato irreconhecível)
                 elif input_original_manual:
                      st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                           "tipo": "Descrição Manual Detalhada",
                           "input_original": input_original_manual,
                           "descricao_manual": input_original_manual
                      }
                      st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi detectada no input manual. O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")

                 # else: Input manual estava vazio, localizacao_exata_processada continua como "Não informada"

            # --- Garante que o motivo da falha da geocodificação automática seja registrado se ela foi tentada ---
            if tentou_geocodificar and not geocodificacao_sucesso:
                 st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = motivo_falha_geo
            elif not st.session_state.geocoding_api_key:
                 st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Chave de API de Geocodificação não fornecida."
            elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                 st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Dados insuficientes para Geocodificação (requer Rua, Número Próximo, Cidade, Estado)."


            # --- Obter Imagem Street View (se houver coordenadas e chave) ---
            st.session_state.streetview_image_data = {"erro": "Imagem Street View não obtida."} # Reseta
            # Tenta obter Street View APENAS se coordenadas FINAIS (geocodificadas ou manuais) estiverem disponíveis
            if lat_final is not None and lon_final is not None and st.session_state.geocoding_api_key:
                 st.info("📸 Tentando obter imagem Street View para as coordenadas...")
                 # Chama a função Street View (é cacheada por lat/lon/chave/size/heading)
                 with st.spinner("⏳ Chamando Google Street View Static API..."):
                      st.session_state.streetview_image_data = get_street_view_image(
                          lat_final,
                          lon_final,
                          st.session_state.geocoding_api_key
                          # O heading (0) é um chute. Poderíamos adicionar um input para o usuário ajustar.
                          # Ou tentar múltiplos headings (0, 90, 180, 270) e mostrar uma galeria.
                          # Para manter simples agora, usamos heading 0.
                      )
                 if 'image_bytes' in st.session_state.streetview_image_data:
                      st.success("✅ Imagem Street View obtida com sucesso!")
                 elif 'erro' in st.session_state.streetview_image_data:
                      st.warning(f"⚠️ Falha ao obter imagem Street View: {st.session_state.streetview_image_data['erro']}")
                      # Nota importante: A API Street View Static precisa ser habilitada no Google Cloud Console.
                      if "not authorized" in st.session_state.streetview_image_data['erro'].lower():
                           st.error("❌ Erro de autorização na Street View Static API. Verifique se a 'Street View Static API' está habilitada e autorizada para sua chave no Google Cloud.")
                      elif "Sem cobertura" in st.session_state.streetview_image_data['erro']:
                           st.info("ℹ️ É possível que não haja cobertura Street View no local exato fornecido.")


            elif not st.session_state.geocoding_api_key:
                 st.warning("⚠️ Chave de API de Geocodificação/Street View não fornecida. Imagem Street View não obtida.")
                 st.session_state.streetview_image_data['erro'] = "Chave de API de Geocodificação/Street View não fornecida."
            elif lat_final is None or lon_final is None:
                 st.info("ℹ️ Coordenadas exatas não disponíveis. Imagem Street View não pode ser obtida.")
                 st.session_state.streetview_image_data['erro'] = "Coordenadas exatas não disponíveis."


            # Agora que a localização, Street View e imagem do usuário foram processadas/coletadas,
            # avançamos para a etapa de processamento das análises de IA.
            next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa todos os dados (texto, imagem) e gera o relatório com a inteligência do Google Gemini.")

    # Verifica se o modelo Gemini (texto ou visão) está disponível antes de processar
    gemini_available = st.session_state.gemini_pro_model or st.session_state.gemini_vision_model

    # Inicializa resultados IA com valores padrão (se ainda não definidos em runs anteriores)
    if 'image_analysis_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "Análise de imagem via IA indisponível."}
    if 'insights_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['insights_ia'] = {"insights": "Análise detalhada via IA indisponível."}
    if 'urgencia_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Sugestão de urgência via IA indisponível."}
    if 'sugestao_acao_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Sugestões de causa/ação via IA indisponíveis."}
    if 'resumo_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Resumo completo via IA indisponível."}


    # Executa análises de IA SOMENTE se os modelos estiverem disponíveis
    if st.session_state.gemini_vision_model and st.session_state.get('uploaded_image'):
         # 1. Análise de Imagem (se houver imagem do usuário e modelo Vision)
         st.info("🧠 Analisando a imagem do buraco com IA Gemini Vision...")
         # Chamar a função de análise de imagem (NÃO cacheada)
         st.session_state.denuncia_completa['image_analysis_ia'] = analyze_image_with_gemini_vision(st.session_state.uploaded_image, st.session_state.gemini_vision_model)
         # A exibição dos resultados IA ocorre no relatório final

    if st.session_state.gemini_pro_model:
         buraco_data = st.session_state.denuncia_completa.get('buraco', {})
         image_analysis_result_for_text_model = st.session_state.denuncia_completa.get('image_analysis_ia', {}) # Passa o resultado da análise de imagem

         # 2. Análise de Texto/Dados Consolidados (se modelo Pro)
         st.info("🧠 Executando análise profunda dos dados do buraco com IA Gemini (Texto)...")
         st.session_state.denuncia_completa['insights_ia'] = analisar_dados_com_gemini(
             buraco_data,
             image_analysis_result_for_text_model, # Passa o resultado da análise de imagem
             st.session_state.gemini_pro_model
         )

         # 3. Sugestão de urgência (usa todos os dados e insights)
         st.info("🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
         st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
             st.session_state.denuncia_completa, # Passa o dicionário completo
             st.session_state.gemini_pro_model
        )

         # 4. Sugestão de causa e ação (usa todos os dados e insights)
         st.info("🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
         st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
             st.session_state.denuncia_completa, # Passa o dicionário completo
             st.session_state.gemini_pro_model
        )

         # 5. Geração do resumo (usa todos os dados coletados e resultados das IAs)
         st.info("🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
         st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
             st.session_state.denuncia_completa, # Passa o dicionário completo
             st.session_state.gemini_pro_model
        )


    if st.session_state.gemini_pro_model or st.session_state.gemini_vision_model:
        st.success("✅ Análises de IA concluídas!")
    else:
        st.warning("⚠️ Nenhuma análise de IA foi executada (Modelos Gemini não configurados ou indisponíveis).")

    # Avança para exibir o relatório APÓS TODAS as chamadas de API e IA processarem
    next_step()


elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊")
    st.write("✅ MISSÃO KRATERAS CONCLUÍDA! RELATÓRIO GERADO. ✅")

    dados_completos = st.session_state.denuncia_completa
    denunciante = dados_completos.get('denunciante', {})
    buraco = dados_completos.get('buraco', {})
    endereco = buraco.get('endereco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Nenhuma observação adicional fornecida.')
    localizacao_exata = dados_completos.get('localizacao_exata_processada', {})

    image_analysis_ia = dados_completos.get('image_analysis_ia', {})
    insights_ia = dados_completos.get('insights_ia', {})
    urgencia_ia = dados_completos.get('urgencia_ia', {})
    sugestao_acao_ia = dados_completos.get('sugestao_acao_ia', {})
    resumo_ia = dados_completos.get('resumo_ia', {})
    streetview_image_data = dados_completos.get('streetview_image_data', {}) # Dados da imagem Street View

    st.markdown("---")

    # Exibir todas as etapas em expanders abertos por padrão
    with st.expander("👤 Dados do Denunciante", expanded=True):
        st.write(f"**Nome:** {denunciante.get('nome', 'Não informado')}")
        st.write(f"**Idade:** {denunciante.get('idade', 'Não informado')}")
        st.write(f"**Cidade de Residência:** {denunciante.get('cidade_residencia', 'Não informada')}")

    with st.expander("🚧 Dados do Buraco Coletados", expanded=True):
        st.subheader("Endereço Base")
        st.write(f"**Rua:** {endereco.get('rua', 'Não informada')}")
        if buraco.get('numero_proximo'):
            st.write(f"**Referência/Número Próximo:** {buraco.get('numero_proximo')}")
        if endereco.get('bairro'):
            st.write(f"**Bairro:** {endereco.get('bairro')}")
        if endereco.get('cidade_buraco'):
             st.write(f"**Cidade do Buraco:** {endereco.get('cidade_buraco')}")
        if endereco.get('estado_buraco'):
            st.write(f"**Estado do Buraco:** {endereco.get('estado_buraco')}")
        if buraco.get('cep_informado'):
            st.write(f"**CEP Informado:** {buraco.get('cep_informado')}")
        st.write(f"**Lado da Rua:** {buraco.get('lado_rua', 'Não informado')}")

        st.subheader("Detalhes Estruturados Preenchidos")
        if structured_details:
            # Filtrar os detalhes que não foram informados para não poluir o relatório
            informed_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}
            if informed_details:
                 # Exibir os detalhes informados de forma limpa
                 for key, value in informed_details.items():
                      key_translated = {
                         'tamanho': 'Tamanho Estimado',
                         'perigo': 'Nível de Perigo',
                         'profundidade': 'Profundidade Estimada',
                         'presenca_agua': 'Presença de Água/Alagamento',
                         'contexto': 'Contexto ou Histórico',
                         'perigos_detalhados': 'Perigos e Impactos Detalhados',
                         'identificadores_visuais': 'Identificadores Visuais Adicionais',
                      }.get(key, key)
                      value_str = ", ".join(value) if isinstance(value, list) else value
                      st.write(f"**{key_translated}:** {value_str}")
            else:
                 st.info("Nenhum detalhe estruturado foi informado.")
        else:
            st.info("Detalhes estruturados não foram coletados.")

        st.subheader("Observações Adicionais (Texto Libre)")
        st.info(observacoes_adicionais if observacoes_adicionais else "Nenhuma observação adicional fornecida.")

        st.subheader("Foto Anexada pelo Usuário")
        if st.session_state.get('uploaded_image'):
             try:
                 # Display image from bytes
                 img_display = Image.open(io.BytesIO(st.session_state.uploaded_image))
                 st.image(img_display, caption="Foto do buraco anexada.", use_column_width=True)
             except Exception as e:
                  st.warning(f"⚠️ Não foi possível exibir a imagem anexada. Erro: {e}")
        else:
            st.info("Nenhuma foto foi anexada a esta denúncia pelo usuário.")


    with st.expander("📍 Localização Exata Processada e Visualizações", expanded=True):
        tipo_loc = localizacao_exata.get('tipo', 'Não informada')
        st.write(f"**Tipo de Coleta/Processamento:** {tipo_loc}")

        lat = localizacao_exata.get('latitude')
        lon = localizacao_exata.get('longitude')

        if lat is not None and lon is not None:
             st.write(f"**Coordenadas:** `{lat}, {lon}`")

             # --- Visualização Street View ---
             st.subheader("Visualização Google Street View Estática")
             if 'image_bytes' in streetview_image_data:
                  try:
                       # Display Street View image from bytes
                       st.image(streetview_image_data['image_bytes'], caption="Imagem Google Street View.", use_column_width=True)
                       st.info("✅ Imagem Street View obtida com sucesso.")
                  except Exception as e:
                       st.error(f"❌ Erro ao exibir a imagem Street View: {e}")
             elif 'erro' in streetview_image_data:
                  st.warning(f"⚠️ Falha ao obter imagem Street View: {streetview_image_data['erro']}")
             else:
                  st.info("ℹ️ Tentativa de obter imagem Street View não realizada ou sem resultado.")

             # --- Visualização no Mapa OpenStreetMap ---
             st.subheader("Visualização no Mapa (OpenStreetMap/MapLibre)")
             try:
                 # Tenta usar st.map se coordenadas válidas (Não precisa de chave Google)
                 map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                 st.map(map_data, zoom=18, use_container_width=True)
                 st.info("ℹ️ O mapa acima é uma representação aproximada usando MapLibre/OpenStreetMap.")
             except Exception as map_error:
                 st.error(f"❌ Erro ao gerar visualização do mapa OpenStreetMap/MapLibre: {map_error}")

             # --- Visualização no Google Maps Embed ---
             st.subheader("Visualização no Google Maps (Embed)")
             embed_link = localizacao_exata.get('google_embed_link_gerado')
             if embed_link:
                 try:
                     st.components.v1.html(
                         f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link}" allowfullscreen></iframe>',
                         height=470,
                         scrolling=False
                     )
                     st.info("✅ Visualização do Google Maps Embed carregada (requer API habilitada e autorizada).")
                 except Exception as embed_error:
                      st.error(f"❌ Erro ao carregar visualização do Google Maps Embed: {embed_error}")
                      st.warning("⚠️ A visualização do Google Maps Embed requer que a 'Maps Embed API' esteja habilitada e autorizada para sua chave de API Geocoding no Google Cloud.")
             elif st.session_state.geocoding_api_key:
                  st.warning("⚠️ Chave de API Geocoding fornecida, mas não foi possível gerar o link Google Maps Embed ou carregá-lo. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")
             else:
                  st.warning("⚠️ Chave de API Geocoding não fornecida. Visualização Google Maps Embed não disponível.")


             link_maps = localizacao_exata.get('google_maps_link_gerado')
             if link_maps:
                 st.write(f"**Link Direto Google Maps:** [Abrir no Google Maps]({link_maps})")

             if localizacao_exata.get('endereco_formatado_api'):
                  st.write(f"**Endereço Formatado (API):** {localizacao_exata.get('endereco_formatado_api')}")
             if localizacao_exata.get('input_original') and tipo_loc != 'Descrição Manual Detalhada':
                  st.write(f"(Input Original para Localização Exata: `{localizacao_exata.get('input_original', 'Não informado')}`)")


        elif tipo_loc == 'Descrição Manual Detalhada':
            st.write(f"**Descrição Manual da Localização:**")
            st.info(localizacao_exata.get('descricao_manual', 'Não informada'))
            if localizacao_exata.get('input_original'):
                st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")

        else:
            st.warning("Localização exata não coletada de forma estruturada (coordenadas/link/descrição manual detalhada).")

        # Inclui motivo da falha na geocodificação se aplicável
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
             st.info(f"ℹ️ Nota: Não foi possível obter a localização exata via Geocodificação automática. Motivo: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")

    st.markdown("---")

    # Exibir análises de IA (se os modelos estavam disponíveis)
    if st.session_state.gemini_pro_model or st.session_state.gemini_vision_model:

        with st.expander("🧠 Análise de Imagem (IA Gemini Vision)", expanded=True):
             st.write(image_analysis_ia.get('image_analysis', 'Análise não realizada, sem imagem ou com erro.'))
             if st.session_state.gemini_vision_model is None:
                  st.info("ℹ️ Motor Gemini Vision indisponível.")

        with st.expander("🧠 Análise Detalhada Consolidada (IA Gemini Texto)", expanded=True):
            st.write(insights_ia.get('insights', 'Análise não realizada ou com erro.'))
            if st.session_state.gemini_pro_model is None:
                 st.info("ℹ️ Motor Gemini Texto indisponível.")


        with st.expander("🚦 Sugestão de Urgência (IA Gemini Texto)", expanded=True):
            st.write(urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro.'))
            if st.session_state.gemini_pro_model is None:
                 st.info("ℹ️ Motor Gemini Texto indisponível.")


        with st.expander("🛠️ Sugestões de Causa e Ação (IA Gemini Texto)", expanded=True):
            st.write(sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões não geradas ou com erro.'))
            if st.session_state.gemini_pro_model is None:
                 st.info("ℹ️ Motor Gemini Texto indisponível.")

        st.markdown("---")
        st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini Texto)")
        st.write(resumo_ia.get('resumo_ia', 'Resumo não gerado ou com erro.'))
        if st.session_state.gemini_pro_model is None:
             st.info("ℹ️ Motor Gemini Texto indisponível.")


    else:
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chaves Gemini não configuradas ou modelos indisponíveis).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Opção para reiniciar o processo
    if st.button("Iniciar Nova Denúncia", key='new_denuncia_button'):
        # Limpa o estado da sessão para recomeçar
        for key in st.session_state.keys():
            # Mantém as chaves de API e modelos cacheada, pois não mudam por sessão do app
            if key not in ['geocoding_api_key', 'gemini_pro_model', 'gemini_vision_model', 'api_keys_loaded']:
                 del st.session_state[key]
        st.rerun()

    # Opção para exibir dados brutos (útil para debug ou exportação)
    with st.expander("🔌 Ver Dados Brutos da Denúncia (JSON)"):
        # Remover bytes da imagem do Street View e do upload para evitar erros de serialização JSON
        dados_para_json = dados_completos.copy()
        if 'streetview_image_data' in dados_para_json and 'image_bytes' in dados_para_json['streetview_image_data']:
             # Cria uma cópia do dicionário streetview_image_data removendo a chave 'image_bytes'
             streetview_data_clean = dados_para_json['streetview_image_data'].copy()
             del streetview_data_clean['image_bytes']
             dados_para_json['streetview_image_data'] = streetview_data_clean
             dados_para_json['streetview_image_data']['note'] = "image_bytes_removed_for_json_view"


        if 'uploaded_image' in dados_para_json and dados_para_json['uploaded_image'] is not None:
             dados_para_json['uploaded_image'] = "image_bytes_removed_for_json_view"

        st.json(dados_para_json)
