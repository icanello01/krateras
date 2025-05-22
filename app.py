# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v3.2 - Streamlit Advanced Edition)

Bem-vindo à versão visual e aprimorada do Krateras! Agora com interface rica,
análise de imagem por IA, inputs estruturados e segurança de credenciais reforçada.

Tecnologias: Python, Streamlit, Google Gemini API (Vision & Pro), Google Geocoding API, ViaCEP.
Objetivo: Coletar dados estruturados e ricos de denúncias de buracos, analisar texto E imagem
com IA, gerar relatórios detalhados, priorizados e acionáveis, incluindo localização
visual em mapa e resumo inteligente.

Vamos juntos consertar essas ruas com a mais alta tecnologia disponível!
Iniciando sistemas visuais, robóticos e de inteligência artificial...
"""

import streamlit as st
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import re
import json
import pandas as pd
from PIL import Image # Para trabalhar com imagens

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Krateras 🚀✨🔒 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados (Para um toque extra de tecnologia e clareza) ---
st.markdown("""
<style>
    /* Geral */
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4 {
        color: #4A90E2; /* Azul Cratera */
        font-weight: bold;
    }
    h1 { font-size: 2.5em; margin-bottom: 0.5em; }
    h2 { font-size: 1.8em; margin-top: 1.5em; margin-bottom: 0.8em;}
    h3 { font-size: 1.4em; margin-top: 1.2em; margin-bottom: 0.6em;}
    h4 { font-size: 1.1em; margin-top: 1em; margin-bottom: 0.4em;}

    /* Botões */
    .stButton>button {
        background-color: #50E3C2; /* Verde Robô */
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        margin-top: 1rem;
        margin-right: 0.5rem;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #00B894; /* Verde Robô Escuro */
        color: white;
    }
    .stButton>button:active {
         background-color: #008C74;
    }

    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 5px;
        padding: 0.5rem;
        border: 1px solid #ccc;
    }
     .stSelectbox>div>div, .stRadio>div {
         margin-bottom: 10px;
     }

    /* Feedback Boxes */
    .css-1aumqxt { border-left: 5px solid #4A90E2 !important; background-color: #E6F3FF; } /* st.info */
    .css-1r6cdft { border-left: 5px solid #F5A623 !important; background-color: #FFF8E1; } /* st.warning */
    .css-t9s6qg { border-left: 5px solid #D0021B !important; background-color: #FFEBEE; } /* st.error */
    .css-1u3jtzg { border-left: 5px solid #7ED321 !important; background-color: #F1F8E9; } /* st.success */

    /* Spinners */
    .stSpinner > div > div {
        border-top-color: #4A90E2 !important;
    }

    /* Expanders (Menus Sanfona) */
    .streamlit-expanderHeader {
        font-size: 1.1em !important;
        font-weight: bold !important;
        color: #4A90E2 !important;
        background-color: #F0F2F6; /* Cinza claro para cabeçalhos */
        border-radius: 5px;
        padding: 0.8rem;
        margin-top: 1rem;
        border: 1px solid #ccc;
    }
    .streamlit-expanderContent {
         background-color: #FFFFFF; /* Fundo branco para o conteúdo */
         padding: 1rem;
         border-left: 1px solid #ccc;
         border-right: 1px solid #ccc;
         border-bottom: 1px solid #ccc;
         border-radius: 0 0 5px 5px;
    }

    /* Separadores */
    hr {
        margin-top: 2em;
        margin-bottom: 2em;
        border: 0;
        border-top: 1px solid #eee;
    }

    /* Imagem upload area */
    .stFileUploader label {
        font-weight: bold;
        color: #4A90E2;
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
if 'image_analysis_result' not in st.session_state:
     st.session_state.image_analysis_result = None


# --- 🔑 Gerenciamento de Chaves Secretas (Streamlit Secrets) ---
# Utiliza o .streamlit/secrets.toml para carregar chaves de forma segura

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    """
    Tenta obter as chaves de API do Google Gemini e Google Maps Geocoding de Streamlit Secrets.
    Retorna None se não encontradas.
    """
    # Chaves definidas no .streamlit/secrets.toml
    gemini_key = st.secrets.get('GOOGLE_API_KEY') # Usada para Gemini-Pro e Gemini-Vision
    geocoding_key = st.secrets.get('geocoding_api_key') # Usada para Geocoding e Embed

    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA do Gemini estarão desabilitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática e Visualização Google Maps Embed estarão desabilitadas.")
        st.info("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit (se ainda não existir a pasta `.streamlit`) com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\n**IMPORTANTE:** Não comite o arquivo `secrets.toml` para repositórios públicos no GitHub! O Streamlit Cloud tem uma interface segura para adicionar estes segredos.")
        st.info("❗ A API Geocoding e a Maps Embed API PODE gerar custos. Verifique a precificação do Google Cloud e habilite-as no seu projeto Google Cloud Platform (Console -> APIs & Services -> Library). O erro 'This API project is not authorized to use this API' para o mapa Embed geralmente significa que a 'Maps Embed API' não está habilitada ou autorizada para a chave.")


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

# Não cachear a Geocodificação diretamente, pois depende de inputs no formulário
# e o resultado da localização manual também precisa ser processado no mesmo fluxo.
# A chamada será feita dentro do fluxo do Streamlit.
# @st.cache_data(show_spinner="⏳ Tentando localizar o buraco no mapa global via Geocoding API...")
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
        if api_key: # Verifica se a chave existe antes de gerar o link embed
             google_embed_link = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"


        return {
            "latitude": lat,
            "longitude": lng,
            "endereco_formatado_api": formatted_address,
            "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
            "google_embed_link_gerado": google_embed_link
        }
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({15}s) ao tentar geocodificar: {address}"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro na comunicação com a API de Geocodificação: {address}. Detalhes: {e}"}
    except Exception as e:
        return {"erro": f"Ocorreu um erro inesperado durante a geocodificação: {address}. Detalhes: {e}"}


# --- Funções de Análise de IA (Cacheado para resultados estáveis por sessão, exceto análise de imagem) ---
# Safety settings configuradas para permitir discussões sobre perigos na rua
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Não cachear a análise de imagem diretamente aqui, será chamada no fluxo principal se houver imagem
# @st.cache_data(show_spinner="🧠 Analisando a imagem do buraco com IA Gemini Vision...")
def analyze_image_with_gemini_vision(image_bytes: bytes, model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini Vision para analisar uma imagem e extrair características do buraco."""
    if not model:
        return {"image_analysis": "🤖 Análise de imagem via IA indisponível (Motor Gemini Vision offline)."}
    if not image_bytes:
         return {"image_analysis": "🔍 Nenhuma imagem fornecida para análise de IA."}

    try:
        # O Gemini Vision aceita bytes da imagem
        image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]

        prompt = [
            "Analyze the provided image of a hole in the road. Describe the visible characteristics relevant to a road repair report. Focus on:",
            "- Estimated size (e.g., small, medium, large, diameter relative to common objects if visible)",
            "- Estimated depth (e.g., shallow, deep, relative to visible objects)",
            "- Presence of water or moisture",
            "- Any obvious visible dangers or context clues in the immediate vicinity of the hole itself (e.g., cracked pavement around it, debris)",
            "Provide a concise textual analysis based SOLELY on the image content.",
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

         structured_text += f"- {key_translated}: {value_str}\n"

    # Adiciona a análise de imagem ao contexto da IA, se disponível
    image_analysis_text = _image_analysis_ia.get('image_analysis', 'Análise de imagem não disponível ou com erro.')
    if "Análise de imagem via IA indisponível" in image_analysis_text or "Nenhuma imagem fornecida" in image_analysis_text:
         image_context = "Nota: Análise de imagem não foi realizada ou está indisponível."
    else:
         image_context = f"Insights da Análise de Imagem (IA Gemini Vision):\n{image_analysis_text}"


    prompt = f"""
    Analise os seguintes dados estruturados, observações adicionais e (se disponível) a análise de uma imagem, todos relacionados a uma denúncia de um buraco em uma rua. Seu objetivo é extrair insights CRUCIAIS e gerar uma análise detalhada objetiva para um sistema de reparo público.

    {structured_text}

    Observações Adicionais do Usuário: "{observacoes_adicionais}"

    {image_context}

    Com base NESTAS informações (estruturadas, observações e análise de imagem), gere uma análise detalhada. Formate a saída como texto claro, usando marcadores (-) ou títulos. Se uma categoria NÃO PUDER ser confirmada com ALTA CONFIANÇA pelas informações fornecidas, indique "Não especificado/inferido".

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
         loc_contexto += f" (Nota: Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior', 'Motivo desconhecido')})"


    # Formatar os detalhes estruturados para o prompt de urgência
    structured_urgency_factors = []
    if structured_details.get('tamanho'): structured_urgency_factors.append(f"Tamanho Estimado: {structured_details['tamanho']}")
    if structured_details.get('profundidade'): structured_urgency_factors.append(f"Profundidade Estimada: {structured_details['profundidade']}")
    if structured_details.get('perigo'): structured_urgency_factors.append(f"Nível de Perigo: {structured_details['perigo']}")
    if structured_details.get('presenca_agua'): structured_urgency_factors.append(f"Presença de Água: {structured_details['presenca_agua']}")
    if structured_details.get('perigos_detalhados'): structured_urgency_factors.append(f"Perigos Detalhados (Selecionados): {', '.join(structured_details['perigos_detalhados'])}")
    if structured_details.get('contexto'): structured_urgency_factors.append(f"Contexto/Histórico: {structured_details['contexto']}")
    structured_urgency_text = "Detalhes Estruturados: " + ("; ".join(structured_urgency_factors) if structured_urgency_factors else "Nenhum informado.")


    prompt = f"""
    Com base nas informações completas da denúncia, análise de imagem (se disponível) e insights extraídos, sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade/tamanho, profundidade, PERIGOS POTENCIAIS e impactos mencionados/visíveis, e qualquer CONTEXTO ADICIONAL relevante (como ser recorrente, em área de alto tráfego/risco, perto de local importante). Dê peso especial aos PERIGOS mencionados ou visíveis.

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem perigo aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, perigo CLARO e/ou frequente (risco de acidente mais sério, dano significativo a veículo, perigo para motos/bikes/pedestres), em via movimentada ou área de risco (escola, hospital). Requer atenção RÁPIDA, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Informações Relevantes da Denúncia:
    Localização Básica do Buraco: Rua {buraco.get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {buraco.get('numero_proximo', 'Não informado')}. Cidade: {buraco.get('endereco', {}).get('cidade_buraco', 'Não informada')}. {loc_contexto}
    {structured_urgency_text}
    Observações Adicionais do Usuário: "{observacoes_adicionais}"
    Insights da Análise Detalhada de IA: {insights_text}
    Insights da Análise de Imagem (se disponível): {image_analysis_text}

    Com base nestes dados consolidados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 3 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais relevantes (tamanho, perigo, contexto, etc.) dos inputs ou análises.

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
    if structured_details.get('tamanho'): structured_action_factors.append(f"Tamanho Estimado: {structured_details['tamanho']}")
    if structured_details.get('profundidade'): structured_action_factors.append(f"Profundidade Estimada: {structured_details['profundidade']}")
    if structured_details.get('presenca_agua'): structured_action_factors.append(f"Presença de Água: {structured_details['presenca_agua']}")
    if structured_details.get('contexto'): structured_action_factors.append(f"Contexto/Histórico: {structured_details['contexto']}")
    structured_action_text = "Detalhes Estruturados: " + ("; ".join(structured_action_factors) if structured_action_factors else "Nenhum informado.")


    prompt = f"""
    Com base nas informações completas da denúncia (dados estruturados, observações, análise de imagem e insights), tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico. Baseie-se em pistas nos inputs (ex: se é recorrente, se choveu muito - se mencionado nas observações/insights/imagem -, desgaste visível na imagem, etc.). Seja especulativo, mas baseado nos dados.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema. Baseie-se na severidade, profundidade, perigos e contexto. (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via).

    Baseie suas sugestões nos dados fornecidos. Se a informação for insuficiente, indique "Não especificado/inferido nos dados".

    Informações Relevantes da Denúncia:
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
             return {"sugestao_acao_ia": f"❌ Sugestão de causa/ação bloqueada pelos protocolos de segurança do Gemini. Motivo: {block_reason}"}

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

    insights_ia = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise detalhada não disponível ou com erro.')
    urgencia_ia_text = _dados_denuncia_completa.get('urgencia_ia', {}).get('urgencia_ia', 'Sugestão de urgência não disponível ou com erro.')
    sugestao_acao_ia_text = _dados_denuncia_completa.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', 'Sugestões de causa/ação não disponíveis ou com erro.')
    image_analysis_text = _dados_denuncia_completa.get('image_analysis_ia', {}).get('image_analysis', 'Análise de imagem não disponível.')


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
    if structured_details.get('tamanho'): structured_summary_items.append(f"Tamanho: {structured_details['tamanho']}")
    if structured_details.get('profundidade'): structured_summary_items.append(f"Profundidade: {structured_details['profundidade']}")
    if structured_details.get('perigo'): structured_summary_items.append(f"Perigo: {structured_details['perigo']}")
    if structured_details.get('presenca_agua'): structured_summary_items.append(f"Água: {structured_details['presenca_agua']}")
    if structured_details.get('perigos_detalhados'): structured_summary_items.append(f"Perigos Específicos: {', '.join(structured_details['perigos_detalhados'])}")
    if structured_details.get('contexto'): structured_summary_items.append(f"Contexto: {structured_details['contexto']}")
    if structured_details.get('identificadores_visuais'): structured_summary_items.append(f"Identificadores Visuais: {structured_details['identificadores_visuais']}")

    structured_summary_text = " / ".join(structured_summary_items) if structured_summary_items else "Detalhes estruturados não fornecidos."


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 8-10 frases) para a seguinte denúncia de buraco no aplicativo Krateras.
    Este resumo deve ser formal, objetivo e útil para equipes de manutenção ou gestão pública.
    Combine os dados do denunciante, detalhes estruturados do buraco, observações adicionais, localização exata processada e os resultados de TODAS as análises de IA (análise de imagem, análise detalhada, urgência, causa/ação).

    Inclua:
    - Denunciante (Nome, Cidade de Residência).
    - Localização base (Rua, Nº Próximo/Referência, Cidade do Buraco, Estado do Buraco).
    - Localização EXATA processada (mencione como foi obtida e os dados relevantes).
    - Resumo dos DETALHES ESTRUTURADOS e Observações Adicionais.
    - Principais pontos da ANÁLISE DE IMAGEM (se disponível).
    - Principais pontos da ANÁLISE DETALHADA.
    - A SUGESTÃO de Categoria de Urgência pela IA e sua Justificativa.
    - As SUGESTÕES de POSSÍVEIS CAUSAS e TIPOS DE AÇÃO/REPARO sugeridas pela IA (se disponíveis).

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
        'processing_ia', # Nova etapa unificada para todas as análises IA (imagem + texto)
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
    para análise de imagem) e APIs de localização (Google Geocoding, ViaCEP) para coletar,
    analisar e gerar um relatório detalhado e acionável para as autoridades competentes.

    Fui criado com o que há de mais avançado em Programação, IA, Design Inteligente,
    Matemática e Lógica Inabalável. Com acesso seguro às APIs, sou imparável.

    Clique em Iniciar para começarmos a coleta de dados.
    """)

    st.info("⚠️ Suas chaves de API do Google (Gemini e Geocoding/Embed) devem ser configuradas nos Streamlit Secrets (`.streamlit/secrets.toml`) para que as funcionalidades de IA e a geocodificação/visualização automática no mapa funcionem corretamente e de forma segura. Consulte o `README.md` ou as instruções ao lado para mais detalhes.")


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
                ['Não Informado', 'Pequeno', 'Médio', 'Grande', 'Enorme', 'Crítico (Cratera)'],
                key='tamanho_buraco'
            )
            profundidade = st.radio(
                "**Profundidade Estimada:**",
                ['Não Informado', 'Raso', 'Médio', 'Fundo', 'Muito Fundo'],
                key='profundidade_buraco'
            )
            presenca_agua = st.radio(
                 "**Presença de Água/Alagamento:**",
                 ['Não Informado', 'Sim', 'Não'],
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

        st.markdown("---")
        st.subheader("Observações Adicionais (Texto Livre)")
        observacoes_adicionais = st.text_area(
            "Qualquer outra informação relevante sobre o buraco ou o local (Histórico, chuva recente, etc.):",
            key='observacoes_adicionais_buraco'
        )

        st.markdown("---")
        st.subheader("Adicionar Foto do Buraco")
        st.write("Anexe uma foto nítida do buraco (JPG, PNG). A IA Gemini Vision pode analisar a imagem para complementar a denúncia!")
        uploaded_image = st.file_uploader("Escolha uma imagem...", type=["jpg", "jpeg", "png"], key='uploader_buraco_image')

        if uploaded_image is not None:
             st.session_state.uploaded_image = uploaded_image.getvalue() # Armazena os bytes da imagem no estado
             try:
                 img = Image.open(uploaded_image)
                 st.image(img, caption="Foto do buraco carregada.", use_column_width=True)
             except Exception as e:
                  st.error(f"❌ Erro ao carregar a imagem: {e}")
                  st.session_state.uploaded_image = None # Limpa se der erro ao abrir


        st.markdown("---")
        st.subheader("📍 Localização Exata (Coordenadas ou Descrição)")

        # --- Tentar Geocodificação Automática ao submeter ---
        # A geocodificação agora acontece APÓS submeter este formulário
        # O input para localização manual só aparece se a geocodificação falhar ou não for tentada.

        submitted_details = st.form_submit_button("Finalizar Coleta e Analisar Denúncia!")

        if submitted_details:
            # Armazena os detalhes estruturados e observações no dicionário buraco
            st.session_state.denuncia_completa['buraco'].update({
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
                # A imagem já está no st.session_state.uploaded_image
            })

            st.subheader("Processando Localização Exata...")

            st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"} # Reseta localização processada
            tentou_geocodificar = False
            geocodificacao_sucesso = False
            motivo_falha_geo = ""

            rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
            cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
            estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')
            numero_proximo_geo = st.session_state.denuncia_completa['buraco'].get('numero_proximo') # Usa o numero_proximo para geocoding

            tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and numero_proximo_geo and cidade_buraco and estado_buraco)

            if tem_dados_para_geo:
                st.info("✅ Chave de Geocodificação e dados básicos de endereço completos encontrados. Tentando gerar o link do Google Maps automaticamente...")
                tentou_geocodificar = True
                # Chamar a função de geocodificação (NÃO cacheada)
                geo_resultado = geocodificar_endereco(
                    rua_buraco,
                    numero_proximo_geo.strip(), # Usa o número/referência como base para geocodificação
                    cidade_buraco,
                    estado_buraco,
                    st.session_state.geocoding_api_key
                )

                if 'erro' not in geo_resultado:
                    geocodificacao_sucesso = True
                    st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                        "tipo": "Geocodificada (API)",
                        "latitude": geo_resultado['latitude'],
                        "longitude": geo_resultado['longitude'],
                        "endereco_formatado_api": geo_resultado.get('endereco_formatado_api', ''),
                        "google_maps_link_gerado": geo_resultado['google_maps_link_gerado'],
                        "google_embed_link_gerado": geo_resultado.get('google_embed_link_gerado') # Pode ser None se chave faltar/API desabilitada
                    }
                    st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                else: # Erro na geocodificação
                    st.warning(f"❌ Falha na Geocodificação automática: {geo_resultado['erro']}")
                    motivo_falha_geo = f"Erro da API de Geocodificação: {geo_resultado.get('erro', 'Motivo desconhecido')}"
            elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes (precisa de Rua, Número Próximo, Cidade, Estado). Geocodificação automática NÃO tentada.")
                motivo_falha_geo = "Dados insuficientes para Geocodificação (requer Rua, Número Próximo, Cidade, Estado)."
            elif not st.session_state.geocoding_api_key:
                st.warning("⚠️ AVISO: Chave de API de Geocodificação NÃO fornecida. Geocodificação automática NÃO tentada.")
                motivo_falha_geo = "Chave de API de Geocodificação não fornecida."


            # --- Coleta/Processamento de Localização Manual (se a geocodificação falhou ou não foi tentada) ---
            # Este input aparece SOMENTE APÓS a submissão do formulário principal,
            # E SOMENTE SE a geocodificação automática não foi bem-sucedida.
            # Usamos um novo formulário ou tratamos no fluxo. Vamos tratar no fluxo após o form submetido.

            if not geocodificacao_sucesso:
                 st.subheader("--- ✍️ Fornecer Localização Exata Manualmente (Alternativa ou Correção) ---")
                 if motivo_falha_geo:
                      st.info(f"(Motivo para entrada manual: {motivo_falha_geo})")

                 st.write("➡️ Por favor, forneça a localização EXATA do buraco de forma manual:")
                 st.markdown("""
                 <p>A MELHOR forma é COPIAR AS COORDENADAS (Lat,Long) ou um LINK do Google Maps que as contenha.<br>
                 Sugestão: Abra o Google Maps, encontre o buraco, <strong>TOQUE/CLIQUE E SEGURE NO LOCAL PREOCUPANTE</strong>.
                 As coordenadas ou um link aparecerão.</p>
                 <p>Alternativamente, uma DESCRIÇÃO MUITO DETALHADA do local EXATO no mapa.</p>
                 """, unsafe_allow_html=True)

                 # Este input é exibido e processado imediatamente após a falha da geocodificação
                 localizacao_manual_input = st.text_input("Insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO DETALHADA:", key='localizacao_manual_input')

                 # Tentar extrair coordenadas do input manual
                 lat: Optional[float] = None
                 lon: Optional[float] = None
                 tipo_manual_processado = "Descrição Manual Detalhada"
                 input_original_manual = localizacao_manual_input.strip()

                 if input_original_manual:
                     match_coords = re.search(r'(-?\d+\.?\d*)[,\s/]+(-?\d+\.?\d*)', input_original_manual)
                     if match_coords:
                         try:
                             teste_lat = float(match_coords.group(1))
                             teste_lon = float(match_coords.group(2))
                             if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                                 lat = teste_lat
                                 lon = teste_lon
                                 tipo_manual_processado = "Coordenadas Fornecidas/Extraídas Manualmente"
                                 st.info("✅ Coordenadas válidas detectadas no input manual! Navegação calibrada.")
                             else:
                                 st.warning("⚠️ Parece um formato de coordenadas, mas fora da faixa esperada. Tratando como descrição.")
                         except ValueError:
                             st.info("ℹ️ Entrada manual não parece ser coordenadas válidas. Tratando como descrição detalhada.")
                     elif input_original_manual.startswith("http"):
                          st.info("ℹ️ Entrada manual é um link. Tentando extrair coordenadas (sujeito a formato do link)...")
                          match_maps_link = re.search(r'/@(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual)
                          if match_maps_link:
                              try:
                                  teste_lat = float(match_maps_link.group(1))
                                  teste_lon = float(match_maps_link.group(2))
                                  if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                                       lat = teste_lat
                                       lon = teste_lon
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
                          st.info("ℹ️ Entrada manual não detectada como coordenadas ou link. Tratando como descrição detalhada.")


                 # Armazenar o resultado do input manual no dicionário de localização processada
                 if lat is not None and lon is not None:
                     st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                          "tipo": tipo_manual_processado,
                          "input_original": input_original_manual,
                          "latitude": lat,
                          "longitude": lon,
                          "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                          # Tenta gerar link embed APENAS se tiver a chave Geocoding (necessária para o Embed API)
                          "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat},{lon}" if st.session_state.geocoding_api_key else None
                     }
                     if st.session_state.geocoding_api_key and st.session_state.denuncia_completa['localizacao_exata_processada'].get('google_embed_link_gerado') is None:
                          # Adiciona um aviso específico se tinha chave mas não gerou embed link
                          st.warning("⚠️ Não foi possível gerar o link Google Maps Embed com a chave fornecida. Verifique se a 'Maps Embed API' está habilitada e autorizada para sua chave no Google Cloud.")

                 elif input_original_manual: # Se há input manual, mas não extraiu Lat/Long
                     st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                          "tipo": "Descrição Manual Detalhada",
                          "input_original": input_original_manual,
                          "descricao_manual": input_original_manual
                     }
                     st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi fornecida ou detectada no input manual. O relatório dependerá apenas da descrição textual e endereço base.")

                 else: # Input manual estava vazio, localizacao_exata_processada continua como "Não informada"
                      st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas, link) foi fornecida, detectada automaticamente (Geocoding) ou inserida manualmente. O relatório dependerá apenas dos detalhes estruturados, observações e endereço base.")


                 # Se houve uma tentativa de geocodificação automática que falhou, registra o motivo
                 if tentou_geocodificar and not geocodificacao_sucesso:
                      st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = motivo_falha_geo
                 elif not st.session_state.geocoding_api_key:
                      st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Chave de API de Geocodificação não fornecida."
                 elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                      st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Dados insuficientes para Geocodificação (requer Rua, Número Próximo, Cidade, Estado)."


                 # Após processar o input manual (se necessário), avançamos para o passo de processamento IA
                 next_step()

            else: # Se a geocodificação automática foi bem-sucedida, apenas avançamos para o passo de processamento IA
                next_step()


    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa todos os dados (texto, imagem) e gera o relatório com a inteligência do Google Gemini.")

    # Verifica se o modelo Gemini (texto ou visão) está disponível antes de processar
    gemini_available = st.session_state.gemini_pro_model or st.session_state.gemini_vision_model

    # Inicializa resultados IA com valores padrão
    st.session_state.denuncia_completa['image_analysis_ia'] = {"image_analysis": "Análise de imagem via IA indisponível."}
    st.session_state.denuncia_completa['insights_ia'] = {"insights": "Análise detalhada via IA indisponível."}
    st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Sugestão de urgência via IA indisponível."}
    st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Sugestões de causa/ação via IA indisponíveis."}
    st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Resumo completo via IA indisponível."}

    if gemini_available:
        # 1. Análise de Imagem (se houver imagem e modelo Vision)
        if st.session_state.uploaded_image and st.session_state.gemini_vision_model:
             st.info("🧠 Analisando a imagem do buraco com IA Gemini Vision...")
             st.session_state.denuncia_completa['image_analysis_ia'] = analyze_image_with_gemini_vision(st.session_state.uploaded_image, st.session_state.gemini_vision_model)
             # Exibe o resultado da análise de imagem imediatamente após processar
             # st.write("**Análise de Imagem (IA):**")
             # st.write(st.session_state.denuncia_completa['image_analysis_ia'].get('image_analysis', 'Erro ou sem análise.'))


        # 2. Análise de Texto/Dados Consolidados (se modelo Pro)
        if st.session_state.gemini_pro_model:
             buraco_data = st.session_state.denuncia_completa.get('buraco', {})
             image_analysis_result_for_text_model = st.session_state.denuncia_completa.get('image_analysis_ia', {}) # Passa o resultado da análise de imagem

             st.info("🧠 Executando análise profunda dos dados do buraco com IA Gemini (Texto)...")
             # A análise detalhada agora recebe os dados estruturados, observações E o resultado da análise de imagem
             st.session_state.denuncia_completa['insights_ia'] = analisar_dados_com_gemini(
                 buraco_data,
                 image_analysis_result_for_text_model,
                 st.session_state.gemini_pro_model
             )
             # st.write("**Análise Detalhada (IA):**")
             # st.write(st.session_state.denuncia_completa['insights_ia'].get('insights', 'Erro ou sem análise.'))


             st.info("🧠 Calculando o Nível de Prioridade Robótica para esta denúncia...")
             # A sugestão de urgência recebe TODOS os dados completos
             st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
                 st.session_state.denuncia_completa, # Passa o dicionário completo
                 st.session_state.gemini_pro_model
            )
             # st.write("**Sugestão de Urgência (IA):**")
             # st.write(st.session_state.denuncia_completa['urgencia_ia'].get('urgencia_ia', 'Erro ou sem sugestão.'))


             st.info("🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
             # As sugestões de causa/ação recebem TODOS os dados completos
             st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
                 st.session_state.denuncia_completa, # Passa o dicionário completo
                 st.session_state.gemini_pro_model
            )
             # st.write("**Sugestões de Causa e Ação (IA):**")
             # st.write(st.session_state.denuncia_completa['sugestao_acao_ia'].get('sugestao_acao_ia', 'Erro ou sem sugestões.'))

             st.info("🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
             # A geração do resumo recebe TODOS os dados completos
             st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
                 st.session_state.denuncia_completa, # Passa o dicionário completo
                 st.session_state.gemini_pro_model
            )
             # st.write("**Resumo Narrativo (IA):**")
             # st.write(st.session_state.denuncia_completa['resumo_ia'].get('resumo_ia', 'Erro ou sem resumo.'))


        # Avança para exibir o relatório após TODO o processamento de IA
        st.success("✅ Análises de IA concluídas!")
        next_step()

    else:
        st.warning("⚠️ Funcionalidades de Análise e Resumo da IA não executadas (Modelos Gemini não configurados ou indisponíveis).")
        # Avança mesmo sem IA se não estiver disponível
        next_step()

    # Nota: As chamadas às funções de IA são cacheada (@st.cache_data),
    # então elas só rodarão a primeira vez que o estado atingir este passo
    # com os inputs mudados. Se o usuário voltar e mudar inputs, o cache invalida
    # e elas rodam novamente. Isso é o comportamento desejado.
    # O `st.rerun()` é implícito no `next_step()`.


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
            st.write(f"**Tamanho Estimado:** {structured_details.get('tamanho', 'Não Informado')}")
            st.write(f"**Profundidade Estimada:** {structured_details.get('profundidade', 'Não Informado')}")
            st.write(f"**Presença de Água/Alagamento:** {structured_details.get('presenca_agua', 'Não Informado')}")
            st.write(f"**Nível de Perigo Aparente:** {structured_details.get('perigo', 'Não Informado')}")
            st.write(f"**Contexto ou Histórico:** {structured_details.get('contexto', 'Não Informado')}")
            st.write(f"**Perigos e Impactos Detalhados:** {', '.join(structured_details.get('perigos_detalhados', ['Nenhum selecionado']))}")
            st.write(f"**Identificadores Visuais Adicionais:** {structured_details.get('identificadores_visuais', 'Não informado')}")
        else:
            st.info("Detalhes estruturados não foram coletados.")

        st.subheader("Observações Adicionais (Texto Livre)")
        st.info(observacoes_adicionais if observacoes_adicionais else "Nenhuma observação adicional fornecida.")

        st.subheader("Foto Anexada")
        if st.session_state.get('uploaded_image'):
             try:
                 img = Image.open(io.BytesIO(st.session_state.uploaded_image))
                 st.image(img, caption="Foto do buraco.", use_column_width=True)
             except Exception as e:
                  st.warning(f"⚠️ Não foi possível exibir a imagem anexada. Erro: {e}")
        else:
            st.info("Nenhuma foto foi anexada a esta denúncia.")


    with st.expander("📍 Localização Exata Processada", expanded=True):
        tipo_loc = localizacao_exata.get('tipo', 'Não informada')
        st.write(f"**Tipo de Coleta/Processamento:** {tipo_loc}")

        if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
            lat = localizacao_exata.get('latitude')
            lon = localizacao_exata.get('longitude')

            if lat is not None and lon is not None:
                 st.write(f"**Coordenadas:** `{lat}, {lon}`")

                 st.subheader("Visualização no Mapa (OpenStreetMap/MapLibre)")
                 try:
                     # Tenta usar st.map se coordenadas válidas (Não precisa de chave Google)
                     map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                     st.map(map_data, zoom=18, use_container_width=True)
                     st.info("ℹ️ O mapa acima é uma representação aproximada usando MapLibre/OpenStreetMap.")
                 except Exception as map_error:
                     st.error(f"❌ Erro ao gerar visualização do mapa OpenStreetMap/MapLibre: {map_error}")

                 st.subheader("Visualização no Google Maps")

                 # Tenta incorporar Google Maps se houver link embed gerado E CHAVE
                 embed_link = localizacao_exata.get('google_embed_link_gerado')
                 if embed_link:
                     try:
                         # Use um placeholder para indicar que está tentando carregar
                         with st.spinner("⏳ Carregando visualização do Google Maps Embed..."):
                              st.components.v1.html(
                                  f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link}" allowfullscreen></iframe>',
                                  height=470, # Altura um pouco maior para incluir borda
                                  scrolling=False
                              )
                         st.info("✅ Visualização do Google Maps Embed carregada (requer API habilitada).")
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
                 if localizacao_exata.get('input_original') and tipo_loc != 'Descrição Manual Detalhada': # Só mostra o input original se não for só descrição
                      st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")


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

    # Exibir análises de IA (se o modelo de texto estava disponível)
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
        st.json(dados_completos)

# --- Rodar a aplicação ---
# A execução principal do script Streamlit é gerenciada pelo próprio Streamlit.
# As funções são chamadas conforme o estado da sessão e as interações do usuário.
# O código abaixo é apenas para garantir que o script seja executado como um app Streamlit.
# Adicionado import io para lidar com uploaded_image bytes.
import io
if __name__ == "__main__":
    # Streamlit cuida do loop principal, não precisamos de uma função main tradicional
    # O código fora das funções e no topo é executado em cada rerun.
    # O fluxo é controlado pelos ifs/elifs baseados em st.session_state.step
    pass # Nada a fazer aqui além do que já está no corpo principal do script
