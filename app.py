# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v4.1 - Fluxo CEP Otimizado)

Bem-vindo à versão visual do Krateras, agora com visão robótica e fluxo CEP mais rápido!
Interface amigável, inteligência da IA aprimorada e segurança de chaves mantida.

Tecnologias: Python, Streamlit, Google Gemini API (Text & Vision), Google Geocoding API, ViaCEP.
Objetivo: Coletar dados de denúncias de buracos com mais detalhes estruturados,
incluindo análise visual por IA de imagens, geocodificação, e gerar relatórios
detalhados, priorizados e com visualização de mapa.

Vamos juntos consertar essas ruas! Otimizando sistemas...
"""

import streamlit as st
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional
import re
import json
import pandas as pd
import io

# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Krateras 🚀✨🔒 - Denúncia de Buracos",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    background-color: #50E3C2; /* Verde Robô */
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #00B894; /* Verde Robô Escuro */
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
.st-emotion-cache-s5fjsg { /* Esta classe pode variar entre versões do streamlit, inspecione o elemento se o padding não funcionar */
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
if 'gemini_vision_model' not in st.session_state: # Novo estado para o modelo de visão
    st.session_state.gemini_vision_model = None
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None

# --- 🔑 Gerenciamento de Chaves Secretas (Streamlit Secrets) ---
# Utiliza o .streamlit/secrets.toml para carregar chaves

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    """
    Tenta obter as chaves de API do Google Gemini e Google Maps Geocoding de Streamlit Secrets.
    Retorna None se não encontradas.
    """
    # Assume que a mesma chave GOOGLE_API_KEY serve para modelos de texto e visão
    gemini_key = st.secrets.get('GOOGLE_API_KEY')
    geocoding_key = st.secrets.get('geocoding_api_key')

    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA (Gemini Text/Vision) estarão desabilitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática e mapa Google Embed estarão desabilitados.")
        st.info("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\nLembre-se que as APIs Geocoding e Gemini podem gerar custos. Ative-as no Google Cloud e verifique sua configuração de cobrança.")

    return gemini_key, geocoding_key

# --- Inicializar APIs (Cacheado para performance) ---

@st.cache_resource
def init_gemini_models(api_key: Optional[str]) -> tuple[Optional[genai.GenerativeModel], Optional[genai.GenerativeModel]]:
    """Inicializa os modelos Google Gemini (Texto e Visão) com cache."""
    if not api_key:
        st.error("❌ ERRO na Fábrica de Modelos: Chave de API Gemini não fornecida.")
        return None, None # Retorna None para ambos se a chave não for fornecida
    try:
        genai.configure(api_key=api_key)
        st.success("✅ Conexão com API Google Gemini estabelecida.")

        available_models = list(genai.list_models())
        text_models = [m for m in available_models if 'generateContent' in m.supported_generation_methods]

        # Selecionar modelo de Texto preferencial
        text_model_obj: Optional[genai.GenerativeModel] = None
        preferred_text_names = ['gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        for name in preferred_text_names:
            found_model = next((m for m in text_models if m.name.endswith(name)), None)
            if found_model:
                text_model_obj = genai.GenerativeModel(found_model.name)
                st.success(f"✅ Modelo de Texto Gemini selecionado: '{found_model.name.replace('models/', '')}'.")
                break
        if not text_model_obj:
            if text_models:
                # Fallback para o primeiro modelo de texto disponível
                text_model_obj = genai.GenerativeModel(text_models[0].name)
                st.warning(f"⚠️ AVISO: Modelos de texto Gemini preferenciais não encontrados. Usando fallback: '{text_models[0].name.replace('models/', '')}'.")
            else:
                 st.error("❌ ERRO na Fábrica de Modelos: Nenhum modelo de texto Gemini compatível encontrado na sua conta.")


        # Selecionar modelo de Visão preferencial (multimodal)
        vision_model_obj: Optional[genai.GenerativeModel] = None
        # Listar modelos com capacidade de processar 'image/jpeg' (proxy para modelos multimodais)
        # A detecção mais robusta seria inspecionar model.supported_generation_methods e model.input_token_limit
        # Mas esta abordagem por nome e filtro de mime_type geralmente funciona para os modelos comuns
        vision_models_candidates = [m for m in available_models if 'generateContent' in m.supported_generation_methods and any('image' in p.mime_type for p in m.supported_input_response_mime_types)]

        preferred_vision_names = ['gemini-1.5-flash-latest', 'gemini-1.5-pro-latest', 'gemini-pro-vision']
        for name in preferred_vision_names:
             # Verifica se o nome preferencial está na lista de candidatos visuais
             found_model = next((m for m in vision_models_candidates if m.name.endswith(name)), None)
             if found_model:
                vision_model_obj = genai.GenerativeModel(found_model.name)
                st.success(f"✅ Modelo de Visão Gemini selecionado: '{found_model.name.replace('models/', '')}'.")
                break

        if not vision_model_obj:
            st.warning("⚠️ AVISO: Nenhum modelo Gemini compatível com análise de imagem ('gemini-pro-vision', 'gemini-1.5-*') encontrado ou disponível. Análise visual por IA estará desabilitada. Verifique se ativou modelos como 'gemini-1.5-flash-latest' na sua conta.")


        return text_model_obj, vision_model_obj

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

@st.cache_data(show_spinner="⏳ Tentando localizar o buraco no mapa global via Geocoding API...")
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
            # Trata casos específicos comuns
            if status == 'ZERO_RESULTS':
                 error_msg = "Nenhum local exato encontrado para o endereço fornecido. Tente refinar o número ou referência, ou use a entrada manual de coordenadas/descrição."
            elif status == 'OVER_DAILY_LIMIT' or status == 'OVER_QUERY_LIMIT':
                 error_msg = "Limite de uso da API Geocoding excedido. Verifique sua configuração de cobrança ou espere."
            elif status == 'REQUEST_DENIED':
                 error_msg = "Requisição à API Geocoding negada. Verifique sua chave, restrições de API ou configurações de cobrança."

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
         return {"erro": f"Tempo limite excedido ({15}s) ao tentar geocodificar: {address}"}
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
def analisar_caracteristicas_e_observacoes_gemini(_caracteristicas: Dict[str, Any], _observacoes: str, _model: genai.GenerativeModel) -> Dict[str, Any]:
    """
    Utiliza o Gemini para analisar as características estruturadas e as observações
    e extrair insights estruturados.
    """
    if not _model:
        return {"insights": "🤖 Análise de descrição via IA indisponível (Motor Gemini Text offline)."}

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in _caracteristicas.items():
        if isinstance(value, list):
            caracteristicas_formatadas.append(f"- {key}: {', '.join(value) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto = "\n".join(caracteristicas_formatadas)

    observacoes_texto = _observacoes.strip() if _observacoes else "Nenhuma observação adicional fornecida."

    prompt = f"""
    Analise as seguintes características estruturadas e observações adicionais de uma denúncia de buraco.
    Seu objetivo é consolidar estas informações e extrair insights CRUCIAIS para um sistema de denúncias de reparo público.
    Formate a saída como um texto claro, usando marcadores (-) ou títulos para cada categoria de insight.
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
    - Sugestões de Ação/Recursos Mencionados pelo Denunciante (Extraído das Observações): [Se o usuário sugere o que fazer (tapa-buraco, recapeamento, sinalizar) ou causas percebidas *mencionadas nas observações*.]
    - Identificadores Visuais Adicionais (se descritos nas Observações): [Coisas únicas próximas que ajudam a achar o buraco (poste X, árvore Y, em frente a Z), *se mencionadas nas observações*.]
    - Palavras-chave Principais: [Liste 3-7 palavras-chave que capturem a essência da denúncia a partir de *todos* os dados de entrada.]

    Formate a resposta de forma limpa e estruturada.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"insights": f"❌ Análise de características/observações bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"insights": response.text.strip()}
    except Exception as e:
        return {"insights": f"❌ Erro ao analisar características/observações com IA: {e}"}

@st.cache_data(show_spinner="🧠 IA está vendo... Analisando a imagem do buraco...")
def analisar_imagem_gemini(_image_bytes: bytes, _mime_type: str, _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o modelo Gemini Vision para analisar uma imagem do buraco."""
    if not _model:
        return {"analise_imagem": "🤖 Análise visual por IA indisponível (Motor Gemini Vision offline)."}

    try:
        # Preparar a imagem para a API
        # genai.types.part() espera BytesIO ou bytes diretamente
        image_part = genai.types.part(mime_type=_mime_type, data=io.BytesIO(_image_bytes).getvalue())

        prompt = """
        Descreva o buraco nesta imagem. Foque nos seguintes aspectos visuais:
        - Tamanho aparente em relação a objetos de referência visíveis (carro, pneu, pessoa, largura da pista, etc.).
        - Profundidade aparente.
        - Forma e contorno do buraco.
        - Condições da superfície ao redor (asfalto bom/ruim, rachaduras, remendos).
        - Presença de água, detritos ou objetos dentro do buraco.
        - Ambiente da via (parece ser via principal, secundária, residencial, etc., se visível. Há carros, faixas, acostamento?).
        - Qualidades visuais que indicam perigo (ex: buraco grande na pista principal, buraco em curva, dificuldade visual para desviar, má iluminação aparente se for foto noturna).
        - Outros detalhes relevantes visíveis na imagem que ajudem a descrever o problema ou o local.

        Baseie sua análise SOMENTE no que você pode ver na imagem. Seja objetivo e descritivo.
        Formate a resposta como um texto narrativo claro.

        Análise Visual:
        """
        # A API generate_content aceita uma lista de partes (texto e imagem)
        response = _model.generate_content([prompt, image_part], safety_settings=SAFETY_SETTINGS)

        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"analise_imagem": f"❌ Análise de imagem bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}

        return {"analise_imagem": response.text.strip()}
    except Exception as e:
        return {"analise_imagem": f"❌ Erro ao analisar a imagem com IA: {e}. Verifique se o modelo Gemini selecionado suporta análise de imagem e se a imagem é válida."}


@st.cache_data(show_spinner="🧠 Calculando o Nível de Prioridade Robótica...")
def categorizar_urgencia_gemini(_dados_denuncia: Dict[str, Any], _insights_ia: Dict[str, Any], _analise_imagem_ia: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir uma categoria de urgência com base nos dados estruturados, observações, insights e análise de imagem."""
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini Text offline)."}

    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('buraco', {}).get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia.get('insights', 'Análise de insights não disponível.')
    analise_imagem_texto = _analise_imagem_ia.get('analise_imagem', 'Análise de imagem não disponível ou com erro.')

    localizacao_exata = _dados_denuncia.get('localizacao_exata_processada', {})
    tipo_loc = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')

    loc_contexto = f"Localização informada: Tipo: {tipo_loc}."
    if input_original_loc != 'Não informado.':
         loc_contexto += f" Detalhes originais: '{input_original_loc}'."

    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
        lat = localizacao_exata.get('latitude')
        lon = localizacao_exata.get('longitude')
        loc_contexto += f" Coordenadas: {lat}, {lon}. Link gerado: {localizacao_exata.get('google_maps_link_gerado', 'Não disponível')}."
    elif localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
         loc_contexto += f" (Nota: Tentativa de Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior', 'Motivo desconhecido')})"


    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            caracteristicas_formatadas.append(f"- {key}: {', '.join(value) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = f"""
    Com base em TODOS os dados da denúncia (características estruturadas, observações, insights da análise de texto e, se disponível, análise da imagem), sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade/tamanho (informado e analisado visualmente), profundidade (informada e analisada visualmente), PERIGOS POTENCIAIS e impactos mencionados, o CONTEXTO DA VIA (tipo de tráfego, contexto específico) e qualquer ADICIONAL visual da análise da imagem que reforce ou altere a percepção dos dados informados.

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem perigo aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, perigo CLARO e/ou frequente (risco de acidente mais sério, dano significativo a veículo, perigo para motos/bikes/pedestres), em via movimentada ou área de risco (escola, hospital, curva, subida/descida). Requer atenção RÁPIDA, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal, buraco em local de desvio impossível), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Dados da Denúncia:
    Localização Básica: Rua {_dados_denuncia.get('buraco', {}).get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {_dados_denuncia.get('buraco', {}).get('numero_proximo', 'Não informado')}. Cidade: {_dados_denuncia.get('buraco', {}).get('endereco', {}).get('cidade_buraco', 'Não informada')}, Estado: {_dados_denuncia.get('buraco', {}).get('endereco', {}).get('estado_buraco', 'Não informado')}.
    {loc_contexto}

    Características Estruturadas Fornecidas:
    {caracteristicas_texto_prompt}

    Observações Adicionais:
    "{observacoes}"

    Insights Extraídos pela Análise de Texto/Características:
    {insights_texto}

    Análise Visual da Imagem (se disponível):
    {analise_imagem_texto}


    Com base em TODOS estes dados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 2 frases) explicando POR QUE essa categoria foi sugerida, citando os elementos mais importantes dos dados fornecidos (incluindo análise visual se relevante).

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
             return {"urgencia_ia": f"❌ Sugestão de urgência bloqueada. Motivo: {block_reason}"}
        return {"urgencia_ia": response.text.strip()}
    except Exception as e:
        return {"urgencia_ia": f"❌ Erro ao sugerir urgência com IA: {e}"}


@st.cache_data(show_spinner="🧠 IA está pensando... Qual pode ser a causa e a melhor ação para este buraco?")
def sugerir_causa_e_acao_gemini(_dados_denuncia: Dict[str, Any], _insights_ia: Dict[str, Any], _analise_imagem_ia: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir possíveis causas do buraco e ações de reparo com base nos dados, insights e análise de imagem."""
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini Text offline)."}

    caracteristicas = _dados_denuncia.get('buraco', {}).get('caracteristicas_estruturadas', {})
    observacoes = _dados_denuncia.get('buraco', {}).get('observacoes_adicionais', 'Sem observações.')
    insights_texto = _insights_ia.get('insights', 'Análise de insights não disponível.')
    analise_imagem_texto = _analise_imagem_ia.get('analise_imagem', 'Análise de imagem não disponível ou com erro.')

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            caracteristicas_formatadas.append(f"- {key}: {', '.join(value) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = f"""
    Com base nos dados fornecidos pelo denunciante (características estruturadas, observações) e nos insights extraídos pelas análises de IA (texto e, se disponível, imagem), tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico (ex: chuva forte recente, desgaste do asfalto pelo tempo/tráfego, problema na drenagem subterrânea, afundamento devido a reparo anterior, obra mal feita na região). Baseie-se em todos os dados disponíveis, incluindo o contexto da via e análise visual.
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via, reparo na rede de água/esgoto). Baseie-se na severidade, perigos, o que foi observado/analisado (texto e visual) e as possíveis causas.
    Baseie suas sugestões EXCLUSIVAMENTE nas informações e análises disponíveis. Se os dados não derem pistas suficientes, indique "Não especificado/inferido nos dados". Seja lógico e prático.

    Informações Relevantes da Denúncia:
    Características Estruturadas:
    {caracteristicas_texto_prompt}
    Observações Adicionais: "{observacoes}"
    Insights Extraídos pela Análise de Texto/Características:
    {insights_texto}
    Análise Visual da Imagem (se disponível):
    {analise_imagem_texto}

    Formato de saída:
    Possíveis Causas Sugeridas: [Lista de causas sugeridas baseadas nos dados ou 'Não especificado/inferido nos dados']
    Sugestões de Ação/Reparo Sugeridas: [Lista de ações sugeridas baseadas nos dados/insights/análise visual ou 'Não especificado/inferido nos dados']
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"sugestao_acao_ia": f"❌ Sugestão de causa/ação bloqueada. Motivo: {block_reason}"}
        return {"sugestao_acao_ia": response.text.strip()}
    except Exception as e:
        return {"sugestao_acao_ia": f"❌ Erro ao sugerir causa/ação com IA: {e}"}

@st.cache_data(show_spinner="🧠 Compilando o Relatório Final Robótico e Inteligente com IA Gemini...")
def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para gerar um resumo narrativo inteligente da denúncia completa, incluindo dados estruturados e análises de IA (texto e imagem)."""
    if not _model:
        return {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini Text offline)."}

    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    caracteristicas = buraco.get('caracteristicas_estruturadas', {})
    observacoes = buraco.get('observacoes_adicionais', 'Nenhuma observação adicional fornecida.')
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    insights_ia = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise da descrição/características não disponível ou com erro.')
    analise_imagem_ia = _dados_denuncia_completa.get('analise_imagem_ia', {}).get('analise_imagem', 'Análise visual por IA não disponível ou com erro.')
    urgencia_ia = dados_completos.get('urgencia_ia', {}).get('urgencia_ia', 'Sugestão de urgência não disponível ou com erro.') # Corrigido para usar dados_completos
    sugestao_acao_ia = dados_completos.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', 'Sugestões de causa/ação não disponíveis ou com erro.') # Corrigido para usar dados_completos

    loc_info_resumo = "Localização exata não especificada ou processada."
    tipo_loc_processada = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')

    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         lat = localizacao_exata.get('latitude')
         lon = localizacao_exata.get('longitude')
         link_gerado = localizacao_exata.get('google_maps_link_gerado', 'Não disponível')
         loc_info_resumo = f"Localização Exata: Coordenadas {lat}, {lon} (Obtida via: {tipo_loc_processada.replace(' (API)', ' API').replace('Manual', 'Manual').replace('Fornecidas/Extraídas', 'Manual')}). Link Google Maps: {link_gerado}."
         if input_original_loc != 'Não informado.':
             loc_info_resumo += f" (Input original: '{input_original_loc}')"

    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização via descrição manual detalhada: '{localizacao_exata.get('descricao_manual', 'Não informada')}'. (Input original: '{input_original_loc}')"

    elif input_original_loc != 'Não informado.' and tipo_loc_processada == 'Não informada':
         loc_info_resumo = f"Localização informada (tipo não detectado): '{input_original_loc}'."

    if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
         loc_info_resumo += f" (Nota: Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')})"

    # Formatar as características estruturadas para o prompt
    caracteristicas_formatadas = []
    for key, value in caracteristicas.items():
        if isinstance(value, list):
            caracteristicas_formatadas.append(f"- {key}: {', '.join(value) if value else 'Não informado'}")
        else:
            caracteristicas_formatadas.append(f"- {key}: {value if value and value != 'Selecione' else 'Não informado'}")
    caracteristicas_texto_prompt = "\n".join(caracteristicas_formatadas)


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 10-12 frases) para a seguinte denúncia de buraco no aplicativo Krateras.
    Este resumo deve ser formal, objetivo e útil para equipes de manutenção ou gestão pública.
    Combine os dados estruturados, as observações adicionais, a localização exata processada e os resultados das análises de IA (texto e, se disponível, imagem).

    Inclua:
    - Quem denunciou (Nome, Cidade de Residência).
    - Onde está o buraco (Rua, Número Próximo/Referência, Bairro, Cidade do Buraco, Estado do Buraco, CEP se disponível).
    - A localização EXATA processada (mencione como foi obtida e os dados relevantes).
    - O lado da rua.
    - As características estruturadas fornecidas (Tamanho, Perigo, Profundidade, Água, Tráfego, Contexto da Via).
    - Informações adicionais importantes das Observações.
    - Os principais pontos da Análise de Texto/Características de IA (Perigos Potenciais, Contexto Adicional).
    - Principais pontos da Análise Visual de Imagem de IA (se disponível).
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
    {insights_ia}

    Análise Visual da Imagem de IA:
    {analise_imagem_ia}

    Sugestão de Urgência pela IA:
    {urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não disponível ou com erro.')}

    Sugestões de Causa e Ação pela IA:
    {sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões não geradas ou com erro.')}


    Gere o resumo em português. Comece com "Relatório Krateras: Denúncia de buraco..." ou algo similar. Use linguagem clara e direta.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"resumo_ia": f"❌ Geração de resumo bloqueada. Motivo: {block_reason}"}
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
        'collect_buraco_address_cep', # Pode pular dependendo da escolha
        'collect_buraco_address_manual', # Pode pular dependendo da escolha
        'collect_buraco_details', # Unifica a coleta do resto e a geocodificação/localização manual/imagem
        'processing_ia',
        'show_report'
    ]
    try:
        current_index = steps.index(st.session_state.step)
        if current_index < len(steps) - 1:
            st.session_state.step = steps[current_index + 1]
            # st.rerun() # Removido st.rerun() explícito aqui para ver se melhora o fluxo CEP
            # Streamlit já reruns após callback/state change
    except ValueError:
        # Caso o passo atual não esteja na lista (erro ou estado inicial)
        st.session_state.step = steps[0]
        # st.rerun() # Removido st.rerun() explícito
    # Um rerun ocorrerá naturalmente após a execução da função next_step() se for chamada por um callback.
    # Se for chamada diretamente, talvez precise reavaliar. No fluxo atual, é chamada por botões ou após processamento.


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
             # Lógica para pular passos de CEP/Manual se não foram usados
             if st.session_state.step == 'collect_buraco_details':
                  # Se chegamos aqui diretamente do método, voltamos para lá
                  # Verifica qual foi o método original de coleta de endereço
                  endereco_coletado_via = st.session_state.get('endereco_coletado_via')
                  if endereco_coletado_via == 'cep':
                      st.session_state.step = 'collect_buraco_address_cep'
                  elif endereco_coletado_via == 'manual':
                      st.session_state.step = 'collect_buraco_address_manual'
                  else: # Fallback seguro se não soubermos a origem
                       st.session_state.step = steps[current_index - 1] # Volta para address_method
             elif st.session_state.step == 'collect_buraco_address_cep' or st.session_state.step == 'collect_buraco_address_manual':
                  st.session_state.step = 'collect_buraco_address_method'
             else:
                  st.session_state.step = steps[current_index - 1]

             st.rerun() # Manter rerun aqui para garantir que a navegação de volta funciona
    except ValueError:
         st.session_state.step = steps[0]
         st.rerun() # Manter rerun aqui


# --- Layout Principal da Aplicação ---

st.title("Krateras 🚀✨🔒")
st.subheader("O Especialista Robótico de Denúncia de Buracos")

# --- Fluxo da Aplicação baseado no Estado ---

if st.session_state.step == 'start':
    st.write("""
    Olá! Krateras v4.1 entrando em órbita com **Visão Robótica** e fluxo otimizado! Sua missão, caso aceite: denunciar buracos na rua
    para que possam ser consertados. A segurança dos seus dados e a precisão da denúncia
    são nossas prioridades máximas.

    Utilizamos inteligência artificial (Google Gemini Text & Vision) e APIs de localização (Google Geocoding,
    ViaCEP) para coletar, analisar (inclusive imagens!) e gerar um relatório detalhado para as autoridades competentes.

    Fui criado com o que há de mais avançado em Programação, IA (Análise de Texto e Visual!), Design Inteligente,
    Matemática e Lógica Inabalável. Com acesso seguro às APIs, sou imparável.

    Clique em Iniciar para começarmos a coleta de dados.
    """)

    st.info("⚠️ Suas chaves de API do Google (Gemini e Geocoding) devem ser configuradas nos Streamlit Secrets (`.streamlit/secrets.toml`) para que a IA e a geocodificação automática funcionem corretamente e de forma segura. A API Gemini pode precisar de modelos multimodais (`gemini-pro-vision`, `gemini-1.5-flash-latest`, etc.) habilitados para a análise de imagens.")


    if st.button("Iniciar Missão Denúncia!"):
        # Carregar chaves e inicializar APIs antes de coletar dados
        gemini_api_key, geocoding_api_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_api_key # Armazena a chave de geocoding no estado
        st.session_state.gemini_model, st.session_state.gemini_vision_model = init_gemini_models(gemini_api_key) # Inicializa os modelos Gemini (cacheado)
        st.session_state.api_keys_loaded = True # Marca que tentamos carregar as chaves
        next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Formulário para coletar dados do denunciante
    with st.form("form_denunciante"):
        nome = st.text_input("Seu nome completo:", key='nome_denunciante')
        idade = st.number_input("Sua idade (opcional, aproximada 😉):", min_value=0, max_value=120, value=None, help="Deixe em branco se não quiser informar.", key='idade_denunciante_input')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", key='cidade_residencia_denunciante')

        submitted = st.form_submit_button("Avançar (Dados Denunciante)")

        if submitted:
            if not nome or not cidade_residencia:
                st.error("❗ Nome e Cidade de residência são campos obrigatórios. Por favor, preencha-os.")
            else:
                st.session_state.denuncia_completa['denunciante'] = {
                    "nome": nome.strip(),
                    "idade": st.session_state.idade_denunciante_input if st.session_state.idade_denunciante_input is not None and st.session_state.idade_denunciante_input > 0 else None, # Store as None if 0 or None
                    "cidade_residencia": cidade_residencia.strip()
                }
                st.success(f"Olá, {nome}! Dados coletados. Preparando para dados do buraco...")
                next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_method':
    st.header("--- 🚧 Detalhes do Buraco (Nosso Alvo!) ---")
    st.subheader("Como identificar a rua do buraco?")

    # Armazenar a escolha do método diretamente no estado para usar no botão Voltar
    st.session_state.endereco_address_method_choice = st.radio(
        "Escolha o método:",
        ('Digitar nome manualmente', 'Buscar por CEP'),
        key='endereco_method' # Keep key for persistence if needed elsewhere
    )

    # Use um botão para confirmar a escolha e mover para o próximo sub-step
    if st.button("Selecionar Método"):
         if st.session_state.endereco_address_method_choice == 'Digitar nome manualmente':
              st.session_state.endereco_coletado_via = 'manual' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_manual'
         elif st.session_state.endereco_address_method_choice == 'Buscar por CEP':
              st.session_state.endereco_coletado_via = 'cep' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_cep'
         st.rerun() # Força a atualização para o próximo passo

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_cep':
    st.header("--- 🚧 Detalhes do Buraco (Busca por CEP) ---")
    st.write("Digite o CEP do local do buraco.")

    # Inicializa estados para o CEP
    if 'dados_cep_validos' not in st.session_state:
         st.session_state.dados_cep_validos = None
    if 'cep_error' not in st.session_state:
         st.session_state.cep_error = False
    if 'cep_buraco' not in st.session_state: # Garante que o input text tem um valor inicial
         st.session_state.cep_buraco = ''


    with st.form("form_cep"):
        cep_input = st.text_input("Digite o CEP (apenas números):", max_chars=8, key='cep_buraco')
        buscar_button = st.form_submit_button("Buscar CEP")

        # --- Lógica de busca e exibição DENTRO do form_submit ---
        if buscar_button:
            if not cep_input:
                st.error("❗ Por favor, digite um CEP.")
                st.session_state.cep_error = True
                st.session_state.dados_cep_validos = None # Limpa dados válidos em caso de input vazio
            else:
                dados_cep = buscar_cep(cep_input.strip())

                if 'erro' in dados_cep:
                    st.error(f"❌ Falha na busca por CEP: {dados_cep['erro']}")
                    st.session_state.cep_error = True # Marca que houve erro no CEP
                    st.session_state.dados_cep_validos = None # Limpa dados válidos
                else:
                    # Sucesso: Armazena dados válidos e exibe IMEDIATAMENTE
                    st.session_state.dados_cep_validos = dados_cep
                    st.session_state.cep_error = False
                    st.success("✅ Endereço Encontrado (ViaCEP):")
                    st.write(f"**Rua:** {dados_cep.get('logradouro', 'Não informado')}")
                    st.write(f"**Bairro:** {dados_cep.get('bairro', 'Não informado')}")
                    st.write(f"**Cidade:** {dados_cep.get('localidade', 'Não informado')}")
                    st.write(f"**Estado:** {dados_cep.get('uf', 'Não informado')}")
                    st.write(f"**CEP:** {cep_input.strip()}")
                    st.info("Por favor, confirme se estes dados estão corretos. Se não, use o botão 'Corrigir Endereço Manualmente'.")

                    # Preenche os dados do buraco no estado AQUI para que "Confirmar" possa usá-los
                    st.session_state.denuncia_completa['buraco'] = {
                        'endereco': {
                            'rua': st.session_state.dados_cep_validos.get('logradouro', ''),
                            'bairro': st.session_state.dados_cep_validos.get('bairro', ''),
                            'cidade_buraco': st.session_state.dados_cep_validos.get('localidade', ''),
                            'estado_buraco': st.session_state.dados_cep_validos.get('uf', '')
                        },
                        'cep_informado': cep_input.strip() # Garante que o CEP digitado é armazenado
                    }
                    # Não precisa de st.rerun() explícito aqui. O form submit já causa um rerun.
                    # A exibição dos botões de ação e a persistência do endereço vêm do estado
                    # na próxima execução do script após o submit.


    # --- Lógica para exibir botões de ação FORA do form, baseada no estado após a busca ---
    # Exibe botões de ação APENAS se uma busca foi feita (cep_buraco existe)
    # E a busca foi bem-sucedida (dados_cep_validos não é None e não houve erro)
    if st.session_state.get('cep_buraco') and not st.session_state.get('cep_error') and st.session_state.get('dados_cep_validos'):
        st.markdown("---") # Separador visual para os botões de ação
        col1, col2 = st.columns(2)
        with col1:
            # Botão para confirmar e ir para detalhes (número, descrição)
            if st.button("Confirmar Endereço e Avançar"):
                 next_step()

        with col2:
            # Botão para corrigir manualmente (volta para entrada manual)
            if st.button("Corrigir Endereço Manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.session_state.dados_cep_validos = None # Limpa dados CEP ao ir para manual
                 st.session_state.cep_error = False # Limpa erro
                 # Limpa o CEP input para o caso de voltar para CEP depois
                 st.session_state.cep_buraco = ''
                 st.rerun()

    elif st.session_state.get('cep_error'): # Se houve erro na busca por CEP
        st.markdown("---")
        st.warning("Não foi possível obter o endereço por CEP.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Tentar novamente por CEP"):
                 st.session_state.cep_error = False # Reseta o erro para tentar novamente
                 st.session_state.cep_buraco = '' # Limpa o input para uma nova tentativa
                 st.session_state.dados_cep_validos = None # Garante que dados validos estao limpos
                 st.rerun() # Força reload para resetar o formulário de CEP
        with col2:
            if st.button("Digitar endereço manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.session_state.dados_cep_validos = None # Limpa dados CEP ao ir para manual
                 st.session_state.cep_error = False # Limpa erro
                 st.session_state.cep_buraco = '' # Limpa o CEP input
                 st.rerun()
    # Note: Se o formulário nunca foi submetido (cep_buraco não existe) ou o input estava vazio (tratado no if buscar_button),
    # esta parte fora do form não exibirá nada, o que é o comportamento esperado.

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_manual':
    st.header("--- 🚧 Detalhes do Buraco (Entrada Manual) ---")
    st.write("Digite os dados do endereço do buraco manualmente.")

    # Use os dados do CEP pré-preenchidos se vier dessa rota, ou inicialize vazio
    endereco_inicial = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})

    with st.form("form_manual_address"):
        rua_manual = st.text_input("Nome completo da rua:", value=endereco_inicial.get('rua', ''), key='rua_manual_buraco')
        bairro_manual = st.text_input("Bairro onde está o buraco (opcional):", value=endereco_inicial.get('bairro', ''), key='bairro_manual_buraco')
        cidade_manual = st.text_input("Cidade onde está o buraco:", value=endereco_inicial.get('cidade_buraco', ''), key='cidade_manual_buraco')
        estado_manual = st.text_input("Estado (UF) onde está o buraco:", value=endereco_inicial.get('estado_buraco', ''), max_chars=2, key='estado_manual_buraco')

        submitted = st.form_submit_button("Avançar (Endereço Manual)")

        if submitted:
            if not rua_manual or not cidade_manual or not estado_manual:
                st.error("❗ Rua, Cidade e Estado são campos obrigatórios para o endereço do buraco.")
            else:
                # Garante que 'buraco' existe antes de adicionar/atualizar 'endereco'
                if 'buraco' not in st.session_state.denuncia_completa:
                    st.session_state.denuncia_completa['buraco'] = {}

                st.session_state.denuncia_completa['buraco']['endereco'] = {
                    'rua': rua_manual.strip(),
                    'bairro': bairro_manual.strip(),
                    'cidade_buraco': cidade_manual.strip(),
                    'estado_buraco': estado_manual.strip().upper() # Guarda em maiúsculas
                }
                # Remove dados de CEP se veio da busca e agora foi corrigido manualmente
                if 'cep_informado' in st.session_state.denuncia_completa['buraco']:
                     del st.session_state.denuncia_completa['buraco']['cep_informado']

                next_step() # Move para a próxima etapa (coleta de detalhes)

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_details':
    st.header("--- 🚧 Detalhes Finais do Buraco ---")
    st.subheader("Informações cruciais para a localização e análise!")

    # Exibe o endereço básico já coletado para referência
    endereco_basico = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})
    st.write(f"Endereço Base: Rua **{endereco_basico.get('rua', 'Não informada')}**, Cidade: **{endereco_basico.get('cidade_buraco', 'Não informada')}** - **{endereco_basico.get('estado_buraco', 'Não informado')}**")
    if endereco_basico.get('bairro'):
         st.write(f"Bairro: **{endereco_basico.get('bairro')}**")
    if st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado'):
         st.write(f"CEP informado: **{st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado')}**")

    st.markdown("---") # Separador visual

    with st.form("form_buraco_details"):
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
        As coordenadas ou um link aparecerão.</p>
        <p>Alternativamente, uma DESCRIÇÃO MUITO DETALHADA do local EXATO no mapa (Ex: 'Exatamente 5 metros à esquerda do poste Y, em frente ao portão azul do nº 456').</p>
        """, unsafe_allow_html=True)
        localizacao_manual_input = st.text_input("Insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO DETALHADA manual:", key='localizacao_manual')

        st.subheader("📷 Foto do Buraco (Opcional, mas a IA Robótica adoraria ver!)")
        st.write("Uma boa foto ajuda MUITO na análise! Por favor, envie uma imagem clara e com boa resolução, mostrando o buraco e, se possível, algo para dar noção de tamanho (ex: um pneu, um sapato, ou a largura da rua).")
        uploaded_image = st.file_uploader("Carregar Imagem do Buraco:", type=['jpg', 'jpeg', 'png', 'webp'], key='uploaded_image_buraco')
        if uploaded_image:
             st.info(f"Imagem '{uploaded_image.name}' pronta para análise.")


        st.subheader("📝 Observações Adicionais")
        st.write("Algo mais a acrescentar que não foi coberto pelas opções? Detalhes como: 'problema recorrente (há quanto tempo?)', 'surgiu depois da última chuva', 'muito difícil desviar à noite', 'causou X dano ao meu carro', 'vi um acidente aqui':")
        observacoes_adicionais = st.text_area("Suas observações:", key='observacoes_buraco')


        submitted = st.form_submit_button("Enviar Denúncia para Análise Robótica!")

        if submitted:
            # Validar campos obrigatórios
            required_selects = {'tamanho_buraco': 'Tamanho Estimado', 'perigo_buraco': 'Perigo Estimado', 'profundidade_buraco': 'Profundidade Estimada', 'agua_buraco': 'Presença de Água', 'trafego_buraco': 'Tráfego Estimado'}
            missing_selects = [label for key, label in required_selects.items() if st.session_state[key] == 'Selecione']

            if not numero_proximo or not lado_rua or not observacoes_adicionais:
                 st.error("❗ Número próximo/referência, Lado da rua e Observações adicionais são campos obrigatórios.")
            elif missing_selects:
                 st.error(f"❗ Por favor, selecione uma opção para os seguintes campos: {', '.join(missing_selects)}.")
            else:
                # Garante que 'buraco' existe no estado (já deve existir dos passos anteriores)
                if 'buraco' not in st.session_state.denuncia_completa:
                    st.session_state.denuncia_completa['buraco'] = {}

                # Armazena os dados do formulário no estado
                st.session_state.denuncia_completa['buraco'].update({
                    'numero_proximo': numero_proximo.strip(),
                    'lado_rua': lado_rua.strip(),
                    'caracteristicas_estruturadas': {
                         'Tamanho Estimado': tamanho,
                         'Perigo Estimado': perigo,
                         'Profundidade Estimada': profundidade,
                         'Presença de Água/Alagamento': agua,
                         'Tráfego Estimado na Via': trafego,
                         'Contexto da Via': contexto_via if contexto_via else [] # Garante que é lista, pode ser vazia
                    },
                    'observacoes_adicionais': observacoes_adicionais.strip()
                    # Endereço base e CEP já devem estar no estado de passos anteriores
                })

                # --- Processar Imagem Upload ---
                # Limpa dados da imagem anterior antes de processar a nova
                st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = None
                if uploaded_image is not None:
                    try:
                        # Leia os bytes da imagem
                        image_bytes = uploaded_image.getvalue()
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {
                            "filename": uploaded_image.name,
                            "type": uploaded_image.type,
                            "bytes": image_bytes # Armazena os bytes
                        }
                        st.info("✅ Imagem carregada com sucesso para análise!")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar a imagem: {e}. Por favor, tente novamente.")
                        st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {"erro": f"Erro ao carregar: {e}"}


                # --- Tentar Geocodificação Automática ---
                # Limpa dados de localização processada anterior
                st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"}
                tentou_geocodificar = False
                geocodificacao_sucesso = False
                motivo_falha_geo = "Não tentado ou motivo não registrado" # Default

                rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
                cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
                estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')

                # Tenta usar o numero_proximo/referencia para geocodificar
                num_referencia_geo = numero_proximo.strip()

                tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and num_referencia_geo and cidade_buraco and estado_buraco)

                if tem_dados_para_geo:
                    st.info("✅ Chave de Geocodificação e dados básicos de endereço completos encontrados. Tentando gerar o link do Google Maps automaticamente...")
                    tentou_geocodificar = True
                    geo_resultado = geocodificar_endereco(
                        rua_buraco,
                        num_referencia_geo, # Usa o número/referência como base para geocodificação
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
                            "google_embed_link_gerado": geo_resultado.get('google_embed_link_gerado'),
                            "input_original": num_referencia_geo # Referencia qual input foi usado para geocodificar
                        }
                        st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                    else:
                        st.warning(f"❌ Falha na Geocodificação automática: {geo_resultado['erro']}")
                        motivo_falha_geo = geo_resultado.get('erro', 'Motivo desconhecido')


                # --- Processar Coordenadas/Link/Descrição Manual (se fornecido) ---
                # Isto é feito *independente* do sucesso da geocodificação automática,
                # pois a entrada manual pode ser mais precisa ou corrigir a automática.
                localizacao_manual_input_processed = localizacao_manual_input.strip()
                if localizacao_manual_input_processed:
                     lat: Optional[float] = None
                     lon: Optional[float] = None
                     tipo_manual_processado = "Descrição Manual Detalhada"
                     input_original_manual = localizacao_manual_input_processed

                     # Regex para tentar achar coordenadas em diferentes formatos (Lat,Long ou em links comuns)
                     # Tenta cobrir "lat,long", "@lat,long" em links, "lat long"
                     # Regex mais robusta: permite espaços ou vírgulas como separadores
                     match_coords = re.search(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)', input_original_manual)
                     if match_coords:
                         try:
                             teste_lat = float(match_coords.group(1))
                             teste_lon = float(match_coords.group(2))
                             # Validação básica de coordenadas
                             if -90 <= teste_lat <= 90 and -180 <= teste_lon <= 180:
                                 lat = teste_lat
                                 lon = teste_lon
                                 tipo_manual_processado = "Coordenadas Fornecidas/Extraídas Manualmente"
                                 st.info("✅ Coordenadas válidas detectadas no input manual!")
                             else:
                                 st.warning("⚠️ Parece um formato de coordenadas, mas fora da faixa esperada (-90 a 90 Latitude, -180 a 180 Longitude). Tratando como descrição detalhada.")
                         except ValueError:
                            # Ignore, continue para a próxima tentativa
                             pass # Não é um número float válido, tratar como descrição

                     if lat is None and input_original_manual.startswith("http"):
                          st.info("ℹ️ Entrada manual é um link. Tentando extrair coordenadas (sujeito a formato do link)...")
                          # Tenta regex para links Google Maps (com @lat,long) ou search (com ?,query=lat,long)
                          match_maps_link = re.search(r'(?:/@|/search/\?api=1&query=)(-?\d+\.?\d*),(-?\d+\.?\d*)', input_original_manual)
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
                                       st.warning("⚠️ Coordenadas extraídas do link no input manual fora da faixa esperada. Tratando como descrição detalhada.")
                              except ValueError:
                                 st.info("ℹ️ Valores no link não parecem coordenadas válidas. Tratando como descrição.")
                          else:
                               st.info("ℹ️ Não foi possível extrair coordenadas reconhecíveis do link do Maps fornecido manualmente.")
                               # Se não extraiu coords do link, trata como descrição manual
                               lat = None
                               lon = None
                               tipo_manual_processado = "Descrição Manual Detalhada"
                     elif lat is None: # Se não achou coords e não é link, é descrição manual
                         st.info("ℹ️ Entrada manual não detectada como coordenadas ou link. Tratando como descrição detalhada.")
                         tipo_manual_processado = "Descrição Manual Detalhada"


                     # Armazenar o resultado do input manual.
                     # Se coordenadas foram encontradas manualmente, elas *substituem* o resultado da geocodificação automática.
                     # A entrada manual com coordenadas TEM PREFERÊNCIA sobre a geocodificação automática.
                     if lat is not None and lon is not None:
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": tipo_manual_processado, # Será Coordenadas Fornecidas/Extraídas ou Coordenadas Extraídas de Link
                              "input_original": input_original_manual,
                              "latitude": lat,
                              "longitude": lon,
                              "google_maps_link_gerado": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                              "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat},{lon}" if st.session_state.geocoding_api_key else None # Tenta gerar embed link se tiver chave
                         }
                         # Sinaliza sucesso para fins de exibir mapa/link
                         geocodificacao_sucesso = True
                         st.success(f"✅ Localização Exata Obtida (via Input Manual - {tipo_manual_processado})!")
                     elif input_original_manual: # Se há input manual, mas não extraiu Lat/Long, guarda como descrição manual
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": "Descrição Manual Detalhada",
                              "input_original": input_original_manual,
                              "descricao_manual": input_original_manual
                         }
                         # Não considera sucesso para fins de exibir mapa/link baseado em coords
                         geocodificacao_sucesso = False
                         st.info("ℹ️ Localização exata processada como Descrição Manual Detalhada.")
                     # else: Se input manual está vazio, mantém o que veio da geocodificação ou o default "Não informada"


                # Se NÃO HOUVE input manual com coords E a geocodificação automática falhou, registra o motivo
                # e garante que o tipo é "Não informada" se não houver nem descrição manual.
                loc_tipo_apos_processamento_manual = st.session_state.denuncia_completa['localizacao_exata_processada'].get('tipo')

                if loc_tipo_apos_processamento_manual not in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Coordenadas Extraídas de Link (Manual)', 'Geocodificada (API)']:
                     # Se a localização ainda não é baseada em coordenadas (veio de geo que falhou, ou não tentou geo, ou é descrição manual)
                     if tentou_geocodificar and motivo_falha_geo != "Não tentado ou motivo não registrado":
                           # Se tentou geocodificar e falhou, registra o motivo, a menos que uma descrição manual já tenha sido definida
                           if loc_tipo_apos_processamento_manual != 'Descrição Manual Detalhada':
                                st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = motivo_falha_geo
                           elif 'motivo_falha_geocodificacao_anterior' not in st.session_state.denuncia_completa['localizacao_exata_processada']:
                                # Se é descrição manual, mas a geo falhou antes, registra o motivo da falha da geo
                                st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = motivo_falha_geo
                     elif not st.session_state.geocoding_api_key:
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Chave de API de Geocodificação não fornecida."
                     elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Dados insuficientes para Geocodificação (requer Rua, Número Próximo/Referência, Cidade, Estado)."


                     # Se a localização processada ainda é "Não informada" após tudo, exibe aviso
                     if loc_tipo_apos_processamento_manual == "Não informada":
                          st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi fornecida ou detectada, nem descrição manual. O relatório dependerá apenas do endereço base e observações.")
                     # Se é Descrição Manual, exibe um aviso diferente
                     # Já coberto pela info acima, mas mantido por clareza
                     # elif loc_tipo_apos_processamento_manual == "Descrição Manual Detalhada":
                     #     st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi detectada. O relatório usará a descrição manual.")


                # Tudo processado, avança para a etapa de análise de IA
                next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa os dados, a imagem (se houver) e gera o relatório com a inteligência do Google Gemini.")

    buraco_data = st.session_state.denuncia_completa.get('buraco', {})
    caracteristicas = buraco_data.get('caracteristicas_estruturadas', {})
    observacoes = buraco_data.get('observacoes_adicionais', '')
    imagem_data = buraco_data.get('imagem_denuncia')

    # Resetar resultados de IA antes de rodar para garantir que não estamos usando resultados de um rerun anterior sem dados
    st.session_state.denuncia_completa['insights_ia'] = {}
    st.session_state.denuncia_completa['analise_imagem_ia'] = {}
    st.session_state.denuncia_completa['urgencia_ia'] = {}
    st.session_state.denuncia_completa['sugestao_acao_ia'] = {}
    st.session_state.denuncia_completa['resumo_ia'] = {}


    # Rodar análise de texto/características
    if st.session_state.gemini_model:
        st.session_state.denuncia_completa['insights_ia'] = analisar_caracteristicas_e_observacoes_gemini(
            caracteristicas,
            observacoes,
            st.session_state.gemini_model
        )
    else:
        st.warning("⚠️ Modelo Google Gemini Text não inicializado. Análise de características/observações por IA desabilitada.")
        st.session_state.denuncia_completa['insights_ia'] = {"insights": "Análise de características/observações via IA indisponível."}


    # Rodar análise de imagem (SE houver imagem E modelo de visão disponível)
    if imagem_data and 'bytes' in imagem_data and st.session_state.gemini_vision_model:
        st.info("🤖 Analisando a imagem do buraco com Visão Robótica...")
        # Passa os bytes e o tipo da imagem carregada
        st.session_state.denuncia_completa['analise_imagem_ia'] = analisar_imagem_gemini(
            imagem_data['bytes'],
            imagem_data['type'],
            st.session_state.gemini_vision_model
        )
    elif imagem_data and 'bytes' in imagem_data and not st.session_state.gemini_vision_model:
        st.warning("⚠️ Imagem carregada, mas Modelo Google Gemini Vision não inicializado ou compatível. Análise visual por IA desabilitada.")
        st.session_state.denuncia_completa['analise_imagem_ia'] = {"analise_imagem": "Análise visual por IA indisponível (Modelo Gemini Vision offline ou modelo incompatível)."}
    elif not (imagem_data and 'bytes' in imagem_data):
        st.info("ℹ️ Nenhuma imagem fornecida para análise visual por IA.")
        st.session_state.denuncia_completa['analise_imagem_ia'] = {"analise_imagem": "Nenhuma imagem fornecida para análise."}


    # Rodar categorização de urgência
    if st.session_state.gemini_model:
        st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.denuncia_completa['insights_ia'],
            st.session_state.denuncia_completa.get('analise_imagem_ia', {}), # Passa análise de imagem (pode estar vazia)
            st.session_state.gemini_model
        )
    else:
        st.warning("⚠️ Modelo Google Gemini Text não inicializado. Sugestão de urgência por IA desabilitada.")
        st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Sugestão de urgência via IA indisponível."}


    # Rodar sugestão de causa e ação
    if st.session_state.gemini_model:
        st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.denuncia_completa['insights_ia'],
            st.session_state.denuncia_completa.get('analise_imagem_ia', {}), # Passa análise de imagem (pode estar vazia)
            st.session_state.gemini_model
        )
    else:
        st.warning("⚠️ Modelo Google Gemini Text não inicializado. Sugestões de causa/ação por IA desabilitadas.")
        st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Sugestões de causa/ação via IA indisponíveis."}


    # Gerar resumo completo
    if st.session_state.gemini_model:
        st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(
            st.session_state.denuncia_completa, # Passa todos os dados
            st.session_state.gemini_model
        )
    else:
        st.warning("⚠️ Modelo Google Gemini Text não inicializado. Geração de resumo por IA desabilitada.")
        st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Resumo completo via IA indisponível."}


    # Avança para exibir o relatório após o processamento (mesmo que algumas IAs falhem/estejam indisponíveis)
    next_step()


elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊")
    st.write("✅ MISSÃO KRATERAS CONCLUÍDA! RELATÓRIO GERADO. ✅")

    dados_completos = st.session_state.denuncia_completa
    denunciante = dados_completos.get('denunciante', {})
    buraco = dados_completos.get('buraco', {})
    endereco = buraco.get('endereco', {})
    caracteristicas = buraco.get('caracteristicas_estruturadas', {})
    observacoes = buraco.get('observacoes_adicionais', 'Nenhuma observação adicional fornecida.')
    imagem_data = buraco.get('imagem_denuncia')
    localizacao_exata = dados_completos.get('localizacao_exata_processada', {})
    insights_ia = dados_completos.get('insights_ia', {})
    analise_imagem_ia = dados_completos.get('analise_imagem_ia', {})
    urgencia_ia = dados_completos.get('urgencia_ia', {})
    sugestao_acao_ia = dados_completos.get('sugestao_acao_ia', {})
    resumo_ia = dados_completos.get('resumo_ia', {})

    st.markdown("---")

    # Exibir todas as etapas abertas em expanders
    with st.expander("👤 Dados do Denunciante", expanded=True):
        st.write(f"**Nome:** {denunciante.get('nome', 'Não informado')}")
        st.write(f"**Idade:** {denunciante.get('idade', 'Não informado')}") # Será None se não informado
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
             # Exibe apenas as características que não são "Selecione" ou None/lista vazia
             caracteristicas_exibir = {k: v for k, v in caracteristicas.items() if v and v != 'Selecione' and (not isinstance(v, list) or v)}
             if caracteristicas_exibir:
                for key, value in caracteristicas_exibir.items():
                     if isinstance(value, list):
                         st.write(f"- **{key}:** {', '.join(value)}")
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

                 st.subheader("Visualização no Mapa")
                 try:
                     # Tenta usar st.map se coordenadas válidas
                     map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                     st.map(map_data, zoom=18, use_container_width=True)
                     st.info("ℹ️ O mapa acima é uma representação aproximada usando MapLibre/OpenStreetMap. Para maior precisão ou detalhes de satélite, use o link direto ou o mapa incorporado do Google Maps.")

                     # Tenta incorporar Google Maps se houver link embed gerado E chave de geocoding
                     embed_link = localizacao_exata.get('google_embed_link_gerado')
                     if embed_link and st.session_state.geocoding_api_key:
                         st.subheader("Visualização no Google Maps (Embed)")
                         # Incorpora o iframe do Google Maps
                         st.components.v1.html(
                             f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link}" allowfullscreen></iframe>',
                             height=470, # Altura um pouco maior para incluir borda
                             scrolling=False
                         )
                         # st.info("ℹ️ Requer chave de Geocoding API e a Embed API habilitada no Google Cloud para funcionar.") # Já avisado antes

                     elif st.session_state.geocoding_api_key and not embed_link:
                          # Isso pode acontecer se a geocodificação automática falhou de forma que não gerou embed link
                          st.warning("⚠️ Chave de Geocodificação fornecida, mas não foi possível gerar um mapa Google Maps incorporado. Verifique se a Embed API está habilitada no Google Cloud.")
                     elif not st.session_state.geocoding_api_key:
                           st.warning("⚠️ Chave de API de Geocodificação não fornecida. O mapa Google Maps incorporado não pode ser gerado.")


                 except Exception as map_error:
                     st.error(f"❌ Erro ao gerar visualização do mapa: {map_error}")


                 link_maps = localizacao_exata.get('google_maps_link_gerado')
                 if link_maps:
                     st.write(f"**Link Direto Google Maps:** [Abrir no Google Maps]({link_maps})")

                 if localizacao_exata.get('endereco_formatado_api'):
                      st.write(f"**Endereço Formatado (API):** {localizacao_exata.get('endereco_formatado_api')}")
                 if localizacao_exata.get('input_original'):
                     st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")


        elif tipo_loc == 'Descrição Manual Detalhada':
            st.write(f"**Descrição Manual:**")
            st.info(localizacao_exata.get('descricao_manual', 'Não informada'))
            if localizacao_exata.get('input_original'):
                st.write(f"(Input Original: `{localizacao_exata.get('input_original', 'Não informado')}`)")

        else: # Tipo "Não informada"
            st.warning("Localização exata não coletada de forma estruturada (coordenadas/link), nem descrição manual. O relatório dependerá da descrição e endereço base.")

        # Inclui motivo da falha na geocodificação se aplicável e se não foi sobrescrito por coords manuais
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior') and tipo_loc not in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Coordenadas Extraídas de Link (Manual)']:
             st.info(f"ℹ️ Nota: Não foi possível obter a localização exata via Geocodificação automática. Motivo: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")


    with st.expander("📷 Imagem da Denúncia", expanded=True):
         if imagem_data and 'bytes' in imagem_data:
              try:
                   # Usar io.BytesIO para exibir a imagem a partir dos bytes
                   st.image(io.BytesIO(imagem_data['bytes']), caption=imagem_data.get('filename', 'Imagem Carregada'), use_column_width=True)
                   st.write(f"**Nome do Arquivo:** {imagem_data.get('filename', 'Não informado')}")
                   st.write(f"**Tipo:** {imagem_data.get('type', 'Não informado')}")
              except Exception as e:
                   st.error(f"❌ Não foi possível exibir a imagem carregada: {e}")
         elif imagem_data and 'erro' in imagem_data:
              st.error(f"❌ Erro ao carregar a imagem: {imagem_data.get('erro', 'Detalhe desconhecido.')}")
         else:
              st.info("Nenhuma imagem foi carregada para esta denúncia.")


    st.markdown("---")
    st.subheader("🤖 Análises Robóticas de IA (Google Gemini)")

    if st.session_state.gemini_model:
        with st.expander("🧠 Análise de Características e Observações (IA Gemini)", expanded=True):
            st.write(insights_ia.get('insights', 'Análise não realizada ou com erro.'))

        # Exibe a análise de imagem SOMENTE se um modelo de visão foi inicializado e uma imagem foi processada
        if st.session_state.gemini_vision_model:
             with st.expander("👁️ Análise Visual do Buraco (IA Gemini Vision)", expanded=True):
                 st.write(analise_imagem_ia.get('analise_imagem', 'Análise não realizada ou com erro.'))
        elif 'analise_imagem_ia' in dados_completos and 'analise_imagem' in dados_completos['analise_imagem_ia'] and 'indisponível' in dados_completos['analise_imagem_ia']['analise_imagem'].lower():
             # Exibe o expander se a análise foi tentada, mas falhou ou o modelo estava indisponível
             with st.expander("👁️ Análise Visual do Buraco (IA Gemini Vision)", expanded=True):
                  st.write(analise_imagem_ia.get('analise_imagem', 'Erro na análise visual ou modelo indisponível.'))
        elif imagem_data and 'bytes' in imagem_data:
             # Se há imagem mas não há resultado de análise (e não é erro de indisponibilidade), algo deu errado
             with st.expander("👁️ Análise Visual do Buraco (IA Gemini Vision)", expanded=True):
                  st.warning("⚠️ Análise Visual de Imagem não foi concluída. Verifique o modelo Gemini Vision e a imagem.")
                  st.write(analise_imagem_ia.get('analise_imagem', 'Análise não iniciada ou falhou sem mensagem específica.'))


        with st.expander("🚦 Sugestão de Urgência (IA Gemini)", expanded=True):
            st.write(urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro.'))

        with st.expander("🛠️ Sugestões de Causa e Ação (IA Gemini)", expanded=True):
            st.write(sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões não geradas ou com erro.'))

        st.markdown("---")
        st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini)")
        st.write(resumo_ia.get('resumo_ia', 'Resumo não gerado ou com erro.'))
    else:
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chave Google API KEY não configurada ou modelos não inicializados).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Opção para reiniciar o processo
    if st.button("Iniciar Nova Denúncia"):
        # Limpa o estado da sessão para recomeçar (exceto as chaves API e modelos que são cache_resource)
        keys_to_keep = ['api_keys_loaded', 'gemini_model', 'gemini_vision_model', 'geocoding_api_key']
        all_keys = list(st.session_state.keys())
        for key in all_keys:
            if key not in keys_to_keep:
                del st.session_state[key]
        st.rerun()

    # Opção para exibir dados brutos (útil para debug ou exportação)
    with st.expander("🔌 Ver Dados Brutos (JSON)"):
        # Remove os bytes da imagem para evitar poluir o JSON bruto, se houver
        dados_para_json = dados_completos.copy()
        if 'buraco' in dados_para_json and 'imagem_denuncia' in dados_para_json['buraco']:
             img_data = dados_para_json['buraco']['imagem_denuncia']
             if img_data and 'bytes' in img_data:
                  # Cria uma cópia e remove a chave 'bytes'
                  img_data_copy = img_data.copy()
                  del img_data_copy['bytes']
                  dados_para_json['buraco']['imagem_denuncia'] = img_data_copy
                  st.info("Conteúdo da imagem (bytes) omitido do JSON bruto.")
             # else: Se imagem_denuncia existe mas não tem 'bytes' (ex: erro), mantém como está

        st.json(dados_para_json)


# --- Rodar a aplicação ---
# A execução principal do script Streamlit é gerenciada pelo próprio Streamlit.
# As funções são chamadas conforme o estado da sessão e as interações do usuário.
# O código abaixo é apenas para garantir que o script seja executado como um app Streamlit.
if __name__ == "__main__":
    # Streamlit cuida do loop principal, não precisamos de uma função main tradicional
    # O código fora das funções e no topo é executado em cada rerun.
    # O fluxo é controlado pelos ifs/elifs baseados em st.session_state.step
    pass # Nada a fazer aqui além do que já está no corpo principal do script
