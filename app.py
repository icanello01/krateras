# -*- coding: utf-8 -*-
"""
Krateras 🚧🚧🚧: O Especialista Robótico de Denúncia de Buracos (v10.1 - Estabilidade Reforçada Final)

Bem-vindo à versão finalizada do Krateras, com estabilidade máxima e geolocalização completa!

Tecnologias: Python, Streamlit, Google Gemini API (Text and Vision), Google Geocoding API, ViaCEP, Google Maps Embed, OpenStreetMap Link.
Objetivo: Coletar dados de denúncias de buracos com detalhes estruturados e observações,
incluir imagem para referência visual, geocodificação, e gerar relatórios
detalhados e priorizados com visualização de mapa.

Vamos juntos consertar essas ruas! Versão final calibrada para precisão e robustez!
"""

import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from image_analyzer import processar_analise_imagem, mostrar_feedback_analise
import re
import json
import pandas as pd
import io
import urllib.parse
import subprocess
import sys
import textwrap

def check_install_dependencies():
    try:
        import google.ai.generativelanguage
    except ImportError:
        st.info("🔧 Instalando dependências necessárias (google-generativeai)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai", "Pillow"])
            st.success("✅ Dependências instaladas com sucesso! Por favor, atualize a página (F5) ou reinicie o app se necessário.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Erro ao instalar dependências: {str(e)}")
            st.stop()

# check_install_dependencies() # Descomente se necessário para o ambiente de deploy

LOGO_URL = "https://raw.githubusercontent.com/icanello01/krateras/refs/heads/main/logo.png"

st.set_page_config(
    page_title="Krateras 🚧🚧🚧 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

col1_logo, col2_logo, col3_logo = st.columns([1, 2, 1])
with col2_logo:
    st.image(LOGO_URL, width=650)

st.markdown("""
<style>
.reportview-container .main .block-container {
    padding-top: 2rem;
    padding-right: 3rem;
    padding-left: 3rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #4A90E2;
}
.stButton>button {
    background-color: #101217; 
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #101217; 
    color: white;
}
.stTextInput, .stNumberInput, .stTextArea, .stRadio, .stSelectbox, .stFileUploader {
    margin-bottom: 10px;
}
.stSpinner > div > div {
    border-top-color: #4A90E2 !important;
}
div[data-testid="stInfo"] {
    border-left: 5px solid #4A90E2 !important;
}
div[data-testid="stWarning"] {
     border-left: 5px solid #F5A623 !important;
}
div[data-testid="stError"] {
     border-left: 5px solid #D0021B !important;
}
div[data-testid="stSuccess"] {
     border-left: 5px solid #7ED321 !important;
}
.streamlit-expanderHeader {
    font-size: 1.1em !important;
    font-weight: bold !important;
    color: #4A90E2 !important;
}
div[data-testid="stExpander"] div[role="button"] + div {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'denuncia_completa' not in st.session_state:
    st.session_state.denuncia_completa = {}
if 'api_keys_loaded' not in st.session_state:
    st.session_state.api_keys_loaded = False
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = None
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    gemini_key = st.secrets.get('GOOGLE_API_KEY')
    geocoding_key = st.secrets.get('geocoding_api_key')
    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado. Funcionalidades de IA (Gemini Text e Análise de Imagem) estarão desabilitadas ou limitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado. Geocodificação e mapa Google Embed estarão desabilitados.")
        st.info("ℹ️ Configure em `.streamlit/secrets.toml`:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```")
    return gemini_key, geocoding_key

@st.cache_resource
def init_gemini_text_model(api_key: Optional[str]) -> Optional[genai.GenerativeModel]:
    if not api_key:
        st.error("❌ ERRO: Chave de API Gemini não fornecida.")
        return None
    try:
        genai.configure(api_key=api_key)
        available_models_info = list(genai.list_models())
        text_generation_models = [m for m in available_models_info if 'generateContent' in m.supported_generation_methods]
        text_model_obj: Optional[genai.GenerativeModel] = None
        preferred_text_names = ['gemini-1.5-flash-latest', 'gemini-1.0-pro-latest', 'gemini-pro']
        selected_model_name = None
        for name_suffix in preferred_text_names:
            found_model_info = next((m for m in text_generation_models if m.name.endswith(name_suffix)), None)
            if found_model_info:
                text_model_obj = genai.GenerativeModel(found_model_info.name)
                selected_model_name = found_model_info.name.replace('models/', '')
                st.success(f"✅ Modelo de Texto Gemini selecionado: '{selected_model_name}'.")
                break
        if not text_model_obj:
            if text_generation_models:
                fallback_model_info = text_generation_models[0]
                text_model_obj = genai.GenerativeModel(fallback_model_info.name)
                selected_model_name = fallback_model_info.name.replace('models/', '')
                st.warning(f"⚠️ Modelos preferenciais não encontrados. Usando fallback: '{selected_model_name}'.")
            else:
                 st.error("❌ ERRO: Nenhum modelo de texto Gemini compatível encontrado.")
                 return None
        return text_model_obj
    except Exception as e:
        st.error(f"❌ ERRO: Falha na inicialização do modelo de texto Gemini.")
        st.exception(e)
        return None

def buscar_cep_uncached(cep: str) -> Dict[str, Any]:
    cep_limpo = cep.replace("-", "").replace(".", "").strip()
    if len(cep_limpo) != 8 or not cep_limpo.isdigit():
        return {"erro": "Formato de CEP inválido."}
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'erro' in data and data['erro'] is True:
            return {"erro": f"CEP '{cep_limpo}' não encontrado."}
        if not data.get('logradouro') or not data.get('localidade') or not data.get('uf'):
             return {"erro": f"CEP '{cep_limpo}' encontrado, mas dados incompletos."}
        return data
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite ao buscar CEP '{cep_limpo}'."}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro de comunicação com ViaCEP: {e}."}
    except Exception as e:
         return {"erro": f"Erro inesperado ao buscar CEP '{cep_limpo}': {e}."}

def geocodificar_endereco_uncached(rua: str, numero: str, cidade: str, estado: str, api_key: str) -> Dict[str, Any]:
    if not api_key: return {"erro": "Chave API Geocodificação não fornecida."}
    if not rua or not numero or not cidade or not estado:
         return {"erro": "Dados de endereço insuficientes."}
    address = f"{rua}, {numero}, {cidade}, {estado}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] != 'OK':
            status = data.get('status', 'DESCONHECIDO')
            error_msg = data.get('error_message', 'Sem mensagem.')
            if status == 'ZERO_RESULTS': error_msg = "Nenhum local exato encontrado."
            elif status in ['OVER_DAILY_LIMIT', 'OVER_QUERY_LIMIT']: error_msg = "Limite de uso da API Geocoding excedido."
            elif status == 'REQUEST_DENIED': error_msg = "Requisição à API Geocoding negada."
            elif status == 'INVALID_REQUEST': error_msg = "Requisição inválida."
            elif status == 'UNKNOWN_ERROR': error_msg = "Erro desconhecido na API Geocoding."
            else: error_msg = f"Status API: {status}. {error_msg}"
            return {"erro": f"Geocodificação falhou. {error_msg}"}
        if not data['results']: return {"erro": "Geocodificação falhou. Nenhum local encontrado."}
        location = data['results'][0]['geometry']['location']
        lat, lng = location['lat'], location['lng']
        formatted_address = data['results'][0].get('formatted_address', address)
        return {
            "latitude": lat, "longitude": lng,
            "endereco_formatado_api": formatted_address,
            "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
            "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"
        }
    except requests.exceptions.Timeout: return {"erro": f"Tempo limite ao geocodificar: {address}"}
    except requests.exceptions.RequestException as e: return {"erro": f"Erro de comunicação (Geocodificação): {e}"}
    except Exception as e: return {"erro": f"Erro inesperado (Geocodificação): {e}"}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

@st.cache_data(show_spinner="🧠 Analisando características e observações com IA Gemini...")
def analisar_caracteristicas_e_observacoes_gemini(_caracteristicas: Dict[str, Any], _observacoes: str, _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"insights": "🤖 Análise de descrição IA indisponível (Motor Gemini Text offline)."}
    caracteristicas_formatadas = []
    for key, value in _caracteristicas.items():
        if isinstance(value, list):
            # Filtra 'Selecione' e itens vazios da lista antes de juntar
            valid_items = [item for item in value if item and item != 'Selecione']
            caracteristicas_formatadas.append(f"- {key}: {', '.join(valid_items) if valid_items else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto = "\n".join(caracteristicas_formatadas)
    observacoes_texto = _observacoes.strip() if _observacoes else "Nenhuma observação adicional fornecida."

    prompt = textwrap.dedent(f"""
        Analise as seguintes características estruturadas e observações adicionais de uma denúncia de buraco.
        Seu objetivo é consolidar estas informações e extrair insights CRUCIAIS para um sistema de denúncias de reparo público.
        Formate a saída como um texto claro, usando marcadores (-) ou títulos para cada categoria.
        Se uma categoria NÃO PUDER ser claramente mencionada ou inferida COM ALTA CONFIANÇA a partir dos dados, indique explicitamente "Não especificado/inferido nos dados". Seja honesto sobre o que PODE ser extraído.

        Características Estruturadas Fornecidas pelo Denunciante:
        {caracteristicas_texto}

        Observações Adicionais do Denunciante:
        "{observacoes_texto}"

        Categorias para Extrair/Inferir dos Dados Fornecidos:
        - Severidade/Tamanho Estimado (Consolidado dos dados): [Use o valor estruturado e adicione nuances das observações se houverem.]
        - Profundidade Estimada (Consolidado dos dados): [Use o valor estruturado e adicione nuances das observações se houverem.]
        - Presença de Água/Alagamento (Consolidado dos dados): [Use o valor estruturado e adicione detalhes das observações se houverem.]
        - Tráfego Estimado na Via (Consolidado dos dados): [Use o valor estruturado.]
        - Contexto da Via (Consolidado dos dados): [Liste os valores estruturados.]
        - Perigos Potenciais e Impactos Mencionados (Extraído das Observações): [Liste riscos específicos citados ou implicados nas *observações* (ex: risco de acidente de carro/moto/bike, perigo para pedestres, causa danos a veículos - pneu furado, suspensão, roda -, dificuldade de desviar, risco de queda, perigo à noite/chuva). Foque no que foi *adicionado* nas observações.]
        - Contexto Adicional Relevante do Local/Histórico (Extraído das Observações): [Problema recorrente/antigo/novo *mencionado nas observações*, perto de local importante (se não coberto pelo 'Contexto da Via'), pouca iluminação *mencionada nas observações*.]
        - Sugestões de Ação/Recursos Mencionados pelo Denunciante: [Se o usuário sugere o que fazer (tapa-buraco, recapeamento, sinalizar) ou causas percebidas *mencionadas nas observações*.]
        - Identificadores Visuais Adicionais (se descritos nas Observações): [Coisas únicas próximas que ajudam a achar o buraco (poste X, árvore Y, em frente a Z), *se mencionadas nas observações*.]
        - Palavras-chave Principais: [Liste 3-7 palavras-chave que capturem a essência da denúncia a partir de *todos* os dados de entrada.]

        Formate a resposta de forma limpa e estruturada.
    """)
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not response.parts:
            block_reason = response.prompt_feedback.block_reason.name if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason else "Não bloqueado/sem conteúdo"
            finish_reason = response.candidates[0].finish_reason.name if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason') else "Não disponível"
            return {"insights": f"❌ Análise de características retornou sem conteúdo. Bloqueio: {block_reason}. Finalização: {finish_reason}."}
        return {"insights": response.text.strip()}
    except Exception as e: return {"insights": f"❌ Erro ao analisar características com IA: {e}"}

@st.cache_data(show_spinner="🧠 Calculando Prioridade Robótica...")
def categorizar_urgencia_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"urgencia_ia": "🤖 Sugestão de urgência IA indisponível (Motor Gemini Text offline)."}
    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia_result.get('insights', 'Análise de insights não disponível.')
    localizacao_exata = _dados_denuncia.get('localizacao_exata_processada', {})
    tipo_loc = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')
    loc_contexto = f"Localização: Tipo: {tipo_loc}."
    if input_original_loc != 'Não informado.': loc_contexto += f" Detalhes originais: '{input_original_loc}'."
    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
        loc_contexto += f" Coords: {localizacao_exata.get('latitude')}, {localizacao_exata.get('longitude')}. Link: {localizacao_exata.get('google_maps_link_gerado', 'N/A')}."
    
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            valid_items = [item for item in value if item and item != 'Selecione']
            caracteristicas_formatadas.append(f"- {key}: {', '.join(valid_items) if valid_items else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = textwrap.dedent(f"""
        Com base nos dados da denúncia (características, observações) e insights, sugira a MELHOR categoria de urgência.
        Categorias: Urgência Baixa, Urgência Média, Urgência Alta, Urgência Imediata/Crítica.

        Dados da Denúncia:
        Localização Básica: Rua {(_dados_denuncia.get('buraco', {}).get('endereco', {})).get('rua', 'N/I')}, Nº Próximo: {(_dados_denuncia.get('buraco', {})).get('numero_proximo', 'N/I')}. Cidade: {(_dados_denuncia.get('buraco', {}).get('endereco', {})).get('cidade_buraco', 'N/I')}, Estado: {(_dados_denuncia.get('buraco', {}).get('endereco', {})).get('estado_buraco', 'N/I')}.
        {loc_contexto}
        Características Estruturadas:
        {caracteristicas_texto_prompt}
        Observações: "{observacoes}"
        Insights da Análise de Texto:
        {insights_texto}

        Qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma JUSTIFICATIVA breve (máx. 2 frases).
        Formato:
        Categoria Sugerida: [Categoria Escolhida]
        Justificativa: [Justificativa Breve]
    """)
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not response.parts:
            block_reason = response.prompt_feedback.block_reason.name if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason else "Não bloqueado/sem conteúdo"
            finish_reason = response.candidates[0].finish_reason.name if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason') else "Não disponível"
            return {"urgencia_ia": f"❌ Sugestão de urgência bloqueada ou sem conteúdo. Bloqueio: {block_reason}. Finalização: {finish_reason}."}
        return {"urgencia_ia": response.text.strip()}
    except Exception as e: return {"urgencia_ia": f"❌ Erro ao sugerir urgência com IA: {e}"}

@st.cache_data(show_spinner="🧠 IA pensando em causas e ações...")
def sugerir_causa_e_acao_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação IA indisponíveis (Motor Gemini Text offline)."}
    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia_result.get('insights', 'Análise de insights não disponível.')
    
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            valid_items = [item for item in value if item and item != 'Selecione']
            caracteristicas_formatadas.append(f"- {key}: {', '.join(valid_items) if valid_items else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)

    prompt = textwrap.dedent(f"""
        Com base nos dados (características, observações) e insights, sugira:
        1. PÓSSIVEIS CAUSAS para este buraco.
        2. TIPOS DE AÇÃO ou REPARO adequados.
        Se os dados não derem pistas, indique "Não especificado/inferido nos dados".

        Informações da Denúncia:
        Características Estruturadas:
        {caracteristicas_texto_prompt}
        Observações: "{observacoes}"
        Insights da Análise de Texto:
        {insights_texto}

        Formato de saída:
        Possíveis Causas Sugeridas: [Lista de causas ou 'Não especificado/inferido nos dados']
        Sugestões de Ação/Reparo Sugeridas: [Lista de ações ou 'Não especificado/inferido nos dados']
    """)
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not response.parts:
            block_reason = response.prompt_feedback.block_reason.name if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason else "Não bloqueado/sem conteúdo"
            finish_reason = response.candidates[0].finish_reason.name if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason') else "Não disponível"
            return {"sugestao_acao_ia": f"❌ Sugestão de causa/ação bloqueada ou sem conteúdo. Bloqueio: {block_reason}. Finalização: {finish_reason}."}
        return {"sugestao_acao_ia": response.text.strip()}
    except Exception as e: return {"sugestao_acao_ia": f"❌ Erro ao sugerir causa/ação com IA: {e}"}

def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _insights_ia_result: Dict[str, Any], _urgencia_ia_result: Dict[str, Any], _sugestao_acao_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"resumo_ia": "🤖 Resumo inteligente IA indisponível (Motor Gemini Text offline)."}
    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    caracteristicas = buraco.get('caracteristicas_estruturadas', {})
    observacoes = buraco.get('observacoes_adicionais', 'N/A.')
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    insights_texto = _insights_ia_result.get('insights', 'N/A.')
    urgencia_ia_text = _urgencia_ia_result.get('urgencia_ia', 'N/A.')
    sugestao_acao_ia_text = (_sugestao_acao_ia_result or {}).get('sugestao_acao_ia', 'N/A.')
    tipo_loc_processada = localizacao_exata.get('tipo', 'N/I')
    input_original_loc = localizacao_exata.get('input_original', 'N/I.')
    motivo_falha_geo_resumo = localizacao_exata.get('motivo_falha_geocodificacao_anterior')
    loc_info_resumo = f"Localização: Tipo: {tipo_loc_processada}."
    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         tipo_display = tipo_loc_processada.replace(' (API)', '').replace(' (Manual)', '').replace('Fornecidas/Extraídas', 'Manual')
         loc_info_resumo = f"Localização Exata: Coords {localizacao_exata.get('latitude')}, {localizacao_exata.get('longitude')} (Via: {tipo_display}). Link: {localizacao_exata.get('google_maps_link_gerado', 'N/A')}."
    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização via descrição manual: '{localizacao_exata.get('descricao_manual', 'N/I')}'."
    if input_original_loc != 'N/I.': loc_info_resumo += f" (Input original: '{input_original_loc}')"
    if motivo_falha_geo_resumo: loc_info_resumo += f" (Nota: {motivo_falha_geo_resumo})"
    
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            valid_items = [item for item in value if item and item != 'Selecione']
            caracteristicas_formatadas.append(f"- {key}: {', '.join(valid_items) if valid_items else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)

    data_hora = _dados_denuncia_completa.get('metadata', {}).get('data_hora_utc', 'N/R')

    prompt = textwrap.dedent(f"""
        Gere um resumo narrativo conciso (máx. 10-12 frases) para a denúncia de buraco. Formal e objetivo.
        Inclua: Denunciante, localização (rua, ref, bairro, cidade, estado, CEP), localização EXATA processada, lado da rua, características, observações, pontos da Análise de Texto, SUGESTÃO de Urgência e Justificativa, SUGESTÕES de CAUSAS e AÇÃO.

        Dados da Denúncia:
        Denunciante: {denunciante.get('nome', 'N/I')}, de {denunciante.get('cidade_residencia', 'N/I')}.
        Endereço: Rua {endereco.get('rua', 'N/I')}, Nº Próximo: {buraco.get('numero_proximo', 'N/I')}. Bairro: {endereco.get('bairro', 'N/I')}. Cidade: {endereco.get('cidade_buraco', 'N/I')}, Estado: {endereco.get('estado_buraco', 'N/I')}. CEP: {buraco.get('cep_informado', 'N/I')}.
        Lado da Rua: {buraco.get('lado_rua', 'N/I')}.
        Localização Exata: {loc_info_resumo}
        Características:
        {caracteristicas_texto_prompt}
        Observações: "{observacoes}"
        Insights da Análise de Texto:
        {insights_texto}
        Sugestão de Urgência pela IA:
        {urgencia_ia_text}
        Sugestões de Causa e Ação pela IA:
        {sugestao_acao_ia_text}

        Gere o resumo em português. Comece com "Relatório Krateras: Denúncia de buraco..."
    """)
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not response.parts:
            block_reason = response.prompt_feedback.block_reason.name if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason else "Não bloqueado/sem conteúdo"
            finish_reason = response.candidates[0].finish_reason.name if hasattr(response, 'candidates') and response.candidates and hasattr(response.candidates[0], 'finish_reason') else "Não disponível"
            return {"resumo_ia": f"❌ Geração de resumo bloqueada ou sem conteúdo. Bloqueio: {block_reason}. Finalização: {finish_reason}."}
        return {"resumo_ia": response.text.strip()}
    except Exception as e: return {"resumo_ia": f"❌ Erro ao gerar resumo com IA: {e}"}

def next_step():
    steps = ['start', 'collect_denunciante', 'collect_address', 'collect_buraco_details_and_location', 'processing_ia', 'show_report']
    try:
        current_index = steps.index(st.session_state.step)
        if current_index < len(steps) - 1:
            st.session_state.step = steps[current_index + 1]
            st.rerun()
    except ValueError: st.session_state.step = steps[0]; st.rerun()

def prev_step():
    steps = ['start', 'collect_denunciante', 'collect_address', 'collect_buraco_details_and_location', 'processing_ia', 'show_report']
    try:
        current_index = steps.index(st.session_state.step)
        if current_index > 0:
             st.session_state.step = steps[current_index - 1]
             st.rerun()
    except ValueError: st.session_state.step = steps[0]; st.rerun()

st.subheader("O Especialista Robótico de Denúncia de Buracos")

if st.session_state.step == 'start':
    st.write("""
    Olá! Krateras v10.1 com **Estabilidade Reforçada Final**! Sua missão: denunciar buracos.
    Nesta versão: fluxo otimizado, imagem no relatório, geolocalização com mapas Google e OpenStreetMap.
    Usamos IA (Google Gemini Text e Vision) e APIs de localização (Google Geocoding, ViaCEP).
    """)
    if st.button("Iniciar Missão Denúncia!"):
        st.session_state.denuncia_completa = {"metadata": {"data_hora_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}}
        st.session_state.update({
            'cep_input_consolidated': '', 'cep_error_consolidated': False,
            'cep_success_message': '', 'cep_error_message': ''
        })
        if 'buraco' in st.session_state: del st.session_state.buraco
        gemini_api_key, geocoding_api_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_api_key
        st.session_state.gemini_model = init_gemini_text_model(gemini_api_key)
        st.session_state.api_keys_loaded = True
        next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína ---")
    with st.form("form_denunciante"):
        current_denunciante_data = st.session_state.denuncia_completa.get('denunciante', {})
        nome = st.text_input("Nome completo:", value=current_denunciante_data.get('nome', ''), key='nome_denunciante')
        idade_value = current_denunciante_data.get('idade')
        idade = st.number_input("Idade (opcional):", min_value=0, max_value=120, value=idade_value, format="%d", help="Deixe em branco ou 0 se não informar.", key='idade_denunciante_input')
        cidade_residencia = st.text_input("Sua cidade de residência:", value=current_denunciante_data.get('cidade_residencia', ''), key='cidade_residencia_denunciante')
        if st.form_submit_button("Avançar"):
            if not nome or not cidade_residencia: st.error("❗ Nome e Cidade de residência são obrigatórios.")
            else:
                st.session_state.denuncia_completa['denunciante'] = {
                    "nome": nome.strip(),
                    "idade": idade if idade and idade > 0 else None,
                    "cidade_residencia": cidade_residencia.strip()
                }
                st.success(f"Olá, {nome}! Dados coletados.")
                next_step()
    st.button("Voltar", on_click=prev_step)

elif st.session_state.step == 'collect_address':
    st.header("--- 🚧 Endereço Base do Buraco ---")
    if 'buraco' not in st.session_state: st.session_state.buraco = {'endereco': {}}
    if 'endereco' not in st.session_state.buraco: st.session_state.buraco['endereco'] = {}
    endereco_atual = st.session_state.buraco.get('endereco', {})
    if 'cep_input_consolidated' not in st.session_state: st.session_state.cep_input_consolidated = endereco_atual.get('cep_informado', '')
    if 'cep_error_consolidated' not in st.session_state: st.session_state.cep_error_consolidated = False
    if 'cep_success_message' not in st.session_state: st.session_state.cep_success_message = ''
    if 'cep_error_message' not in st.session_state: st.session_state.cep_error_message = ''

    st.subheader("Opção 1: Buscar por CEP")
    col1_cep, col2_cep = st.columns([3,1])
    with col1_cep:
         cep_input_val = st.text_input("CEP (só números):", max_chars=8, key='cep_field_key', value=st.session_state.cep_input_consolidated)
         if cep_input_val != st.session_state.cep_input_consolidated:
             st.session_state.cep_input_consolidated = cep_input_val
    with col2_cep:
         if st.button("Buscar CEP", key='buscar_cep_btn_key'):
             st.session_state.cep_success_message = ''; st.session_state.cep_error_message = ''
             if not st.session_state.cep_input_consolidated:
                 st.session_state.cep_error_consolidated = True; st.session_state.cep_error_message = "❗ Digite um CEP."
             else:
                 with st.spinner("⏳ Buscando CEP..."):
                    dados_cep_result = buscar_cep_uncached(st.session_state.cep_input_consolidated)
                 if 'erro' in dados_cep_result:
                     st.session_state.cep_error_consolidated = True; st.session_state.cep_error_message = f"❌ {dados_cep_result['erro']}"
                 else:
                     st.session_state.cep_error_consolidated = False; st.session_state.cep_success_message = "✅ Endereço Encontrado! Confirme/corrija abaixo."
                     st.session_state.buraco['endereco'].update({
                         'rua': dados_cep_result.get('logradouro', st.session_state.buraco['endereco'].get('rua', '')),
                         'bairro': dados_cep_result.get('bairro', st.session_state.buraco['endereco'].get('bairro', '')),
                         'cidade_buraco': dados_cep_result.get('localidade', st.session_state.buraco['endereco'].get('cidade_buraco', '')),
                         'estado_buraco': dados_cep_result.get('uf', st.session_state.buraco['endereco'].get('estado_buraco', ''))
                     })
                     st.session_state.buraco['cep_informado'] = st.session_state.cep_input_consolidated
             st.rerun()
    if st.session_state.cep_success_message: st.success(st.session_state.cep_success_message)
    if st.session_state.cep_error_message: st.error(st.session_state.cep_error_message)

    st.markdown("---"); st.subheader("Opção 2: Digitar Endereço Manualmente")
    with st.form("form_manual_address"):
        rua_manual = st.text_input("Rua:", value=st.session_state.buraco.get('endereco', {}).get('rua', ''), key='rua_manual_key')
        bairro_manual = st.text_input("Bairro (opcional):", value=st.session_state.buraco.get('endereco', {}).get('bairro', ''), key='bairro_manual_key')
        cidade_manual = st.text_input("Cidade:", value=st.session_state.buraco.get('endereco', {}).get('cidade_buraco', ''), key='cidade_manual_key')
        estado_manual = st.text_input("Estado (UF):", value=st.session_state.buraco.get('endereco', {}).get('estado_buraco', ''), max_chars=2, key='estado_manual_key')
        if st.form_submit_button("Confirmar Endereço Base e Avançar"):
            if not rua_manual or not cidade_manual or not estado_manual: st.error("❗ Rua, Cidade e Estado são obrigatórios.")
            else:
                st.session_state.buraco['endereco'] = {
                    'rua': rua_manual.strip(), 'bairro': bairro_manual.strip(),
                    'cidade_buraco': cidade_manual.strip(), 'estado_buraco': estado_manual.strip().upper()
                }
                if st.session_state.cep_input_consolidated and 'cep_informado' not in st.session_state.buraco:
                     st.session_state.buraco['cep_informado'] = st.session_state.cep_input_consolidated
                st.session_state.denuncia_completa['buraco'] = st.session_state.buraco.copy()
                if 'buraco' in st.session_state: del st.session_state.buraco # Limpa estado temporário
                next_step()
    st.button("Voltar", on_click=prev_step)

elif st.session_state.step == 'collect_buraco_details_and_location':
    st.header("--- 🚧 Detalhes Finais e Localização Exata ---")
    buraco_data_current = st.session_state.denuncia_completa.get('buraco', {})
    endereco_basico = buraco_data_current.get('endereco', {})
    if not endereco_basico or not endereco_basico.get('rua') or not endereco_basico.get('cidade_buraco') or not endereco_basico.get('estado_buraco'):
         st.error("❗ Erro: Endereço base faltando. Volte para a etapa anterior.")
         if st.button("Voltar", key="voltar_details_erro_key"): prev_step()
         st.stop()
    st.write(f"Endereço Base: Rua **{endereco_basico.get('rua', 'N/I')}**, Cidade: **{endereco_basico.get('cidade_buraco', 'N/I')}** - **{endereco_basico.get('estado_buraco', 'N/I')}**")
    if endereco_basico.get('bairro'): st.write(f"Bairro: **{endereco_basico.get('bairro')}**")
    if buraco_data_current.get('cep_informado'): st.write(f"CEP: **{buraco_data_current.get('cep_informado')}**")
    st.markdown("---")
    with st.form("form_buraco_details_location"):
        st.subheader("📋 Características do Buraco")
        col1_d, col2_d = st.columns(2)
        with col1_d:
             tamanho = st.selectbox("Tamanho:", ['Selecione', 'Pequeno (cabe um pneu)', 'Médio (maior que um pneu, mas cabe em uma faixa)', 'Grande (ocupa mais de uma faixa, difícil desviar)', 'Enorme (cratera, impede passagem)', 'Crítico (buraco na pista principal, risco iminente de acidente grave)'], key='t_b')
             perigo = st.selectbox("Perigo:", ['Selecione', 'Baixo (principalmente estético, risco mínimo)', 'Médio (risco de dano leve ao pneu ou suspensão)', 'Alto (risco de acidente/dano sério para carro, alto risco para moto/bike/pedestre)', 'Altíssimo (risco grave e iminente de acidente, histórico de acidentes no local)'], key='p_b')
             profundidade = st.selectbox("Profundidade:", ['Selecione', 'Raso (menos de 5 cm)', 'Médio (5-15 cm)', 'Fundo (15-30 cm)', 'Muito Fundo (mais de 30 cm / "engole" um pneu)'], key='pr_b')
        with col2_d:
             agua = st.selectbox("Água/Alagamento:", ['Selecione', 'Seco', 'Acumula pouca água', 'Acumula muita água (vira piscina)', 'Problema de drenagem visível (jato de água, nascente)'], key='a_b')
             trafego_key_form = 'traf_b_key' 
             trafego = st.selectbox("Tráfego na Via:", ['Selecione', 'Muito Baixo (rua local sem saída)', 'Baixo (rua residencial calma)', 'Médio (rua residencial/comercial com algum fluxo)', 'Alto (avenida movimentada, via de acesso)', 'Muito Alto (via expressa, anel viário)'], key=trafego_key_form)
             contexto_via = st.multiselect("Contexto da Via:", ['Reta', 'Curva acentuada', 'Cruzamento/Esquina', 'Subida', 'Descida', 'Próximo a faixa de pedestre', 'Próximo a semáforo/lombada', 'Área escolar/Universitária', 'Área hospitalar/Saúde', 'Área comercial intensa', 'Via de acesso principal', 'Via secundária', 'Próximo a ponto de ônibus/transporte público', 'Próximo a ciclovia/ciclofaixa'], key='c_b')
        st.subheader("✍️ Localização Exata e Outros Detalhes")
        num_prox_key = 'num_prox_b_key'
        lado_rua_key = 'lado_rua_b_key'
        loc_man_key = 'loc_man_b_key'
        obs_key = 'obs_b_key'
        numero_proximo = st.text_input("Nº próximo ou referência (ESSENCIAL!):", key=num_prox_key)
        lado_rua = st.text_input("Lado da rua:", key=lado_rua_key)
        st.markdown("""<p style="font-weight: bold;">Localização EXATA (opcional, mas recomendado):</p>
        <p>COPIE COORDENADAS (Lat,Long) ou LINK do Google Maps. Ou DESCRIÇÃO DETALHADA.</p>""", unsafe_allow_html=True)
        localizacao_manual_input = st.text_input("Coords (Lat,Long), Link Maps, OU Descrição Detalhada:", key=loc_man_key)
        st.subheader("📷 Foto do Buraco (Opcional)")
        uploaded_image = st.file_uploader("Carregar Imagem:", type=['jpg', 'jpeg', 'png', 'webp'], key='img_b_key')
        if uploaded_image: st.info(f"Imagem '{uploaded_image.name}' carregada.")
        st.subheader("📝 Observações Adicionais")
        observacoes_adicionais = st.text_area("Suas observações:", key=obs_key)

        if st.form_submit_button("Enviar Denúncia para Análise Robótica!"):
            req_selects = {'t_b': 'Tamanho', 'p_b': 'Perigo', 'pr_b': 'Profundidade', 'a_b': 'Água/Alagamento', trafego_key_form: 'Tráfego na Via'}
            missing = [label for key, label in req_selects.items() if st.session_state.get(key) == 'Selecione']
            if not st.session_state[num_prox_key] or not st.session_state[lado_rua_key] or not st.session_state[obs_key]:
                 st.error("❗ Nº próximo/referência, Lado da rua e Observações são obrigatórios.")
            elif missing: st.error(f"❗ Selecione uma opção para: {', '.join(missing)}.")
            else:
                if 'buraco' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['buraco'] = {}
                st.session_state.denuncia_completa['buraco'].update({
                    'numero_proximo': st.session_state[num_prox_key].strip(),
                    'lado_rua': st.session_state[lado_rua_key].strip(),
                    'caracteristicas_estruturadas': {
                         'Tamanho Estimado': st.session_state.t_b, 'Perigo Estimado': st.session_state.p_b,
                         'Profundidade Estimada': st.session_state.pr_b, 'Presença de Água/Alagamento': st.session_state.a_b,
                         'Tráfego Estimado na Via': st.session_state[trafego_key_form],
                         'Contexto da Via': st.session_state.c_b if st.session_state.c_b else []
                    },
                    'observacoes_adicionais': st.session_state[obs_key].strip()
                })
                st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = None
                if uploaded_image:
                    try:
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {
                            "filename": uploaded_image.name, "type": uploaded_image.type,
                            "bytes": uploaded_image.getvalue()
                        }
                    except Exception as e:
                        st.error(f"❌ Erro ao processar imagem: {e}.")
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {"erro": f"Erro: {e}"}

                st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"}
                tentou_geo, geo_ok_coords, geo_res = False, False, {}
                rua_b, cid_b, est_b = endereco_basico.get('rua'), endereco_basico.get('cidade_buraco'), endereco_basico.get('estado_buraco')
                num_ref_geo = st.session_state[num_prox_key].strip()
                tem_dados_geo = (st.session_state.geocoding_api_key and rua_b and num_ref_geo and cid_b and est_b)
                if tem_dados_geo:
                    tentou_geo = True
                    with st.spinner("⏳ Geocodificando..."):
                         geo_res = geocodificar_endereco_uncached(rua_b, num_ref_geo, cid_b, est_b, st.session_state.geocoding_api_key)
                    if 'erro' not in geo_res:
                        geo_ok_coords = True
                        st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                            "tipo": "Geocodificada (API)", "latitude": geo_res['latitude'], "longitude": geo_res['longitude'],
                            "endereco_formatado_api": geo_res.get('endereco_formatado_api', ''),
                            "google_maps_link_gerado": geo_res['google_maps_link_gerado'],
                            "google_embed_link_gerado": geo_res.get('google_embed_link_gerado'),
                            "input_original": num_ref_geo
                        }
                loc_man_val = st.session_state[loc_man_key].strip()
                lat_man, lon_man, tipo_man_proc = None, None, "Descrição Manual Detalhada"
                if loc_man_val:
                     match_coords = re.search(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)', loc_man_val)
                     if match_coords:
                         try:
                             t_lat, t_lon = float(match_coords.group(1)), float(match_coords.group(2))
                             if -90 <= t_lat <= 90 and -180 <= t_lon <= 180:
                                 lat_man, lon_man = t_lat, t_lon
                                 tipo_man_proc = "Coordenadas Fornecidas/Extraídas Manualmente"
                         except ValueError: pass
                     if lat_man is None and loc_man_val.startswith("http"):
                          match_maps_link = re.search(r'(?:/@|/search/\?api=1&query=)(-?\d+\.?\d*),(-?\d+\.?\d*)', loc_man_val)
                          if match_maps_link:
                              try:
                                  t_lat, t_lon = float(match_maps_link.group(1)), float(match_maps_link.group(2))
                                  if -90 <= t_lat <= 90 and -180 <= t_lon <= 180:
                                       lat_man, lon_man = t_lat, t_lon
                                       tipo_man_proc = "Coordenadas Extraídas de Link (Manual)"
                              except ValueError: pass
                     if lat_man is not None and lon_man is not None:
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": tipo_man_proc, "input_original": loc_man_val,
                              "latitude": lat_man, "longitude": lon_man,
                              "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat_man},{lon_man}",
                              "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_man},{lon_man}" if st.session_state.geocoding_api_key else None
                         }
                         geo_ok_coords = True
                     elif loc_man_val and not geo_ok_coords:
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": "Descrição Manual Detalhada", "input_original": loc_man_val, "descricao_manual": loc_man_val
                         }
                final_loc_data = st.session_state.denuncia_completa.get('localizacao_exata_processada', {})
                final_loc_type = final_loc_data.get('tipo')
                if final_loc_type not in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Coordenadas Extraídas de Link (Manual)', 'Geocodificada (API)']:
                     reasons = []
                     if tentou_geo and 'erro' in geo_res: reasons.append(f"Geo Auto Falhou: {geo_res['erro']}")
                     elif not st.session_state.geocoding_api_key: reasons.append("Chave GeoAPI não fornecida.")
                     elif st.session_state.geocoding_api_key and not tem_dados_geo: reasons.append("Dados insuficientes para Geo Auto.")
                     if loc_man_val and not (lat_man and lon_man): reasons.append("Coords não extraídas do input manual.")
                     if reasons: final_loc_data['motivo_falha_geocodificacao_anterior'] = " / ".join(reasons)
                     elif final_loc_type == "Não informada" and not final_loc_data.get('motivo_falha_geocodificacao_anterior'):
                         final_loc_data['motivo_falha_geocodificacao_anterior'] = "Coords não obtidas por nenhum método."
                     st.session_state.denuncia_completa['localizacao_exata_processada'] = final_loc_data
                next_step()
    if st.button("Voltar", on_click=prev_step, key="voltar_details_btn_key"): pass

elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    buraco_data = st.session_state.denuncia_completa.get('buraco', {})
    imagem_data_dict = buraco_data.get('imagem_denuncia')
    caracteristicas = buraco_data.get('caracteristicas_estruturadas', {})
    observacoes = buraco_data.get('observacoes_adicionais', '')
    st.session_state.denuncia_completa['resultado_analise_visual_krateras'] = None
    if imagem_data_dict and 'bytes' in imagem_data_dict:
        st.info("👁️‍🗨️ Iniciando Análise Visual da Imagem...")
        resultado_analise_visual = processar_analise_imagem(imagem_data_dict)
        st.session_state.denuncia_completa['resultado_analise_visual_krateras'] = resultado_analise_visual
        if resultado_analise_visual and resultado_analise_visual.get("status") != "error" and "nivel_severidade" in resultado_analise_visual:
            st.markdown("---"); st.subheader("Feedback Adicional (Análise Visual)")
            mostrar_feedback_analise(resultado_analise_visual["nivel_severidade"])
        elif resultado_analise_visual and resultado_analise_visual.get("status") == "error":
            st.caption(f"Nota: Análise visual da imagem reportou erro (detalhes acima).")
        st.markdown("---")
    else:
        st.info("ℹ️ Nenhuma imagem fornecida, análise visual pulada.")
        st.session_state.denuncia_completa['resultado_analise_visual_krateras'] = {
            "status": "skipped", "analise_visual": "Nenhuma imagem fornecida.",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    fallbacks = {
        'insights_ia': {"insights": "Análise características/observações (IA Texto) não realizada/erro."},
        'urgencia_ia': {"urgencia_ia": "Sugestão urgência (IA Texto) não gerada/erro."},
        'sugestao_acao_ia': {"sugestao_acao_ia": "Sugestões causa/ação (IA Texto) não geradas/erro."},
        'resumo_ia': {"resumo_ia": "Resumo narrativo (IA Texto) não gerado/erro."}
    }
    for key, val in fallbacks.items():
        if key not in st.session_state.denuncia_completa: st.session_state.denuncia_completa[key] = val.copy()

    with st.spinner("Executando análises de IA (Texto)..."):
        st.session_state.denuncia_completa['insights_ia'] = analisar_caracteristicas_e_observacoes_gemini(
            caracteristicas, observacoes, st.session_state.gemini_model)
        st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
            st.session_state.denuncia_completa, st.session_state.denuncia_completa['insights_ia'], st.session_state.gemini_model)
        st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
            st.session_state.denuncia_completa, st.session_state.denuncia_completa['insights_ia'], st.session_state.gemini_model)
        st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
            st.session_state.denuncia_completa, st.session_state.denuncia_completa['insights_ia'],
            st.session_state.denuncia_completa['urgencia_ia'], st.session_state.denuncia_completa['sugestao_acao_ia'],
            st.session_state.gemini_model)
    next_step()

elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊"); st.balloons()
    st.success("✅ MISSÃO CONCLUÍDA! RELATÓRIO GERADO. ✅")
    dados = st.session_state.denuncia_completa
    den, bur, end, carac, obs = dados.get('denunciante',{}), dados.get('buraco',{}), dados.get('buraco',{}).get('endereco',{}), dados.get('buraco',{}).get('caracteristicas_estruturadas',{}), dados.get('buraco',{}).get('observacoes_adicionais','N/A')
    img_data_rep = bur.get('imagem_denuncia')
    loc_exata = dados.get('localizacao_exata_processada',{})
    res_analise_vis_rep = dados.get('resultado_analise_visual_krateras')
    ins_ia, urg_ia, sug_ia, res_ia = dados.get('insights_ia',{}), dados.get('urgencia_ia',{}), dados.get('sugestao_acao_ia',{}), dados.get('resumo_ia',{})
    st.write(f"📅 Data/Hora (UTC): **{dados.get('metadata',{}).get('data_hora_utc','N/R')}**"); st.markdown("---")

    with st.expander("👤 Denunciante", expanded=True):
        st.write(f"**Nome:** {den.get('nome','N/I')}"); st.write(f"**Idade:** {den.get('idade') if den.get('idade') is not None else 'N/I'}")
        st.write(f"**Cidade Residência:** {den.get('cidade_residencia','N/I')}")
    with st.expander("🚧 Endereço do Buraco", expanded=True):
        st.write(f"**Rua:** {end.get('rua','N/I')}"); st.write(f"**Ref/Nº Próximo:** {bur.get('numero_proximo','N/I')}")
        st.write(f"**Bairro:** {end.get('bairro','N/I')}"); st.write(f"**Cidade:** {end.get('cidade_buraco','N/I')}")
        st.write(f"**Estado:** {end.get('estado_buraco','N/I')}"); st.write(f"**CEP:** {bur.get('cep_informado','N/I')}")
        st.write(f"**Lado da Rua:** {bur.get('lado_rua','N/I')}")
    with st.expander("📋 Características e Observações (Denunciante)", expanded=True):
         st.write("**Características:**")
         carac_ex = {}
         if isinstance(carac, dict): # Garantir que carac é um dicionário
            carac_ex = {k:v for k,v in carac.items() if v and v!='Selecione' and (not isinstance(v,list) or any(i for i in v if i and i!='Selecione'))}
         
         if carac_ex:
             for k,v_list in carac_ex.items():
                 if isinstance(v_list, list):
                     valid_v_items = [item for item in v_list if item and item != 'Selecione']
                     if valid_v_items: # Só exibe se houver itens válidos
                        st.write(f"- **{k}:** {', '.join(valid_v_items)}")
                 else: # Não é lista, é um valor único
                    st.write(f"- **{k}:** {v_list}")
         else: st.info("Nenhuma característica significativa selecionada.")
         st.write("**Observações:**"); st.info(obs if obs else 'N/A.')

    with st.expander("📍 Localização Exata Processada", expanded=True):
        tipo_loc_r = loc_exata.get('tipo','N/I'); st.write(f"**Tipo Coleta:** {tipo_loc_r}")
        if tipo_loc_r in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
            lat_r, lon_r = loc_exata.get('latitude'), loc_exata.get('longitude')
            if lat_r is not None and lon_r is not None:
                 st.write(f"**Coords:** `{lat_r}, {lon_r}`"); st.subheader("Visualizações de Mapa")
                 emb_g, link_g = loc_exata.get('google_embed_link_gerado'), loc_exata.get('google_maps_link_gerado')
                 if (emb_g and st.session_state.geocoding_api_key) or link_g:
                     st.markdown("---"); st.write("**Google Maps:**")
                     if emb_g and st.session_state.geocoding_api_key:
                          try: st.components.v1.html(f'<iframe width="100%" height="450" loading="lazy" src="{emb_g}" allowfullscreen></iframe>', height=470)
                          except Exception as e_g: st.error(f"❌ Erro mapa Google: {e_g}")
                     elif not st.session_state.geocoding_api_key and link_g: st.info("Chave GeoAPI não fornecida. Mapa indisponível, só link.")
                     if link_g: st.markdown(f"[Abrir no Google Maps]({link_g})")
                 st.markdown("---"); st.write("**OpenStreetMap:**")
                 
                 # CORREÇÃO APLICADA AQUI
                 delta_o = 0.005 
                 bbox_o = f"{lon_r-delta_o},{lat_r-delta_o},{lon_r+delta_o},{lat_r+delta_o}"
                 # FIM DA CORREÇÃO

                 osm_emb_r = f"https://www.openstreetmap.org/export/embed.html?bbox={urllib.parse.quote(bbox_o)}&layer=mapnik&marker={urllib.parse.quote(f'{lat_r},{lon_r}')}"
                 try: st.components.v1.html(f'<iframe width="100%" height="450" src="{osm_emb_r}" allowfullscreen></iframe>', height=470)
                 except Exception as e_o: st.error(f"❌ Erro mapa OSM: {e_o}")
                 st.markdown(f"[Abrir no OpenStreetMap.org](https://www.openstreetmap.org/?mlat={lat_r}&mlon={lon_r}#map=18/{lat_r}/{lon_r})")
                 st.markdown("---"); st.write("**OpenStreetMap (Simplificado):**")
                 try: st.map(pd.DataFrame({'lat':[lat_r],'lon':[lon_r]}), zoom=17)
                 except Exception as e_stmap: st.error(f"❌ Erro mapa OSM simplificado: {e_stmap}")
                 if loc_exata.get('endereco_formatado_api'): st.write(f"**Endereço Formatado (API):** {loc_exata.get('endereco_formatado_api')}")
                 if loc_exata.get('input_original'): st.write(f"(Input Original Loc. Exata: `{loc_exata.get('input_original', 'N/I')}`)")
        elif tipo_loc_r == 'Descrição Manual Detalhada':
            st.info(loc_exata.get('descricao_manual','N/I')); st.write(f"(Input Original Loc. Exata: `{loc_exata.get('input_original', 'N/I')}`)")
        else: st.warning("Localização exata não coletada (coords/link/descrição).")
        if loc_exata.get('motivo_falha_geocodificacao_anterior'): st.info(f"ℹ️ Nota Coords: {loc_exata.get('motivo_falha_geocodificacao_anterior')}")
    with st.expander("📷 Imagem da Denúncia", expanded=True):
         if img_data_rep and 'bytes' in img_data_rep:
              try: st.image(io.BytesIO(img_data_rep['bytes']), caption=img_data_rep.get('filename','Img Carregada'), use_container_width=True)
              except Exception as e_id: st.error(f"❌ Não foi possível exibir imagem: {e_id}")
         elif img_data_rep and 'erro' in img_data_rep: st.error(f"❌ Erro ao carregar imagem: {img_data_rep.get('erro','N/D')}.")
         else: st.info("ℹ️ Nenhuma imagem carregada.")
    with st.expander("👁️‍🗨️ Resultado da Análise Visual da Imagem (Krateras Image Analyzer)", expanded=True):
        if res_analise_vis_rep:
            status_vis = res_analise_vis_rep.get("status")
            if status_vis == "success":
                st.success("✅ Análise visual da imagem concluída e exibida na etapa de processamento.")
                q_img_rep = res_analise_vis_rep.get("qualidade_imagem",{})
                if q_img_rep and q_img_rep.get("status") is not None:
                    st.write(f"**Qualidade Imagem:** {'Boa' if q_img_rep.get('status') else 'Com problemas'}")
                    if q_img_rep.get('problemas'): st.write(f"Problemas: {', '.join(q_img_rep['problemas'])}")
                ts_vis = res_analise_vis_rep.get("analise_visual_ia",{}).get("timestamp")
                if ts_vis: st.caption(f"Timestamp análise visual (UTC): {ts_vis}")
            elif status_vis == "error": st.error(f"Análise visual falhou: {res_analise_vis_rep.get('analise_visual','Erro N/D')}")
            elif status_vis == "skipped": st.info(f"ℹ️ Análise visual pulada: {res_analise_vis_rep.get('analise_visual','Nenhuma imagem')}")
            else: st.warning("⚠️ Estado da análise visual indeterminado.")
        else: st.warning("⚠️ Dados da análise visual não encontrados.")
    st.markdown("---"); st.subheader("🤖 Análises Robóticas de IA (Google Gemini Text)")
    if st.session_state.gemini_model:
        with st.expander("🧠 Análise Características/Observações (IA Gemini Text)", expanded=True): st.markdown(ins_ia.get('insights','N/A.'))
        with st.expander("🚦 Sugestão de Urgência (IA Gemini Text)", expanded=True): st.markdown(urg_ia.get('urgencia_ia','N/A.'))
        with st.expander("🛠️ Sugestões Causa/Ação (IA Gemini Text)", expanded=True): st.markdown(sug_ia.get('sugestao_acao_ia','N/A.'))
        st.markdown("---"); st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini Text)")
        st.markdown(res_ia.get('resumo_ia','N/A.'))
    else: st.warning("⚠️ Análises e Resumo IA Texto não disponíveis (Chave GOOGLE_API_KEY ou modelo não inicializado).")
    st.markdown("---"); st.write("Esperamos que ajude!")
    if st.button("Iniciar Nova Denúncia", key="nova_den_rep_key"):
        keys_del = [k for k in st.session_state.keys() if k not in ['gemini_model','geocoding_api_key']]
        for k in keys_del: del st.session_state[k]
        st.session_state.step = 'start'; st.rerun()
    with st.expander("🔌 Ver Dados Brutos (JSON)"):
        dados_json = dados.copy()
        if 'buraco' in dados_json and 'imagem_denuncia' in dados_json['buraco']:
             img_d_main = dados_json['buraco'].get('imagem_denuncia')
             if img_d_main and isinstance(img_d_main, dict) and 'bytes' in img_d_main:
                  img_d_copy_main = img_d_main.copy(); img_d_copy_main['bytes'] = f"<omitido {len(img_d_main['bytes'])} bytes>"
                  dados_json['buraco']['imagem_denuncia'] = img_d_copy_main
        st.json(dados_json)

if __name__ == "__main__":
    pass
