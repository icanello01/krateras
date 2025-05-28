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
import urllib.parse # Importado para lidar com URLs

# Image URL provided by the user
LOGO_URL = "https://raw.githubusercontent.com/icanello01/krateras/refs/heads/main/logo.png"


# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Krateras 🚧🚧🚧 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Add the Logo ---
# Use columns to center the image
col1, col2, col3 = st.columns([1, 2, 1]) # Adjust column ratios as needed
with col2: # Place the image in the middle column
    st.image(LOGO_URL, width=650) # Adjust width as needed


# --- Estilos CSS Personalizados (Opcional, para um toque extra) ---
st.markdown("""
<style>
.reportview-container .main .block-container {
    padding-top: 2rem;
    padding-right: 3rem;
    padding-left: 3rem;
    padding-bottom: 2rem;
}
h1, h2, h3 {
    color: #4A90E2; /* Azul Cratera */
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
.css-1aumqxt { /* Estilo para st.info */
    border-left: 5px solid #4A90E2 !important;
}
.css-1r6cdft { /* Estilo para st.warning */
     border-left: 5px solid #F5A623 !important;
}
.css-t9s6qg { /* Estilo para st.error */
     border-left: 5px solid #D0021B !important;
}
.css-1u3jtzg { /* Estilo para st.success */
     border-left: 5px solid #7ED321 !important;
}
/* Ajustes para expanders */
.streamlit-expanderHeader {
    font-size: 1.1em !important;
    font-weight: bold !important;
    color: #4A90E2 !important;
}
/* Classe para ajustar o padding interno dos expanders */
/* As classes exatas podem variar, inspecione o elemento se precisar refinar */
.st-emotion-cache-s5fjsg, .st-emotion-cache-1njf35f {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# --- Inicialização de Estado da Sessão ---
# Gerencia o fluxo da aplicação web
if 'step' not in st.session_state:
    st.session_state.step = 'start'
if 'denuncia_completa' not in st.session_state:
    st.session_state.denuncia_completa = {}
if 'api_keys_loaded' not in st.session_state:
    st.session_state.api_keys_loaded = False
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = None
if 'gemini_vision_model' not in st.session_state:
    st.session_state.gemini_vision_model = None
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None

# --- 🔑 Gerenciamento de Chaves Secretas (Streamlit Secrets) ---
# Utiliza o .streamlit/secrets.toml para carregar chaves

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    """
    Tenta obter as chaves de API do Google Gemini (Text) e Google Maps Geocoding de Streamlit Secrets.
    Retorna None se não encontradas.
    """
    gemini_key = st.secrets.get('GOOGLE_API_KEY')
    geocoding_key = st.secrets.get('geocoding_api_key')

    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA (Gemini Text) estarão desabilitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática e mapa Google Embed estarão desabilitados.")
        st.info("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\nLembre-se que as APIs Geocoding e Gemini podem gerar custos. Ative-as no Google Cloud e verifique sua configuração de cobrança.")

    return gemini_key, geocoding_key

# --- Inicializar APIs (Cacheado para performance) ---

@st.cache_resource
def init_gemini_text_model(api_key: Optional[str]) -> Tuple[Optional[genai.GenerativeModel], Optional[genai.GenerativeModel]]:
    """Inicializa o modelo Google Gemini (Texto APENAS) com cache."""
    if not api_key:
        st.error("❌ ERRO na Fábrica de Modelos: Chave de API Gemini não fornecida.")
        return None, None
    try:
        genai.configure(api_key=api_key)
        st.success("✅ Conexão com API Google Gemini estabelecida.")

        available_models = list(genai.list_models())
        text_models = [m for m in available_models if 'generateContent' in m.supported_generation_methods]

        # Selecionar modelo de Texto preferencial
        text_model_obj: Optional[genai.GenerativeModel] = None
        preferred_text_names = ['gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        for name in preferred_text_names:
            # Verifica se o nome preferencial está na lista de modelos de texto disponíveis
            found_model = next((m for m in text_models if m.name.endswith(name)), None)
            if found_model:
                text_model_obj = genai.GenerativeModel(found_model.name)
                st.success(f"✅ Modelo de Texto Gemini selecionado: '{found_model.name.replace('models/', '')}'. A IA Textual está online!")
                break
        if not text_model_obj:
            if text_models:
                # Fallback para o primeiro modelo de texto disponível
                text_model_obj = genai.GenerativeModel(text_models[0].name)
                st.warning(f"⚠️ AVISO: Modelos de texto Gemini preferenciais não encontrados. Usando fallback: '{text_models[0].name.replace('models/', '')}'.")
            else:
                 st.error("❌ ERRO na Fábrica de Modelos: Nenhum modelo de texto Gemini compatível encontrado na sua conta.")
        vision_model_obj = None
        if text_model_obj and 'gemini-pro-vision' in [m.name for m in available_models]:
            vision_model_obj = genai.GenerativeModel('gemini-pro-vision')
            st.success("✅ Modelo de Visão Gemini (gemini-pro-vision) inicializado com sucesso!")
        return text_model_obj, vision_model_obj

    except Exception as e:
        st.error(f"❌ ERRO no Painel de Controle Gemini: Falha na inicialização dos modelos Google Gemini. Verifique sua chave e status do serviço.")
        st.exception(e)
        return None, None


# --- Funções de API Call ---
# Funções de API Call não são @st.cache_data para permitir novas tentativas dentro da mesma sessão
# sem esperar o cache expirar, se o usuário tentar corrigir um CEP ou endereço.

def buscar_cep_uncached(cep: str) -> Dict[str, Any]:
    """Consulta a API ViaCEP para obter dados de endereço com tratamento de erros (sem cache)."""
    cep_limpo = cep.replace("-", "").replace(".", "").strip()
    if len(cep_limpo) != 8 or not cep_limpo.isdigit():
        return {"erro": "Formato de CEP inválido. Precisa de 8 dígitos, amigão!"}

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        response = requests.get(url, timeout=10) # Tempo menor para resposta rápida
        response.raise_for_status()
        data = response.json()
        if 'erro' in data and data['erro'] is True:
            return {"erro": f"CEP '{cep_limpo}' não encontrado no ViaCEP. Ele se escondeu! 🧐"}
        if not data.get('logradouro') or not data.get('localidade') or not data.get('uf'):
             return {"erro": f"CEP '{cep_limpo}' encontrado, mas os dados de endereço estão incompletos. O ViaCEP só contou parte da história!"}
        return data
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({10}s) ao buscar o CEP '{cep_limpo}'. O ViaCEP não responde! 😴"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro na comunicação com o ViaCEP para o CEP '{cep_limpo}': {e}. Problemas na linha!"}
    except Exception as e:
         return {"erro": f"Ocorreu um erro inesperado ao buscar o CEP '{cep_limpo}': {e}. Isso não estava nos meus manuais!"}

def geocodificar_endereco_uncached(rua: str, numero: str, cidade: str, estado: str, api_key: str) -> Dict[str, Any]:
    """Tenta obter coordenadas geográficas e link Google Maps via Google Maps Geocoding API (sem cache)."""
    if not api_key:
        return {"erro": "Chave de API de Geocodificação não fornecida."}
    if not rua or not numero or not cidade or not estado:
         return {"erro": "Dados de endereço insuficientes (requer rua, número, cidade, estado) para geocodificar."}

    address = f"{rua}, {numero}, {cidade}, {estado}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&key={api_key}"

    try:
        response = requests.get(url, timeout=10) # Tempo menor para resposta rápida
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK':
            status = data.get('status', 'STATUS DESCONHECIDO')
            error_msg = data.get('error_message', 'Sem mensagem adicional.')
            # Trata casos específicos comuns
            if status == 'ZERO_RESULTS':
                 error_msg = "Nenhum local exato encontrado para o endereço fornecido. Tente refinar o número ou referência, ou use a entrada manual de coordenadas/descrição."
            elif status == 'OVER_DAILY_LIMIT' or status == 'OVER_QUERY_LIMIT':
                 error_msg = "Limite de uso da API Geocoding excedido. Verifique sua configuração de cobrança ou espere."
            elif status == 'REQUEST_DENIED':
                 error_msg = "Requisição à API Geocoding negada. Verifique sua chave, restrições de API ou configurações de cobrança."
            # Inclui outros status conhecidos
            elif status == 'INVALID_REQUEST':
                 error_msg = "Requisição inválida (endereço mal formatado?)."
            elif status == 'UNKNOWN_ERROR':
                 error_msg = "Erro desconhecido na API Geocoding."
            else:
                 error_msg = f"Status da API: {status}. {error_msg}"


            return {"erro": f"Geocodificação falhou. Status: {status}. Mensagem: {error_msg}"}

        if not data['results']:
             return {"erro": "Geocodificação falhou. Nenhum local exato encontrado para o endereço fornecido. Tente refinar o número ou referência."}

        location = data['results'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = data['results'][0].get('formatted_address', address)

        return {
            "latitude": lat,
            "longitude": lng,
            "endereco_formatado_api": formatted_address,
            "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
            "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"
        }
    except requests.exceptions.Timeout:
         return {"erro": f"Tempo limite excedido ({10}s) ao tentar geocodificar: {address}"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro na comunicação com a API de Geocodificação: {address}. Detalhes: {e}"}
    except Exception as e:
        return {"erro": f"Ocorreu um erro inesperado durante a geocodificação: {address}. Detalhes: {e}"}


# --- Funções de Análise de IA (Cacheado para resultados estáveis por sessão) ---
# Safety settings configuradas para permitir discussões sobre perigos na rua
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

@st.cache_data(show_spinner="🧠 Analisando características estruturadas e observações com IA Gemini...")
def analisar_caracteristicas_e_observacoes_gemini(_caracteristicas: Dict[str, Any], _observacoes: str, _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """
    Utiliza o Gemini (Texto) para analisar as características estruturadas e as observações
    e extrair insights estruturados. Retorna um dicionário com o resultado ou mensagem de erro.
    """
    if not _model:
        return {"insights": "🤖 Análise de descrição via IA indisponível (Motor Gemini Text offline)."}

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in _caracteristicas.items():
        if isinstance(value, list):
            caracteristicas_formatadas.append(f"- {key}: {', '.join([item for item in value if item and item != 'Selecione']) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto = "\n".join(caracteristicas_formatadas)

    observacoes_texto = _observacoes.strip() if _observacoes else "Nenhuma observação adicional fornecida."

    prompt = f"""
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
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"insights": f"❌ Análise de características/observações bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"insights": response.text.strip()}
    except Exception as e:
        return {"insights": f"❌ Erro ao analisar características/observações com IA: {e}"}

@st.cache_data(show_spinner="🧠 Calculando o Nível de Prioridade Robótica...")
def categorizar_urgencia_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """
    Utiliza o Gemini (Texto) para sugerir uma categoria de urgência com base nos dados estruturados, observações e insights.
    Retorna um dicionário com o resultado ou mensagem de erro.
    """
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Text offline)."}

    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia_result.get('insights', 'Análise de insights não disponível.')

    localizacao_exata = _dados_denuncia.get('localizacao_exata_processada', {})
    tipo_loc = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')

    loc_contexto = f"Localização informada: Tipo: {tipo_loc}."
    if input_original_loc and input_original_loc != 'Não informado.':
         loc_contexto += f" Detalhes originais: '{input_original_loc}'."

    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
        lat = localizacao_exata.get('latitude')
        lon = localizacao_exata.get('longitude')
        loc_contexto += f" Coordenadas: {lat}, {lon}. Link gerado: {localizacao_exata.get('google_maps_link_gerado', 'Não disponível')}."

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
             # Filtra 'Selecione' ou vazios da lista
            caracteristicas_formatadas.append(f"- {key}: {', '.join([item for item in value if item and item != 'Selecione']) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = f"""
    Com base nos dados da denúncia (características estruturadas, observações) e nos insights da análise de texto, sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade/tamanho, profundidade, PERIGOS POTENCIAIS e impactos mencionados, o CONTEXTO DA VIA (tipo de tráfego, contexto específico) e qualquer ADICIONAL relevante nas observações ou insights.

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem perigo aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, perigo CLARO e/ou frequente (risco de acidente mais sério, dano significativo a veículo, alto risco para moto/bike/pedestre), em via movimentada ou área de risco (escola, hospital, curva, subida/descida). Requer atenção RÁPida, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal, buraco em local de desvio impossível), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Dados da Denúncia:
    Localização Básica: Rua {_dados_denuncia.get('buraco', {}).get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {_dados_denuncia.get('buraco', {}).get('numero_proximo', 'Não informado')}. Cidade: {_dados_denuncia.get('buraco', {}).get('endereco', {}).get('cidade_buraco', 'Não informada')}, Estado: {_dados_denuncia.get('buraco', {}).get('estado_buraco', 'Não informado')}.
    {loc_contexto}

    Características Estruturadas Fornecidas:
    {caracteristicas_texto_prompt}

    Observações Adicionais:
    "{observacoes}"

    Insights Extraídos pela Análise de Texto/Características:
    {insights_texto}

    Com base nestes dados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 2 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais importantes dos dados fornecidos e insights.

    Formato de saída (muito importante seguir este formato):
    Categoria Sugerida: [Categoria Escolhida]
    Justificativa: [Justificativa Breve]
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"urgencia_ia": f"❌ Sugestão de urgência bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"urgencia_ia": response.text.strip()}
    except Exception as e:
        return {"urgencia_ia": f"❌ Erro ao sugerir urgência com IA: {e}"}


@st.cache_data(show_spinner="🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
def sugerir_causa_e_acao_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """
    Utiliza o Gemini (Texto) para sugerir possíveis causas do buraco e ações de reparo com base nos dados, insights e observações.
    Retorna um dicionário com o resultado ou mensagem de erro.
    """
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Text offline)."}

    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia_result.get('insights', 'Análise de insights não disponível.')

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
             # Filtra 'Selecione' ou vazios da lista
            caracteristicas_formatadas.append(f"- {key}: {', '.join([item for item in value if item and item != 'Selecione']) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = f"""
    Com base nos dados fornecidos pelo denunciante (características estruturadas, observações) e nos insights extraídos pela análise de IA de texto, tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico (ex: chuva forte recente, desgaste do asfalto pelo tempo/tráfego, problema na drenagem subterrânea, afundamento devido a reparo anterior, obra mal feita na região). Baseie-se em todos os dados textuais disponíveis.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via, reparo na rede de água/esgoto). Baseie-se na severidade, perigos e o que foi observado/analisado (texto) e as possíveis causas.
    Baseie suas sugestões EXCLUSIVAMENTE nas informações e análises disponíveis. Se os dados não derem pistas suficientes, indique "Não especificado/inferido nos dados". Seja lógico e prático.

    Informações Relevantes da Denúncia:
    Características Estruturadas:
    {caracteristicas_texto_prompt}
    Observações Adicionais: "{observacoes}"
    Insights Extraídos pela Análise de Texto/Características:
    {insights_texto}

    Formato de saída:
    Possíveis Causas Sugeridas: [Lista de causas sugeridas baseadas nos dados ou 'Não especificado/inferido nos dados']
    Sugestões de Ação/Reparo Sugeridas: [Lista de ações sugeridas baseadas nos dados/insights ou 'Não especificado/inferido nos dados']
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"sugestao_acao_ia": f"❌ Sugestão de causa/ação bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"sugestao_acao_ia": response.text.strip()}
    except Exception as e:
        return {"sugestao_acao_ia": f"❌ Erro ao sugerir causa/ação com IA: {e}"}

# Removed @st.cache_data from gerar_resumo_completo_gemini for improved stability
def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _insights_ia_result: Dict[str, Any], _urgencia_ia_result: Dict[str, Any], _sugestao_acao_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """
    Utiliza o Gemini (Texto) para gerar um resumo narrativo inteligente da denúncia completa,
    incluindo dados estruturados e resultados das análises de IA (texto).
    Retorna um dicionário com o resultado ou mensagem de erro.
    """
    if not _model:
        return {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini Text offline)."}

    # Acessando os dados diretamente do dicionário completo passado como argumento
    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    caracteristicas = buraco.get('caracteristicas_estruturadas', {})
    observacoes = buraco.get('observacoes_adicionais', 'Nenhuma observação adicional fornecida.')
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})

    # Acessando os resultados das análises anteriores passados como argumentos
    insights_texto = _insights_ia_result.get('insights', 'Análise da descrição/características não disponível ou com erro.')
    urgencia_ia_text = _urgencia_ia_result.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro.')
    # Access _sugestao_acao_ia_result safely using the (variable or {}).get() pattern
    sugestao_acao_ia_text = (_sugestao_acao_ia_result or {}).get('sugestao_acao_ia', 'Sugestões de causa/ação não disponíveis ou com erro.') # Apply safe access here

    loc_info_resumo = "Localização exata não especificada ou processada."
    tipo_loc_processada = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')
    motivo_falha_geo_resumo = localizacao_exata.get('motivo_falha_geocodificacao_anterior', None)

    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         lat = localizacao_exata.get('latitude')
         lon = localizacao_exata.get('longitude')
         link_gerado = localizacao_exata.get('google_maps_link_gerado', 'Não disponível')
         loc_info_resumo = f"Localização Exata: Coordenadas {lat}, {lon} (Obtida via: {tipo_loc_processada.replace(' (API)', ' API').replace('Manual', 'Manual').replace('Fornecidas/Extraídas', 'Manual')}). Link Google Maps: {link_gerado}."
         if input_original_loc and input_original_loc != 'Não informado.':
             loc_info_resumo += f" (Input original: '{input_original_loc}')"

    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização via descrição manual detalhada: '{localizacao_exata.get('descricao_manual', 'Não informada')}'. (Input original: '{input_original_loc}')"

    elif input_original_loc and input_original_loc != 'Não informado.' and tipo_loc_processada == 'Não informada':
         loc_info_resumo = f"Localização informada (tipo não detectado): '{input_original_loc}'."

    if motivo_falha_geo_resumo:
         loc_info_resumo += f" (Nota: {motivo_falha_geo_resumo})"

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
             # Filtra 'Selecione' ou vazios da lista
            caracteristicas_formatadas.append(f"- {key}: {', '.join([item for item in value if item and item != 'Selecione']) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)

    data_hora = _dados_denuncia_completa.get('metadata', {}).get('data_hora_utc', 'Não registrada')

    prompt = f"""
    Gere um resumo narrativo conciso (máximo 10-12 frases) para a seguinte denúncia de buraco no aplicativo Krateras.
    Este resumo deve ser formal, objetivo e útil para equipes de manutenção ou gestão pública.
    Combine os dados estruturados, as observações adicionais, a localização exata processada e os resultados das análises de IA (texto).

    Inclua:
    - Quem denunciou (Nome, Cidade de Residência).
    - Onde está o buraco (Rua, Número Próximo/Referência, Bairro, Cidade do Buraco, Estado do Buraco, CEP se disponível).
    - A localização EXATA processada (mencione como foi obtida e os dados relevantes).
    - O lado da rua.
    - As características estruturadas fornecidas (Tamanho, Perigo, Profundidade, Água, Tráfego, Contexto da Via).
    - Informações adicionais importantes das Observações.
    - Os principais pontos da Análise de Texto/Características de IA (Perigos Potenciais, Contexto Adicional).
    - A SUGESTÃO de Categoria de Urgência pela IA e sua Justificativa.
    - As SUGESTÕES de POSSÍVEIS CAUSAS e TIPOS DE AÇÃO/REPARO sugeridas pela IA (se disponíveis).

    Dados Completos da Denúncia:
    Denunciante: {denunciante.get('nome', 'Não informado')}, de {denunciante.get('cidade_residencia', 'Não informada')}.
    Endereço do Buraco: Rua {endereco.get('rua', 'Não informada')}, Nº Próximo: {buraco.get('numero_proximo', 'Não informado')}. Bairro: {endereco.get('bairro', 'Não informado')}. Cidade: {endereco.get('cidade_buraco', 'Não informada')}, Estado: {endereco.get('estado_buraco', 'Não informado')}. CEP: {buraco.get('cep_informado', 'Não informado')}.
    Lado da Rua: {buraco.get('lado_rua', 'Não informado')}.
    Localização Exata Coletada: {loc_info_resumo}
    Características Estruturadas Fornecidas:
    {caracteristicas_texto_prompt}
    Observações Adicionais: "{observacoes}"

    Insights da Análise de Texto/Características de IA:
    {insights_texto}

    Sugestão de Urgência pela IA:
    {urgencia_ia_text}

    Sugestões de Causa e Ação pela IA:
    {sugestao_acao_ia_text}


    Gere o resumo em português. Comece com "Relatório Krateras: Denúncia de buraco..." ou algo similar. Use linguagem clara e direta.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"resumo_ia": f"❌ Geração de resumo bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"resumo_ia": response.text.strip()}
    except Exception as e:
        return {"resumo_ia": f"❌ Erro ao gerar resumo completo com IA: {e}"}

@st.cache_data(show_spinner="🔍 Analisando imagem com IA Gemini Vision...")
def analisar_imagem_buraco(image_bytes: bytes, _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """
    Utiliza o Gemini Vision para analisar a imagem do buraco.
    Retorna um dicionário com o resultado ou mensagem de erro.
    """
    if not _model:
        return {"analise_visual": "🤖 Análise visual via IA indisponível (Motor Gemini Vision offline)."}

    try:
        prompt = """
        Analise esta imagem de um buraco na rua e forneça uma análise técnica detalhada.
        
        Forneça a análise no seguinte formato:
        
        DESCRIÇÃO FÍSICA:
        - Descrição detalhada do tamanho aparente, forma e características visíveis
        - Profundidade estimada baseada em aspectos visuais
        - Condições do asfalto ao redor
        
        AVALIAÇÃO DE SEVERIDADE:
        - Classificação: [BAIXA/MÉDIA/ALTA/CRÍTICA]
        - Justificativa da classificação
        
        RISCOS IDENTIFICADOS:
        - Liste os riscos potenciais para veículos
        - Liste os riscos potenciais para pedestres/ciclistas
        - Outros riscos relevantes observados
        
        CONDIÇÕES AGRAVANTES:
        - Problemas adicionais visíveis (rachaduras, água, etc.)
        - Fatores que podem piorar a situação
        
        RECOMENDAÇÕES:
        - Tipo de intervenção sugerida
        - Urgência do reparo
        - Medidas temporárias recomendadas
        
        Seja preciso, técnico e detalhado na análise.
        """

        response = _model.generate_content([prompt, image_bytes], stream=False)
        
        if not hasattr(response, 'text'):
            return {"analise_visual": "❌ Erro: A análise da imagem não gerou resposta válida."}
            
        return {"analise_visual": response.text.strip()}
        
    except Exception as e:
        return {"analise_visual": f"❌ Erro ao analisar imagem com IA: {e}"}


# --- Funções de Navegação e Renderização de UI ---

def next_step():
    """Avança para o próximo passo no fluxo da aplicação."""
    steps = [
        'start',
        'collect_denunciante',
        'collect_address', # Etapa consolidada
        'collect_buraco_details_and_location', # Etapa consolidada
        'processing_ia',
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
        'collect_address', # Etapa consolidada
        'collect_buraco_details_and_location', # Etapa consolidada
        'processing_ia',
        'show_report'
    ]
    try:
        current_index = steps.index(st.session_state.step)
        if current_index > 0:
             st.session_state.step = steps[current_index - 1]
             st.rerun()
    except ValueError:
         st.session_state.step = steps[0]
         st.rerun()


# --- Layout Principal da Aplicação ---

#st.title("Krateras 🚧🚧🚧")
st.subheader("O Especialista Robótico de Denúncia de Buracos")

# --- Fluxo da Aplicação baseado no Estado ---

if st.session_state.step == 'start':
    st.write("""
    Olá! Krateras v10.1 entrando em órbita com **Estabilidade Reforçada Final**! Sua missão, caso aceite: denunciar buracos na rua
    para que possam ser consertados. A segurança dos seus dados e a precisão da denúncia
    são nossas prioridades máximas.

    Nesta versão, as etapas de coleta de endereço e detalhes foram otimizadas para um fluxo mais suave.
    Uma imagem pode ser incluída no relatório final.
    A geolocalização no relatório agora inclui mapas Google Maps e OpenStreetMap incorporados e links diretos para referência visual.

    Utilizamos inteligência artificial (Google Gemini Text) e APIs de localização (Google Geocoding,
    ViaCEP) para coletar, analisar (via texto) e gerar um relatório detalhado para as autoridades competentes.

    Fui criado com o que há de mais avançado em Programação, IA (Análise de Texto!), Design Inteligente,
    Matemática e Lógica Inabalável. Com acesso seguro às APIs, sou imparável.

    Clique em Iniciar para começarmos a coleta de dados.
    """)




    if st.button("Iniciar Missão Denúncia!"):
        # Limpa o estado da denúncia completa ao iniciar uma nova
        st.session_state.denuncia_completa = {
            "metadata": {
                "data_hora_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        # Limpa estados específicos da coleta de endereço para garantir um início limpo
        st.session_state.cep_input_consolidated = ''
        st.session_state.cep_error_consolidated = False
        st.session_state.cep_success_message = ''
        st.session_state.cep_error_message = ''
        # Limpa também o estado de 'buraco' na sessão_state fora de denuncia_completa
        # que era usado para pré-preencher na etapa 'collect_address'
        if 'buraco' in st.session_state:
            del st.session_state.buraco
        # Carregar chaves e inicializar APIs (cache_resource mantém os objetos model/key)
        gemini_api_key, geocoding_api_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_api_key
        st.session_state.gemini_model, st.session_state.gemini_vision_model = init_gemini_text_model(gemini_api_key) 
        st.session_state.api_keys_loaded = True
        next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Formulário para coletar dados do denunciante
    with st.form("form_denunciante"):
        # Using .get() with a default value for robustness in case state is cleared unexpectedly mid-run
        current_denunciante_data = st.session_state.denuncia_completa.get('denunciante', {})

        nome = st.text_input("Seu nome completo:", value=current_denunciante_data.get('nome', ''), key='nome_denunciante')
        # Adjusting number_input value handling for None
        current_idade = current_denunciante_data.get('idade')
        idade_value = current_idade if current_idade is not None else None # Use None directly
        idade = st.number_input("Sua idade (opcional, aproximada 😉):", min_value=0, max_value=120, value=idade_value, help="Deixe em branco ou use 0 se não quiser informar.", key='idade_denunciante_input')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", value=current_denunciante_data.get('cidade_residencia', ''), key='cidade_residencia_denunciante')

        submitted = st.form_submit_button("Avançar (Dados Denunciante)")

        if submitted:
            if not nome or not cidade_residencia:
                st.error("❗ Nome e Cidade de residência são campos obrigatórios. Por favor, preencha-os.")
            else:
                st.session_state.denuncia_completa['denunciante'] = {
                    "nome": nome.strip(),
                    # Store as None if 0 or None input, only store positive integers
                    "idade": st.session_state.idade_denunciante_input if st.session_state.idade_denunciante_input is not None and st.session_state.idade_denunciante_input > 0 else None,
                    "cidade_residencia": cidade_residencia.strip()
                }
                st.success(f"Olá, {nome}! Dados coletados. Preparando para dados do buraco...")
                next_step()

    st.button("Voltar", on_click=prev_step)

# --- ETAPA CONSOLIDADA: COLETAR ENDEREÇO BASE ---
elif st.session_state.step == 'collect_address':
    st.header("--- 🚧 Detalhes do Buraco (Endereço Base) ---")
    st.subheader("Forneça a rua do buraco.")

    # Initialize buraco/endereco data in state if not present.
    # This state is separate from denuncia_completa until submission for cleaner handling in this step.
    if 'buraco' not in st.session_state:
        st.session_state.buraco = {'endereco': {}}
    if 'endereco' not in st.session_state.buraco:
         st.session_state.buraco['endereco'] = {}

    endereco_atual = st.session_state.buraco.get('endereco', {})

    # Initialize/manage CEP state
    if 'cep_input_consolidated' not in st.session_state:
         st.session_state.cep_input_consolidated = ''
    if 'cep_error_consolidated' not in st.session_state:
         st.session_state.cep_error_consolidated = False
    if 'cep_success_message' not in st.session_state:
         st.session_state.cep_success_message = ''
    if 'cep_error_message' not in st.session_state:
         st.session_state.cep_error_message = ''

    # --- CEP Section ---
    st.subheader("Opção 1: Buscar por CEP")
    st.info("Digite o CEP para preencher automaticamente os campos de Rua, Bairro, Cidade e Estado. Você poderá corrigir os dados se necessário.")
    col1, col2 = st.columns([3,1])
    with col1:
         cep_atual = st.text_input("Digite o CEP (apenas números):", max_chars=8, key='cep_input_field_consolidated', value=st.session_state.cep_input_consolidated, help="Ex: 12345678")
    with col2:
         # Button to trigger CEP search
         if st.button("Buscar CEP", key='buscar_cep_button_consolidated'):
             st.session_state.cep_input_consolidated = cep_atual # Store the input value
             # Clear previous CEP messages
             st.session_state.cep_success_message = ''
             st.session_state.cep_error_message = ''

             if not st.session_state.cep_input_consolidated:
                 st.session_state.cep_error_consolidated = True
                 st.session_state.cep_error_message = "❗ Por favor, digite um CEP para buscar."
             else:
                 # Show spinner explicitly for this uncached API call
                 with st.spinner("⏳ Interrogando o ViaCEP..."):
                    dados_cep_result = buscar_cep_uncached(st.session_state.cep_input_consolidated) # Use uncached version

                 if 'erro' in dados_cep_result:
                     st.session_state.cep_error_consolidated = True
                     st.session_state.cep_error_message = f"❌ Falha na busca por CEP: {dados_cep_result['erro']}"
                     st.session_state.cep_success_message = ''
                     # Do NOT clear manual fields on CEP error, user might want to correct them
                     # endereco_atual remains as it was or as manually edited
                 else:
                     st.session_state.cep_error_consolidated = False
                     st.session_state.cep_error_message = ''
                     st.session_state.cep_success_message = "✅ Endereço Encontrado (ViaCEP)! Por favor, confirme ou corrija abaixo."
                     # Update buraco.endereco state and potentially the manual fields display
                     st.session_state.buraco['endereco'].update({
                         'rua': dados_cep_result.get('logradouro', ''),
                         'bairro': dados_cep_result.get('bairro', ''),
                         'cidade_buraco': dados_cep_result.get('localidade', ''),
                         'estado_buraco': dados_cep_result.get('uf', '')
                     })
                     # Store CEP in buraco data if search was successful
                     st.session_state.buraco['cep_informado'] = st.session_state.cep_input_consolidated


             st.rerun() # Rerun to update the display based on CEP result and state

    # Display CEP messages after the button action
    if st.session_state.cep_success_message:
         st.success(st.session_state.cep_success_message)
    if st.session_state.cep_error_message:
         st.error(st.session_state.cep_error_message)


    st.markdown("---")
    st.subheader("Opção 2: Digitar Endereço Manualmente")
    st.info("Digite o endereço da rua do buraco nos campos abaixo.")

    # Manual input fields (always displayed, potentially pre-filled by CEP result or previous state)
    # Wrap these in a form to allow validation and advancing the step
    with st.form("form_manual_address_submit"):
        # Use the current state (potentially updated by CEP) as initial value for manual fields
        rua_manual = st.text_input("Nome completo da rua:", value=endereco_atual.get('rua', ''), key='rua_manual_buraco_form_submit', help="Ex: Rua das Acácias")
        bairro_manual = st.text_input("Bairro onde está o buraco (opcional):", value=endereco_atual.get('bairro', ''), key='bairro_manual_buraco_form_submit', help="Ex: Centro")
        cidade_manual = st.text_input("Cidade onde está o buraco:", value=endereco_atual.get('cidade_buraco', ''), key='cidade_manual_buraco_form_submit', help="Ex: Belo Horizonte")
        estado_manual = st.text_input("Estado (UF) onde está o buraco:", value=endereco_atual.get('estado_buraco', ''), max_chars=2, key='estado_manual_buraco_form_submit', help="Ex: MG")

        # Use a single submit button to advance the step after confirming address
        submitted_address = st.form_submit_button("Confirmar Endereço Base e Avançar")

        if submitted_address:
            if not rua_manual or not cidade_manual or not estado_manual:
                st.error("❗ Rua, Cidade e Estado são campos obrigatórios para o endereço do buraco.")
            else:
                # Update the address in buraco.endereco state from the manual fields (most current values from the form)
                st.session_state.buraco['endereco'] = {
                    'rua': rua_manual.strip(),
                    'bairro': bairro_manual.strip(),
                    'cidade_buraco': cidade_manual.strip(),
                    'estado_buraco': estado_manual.strip().upper()
                }
                # If manual entry was used, clear CEP info from buraco data state
                # This ensures CEP is only kept if the CEP search was the LAST successful operation AND the user confirms via this form.
                if st.session_state.get('cep_input_field_consolidated') and not st.session_state.get('cep_error_consolidated') and st.session_state.get('cep_success_message'):
                     # CEP search was successful and user confirmed, keep the CEP that was stored in buraco state.
                     pass # CEP is already in st.session_state.buraco from the CEP search logic
                else:
                     # Manual entry was used, or CEP failed. Clear potential old CEP info from buraco state.
                     if 'cep_informado' in st.session_state.buraco:
                          del st.session_state.buraco['cep_informado']

                # Store the buraco data (including address and possibly cep) in the full denunciation state
                st.session_state.denuncia_completa['buraco'] = st.session_state.buraco
                # Clear the separate 'buraco' state managed within this step after transferring it
                del st.session_state.buraco


                next_step() # Move to the next stage (collecting details and location)

    st.button("Voltar", on_click=prev_step)


# --- ETAPA CONSOLIDADA: COLETAR DETALHES E LOCALIZAÇÃO EXATA ---
elif st.session_state.step == 'collect_buraco_details_and_location':
    st.header("--- 🚧 Detalhes Finais e Localização Exata ---")
    st.subheader("Informações cruciais para a localização e análise!")

    # Access buraco data from the full denunciation state
    buraco_data_current = st.session_state.denuncia_completa.get('buraco', {})
    endereco_basico = buraco_data_current.get('endereco', {})

    # Check if basic address info is present (safety check)
    if not endereco_basico or not endereco_basico.get('rua') or not endereco_basico.get('cidade_buraco') or not endereco_basico.get('estado_buraco'):
         st.error("❗ Erro interno: Informações básicas de endereço estão faltando. Por favor, volte para a etapa anterior.")
         st.button("Voltar para Endereço Base", on_click=prev_step) # Provide a way back
         st.stop() # Stop execution here if critical data is missing


    st.write(f"Endereço Base: Rua **{endereco_basico.get('rua', 'Não informada')}**, Cidade: **{endereco_basico.get('cidade_buraco', 'Não informada')}** - **{endereco_basico.get('estado_buraco', 'Não informado')}**")
    if endereco_basico.get('bairro'):
         st.write(f"Bairro: **{endereco_basico.get('bairro')}**")
    if buraco_data_current.get('cep_informado'):
         st.write(f"CEP informado: **{buraco_data_current.get('cep_informado')}**")

    st.markdown("---") # Separador visual

    with st.form("form_buraco_details_location"):
        st.subheader("📋 Características do Buraco (Escolha as opções)")
        col1, col2 = st.columns(2)
        with col1:
             tamanho = st.selectbox(
                 "Tamanho Estimado:",
                 ['Selecione', 'Pequeno (cabe um pneu)', 'Médio (maior que um pneu, mas cabe em uma faixa)', 'Grande (ocupa mais de uma faixa, difícil desviar)', 'Enorme (cratera, impede passagem)', 'Crítico (buraco na pista principal, risco iminente de acidente grave)'],
                 key='tamanho_buraco'
             )
             perigo = st.selectbox(
                 "Perigo Estimado:",
                 ['Selecione', 'Baixo (principalmente estético, risco mínimo)', 'Médio (risco de dano leve ao pneu ou suspensão)', 'Alto (risco de acidente/dano sério para carro, alto risco para moto/bike/pedestre)', 'Altíssimo (risco grave e iminente de acidente, histórico de acidentes no local)'],
                 key='perigo_buraco'
             )
             profundidade = st.selectbox(
                 "Profundidade Estimada:",
                 ['Selecione', 'Raso (menos de 5 cm)', 'Médio (5-15 cm)', 'Fundo (15-30 cm)', 'Muito Fundo (mais de 30 cm / "engole" um pneu)'],
                 key='profundidade_buraco'
             )
        with col2:
             agua = st.selectbox(
                 "Presença de Água/Alagamento:",
                 ['Selecione', 'Seco', 'Acumula pouca água', 'Acumula muita água (vira piscina)', 'Problema de drenagem visível (jato de água, nascente)'],
                 key='agua_buraco'
             )
             trafego = st.selectbox(
                 "Tráfego Estimado na Via:",
                 ['Selecione', 'Muito Baixo (rua local sem saída)', 'Baixo (rua residencial calma)', 'Médio (rua residencial/comercial com algum fluxo)', 'Alto (avenida movimentada, via de acesso)', 'Muito Alto (via expressa, anel viário)'],
                 key='trafego_buraco'
             )
             contexto_via = st.multiselect(
                 "Contexto da Via (selecione um ou mais):",
                 ['Reta', 'Curva acentuada', 'Cruzamento/Esquina', 'Subida', 'Descida', 'Próximo a faixa de pedestre', 'Próximo a semáforo/lombada', 'Área escolar/Universitária', 'Área hospitalar/Saúde', 'Área comercial intensa', 'Via de acesso principal', 'Via secundária', 'Próximo a ponto de ônibus/transporte público', 'Próximo a ciclovia/ciclofaixa'],
                 key='contexto_buraco'
             )

        st.subheader("✍️ Localização Exata e Outros Detalhes")
        st.write("➡️ Utilize o número próximo ou ponto de referência para ajudar na geocodificação automática. Se falhar ou for impreciso, forneça COORDENADAS ou LINK do Google Maps com coordenadas.")
        numero_proximo = st.text_input("Número do imóvel mais próximo ou ponto de referência (ESSENCIAL para precisão! Ex: 'Em frente ao 123', 'Esquina c/ Rua X', 'Entre os números 45 e 60'):", key='numero_proximo_buraco')
        lado_rua = st.text_input("Lado da rua onde está o buraco (Ex: 'lado par', 'lado ímpar', 'lado direito (sentido centro)', 'lado esquerdo (sentido bairro)'):", key='lado_rua_buraco')

        st.markdown("""
        <p>Localização EXATA (opcional, mas altamente recomendado se a geocodificação falhar):</p>
        <p>A MELHOR forma é COPIAR AS COORDENADAS (Lat,Long) ou um LINK do Google Maps que as contenha.<br>
        Sugestão: Abra o Google Maps, encontre o buraco, <strong>TOQUE/CLIQUE E SEGURE NO LOCAL PREOCUPANTE</strong>.
        As coordenadas ou um link aparecerão na barra de busca ou ao compartilhar.</p>
        <p>Alternativamente, uma DESCRIÇÃO MUITO DETALHADA do local EXATO no mapa (Ex: 'Exatamente 5 metros à esquerda do poste Y, em frente ao portão azul do nº 456').</p>
        """, unsafe_allow_html=True)
        localizacao_manual_input = st.text_input("Insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO DETALHADA manual:", key='localizacao_manual')

        st.subheader("📷 Foto do Buraco (Opcional, para referência visual no relatório)")
        st.write("Uma boa foto ajuda as equipes de reparo a identificar o problema rapidamente. Por favor, envie uma imagem clara.")
        uploaded_image = st.file_uploader("Carregar Imagem do Buraco:", type=['jpg', 'jpeg', 'png', 'webp'], key='uploaded_image_buraco')
        if uploaded_image:
             st.info(f"Imagem '{uploaded_image.name}' carregada e será incluída no relatório.")


        st.subheader("📝 Observações Adicionais")
        st.write("Algo mais a acrescentar que não foi coberto pelas opções? Detalhes como: 'problema recorrente (há quanto tempo?)', 'surgiu depois da última chuva', 'muito difícil desviar à noite', 'causou X dano ao meu carro', 'vi um acidente aqui':")
        observacoes_adicionais = st.text_area("Suas observações:", key='observacoes_buraco')


        submitted = st.form_submit_button("Enviar Denúncia para Análise Robótica!")

        if submitted:
            # Validate required fields
            required_selects = {'tamanho_buraco': 'Tamanho Estimado', 'perigo_buraco': 'Perigo Estimado', 'profundidade_buraco': 'Profundidade Estimada', 'agua_buraco': 'Presença de Água', 'trafego_buraco': 'Tráfego Estimado na Via'}
            missing_selects = [label for key, label in required_selects.items() if st.session_state.get(key, 'Selecione') == 'Selecione'] # Use .get for safety


            if not numero_proximo or not lado_rua or not observacoes_adicionais:
                 st.error("❗ Número próximo/referência, Lado da rua e Observações adicionais são campos obrigatórios.")
            elif missing_selects:
                 st.error(f"❗ Por favor, selecione uma opção para os seguintes campos: {', '.join(missing_selects)}.")
            else:
                # Update buraco data with details and observations
                st.session_state.denuncia_completa['buraco'].update({
                    'numero_proximo': numero_proximo.strip(),
                    'lado_rua': lado_rua.strip(),
                    'caracteristicas_estruturadas': {
                         'Tamanho Estimado': tamanho,
                         'Perigo Estimado': perigo,
                         'Profundidade Estimada': profundidade,
                         'Presença de Água/Alagamento': agua,
                         'Tráfego Estimado na Via': st.session_state.get('trafego_buraco', 'Selecione'), # Use .get
                         'Contexto da Via': contexto_via if contexto_via else [] # Ensure it's a list, can be empty
                    },
                    'observacoes_adicionais': observacoes_adicionais.strip()
                })

                # --- Processar Imagem Upload ---
                # Clear previous image data before processing the new one
                st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = None
                if uploaded_image is not None:
                    try:
                        # Read the image bytes
                        image_bytes = uploaded_image.getvalue()
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {
                            "filename": uploaded_image.name,
                            "type": uploaded_image.type,
                            "bytes": image_bytes # Store the bytes
                        }
                    except Exception as e:
                        st.error(f"❌ Erro ao processar a imagem para inclusão no relatório: {e}. Por favor, tente novamente.")
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {"erro": f"Erro ao carregar: {e}"}


                # --- Tentar Geocodificação Automática ---
                # Clear previous processed location data
                st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"}
                tentou_geocodificar = False
                geocodificacao_sucesso_coords = False # Flag specifically for getting coordinates
                geo_resultado: Dict[str, Any] = {} # Initialize to store auto-geo result

                rua_buraco = endereco_basico.get('rua')
                cidade_buraco = endereco_basico.get('cidade_buraco')
                estado_buraco = endereco_basico.get('estado_buraco')

                # Try to use the number/reference for geocoding
                num_referencia_geo = numero_proximo.strip()

                # We need Street, Number/Reference, City, State and Geocoding API Key to attempt auto-geocoding
                tem_dados_para_geo_completo = (st.session_state.geocoding_api_key and rua_buraco and num_referencia_geo and cidade_buraco and estado_buraco)

                if tem_dados_para_geo_completo:
                    st.info("✅ Chave de Geocodificação e dados completos para tentativa automática encontrados. Tentando gerar o link do Google Maps automaticamente...")
                    tentou_geocodificar = True
                    # Show spinner for geocoding API call
                    with st.spinner("⏳ Tentando localizar o buraco no mapa global via Geocoding API..."):
                         geo_resultado = geocodificar_endereco_uncached( # Use uncached version
                            rua_buraco,
                            num_referencia_geo, # Use the number/reference as base for geocoding
                            cidade_buraco,
                            estado_buraco,
                            st.session_state.geocoding_api_key
                        )

                    if 'erro' not in geo_resultado:
                        geocodificacao_sucesso_coords = True
                        st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                            "tipo": "Geocodificada (API)",
                            "latitude": geo_resultado['latitude'],
                            "longitude": geo_resultado['longitude'],
                            "endereco_formatado_api": geo_resultado.get('endereco_formatado_api', ''),
                            "google_maps_link_gerado": geo_resultado['google_maps_link_gerado'],
                            "google_embed_link_gerado": geo_resultado.get('google_embed_link_gerado'),
                            "input_original": num_referencia_geo # Reference what input was used for geocoding
                        }
                        st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                    # If there's an error in geo_resultado, it's handled later when setting the failure reason.
                elif not st.session_state.geocoding_api_key:
                     st.warning("⚠️ AVISO: Chave de API de Geocodificação NÃO fornecida. Geocodificação automática NÃO tentada.")
                elif st.session_state.geocoding_api_key and not tem_dados_para_geo_completo:
                     st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes para tentativa automática (precisa de Rua, Número Próximo/Referência, Cidade, Estado). Geocodificação automática NÃO tentada.")


                # --- Processar Coordenadas/Link/Descrição Manual (if provided) ---
                # This is done *regardless* of the success of automatic geocoding,
                # as manual entry might be more accurate or correct the automatic one.
                localizacao_manual_input_processed = localizacao_manual_input.strip()
                lat_manual: Optional[float] = None
                lon_manual: Optional[float] = None
                tipo_manual_processado = "Descrição Manual Detalhada" # Assume manual description by default
                input_original_manual = localizacao_manual_input_processed

                if localizacao_manual_input_processed:
                     # Regex to try to find coordinates in different formats (Lat,Lon or in common links)
                     # Tries to cover "lat,lon", "@lat,lon" in links, "lat lon"
                     # More robust regex: allows spaces or commas as separators, supports negative signs
                     match_coords = re.search(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)', input_original_manual)
                     if match_coords:
                         try:
                             teste_lat = float(match_coords.group(1))
                             teste_lon = float(match_coords.group(2))
                             # Basic coordinate validation
                             if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                                 lat_manual = teste_lat
                                 lon_manual = teste_lon
                                 tipo_manual_processado = "Coordenadas Fornecidas/Extraídas Manualmente"
                                 st.info("✅ Coordenadas válidas detectadas no input manual!")
                             else:
                                 st.warning("⚠️ Parece um formato de coordenadas, mas fora da faixa esperada (-90 a 90 Latitude, -180 a 180 Longitude). Tratando como descrição detalhada.")
                         except ValueError:
                             pass # Not a valid float, proceed to next attempt (link)

                     # If coordinates haven't been found yet, try from a link if it's a link
                     if lat_manual is None and input_original_manual.startswith("http"):
                          st.info("ℹ️ Entrada manual é um link. Tentando extrair coordenadas (sujeito a formato do link)...")
                          # Try regex for Google Maps links (with @lat,lon) or search (with ?,query=lat,lon)
                          match_maps_link = re.search(r'(?:/@|/search/\?api=1&query=)(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual)
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
                                       st.warning("⚠️ Coordenadas extraídas do link no input manual fora da faixa esperada. Tratando como descrição detalhada.")
                              except ValueError:
                                 st.info("ℹ️ Valores no link não parecem coordenadas válidas. Tratando como descrição.")
                          else:
                               st.info("ℹ️ Não foi possível extrair coordenadas reconhecíveis do link do Maps fornecido manualmente.")
                               lat_manual = None
                               lon_manual = None
                               tipo_manual_processado = "Descrição Manual Detalhada"
                     # If coordinates weren't found and it's not a link, it's a manual description
                     elif lat_manual is None:
                         st.info("ℹ️ Entrada manual não detectada como coordenadas ou link. Tratando como descrição detalhada.")
                         tipo_manual_processado = "Descrição Manual Detalhada"


                     # Store the result of the manual input.
                     # If coordinates were found manually, they *override* the result of automatic geocoding.
                     # Manual entry with coordinates has PRIORITY over automatic geocoding.
                     if lat_manual is not None and lon_manual is not None:
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": tipo_manual_processado, # Will be 'Coordenadas Fornecidas/Extraídas Manualmente' or 'Coordenadas Extraídas de Link (Manual)'
                              "input_original": input_original_manual,
                              "latitude": lat_manual,
                              "longitude": lon_manual,
                              # Generate links using manual coordinates
                              "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat_manual},{lon_manual}",
                              "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_manual},{lon_manual}" if st.session_state.geocoding_api_key else None # Try to generate embed link if key exists
                         }
                         geocodificacao_sucesso_coords = True # We have coordinates (via manual)!
                         st.success(f"✅ Localização Exata Obtida (via Input Manual - {tipo_manual_processado})!")
                     # If manual input exists but isn't coordinates, store as manual description:
                     elif localizacao_manual_input_processed:
                         # Only set this if manual input was provided and NO coordinates were found by any method (auto or manual regex)
                         if not geocodificacao_sucesso_coords and lat_manual is None and lon_manual is None: # Added check for manual lat/lon
                             st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                                  "tipo": "Descrição Manual Detalhada",
                                  "input_original": input_original_manual,
                                  "descricao_manual": input_original_manual
                             }
                             # geocodificacao_sucesso_coords remains False if auto-geo failed and manual didn't give coords
                             st.info("ℹ️ Localização exata processada como Descrição Manual Detalhada.")
                     # else: If manual input is empty, keep whatever came from auto-geocoding or the default "Não informada"


                # --- Final check and setting the failure reason ---
                # Check if the *final* processed location type is one that does NOT have coordinates
                final_loc_type = st.session_state.denuncia_completa['localizacao_exata_processada'].get('tipo')

                if final_loc_type not in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Coordenadas Extraídas de Link (Manual)', 'Geocodificada (API)']:
                     # If we ended up *without* coordinates, let's store the reason why we couldn't get them.
                     reason_parts = []

                     # Reason 1: Auto-geocoding failed (if it was attempted)
                     if tentou_geocodificar and 'erro' in geo_resultado:
                          reason_parts.append(f"Geocodificação automática falhou: {geo_resultado['erro']}")
                     # Reason 2: Auto-geocoding not attempted due to missing key
                     elif not st.session_state.geocoding_api_key:
                          reason_parts.append("Chave de API de Geocodificação não fornecida.")
                     # Reason 3: Auto-geocoding not attempted due to insufficient data (but key existed)
                     elif st.session_state.geocoding_api_key and not tem_dados_para_geo_completo:
                          reason_parts.append("Dados insuficientes para Geocodificação automática (requer Rua, Número Próximo/Referência, Cidade, Estado).")

                     # Reason 4: Manual input was given, but wasn't coordinates that could be extracted
                     # Only add this if manual input was provided AND it did NOT result in coordinates
                     if localizacao_manual_input_processed and not (lat_manual is not None and lon_manual is not None):
                          reason_parts.append("Coordenadas não encontradas ou extraídas do input manual.")

                     # Combine and store the reasons if any
                     if reason_parts:
                          # Only update if the current processed type is not already 'Descrição Manual Detalhada'
                          # or if it is, but we have new failure reasons to add.
                          current_failure_reason = st.session_state.denuncia_completa['localizacao_exata_processada'].get('motivo_falha_geocodificacao_anterior', '')
                          new_failure_reason = " / ".join(reason_parts)
                          # Prevent adding redundant messages if it's already set to a specific error
                          if 'motivo_falha_geocodificacao_anterior' not in st.session_state.denuncia_completa['localizacao_exata_processada'] or (current_failure_reason and new_failure_reason != current_failure_reason): # Check if current exists and is different
                                st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = new_failure_reason
                          elif not current_failure_reason and new_failure_reason: # If current is empty but new exists
                               st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = new_failure_reason

                     elif final_loc_type == "Não informada":
                         # Fallback reason if it's "Não informada" and no specific failure reason was captured
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Localização exata baseada em coordenadas não obtida por nenhum método."


                # Everything processed, advance to the IA analysis step
                next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa os dados (via texto) e gera o relatório com a inteligência do Google Gemini.")

    # Access data needed for IA functions
    buraco_data = st.session_state.denuncia_completa.get('buraco', {})
    imagem_data = buraco_data.get('imagem_denuncia')
    caracteristicas = buraco_data.get('caracteristicas_estruturadas', {})
    observacoes = buraco_data.get('observacoes_adicionais', '')

    if imagem_data and 'bytes' in imagem_data and st.session_state.gemini_vision_model:
        st.info("🔍 Iniciando análise visual da imagem com Gemini Vision...")
        st.session_state.denuncia_completa['analise_visual_ia'] = analisar_imagem_buraco(
            imagem_data['bytes'],
            st.session_state.gemini_vision_model
        )

    # Ensure IA result dicts exist in state before populating them with results
    # Initialize with default error/unavailable messages instead of empty dicts for clarity in report if IA fails
    if 'insights_ia' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['insights_ia'] = {"insights": "Análise de características/observações não realizada ou com error."}
    if 'urgencia_ia' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Sugestão de urgência não gerada ou com error."}
    if 'sugestao_acao_ia' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Sugestões de causa/ação não geradas ou com error."}
    if 'resumo_ia' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Resumo não gerado ou com error."}


    # Use a spinner context manager for the whole processing block
    with st.spinner("Executando análises de IA..."):
        # Rodar análise de texto/características
        # Passa o modelo Gemini (pode ser None). Store result directly in state inside the spinner
        st.session_state.denuncia_completa['insights_ia'] = analisar_caracteristicas_e_observacoes_gemini(
            caracteristicas,
            observacoes,
            st.session_state.gemini_model
        )

        # Rodar categorização de urgência
        # Passa o modelo Gemini (pode ser None) E o resultado da análise anterior (acessado diretamente do state)
        st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.denuncia_completa['insights_ia'], # Passa o resultado da análise de insights (garantido ser um dict ou fallback)
            st.session_state.gemini_model
        )


        # Rodar sugestão de causa e ação
        # Passa o modelo Gemini (pode ser None) E o resultado da análise anterior (acessado diretamente do state)
        st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.denuncia_completa['insights_ia'], # Passa o resultado da análise de insights (garantido ser um dict ou fallback)
            st.session_state.gemini_model
        )


        # Gerar resumo completo
        # Passa o modelo Gemini (pode ser None) E os resultados das análises anteriores (acessados diretamente do state)
        # Note: This function is not cached
        st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.denuncia_completa['insights_ia'], # Passa o resultado da análise de insights (garantido ser um dict ou fallback)
            st.session_state.denuncia_completa['urgencia_ia'], # Passa o resultado da sugestão de urgência (garantido ser um dict ou fallback)
            st.session_state.denuncia_completa['sugestao_acao_ia'], # Passa o resultado da sugestão de causa/ação (garantido ser um dict ou fallback)
            st.session_state.gemini_model
        )

        # Avança para exibir o relatório após o processamento (mesmo que algumas IAs falhem/estejam indisponíveis)
    next_step() # Called outside the spinner, after all IA calls are attempted


elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊")
    st.write("✅ MISSÃO KRATERAS CONCLUÍDA! RELATÓRIO GERADO. ✅")

    # Access data from the state with fallbacks for safety
    dados_completos = st.session_state.denuncia_completa
    denunciante = dados_completos.get('denunciante', {})
    buraco = dados_completos.get('buraco', {})
    endereco = buraco.get('endereco', {})
    caracteristicas = buraco.get('caracteristicas_estruturadas', {})
    observacoes = buraco.get('observacoes_adicionais', 'Nenhuma observação adicional fornecida.')
    imagem_data = buraco.get('imagem_denuncia') # Image data
    localizacao_exata = dados_completos.get('localizacao_exata_processada', {})
    insights_ia = dados_completos.get('insights_ia', {})
    urgencia_ia = dados_completos.get('urgencia_ia', {})
    sugestao_acao_ia = dados_completos.get('sugestao_acao_ia', {})
    resumo_ia = dados_completos.get('resumo_ia', {})
    data_hora = dados_completos.get('metadata', {}).get('data_hora_utc', 'Não registrada')
    st.write(f"📅 Data/Hora do Registro (UTC): **{data_hora}**")

    st.markdown("---")

    # Display all steps open in expanders
    with st.expander("👤 Dados do Denunciante", expanded=True):
        st.write(f"**Nome:** {denunciante.get('nome', 'Não informado')}")
        st.write(f"**Idade:** {denunciante.get('idade', 'Não informado')}") # Will be None if not informed
        st.write(f"**Cidade de Residência:** {denunciante.get('cidade_residencia', 'Não informada')}")

    with st.expander("🚧 Dados Base do Endereço do Buraco", expanded=True):
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


    with st.expander("📋 Características Estruturadas e Observações (Denunciante)", expanded=True):
         st.write("**Características Selecionadas:**")
         if caracteristicas:
             # Display only characteristics that are not "Selecione" or None/empty list
             caracteristicas_exibir = {k: v for k, v in caracteristicas.items() if v and v != 'Selecione' and (not isinstance(v, list) or v)}
             if caracteristicas_exibir:
                for key, value in caracteristicas_exibir.items():
                     if isinstance(value, list):
                         st.write(f"- **{key}:** {', '.join([item for item in value if item and item != 'Selecione'])}") # Filter here too for display
                     else:
                       st.write(f"- **{key}:** {value}")
             else:
                 st.info("Nenhuma característica estruturada significativa foi selecionada.")
         else:
              st.info("Nenhuma característica estruturada coletada.")


         st.write("**Observações Adicionais Fornecidas:**")
         st.info(observacoes if observacoes else 'Nenhuma observação adicional fornecida.')

    with st.expander("📍 Localização Exata Processada", expanded=True):
        tipo_loc = localizacao_exata.get('tipo', 'Não informada')
        st.write(f"**Tipo de Coleta:** {tipo_loc}")

        if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
            lat = localizacao_exata.get('latitude')
            lon = localizacao_exata.get('longitude')

            if lat is not None and lon is not None:
                 st.write(f"**Coordenadas:** `{lat}, {lon}`")

                 st.subheader("Visualizações de Mapa")

                 # 1. Google Maps Embed and Link (Combined)
                 embed_link_google = localizacao_exata.get('google_embed_link_gerado')
                 link_maps_google = localizacao_exata.get('google_maps_link_gerado')

                 # Display Google Maps section only if embed link was generated (requires key & API) OR direct link exists
                 if (embed_link_google and st.session_state.geocoding_api_key) or link_maps_google:
                     st.markdown("---")
                     st.write("**Google Maps:**")

                     if embed_link_google and st.session_state.geocoding_api_key:
                          try:
                              st.components.v1.html(
                                  f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link_google}" allowfullscreen></iframe>',
                                  height=470, # A bit taller to include border
                                  scrolling=False
                              )
                              st.info("ℹ️ Mapa Google Maps gerado usando a chave de Geocoding API. Requer Embed API habilitada.")
                          except Exception as e:
                               st.error(f"❌ Erro ao gerar mapa Google Maps incorporado: {e}")
                     elif st.session_state.geocoding_api_key:
                          st.warning("⚠️ Chave de Geocodificação fornecida, mas não foi possível gerar um mapa Google Maps incorporado. Verifique se a Embed API está habilitada no Google Cloud ou se a geocodificação automática falhou.")
                     elif not st.session_state.geocoding_api_key and link_maps_google:
                           st.info("ℹ️ Chave de API de Geocodificação não fornecida. Mapa Google Maps incorporado indisponível, apenas link direto.")
                     elif not st.session_state.geocoding_api_key and not link_maps_google:
                           st.warning("⚠️ Chave de API de Geocodificação não fornecida. Mapas Google indisponíveis.")


                     # Display the link below the embed if it exists
                     if link_maps_google:
                         st.write(f"[Abrir no Google Maps]({link_maps_google})")


                 # 2. OpenStreetMap Embed and Link (Combined)
                 st.markdown("---")
                 st.write("**OpenStreetMap:**")

                 # Generate the detailed OpenStreetMap embed iframe URL
                 # A reasonable delta for a small area view. Adjust zoom if needed.
                 delta = 0.005
                 bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
                 # Encode bbox and marker coordinates for the URL
                 encoded_bbox = urllib.parse.quote(bbox)
                 encoded_marker = urllib.parse.quote(f"{lat},{lon}")
                 osm_embed_url = f"https://www.openstreetmap.org/export/embed.html?bbox={encoded_bbox}&layer=mapnik&marker={encoded_marker}"


                 try:
                     # Use st.components.v1.html to embed the detailed OSM map
                     st.components.v1.html(
                         f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{osm_embed_url}" allowfullscreen></iframe>',
                         height=470, # A bit taller to include border
                         scrolling=False
                     )
                     st.info("ℹ️ Mapa OpenStreetMap detalhado incorporado (via openstreetmap.org).")
                 except Exception as embed_error:
                      st.error(f"❌ Erro ao gerar mapa OpenStreetMap incorporado: {embed_error}")


                 # Display the direct link below the embed
                 osm_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"
                 st.write(f"[Abrir no OpenStreetMap.org]({osm_link})")

                 # Add the simple st.map version back as well for diversity
                 st.markdown("---")
                 st.write("**OpenStreetMap (Mapa Simplificado Streamlit):**")
                 try:
                     map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                     st.map(map_data, zoom=18, use_container_width=True) # Correct parameter
                     st.info("ℹ️ Este é um mapa simplificado gerado diretamente no Streamlit usando dados OpenStreetMap.")
                 except Exception as map_error:
                      st.error(f"❌ Erro ao gerar visualização do mapa OpenStreetMap simplificado: {map_error}")


                 if localizacao_exata.get('endereco_formatado_api'):
                      st.markdown("---")
                      st.write(f"**Endereço Formatado (API):** {localizacao_exata.get('endereco_formatado_api')}")
                 if localizacao_exata.get('input_original'):
                     st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")


        elif tipo_loc == 'Descrição Manual Detalhada':
            st.write(f"**Descrição Manual:**")
            st.info(localizacao_exata.get('descricao_manual', 'Não informada'))
            if localizacao_exata.get('input_original'):
                st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")

        else: # Type "Não informada"
            st.warning("Localização exata não coletada de forma estruturada (coordenadas/link), nem descrição manual. O relatório dependerá da descrição e endereço base.")

        # Include reason for geocoding failure if applicable and not overridden by manual coords
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
             st.info(f"ℹ️ Nota: Motivo da falha na geocodificação automática ou input manual sem coordenadas: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")


    with st.expander("📷 Imagem da Denúncia (Referência Visual)", expanded=True):
         if imagem_data and 'bytes' in imagem_data:
              try:
                   # Use io.BytesIO to display the image from bytes
                   # Corrected deprecated parameter
                   st.image(io.BytesIO(imagem_data['bytes']), caption=imagem_data.get('filename', 'Imagem Carregada'), use_container_width=True)
                   st.write(f"**Nome do Arquivo:** {imagem_data.get('filename', 'Não informado')}")
                   st.write(f"**Tipo:** {imagem_data.get('type', 'Não informado')}")
                   st.info("Esta imagem é incluída no relatório para referência visual e será analisada pelo modelo Gemini Vision.")
              except Exception as e:
                   st.error(f"❌ Não foi possível exibir a imagem carregada: {e}")
         elif imagem_data and 'erro' in imagem_data:
              st.error(f"❌ Erro ao carregar a imagem: {imagem_data.get('erro', 'Detalhe desconhecido.')}")
         else:
              st.info("ℹ️ Nenhuma imagem foi carregada para esta denúncia.")

    with st.expander("🔍 Análise Visual por IA (Gemini Vision)", expanded=True):
        if imagem_data and 'bytes' in imagem_data and st.session_state.gemini_vision_model:
            analise_visual = dados_completos.get('analise_visual_ia', {}).get('analise_visual', 'Análise visual não realizada ou com erro.')
            st.write(analise_visual)
        elif not st.session_state.gemini_vision_model:
            st.warning("⚠️ Análise visual por IA indisponível (Modelo Gemini Vision não inicializado)")
        else:
            st.info("ℹ️ Nenhuma imagem fornecida para análise visual.")


    st.markdown("---")
    st.subheader("🤖 Análises Robóticas de IA (Google Gemini Text)")

    if st.session_state.gemini_model:
        with st.expander("🧠 Análise de Características e Observações (IA Gemini)", expanded=True):
            st.write(insights_ia.get('insights', 'Análise não realizada ou com erro.'))

        # Image analysis expander removed.

        with st.expander("🚦 Sugestão de Urgência (IA Gemini)", expanded=True):
            st.write(urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro.'))

        with st.expander("🛠️ Sugestões de Causa e Ação (IA Gemini)", expanded=True):
            st.write(sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões não geradas ou com erro.'))

        st.markdown("---")
        st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini)")
        st.write(resumo_ia.get('resumo_ia', 'Resumo não gerado ou com erro.'))
    else:
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chave Google API KEY não configurada ou modelo de texto não inicializado).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Option to restart the process
    if st.button("Iniciar Nova Denúncia"):
        # Clear the session state for a fresh start (except cache_resource objects)
        all_keys = list(st.session_state.keys())
        for key in all_keys:
             del st.session_state[key]
        st.rerun()

    # Option to display raw data (useful for debugging or export)
    with st.expander("🔌 Ver Dados Brutos (JSON)"):
        # Remove image bytes to avoid polluting the raw JSON, if present
        dados_para_json = dados_completos.copy()
        if 'buraco' in dados_para_json and 'imagem_denuncia' in dados_para_json['buraco']:
             img_data = dados_para_json['buraco']['imagem_denuncia']
             if img_data and 'bytes' in img_data:
                  # Create a copy and remove the 'bytes' key
                  img_data_copy = img_data.copy()
                  del img_data_copy['bytes']
                  dados_para_json['buraco']['imagem_denuncia'] = img_data_copy
                  st.info("Conteúdo da imagem (bytes) omitido do JSON bruto.")
             # else: If imagem_denuncia exists but doesn't have 'bytes' (e.g., error), keep as is

        st.json(dados_para_json)


# --- Run the application ---
# The main execution of the Streamlit script is managed by Streamlit itself.
# Functions are called based on the session state and user interactions.
# The code below is just to ensure the script runs as a Streamlit app.
if __name__ == "__main__":
    # Streamlit handles the main loop, no traditional main function needed
    # Code outside functions and at the top is executed on each rerun.
    # Flow is controlled by ifs/elifs based on st.session_state.step
    pass # Nothing to do here beyond what's already in the main body of the script
