# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v3.4.1 - Correção Sintaxe e Resiliência IA)

Versão aprimorada do Krateras com correção de erro sintático e foco em diagnósticos robustos
para as análises de IA e um fluxo de processamento mais transparente.

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
import time # Para simular um pequeno delay no processamento para melhor visualização do spinner

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Krateras 🚀✨🔒 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados (Replicando o visual clean/light da v3.3) ---
# Definindo variáveis CSS para as cores principais do tema clean/light
st.markdown("""
<style>
    :root {
        --color-primary: #4A90E2; /* Azul principal (mantido vibrante, mas menos escuro) */
        --color-secondary: #5C6BC0; /* Um azul/roxo suave para botões secundários/submit */
        --color-text: #333; /* Cor de texto escura */
        --color-light-text: #555; /* Cor de texto um pouco mais clara */
        --color-background-light: #F8F9FA; /* Fundo muito claro para seções */
        --color-background-mid: #E9ECEF; /* Fundo levemente mais escuro para contraste sutil */
        --color-border: #CED4DA; /* Cor de borda sutil */
        --color-success: #28A745; /* Verde Bootstrap */
        --color-warning: #FFC107; /* Amarelo Bootstrap */
        --color-error: #DC3545; /* Vermelho Bootstrap */
        --color-info: #17A2B8; /* Azul claro Bootstrap */
         --color-primary-rgb: 74, 144, 226; /* RGB para sombras */
    }

    /* Importar fonte (Open Sans - clean e legível) */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        margin: 0;
        padding: 0;
        font-family: 'Open Sans', sans-serif;
        color: var(--color-text);
        /* Fundo muito claro ou gradiente suave */
        background: linear-gradient(to bottom right, #e0f7fa, #b3e5fc) !important; /* Gradiente azul claro suave */
        /* background: #f0f2f5 !important; */ /* Alternativa: fundo sólido muito claro */
        background-attachment: fixed;
        min-height: 100vh;
        width: 100%;
        overflow-x: hidden;
    }

    /* Target the main content block */
    [data-testid="stAppViewContainer"] > .st-emotion-cache-xyz { /* Note: xyz part is unstable, may need adjustment */
         background-color: #FFFFFF; /* Fundo branco sólido para o conteúdo */
         padding: 2rem 3rem;
         border-radius: 10px;
         box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* Sombra mais suave */
         margin-top: 2rem;
         margin-bottom: 2rem;
         max-width: 1000px;
         margin-left: auto;
         margin-right: auto;
         box-sizing: border-box;
    }
    /* Fallback/alternative selector for the main content */
     [data-testid="stVerticalBlock"] {
          box-sizing: border-box !important;
     }


    /* Ajuste para o sidebar se ele existir */
    [data-testid="stSidebar"] {
       background-color: rgba(255, 255, 255, 0.9); /* Fundo semi-transparente branco */
       padding-top: 2rem;
       box-shadow: 2px 0 5px rgba(0,0,0,0.05);
    }


    h1, h2, h3, h4 {
        color: var(--color-primary); /* Títulos com a cor primária */
        font-weight: 700;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    h1 { font-size: 2.5em; }
    h2 { font-size: 1.8em; }
    h3 { font-size: 1.4em; }
    h4 { font-size: 1.1em; }


    /* Botões - Clean Look */
    /* Target base button container */
    [data-testid="baseButton-secondary"] button { /* Applies to st.button */
        background-color: var(--color-background-mid); /* Fundo cinza claro */
        color: var(--color-text); /* Texto escuro */
        font-weight: 600; /* Semibold */
        border-radius: 8px; /* Menos arredondado que antes, mais clean */
        padding: 0.7rem 1.2rem; /* Padding ajustado */
        margin-top: 1.5rem;
        margin-right: 0.5rem;
        border: 1px solid var(--color-border); /* Borda sutil */
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        box-shadow: none; /* Sem sombra padrão */
        min-width: 120px; /* Minimum size adjusted */
        text-align: center;
    }
    [data-testid="baseButton-secondary"] button:hover {
        background-color: var(--color-background-light); /* Fundo ainda mais claro no hover */
        border-color: var(--color-primary); /* Borda com cor primária no hover */
        color: var(--color-primary); /* Texto com cor primária no hover */
    }
    [data-testid="baseButton-secondary"] button:active {
         background-color: var(--color-border); /* Um pouco mais escuro no active */
         box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); /* Sombra interna sutil */
    }
    /* Style for form submit button */
     [data-testid="FormSubmitButton"] button {
         background-color: var(--color-primary); /* Fundo com cor primária */
         color: white; /* Texto branco */
         border: 1px solid var(--color-primary); /* Borda primária */
         box-shadow: 0 4px 8px rgba(var(--color-primary-rgb), 0.3); /* Sombra mais proeminente para submit */
     }
     [data-testid="FormSubmitButton"] button:hover {
         background-color: #3A7AD2; /* Darker primary on hover */
         border-color: #3A7AD2;
         color: white;
         box-shadow: 0 6px 10px rgba(var(--color-primary-rgb), 0.4);
     }
     [data-testid="FormSubmitButton"] button:active {
         background-color: #2A5BA2;
         border-color: #2A5BA2;
         box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
     }


    /* Inputs de Texto, Número, Área de Texto, Selectboxes */
    /* Target the input/textarea/select elements directly or their containers */
    input[type="text"], input[type="number"], textarea, [data-testid="stSelectbox"] > div > div {
        border-radius: 5px;
        padding: 0.8rem 1rem;
        border: 1px solid var(--color-border);
        width: 100%;
        box-sizing: border-box;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        background-color: white; /* Explicitly white background for inputs */
        color: var(--color-text); /* Explicitly text color for inputs */
    }
    input[type="text"]:focus, input[type="number"]:focus, textarea:focus, [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: var(--color-primary);
        box-shadow: 0 0 5px rgba(var(--color-primary-rgb), 0.3); /* Sombra mais suave no focus */
        outline: none;
    }
    /* Ensure text color inside selectbox is correct */
     [data-testid="stSelectbox"] div[data-baseweb="select"] div,
     [data-testid="stSelectbox"] div[data-baseweb="select"] span {
         color: var(--color-text) !important;
     }


     /* Radio buttons and Checkboxes */
     [data-testid="stRadio"] > div, [data-testid="stCheckbox"] > label {
         margin-bottom: 0.5rem; /* Smaller margin */
     }
     [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
         color: var(--color-text); /* Ensure label text color is correct */
     }


    /* Feedback Boxes (Info, Success, Warning, Error) */
    /* Warning: These selectors are highly unstable and may break in future Streamlit versions! */
    .css-1aumqxt { border-left: 5px solid var(--color-info) !important; background-color: #EBF5FB; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.info - light blue */
    .css-1r6cdft { border-left: 5px solid var(--color-warning) !important; background-color: #FFFDE7; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.warning - light yellow */
    .css-t9s6qg { border-left: 5px solid var(--color-error) !important; background-color: #FFEBEE; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.error - light red */
    .css-1u3jtzg { border-left: 5px solid var(--color-success) !important; background-color: #E8F5E9; color: var(--color-text); border-radius: 5px; padding: 1rem; margin-bottom: 1rem;} /* st.success - light green */


    /* Spinners */
    .stSpinner > div > div {
        border-top-color: var(--color-primary) !important;
    }

    /* Expander (Menus Sanfona) */
    .streamlit-expanderHeader {
        font-size: 1.1em !important; /* Slightly smaller */
        font-weight: 600 !important; /* Semibold */
        color: var(--color-primary) !important;
        background-color: var(--color-background-light);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1.5rem; /* Adjusted margin */
        border: 1px solid var(--color-border);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); /* Softer shadow */
        transition: all 0.2s ease-in-out;
    }
    .streamlit-expanderHeader:hover {
         background-color: var(--color-background-mid);
    }
    .streamlit-expanderContent {
         background-color: #FFFFFF; /* White background for content */
         padding: 1.5rem;
         border-left: 1px solid var(--color-border);
         border-right: 1px solid var(--color-border);
         border-bottom: 1px solid var(--color-border);
         border-radius: 0 0 8px 8px;
         margin-bottom: 1rem;
         box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); /* Softer shadow */
    }

    /* Separadores */
    hr {
        margin-top: 1.5em; /* Adjusted margin */
        margin-bottom: 1.5em; /* Adjusted margin */
        border: 0;
        border-top: 1px solid var(--color-border);
    }

    /* Image upload area label */
    [data-testid="stFileUploader"] label {
        font-weight: 600; /* Semibold */
        color: var(--color-light-text);
    }

    /* Centralize images and maps */
     [data-testid="stImage"], [data-testid="stMap"], [data-testid="stDeckGlChart"], [data-testid="stComponentsV1"] iframe {
          display: block;
          margin-left: auto;
          margin-right: auto;
          max-width: 100%;
          margin-top: 1rem;
          margin-bottom: 1rem;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Add shadow to visual elements */
     }
     /* Ensure iframes inside components also respect styling */
     [data-testid="stComponentsV1"] iframe {
          border: none; /* Remove default iframe border */
     }

</style>
""", unsafe_allow_html=True)


# --- Inicialização de Estado da Sessão ---
# Gerencia o fluxo da aplicação web e os dados coletados/processados
if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'denuncia_completa' not in st.session_state:
    # Initialize denuncia_completa with structure and default IA status messages
    st.session_state.denuncia_completa = {
        'denunciante': {},
        'buraco': {
            'endereco': {},
            'structured_details': {},
            'observacoes_adicionais': '',
            'numero_proximo': '',
            'lado_rua': '',
            'cep_informado': ''
        },
        'localizacao_exata_processada': {"tipo": "Não informada", "motivo_falha_geocodificacao_anterior": "Não tentada/aplicável", "input_original":""},
        'streetview_image_data': {"erro": "Status Street View: Não iniciada."},
        'image_analysis_ia': {"image_analysis": "Status Análise Imagem IA: Não iniciada."},
        'insights_ia': {"insights": "Status Análise Detalhada IA: Não iniciada."},
        'urgencia_ia': {"urgencia_ia": "Status Sugestão Urgência IA: Não iniciada."},
        'sugestao_acao_ia': {"sugestao_acao_ia": "Status Sugestões Causa/Ação IA: Não iniciada."},
        'resumo_ia': {"resumo_ia": "Status Geração Resumo IA: Não iniciada."},
    }

if 'api_keys_loaded' not in st.session_state:
    st.session_state.api_keys_loaded = False
if 'gemini_pro_model' not in st.session_state: # Modelo para texto
    st.session_state.gemini_pro_model = None
if 'gemini_vision_model' not in st.session_state: # Modelo para visão
    st.session_state.gemini_vision_model = None
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None
if 'uploaded_image_bytes' not in st.session_state: # Armazena bytes da imagem
    st.session_state.uploaded_image_bytes = None
if 'uploaded_image_type' not in st.session_state: # Armazena tipo da imagem
    st.session_state.uploaded_image_type = None
if 'endereco_coletado_via' not in st.session_state:
    st.session_state.endereco_coletado_via = None # 'cep' or 'manual'


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

    warnings = []
    if not gemini_key:
        warnings.append("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA do Gemini estarão desabilitadas.")
    if not geocoding_key:
        warnings.append("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática, Visualização Google Maps Embed e Street View Static estarão desabilitadas.")
        warnings.append("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit (se ainda não existir a pasta `.streamlit`) com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\n**IMPORTANTE:** Não comite o arquivo `secrets.toml` para repositórios públicos no GitHub! O Streamlit Cloud tem uma interface segura para adicionar estes segredos.")
        warnings.append("❗ As APIs Google Maps (Geocoding, Embed, Street View Static) PODE gerar custos. Verifique a precificação do Google Cloud e habilite-as no seu projeto Google Cloud Platform (Console -> APIs & Services -> Library). O erro 'This API project is not authorized to use this API' geralmente significa que a API específica não está habilitada ou autorizada para a chave.")

    # Exibe todos os avisos juntos
    for warning in warnings:
         st.warning(warning)

    return gemini_key, geocoding_key

# --- Inicializar APIs (Cacheado para performance) ---

@st.cache_resource
def init_gemini_models(api_key: Optional[str]) -> tuple[Optional[genai.GenerativeModel], Optional[genai.GenerativeModel]]:
    """Inicializa os modelos Google Gemini (Pro e Vision) com cache."""
    if not api_key:
        st.warning("🚫 Chave de API Gemini não fornecida. Modelos Gemini não serão inicializados.")
        return None, None # Retorna None para ambos se a chave não for fornecida

    model_pro = None
    model_vision = None
    success_messages = []
    warning_messages = []

    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models()]

        # Inicializar Gemini-Pro (ou Flash) para texto
        preferred_text_models: list[str] = ['gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        text_model_name: Optional[str] = None
        for pref_model in preferred_text_models:
            full_name = f'models/{pref_model}'
            if full_name in available_models:
                text_model_name = full_name
                break
            if pref_model in available_models: # Fallback check
                 text_model_name = pref_model
                 break


        if text_model_name:
             model_pro = genai.GenerativeModel(text_model_name)
             success_messages.append(f"✅ Conexão com Google Gemini (Texto) estabelecida usando modelo '{text_model_name}'.")
        else:
             warning_messages.append("⚠️ Nenhum modelo de texto Gemini compatível (como 1.5 Flash, 1.0 Pro ou Pro) encontrado na sua conta.")


        # Inicializar Gemini-Vision para análise de imagem
        vision_model_name = 'gemini-pro-vision'
        vision_model_full_name = f'models/{vision_model_name}'
        if vision_model_full_name in available_models or vision_model_name in available_models:
            model_vision = genai.GenerativeModel(vision_model_full_name if vision_model_full_name in available_models else vision_model_name)
            success_messages.append(f"✅ Conexão com Google Gemini (Visão) estabelecida usando modelo '{vision_model_name}'.")
        else:
            warning_messages.append(f"⚠️ Modelo Gemini Vision ('{vision_model_name}') não encontrado ou compatível na sua conta. Análise de imagem desabilitada.")

        # Report results
        for msg in success_messages: st.success(msg)
        for msg in warning_messages: st.warning(msg)

        if model_pro or model_vision:
            st.info("A IA está online e pensativa!")
        elif not success_messages and not warning_messages:
             st.warning("⚠️ Não foi possível encontrar modelos Gemini disponíveis com a chave fornecida. Verifique sua chave e os modelos disponíveis para seu projeto.")


        return model_pro, model_vision

    except Exception as e:
        st.error(f"❌ ERRO Crítico na Inicialização Gemini: Falha na inicialização dos modelos Google Gemini. Verifique sua chave, habilitação dos modelos no Google Cloud e status do serviço.")
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
    # Permitir geocodificação mesmo sem número, mas alertar que pode ser imprecisa
    if not rua or not cidade or not estado:
         return {"erro": "Dados de endereço insuficientes (requer rua, cidade, estado) para geocodificar."}

    # Construir o endereço para a API. Incluir número se disponível.
    address_parts = [rua.strip()]
    if numero and numero.strip():
         address_parts.append(numero.strip())
    address_parts.extend([cidade.strip(), estado.strip()])
    address = ", ".join(address_parts)

    if not address or address.replace(',', '').strip() == "":
         return {"erro": "Endereço vazio ou inválido para geocodificação."}


    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&key={api_key}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            status = data.get('status', 'STATUS DESCONHECIDO')
            # Tentativa de extrair mensagem de erro mais detalhada da resposta JSON
            error_msg = data.get('error_message', 'Sem mensagem adicional.')
            # Verifica se o status indica problema na chave/autorização
            if status == 'REQUEST_DENIED':
                 error_msg = f"REQUEST_DENIED. Causa: {data.get('error_message', 'API não habilitada ou chave inválida/restrita?')}"
                 # Add specific instructions for REQUEST_DENIED
                 error_msg += " Verifique se a 'Geocoding API' está habilitada e autorizada para sua chave no Google Cloud."
            elif status == 'ZERO_RESULTS':
                 error_msg = "ZERO_RESULTS. Nenhum local encontrado para o endereço (verifique o endereço completo)."


            return {"erro": f"Geocodificação falhou. Status: {status}. Mensagem: {error_msg}"}
        if not data['results']:
             # Esta condição já deveria ser coberta por status 'ZERO_RESULTS', mas é um fallback seguro
             return {"erro": "Geocodificação falhou. Nenhum local exato encontrado para o endereço fornecido."}

        location = data['results'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = data['results'][0].get('formatted_address', address)

        # O link embed usa a mesma chave da Geocoding API, mas a Maps Embed API precisa estar habilitada
        google_embed_link = None
        # Verificar se a API Embed está habilitada na chave (não diretamente possível via Geocoding API,
        # mas geramos o link se a chave existe e assumimos que a API Embed pode estar habilitada).
        # O erro de habilitação aparecerá no iframe.
        if api_key:
             google_embed_link = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"

        return {
            "latitude": lat,
            "longitude": lng,
            "endereco_formatado_api": formatted_address,
            "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
            "google_embed_link_gerado": google_embed_link # Pode ser None se chave faltar
        }
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao tentar geocodificar: {address}"}
    except requests.exceptions.RequestException as e:
        # Capture specific HTTP errors like 403 (Forbidden)
        error_msg = f"Erro na comunicação com a API de Geocodificação: {address}. Detalhes: {e}"
        if e.response is not None and e.response.status_code == 403:
             error_msg = "Erro 403 (Forbidden): A chave de API não está autorizada a usar a Geocoding API. Verifique se a 'Geocoding API' está habilitada e autorizada para sua chave no Google Cloud."
        return {"erro": error_msg}
    except Exception as e:
        return {"erro": f"Ocorreu um erro inesperado durante a geocodificação: {address}. Detalhes: {e}"}

# --- Função: Obter Imagem Street View ---
@st.cache_data(show_spinner="📸 Obtendo imagem Street View do local...")
def get_street_view_image(lat: float, lon: float, api_key: Optional[str], size: str = "600x400", heading: int = 0) -> Dict[str, Any]:
    """
    Tenta obter uma imagem Street View estática para as coordenadas fornecidas.
    Retorna os bytes da imagem em {"image_bytes": ...} ou um dicionário de erro {"erro": ...}.
    """
    if not api_key:
        return {"erro": "Chave de API de Geocodificação/Street View não fornecida."}

    # Construir a URL da Street View Static API
    location = f"{lat},{lon}"
    # Usamos um heading fixo (0=Norte) como padrão. Ajuste se necessário.
    # heading=0 (Norte), 90 (Leste), 180 (Sul), 270 (Oeste). Poderia tentar múltiplos.

    url = f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={location}&heading={heading}&key={api_key}&return_error_code=true" # Adiciona para obter códigos em vez de imagens de erro

    try:
        response = requests.get(url, timeout=15)
        # response.raise_for_status() # Não usar raise_for_status() se return_error_code=true, pois 4xx/5xx são esperados para indicar erros específicos da API

        # A API Street View Static retorna uma imagem (status 200) ou um código de erro/imagem de erro (status 4xx/5xx)
        if response.status_code == 200:
             # Verifica se o Content-Type é realmente uma imagem
             if response.headers.get('Content-Type', '').startswith('image'):
                  return {"image_bytes": response.content}
             else:
                  # Isso pode acontecer se return_error_code=true mas a resposta não é bem formada
                  return {"erro": f"API Street View retornou status 200, mas o conteúdo não é uma imagem. Content-Type: {response.headers.get('Content-Type', 'Não especificado')}."}
        elif response.status_code == 404: # Not Found - Generally means no coverage
             return {"erro": "Nenhuma imagem Street View encontrada para este local (Erro 404 - Sem cobertura?)."}
        elif response.status_code == 403: # Forbidden - API not enabled or key unauthorized
             return {"erro": "Erro 403 (Forbidden): A chave de API não está autorizada a usar a Street View Static API. Verifique se a 'Street View Static API' está habilitada e autorizada para sua chave no Google Cloud."}
        elif response.status_code == 400: # Bad Request - Includes Invalid_Request, Photo_Not_Found (if using pano id), etc.
             # API might return text in the body for 400 errors with return_error_code=true
             error_details = response.text.strip() if response.text else f"Status {response.status_code}"
             # Check for specific error messages if available in text body (less reliable)
             if "fallback to a panorama" in error_details:
                 # This often happens when heading/pitch is invalid for the pano. We use heading=0, pitch=0. Should be OK.
                  pass # Not a critical error message to report prominently

             return {"erro": f"Erro {response.status_code} da API Street View. Detalhes: {error_details[:200]}..."} # Limit details for display
        else:
            # Any other unexpected status code
            return {"erro": f"Erro inesperado da API Street View. Status: {response.status_code}. Detalhes: {response.text[:200]}..."}


    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao obter Street View para {location}."}
    except requests.exceptions.RequestException as e:
        # Catch network errors, invalid URLs, etc.
        return {"erro": f"Erro na comunicação com a API Street View para {location}. Detalhes: {e}"}
    except Exception as e:
         return {"erro": f"Ocorreu um erro inesperado durante a obtenção de Street View para {location}. Detalhes: {e}"}


# --- Funções de Análise de IA ---
# Safety settings configuradas para permitir discussões sobre perigos na rua,
# mas tentando guiar a IA para descrições objetivas de risco e dano.
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}, # Mantido como BLOCK_NONE
]

# Função auxiliar para processar a resposta do Gemini e extrair texto ou erro
def process_gemini_response(response: Any, context: str) -> str:
    """Processa a resposta do Gemini, retornando o texto ou uma mensagem de erro detalhada."""
    try:
        # Check if response is None or empty before accessing attributes
        if response is None:
             return f"❌ Resposta Vazia ou Nula do Gemini durante a {context}."

        # Prioritize checking for prompt feedback (blocking)
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
             if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                  block_reason = response.prompt_feedback.block_reason.name
                  # More detailed block info if available
                  block_details = ""
                  if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                       ratings = ", ".join([f"{r.category.name}: {r.probability.name}" for r in response.prompt_feedback.safety_ratings])
                       block_details = f" (Ratings: {ratings})"
                  # Log block reason to console for debugging
                  st.error(f"DEBUG: Blocked during {context}. Reason: {block_reason} {block_details}")
                  return f"❌ Análise bloqueada pelo filtro de segurança do Gemini durante a {context}. Motivo: {block_reason}{block_details}"
             elif hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                  # Block occurred, but reason not explicitly set? Still report ratings.
                  ratings = ", ".join([f"{r.category.name}: {r.probability.name}" for r in response.prompt_feedback.safety_ratings])
                  st.error(f"DEBUG: Blocked during {context}. No explicit reason, ratings: {ratings}")
                  return f"❌ Análise bloqueada pelo filtro de segurança do Gemini durante a {context} (sem motivo explícito, ratings: {ratings})."


        # Check for successful content if not blocked
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
             # If candidates exist but .text is empty, maybe try accessing the first candidate's text
             if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                  # Assuming the first part is text
                  # Convert part to string explicitly
                  part_content = response.candidates[0].content.parts[0]
                  return str(part_content).strip()
             else:
                  st.error(f"DEBUG: Gemini response has candidates but no text parts during {context}.")
                  return f"❌ A resposta do Gemini durante a {context} não contém texto processável, mas candidatos foram retornados."
        else:
             # This case means no text, no candidates, and no explicit prompt_feedback block
             # It could be an API error or other unexpected response structure
             st.error(f"DEBUG: Gemini response has no content, candidates, or feedback during {context}. Response: {response}")
             return f"❌ A resposta do Gemini durante a {context} não contém conteúdo nem feedback de bloqueio. Resposta completa (estrutura): {response}" # Show response structure for debug


    except Exception as e:
        # Catch errors *during* processing the response object
        st.error(f"DEBUG: Unexpected error processing Gemini response during {context}: {e}. Response was: {response}")
        return f"❌ Erro inesperado ao processar a resposta do Gemini durante a {context}: {e}. Resposta original: {response}" # Include original response object structure


def analyze_image_with_gemini_vision(image_bytes: bytes, image_type: str, model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini Vision para analisar uma imagem e extrair características do buraco."""
    if not model:
        return {"image_analysis": "🤖 Análise de imagem via IA indisponível (Motor Gemini Vision offline ou não configurado)."}
    if not image_bytes:
         return {"image_analysis": "🔍 Nenhuma imagem fornecida pelo usuário para análise de IA."}
    if not image_type:
         # Should not happen if uploaded via st.file_uploader, but check
         return {"image_analysis": "🔍 Tipo de imagem não detectado. Não é possível analisar."}


    try:
        # Prepare image part with correct mime type
        # Validate mime type before sending to ensure it's image/*
        if not image_type.startswith('image/'):
             return {"image_analysis": f"❌ Tipo de arquivo inválido para análise de imagem: '{image_type}'. Esperado 'image/*'."}

        image_parts = [{"mime_type": image_type, "data": image_bytes}]

        prompt = [
            "Analise a imagem fornecida de um buraco em uma estrada. Descreva as características visíveis relevantes para um relatório de reparo de estrada.",
            "Concentre-se em descrições OBJETIVAS baseadas *APENAS* no que é visível na imagem:",
            "- Tamanho estimado (pequeno, médio, grande, diâmetro em relação a objetos comuns se visível)",
            "- Profundidade estimada (raso, fundo, em relação a objetos visíveis)",
            "- Presença de água ou umidade",
            "- Condição do pavimento imediatamente ao redor (rachado, esfarelando, afundado, etc.)",
            "- Quaisquer objetos ou condições *visíveis* na imagem que possam indicar risco ou contexto (por exemplo, detritos na pista, desnível, localização aparente em via de tráfego, proximidade de faixa de pedestre).",
            "Forneça uma análise textual concisa, factual e baseada EXCLUSIVAMENTE no conteúdo da imagem. Evite termos excessivamente dramáticos ou juízos de valor; descreva o que é visto de forma direta e útil para um engenheiro de manutenção de vias.", # <--- VÍRGULA ADICIONADA AQUI
            image_parts[0] # Adiciona a imagem ao prompt
        ]

        # Using generate_content with safety settings
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        analysis_text = process_gemini_response(response, "análise de imagem")

        return {"image_analysis": analysis_text}

    except Exception as e:
        # This catch should be for errors *before* or *during* the API call itself
        st.error(f"❌ Erro inesperado ao chamar a API Gemini Vision: {e}")
        return {"image_analysis": f"❌ Erro inesperado ao chamar a API Gemini Vision: {e}"}


# Não cachear a análise de imagem diretamente aqui, será chamada no fluxo principal se houver imagem
# As funções de análise de texto são cacheadas para evitar chamadas repetidas na mesma sessão
# com os MESMOS inputs (o dicionário de dados).

@st.cache_data(show_spinner=False) # Spinner is managed manually in processing_ia
def analisar_dados_com_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini (texto) para analisar dados estruturados, observações e análise de imagem."""
    if not _model:
        return {"insights": "🤖 Análise de dados via IA indisponível (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache, mas extraia o que é relevante para o prompt
    _dados_buraco = _dados_denuncia_completa.get('buraco', {})
    _image_analysis_ia = _dados_denuncia_completa.get('image_analysis_ia', {})

    structured_details = _dados_buraco.get('structured_details', {})
    observacoes_adicionais = _dados_buraco.get('observacoes_adicionais', 'Sem observações adicionais.')

    structured_text = "Detalhes Estruturados Fornecidos pelo Usuário:\n"
    informed_structured_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}

    if informed_structured_details:
         for key in ['tamanho', 'profundidade', 'presenca_agua', 'perigo', 'contexto', 'perigos_detalhados', 'identificadores_visuais']: # Maintain order
             value = informed_structured_details.get(key)
             if value is not None: # Check if key exists and has a value
                  value_str = ", ".join(value) if isinstance(value, list) else value
                  # Traduz as chaves para o prompt de forma mais amigável (manter consistência com os inputs)
                  key_translated = {
                      'tamanho': 'Tamanho Estimado',
                      'perigo': 'Nível de Risco Aparente (User)', # Especifica que é do usuário
                      'profundidade': 'Profundidade Estimada',
                      'presenca_agua': 'Presença de Água',
                      'contexto': 'Contexto/Histórico do Local (User)', # Especifica que é do usuário
                      'perigos_detalhados': 'Fatores de Risco e Impactos Detalhados (User)', # Especifica que é do usuário
                      'identificadores_visuais': 'Identificadores Visuais Adicionais (User)', # Especifica que é do usuário
                  }.get(key, key)
                  structured_text += f"- {key_translated}: {value_str}\n"
    else:
         structured_text += "Nenhum detalhe estruturado relevante informado pelo usuário.\n"


    # Adiciona a análise de imagem ao contexto da IA, se disponível, limpando prefixos de erro para o prompt
    image_analysis_text_raw = _image_analysis_ia.get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    if image_analysis_text_raw.startswith("❌"): # If image analysis failed, just report that for the text model context
         image_context = f"Insights da Análise de Imagem do Usuário (IA Gemini Vision): {image_analysis_text_raw}"
    else: # If image analysis succeeded, include its content
         image_context = f"Insights da Análise de Imagem do Usuário (IA Gemini Vision):\n{image_analysis_text_raw}"


    # Inclui info de localização processada para contexto (sem detalhes sensíveis de API)
    loc_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    loc_context_text = f"Localização Exata (Tipo Processado): {loc_exata.get('tipo', 'Não informado')}. "
    if loc_exata.get('latitude') is not None and loc_exata.get('longitude') is not None:
        loc_context_text += f"Coordenadas: [Latitude, Longitude]. " # Evita expor coordenadas exatas no prompt se sensível? (O Google diz que dados enviados são privados, mas melhor ser seguro) Ou manter? Manter para a IA ser precisa.
        loc_context_text = f"Localização Exata (Tipo Processado): {loc_exata.get('tipo', 'Não informado')}. Coordenadas: {loc_exata.get('latitude')},{loc_exata.get('longitude')}. "
    if loc_exata.get('descricao_manual'):
         loc_context_text += f"Descrição Manual: '{loc_exata.get('descricao_manual')}'."
    if loc_exata.get('input_original'):
         loc_context_text += f" Input Original: '{loc_exata.get('input_original')}'."


    prompt = f"""
    Analise os seguintes dados sobre um buraco em uma rua: detalhes estruturados fornecidos pelo usuário, observações adicionais do usuário, análise de imagem gerada por IA (se disponível), e contexto de localização.
    Gere uma análise detalhada objetiva para um relatório de reparo de via. Concentre-se em consolidar as informações sobre características físicas do buraco, fatores de risco, e contexto relevante.
    Use linguagem clara, formal e focada em fatos inferidos dos inputs. Sua análise deve ser útil para uma equipe técnica avaliar a situação. Se a informação para uma categoria NÃO FOR CLARA, CONSISTENTE ou NÃO ESTIVER PRESENTE NOS DADOS FORNECIDOS, indique "Não claro/inconsistente nos dados" ou similar.

    Dados Brutos e Análises Iniciais Fornecidas:
    {structured_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    {image_context}
    Contexto de Localização: {loc_context_text}

    Análise Detalhada Consolidada (Baseada APENAS nos dados acima):
    - Severidade e Características Físicas: [Consolide tamanho e profundidade informados pelo usuário e/ou visíveis na imagem. Descreva a forma e condição visível do buraco e pavimento adjacente. Mencione se os inputs divergem ou reforçam as mesmas conclusões.]
    - Presença de Água/Umidade: [Confirme a presença ou ausência conforme inputs/imagem.]
    - Fatores de Risco e Potenciais Impactos: [Liste riscos específicos citados nos inputs estruturados (seleções, texto libre), e/ou inferidos da análise de imagem ou contexto. Foco nos perigos objetivos para veículos (pneu, suspensão, roda), motos, bicicletas e pedestres.]
    - Contexto e Referências: [Integre contexto (tráfego, recorrência, etc.) e identificadores visuais que ajudem a localizar ou entender a situação do buraco (ex: perto de esquina, em curva, via movimentada).]
    - Palavras-chave para Indexação: [Liste 3-7 palavras-chave relevantes.]

    Formate a resposta usando marcadores (-) para cada categoria.
    """
    try:
        # Adding a small delay to make the spinner visible if cached
        time.sleep(0.5)
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        insights_text = process_gemini_response(response, "análise detalhada")
        return {"insights": insights_text}

    except Exception as e:
        st.error(f"❌ Erro inesperado ao chamar a API Gemini (Análise Detalhada): {e}")
        return {"insights": f"❌ Erro inesperado ao chamar a API Gemini (Análise Detalhada): {e}"}


@st.cache_data(show_spinner=False) # Spinner is managed manually
def categorizar_urgencia_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir uma categoria de urgência com base em todos os dados e insights."""
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache
    # Acessa todos os dados relevantes
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    # Pass the *result* of previous analyses to the prompt
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível ou com erro.')


    loc_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    loc_contexto = f"Localização Processada (Tipo): {loc_exata.get('tipo', 'Não informada')}."
    if loc_exata.get('latitude') is not None and loc_exata.get('longitude') is not None:
        loc_contexto += f" Coordenadas Processadas: [Latitude, Longitude]." # Obfuscate coords slightly for prompt
    elif loc_exata.get('descricao_manual'):
         loc_contexto += f" Descrição Manual: '{loc_exata.get('descricao_manual', 'Não informada')}'."


    # Formatar os detalhes estruturados para o prompt de urgência
    structured_urgency_factors = []
    informed_structured_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}
    if informed_structured_details:
         for key in ['tamanho', 'profundidade', 'presenca_agua', 'perigo', 'contexto', 'perigos_detalhados']:
             value = informed_structured_details.get(key)
             if value is not None:
                  value_str = ", ".join(value) if isinstance(value, list) else value
                  key_translated = {
                      'tamanho': 'Tamanho Estimado',
                      'perigo': 'Nível de Risco Aparente (User)',
                      'profundidade': 'Profundidade Estimada',
                      'presenca_agua': 'Presença de Água',
                      'contexto': 'Contexto/Histórico (User)',
                      'perigos_detalhados': 'Fatores de Risco Detalhados (User)',
                  }.get(key, key)
                  structured_urgency_factors.append(f"{key_translated}: {value_str}")
    structured_urgency_text = "Detalhes Estruturados do Usuário: " + ("; ".join(structured_urgency_factors) if structured_urgency_factors else "Nenhum informado pelo usuário.")


    # Remove error prefixes for the prompt
    image_analysis_for_prompt = image_analysis_text if not image_analysis_text.startswith("❌") else f"Análise de imagem com erro: {image_analysis_text[2:].strip()}"
    insights_for_prompt = insights_text if not insights_text.startswith("❌") else f"Análise detalhada com erro: {insights_text[2:].strip()}"


    prompt = f"""
    Com base nas informações da denúncia (detalhes estruturados do usuário, observações, análise de imagem e análise detalhada geradas por IA) e no contexto de localização, sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade (tamanho/profundidade), FATORES DE RISCO E IMPACTOS (mencionados pelo usuário e/ou inferidos pelas IAs), e qualquer CONTEXTO ADICIONAL relevante (local de alto tráfego, recorrência, etc.). Dê peso especial aos FATORES DE RISCO e IMPACTOS. Use as informações mais confiáveis disponíveis (input estruturado > análise de imagem > observações/análise detalhada).

    Escolha UMA Categoria de Urgência entre estas (seja objetivo):
    - Urgência Baixa: Pequeno, sem fator de risco claro, em local de baixo tráfego.
    - Urgência Média: Tamanho razoável, risco menor/moderado (dano leve a veículo), via secundária ou tráfego moderado.
    - Urgência Alta: Grande/profundo, risco significativo (acidente sério, dano a veículo/moto/bike/pedestre), via movimentada ou área de risco.
    - Urgência Imediata/Crítica: Enorme/muito profundo, risco GRAVE/iminente (acidentes constantes, interdição), afeta fluidez severamente.

    Informações Relevantes da Denúncia para Avaliação de Urgência:
    Localização Contexto: {loc_contexto}
    {structured_urgency_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_for_prompt}
    Insights da Análise de Imagem (se disponível): {image_analysis_for_prompt}

    Com base nestes dados consolidados, qual categoria de urgência você sugere?
    Forneça APENAS a categoria escolhida e uma breve JUSTIFICATIVA (máximo 3 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais relevantes (severidade, risco, contexto) dos inputs ou análises que justificam a urgência.

    Formato de saída (muito importante seguir este formato exato):
    Categoria Sugerida: [Categoria Escolhida]
    Justificativa: [Justificativa Breve]
    """
    try:
        # Adding a small delay
        time.sleep(0.5)
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        urgencia_text = process_gemini_response(response, "sugestão de urgência")
        return {"urgencia_ia": urgencia_text}

    except Exception as e:
        st.error(f"❌ Erro inesperado ao chamar a API Gemini (Sugestão de Urgência): {e}")
        return {"urgencia_ia": f"❌ Erro inesperado ao chamar a API Gemini (Sugestão de Urgência): {e}"}


@st.cache_data(show_spinner=False) # Spinner is managed manually
def sugerir_causa_e_acao_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir possíveis causas do buraco e ações de reparo com base nos dados e insights."""
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache
    # Acessa todos os dados relevantes
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = _dados_denuncia_completa.get('buraco', {}).get('observacoes_adicionais', 'Sem observações adicionais.')
    # Pass the *result* of previous analyses to the prompt
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível ou com erro.')


    structured_action_factors = []
    informed_structured_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}
    if informed_structured_details:
         for key in ['tamanho', 'profundidade', 'presenca_agua', 'contexto', 'perigos_detalhados']:
              value = informed_structured_details.get(key)
              if value is not None:
                   value_str = ", ".join(value) if isinstance(value, list) else value
                   key_translated = {
                       'tamanho': 'Tamanho Estimado',
                       'profundidade': 'Profundidade Estimada',
                       'presenca_agua': 'Presença de Água',
                       'contexto': 'Contexto/Histórico (User)',
                       'perigos_detalhados': 'Fatores de Risco Detalhados (User)',
                   }.get(key, key)
                   structured_action_factors.append(f"{key_translated}: {value_str}")
    structured_action_text = "Detalhes Estruturados do Usuário: " + ("; ".join(structured_action_factors) if structured_action_factors else "Nenhum informado pelo usuário.")


    # Remove error prefixes for the prompt
    image_analysis_for_prompt = image_analysis_text if not image_analysis_text.startswith("❌") else f"Análise de imagem com erro: {image_analysis_text[2:].strip()}"
    insights_for_prompt = insights_text if not insights_text.startswith("❌") else f"Análise detalhada com erro: {insights_text[2:].strip()}"


    prompt = f"""
    Com base nas informações completas da denúncia (dados estruturados do usuário, observações, análise de imagem e insights gerados por IA), tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico. Baseie-se em pistas nos inputs (ex: se é recorrente, se há água/umidade/drenagem, condição do pavimento adjacente visível na imagem/mencionado, contexto de tráfego/histórico). Seja especulativo, mas baseado nos dados fornecidos.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema. Baseie-se na severidade (tamanho/profundidade), fatores de risco, contexto e condição do pavimento. Sugira ações práticas para uma equipe de manutenção (ex: simples tapa-buraco, recapeamento de seção, inspeção de drenagem, sinalização de emergência temporária, interdição parcial da via).

    Baseie suas sugestões APENAS nos dados fornecidos. Se a informação for insuficiente para inferir causas ou ações, indique "Não especificado/inferido nos dados".

    Informações Relevantes para Inferência de Causa e Sugestão de Ação:
    {structured_action_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_for_prompt}
    Insights da Análise de Imagem (se disponível): {image_analysis_for_prompt}

    Formato de saída (muito importante seguir este formato exato):
    Possíveis Causas Sugeridas: [Lista de causas sugeridas baseadas nos dados ou 'Não especificado/inferido nos dados']
    Sugestões de Ação/Reparo Sugeridas: [Lista de ações sugeridas baseadas nos dados ou 'Não especificado/inferido nos dados']
    """
    try:
        # Adding a small delay
        time.sleep(0.5)
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        sugestao_acao_text = process_gemini_response(response, "sugestões de causa e ação")
        return {"sugestao_acao_ia": sugestao_acao_text}

    except Exception as e:
        st.error(f"❌ Erro inesperado ao chamar a API Gemini (Sugestões Causa/Ação): {e}")
        return {"sugestao_acao_ia": f"❌ Erro inesperado ao chamar a API Gemini (Sugestões Causa/Ação): {e}"}


@st.cache_data(show_spinner=False) # Spinner is managed manually
def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para gerar um resumo narrativo inteligente da denúncia completa."""
    if not _model:
        return {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache
    # Acessa todos os dados coletados e resultados das IAs
    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})

    image_analysis_ia = _dados_denuncia_completa.get('image_analysis_ia', {})
    insights_ia = _dados_denuncia_completa.get('insights_ia', {})
    urgencia_ia = _dados_denuncia_completa.get('urgencia_ia', {})
    sugestao_acao_ia = _dados_denuncia_completa.get('sugestao_acao_ia', {})
    streetview_image_data = _dados_denuncia_completa.get('streetview_image_data', {}) # Dados da imagem Street View


    # Formatar a string de localização para o resumo
    loc_info_resumo = "Localização exata não especificada ou processada de forma estruturada."
    tipo_loc_processada = localizacao_exata.get('tipo', 'Não informada')

    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         lat = localizacao_exata.get('latitude')
         lon = localizacao_exata.get('longitude')
         link_gerado = localizacao_exata.get('google_maps_link_gerado', 'Não disponível')
         loc_info_resumo = f"Localização Processada: Coordenadas {lat}, {lon} (Obtida via: {tipo_loc_processada.replace(' (API)', ' API').replace('Manual', 'Manual').replace('Fornecidas/Extraídas', 'Manual')}). Link Google Maps: {link_gerado}."
         # Não inclui input original aqui para manter o resumo mais limpo, já que está no relatório completo

    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização Processada via descrição manual detalhada: '{localizacao_exata.get('descricao_manual', 'Não informada')}'."

    elif localizacao_exata.get('input_original') and tipo_loc_processada == 'Não informada':
         loc_info_resumo = f"Localização Processada (input original): '{localizacao_exata.get('input_original')}' (Tipo não detectado)."
    else:
         # Se não há localização processada, mas tem endereço base, inclui o endereço base
         if endereco.get('rua') or endereco.get('cidade_buraco') or endereco.get('estado_buraco'):
              loc_info_resumo = f"Localização Base Informada: Rua {endereco.get('rua', 'Não informada')}, Nº Próximo: {buraco.get('numero_proximo', 'Não informado')}. Cidade: {endereco.get('cidade_buraco', 'Não informada')}, Estado: {endereco.get('estado_buraco', 'Não informado')}."


    # Formatar os detalhes estruturados para inclusão no resumo
    structured_summary_items = []
    informed_structured_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}

    if informed_structured_details:
         for key in ['tamanho', 'profundidade', 'presenca_agua', 'perigo', 'contexto', 'perigos_detalhados', 'identificadores_visuais']:
              value = informed_structured_details.get(key)
              if value is not None: # Check if key exists and has a value
                   key_translated = {
                      'tamanho': 'Tamanho',
                      'perigo': 'Risco Aparente',
                      'profundidade': 'Profundidade',
                      'presenca_agua': 'Água',
                      'contexto': 'Contexto',
                      'perigos_detalhados': 'Perigos Específicos',
                      'identificadores_visuais': 'Identificadores Visuais',
                   }.get(key, key)
                   value_str = ", ".join(value) if isinstance(value, list) else value
                   structured_summary_items.append(f"{key_translated}: {value_str}")

    structured_summary_text = "Detalhes Estruturados Principais (User): " + ("; ".join(structured_summary_items) if structured_summary_items else "Nenhum detalhe estruturado relevante fornecido.")

    # Adicionar informação sobre Street View ao resumo
    streetview_summary = ""
    if streetview_image_data and 'image_bytes' in streetview_image_data:
         streetview_summary = " Imagem Street View do local obtida."
    elif streetview_image_data and 'erro' in streetview_image_data:
         streetview_summary = f" Status Street View: {streetview_image_data['erro']}"
    else:
         streetview_summary = " Tentativa de obter imagem Street View não realizada ou sem resultado específico registrado."


    # Use os resultados das IAs no prompt, lidando com os possíveis prefixos de erro "❌"
    # Format the IA results for inclusion in the summary prompt - strip error prefixes if present
    image_analysis_for_prompt = image_analysis_ia.get('image_analysis', 'Não disponível.')
    if image_analysis_for_prompt.startswith("❌"): image_analysis_for_prompt = f"Análise de imagem indisponível/com erro: {image_analysis_for_prompt[2:].strip()}"

    insights_for_prompt = insights_ia.get('insights', 'Não disponível.')
    if insights_for_prompt.startswith("❌"): insights_for_prompt = f"Análise detalhada indisponível/com error: {insights_for_prompt[2:].strip()}"

    urgencia_for_prompt = urgencia_ia.get('urgencia_ia', 'Não disponível.')
    if urgencia_for_prompt.startswith("❌"): urgencia_for_prompt = f"Sugestão de urgência indisponível/com erro: {urgencia_for_prompt[2:].strip()}"

    sugestao_acao_for_prompt = sugestao_acao_ia.get('sugestao_acao_ia', 'Não disponível.')
    if sugestao_acao_for_prompt.startswith("❌"): sugestao_acao_for_prompt = f"Sugestões de causa/ação indisponíveis/com erro: {sugestao_acao_for_prompt[2:].strip()}"


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 8-10 frases) para o relatório desta denúncia de buraco.
    O resumo deve ser formal, objetivo e útil para equipes de manutenção.
    Combine dados do denunciante, detalhes do buraco, observações, localização processada, resultados das análises de IA e status Street View.

    Dados Chave para o Resumo:
    Denunciante: {denunciante.get('nome', 'Não informado')}, de {denunciante.get('cidade_residencia', 'Não informada')}.
    Localização Processada: {loc_info_resumo}
    {structured_summary_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Análise de Imagem (IA): {image_analysis_for_prompt}
    Análise Detalhada (IA Texto): {insights_for_prompt}
    Sugestão de Urgência (IA Texto): {urgencia_for_prompt}
    Sugestões de Causa e Ação (IA Texto): {sugestao_acao_for_prompt}
    Status Street View: {streetview_summary}

    Crie um resumo fluido e profissional em português, focando nas informações mais relevantes para a avaliação do buraco. Comece com uma frase introdutória clara como "Relatório Krateras sobre denúncia de buraco...".
    """
    try:
        # Adding a small delay
        time.sleep(0.5)
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        resumo_text = process_gemini_response(response, "geração de resumo completo")
        return {"resumo_ia": resumo_text}

    except Exception as e:
        st.error(f"❌ Erro inesperado ao chamar a API Gemini (Resumo): {e}")
        return {"resumo_ia": f"❌ Erro inesperado ao chamar a API Gemini (Resumo): {e}"}


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
                  # Determina para onde voltar com base em como o endereço foi coletado
                  if st.session_state.get('endereco_coletado_via') == 'cep':
                      st.session_state.step = 'collect_buraco_address_cep'
                  elif st.session_state.get('endereco_coletado_via') == 'manual':
                      st.session_state.step = 'collect_buraco_address_manual'
                  else: # Fallback seguro, volta para a escolha do método
                       st.session_state.step = 'collect_buraco_address_method'
             elif st.session_state.step in ['collect_buraco_address_cep', 'collect_buraco_address_manual']:
                  # If in CEP or Manual steps, go back to the method choice
                  st.session_state.step = 'collect_buraco_address_method'
             elif st.session_state.step == 'processing_ia':
                 # If processing, go back to final details
                 st.session_state.step = 'collect_buraco_details'
             else: # For all other cases, go back one step linearly
                  st.session_state.step = steps[current_index - 1]

             st.rerun()
    except ValueError:
         st.session_state.step = steps[0]
         st.rerun()

def force_rerun_ia_analysis():
     """Clears IA related results in session state to force re-computation by cached functions."""
     # Clear cached results by making inputs differ
     # The cached functions use the entire st.session_state.denuncia_completa dict as a key.
     # Modifying the IA result keys will make the cache key different, forcing rerun.
     st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "Status Análise Imagem IA: Re-iniciada."}
     st.session_state.denuncia_completa['insights_ia'] = {"insights": "Status Análise Detalhada IA: Re-iniciada."}
     st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Status Sugestão Urgência IA: Re-iniciada."}
     st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Status Sugestões Causa/Ação IA: Re-iniciada."}
     st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Status Geração Resumo IA: Re-iniciada."}
     # Note: Street View image and Geocoding results are also cached but might not need rerun unless location inputs change.
     # Forcing re-run of IA analysis implies re-running the processing step.
     st.session_state.step = 'processing_ia'
     st.rerun()


# --- Layout Principal da Aplicação ---

st.title("Krateras 🚀✨🔒")
st.subheader("O Especialista Robótico de Denúncia de Buracos")

# Carregar chaves e inicializar APIs quando a aplicação começa (guarded by api_keys_loaded state)
# This ensures models are initialized on the first load and subsequent reruns on the initial page.
if not st.session_state.api_keys_loaded:
    st.info("🔌 Tentando carregar chaves de API e inicializar sistemas IA e de Localização...")
    gemini_api_key, geocoding_api_key = load_api_keys()
    st.session_state.geocoding_api_key = geocoding_api_key
    st.session_state.gemini_pro_model, st.session_state.gemini_vision_model = init_gemini_models(gemini_api_key)
    st.session_state.api_keys_loaded = True
    # Rerun might be needed if load_api_keys or init_gemini_models added messages,
    # but st.info/warning/error usually force a brief rerun anyway.

# --- Fluxo da Aplicação baseado no Estado ---

if st.session_state.step == 'start':
    st.write("""
    Olá! Krateras v3.4.1 entrando em órbita! Sua missão, caso aceite: denunciar buracos na rua
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

    # API key status is already displayed by load_api_keys and init_gemini_models if they ran.

    if st.button("Iniciar Missão Denúncia!"):
        # The keys and models are initialized above this block, outside the button check,
        # on the first load of the 'start' page. So clicking the button just proceeds.
        next_step()


elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Use unique keys for form inputs to prevent conflicts on reruns
    with st.form("form_denunciante_v341"):
        # Initialize with empty strings if not in state
        # Access via .get with a default ensures keys exist even if denuncia_completa was just initialized empty
        denunciante_data = st.session_state.denuncia_completa.get('denunciante', {})
        nome_initial = denunciante_data.get('nome', '')
        idade_initial = denunciante_data.get('idade', 30) # Default idade
        cidade_residencia_initial = denunciante_data.get('cidade_residencia', '')

        nome = st.text_input("Seu nome completo:", value=nome_initial, key='nome_denunciante_input_v341')
        idade = st.number_input("Sua idade (aproximada, se preferir, sem pressão 😉):", min_value=1, max_value=120, value=idade_initial, key='idade_denunciante_input_v341')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", value=cidade_residencia_initial, key='cidade_residencia_denunciante_input_v341')

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
                next_step()

    st.button("Voltar", on_click=prev_step, key='back_from_denunciante_v341')


elif st.session_state.step == 'collect_buraco_address_method':
    st.header("--- 🚧 Detalhes do Buraco (Nosso Alvo!) ---")
    st.subheader("Como identificar a rua do buraco?")

    # Initialize radio value based on previously collected address method if available
    initial_method = st.session_state.get('endereco_coletado_via') # 'cep', 'manual', or None
    if initial_method == 'cep':
        initial_index = 1
    elif initial_method == 'manual':
        initial_index = 0
    else: # Default or first visit
        initial_index = 0 # Default to manual entry

    opcao_localizacao = st.radio(
        "Escolha o método:",
        ('Digitar nome manualmente', 'Buscar por CEP'),
        index = initial_index,
        key='endereco_method_radio_v341'
    )

    # Let's use buttons *outside* the form for navigation clarity
    col_method1, col_method2 = st.columns(2)
    with col_method1:
        if st.button("Selecionar Método e Continuar", key='select_method_btn_v341'):
             if opcao_localizacao == 'Digitar nome manualmente':
                  st.session_state.endereco_coletado_via = 'manual' # Guarda a forma como coletamos o endereço
                  st.session_state.step = 'collect_buraco_address_manual'
             elif opcao_localizacao == 'Buscar por CEP':
                  st.session_state.endereco_coletado_via = 'cep' # Guarda a forma como coletamos o endereço
                  st.session_state.step = 'collect_buraco_address_cep'
             st.rerun()

    with col_method2:
        st.button("Voltar", on_click=prev_step, key='back_from_method_v341')


elif st.session_state.step == 'collect_buraco_address_cep':
    st.header("--- 🚧 Detalhes do Buraco (Busca por CEP) ---")
    st.write("Digite o CEP do local do buraco.")

    # Ensure buraco key exists for initial values
    if 'buraco' not in st.session_state.denuncia_completa:
        st.session_state.denuncia_completa['buraco'] = {}

    with st.form("form_cep_v341"):
        # Use an initial value from state, or empty if not found
        initial_cep = st.session_state.denuncia_completa['buraco'].get('cep_informado', '')
        cep_input = st.text_input("Digite o CEP (apenas números):", value=initial_cep, max_chars=8, key='cep_buraco_input_v341')
        buscar_button = st.form_submit_button("Buscar CEP")

        # Reset search state vars if form is submitted (new search attempt)
        if buscar_button:
             st.session_state.cep_search_error = False
             st.session_state.dados_cep_validos = None # Clear previous valid data
             st.session_state.denuncia_completa['buraco']['cep_informado'] = cep_input.strip() # Always store the input CEP

             if not cep_input:
                 st.error("❗ Por favor, digite um CEP.")
             else:
                 dados_cep = buscar_cep(cep_input.strip())

                 if 'erro' in dados_cep:
                     st.error(f"❌ Falha na busca por CEP: {dados_cep['erro']}")
                     st.session_state.cep_search_error = True
                     # Clear previous endereco data if search failed, keeping only the input CEP
                     if 'endereco' in st.session_state.denuncia_completa['buraco']:
                          del st.session_state.denuncia_completa['buraco']['endereco']
                     st.session_state.denuncia_completa['buraco']['endereco'] = {} # Ensure it's an empty dict

                 else:
                     st.session_state.dados_cep_validos = dados_cep
                     st.session_state.cep_search_error = False
                     st.success("✅ Endereço Encontrado (ViaCEP):")
                     st.write(f"**Rua:** {dados_cep.get('logradouro', 'Não informado')}")
                     st.write(f"**Bairro:** {dados_cep.get('bairro', 'Não informado')}")
                     st.write(f"**Cidade:** {dados_cep.get('localidade', 'Não informado')}")
                     st.write(f"**Estado:** {dados_cep.get('uf', 'Não informado')}")
                     st.write(f"**CEP:** {cep_input.strip()}")
                     st.info("Por favor, confirme se estes dados parecem corretos. Se não, use o botão 'Corrigir Endereço Manualmente'.")
                     # Salva os dados básicos do CEP no buraco_data
                     st.session_state.denuncia_completa['buraco']['endereco'] = {
                          'rua': dados_cep.get('logradouro', '').strip(),
                          'bairro': dados_cep.get('bairro', '').strip(),
                          'cidade_buraco': dados_cep.get('localidade', '').strip(),
                          'estado_buraco': dados_cep.get('uf', '').strip().upper()
                     }
                     # Force rerun to show the action buttons next to the form
                     st.rerun()


    # Display action buttons only if a search attempt was made or user came back here
    if 'cep_buraco_input_v341' in st.session_state: # Check if the form has been rendered
        col_cep_actions1, col_cep_actions2 = st.columns(2)
        if st.session_state.get('dados_cep_validos'): # If CEP data was found and is valid
            with col_cep_actions1:
                 st.button("Confirmar Endereço e Avançar", on_click=next_step, key='confirm_cep_advance_v341')
            with col_cep_actions2:
                 if st.button("Corrigir Endereço Manualmente", key='correct_cep_manual_v341'):
                      st.session_state.endereco_coletado_via = 'manual'
                      # Basic address from CEP is already in state for the manual form
                      st.session_state.step = 'collect_buraco_address_manual'
                      st.rerun()

        elif st.session_state.get('cep_search_error') is True: # Explicitly check for the error state
             st.warning("Não foi possível obter o endereço por CEP.")
             # No "Try again by CEP" button needed; user can just modify the input and click "Buscar CEP" again.
             col_cep_error1, col_cep_error2 = st.columns(2)
             with col_cep_error1:
                  if st.button("Digitar endereço manualmente", key='manual_after_cep_error_v341'):
                       st.session_state.endereco_coletado_via = 'manual'
                       # Preserve CEP input if user switches to manual after error
                       # Basic address might be empty if CEP search failed completely, which is fine for manual input
                       st.session_state.step = 'collect_buraco_address_manual'
                       st.rerun()
             with col_cep_error2:
                  st.button("Voltar", on_click=prev_step, key='back_from_cep_error_v341')
        else: # If the form was just rendered, but no search attempted yet, or user came back here
             st.button("Voltar", on_click=prev_step, key='back_from_cep_no_search_v341')

    else: # Initial page load, form not yet rendered (shouldn't happen with navigation flow)
         st.button("Voltar", on_click=prev_step, key='back_from_cep_initial_v341')



elif st.session_state.step == 'collect_buraco_address_manual':
    st.header("--- 🚧 Detalhes do Buraco (Entrada Manual) ---")
    st.write("Digite os dados do endereço do buraco manualmente.")

    # Ensure necessary keys exist for initial values
    if 'buraco' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['buraco'] = {}
    if 'endereco' not in st.session_state.denuncia_completa['buraco']:
         st.session_state.denuncia_completa['buraco']['endereco'] = {}

    # Use data from state for initial values
    endereco_initial = st.session_state.denuncia_completa['buraco'].get('endereco', {})

    with st.form("form_manual_address_v341"):
        rua_manual = st.text_input("Nome completo da rua:", value=endereco_initial.get('rua', ''), key='rua_manual_buraco_input_v341')
        bairro_manual = st.text_input("Bairro onde está o buraco (opcional):", value=endereco_initial.get('bairro', ''), key='bairro_manual_buraco_input_v341')
        cidade_manual = st.text_input("Cidade onde está o buraco:", value=endereco_initial.get('cidade_buraco', ''), key='cidade_manual_buraco_input_v341')
        estado_manual = st.text_input("Estado (UF) onde está o buraco:", value=endereco_initial.get('estado_buraco', ''), max_chars=2, key='estado_manual_buraco_input_v341')

        submitted = st.form_submit_button("Avançar (Endereço Manual)")

        if submitted:
            if not rua_manual or not cidade_manual or not estado_manual:
                st.error("❗ Rua, Cidade e Estado são campos obrigatórios para o endereço do buraco.")
            else:
                # Salva o endereço manual no dicionário buraco
                st.session_state.denuncia_completa['buraco']['endereco'] = {
                    'rua': rua_manual.strip(),
                    'bairro': bairro_manual.strip(),
                    'cidade_buraco': cidade_manual.strip(),
                    'estado_buraco': estado_manual.strip().upper()
                }
                # CEP informed is kept if user came from CEP step
                # st.session_state.denuncia_completa['buraco']['cep_informado'] is already set if user came from CEP step
                next_step() # Move to the next step (collect details + photo + exact location)

    st.button("Voltar", on_click=prev_step, key='back_from_manual_address_v341')


elif st.session_state.step == 'collect_buraco_details':
    st.header("--- 🚧 Detalhes Finais do Buraco ---")
    st.subheader("Informações cruciais para a localização, análise e reparo!")

    # Exibe o endereço básico já coletado para referência
    endereco_basico = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})
    st.write(f"**Endereço Base Informado:** Rua {endereco_basico.get('rua', 'Não informada')}, {endereco_basico.get('cidade_buraco', 'Não informada')} - {endereco_basico.get('estado_buraco', 'Não informada')}")
    if endereco_basico.get('bairro'):
         st.write(f"**Bairro:** {endereco_basico.get('bairro')}")
    if st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado'):
         st.write(f"**CEP informado:** {st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado')}")

    st.markdown("---")

    # Ensure necessary keys exist for initial values
    if 'buraco' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['buraco'] = {}
    if 'structured_details' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['structured_details'] = {}
    if 'observacoes_adicionais' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['observacoes_adicionais'] = ''
    if 'numero_proximo' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['numero_proximo'] = ''
    if 'lado_rua' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['lado_rua'] = ''
    # The manual location input is stored directly in session_state, not under denuncia_completa['buraco']
    if 'localizacao_manual_input' not in st.session_state: st.session_state.localizacao_manual_input = ''


    with st.form("form_buraco_details_structured_v341"):

        # Initial values from state
        initial_structured_details = st.session_state.denuncia_completa['buraco']['structured_details']
        initial_tamanho = initial_structured_details.get('tamanho', 'Não Informado')
        initial_profundidade = initial_structured_details.get('profundidade', 'Não Informado')
        initial_agua = initial_structured_details.get('presenca_agua', 'Não Informado')
        initial_perigo = initial_structured_details.get('perigo', 'Não Informado')
        initial_contexto = initial_structured_details.get('contexto', 'Não Informado')
        initial_perigos_detalhados = initial_structured_details.get('perigos_detalhados', [])
        initial_identificadores = initial_structured_details.get('identificadores_visuais', '')
        initial_numero_proximo = st.session_state.denuncia_completa['buraco'].get('numero_proximo', '')
        initial_lado_rua = st.session_state.denuncia_completa['buraco'].get('lado_rua', '')
        initial_observacoes = st.session_state.denuncia_completa['buraco'].get('observacoes_adicionais', '')
        initial_localizacao_manual = st.session_state.get('localizacao_manual_input', '')

        st.subheader("Detalhes Estruturados do Buraco")

        col1, col2 = st.columns(2)

        with col1:
            tamanho_options = ['Não Informado', 'Pequeno (Cabe uma bola de futebol)', 'Médio (Cabe um pneu de carro)', 'Grande (Cabe uma pessoa sentada)', 'Enorme (Cobre a faixa)', 'Crítico (Cratera, afeta múltiplos veículos)']
            tamanho = st.radio(
                "**Tamanho Estimado:**",
                tamanho_options,
                index=tamanho_options.index(initial_tamanho),
                key='tamanho_buraco_v341'
            )
            profundidade_options = ['Não Informado', 'Raso (Dá um susto, não danifica)', 'Médio (Pode furar pneu ou danificar suspensão)', 'Fundo (Causa dano considerável, pode entortar roda)', 'Muito Fundo (Causa acidentes graves, imobiliza veículo)']
            profundidade = st.radio(
                "**Profundidade Estimada:**",
                profundidade_options,
                index=profundidade_options.index(initial_profundidade),
                key='profundidade_buraco_v341'
            )
            presenca_agua_options = ['Não Informado', 'Sim (Acumula água)', 'Não (Está seco)']
            presenca_agua = st.radio(
                 "**Presença de Água/Alagamento:**",
                 presenca_agua_options,
                 index=presenca_agua_options.index(initial_agua),
                 key='agua_buraco_v341'
            )

        with col2:
             perigo_options = ['Não Informado', 'Baixo (Principalmente estético)', 'Médio (Pode causar dano menor)', 'Alto (Risco de acidente sério ou dano significativo)', 'Altíssimo (Risco grave e iminente, acidentes frequentes)']
             perigo = st.radio(
                 "**Nível de Risco Aparente:**",
                 perigo_options,
                 index=perigo_options.index(initial_perigo),
                 key='perigo_buraco_v341'
             )
             contexto_options = ['Não Informado', 'Via de Alto Tráfego', 'Via de Baixo Tráfego', 'Perto de Escola/Hospital', 'Em Curva', 'Na Esquina', 'Em Subida/Descida', 'Pouca Iluminação', 'Problema Recorrente', 'Obra Recente na Região']
             contexto = st.selectbox(
                 "**Contexto ou Histórico do Local:**",
                 contexto_options,
                 index=contexto_options.index(initial_contexto),
                 key='contexto_buraco_v341'
             )
             perigos_detalhados_options = ['Risco para Carros (Pneu/Suspensão/Roda)', 'Risco para Motos/Bikes', 'Risco para Pedestres', 'Dificulta Desvio', 'Perigoso à Noite', 'Perigoso na Chuva', 'Causa Lentidão no Trânsito', 'Já Causou Acidentes (Se souber)']
             perigos_detalhados = st.multiselect(
                 "**Fatores de Risco e Impactos Detalhados (Selecione todos que se aplicam):**",
                 perigos_detalhados_options,
                 default=initial_perigos_detalhados,
                 key='perigos_detalhados_buraco_v341'
             )


        identificadores_visuais = st.text_input(
             "**Identificadores Visuais Adicionais Próximos (Ex: Em frente ao poste X, perto da árvore Y):**",
             value=initial_identificadores,
             key='identificadores_visuais_buraco_v341'
        )

        # This input is crucial for Geocoding and location
        numero_proximo = st.text_input(
             "**Número do imóvel mais próximo ou ponto de referência (ESSENCIAL para precisão! Ex: 'Em frente ao 123', 'Esquina c/ Rua X'):**",
             value=initial_numero_proximo,
             key='numero_proximo_buraco_v341'
        )
        lado_rua = st.text_input(
             "**Lado da rua onde está o buraco (Ex: 'lado par', 'lado ímpar', 'lado direito', 'lado esquerdo'):**",
             value=initial_lado_rua,
             key='lado_rua_buraco_v341'
        )


        st.markdown("---")
        st.subheader("Observações Adicionais (Texto Libre)")
        observacoes_adicionais = st.text_area(
            "Qualquer outra informação relevante sobre o buraco ou o local (Histórico, chuva recente, etc.):",
            value=initial_observacoes,
            key='observacoes_adicionais_buraco_v341'
        )

        st.markdown("---")
        st.subheader("Adicionar Foto do Buraco")
        st.write("Anexe uma foto nítida do buraco (JPG, PNG). A IA Gemini Vision pode analisar a imagem para complementar a denúncia!")
        st.info("💡 Dica: Tire a foto de um ângulo que mostre o tamanho e profundidade do buraco, e também inclua um pouco do entorno (calçada, postes, referências) para ajudar a IA e as equipes de reparo a localizarem.")

        # File uploader handles both upload and displaying info about the uploaded file
        uploaded_image = st.file_uploader("Escolha uma imagem...", type=["jpg", "jpeg", "png"], key='uploader_buraco_image_v341')

        # Handle image upload and display
        if uploaded_image is not None:
             # Read image as bytes and store type, but only if a *new* file is uploaded
             # or if the bytes/type state is empty (initial load or after clear).
             # Check if the file object has changed by comparing its ID or a hash (getvalue() hash is simpler)
             current_image_bytes = uploaded_image.getvalue()

             if st.session_state.uploaded_image_bytes is None or \
                st.session_state.uploaded_image_bytes != current_image_bytes: # Simple check if content changed
                 try:
                     st.session_state.uploaded_image_bytes = current_image_bytes
                     st.session_state.uploaded_image_type = uploaded_image.type # Store mime type
                     st.info(f"Foto carregada: {uploaded_image.name} ({uploaded_image.type})")
                 except Exception as e:
                     st.error(f"❌ Erro ao ler o arquivo de imagem: {e}")
                     st.session_state.uploaded_image_bytes = None
                     st.session_state.uploaded_image_type = None

             # Always display the image if bytes are in state
             if st.session_state.uploaded_image_bytes:
                  try:
                      img_display = Image.open(io.BytesIO(st.session_state.uploaded_image_bytes))
                      st.image(img_display, caption="Foto do buraco carregada.", use_column_width=True)
                  except Exception as e:
                       st.error(f"❌ Erro ao exibir a imagem carregada: {e}")
                       # Clear potentially corrupted image data if display fails
                       st.session_state.uploaded_image_bytes = None
                       st.session_state.uploaded_image_type = None
        else:
            # If uploader is None, clear the state variables for the image
            st.session_state.uploaded_image_bytes = None
            st.session_state.uploaded_image_type = None


        st.markdown("---")
        st.subheader("📍 Localização Exata (Coordenadas ou Descrição)")
        st.info("A MELHOR forma de garantir que o reparo vá ao local exato é fornecer Coordenadas (Lat,Long) ou um Link do Google Maps que as contenha. Tente obter isso tocando/clicando e segurando no local exato do buraco no Google Maps.")

        # Input de localização manual (appears always)
        localizacao_manual_input = st.text_input(
             "Alternativamente, ou para corrigir a Geocodificação, insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO Detalhada EXATA:",
             value=initial_localizacao_manual,
             key='localizacao_manual_input_v341'
        )


        submitted_details = st.form_submit_button("Finalizar Coleta e Analisar Denúncia!")

        if submitted_details:
            # Perform validations AFTER submission
            if not numero_proximo or not lado_rua: # Validation for required fields
                 st.error("❗ Número próximo/referência e Lado da rua são campos obrigatórios.")
                 # Stop further execution until inputs are corrected and form is resubmitted
                 st.stop()

            # Store the manual location input value regardless of what it is
            st.session_state.localizacao_manual_input = localizacao_manual_input.strip() # Update the state variable


            # Armazena os detalhes estruturados e observações no dicionário buraco
            st.session_state.denuncia_completa['buraco'].update({
                'numero_proximo': numero_proximo.strip(),
                'lado_rua': lado_rua.strip(),
                'structured_details': {
                     'tamanho': tamanho,
                     'perigo': perigo, # Keep key as 'perigo' for consistency
                     'profundidade': profundidade,
                     'presenca_agua': presenca_agua,
                     'contexto': contexto,
                     'perigos_detalhados': perigos_detalhados, # Keep key
                     'identificadores_visuais': identificadores_visuais.strip(),
                },
                'observacoes_adicionais': observacoes_adicionais.strip(),
                # Image bytes and type are stored separately in session state
            })

            st.subheader("Processando Localização Exata...")

            # Reset processed location data and Street View data BEFORE processing
            st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada", "motivo_falha_geocodificacao_anterior": "Não tentada/aplicável", "input_original": st.session_state.localizacao_manual_input} # Clear previous result, keep the manual input
            st.session_state.streetview_image_data = {"erro": "Status Street View: Processando..."} # Indicate processing started


            lat_final: Optional[float] = None
            lon_final: Optional[float] = None
            link_maps_final: Optional[str] = None
            embed_link_final: Optional[str] = None
            geocoding_attempt_error = "Não tentada/aplicável (Chave ou dados insuficientes)" # Default error message


            # --- Tentar Geocodificação Automática Primeiro ---
            rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
            cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
            estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')
            numero_proximo_geo = st.session_state.denuncia_completa['buraco'].get('numero_proximo') # Usa o numero_proximo para geocoding

            # Geocoding requires API key and basic address (at least street, city, state)
            tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and cidade_buraco and estado_buraco)

            if tem_dados_para_geo:
                st.info("✅ Chave de Geocodificação e dados básicos de endereço encontrados. Tentando gerar a localização exata automaticamente...")
                with st.spinner("⏳ Chamando Google Maps Geocoding API..."):
                    geo_resultado = geocodificar_endereco(
                        rua_buraco,
                        numero_proximo_geo.strip(), # Pass number, but function handles if empty
                        cidade_buraco,
                        estado_buraco,
                        st.session_state.geocoding_api_key
                    )

                if 'erro' not in geo_resultado:
                    lat_final = geo_resultado['latitude']
                    lon_final = geo_resultado['longitude']
                    link_maps_final = geo_resultado['google_maps_link_gerado']
                    embed_link_final = geo_resultado.get('google_embed_link_gerado')
                    # Store successful geocoding result temporarily
                    processed_geo_result = {
                        "tipo": "Geocodificada (API)",
                        "latitude": lat_final,
                        "longitude": lon_final,
                        "endereco_formatado_api": geo_resultado.get('endereco_formatado_api', ''),
                        "google_maps_link_gerado": link_maps_final,
                        "google_embed_link_gerado": embed_link_final,
                         "motivo_falha_geocodificacao_anterior": "Sucesso na Geocodificação automática." # Record success
                    }
                    st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                else:
                    st.warning(f"❌ Falha na Geocodificação automática: {geo_resultado['erro']}")
                    geocoding_attempt_error = geo_resultado['erro'] # Record the specific error
            elif not st.session_state.geocoding_api_key:
                st.warning("⚠️ Chave de API de Geocodificação NÃO fornecida nos Secrets. Geocodificação automática NÃO tentada.")
                geocoding_attempt_error = "Chave de API de Geocodificação não fornecida."
            else: # Key is provided, but data is insufficient
                 st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes (requer pelo menos Rua, Cidade, Estado, e idealmente Número Próximo). Geocodificação automática NÃO tentada.")
                 geocoding_attempt_error = "Dados insuficientes para Geocodificação (requer pelo menos Rua, Cidade, Estado, e idealmente Número Próximo)."


            # --- Processar Localização Manual (if provided) ---
            input_original_manual = st.session_state.localizacao_manual_input # Already stripped above

            # Process manual input ONLY IF it was provided
            lat_manual: Optional[float] = None
            lon_manual: Optional[float] = None
            tipo_manual_processado = "Descrição Manual Detalhada" # Default type if no coords found in manual input

            if input_original_manual:
                 st.info("⏳ Verificando input manual de localização para coordenadas/link...")
                 # Attempt to extract coordinates from the manual input string
                 match_coords = re.search(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', input_original_manual) # Relaxed regex for space/comma
                 if match_coords:
                     try:
                         test_lat = float(match_coords.group(1))
                         test_lon = float(match_coords.group(2))
                         if -90 <= test_lat <= 90 and -180 <= test_lon <= 180:
                             lat_manual = test_lat
                             lon_manual = test_lon
                             tipo_manual_processado = "Coordenadas Fornecidas/Extraídas Manualmente"
                             st.info("✅ Coordenadas válidas detectadas no input manual!")
                         else:
                             st.warning("⚠️ Parece um formato de coordenadas no input manual, mas fora da faixa esperada (-90 a 90 Lat, -180 a 180 Lon). Tratando como descrição.")
                     except ValueError:
                         st.info("ℹ️ Input manual não parece ser coordenadas numéricas válidas. Tratando como descrição detalhada.")
                     except Exception as e: # Catch any other unexpected error during parsing
                          st.info(f"ℹ️ Ocorreu um erro ao tentar processar as coordenadas no input manual: {e}. Tratando como descrição.")

                 # If coordinates weren't found, check if it's a Google Maps link
                 if lat_manual is None and input_original_manual.lower().startswith("http"):
                      st.info("ℹ️ Input manual é um link. Tentando extrair coordenadas...")
                      # Regex to find /@-lat,long pattern in Google Maps URLs or q=lat,long
                      match_maps_link = re.search(r'/@-?(\d+\.?\d*)[, ]-?(\d+\.?\d*)', input_original_manual) # Pattern /@-lat,long or /@-lat long
                      if not match_maps_link: # Try alternative link pattern like https://maps.app.goo.gl/...?q=lat,long
                           match_maps_link = re.search(r'[?&]q=(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual) # Pattern ?q=lat,long or &q=lat,long

                      if match_maps_link:
                          try:
                              test_lat = float(match_maps_link.group(1))
                              test_lon = float(match_maps_link.group(2))
                              if -90 <= test_lat <= 90 and -180 <= test_lon <= 180:
                                   lat_manual = test_lat
                                   lon_manual = test_lon
                                   tipo_manual_processado = "Coordenadas Extraídas de Link (Manual)"
                                   st.info("✅ Coordenadas extraídas de link do Maps no input manual!")
                              else:
                                   st.warning("⚠️ Coordenadas extraídas do link no input manual fora da faixa esperada. Tratando como descrição.")
                          except ValueError:
                             st.info("ℹ️ Valores extraídos do link não parecem coordenadas numéricas válidas. Tratando como descrição.")
                          except Exception as e: # Catch any other unexpected error during parsing
                               st.info(f"ℹ️ Ocorreu um erro ao tentar processar o link no input manual: {e}. Tratando como descrição.")
                      else:
                           st.info("ℹ️ Não foi possível extrair coordenadas reconhecíveis do link fornecido manualmente.")
                 # else: If it's not coords and not a link, it will fall through to being a "Descrição Manual Detalhada"
            # else: Manual input was empty, no processing needed for it.


            # --- Determine FINAL Location Data ---
            # Prioritize manual coordinates/link if found, otherwise use geocoding result if successful, otherwise use manual description if provided, otherwise mark as not found.
            if lat_manual is not None and lon_manual is not None:
                 # Manual input with valid coords/link overrides geocoding result (if any)
                 lat_final = lat_manual
                 lon_final = lon_manual
                 # Use original input if it was a link, otherwise generate search link
                 link_maps_final = input_original_manual if input_original_manual.lower().startswith("http") else f"https://www.google.com/maps/search/?api=1&query={lat_final},{lon_final}"
                 # Attempt to generate embed link ONLY if Geocoding API key is available
                 embed_link_final = f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_final},{lon_final}" if st.session_state.geocoding_api_key else None

                 st.session_state.denuncia_completa['localizacao_exata_processada'].update({
                      "tipo": tipo_manual_processado, # Will be Coordenadas... or Coordenadas Extraídas...
                      "latitude": lat_final,
                      "longitude": lon_final,
                      "google_maps_link_gerado": link_maps_final,
                      "google_embed_link_gerado": embed_link_final,
                      "motivo_falha_geocodificacao_anterior": geocoding_attempt_error # Still record if geocoding failed
                 })
                 if st.session_state.geocoding_api_key and embed_link_final is None:
                      st.warning("⚠️ Não foi possível gerar o link Google Maps Embed com a chave fornecida. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")
                 elif not st.session_state.geocoding_api_key:
                      st.info("ℹ️ Chave de API de Geocodificação/Embed não fornecida. Link Google Maps Embed não gerado.")
                 # Success message for manual coord/link processing is implicit via st.info above

            elif 'processed_geo_result' in locals(): # Check if geocoding was successful and stored in local var
                 # Geocoding was successful, and manual input was empty or unusable as coords/link.
                 st.session_state.denuncia_completa['localizacao_exata_processada'].update(processed_geo_result)
                 st.session_state.denuncia_completa['localizacao_exata_processada']['input_original'] = input_original_manual # Store the manual input value

            elif input_original_manual:
                 # Manual input provided, but no coordinates/link detected. Treat as description.
                 # This only happens if geocoding failed or wasn't attempted.
                 st.session_state.denuncia_completa['localizacao_exata_processada'].update({
                      "tipo": "Descrição Manual Detalhada",
                      "descricao_manual": input_original_manual,
                      "motivo_falha_geocodificacao_anterior": geocoding_attempt_error # Record geocoding attempt error
                 })
                 st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi detectada no input manual. O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")

            else:
                 # Geocoding failed/skipped AND manual input was empty.
                 st.warning("⚠️ Nenhuma localização exata foi obtida (Geocodificação falhou ou não tentada, e input manual estava vazio). O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")
                 # The reason for geocoding failure is already stored in geocoding_attempt_error variable.
                 st.session_state.denuncia_completa['localizacao_exata_processada'].update({
                      "tipo": "Não informada",
                      "motivo_falha_geocodificacao_anterior": geocoding_attempt_error
                 })

            # Ensure input_original is always stored
            st.session_state.denuncia_completa['localizacao_exata_processada']['input_original'] = input_original_manual


            # --- Obter Imagem Street View (se houver coordenadas e chave) ---
            # Attempt to get Street View ONLY if final coordinates (geocoded or manual) are available and not None
            lat_for_sv = st.session_state.denuncia_completa['localizacao_exata_processada'].get('latitude')
            lon_for_sv = st.session_state.denuncia_completa['localizacao_exata_processada'].get('longitude')
            api_key_for_sv = st.session_state.geocoding_api_key # Street View Static uses the same key

            if lat_for_sv is not None and lon_for_sv is not None and api_key_for_sv:
                 st.info("📸 Tentando obter imagem Street View para as coordenadas...")
                 # Call the Street View function (it's cached)
                 with st.spinner("⏳ Chamando Google Street View Static API..."):
                      st.session_state.streetview_image_data = get_street_view_image(
                          lat_for_sv,
                          lon_for_sv,
                          api_key_for_sv
                          # Default size "600x400", heading 0 (North)
                      )
                 if st.session_state.streetview_image_data and 'image_bytes' in st.session_state.streetview_image_data:
                      st.success("✅ Imagem Street View obtida com sucesso!")
                 elif st.session_state.streetview_image_data and 'erro' in st.session_state.streetview_image_data:
                      st.warning(f"⚠️ Falha ao obter imagem Street View: {st.session_state.streetview_image_data['erro']}")
                      # Note: Street View Static API needs to be enabled in Google Cloud Console.
                      if "not authorized" in st.session_state.streetview_image_data['erro'].lower() or "forbidden" in st.session_state.streetview_image_data['erro'].lower():
                           st.error("❌ Erro de autorização na Street View Static API. Verifique se a 'Street View Static API' está habilitada e autorizada para sua chave no Google Cloud.")
                      elif "Nenhuma imagem Street View encontrada" in st.session_state.streetview_image_data['erro']:
                           st.info("ℹ️ É possível que não haja cobertura Street View no local exato fornecido.")
            elif not api_key_for_sv:
                 st.warning("⚠️ Chave de API de Geocodificação/Street View não fornecida nos Secrets. Imagem Street View não obtida.")
                 st.session_state.streetview_image_data = {"erro": "Chave de API de Geocodificação/Street View não fornecida."}
            elif lat_for_sv is None or lon_for_sv is None:
                 st.info("ℹ️ Coordenadas exatas não disponíveis. Imagem Street View não pode ser obtida.")
                 st.session_state.streetview_image_data = {"erro": "Coordenadas exatas não disponíveis."}
            else: # Fallback if status wasn't explicitly set
                 st.session_state.streetview_image_data = {"erro": "Status Street View: Não processado ou sem resultado específico registrado."}


            # Now that location, Street View, and user image were processed/collected,
            # advance to the IA processing step.
            next_step()

    st.button("Voltar", on_click=prev_step, key='back_from_details_v341')


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa todos os dados (texto, imagem) e gera o relatório com a inteligência do Google Gemini.")

    # Check model availability
    gemini_pro_available = st.session_state.gemini_pro_model is not None
    gemini_vision_available = st.session_state.gemini_vision_model is not None
    ia_available = gemini_pro_available or gemini_vision_available

    if not ia_available:
         st.warning("⚠️ Nenhuma análise de IA será executada (Modelos Gemini não configurados ou indisponíveis).")
         st.button("Avançar para o Relatório (Sem IA)", on_click=next_step, key='skip_ia_button_v341')
         st.button("Voltar", on_click=prev_step, key='back_from_processing_noia_v341')
         st.stop() # Stop execution if no IA is possible


    # Define the processing order and check if each step needs to run based on current state
    processing_queue = []
    ia_results_keys = ['image_analysis_ia', 'insights_ia', 'urgencia_ia', 'sugestao_acao_ia', 'resumo_ia'] # Keys to check status

    # 1. Image Analysis
    # Check if vision is available, image is uploaded, and analysis hasn't been done/failed in a previous run
    img_analysis_status = st.session_state.denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Status Análise Imagem IA: Não iniciada.')
    if gemini_vision_available and st.session_state.get('uploaded_image_bytes') and img_analysis_status.startswith('Status Análise Imagem IA:'):
         processing_queue.append('image_analysis')
    elif not gemini_vision_available:
         if img_analysis_status.startswith('Status Análise Imagem IA:'): # Avoid overwriting a specific failure from a previous run
             st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "🤖 Análise de imagem via IA indisponível (Motor Gemini Vision offline ou não configurado)."}
    elif st.session_state.get('uploaded_image_bytes') is None:
         if img_analysis_status.startswith('Status Análise Imagem IA:'): # Avoid overwriting a specific failure
             st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "🔍 Nenhuma imagem fornecida pelo usuário para análise de IA."}


    # 2. Text Analyses (depend on Pro model)
    if gemini_pro_available:
         # Detailed Analysis
         insights_status = st.session_state.denuncia_completa.get('insights_ia', {}).get('insights', 'Status Análise Detalhada IA: Não iniciada.')
         if insights_status.startswith('Status Análise Detalhada IA:'):
              processing_queue.append('detailed_analysis')

         # Urgency, Cause/Action, and Summary checks
         urgency_status = st.session_state.denuncia_completa.get('urgencia_ia', {}).get('urgencia_ia', 'Status Sugestão Urgência IA: Não iniciada.')
         if urgency_status.startswith('Status Sugestão Urgência IA:'):
              processing_queue.append('urgency_suggestion')

         action_status = st.session_state.denuncia_completa.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', 'Status Sugestões Causa/Ação IA: Não iniciada.')
         if action_status.startswith('Status Sugestões Causa/Ação IA:'):
              processing_queue.append('action_suggestion')

         summary_status = st.session_state.denuncia_completa.get('resumo_ia', {}).get('resumo_ia', 'Status Geração Resumo IA: Não iniciada.')
         if summary_status.startswith('Status Geração Resumo IA:'):
              processing_queue.append('summary_generation')

    else:
         # Set all text analysis statuses to unavailable if Pro model is missing, unless they already show a specific error
         if st.session_state.denuncia_completa.get('insights_ia', {}).get('insights', '').startswith('Status Análise Detalhada IA:'):
              st.session_state.denuncia_completa['insights_ia'] = {"insights": "🤖 Análise detalhada via IA indisponível (Motor Gemini Texto offline ou não configurado)."}
         if st.session_state.denuncia_completa.get('urgencia_ia', {}).get('urgencia_ia', '').startswith('Status Sugestão Urgência IA:'):
              st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Texto offline ou não configurado)."}
         if st.session_state.denuncia_completa.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', '').startswith('Status Sugestões Causa/Ação IA:'):
              st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Texto offline ou não configurado)."}
         if st.session_state.denuncia_completa.get('resumo_ia', {}).get('resumo_ia', '').startswith('Status Geração Resumo IA:'):
              st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini Texto offline ou não configurado)."}


    # Execute processing steps in order
    if processing_queue:
         st.info(f"Fila de processamento de IA: {', '.join(processing_queue)}")
         # Use a placeholder to update status during processing
         status_placeholder = st.empty()

         for step_name in processing_queue:
              try:
                  if step_name == 'image_analysis':
                       status_placeholder.info("🧠 Analisando a imagem do buraco com IA Gemini Vision...")
                       # Call the function (not cached), it will store result in state directly
                       st.session_state.denuncia_completa['image_analysis_ia'] = analyze_image_with_gemini_vision(
                           st.session_state.uploaded_image_bytes,
                           st.session_state.uploaded_image_type,
                           st.session_state.gemini_vision_model
                       )
                       # Check the result and update placeholder
                       result_text = st.session_state.denuncia_completa['image_analysis_ia'].get('image_analysis', 'Erro desconhecido.')
                       if result_text.startswith("❌"):
                            status_placeholder.error(f"❌ Análise de Imagem Falhou: {result_text}")
                       else:
                            status_placeholder.success("✅ Análise de Imagem concluída.")

                  elif step_name == 'detailed_analysis':
                       status_placeholder.info("🧠 Executando análise profunda dos dados do buraco com IA Gemini (Texto)...")
                       # Call the cached function
                       st.session_state.denuncia_completa['insights_ia'] = analisar_dados_com_gemini(
                            st.session_state.denuncia_completa, # Pass complete data (this is the cache key)
                            st.session_state.gemini_pro_model
                       )
                       # Check the result and update placeholder
                       result_text = st.session_state.denuncia_completa['insights_ia'].get('insights', 'Erro desconhecido.')
                       if result_text.startswith("❌"):
                            status_placeholder.error(f"❌ Análise Detalhada Falhou: {result_text}")
                       else:
                            status_placeholder.success("✅ Análise Detalhada concluída.")


                  elif step_name == 'urgency_suggestion':
                       # Check if prerequisite analysis (detailed_analysis) had a critical failure
                       insights_status_check = st.session_state.denuncia_completa.get('insights_ia', {}).get('insights', 'Status Análise Detalhada IA: Não iniciada.')
                       if insights_status_check.startswith("❌"):
                           status_placeholder.warning("⚠️ Pulando Sugestão de Urgência: Análise Detalhada prévia falhou.")
                           st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "🤖 Sugestão de urgência não realizada (Análise Detalhada prévia falhou)."}
                       else:
                           status_placeholder.info("🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
                           st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
                                st.session_state.denuncia_completa, # Pass complete data (this is the cache key)
                                st.session_state.gemini_pro_model
                           )
                           result_text = st.session_state.denuncia_completa['urgencia_ia'].get('urgencia_ia', 'Erro desconhecido.')
                           if result_text.startswith("❌"):
                                status_placeholder.error(f"❌ Sugestão de Urgência Falhou: {result_text}")
                           else:
                                status_placeholder.success("✅ Sugestão de Urgência concluída.")


                  elif step_name == 'action_suggestion':
                       # Check if prerequisite analysis (detailed_analysis) had a critical failure
                       insights_status_check = st.session_state.denuncia_completa.get('insights_ia', {}).get('insights', 'Status Análise Detalhada IA: Não iniciada.')
                       if insights_status_check.startswith("❌"):
                           status_placeholder.warning("⚠️ Pulando Sugestões de Causa/Ação: Análise Detalhada prévia falhou.")
                           st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "🤖 Sugestões de causa/ação não realizadas (Análise Detalhada prévia falhou)."}
                       else:
                            status_placeholder.info("🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
                            st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
                                 st.session_state.denuncia_completa, # Pass complete data (this is the cache key)
                                 st.session_state.gemini_pro_model
                           )
                            result_text = st.session_state.denuncia_completa['sugestao_acao_ia'].get('sugestao_acao_ia', 'Erro desconhecido.')
                            if result_text.startswith("❌"):
                                 status_placeholder.error(f"❌ Sugestões de Causa/Ação Falharam: {result_text}")
                            else:
                                 status_placeholder.success("✅ Sugestões de Causa/Ação concluídas.")

                  elif step_name == 'summary_generation':
                       # Check if prerequisite analysis (detailed_analysis) had a critical failure
                       insights_status_check = st.session_state.denuncia_completa.get('insights_ia', {}).get('insights', 'Status Análise Detalhada IA: Não iniciada.')
                       if insights_status_check.startswith("❌"):
                           status_placeholder.warning("⚠️ Pulando Geração de Resumo: Análise Detalhada prévia falhou.")
                           st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "🤖 Resumo completo não gerado (Análise Detalhada prévia falhou)."}
                       else:
                            status_placeholder.info("🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
                            st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
                                 st.session_state.denuncia_completa, # Pass complete data (this is the cache key)
                                 st.session_state.gemini_pro_model
                            )
                            result_text = st.session_state.denuncia_completa['resumo_ia'].get('resumo_ia', 'Erro desconhecido.')
                            if result_text.startswith("❌"):
                                 status_placeholder.error(f"❌ Geração de Resumo Falhou: {result_text}")
                            else:
                                 status_placeholder.success("✅ Geração de Resumo concluída.")

                  # Small pause after each step display
                  time.sleep(0.3) # Reduced delay slightly

              except Exception as e:
                  # Catch unexpected errors during the execution of a step (should be caught by process_gemini_response too, but safety net)
                   error_message = f"❌ ERRO FATAL INESPERADO durante a etapa '{step_name}': {e}"
                   status_placeholder.error(error_message)
                   st.error(f"DEBUG: {error_message}")
                   # Log the error in the relevant state key if it wasn't already set by process_gemini_response's inner try/except
                   if step_name == 'image_analysis' and not st.session_state.denuncia_completa['image_analysis_ia'].get('image_analysis', '').startswith("❌"):
                        st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": error_message}
                   elif step_name == 'detailed_analysis' and not st.session_state.denuncia_completa['insights_ia'].get('insights', '').startswith("❌"):
                        st.session_state.denuncia_completa['insights_ia'] = {"insights": error_message}
                   elif step_name == 'urgency_suggestion' and not st.session_state.denuncia_completa['urgencia_ia'].get('urgencia_ia', '').startswith("❌"):
                        st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": error_message}
                   elif step_name == 'action_suggestion' and not st.session_state.denuncia_completa['sugestao_acao_ia'].get('sugestao_acao_ia', '').startswith("❌"):
                        st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": error_message}
                   elif step_name == 'summary_generation' and not st.session_state.denuncia_completa['resumo_ia'].get('resumo_ia', '').startswith("❌"):
                        st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": error_message}

                   # Decide if processing should stop after a fatal error.
                   # For now, we continue to attempt other steps, but log the failure.
                   pass


         # Clear final status message placeholder
         status_placeholder.empty()
         # Provide a final summary status
         all_ia_done = all(not st.session_state.denuncia_completa.get(key, {}).get(key.replace('_ia',''), '').startswith('Status ') for key in ia_results_keys)
         any_ia_failed = any(st.session_state.denuncia_completa.get(key, {}).get(key.replace('_ia',''), '').startswith('❌') for key in ia_results_keys)

         if all_ia_done and not any_ia_failed:
              st.success("✅ Todas as análises de IA solicitadas foram concluídas com sucesso!")
         elif any_ia_failed:
              st.warning("⚠️ Processamento de IA concluído, mas algumas análises falharam. Verifique os detalhes no relatório final.")
         else:
              st.info("ℹ️ Processamento de IA concluído. Algumas análises podem não ter sido realizadas (modelos indisponíveis, falta de dados, etc.). Verifique o relatório.")


         next_step() # Always advance to the report after attempting IA processing

    else: # No tasks queued (e.g. user re-ran processing page after success)
         st.info("Todas as análises de IA solicitadas já foram concluídas para esta denúncia.")
         st.button("Ver Relatório", on_click=next_step, key='view_report_after_processing_v341')


    st.button("Voltar", on_click=prev_step, key='back_from_processing_done_v341')


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
        st.subheader("Endereço Base Informado")
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
        if buraco.get('lado_rua'):
            st.write(f"**Lado da Rua:** {buraco.get('lado_rua')}")


        st.subheader("Detalhes Estruturados Preenchidos")
        if structured_details:
            # Define the order of keys to display
            detail_keys_order = ['tamanho', 'profundidade', 'presenca_agua', 'perigo', 'contexto', 'perigos_detalhados', 'identificadores_visuais']
            informed_details = {k: v for k, v in structured_details.items() if k in detail_keys_order and v and (not isinstance(v, list) or v)}

            if informed_details:
                 for key in detail_keys_order:
                     value = informed_details.get(key)
                     if value is not None: # Check if key exists and has a value
                          key_translated = {
                             'tamanho': 'Tamanho Estimado',
                             'perigo': 'Nível de Risco Aparente',
                             'profundidade': 'Profundidade Estimada',
                             'presenca_agua': 'Presença de Água/Alagamento',
                             'contexto': 'Contexto ou Histórico',
                             'perigos_detalhados': 'Fatores de Risco e Impactos Detalhados',
                             'identificadores_visuais': 'Identificadores Visuais Adicionais',
                          }.get(key, key)
                          value_str = ", ".join(value) if isinstance(value, list) else value
                          st.write(f"**{key_translated}:** {value_str}")
            else:
                 st.info("Nenhum detalhe estruturado foi informado pelo usuário.")
        else:
            st.info("Detalhes estruturados não foram coletados.")


        st.subheader("Observações Adicionais (Texto Libre)")
        st.info(observacoes_adicionais if observacoes_adicionais else "Nenhuma observação adicional fornecida.")

        st.subheader("Foto Anexada pelo Usuário")
        if st.session_state.get('uploaded_image_bytes'):
             try:
                 # Display image from bytes
                 img_display = Image.open(io.BytesIO(st.session_state.uploaded_image_bytes))
                 st.image(img_display, caption="Foto do buraco anexada.", use_column_width=True)
             except Exception as e:
                  st.warning(f"⚠️ Não foi possível exibir a imagem anexada. Erro: {e}")
        else:
            st.info("Nenhuma foto foi anexada a esta denúncia pelo usuário.")


    with st.expander("📍 Localização Exata Processada e Visualizações", expanded=True):
        tipo_loc = localizacao_exata.get('tipo', 'Não informada')
        st.write(f"**Tipo de Coleta/Processamento da Localização Exata:** {tipo_loc}")

        lat = localizacao_exata.get('latitude')
        lon = localizacao_exata.get('longitude')

        if lat is not None and lon is not None:
             st.write(f"**Coordenadas Processadas:** `{lat}, {lon}`")

             # --- Visualização Street View ---
             st.subheader("Visualização Google Street View Estática")
             if streetview_image_data and 'image_bytes' in streetview_image_data:
                  try:
                       # Display Street View image from bytes
                       st.image(streetview_image_data['image_bytes'], caption="Imagem Google Street View.", use_column_width=True)
                       st.info("✅ Imagem Google Street View obtida com sucesso.")
                  except Exception as e:
                       st.error(f"❌ Erro ao exibir a imagem Street View: {e}")
             elif streetview_image_data and 'erro' in streetview_image_data:
                  st.warning(f"⚠️ Falha ao obter imagem Street View: {streetview_image_data['erro']}")
             else:
                  # This case should ideally not happen with the improved error handling
                  st.info("ℹ️ Status Street View: Não processado ou sem resultado específico registrado.")


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
                 # Verify embed link requires API key before trying to display
                 if st.session_state.geocoding_api_key:
                     try:
                         st.components.v1.html(
                             f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link}" allowfullscreen></iframe>',
                             height=470,
                             scrolling=False
                         )
                         st.info("✅ Visualização do Google Maps Embed carregada (requer Maps Embed API habilitada e autorizada para sua chave).")
                     except Exception as embed_error:
                          st.error(f"❌ Erro ao carregar visualização do Google Maps Embed: {embed_error}")
                          st.warning("⚠️ A visualização do Google Maps Embed requer que a 'Maps Embed API' esteja habilitada e autorizada para sua chave de API Geocoding no Google Cloud.")
                 else:
                      st.warning("⚠️ Chave de API Geocoding/Embed não fornecida nos Secrets. Visualização Google Maps Embed não disponível.")

             elif st.session_state.geocoding_api_key:
                  # Embed link wasn't generated even though key exists and coords were found.
                  st.warning("⚠️ Chave de API Geocoding fornecida e coordenadas encontradas, mas o link Google Maps Embed não foi gerado com sucesso. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")
             else:
                  st.warning("⚠️ Chave de API Geocoding/Embed não fornecida nos Secrets. Visualização Google Maps Embed não disponível.")


             link_maps = localizacao_exata.get('google_maps_link_gerado')
             if link_maps:
                 st.write(f"**Link Direto Google Maps:** [Abrir no Google Maps]({link_maps})")

             if localizacao_exata.get('endereco_formatado_api'):
                  st.write(f"**Endereço Formatado (API):** {localizacao_exata.get('endereco_formatado_api')}")
             if localizacao_exata.get('input_original') and tipo_loc not in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Coordenadas Extraídas de Link (Manual)']:
                  # Show original input if it wasn't just coordinates or a recognized link
                  st.write(f"(Input Manual Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")


        elif tipo_loc == 'Descrição Manual Detalhada':
            st.write(f"**Localização Processada:** Descrição Manual Detalhada")
            st.info(localizacao_exata.get('descricao_manual', 'Não informada'))
            if localizacao_exata.get('input_original') != localizacao_exata.get('descricao_manual'):
                 st.write(f"(Input Manual Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")

        else: # tipo_loc is 'Não informada' or other unhandled case
            st.warning("Localização exata não coletada de forma estruturada (coordenadas/link/descrição manual detalhada).")


        # Includes the reason for geocoding failure if applicable, unless geocoding was successful
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior') and not localizacao_exata.get('motivo_falha_geocodificacao_anterior') == "Sucesso na Geocodificação automática.":
             st.info(f"ℹ️ Nota: Não foi possível obter a localização exata via Geocodificação automática. Motivo: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")


    st.markdown("---")

    # Exibir análises de IA (even if they failed, the error message from process_gemini_response will be shown)
    gemini_pro_available = st.session_state.gemini_pro_model is not None
    gemini_vision_available = st.session_state.gemini_vision_model is not None
    ia_available = gemini_pro_available or gemini_vision_available


    if ia_available:
        st.subheader("🧠 Análises de Inteligência Artificial (Google Gemini)")

        with st.expander("🧠 Análise de Imagem (IA Gemini Vision)", expanded=True):
             st.write(image_analysis_ia.get('image_analysis', 'Análise de imagem não realizada ou com erro inesperado.')) # Default if key missing
             if not gemini_vision_available:
                  st.info("ℹ️ Motor Gemini Vision indisponível ou não configurado. Análise de imagem não realizada.")
             elif st.session_state.get('uploaded_image_bytes') is None:
                  st.info("ℹ️ Nenhuma imagem foi anexada pelo usuário. Análise de imagem não realizada.")


        with st.expander("🧠 Análise Detalhada Consolidada (IA Gemini Texto)", expanded=True):
            st.write(insights_ia.get('insights', 'Análise detalhada não gerada ou com erro inesperado.')) # Default if key missing
            if not gemini_pro_available:
                 st.info("ℹ️ Motor Gemini Texto indisponível ou não configurado. Análise detalhada não realizada.")


        with st.expander("🚦 Sugestão de Urgência (IA Gemini Texto)", expanded=True):
            st.write(urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro inesperado.')) # Default if key missing
            if not gemini_pro_available:
                 st.info("ℹ️ Motor Gemini Texto indisponível ou não configurado. Sugestão de urgência não realizada.")


        with st.expander("🛠️ Sugestões de Causa e Ação (IA Gemini Texto)", expanded=True):
            st.write(sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões de causa/ação não geradas ou com erro inesperado.')) # Default if key missing
            if not gemini_pro_available:
                 st.info("ℹ️ Motor Gemini Texto indisponível ou não configurado. Sugestões de causa/ação não realizadas.")

        st.markdown("---")
        st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini Texto)")
        st.write(resumo_ia.get('resumo_ia', 'Resumo completo não gerado ou com erro inesperado.')) # Default if key missing
        if not gemini_pro_available:
             st.info("ℹ️ Motor Gemini Texto indisponível ou não configurado. Resumo completo não gerado.")

        # Button to re-run IA analysis
        if st.button("Re-executar Análises de IA", key='rerun_ia_button_v341'):
             force_rerun_ia_analysis() # This will clear IA results in state and transition to processing_ia step


    else: # Neither Gemini model was available
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chaves Gemini não configuradas ou modelos indisponíveis).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Option to start new process
    col_report_actions1, col_report_actions2 = st.columns(2)
    with col_report_actions1:
        if st.button("Iniciar Nova Denúncia", key='new_denuncia_button_v341'):
            # Clear session state except for API keys and models (which are cached resources)
            for key in list(st.session_state.keys()): # Iterate over a copy of keys as we modify the dict
                # Keep API keys, models, and the flag indicating keys were loaded
                if key not in ['geocoding_api_key', 'gemini_pro_model', 'gemini_vision_model', 'api_keys_loaded']:
                     del st.session_state[key]

            # Re-initialize the base structure of denuncia_completa with default statuses
            st.session_state.denuncia_completa = {
                'denunciante': {},
                'buraco': {
                    'endereco': {},
                    'structured_details': {},
                    'observacoes_adicionais': '',
                    'numero_proximo': '',
                    'lado_rua': '',
                    'cep_informado': ''
                },
                'localizacao_exata_processada': {"tipo": "Não informada", "motivo_falha_geocodificacao_anterior": "Não tentada/aplicável", "input_original":""},
                'streetview_image_data': {"erro": "Status Street View: Não iniciada."},
                'image_analysis_ia': {"image_analysis": "Status Análise Imagem IA: Não iniciada."},
                'insights_ia': {"insights": "Status Análise Detalhada IA: Não iniciada."},
                'urgencia_ia': {"urgencia_ia": "Status Sugestão Urgência IA: Não iniciada."},
                'sugestao_acao_ia': {"sugestao_acao_ia": "Status Sugestões Causa/Ação IA: Não iniciada."},
                'resumo_ia': {"resumo_ia": "Status Geração Resumo IA: Não iniciada."},
            }
            # Also explicitly clear image data and manual location input
            st.session_state.uploaded_image_bytes = None
            st.session_state.uploaded_image_type = None
            st.session_state.localizacao_manual_input = ''
            st.session_state.endereco_coletado_via = None
            # Clear cached functions related to IA and Geocoding/StreetView
            # @st.cache_data functions can be cleared individually or globally
            # Clearing all cache might be safer for a full restart
            st.cache_data.clear()
            st.cache_resource.clear()

            st.rerun()

    # Option to display raw data (useful for debug or export)
    with col_report_actions2:
        with st.expander("🔌 Ver Dados Brutos da Denúncia (JSON)"):
            # Create a deep copy to safely modify for JSON display
            import copy
            dados_para_json = copy.deepcopy(dados_completos)

            # Handle streetview_image_data
            if 'streetview_image_data' in dados_para_json and dados_para_json['streetview_image_data'] is not None:
                 if 'image_bytes' in dados_para_json['streetview_image_data']:
                      # Remove image_bytes
                      del dados_para_json['streetview_image_data']['image_bytes']
                      dados_para_json['streetview_image_data']['note'] = "image_bytes_removed_for_json_view"
                 # Else: streetview_image_data is already serializable

            # Handle uploaded_image_bytes (stored in session state, not denuncia_completa)
            # Add it explicitly to the copy for JSON view
            if st.session_state.get('uploaded_image_bytes') is not None:
                 dados_para_json['uploaded_image_bytes_status'] = "image_bytes_removed_for_json_view"
                 dados_para_json['uploaded_image_type'] = st.session_state.get('uploaded_image_type')
            else:
                 dados_para_json['uploaded_image_bytes_status'] = None
                 dados_para_json['uploaded_image_type'] = None

            # Handle manual location input (stored in session state, not denuncia_completa)
            dados_para_json['localizacao_manual_input_original'] = st.session_state.get('localizacao_manual_input')
            dados_para_json['endereco_coletado_via'] = st.session_state.get('endereco_coletado_via')


            try:
                 st.json(dados_para_json)
            except Exception as e:
                 st.error(f"❌ Erro ao serializar dados para JSON. Verifique a estrutura: {e}")
                 # As a fallback, try printing a simpler representation
                 st.write("Erro ao exibir JSON. Conteúdo:")
                 st.write(dados_para_json)
