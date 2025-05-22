# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v3.3 - Interphase Refined + IA Fixes)

Bem-vindo à versão ainda mais visual e aprimorada do Krateras, agora com um visual inspirado
no elegante template Interphase, com estilos CSS refinados para maior compatibilidade,
mais clean e agradável aos olhos!

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

# --- Estilos CSS Personalizados (Inspirado no Template Interphase - REFINADO para visual clean/light) ---
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
       background-color: #e0f7fa; /* Fundo semi-transparente (pode ser mais claro se o body for sólido) */
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

    /* Expanders (Menus Sanfona) */
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

    /* Separators */
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
    st.session_state.denuncia_completa = {}
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
            # Check both 'models/name' and just 'name'
            if f'models/{pref_model}' in available_models:
                text_model_name = f'models/{pref_model}'
                break
            if pref_model in available_models: # Fallback check, though models/name is preferred
                 text_model_name = pref_model
                 break


        if text_model_name:
             model_pro = genai.GenerativeModel(text_model_name)
             st.success(f"✅ Conexão com Google Gemini (Texto) estabelecida usando modelo '{text_model_name}'.")
        else:
             st.warning("⚠️ Nenhum modelo de texto Gemini compatível (como 1.5 Flash, 1.0 Pro ou Pro) encontrado na sua conta.")


        # Inicializar Gemini-Vision para análise de imagem
        vision_model_name = 'gemini-pro-vision'
        vision_model_full_name = f'models/{vision_model_name}'
        if vision_model_full_name in available_models or vision_model_name in available_models:
            model_vision = genai.GenerativeModel(vision_model_full_name if vision_model_full_name in available_models else vision_model_name)
            st.success(f"✅ Conexão com Google Gemini (Visão) estabelecida usando modelo '{vision_model_name}'.")
        else:
            st.warning(f"⚠️ Modelo Gemini Vision ('{vision_model_name}') não encontrado ou compatível na sua conta. Análise de imagem desabilitada.")


        if model_pro or model_vision:
            st.info("A IA está online e pensativa!")

        return model_pro, model_vision

    except Exception as e:
        st.error(f"❌ ERRO no Painel de Controle Gemini: Falha na inicialização dos modelos Google Gemini. Verifique sua chave, habilitação dos modelos no Google Cloud e status do serviço.")
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
    # if not rua or not cidade or not estado:
    #      return {"erro": "Dados de endereço insuficientes (requer rua, cidade, estado) para geocodificar."}

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
        error_msg = f"Erro na comunicação com a API de Geocodificação: {e}"
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
# BLOCK_NONE é o mais permissivo. Se o problema persistir, pode indicar que
# o conteúdo (mesmo com BLOCK_NONE) viola limites rígidos ou há um problema
# temporário ou de configuração com a API/modelo.
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
        # Prioritize checking for prompt feedback (blocking)
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
             if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                  block_reason = response.prompt_feedback.block_reason.name
                  # More detailed block info if available
                  block_details = ""
                  if hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                       ratings = ", ".join([f"{r.category.name}: {r.probability.name}" for r in response.prompt_feedback.safety_ratings])
                       block_details = f" (Ratings: {ratings})"
                  return f"❌ Análise bloqueada pelo filtro de segurança do Gemini durante a {context}. Motivo: {block_reason}{block_details}"
             elif hasattr(response.prompt_feedback, 'safety_ratings') and response.prompt_feedback.safety_ratings:
                  # Block occurred, but reason not explicitly set? Still report ratings.
                  ratings = ", ".join([f"{r.category.name}: {r.probability.name}" for r in response.prompt_feedback.safety_ratings])
                  return f"❌ Análise bloqueada pelo filtro de segurança do Gemini durante a {context} (sem motivo explícito, ratings: {ratings})."


        # Check for successful content if not blocked
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
             # If candidates exist but .text is empty, maybe try accessing the first candidate's text
             if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                  # Assuming the first part is text
                  return str(response.candidates[0].content.parts[0]).strip()
             else:
                  return f"❌ A resposta do Gemini durante a {context} não contém texto processável."
        else:
             return f"❌ A resposta do Gemini durante a {context} não contém conteúdo nem feedback de bloqueio. Resposta completa: {response}" # Show response structure for debug


    except Exception as e:
        # Catch errors during response processing or API call
        return f"❌ Erro inesperado ao processar a resposta do Gemini durante a {context}: {e}"


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
        image_parts = [{"mime_type": image_type, "data": image_bytes}]

        prompt = [
            "Analise a imagem fornecida de um buraco em uma estrada. Descreva as características visíveis relevantes para um relatório de reparo de estrada.",
            "Concentre-se em:",
            "- Tamanho estimado (pequeno, médio, grande, diâmetro em relação a objetos comuns se visível)",
            "- Profundidade estimada (raso, fundo, em relação a objetos visíveis)",
            "- Presença de água ou umidade",
            "- Condição do pavimento ao redor (rachado, esfarelando, etc.)",
            "- Quaisquer perigos visíveis óbvios ou pistas de contexto *na vizinhança imediata do buraco* (por exemplo, detritos na pista, proximidade de meio-fio/acostamento).",
            "Forneça uma análise textual concisa baseada EXCLUSIVAMENTE no conteúdo da imagem. Use linguagem objetiva, focando em características físicas e observáveis.",
            image_parts[0] # Adiciona a imagem ao prompt
        ]

        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        analysis_text = process_gemini_response(response, "análise de imagem")

        # Check if the analysis_text indicates a block and if the original error was dangerous_content
        # Note: This post-check on the text string is a bit hacky. The ideal is to get the error directly from process_gemini_response.
        # Let's rely on process_gemini_response to give the structured error message.
        if analysis_text.startswith("❌"): # Indicate failure
             return {"image_analysis": analysis_text}
        else:
            return {"image_analysis": analysis_text}

    except Exception as e:
        # This catch should be for errors *before* or *during* the API call itself
        return {"image_analysis": f"❌ Erro inesperado ao chamar a API Gemini Vision: {e}"}


# Não cachear a análise de imagem diretamente aqui, será chamada no fluxo principal se houver imagem
# As funções de análise de texto são cacheadas para evitar chamadas repetidas na mesma sessão
# com os MESMOS inputs (o dicionário de dados).

@st.cache_data(show_spinner="🧠 Executando análise profunda dos dados do buraco com IA Gemini...")
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
         for key, value in informed_structured_details.items():
             value_str = ", ".join(value) if isinstance(value, list) else value
             # Traduz as chaves para o prompt de forma mais amigável (manter consistência com os inputs)
             key_translated = {
                 'tamanho': 'Tamanho Estimado',
                 'perigo': 'Nível de Perigo Aparente', # Ajustado para refletir input
                 'profundidade': 'Profundidade Estimada',
                 'presenca_agua': 'Presença de Água',
                 'contexto': 'Contexto/Histórico do Local', # Ajustado
                 'perigos_detalhados': 'Perigos e Impactos Detalhados (Selecionados)',
                 'identificadores_visuais': 'Identificadores Visuais Adicionais',
             }.get(key, key)
             structured_text += f"- {key_translated}: {value_str}\n"
    else:
         structured_text += "Nenhum detalhe estruturado relevante informado pelo usuário.\n"


    # Adiciona a análise de imagem ao contexto da IA, se disponível
    image_analysis_text = _image_analysis_ia.get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    # Se a análise de imagem resultou em um erro/indisponibilidade, informe isso claramente
    if image_analysis_text.startswith("❌") or "indisponível" in image_analysis_text or "Nenhuma imagem fornecida" in image_analysis_text:
         image_context = f"Insights da Análise de Imagem do Usuário (IA Gemini Vision): {image_analysis_text}"
    else:
         image_context = f"Insights da Análise de Imagem do Usuário (IA Gemini Vision):\n{image_analysis_text}"


    # Inclui info de localização processada para contexto (sem detalhes sensíveis de API)
    loc_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    loc_context_text = f"Localização Exata (Tipo Processado): {loc_exata.get('tipo', 'Não informado')}. "
    if loc_exata.get('latitude') is not None and loc_exata.get('longitude') is not None:
        loc_context_text += f"Coordenadas: {loc_exata.get('latitude')},{loc_exata.get('longitude')}. "
    if loc_exata.get('descricao_manual'):
         loc_context_text += f"Descrição Manual: '{loc_exata.get('descricao_manual')}'."

    prompt = f"""
    Analise os seguintes dados sobre um buraco em uma rua: detalhes estruturados, observações adicionais, análise de imagem e contexto de localização.
    Gere uma análise detalhada objetiva para um relatório de reparo. Concentre-se em consolidar as informações sobre características, riscos e contexto.
    Use linguagem clara e formal, focando em fatos inferidos dos inputs. Se a informação para uma categoria NÃO FOR CLARA OU CONSISTENTE, indique "Não claro/inconsistente nos dados" ou similar.

    Informações Brutas e Análises Iniciais:
    {structured_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    {image_context}
    Contexto de Localização: {loc_context_text}

    Análise Detalhada Consolidada (Baseada APENAS nos dados acima):
    - Severidade e Tamanho Consolidado: [Consolide tamanho e profundidade informados pelo usuário e/ou visíveis na imagem. Mencione se há divergência ou reforço entre as fontes.]
    - Presença de Água/Umidade: [Confirme a presença ou ausência conforme inputs/imagem.]
    - Fatores de Risco e Potenciais Impactos: [Liste riscos específicos citados nos inputs estruturados, observações e/ou inferidos da imagem/contexto. Foco nos perigos objetivos.]
    - Condição do Pavimento Adjacente: [Descreva o estado da rua ao redor do buraco conforme inputs/imagem.]
    - Contexto e Histórico Relevante: [Integre contexto (tráfego, recorrência, etc.) e identificadores visuais.]
    - Palavras-chave Principais para Indexação: [Liste 3-7 palavras-chave relevantes.]

    Formate a resposta usando marcadores (-) para cada categoria.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        insights_text = process_gemini_response(response, "análise detalhada")
        return {"insights": insights_text}

    except Exception as e:
        return {"insights": f"❌ Erro inesperado ao chamar a API Gemini (Análise Detalhada): {e}"}


@st.cache_data(show_spinner="🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
def categorizar_urgencia_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir uma categoria de urgência com base em todos os dados e insights."""
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache
    # Acessa todos os dados relevantes
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível.') # Usa o resultado da análise detalhada


    loc_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    loc_contexto = f"Localização (Tipo Processado): {loc_exata.get('tipo', 'Não informada')}."
    if loc_exata.get('latitude') is not None and loc_exata.get('longitude') is not None:
        loc_contexto += f" Coordenadas: {loc_exata.get('latitude')}, {loc_exata.get('longitude')}."
    elif loc_exata.get('descricao_manual'):
         loc_contexto += f" Descrição Manual: '{loc_exata.get('descricao_manual', 'Não informada')}'."

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
    Considere a severidade/tamanho/profundidade (consolidado), FATORES DE RISCO E IMPACTOS mencionados/visíveis, e qualquer CONTEXTO ADICIONAL relevante (como ser recorrente, em área de alto tráfego/risco). Dê peso especial aos FATORES DE RISCO E IMPACTOS mencionados ou visíveis. Use as informações mais confiáveis disponíveis (input estruturado > análise de imagem > observações/análise detalhada).

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem fator de risco aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, FATOR DE RISCO CLARO e/ou frequente (risco de acidente sério, dano significativo a veículo, perigo para motos/bikes/pedestres), em via movimentada ou área de risco (escola, hospital). Requer atenção RÁPIDA, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Informações Relevantes da Denúncia para Urgência:
    Localização Básica do Buraco: Rua {buraco.get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {buraco.get('numero_proximo', 'Não informado')}. Cidade: {buraco.get('endereco', {}).get('cidade_buraco', 'Não informada')}. {loc_contexto}
    {structured_urgency_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_text}
    Insights da Análise de Imagem (se disponível): {image_analysis_text}

    Com base nestes dados consolidados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 3 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais relevantes (severidade, risco, contexto, etc.) dos inputs ou análises que justificam a urgência.

    Formato de saída (muito importante seguir este formato):
    Categoria Sugerida: [Categoria Escolhida]
    Justificativa: [Justificativa Breve]
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        urgencia_text = process_gemini_response(response, "sugestão de urgência")
        return {"urgencia_ia": urgencia_text}

    except Exception as e:
        return {"urgencia_ia": f"❌ Erro inesperado ao chamar a API Gemini (Sugestão de Urgência): {e}"}


@st.cache_data(show_spinner="🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
def sugerir_causa_e_acao_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir possíveis causas do buraco e ações de reparo com base nos dados e insights."""
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Texto offline ou não configurado)."}

    # Use o dicionário completo como input para o cache
    # Acessa todos os dados relevantes
    buraco = _dados_denuncia_completa.get('buraco', {})
    structured_details = buraco.get('structured_details', {})
    observacoes_adicionais = buraco.get('observacoes_adicionais', 'Sem observações adicionais.')
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')
    insights_text = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível.') # Usa o resultado da análise detalhada

    structured_action_factors = []
    if structured_details.get('tamanho') and structured_details['tamanho'] != 'Não Informado': structured_action_factors.append(f"Tamanho Estimado (User): {structured_details['tamanho']}")
    if structured_details.get('profundidade') and structured_details['profundidade'] != 'Não Informado': structured_action_factors.append(f"Profundidade Estimada (User): {structured_details['profundidade']}")
    if structured_details.get('presenca_agua') and structured_details['presenca_agua'] != 'Não Informado': structured_action_factors.append(f"Presença de Água (User): {structured_details['presenca_agua']}")
    if structured_details.get('contexto') and structured_details['contexto'] != 'Não Informado': structured_action_factors.append(f"Contexto/Histórico (User): {structured_details['contexto']}")
    structured_action_text = "Detalhes Estruturados: " + ("; ".join(structured_action_factors) if structured_action_factors else "Nenhum informado pelo usuário.")


    prompt = f"""
    Com base nas informações completas da denúncia (dados estruturados, observações, análise de imagem e insights), tente sugerir:
    1. Uma ou duas POSSÍVEIS CAUSAS para a formação deste buraco específico. Baseie-se em pistas nos inputs (ex: se é recorrente, se há água/umidade, condição do pavimento adjacente, contexto, etc.). Seja especulativo, mas fundamentado nos dados.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema. Baseie-se na severidade, profundidade, fatores de risco, contexto e condição do pavimento. (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via).

    Baseie suas sugestões APENAS nos dados fornecidos. Se a informação for insuficiente para inferir causas ou ações, indique "Não especificado/inferido nos dados".

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
        sugestao_acao_text = process_gemini_response(response, "sugestões de causa e ação")
        return {"sugestao_acao_ia": sugestao_acao_text}

    except Exception as e:
        return {"sugestao_acao_ia": f"❌ Erro inesperado ao chamar a API Gemini (Sugestões Causa/Ação): {e}"}


@st.cache_data(show_spinner="🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
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
         for key, value in informed_structured_details.items():
              key_translated = {
                 'tamanho': 'Tamanho',
                 'perigo': 'Perigo',
                 'profundidade': 'Profundidade',
                 'presenca_agua': 'Água',
                 'contexto': 'Contexto',
                 'perigos_detalhados': 'Perigos Específicos',
                 'identificadores_visuais': 'Identificadores Visuais',
              }.get(key, key)
              value_str = ", ".join(value) if isinstance(value, list) else value
              structured_summary_items.append(f"{key_translated}: {value_str}")

    structured_summary_text = "Detalhes Estruturados Principais: " + ("; ".join(structured_summary_items) if structured_summary_items else "Nenhum detalhe estruturado relevante fornecido.")

    # Adicionar informação sobre Street View ao resumo
    streetview_summary = ""
    if streetview_image_data and 'image_bytes' in streetview_image_data:
         streetview_summary = " Imagem Street View do local obtida."
    elif streetview_image_data and 'erro' in streetview_image_data:
         streetview_summary = f" Status Street View: {streetview_image_data['erro']}"
    else:
         streetview_summary = " Tentativa de obter imagem Street View não realizada ou sem resultado."


    # Use os resultados das IAs no prompt, lidando com os possíveis prefixos de erro "❌"
    image_analysis_for_prompt = image_analysis_ia.get('image_analysis', 'Não disponível.')
    insights_for_prompt = insights_ia.get('insights', 'Não disponível.')
    urgencia_for_prompt = urgencia_ia.get('urgencia_ia', 'Não disponível.')
    sugestao_acao_for_prompt = sugestao_acao_ia.get('sugestao_acao_ia', 'Não disponível.')

    # Remover prefixos de erro "❌..." para o resumo narrativo, apenas inclua o texto após o erro
    if image_analysis_for_prompt.startswith("❌"): image_analysis_for_prompt = f"Análise de imagem indisponível/com erro: {image_analysis_for_prompt}"
    if insights_for_prompt.startswith("❌"): insights_for_prompt = f"Análise detalhada indisponível/com erro: {insights_for_prompt}"
    if urgencia_for_prompt.startswith("❌"): urgencia_for_prompt = f"Sugestão de urgência indisponível/com erro: {urgencia_for_prompt}"
    if sugestao_acao_for_prompt.startswith("❌"): sugestao_acao_for_prompt = f"Sugestões de causa/ação indisponíveis/com erro: {sugestao_acao_for_prompt}"


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 8-10 frases) para o relatório desta denúncia de buraco.
    O resumo deve ser formal, objetivo e útil para equipes de manutenção.
    Combine dados do denunciante, detalhes do buraco, observações, localização processada, resultados das análises de IA e status Street View.

    Dados Chave para o Resumo:
    Denunciante: {denunciante.get('nome', 'Não informado')}, de {denunciante.get('cidade_residencia', 'Não informada')}.
    Localização Exata Processada: {loc_info_resumo}
    {structured_summary_text}
    Observações Adicionais: "{observacoes_adicionais}"
    Análise de Imagem (IA): {image_analysis_for_prompt}
    Análise Detalhada (IA): {insights_for_prompt}
    Sugestão de Urgência (IA): {urgencia_for_prompt}
    Sugestões de Causa e Ação (IA): {sugestao_acao_for_prompt}
    Status Street View: {streetview_summary}

    Crie um resumo fluido e profissional em português. Comece com uma frase introdutória clara.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        resumo_text = process_gemini_response(response, "geração de resumo completo")
        return {"resumo_ia": resumo_text}

    except Exception as e:
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
                  # Se estiver nas etapas de CEP ou Manual, volta para a escolha do método
                  st.session_state.step = 'collect_buraco_address_method'
             elif st.session_state.step == 'processing_ia':
                 # Se estiver processando, volta para os detalhes finais
                 st.session_state.step = 'collect_buraco_details'
             else: # Para todos os outros casos, volta um passo linearmente
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
    Olá! Krateras v3.3 entrando em órbita! Sua missão, caso aceite: denunciar buracos na rua
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

    # As instruções para configurar as chaves agora aparecem na função load_api_keys
    # st.info("⚠️ Suas chaves de API do Google (...)")

    if st.button("Iniciar Missão Denúncia!"):
        # Carregar chaves e inicializar APIs antes de coletar dados
        # Isso acontece na primeira vez que o botão Iniciar é clicado.
        # Nas reruns subsequentes nesta etapa, isso será pulado a menos que o estado seja limpo.
        # Para garantir que as chaves sejam carregadas AO INICIAR a aplicação
        # (mesmo em reruns por outros motivos nesta tela), vamos carregar aqui FORA do if button
        # e usar o api_keys_loaded state.
        if not st.session_state.api_keys_loaded:
             gemini_api_key, geocoding_api_key = load_api_keys()
             st.session_state.geocoding_api_key = geocoding_api_key
             st.session_state.gemini_pro_model, st.session_state.gemini_vision_model = init_gemini_models(gemini_api_key)
             st.session_state.api_keys_loaded = True # Marca que tentamos carregar as chaves


        # Agora sim, quando o botão é clicado, avança. As chaves já foram carregadas acima.
        next_step()

# Moved API key loading and model initialization outside the button check, but guarded by api_keys_loaded state
# This ensures they are initialized when the app loads the 'start' page, even before the button click
# if not st.session_state.api_keys_loaded:
#      gemini_api_key, geocoding_api_key = load_api_keys()
#      st.session_state.geocoding_api_key = geocoding_api_key
#      st.session_state.gemini_pro_model, st.session_state.gemini_vision_model = init_gemini_models(gemini_api_key)
#      st.session_state.api_keys_loaded = True # Marca que tentamos carregar as chaves


elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Formulário para coletar dados do denunciante
    with st.form("form_denunciante"):
        # Initialize with empty strings if not in state
        nome_initial = st.session_state.denuncia_completa.get('denunciante', {}).get('nome', '')
        idade_initial = st.session_state.denuncia_completa.get('denunciante', {}).get('idade', 30) # Default idade
        cidade_residencia_initial = st.session_state.denuncia_completa.get('denunciante', {}).get('cidade_residencia', '')


        nome = st.text_input("Seu nome completo:", value=nome_initial, key='nome_denunciante_input')
        idade = st.number_input("Sua idade (aproximada, se preferir, sem pressão 😉):", min_value=1, max_value=120, value=idade_initial, key='idade_denunciante_input')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", value=cidade_residencia_initial, key='cidade_residencia_denunciante_input')

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
                # st.success(f"Olá, {nome}! Dados coletados. Preparando para dados do buraco...") # Removed to avoid double message
                next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_method':
    st.header("--- 🚧 Detalhes do Buraco (Nosso Alvo!) ---")
    st.subheader("Como identificar a rua do buraco?")

    # Initialize radio value based on previously collected address method if available
    initial_method = 'Buscar por CEP' if st.session_state.get('endereco_coletado_via') == 'cep' else \
                     'Digitar nome manualmente' if st.session_state.get('endereco_coletado_via') == 'manual' else \
                     'Digitar nome manualmente' # Default to manual

    opcao_localizacao = st.radio(
        "Escolha o método:",
        ('Digitar nome manualmente', 'Buscar por CEP'),
        index = 0 if initial_method == 'Digitar nome manualmente' else 1, # Set initial index
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

    # Ensure buraco key exists for initial values
    if 'buraco' not in st.session_state.denuncia_completa:
        st.session_state.denuncia_completa['buraco'] = {}

    with st.form("form_cep"):
        # Use um placeholder se veio do manual com CEP, ou vazio se for a primeira vez no CEP
        initial_cep = st.session_state.denuncia_completa['buraco'].get('cep_informado', '')
        cep_input = st.text_input("Digite o CEP (apenas números):", value=initial_cep, max_chars=8, key='cep_buraco_input')
        buscar_button = st.form_submit_button("Buscar CEP")

        # Reset search state vars if form is submitted (new search attempt)
        if buscar_button:
             st.session_state.cep_search_error = False
             st.session_state.dados_cep_validos = None
             if not cep_input:
                 st.error("❗ Por favor, digite um CEP.")
             else:
                 dados_cep = buscar_cep(cep_input.strip())

                 if 'erro' in dados_cep:
                     st.error(f"❌ Falha na busca por CEP: {dados_cep['erro']}")
                     st.session_state.cep_search_error = True
                     # Don't store incomplete address data if CEP search failed
                     st.session_state.denuncia_completa['buraco']['cep_informado'] = cep_input.strip() # Keep CEP input
                     if 'endereco' in st.session_state.denuncia_completa['buraco']:
                          del st.session_state.denuncia_completa['buraco']['endereco'] # Clear previous endereco if search failed
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
                     st.session_state.denuncia_completa['buraco'] = {
                          'endereco': {
                              'rua': dados_cep.get('logradouro', '').strip(),
                              'bairro': dados_cep.get('bairro', '').strip(),
                              'cidade_buraco': dados_cep.get('localidade', '').strip(),
                              'estado_buraco': dados_cep.get('uf', '').strip().upper()
                          },
                          'cep_informado': cep_input.strip()
                     }
                     # Forçar reload para exibir os botões de ação após a busca bem-sucedida
                     st.rerun()


    # Exibe botões de ação APENAS se tentou buscar CEP
    # Verifica se o formulário de busca foi processado e há um resultado (válido ou com erro)
    if 'cep_buraco_input' in st.session_state: # This means the form was rendered at least once
        if st.session_state.get('dados_cep_validos'): # If CEP data was found and is valid
            st.button("Confirmar Endereço e Avançar", on_click=next_step)
            if st.button("Corrigir Endereço Manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 # Preserve collected CEP and basic address for the manual form
                 # Already done inside the form submission check
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.rerun()

        elif st.session_state.get('cep_search_error') is True: # Explicitly check for the error state
             st.warning("Não foi possível obter o endereço por CEP.")
             if st.button("Digitar endereço manualmente"):
                  st.session_state.endereco_coletado_via = 'manual'
                  # Preserve CEP input if user switches to manual after error
                  # Already done inside the form submission check
                  st.session_state.step = 'collect_buraco_address_manual'
                  st.rerun()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_manual':
    st.header("--- 🚧 Detalhes do Buraco (Entrada Manual) ---")
    st.write("Digite os dados do endereço do buraco manualmente.")

    # Ensure buraco and endereco keys exist for initial values
    if 'buraco' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['buraco'] = {}
    if 'endereco' not in st.session_state.denuncia_completa['buraco']:
         st.session_state.denuncia_completa['buraco']['endereco'] = {}

    # Use os dados do CEP pré-preenchidos se veio dessa rota, ou use o que já foi digitado manualmente
    endereco_inicial = st.session_state.denuncia_completa['buraco'].get('endereco', {})

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
                st.session_state.denuncia_completa['buraco']['endereco'] = {
                    'rua': rua_manual.strip(),
                    'bairro': bairro_manual.strip(),
                    'cidade_buraco': cidade_manual.strip(),
                    'estado_buraco': estado_manual.strip().upper()
                }
                # Mantém o CEP se ele foi informado na etapa anterior (via CEP search)
                # st.session_state.denuncia_completa['buraco']['cep_informado'] is already set if user came from CEP step
                next_step() # Move para a próxima etapa (coleta de detalhes + foto + localização exata)

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_details':
    st.header("--- 🚧 Detalhes Finais do Buraco ---")
    st.subheader("Informações cruciais para a localização, análise e reparo!")

    # Exibe o endereço básico já coletado para referência
    endereco_basico = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})
    st.write(f"**Endereço Base Informado:** Rua {endereco_basico.get('rua', 'Não informada')}, {endereco_basico.get('cidade_buraco', 'Não informada')} - {endereco_basico.get('estado_buraco', 'Não informado')}")
    if endereco_basico.get('bairro'):
         st.write(f"**Bairro:** {endereco_basico.get('bairro')}")
    if st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado'):
         st.write(f"**CEP informado:** {st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado')}")

    st.markdown("---")

    # Ensure buraco key and structured_details key exist for initial values
    if 'buraco' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['buraco'] = {}
    if 'structured_details' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['structured_details'] = {}
    if 'observacoes_adicionais' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['observacoes_adicionais'] = ''
    if 'numero_proximo' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['numero_proximo'] = ''
    if 'lado_rua' not in st.session_state.denuncia_completa['buraco']: st.session_state.denuncia_completa['buraco']['lado_rua'] = ''
    if 'localizacao_manual_input' not in st.session_state: st.session_state.localizacao_manual_input = ''


    with st.form("form_buraco_details_structured"):
        st.subheader("Detalhes Estruturados do Buraco")

        col1, col2 = st.columns(2)

        # Initial values from state
        initial_tamanho = st.session_state.denuncia_completa['buraco']['structured_details'].get('tamanho', 'Não Informado')
        initial_profundidade = st.session_state.denuncia_completa['buraco']['structured_details'].get('profundidade', 'Não Informado')
        initial_agua = st.session_state.denuncia_completa['buraco']['structured_details'].get('presenca_agua', 'Não Informado')
        initial_perigo = st.session_state.denuncia_completa['buraco']['structured_details'].get('perigo', 'Não Informado')
        initial_contexto = st.session_state.denuncia_completa['buraco']['structured_details'].get('contexto', 'Não Informado')
        initial_perigos_detalhados = st.session_state.denuncia_completa['buraco']['structured_details'].get('perigos_detalhados', [])
        initial_identificadores = st.session_state.denuncia_completa['buraco']['structured_details'].get('identificadores_visuais', '')
        initial_numero_proximo = st.session_state.denuncia_completa['buraco'].get('numero_proximo', '')
        initial_lado_rua = st.session_state.denuncia_completa['buraco'].get('lado_rua', '')
        initial_observacoes = st.session_state.denuncia_completa['buraco'].get('observacoes_adicionais', '')
        initial_localizacao_manual = st.session_state.get('localizacao_manual_input', '')


        with col1:
            tamanho = st.radio(
                "**Tamanho Estimado:**",
                ['Não Informado', 'Pequeno (Cabe uma bola de futebol)', 'Médio (Cabe um pneu de carro)', 'Grande (Cabe uma pessoa sentada)', 'Enorme (Cobre a faixa)', 'Crítico (Cratera, afeta múltiplos veículos)'],
                index=['Não Informado', 'Pequeno (Cabe uma bola de futebol)', 'Médio (Cabe um pneu de carro)', 'Grande (Cabe uma pessoa sentada)', 'Enorme (Cobre a faixa)', 'Crítico (Cratera, afeta múltiplos veículos)'].index(initial_tamanho),
                key='tamanho_buraco'
            )
            profundidade = st.radio(
                "**Profundidade Estimada:**",
                ['Não Informado', 'Raso (Dá um susto, não danifica)', 'Médio (Pode furar pneu ou danificar suspensão)', 'Fundo (Causa dano considerável, pode entortar roda)', 'Muito Fundo (Causa acidentes graves, imobiliza veículo)'],
                index=['Não Informado', 'Raso (Dá um susto, não danifica)', 'Médio (Pode furar pneu ou danificar suspensão)', 'Fundo (Causa dano considerável, pode entortar roda)', 'Muito Fundo (Causa acidentes graves, imobiliza veículo)'].index(initial_profundidade),
                key='profundidade_buraco'
            )
            presenca_agua = st.radio(
                 "**Presença de Água/Alagamento:**",
                 ['Não Informado', 'Sim (Acumula água)', 'Não (Está seco)'],
                 index=['Não Informado', 'Sim (Acumula água)', 'Não (Está seco)'].index(initial_agua),
                 key='agua_buraco'
            )

        with col2:
             perigo = st.radio(
                 "**Nível de Risco Aparente:**", # Ajustado para "Risco"
                 ['Não Informado', 'Baixo (Principalmente estético)', 'Médio (Pode causar dano menor)', 'Alto (Risco de acidente sério ou dano significativo)', 'Altíssimo (Risco grave e iminente, acidentes frequentes)'],
                 index=['Não Informado', 'Baixo (Principalmente estético)', 'Médio (Pode causar dano menor)', 'Alto (Risco de acidente sério ou dano significativo)', 'Altíssimo (Risco grave e iminente, acidentes frequentes)'].index(initial_perigo),
                 key='perigo_buraco' # Key remains for consistency with previous data
             )
             contexto = st.selectbox(
                 "**Contexto ou Histórico do Local:**",
                 ['Não Informado', 'Via de Alto Tráfego', 'Via de Baixo Tráfego', 'Perto de Escola/Hospital', 'Em Curva', 'Na Esquina', 'Em Subida/Descida', 'Pouca Iluminação', 'Problema Recorrente', 'Obra Recente na Região'],
                 index=['Não Informado', 'Via de Alto Tráfego', 'Via de Baixo Tráfego', 'Perto de Escola/Hospital', 'Em Curva', 'Na Esquina', 'Em Subida/Descida', 'Pouca Iluminação', 'Problema Recorrente', 'Obra Recente na Região'].index(initial_contexto),
                 key='contexto_buraco'
             )
             perigos_detalhados = st.multiselect(
                 "**Fatores de Risco e Impactos Detalhados (Selecione todos que se aplicam):**", # Ajustado para "Fatores de Risco e Impactos"
                 ['Risco para Carros (Pneu/Suspensão/Roda)', 'Risco para Motos/Bikes', 'Risco para Pedestres', 'Dificulta Desvio', 'Perigoso à Noite', 'Perigoso na Chuva', 'Causa Lentidão no Trânsito', 'Já Causou Acidentes (Se souber)'],
                 default=initial_perigos_detalhados,
                 key='perigos_detalhados_buraco' # Key remains
             )


        identificadores_visuais = st.text_input(
             "**Identificadores Visuais Adicionais Próximos (Ex: Em frente ao poste X, perto da árvore Y):**",
             value=initial_identificadores,
             key='identificadores_visuais_buraco'
        )

        # Este input é movido para cá, pois é crucial para Geocoding e localização
        numero_proximo = st.text_input(
             "**Número do imóvel mais próximo ou ponto de referência (ESSENCIAL para precisão! Ex: 'Em frente ao 123', 'Esquina c/ Rua X'):**",
             value=initial_numero_proximo,
             key='numero_proximo_buraco'
        )
        lado_rua = st.text_input(
             "**Lado da rua onde está o buraco (Ex: 'lado par', 'lado ímpar', 'lado direito', 'lado esquerdo'):**",
             value=initial_lado_rua,
             key='lado_rua_buraco'
        )


        st.markdown("---")
        st.subheader("Observações Adicionais (Texto Libre)")
        observacoes_adicionais = st.text_area(
            "Qualquer outra informação relevante sobre o buraco ou o local (Histórico, chuva recente, etc.):",
            value=initial_observacoes,
            key='observacoes_adicionais_buraco'
        )

        st.markdown("---")
        st.subheader("Adicionar Foto do Buraco")
        st.write("Anexe uma foto nítida do buraco (JPG, PNG). A IA Gemini Vision pode analisar a imagem para complementar a denúncia!")
        st.info("💡 Dica: Tire a foto de um ângulo que mostre o tamanho e profundidade do buraco, e também inclua um pouco do entorno (calçada, postes, referências) para ajudar a IA e as equipes de reparo a localizarem.")

        # File uploader handles both upload and displaying info about the uploaded file
        uploaded_image = st.file_uploader("Escolha uma imagem...", type=["jpg", "jpeg", "png"], key='uploader_buraco_image')

        # Handle image upload and display
        if uploaded_image is not None:
             # Read image as bytes and store type, but only if a *new* file is uploaded
             # Streamlit re-runs, so uploaded_image is non-None even if user navigates back/forth
             # Check if the file object has changed or if bytes are not yet stored
             if st.session_state.uploaded_image_bytes is None or \
                st.session_state.uploaded_image_bytes != uploaded_image.getvalue(): # Simple check if content changed
                 try:
                     st.session_state.uploaded_image_bytes = uploaded_image.getvalue()
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
             key='localizacao_manual_input'
        )


        submitted_details = st.form_submit_button("Finalizar Coleta e Analisar Denúncia!")

        if submitted_details:
            # Perform validations AFTER submission
            if not numero_proximo or not lado_rua: # Validation for required fields
                 st.error("❗ Número próximo/referência e Lado da rua são campos obrigatórios.")
                 # Stop further execution until inputs are corrected and form is resubmitted
                 st.stop()

            # Armazena os detalhes estruturados e observações no dicionário buraco
            st.session_state.denuncia_completa['buraco'].update({
                'numero_proximo': numero_proximo.strip(),
                'lado_rua': lado_rua.strip(),
                'structured_details': {
                     'tamanho': tamanho,
                     'perigo': perigo, # Keep key as 'perigo' for consistency with previous versions/data structure
                     'profundidade': profundidade,
                     'presenca_agua': presenca_agua,
                     'contexto': contexto,
                     'perigos_detalhados': perigos_detalhados, # Keep key as 'perigos_detalhados'
                     'identificadores_visuais': identificadores_visuais.strip(),
                },
                'observacoes_adicionais': observacoes_adicionais.strip(),
                # Image bytes and type are stored separately in session state
            })

            st.subheader("Processando Localização Exata...")

            # Reset processed location data and Street View data before processing
            st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada", "motivo_falha_geocodificacao_anterior": "Não tentada/aplicável"}
            st.session_state.streetview_image_data = {"erro": "Processamento Street View pendente..."}


            tentou_geocodificar = False
            geocodificacao_sucesso = False
            lat_final: Optional[float] = None
            lon_final: Optional[float] = None
            link_maps_final: Optional[str] = None
            embed_link_final: Optional[str] = None


            # --- Tentar Geocodificação Automática Primeiro ---
            rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
            cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
            estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')
            numero_proximo_geo = st.session_state.denuncia_completa['buraco'].get('numero_proximo') # Usa o numero_proximo para geocoding

            # Geocoding requires API key and basic address (at least street, city, state) + preferably number
            tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and cidade_buraco and estado_buraco)

            if tem_dados_para_geo:
                st.info("✅ Chave de Geocodificação e dados básicos de endereço encontrados. Tentando gerar a localização exata automaticamente...")
                tentou_geocodificar = True
                with st.spinner("⏳ Chamando Google Maps Geocoding API..."):
                    geo_resultado = geocodificar_endereco(
                        rua_buraco,
                        numero_proximo_geo.strip(), # Pass number, but function handles if empty
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
                    st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = geo_resultado['erro']
            elif not st.session_state.geocoding_api_key:
                st.warning("⚠️ Chave de API de Geocodificação NÃO fornecida nos Secrets. Geocodificação automática NÃO tentada.")
                st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Chave de API de Geocodificação não fornecida."
            else: # Key is provided, but data is insufficient
                 st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes (requer pelo menos Rua, Cidade, Estado, e idealmente Número Próximo). Geocodificação automática NÃO tentada.")
                 st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Dados insuficientes para Geocodificação (requer pelo menos Rua, Cidade, Estado, e idealmente Número Próximo)."


            # --- Processar Localização Manual (se fornecida E Geocoding falhou ou não tentada) ---
            # Only process manual input if geocoding was not successful OR not attempted
            # AND manual input was actually provided
            input_original_manual = st.session_state.get('localizacao_manual_input', '').strip()

            if not geocodificacao_sucesso and input_original_manual:
                 st.info("⏳ Processando input manual de localização...")
                 lat_manual: Optional[float] = None
                 lon_manual: Optional[float] = None
                 tipo_manual_processado = "Descrição Manual Detalhada" # Default type if no coords found

                 # Attempt to extract coordinates from the manual input string
                 match_coords = re.search(r'(-?\d+\.?\d*)[,\s/]+(-?\d+\.?\d*)', input_original_manual)
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
                      # Regex to find /@-lat,long pattern in Google Maps URLs
                      match_maps_link = re.search(r'/@-?(\d+\.?\d*),-?(\d+\.?\d*)', input_original_manual) # Matches pattern /@-lat,long
                      if not match_maps_link: # Try alternative link pattern like https://maps.app.goo.gl/...?q=lat,long
                           match_maps_link = re.search(r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual) # Matches ?q=lat,long

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


                 # --- Update final coordinates/location type based on manual processing ---
                 if lat_manual is not None and lon_manual is not None:
                     # Manual coordinates successfully extracted/provided override any failed geocoding
                     lat_final = lat_manual
                     lon_final = lon_manual
                     link_maps_final = input_original_manual if input_original_manual.lower().startswith("http") else f"https://www.google.com/maps/search/?api=1&query={lat_final},{lon_final}"
                     # Attempt to generate embed link ONLY if Geocoding API key is available
                     embed_link_final = f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_final},{lon_final}" if st.session_state.geocoding_api_key else None

                     st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                          "tipo": tipo_manual_processado,
                          "input_original": input_original_manual,
                          "latitude": lat_final,
                          "longitude": lon_final,
                          "google_maps_link_gerado": link_maps_final,
                          "google_embed_link_gerado": embed_link_final,
                          "motivo_falha_geocodificacao_anterior": st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] # Keep info about geocoding attempt failure
                     }
                     if st.session_state.geocoding_api_key and embed_link_final is None:
                          st.warning("⚠️ Não foi possível gerar o link Google Maps Embed com a chave fornecida. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")
                     elif not st.session_state.geocoding_api_key:
                          st.info("ℹ️ Chave de API de Geocodificação/Embed não fornecida. Link Google Maps Embed não gerado.")


                 # If no coordinates extracted from manual input (it's just description or unrecognized)
                 elif input_original_manual:
                      # Only update if it's a manual description and no coords were found
                      st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                           "tipo": "Descrição Manual Detalhada",
                           "input_original": input_original_manual,
                           "descricao_manual": input_original_manual,
                           "motivo_falha_geocodificacao_anterior": st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] # Keep info about geocoding attempt failure
                      }
                      st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi detectada no input manual. O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")

                 # else: Input manual was empty, localizacao_exata_processada remains as initialized ("Não informada")
            elif not geocodificacao_sucesso and not input_original_manual:
                 # Geocoding failed/skipped AND manual input was empty
                 st.warning("⚠️ Nenhuma localização exata foi obtida (Geocodificação falhou ou não tentada, e input manual estava vazio). O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")
                 # The reason for geocoding failure is already set in st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior']


            # --- Obter Imagem Street View (se houver coordenadas e chave) ---
            # Attempt to get Street View ONLY if final coordinates (geocoded or manual) are available
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
                 if 'image_bytes' in st.session_state.streetview_image_data:
                      st.success("✅ Imagem Street View obtida com sucesso!")
                 elif 'erro' in st.session_state.streetview_image_data:
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
            # else: streetview_image_data remains as initialized "Processamento Street View pendente..." if logic somehow missed it,
            # which shouldn't happen with the checks above. The report handles {"erro": ...} case.


            # Now that location, Street View, and user image were processed/collected,
            # advance to the IA processing step.
            next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa todos os dados (texto, imagem) e gera o relatório com a inteligência do Google Gemini.")

    # Verifica se o modelo Gemini (texto ou visão) está disponível antes de processar
    gemini_pro_available = st.session_state.gemini_pro_model is not None
    gemini_vision_available = st.session_state.gemini_vision_model is not None

    # Initialize IA results in denuncia_completa if not already present
    if 'image_analysis_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "Status Análise Imagem IA: Não iniciada."}
    if 'insights_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['insights_ia'] = {"insights": "Status Análise Detalhada IA: Não iniciada."}
    if 'urgencia_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Status Sugestão Urgência IA: Não iniciada."}
    if 'sugestao_acao_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Status Sugestões Causa/Ação IA: Não iniciada."}
    if 'resumo_ia' not in st.session_state.denuncia_completa:
         st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Status Geração Resumo IA: Não iniciada."}


    # Define a order of operations
    processing_order = []

    # 1. Análise de Imagem (if available and needed)
    if gemini_vision_available and st.session_state.get('uploaded_image_bytes') and \
       st.session_state.denuncia_completa['image_analysis_ia'].get('image_analysis', '').startswith('Status Análise Imagem IA: Não iniciada.'): # Only run if not already processed
         processing_order.append('image_analysis')

    # 2. Text Analyses (if available and needed). They depend on collected data and potentially image analysis.
    # Only queue text analysis steps if Gemini-Pro is available and the step hasn't been initiated.
    if gemini_pro_available:
         if st.session_state.denuncia_completa['insights_ia'].get('insights', '').startswith('Status Análise Detalhada IA: Não iniciada.'):
              processing_order.append('detailed_analysis')
         # Urgency, Cause/Action, and Summary depend on detailed analysis, so queue them after
         if st.session_state.denuncia_completa['urgencia_ia'].get('urgencia_ia', '').startswith('Status Sugestão Urgência IA: Não iniciada.'):
              processing_order.append('urgency_suggestion')
         if st.session_state.denuncia_completa['sugestao_acao_ia'].get('sugestao_acao_ia', '').startswith('Status Sugestões Causa/Ação IA: Não iniciada.'):
              processing_order.append('action_suggestion')
         if st.session_state.denuncia_completa['resumo_ia'].get('resumo_ia', '').startswith('Status Geração Resumo IA: Não iniciada.'):
              processing_order.append('summary_generation')

    # Execute processing steps in order
    if processing_order:
         st.info(f"Iniciando processamento em fila: {', '.join(processing_order)}")
         for step_name in processing_order:
              if step_name == 'image_analysis':
                   st.info("🧠 Analisando a imagem do buraco com IA Gemini Vision...")
                   st.session_state.denuncia_completa['image_analysis_ia'] = analyze_image_with_gemini_vision(
                       st.session_state.uploaded_image_bytes,
                       st.session_state.uploaded_image_type,
                       st.session_state.gemini_vision_model
                   )
              elif step_name == 'detailed_analysis':
                   st.info("🧠 Executando análise profunda dos dados do buraco com IA Gemini (Texto)...")
                   st.session_state.denuncia_completa['insights_ia'] = analisar_dados_com_gemini(
                        st.session_state.denuncia_completa, # Pass complete data
                        st.session_state.gemini_pro_model
                   )
              elif step_name == 'urgency_suggestion':
                   st.info("🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
                   st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
                        st.session_state.denuncia_completa, # Pass complete data
                        st.session_state.gemini_pro_model
                   )
              elif step_name == 'action_suggestion':
                   st.info("🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
                   st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
                        st.session_state.denuncia_completa, # Pass complete data
                        st.session_state.gemini_pro_model
                   )
              elif step_name == 'summary_generation':
                   st.info("🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
                   st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
                        st.session_state.denuncia_completa, # Pass complete data
                        st.session_state.gemini_pro_model
                   )

         # After processing all queued steps, advance
         st.success("✅ Todas as análises de IA solicitadas foram concluídas (ou ignoradas se modelos indisponíveis).")
         next_step()

    elif not gemini_pro_available and not gemini_vision_available:
         st.warning("⚠️ Nenhuma análise de IA foi executada (Modelos Gemini não configurados ou indisponíveis).")
         st.button("Avançar para o Relatório (Sem IA)", on_click=next_step) # Provide way to continue

    else: # Some models available, but no tasks queued (e.g. user re-ran processing page)
         st.info("Todas as análises de IA já foram concluídas para esta denúncia.")
         st.button("Ver Relatório", on_click=next_step) # Just go to report


    st.button("Voltar", on_click=prev_step)


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
        st.write(f"**Lado da Rua:** {buraco.get('lado_rua', 'Não informado')}")

        st.subheader("Detalhes Estruturados Preenchidos")
        if structured_details:
            # Filtrar os detalhes que não foram informados para não poluir o relatório
            informed_details = {k: v for k, v in structured_details.items() if v and (not isinstance(v, list) or v)}
            if informed_details:
                 # Exibir os detalhes informados de forma limpa
                 for key in ['tamanho', 'profundidade', 'presenca_agua', 'perigo', 'contexto', 'perigos_detalhados', 'identificadores_visuais']: # Maintain order
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
                  # This case should ideally not happen with the improved error handling,
                  # as streetview_image_data should contain 'erro' if not successful.
                  # Kept as a fallback.
                  st.info("ℹ️ Tentativa de obter imagem Street View não realizada ou sem resultado específico registrado.")


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
                  # This could happen if get_street_view_image (which generates the embed link in some cases)
                  # had a specific issue, or if coords came from manual input parsing that didn't generate it.
                  # Re-generate if possible, or show warning. The logic in collect_buraco_details
                  # should generate embed_link_gerado if key exists and coords found (either geo or manual).
                  # If it's None here, it implies the generation failed or was skipped unexpectedly.
                  # Let's assume the generation logic in details step is sufficient.
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


        # Includes the reason for geocoding failure if applicable
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior') and not localizacao_exata.get('motivo_falha_geocodificacao_anterior').startswith('Não tentada/aplicável'):
             st.info(f"ℹ️ Nota: Não foi possível obter a localização exata via Geocodificação automática. Motivo: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")


    st.markdown("---")

    # Exibir análises de IA (even if they failed, the error message from process_gemini_response will be shown)
    gemini_pro_available = st.session_state.gemini_pro_model is not None
    gemini_vision_available = st.session_state.gemini_vision_model is not None

    if gemini_pro_available or gemini_vision_available:

        with st.expander("🧠 Análise de Imagem (IA Gemini Vision)", expanded=True):
             st.write(image_analysis_ia.get('image_analysis', 'Análise de imagem não realizada ou com erro inesperado.')) # Default if key missing
             if not gemini_vision_available:
                  st.info("ℹ️ Motor Gemini Vision indisponível ou não configurado. Análise de imagem não realizada.")
             elif not st.session_state.get('uploaded_image_bytes'):
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


    else: # Neither Gemini model was available
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chaves Gemini não configuradas ou modelos indisponíveis).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Option to start new process
    if st.button("Iniciar Nova Denúncia", key='new_denuncia_button'):
        # Clear session state except for API keys and models (which are cached resources)
        for key in list(st.session_state.keys()): # Iterate over a copy of keys as we modify the dict
            # Keep API keys, models, and the flag indicating keys were loaded
            if key not in ['geocoding_api_key', 'gemini_pro_model', 'gemini_vision_model', 'api_keys_loaded']:
                 del st.session_state[key]
        st.rerun()

    # Option to display raw data (useful for debug or export)
    with st.expander("🔌 Ver Dados Brutos da Denúncia (JSON)"):
        # Remove image bytes from Street View and user upload for JSON serialization
        dados_para_json = dados_completos.copy()

        # Handle streetview_image_data
        if 'streetview_image_data' in dados_para_json and dados_para_json['streetview_image_data'] is not None:
             if 'image_bytes' in dados_para_json['streetview_image_data']:
                  # Create a copy excluding image_bytes
                  streetview_data_clean = dados_para_json['streetview_image_data'].copy()
                  del streetview_data_clean['image_bytes']
                  streetview_data_clean['note'] = "image_bytes_removed_for_json_view"
                  dados_para_json['streetview_image_data'] = streetview_data_clean
             # Else: streetview_image_data is already serializable (contains 'erro' or is None/empty)
        elif 'streetview_image_data' in dados_para_json and dados_para_json['streetview_image_data'] is None:
             dados_para_json['streetview_image_data'] = None # Ensure explicit None if it was None

        # Handle uploaded_image_bytes
        if 'uploaded_image_bytes' in st.session_state and st.session_state.uploaded_image_bytes is not None:
             dados_para_json['uploaded_image_bytes'] = "image_bytes_removed_for_json_view"
             dados_para_json['uploaded_image_type'] = st.session_state.uploaded_image_type # Keep type info
        elif 'uploaded_image_bytes' in st.session_state and st.session_state.uploaded_image_bytes is None:
             dados_para_json['uploaded_image_bytes'] = None
             dados_para_json['uploaded_image_type'] = None
        # Ensure the old 'uploaded_image' key (if it somehow persisted) is also handled
        if 'uploaded_image' in dados_para_json:
            del dados_para_json['uploaded_image']


        try:
             st.json(dados_para_json)
        except Exception as e:
             st.error(f"❌ Erro ao serializar dados para JSON. Verifique a estrutura: {e}")
             # As a fallback, try printing a simpler representation
             st.write("Erro ao exibir JSON. Conteúdo:")
             st.write(dados_para_json)
