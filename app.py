# -*- coding: utf-8 -*-
"""
Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos (v3.2 - Streamlit Secure Edition)

Bem-vindo à versão visual do Krateras! Agora em uma interface amigável,
mantendo a inteligência da IA e a segurança das suas chaves (fora do código!).

Tecnologias: Python, Streamlit, Google Gemini API, Google Geocoding API, ViaCEP.
Objetivo: Coletar dados de denúncias de buracos, analisá-los com IA e gerar relatórios
detalhados e priorizados, incluindo localização visual em mapa.

Vamos juntos consertar essas ruas! Iniciando sistemas visuais e robóticos...
"""

import streamlit as st
import requests
import google.generativeai as genai
from typing import Dict, Any, Optional
import re
import json # Adicionado para exibir dados brutos opcionalmente
import pandas as pd # Para usar st.map

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
.stTextInput, .stNumberInput, .stTextArea, .stRadio, .stSelectbox {
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
if 'geocoding_api_key' not in st.session_state:
    st.session_state.geocoding_api_key = None

# --- 🔑 Gerenciamento de Chaves Secretas (Streamlit Secrets) ---
# Utiliza o .streamlit/secrets.toml para carregar chaves

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    """
    Tenta obter as chaves de API do Google Gemini e Google Maps Geocoding de Streamlit Secrets.
    Retorna None se não encontradas.
    """
    gemini_key = st.secrets.get('GOOGLE_API_KEY')
    geocoding_key = st.secrets.get('geocoding_api_key')

    if not gemini_key:
        st.warning("⚠️ Segredo 'GOOGLE_API_KEY' não encontrado nos Streamlit Secrets. Funcionalidades de IA do Gemini estarão desabilitadas.")
    if not geocoding_key:
        st.warning("⚠️ Segredo 'geocoding_api_key' não encontrado nos Streamlit Secrets. Geocodificação automática estará desabilitada.")
        st.info("ℹ️ Para configurar os segredos, crie um arquivo `.streamlit/secrets.toml` na raiz do seu projeto Streamlit com:\n```toml\nGOOGLE_API_KEY = \"SUA_CHAVE_GEMINI\"\ngeocoding_api_key = \"SUA_CHAVE_GEOCODING\"\n```\nLembre-se que a API Geocoding PODE gerar custos. Ative-a no Google Cloud.")

    return gemini_key, geocoding_key

# --- Inicializar APIs (Cacheado para performance) ---

@st.cache_resource
def init_gemini(api_key: Optional[str]) -> Optional[genai.GenerativeModel]:
    """Inicializa o modelo Google Gemini com cache."""
    if not api_key:
        return None # Retorna None se a chave não for fornecida
    try:
        genai.configure(api_key=api_key)
        # Buscar modelos que suportam geração de conteúdo de texto
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

        if not available_models:
             st.error("❌ ERRO na Fábrica de Modelos: Nenhum modelo de texto Gemini compatível encontrado na sua conta.")
             return None

        # Preferência por modelos mais recentes ou Pro
        preferred_models: list[str] = ['gemini-1.5-flash-latest', 'gemini-1.0-pro', 'gemini-pro']
        model_name: Optional[str] = None
        for pref_model in preferred_models:
            # Verifica com e sem o prefixo 'models/'
            if f'models/{pref_model}' in available_models:
                model_name = pref_model
                break
            if pref_model in available_models:
                 model_name = pref_model
                 break

        if not model_name:
            # Fallback para o primeiro modelo disponível se nenhum preferencial for encontrado
            model_name = available_models[0].replace('models/', '')
            st.warning(f"⚠️ AVISO: Modelos Gemini preferenciais não encontrados. Usando fallback: '{model_name}'. Pode ter menos funcionalidades.")

        model = genai.GenerativeModel(model_name)
        # Teste básico pode ser feito aqui se necessário, mas cache_resource já lida com isso
        # model.generate_content("Ping") # Remover teste real em produção para evitar custos desnecessários
        st.success(f"✅ Conexão com Google Gemini estabelecida usando modelo '{model_name}'. A IA está online e pensativa!")
        return model
    except Exception as e:
        st.error(f"❌ ERRO no Painel de Controle Gemini: Falha na inicialização do Google Gemini. Verifique sua chave e status do serviço.")
        st.exception(e)
        return None

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
            return {"erro": f"Geocodificação falhou. Status: {status}. Mensagem: {error_msg}"}
        if not data['results']:
             return {"erro": "Geocodificação falhou. Nenhum local exato encontrado para o endereço fornecido."}

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


@st.cache_data(show_spinner="🧠 Executando análise profunda da descrição do buraco com IA Gemini...")
def analisar_descricao_gemini(_descricao: str, _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para analisar a descrição detalhada do buraco e extrair insights estruturados."""
    if not _model:
        return {"insights": "🤖 Análise de descrição via IA indisponível (Motor Gemini offline)."}
    if not _descricao or _descricao.strip() == "":
         return {"insights": "🔍 Sem descrição fornecida para análise de IA."}

    prompt = f"""
    Analise a seguinte descrição DETALHADA de um buraco em uma rua. Seu objetivo é extrair informações objetivas e insights CRUCIAIS para um sistema de denúncias de reparo público.
    Formate a saída como um texto claro, usando marcadores (-) ou títulos para cada categoria.
    Se uma categoria NÃO PUDER ser claramente mencionada ou inferida COM ALTA CONFIANÇA a partir do texto, indique explicitamente "Não especificado/inferido na descrição". Seja honesto sobre o que PODE ser extraído.

    Descrição do Buraco: "{_descricao}"

    Categorias para Extrair/Inferir da Descrição:
    - Severidade/Tamanho Estimado (Baseado na descrição): [Ex: Pequeno, Médio, Grande, Enorme, Crítico. Use termos comparativos se presentes, ex: "do tamanho de uma roda de carro".]
    - Profundidade Estimada: [Ex: Raso, Fundo, Muito Fundo. Termos como "cabe um pneu" indicam profundidade.]
    - Presença de Água/Alagamento: [Sim/Não/Não mencionado, se acumula água, vira piscina.]
    - Perigos Potenciais e Impactos Mencionados: [Liste riscos específicos citados ou implicados (ex: risco de acidente de carro/moto/bike, perigo para pedestres, causa danos a veículos - pneu furado, suspensão, roda -, dificuldade de desviar, risco de queda, perigo à noite/chuva). Seja específico.]
    - Contexto Adicional Relevante do Local/Histórico: [Problema recorrente/antigo/novo, perto de local importante (escola, hospital, comércio), em via movimentada, em curva, na esquina, na subida/descida, pouca iluminação.]
    - Sugestões de Ação/Recursos Mencionados pelo Denunciante: [Se o usuário sugere o que fazer (tapa-buraco, recapeamento, sinalizar) ou causas percebidas.]
    - Identificadores Visuais Adicionais (se descritos): [Coisas únicas próximas que ajudam a achar o buraco (poste X, árvore Y, em frente a Z).]
    - Palavras-chave Principais: [Liste 3-7 palavras-chave que capturem a essência da denúncia e o problema principal.]

    Formate a resposta de forma limpa e estruturada.
    """
    try:
        response = _model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not hasattr(response, 'candidates') or not response.candidates:
             block_reason = "Desconhecido"
             if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
                 block_reason = response.prompt_feedback.block_reason.name
             return {"insights": f"❌ Análise de descrição bloqueada pelo filtro de segurança do Gemini. Motivo: {block_reason}"}
        return {"insights": response.text.strip()}
    except Exception as e:
        return {"insights": f"❌ Erro ao analisar a descrição com IA: {e}"}


@st.cache_data(show_spinner="🧠 Calculando o Nível de Prioridade Robótica...")
def categorizar_urgencia_gemini(_dados_denuncia: Dict[str, Any], _insights_ia: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir uma categoria de urgência com base nos dados e insights."""
    if not _model:
        return {"urgencia_ia": "🤖 Sugestão de urgência via IA indisponível (Motor Gemini offline)."}

    descricao = _dados_denuncia.get('descricao_detalhada', 'Sem descrição.')
    insights_texto = _insights_ia.get('insights', 'Análise de insights não disponível.')
    localizacao_exata = _dados_denuncia.get('localizacao_exata_processada', {})
    tipo_loc = localizacao_exata.get('tipo', 'Não informada')
    input_original_loc = localizacao_exata.get('input_original', 'Não informado.')

    loc_contexto = f"Localização informada: Tipo: {tipo_loc}. Detalhes originais: '{input_original_loc}'."
    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
        lat = localizacao_exata.get('latitude')
        lon = localizacao_exata.get('longitude')
        loc_contexto += f" Coordenadas: {lat}, {lon}. Link gerado: {localizacao_exata.get('google_maps_link_gerado', 'Não disponível')}."
    elif localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
         loc_contexto += f" (Nota: Tentativa de Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior', 'Motivo desconhecido')})"


    prompt = f"""
    Com base nas informações da denúncia e nos insights extraídos pela análise anterior, sugira a MELHOR categoria de urgência para o reparo deste buraco.
    Considere a severidade/tamanho, profundidade, PERIGOS POTENCIAIS e impactos mencionados, e qualquer CONTEXTO ADICIONAL relevante (como ser recorrente, em área de alto tráfego/risco, perto de local importante).

    Escolha UMA Categoria de Urgência entre estas:
    - Urgência Baixa: Buraco pequeno, sem perigo aparente, em local de baixo tráfego. Principalmente estético ou pequeno incômodo.
    - Urgência Média: Tamanho razoável, pode causar leve incômodo ou dano menor (ex: pneu furado leve), em via secundária ou com tráfego moderado. Requer reparo em prazo razoável.
    - Urgência Alta: Buraco grande, profundo, perigo CLARO e/ou frequente (risco de acidente mais sério, dano significativo a veículo, perigo para motos/bikes/pedestres), em via movimentada ou área de risco (escola, hospital). Requer atenção RÁPIDA, possivelmente em poucos dias.
    - Urgência Imediata/Crítica: Buraco ENORME/muito profundo que causa acidentes CONSTANTES ou representa risco GRAVE e iminente a veículos ou pessoas (ex: cratera na pista principal), afeta severamente a fluidez ou acessibilidade. Requer intervenção de EMERGÊNCIA (horas/poucas horas).

    Informações Relevantes da Denúncia:
    Localização Básica: Rua {_dados_denuncia.get('endereco', {}).get('rua', 'Não informada')}, Número Próximo/Referência: {_dados_denuncia.get('numero_proximo', 'Não informado')}, Lado: {_dados_denuncia.get('lado_rua', 'Não informado')}, Cidade: {_dados_denuncia.get('endereco', {}).get('cidade_buraco', 'Não informada')}, Estado: {_dados_denuncia.get('endereco', {}).get('estado_buraco', 'Não informado')}.
    {loc_contexto}
    Descrição Original do Denunciante: "{descricao}"
    Insights Extraídos pela Análise de IA:
    {insights_texto}

    Com base nestes dados, qual categoria de urgência você sugere? Forneça APENAS a categoria (ex: "Urgência Alta") e uma breve JUSTIFICATIVA (máximo 2 frases) explicando POR QUE essa categoria foi sugerida, citando elementos da descrição ou insights.

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
def sugerir_causa_e_acao_gemini(_dados_denuncia: Dict[str, Any], _insights_ia: Dict[str, Any], _model: genai.GenerativeModel) -> Dict[str, Any]:
    """Utiliza o Gemini para sugerir possíveis causas do buraco e ações de reparo com base nos dados e insights."""
    if not _model:
        return {"sugestao_acao_ia": "🤖 Sugestões de causa/ação via IA indisponíveis (Motor Gemini offline)."}

    descricao = _dados_denuncia.get('descricao_detalhada', 'Sem descrição.')
    insights_texto = _insights_ia.get('insights', 'Análise de insights não disponível.')

    prompt = f"""
    Com base na descrição fornecida pelo denunciante e nos insights extraídos pela análise de IA, tente sugerir:
    1. Uma ou duas PÓSSIVEIS CAUSAS para a formação deste buraco específico (ex: chuva forte recente, desgaste do asfalto pelo tempo/tráfego, problema na drenagem subterrânea, afundamento devido a reparo anterior, obra mal feita na região). Baseie-se no contexto (se recorrente, se choveu, etc).
    2. Sugestões de TIPOS DE AÇÃO ou REPARO mais adequados ou necessários para resolver este problema (ex: simples tapa-buraco, recapeamento da seção, inspeção de drenagem, sinalização de emergência, interdição parcial da via). Baseie-se na severidade e perigos.
    Baseie suas sugestões EXCLUSIVAMENTE nas informações fornecidas na descrição e nos insights. Se a descrição não der pistas suficientes, indique "Não especificado/inferido na descrição". Seja lógico e prático.

    Informações Relevantes da Denúncia:
    Descrição Original do Buraco: "{descricao}"
    Insights Extraídos pela Análise de IA:
    {insights_texto}

    Formato de saída:
    Possíveis Causas Sugeridas: [Lista de causas sugeridas baseadas na descrição ou 'Não especificado/inferido']
    Sugestões de Ação/Reparo Sugeridas: [Lista de ações sugeridas baseadas na descrição/insights ou 'Não especificado/inferido']
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
    """Utiliza o Gemini para gerar um resumo narrativo inteligente da denúncia completa."""
    if not _model:
        return {"resumo_ia": "🤖 Resumo inteligente via IA indisponível (Motor Gemini offline)."}

    denunciante = _dados_denuncia_completa.get('denunciante', {})
    buraco = _dados_denuncia_completa.get('buraco', {})
    endereco = buraco.get('endereco', {})
    localizacao_exata = _dados_denuncia_completa.get('localizacao_exata_processada', {})
    insights_ia = _dados_denuncia_completa.get('insights_ia', {}).get('insights', 'Análise da descrição não disponível ou com erro.')
    urgencia_ia = _dados_denuncia_completa.get('urgencia_ia', {}).get('urgencia_ia', 'Sugestão de urgência não disponível ou com erro.')
    sugestao_acao_ia = _dados_denuncia_completa.get('sugestao_acao_ia', {}).get('sugestao_acao_ia', 'Sugestões de causa/ação não disponíveis ou com erro.')


    loc_info_resumo = "Localização exata não especificada ou processada."
    tipo_loc_processada = localizacao_exata.get('tipo', 'Não informada')

    if tipo_loc_processada in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
         lat = localizacao_exata.get('latitude')
         lon = localizacao_exata.get('longitude')
         link_gerado = localizacao_exata.get('google_maps_link_gerado', 'Não disponível')
         loc_info_resumo = f"Localização: Coordenadas {lat}, {lon} (Obtida via: {tipo_loc_processada.replace(' (API)', ' API').replace('Manual', 'Manual').replace('Fornecidas/Extraídas', 'Manual')}). Link Google Maps: {link_gerado}."
         if localizacao_exata.get('input_original'):
             loc_info_resumo += f" (Input original: '{localizacao_exata.get('input_original')}')"

    elif tipo_loc_processada == 'Descrição Manual Detalhada':
         loc_info_resumo = f"Localização via descrição manual detalhada: '{localizacao_exata.get('descricao_manual', 'Não informada')}'. (Input original: '{localizacao_exata.get('input_original', 'Não informado')}')"

    elif localizacao_exata.get('input_original') and tipo_loc_processada == 'Não informada':
         loc_info_resumo = f"Localização informada (tipo não detectado): '{localizacao_exata.get('input_original')}'."

    if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
         loc_info_resumo += f" (Nota: Geocodificação automática falhou/não tentada: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')})"


    prompt = f"""
    Gere um resumo narrativo conciso (máximo 8-10 frases) para a seguinte denúncia de buraco no aplicativo Krateras.
    Este resumo deve ser formal, objetivo e útil para equipes de manutenção ou gestão pública.
    Combine os dados estruturados, a localização exata processada e os insights das análises de IA.

    Inclua:
    - Quem denunciou (Nome, Cidade de Residência).
    - Onde está o buraco (Rua, Número Próximo/Referência, Bairro, Cidade do Buraco, Estado do Buraco, CEP se disponível).
    - A localização EXATA (mencione como foi obtida - Geocodificada, Coordenadas Manual, Descrição Manual - e inclua os dados - Coordenadas/Link Gerado ou Descrição Manual).
    - O lado da rua.
    - Os principais pontos da Análise Detalhada de IA sobre o buraco (Severidade/Tamanho, Perigos Potenciais, Contexto Relevante).
    - A SUGESTÃO de Categoria de Urgência pela IA e sua Justificativa.
    - As SUGESTÕES de POSSÍVEIS CAUSAS e TIPOS DE AÇÃO/REPARO sugeridas pela IA (se disponíveis).

    Dados da Denúncia:
    Denunciante: {denunciante.get('nome', 'Não informado')}, de {denunciante.get('cidade_residencia', 'Não informada')}.
    Endereço do Buraco: Rua {endereco.get('rua', 'Não informada')}, Nº Próximo: {buraco.get('numero_proximo', 'Não informado')}. Bairro: {endereco.get('bairro', 'Não informado')}. Cidade: {endereco.get('cidade_buraco', 'Não informada')}, Estado: {endereco.get('estado_buraco', 'Não informado')}. CEP: {buraco.get('cep_informado', 'Não informado')}.
    Lado da Rua: {buraco.get('lado_rua', 'Não informado')}.
    Localização Exata Coletada: {loc_info_resumo}
    Descrição Original: "{buraco.get('descricao_detalhada', 'Não fornecida.')}"

    Insights da Análise Detalhada de IA:
    {insights_ia}

    Sugestão de Urgência pela IA:
    {urgencia_ia}

    Sugestões de Causa e Ação pela IA:
    {sugestao_acao_ia}


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
        'collect_buraco_details', # Unifica a coleta do resto e a geocodificação/localização manual
        'processing_ia',
        'show_report'
    ]
    try:
        current_index = steps.index(st.session_state.step)
        if current_index < len(steps) - 1:
            st.session_state.step = steps[current_index + 1]
            # Forçar um reruns para atualizar a UI para o próximo passo
            st.rerun()
    except ValueError:
        # Caso o passo atual não esteja na lista (erro ou estado inicial)
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
             # Lógica para pular passos de CEP/Manual se não foram usados
             if st.session_state.step == 'collect_buraco_details':
                  # Se chegamos aqui diretamente do método, voltamos para lá
                  if st.session_state.get('endereco_coletado_via') == 'cep':
                      st.session_state.step = 'collect_buraco_address_cep'
                  elif st.session_state.get('endereco_coletado_via') == 'manual':
                      st.session_state.step = 'collect_buraco_address_manual'
                  else: # Fallback seguro
                       st.session_state.step = steps[current_index - 1]
             elif st.session_state.step == 'collect_buraco_address_cep' or st.session_state.step == 'collect_buraco_address_manual':
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

    Utilizamos inteligência artificial (Google Gemini) e APIs de localização (Google Geocoding,
    ViaCEP) para coletar, analisar e gerar um relatório detalhado para as autoridades competentes.

    Fui criado com o que há de mais avançado em Programação, IA, Design Inteligente,
    Matemática e Lógica Inabalável. Com acesso seguro às APIs, sou imparável.

    Clique em Iniciar para começarmos a coleta de dados.
    """)

    st.info("⚠️ Suas chaves de API do Google (Gemini e Geocoding) devem ser configuradas nos Streamlit Secrets (`.streamlit/secrets.toml`) para que a IA e a geocodificação automática funcionem corretamente e de forma segura.")


    if st.button("Iniciar Missão Denúncia!"):
        # Carregar chaves e inicializar APIs antes de coletar dados
        gemini_api_key, geocoding_api_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_api_key # Armazena a chave de geocoding no estado
        st.session_state.gemini_model = init_gemini(gemini_api_key) # Inicializa o modelo Gemini (cacheado)
        st.session_state.api_keys_loaded = True # Marca que tentamos carregar as chaves
        next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína da Vez! ---")
    st.write("Sua contribuição é super valiosa! 💪")

    # Formulário para coletar dados do denunciante
    with st.form("form_denunciante"):
        nome = st.text_input("Seu nome completo:", key='nome_denunciante')
        idade = st.number_input("Sua idade (aproximada, se preferir, sem pressão 😉):", min_value=1, max_value=120, value=30, key='idade_denunciante')
        cidade_residencia = st.text_input("Em qual cidade você reside?:", key='cidade_residencia_denunciante')

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
        key='endereco_method'
    )

    # Use um botão para confirmar a escolha e mover para o próximo sub-step
    if st.button("Selecionar Método"):
         if opcao_localizacao == 'Digitar nome manualmente':
              st.session_state.endereco_coletado_via = 'manual' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_manual'
         elif opcao_localizacao == 'Buscar por CEP':
              st.session_state.endereco_coletado_via = 'cep' # Guarda a forma como coletamos o endereço
              st.session_state.step = 'collect_buraco_address_cep'
         st.rerun() # Força a atualização para o próximo passo

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_cep':
    st.header("--- 🚧 Detalhes do Buraco (Busca por CEP) ---")
    st.write("Digite o CEP do local do buraco.")

    with st.form("form_cep"):
        cep_input = st.text_input("Digite o CEP (apenas números):", max_chars=8, key='cep_buraco')
        buscar_button = st.form_submit_button("Buscar CEP")

        if buscar_button:
            if not cep_input:
                st.error("❗ Por favor, digite um CEP.")
            else:
                dados_cep = buscar_cep(cep_input.strip())

                if 'erro' in dados_cep:
                    st.error(f"❌ Falha na busca por CEP: {dados_cep['erro']}")
                    st.session_state.cep_error = True # Marca que houve erro no CEP
                    st.session_state.dados_cep_validos = None # Limpa dados válidos
                else:
                    st.session_state.dados_cep_validos = dados_cep # Armazena dados do CEP válidos
                    st.session_state.cep_error = False # Limpa erro
                    st.success("✅ Endereço Encontrado (ViaCEP):")
                    st.write(f"**Rua:** {dados_cep.get('logradouro', 'Não informado')}")
                    st.write(f"**Bairro:** {dados_cep.get('bairro', 'Não informado')}")
                    st.write(f"**Cidade:** {dados_cep.get('localidade', 'Não informado')}")
                    st.write(f"**Estado:** {dados_cep.get('uf', 'Não informado')}")
                    st.write(f"**CEP:** {cep_input.strip()}")
                    st.info("Por favor, confirme se estes dados estão corretos. Se não, use o botão 'Corrigir Endereço Manualmente'.")


    # Exibe botões de ação APENAS se tentou buscar CEP
    if st.session_state.get('cep_buraco'): # Verifica se o input de CEP foi preenchido
        if st.session_state.get('dados_cep_validos'): # Se dados do CEP foram encontrados e são válidos
            st.session_state.denuncia_completa['buraco'] = {
                'endereco': {
                    'rua': st.session_state.dados_cep_validos.get('logradouro', ''),
                    'bairro': st.session_state.dados_cep_validos.get('bairro', ''),
                    'cidade_buraco': st.session_state.dados_cep_validos.get('localidade', ''),
                    'estado_buraco': st.session_state.dados_cep_validos.get('uf', '')
                },
                'cep_informado': st.session_state.get('cep_buraco', '')
            }
            # Botão para confirmar e ir para detalhes (número, descrição)
            if st.button("Confirmar Endereço e Avançar"):
                 next_step()

            # Botão para corrigir manualmente (volta para entrada manual)
            if st.button("Corrigir Endereço Manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.rerun()

        elif st.session_state.get('cep_error'): # Se houve erro na busca por CEP
            st.warning("Não foi possível obter o endereço por CEP.")
            if st.button("Tentar novamente por CEP"):
                 st.session_state.cep_error = False # Reseta o erro para tentar novamente
                 st.rerun() # Força reload para resetar o formulário de CEP
            if st.button("Digitar endereço manualmente"):
                 st.session_state.endereco_coletado_via = 'manual'
                 st.session_state.step = 'collect_buraco_address_manual'
                 st.rerun()
        # else: # Caso clicou buscar mas input estava vazio, o erro é exibido no form
        #     pass # Sem botões de ação extras

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_address_manual':
    st.header("--- 🚧 Detalhes do Buraco (Entrada Manual) ---")
    st.write("Digite os dados do endereço do buraco manualmente.")

    # Use os dados do CEP pré-preenchidos se vier dessa rota
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
                st.session_state.denuncia_completa['buraco'] = {
                    'endereco': {
                        'rua': rua_manual.strip(),
                        'bairro': bairro_manual.strip(),
                        'cidade_buraco': cidade_manual.strip(),
                        'estado_buraco': estado_manual.strip().upper() # Guarda em maiúsculas
                    },
                    'cep_informado': st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado', '') # Mantém o CEP se veio da busca
                }
                next_step() # Move para a próxima etapa (coleta de detalhes)

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'collect_buraco_details':
    st.header("--- 🚧 Detalhes Finais do Buraco ---")
    st.subheader("Informações cruciais para a localização e análise!")

    # Exibe o endereço básico já coletado para referência
    endereco_basico = st.session_state.denuncia_completa.get('buraco', {}).get('endereco', {})
    st.write(f"Endereço Base: {endereco_basico.get('rua', 'Não informado')}, {endereco_basico.get('cidade_buraco', 'Não informada')} - {endereco_basico.get('estado_buraco', 'Não informado')}")
    if endereco_basico.get('bairro'):
         st.write(f"Bairro: {endereco_basico.get('bairro')}")
    if st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado'):
         st.write(f"CEP informado: {st.session_state.denuncia_completa.get('buraco', {}).get('cep_informado')}")

    st.markdown("---") # Separador visual

    with st.form("form_buraco_details"):
        numero_proximo = st.text_input("Número do imóvel mais próximo ou ponto de referência (ESSENCIAL para precisão! Ex: 'Em frente ao 123', 'Esquina c/ Rua X'):", key='numero_proximo_buraco')
        lado_rua = st.text_input("Lado da rua onde está o buraco (Ex: 'lado par', 'lado ímpar', 'lado direito', 'lado esquerdo'):", key='lado_rua_buraco')
        descricao_detalhada = st.text_area("Sua descrição detalhada do buraco (Tamanho, profundidade, perigos, se tem água, antigo/novo, etc. Hora da IA Brilhar!):", key='descricao_buraco')

        submitted = st.form_submit_button("Coletar Localização e Continuar")

        if submitted:
            if not numero_proximo or not lado_rua or not descricao_detalhada:
                 st.error("❗ Número próximo/referência, Lado da rua e Descrição detalhada são campos obrigatórios.")
            else:
                # Atualiza o dicionário de buraco no estado
                st.session_state.denuncia_completa['buraco'].update({
                    'numero_proximo': numero_proximo.strip(),
                    'lado_rua': lado_rua.strip(),
                    'descricao_detalhada': descricao_detalhada.strip()
                })

                # --- Tentar Geocodificação Automática ---
                st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo": "Não informada"} # Reseta localização processada
                tentou_geocodificar = False
                geocodificacao_sucesso = False
                motivo_falha_geo = ""

                rua_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('rua')
                cidade_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('cidade_buraco')
                estado_buraco = st.session_state.denuncia_completa['buraco']['endereco'].get('estado_buraco')

                tem_dados_para_geo = (st.session_state.geocoding_api_key and rua_buraco and numero_proximo and cidade_buraco and estado_buraco)

                if tem_dados_para_geo:
                    st.info("✅ Chave de Geocodificação e dados básicos de endereço completos encontrados. Tentando gerar o link do Google Maps automaticamente...")
                    tentou_geocodificar = True
                    geo_resultado = geocodificar_endereco(
                        rua_buraco,
                        numero_proximo.strip(), # Usa o número/referência como base para geocodificação
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
                            "google_embed_link_gerado": geo_resultado.get('google_embed_link_gerado')
                        }
                        st.success("✅ Localização Obtida (via Geocodificação Automática)!")
                    else:
                        st.warning(f"❌ Falha na Geocodificação automática: {geo_resultado['erro']}")
                        motivo_falha_geo = f"Erro da API de Geocodificação: {geo_resultado.get('erro', 'Motivo desconhecido')}"
                elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                    st.warning("⚠️ AVISO: Chave de Geocodificação fornecida, mas dados de endereço insuficientes (precisa de Rua, Número Próximo, Cidade, Estado). Geocodificação automática NÃO tentada.")
                    motivo_falha_geo = "Dados insuficientes para Geocodificação (requer Rua, Número, Cidade, Estado)."
                elif not st.session_state.geocoding_api_key:
                    st.warning("⚠️ AVISO: Chave de API de Geocodificação NÃO fornecida. Geocodificação automática NÃO tentada.")
                    motivo_falha_geo = "Chave de API de Geocodificação não fornecida."


                # --- Coleta de Localização Manual (se a geocodificação falhou ou não foi tentada) ---
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

                     localizacao_manual_input = st.text_input("Insira COORDENADAS (Lat,Long), LINK do Maps com Coordenadas, OU DESCRIÇÃO DETALHADA:", key='localizacao_manual')

                     # Tentar extrair coordenadas do input manual (reusando regex)
                     lat: Optional[float] = None
                     lon: Optional[float] = None
                     tipo_manual_processado = "Descrição Manual Detalhada"
                     input_original_manual = localizacao_manual_input.strip()

                     if input_original_manual:
                         # Regex para tentar achar coordenadas em diferentes formatos (Lat,Long ou em links comuns)
                         # Tenta cobrir "lat,long", "@lat,long" em links
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
                              "google_embed_link_gerado": f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat},{lon}" if st.session_state.geocoding_api_key else None # Tenta gerar embed link se tiver chave
                         }
                     elif input_original_manual: # Se há input manual, mas não extraiu Lat/Long
                         st.session_state.denuncia_completa['localizacao_exata_processada'] = {
                              "tipo": "Descrição Manual Detalhada",
                              "input_original": input_original_manual,
                              "descricao_manual": input_original_manual
                         }
                     # else: Se input manual está vazio, o tipo continua "Não informada" como inicializado

                     # Se houve uma tentativa de geocodificação automática que falhou, registra o motivo
                     if tentou_geocodificar and not geocodificacao_sucesso:
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = motivo_falha_geo
                     elif not st.session_state.geocoding_api_key:
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Chave de API de Geocodificação não fornecida."
                     elif st.session_state.geocoding_api_key and not tem_dados_para_geo:
                          st.session_state.denuncia_completa['localizacao_exata_processada']['motivo_falha_geocodificacao_anterior'] = "Dados insuficientes para Geocodificação (requer Rua, Número, Cidade, Estado)."


                     # Agora que a localização manual foi processada, passamos para a análise de IA
                     if st.session_state.denuncia_completa['localizacao_exata_processada'].get('tipo') == "Não informada":
                          st.warning("⚠️ Nenhuma localização exata estruturada (coordenadas ou link) foi fornecida ou detectada. O relatório dependerá apenas da descrição textual e endereço base.")
                          # Ainda assim, podemos ir para a próxima etapa se a descrição foi fornecida.
                          next_step()
                     else:
                         next_step() # Avança para a etapa de processamento IA

                else: # Se a geocodificação automática foi bem-sucedida, apenas avançamos
                    next_step()

    st.button("Voltar", on_click=prev_step)


elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    st.write("Por favor, aguarde enquanto o Krateras analisa os dados e gera o relatório com a inteligência do Google Gemini.")

    # Verifica se o modelo Gemini está disponível antes de processar
    if st.session_state.gemini_model:
        buraco_data = st.session_state.denuncia_completa.get('buraco', {})

        # Rodar as análises de IA
        st.session_state.denuncia_completa['insights_ia'] = analisar_descricao_gemini(buraco_data.get('descricao_detalhada', ''), st.session_state.gemini_model)
        st.session_state.denuncia_completa['urgencia_ia'] = categorizar_urgencia_gemini(buraco_data, st.session_state.denuncia_completa['insights_ia'], st.session_state.gemini_model)
        st.session_state.denuncia_completa['sugestao_acao_ia'] = sugerir_causa_e_acao_gemini(buraco_data, st.session_state.denuncia_completa['insights_ia'], st.session_state.gemini_model)
        st.session_state.denuncia_completa['resumo_ia'] = gerar_resumo_completo_gemini(st.session_state.denuncia_completa, st.session_state.gemini_model)

        # Avança para exibir o relatório após o processamento
        next_step()
    else:
        st.warning("⚠️ Modelo Google Gemini não inicializado. Pulando análises de IA.")
        # Define resultados IA como indisponíveis
        st.session_state.denuncia_completa['insights_ia'] = {"insights": "Análise de descrição via IA indisponível."}
        st.session_state.denuncia_completa['urgencia_ia'] = {"urgencia_ia": "Sugestão de urgência via IA indisponível."}
        st.session_state.denuncia_completa['sugestao_acao_ia'] = {"sugestao_acao_ia": "Sugestões de causa/ação via IA indisponíveis."}
        st.session_state.denuncia_completa['resumo_ia'] = {"resumo_ia": "Resumo completo via IA indisponível."}
        next_step() # Avança mesmo sem IA se não estiver disponível

    # Note: Streamlit reruns automatically after state changes in callbacks or after button clicks.
    # Forcing rerun explicitly after long processes like API calls or IA is not usually needed if state is updated correctly.
    # However, next_step() explicitly calls st.rerun() which is fine for controlling flow.


elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊")
    st.write("✅ MISSÃO KRATERAS CONCLUÍDA! RELATÓRIO GERADO. ✅")

    dados_completos = st.session_state.denuncia_completa
    denunciante = dados_completos.get('denunciante', {})
    buraco = dados_completos.get('buraco', {})
    endereco = buraco.get('endereco', {})
    localizacao_exata = dados_completos.get('localizacao_exata_processada', {})
    insights_ia = dados_completos.get('insights_ia', {})
    urgencia_ia = dados_completos.get('urgencia_ia', {})
    sugestao_acao_ia = dados_completos.get('sugestao_acao_ia', {})
    resumo_ia = dados_completos.get('resumo_ia', {})

    st.markdown("---")

    with st.expander("👤 Dados do Denunciante"):
        st.write(f"**Nome:** {denunciante.get('nome', 'Não informado')}")
        st.write(f"**Idade:** {denunciante.get('idade', 'Não informado')}")
        st.write(f"**Cidade de Residência:** {denunciante.get('cidade_residencia', 'Não informada')}")

    with st.expander("🚧 Dados do Buraco"):
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
        st.write(f"**Descrição Original do Denunciante:**")
        st.info(buraco.get('descricao_detalhada', 'Nenhuma descrição fornecida.'))


    with st.expander("📍 Localização Exata"):
        tipo_loc = localizacao_exata.get('tipo', 'Não informada')
        st.write(f"**Tipo de Coleta:** {tipo_loc}")

        if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente', 'Geocodificada (API)', 'Coordenadas Extraídas de Link (Manual)']:
            lat = localizacao_exata.get('latitude')
            lon = localizacao_exata.get('longitude')

            if lat is not None and lon is not None:
                 st.write(f"**Coordenadas:** `{lat}, {lon}`")

                 # Exibir Mapa Visual
                 st.subheader("Visualização no Mapa")
                 try:
                     # Tenta usar st.map se coordenadas válidas
                     map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                     st.map(map_data, zoom=18, use_container_width=True)
                     st.info("ℹ️ O mapa acima é uma representação aproximada usando MapLibre/OpenStreetMap.")

                     # Tenta incorporar Google Maps se houver link embed gerado
                     embed_link = localizacao_exata.get('google_embed_link_gerado')
                     if embed_link:
                         st.subheader("Visualização no Google Maps (Embed)")
                         # Incorpora o iframe do Google Maps
                         st.components.v1.html(
                             f'<iframe width="100%" height="450" frameborder="0" style="border:0" src="{embed_link}" allowfullscreen></iframe>',
                             height=470, # Altura um pouco maior para incluir borda
                             scrolling=False
                         )
                     elif st.session_state.geocoding_api_key:
                          st.warning("⚠️ Não foi possível gerar um mapa Google Maps incorporado. Verifique a chave de API Geocoding e se a Embed API está habilitada (pode requerer configuração no Google Cloud).")

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

        else:
            st.warning("Localização exata não coletada de forma estruturada (coordenadas/link). O relatório dependerá da descrição e endereço base.")

        # Inclui motivo da falha na geocodificação se aplicável
        if localizacao_exata.get('motivo_falha_geocodificacao_anterior'):
             st.info(f"ℹ️ Nota: Não foi possível obter a localização exata via Geocodificação automática. Motivo: {localizacao_exata.get('motivo_falha_geocodificacao_anterior')}")


    if st.session_state.gemini_model:
        st.markdown("---")
        with st.expander("🧠 Análise Detalhada da Descrição (IA Gemini)"):
            st.write(insights_ia.get('insights', 'Análise não realizada ou com erro.'))

        with st.expander("🚦 Sugestão de Urgência (IA Gemini)"):
            st.write(urgencia_ia.get('urgencia_ia', 'Sugestão de urgência não gerada ou com erro.'))

        with st.expander("🛠️ Sugestões de Causa e Ação (IA Gemini)"):
            st.write(sugestao_acao_ia.get('sugestao_acao_ia', 'Sugestões não geradas ou com erro.'))

        st.markdown("---")
        st.subheader("📜 Resumo Narrativo Inteligente (IA Gemini)")
        st.write(resumo_ia.get('resumo_ia', 'Resumo não gerado ou com erro.'))
    else:
        st.warning("⚠️ Análises e Resumo da IA não disponíveis (Chave Gemini não configurada).")


    st.markdown("---")
    st.write("Esperamos que este relatório ajude a consertar o buraco!")

    # Opção para reiniciar o processo
    if st.button("Iniciar Nova Denúncia"):
        # Limpa o estado da sessão para recomeçar
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    # Opção para exibir dados brutos (útil para debug ou exportação)
    with st.expander("🔌 Ver Dados Brutos (JSON)"):
        st.json(dados_completos)

# --- Rodar a aplicação ---
# A execução principal do script Streamlit é gerenciada pelo próprio Streamlit.
# As funções são chamadas conforme o estado da sessão e as interações do usuário.
# O código abaixo é apenas para garantir que o script seja executado como um app Streamlit.
if __name__ == "__main__":
    # Streamlit cuida do loop principal, não precisamos de uma função main tradicional
    # O código fora das funções e no topo é executado em cada rerun.
    # O fluxo é controlado pelos ifs/elifs baseados em st.session_state.step
    pass # Nada a fazer aqui além do que já está no corpo principal do script