# -*- coding: utf-8 -*-
"""
Krateras 🚧🚧🚧: O Especialista Robótico de Denúncia de Buracos (v10.1 - Estabilidade Reforçada Final)
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
            st.success("✅ Dependências instaladas! Por favor, atualize a página (F5) ou reinicie o app.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Erro ao instalar dependências: {str(e)}")
            st.stop()

# check_install_dependencies()

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
.reportview-container .main .block-container {padding-top:2rem;padding-right:3rem;padding-left:3rem;padding-bottom:2rem;}
h1,h2,h3{color:#4A90E2;}
.stButton>button{background-color:#101217;color:white;font-weight:bold;border-radius:10px;padding:0.5rem 1rem;transition:all 0.2s ease-in-out;}
.stButton>button:hover{background-color:#101217;color:white;}
.stTextInput,.stNumberInput,.stTextArea,.stRadio,.stSelectbox,.stFileUploader{margin-bottom:10px;}
.stSpinner > div > div {border-top-color:#4A90E2 !important;}
div[data-testid="stInfo"]{border-left:5px solid #4A90E2 !important;}
div[data-testid="stWarning"]{border-left:5px solid #F5A623 !important;}
div[data-testid="stError"]{border-left:5px solid #D0021B !important;}
div[data-testid="stSuccess"]{border-left:5px solid #7ED321 !important;}
.streamlit-expanderHeader{font-size:1.1em !important;font-weight:bold !important;color:#4A90E2 !important;}
div[data-testid="stExpander"] div[role="button"] + div {padding-top:0.5rem !important;padding-bottom:0.5rem !important;}
</style>
""", unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 'start'
if 'denuncia_completa' not in st.session_state: st.session_state.denuncia_completa = {}
if 'api_keys_loaded' not in st.session_state: st.session_state.api_keys_loaded = False
if 'gemini_model' not in st.session_state: st.session_state.gemini_model = None
if 'geocoding_api_key' not in st.session_state: st.session_state.geocoding_api_key = None

def load_api_keys() -> tuple[Optional[str], Optional[str]]:
    gemini_key = st.secrets.get('GOOGLE_API_KEY')
    geocoding_key = st.secrets.get('geocoding_api_key')
    if not gemini_key: st.warning("⚠️ 'GOOGLE_API_KEY' não encontrada. IA (Texto e Imagem) desabilitada/limitada.")
    if not geocoding_key:
        st.warning("⚠️ 'geocoding_api_key' não encontrada. Geocodificação/mapa Google desabilitados.")
        st.info("ℹ️ Configure em `.streamlit/secrets.toml`:\n```toml\nGOOGLE_API_KEY=\"SUA_CHAVE\"\ngeocoding_api_key=\"SUA_CHAVE_GEO\"\n```")
    return gemini_key, geocoding_key

@st.cache_resource
def init_gemini_text_model(api_key: Optional[str]) -> Optional[genai.GenerativeModel]:
    if not api_key: st.error("❌ ERRO: Chave API Gemini não fornecida."); return None
    try:
        genai.configure(api_key=api_key)
        models = [m for m in list(genai.list_models()) if 'generateContent' in m.supported_generation_methods]
        preferred = ['gemini-1.5-flash-latest', 'gemini-1.0-pro-latest', 'gemini-pro']
        for name_suffix in preferred:
            if found := next((m for m in models if m.name.endswith(name_suffix)), None):
                st.success(f"✅ Modelo Texto Gemini: '{found.name.replace('models/','')}'."); return genai.GenerativeModel(found.name)
        if models: st.warning(f"⚠️ Fallback: '{models[0].name.replace('models/','')}'."); return genai.GenerativeModel(models[0].name)
        st.error("❌ ERRO: Nenhum modelo texto Gemini compatível."); return None
    except Exception as e: st.error(f"❌ ERRO: Falha init modelo texto Gemini."); st.exception(e); return None

def buscar_cep_uncached(cep: str) -> Dict[str, Any]:
    cep_limpo = re.sub(r'\D', '', cep)
    if len(cep_limpo) != 8: return {"erro": "CEP inválido."}
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=10); r.raise_for_status()
        data = r.json()
        if data.get('erro'): return {"erro": f"CEP '{cep_limpo}' não encontrado."}
        if not all(data.get(k) for k in ['logradouro', 'localidade', 'uf']): return {"erro": "Dados CEP incompletos."}
        return data
    except requests.exceptions.Timeout: return {"erro": "Timeout ViaCEP."}
    except requests.exceptions.RequestException as e: return {"erro": f"Erro ViaCEP: {e}."}
    except Exception as e: return {"erro": f"Erro inesperado ViaCEP: {e}."}

def geocodificar_endereco_uncached(rua: str, numero: str, cidade: str, estado: str, api_key: str) -> Dict[str, Any]:
    if not api_key: return {"erro": "Chave GeoAPI não fornecida."}
    if not all([rua, numero, cidade, estado]): return {"erro": "Endereço insuficiente."}
    address = f"{rua}, {numero}, {cidade}, {estado}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
    try:
        r = requests.get(url, timeout=10); r.raise_for_status()
        data = r.json()
        if data['status'] != 'OK':
            s, msg = data.get('status','DESCONHECIDO'), data.get('error_message','Sem mensagem.')
            err_map = {'ZERO_RESULTS':"Nenhum local.",'OVER_DAILY_LIMIT':"Limite API.",'OVER_QUERY_LIMIT':"Limite API.",
                       'REQUEST_DENIED':"Requisição API negada.",'INVALID_REQUEST':"Requisição inválida.",'UNKNOWN_ERROR':"Erro API."}
            return {"erro": f"Geo falhou. {err_map.get(s, f'Status: {s}. {msg}')}"}
        if not data['results']: return {"erro": "Geo falhou. Nenhum local."}
        loc = data['results'][0]['geometry']['location']; lat,lng = loc['lat'],loc['lng']
        fmt_addr = data['results'][0].get('formatted_address',address)
        return {"latitude":lat,"longitude":lng,"endereco_formatado_api":fmt_addr,
                "google_maps_link_gerado":f"https://www.google.com/maps/search/?api=1&query={lat},{lng}",
                "google_embed_link_gerado":f"https://www.google.com/maps/embed/v1/place?key={api_key}&q={lat},{lng}"}
    except requests.exceptions.Timeout: return {"erro": f"Timeout Geo: {address}"}
    except requests.exceptions.RequestException as e: return {"erro": f"Erro Comunicação Geo: {e}"}
    except Exception as e: return {"erro": f"Erro Inesperado Geo: {e}"}

SAFETY_SETTINGS = [{"category":cat,"threshold":"BLOCK_NONE"} for cat in ["HARM_CATEGORY_HARASSMENT","HARM_CATEGORY_HATE_SPEECH","HARM_CATEGORY_SEXUALLY_EXPLICIT","HARM_CATEGORY_DANGEROUS_CONTENT"]]

def _call_gemini_api(prompt: str, model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    """Helper para chamadas Gemini, tratando bloqueios e erros."""
    if not model: return {"text": "Modelo IA não disponível.", "error": True}
    try:
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if not response.parts:
            block = response.prompt_feedback.block_reason.name if hasattr(response,'prompt_feedback') and response.prompt_feedback.block_reason else "Sem conteúdo"
            finish = response.candidates[0].finish_reason.name if hasattr(response,'candidates') and response.candidates and hasattr(response.candidates[0],'finish_reason') else "N/A"
            return {"text": f"❌ Bloqueado/sem conteúdo. Bloqueio: {block}. Finalização: {finish}.", "error": True}
        return {"text": response.text.strip(), "error": False}
    except Exception as e: return {"text": f"❌ Erro API Gemini: {e}", "error": True}

@st.cache_data(show_spinner="🧠 Analisando características e observações...")
def analisar_caracteristicas_e_observacoes_gemini(_caracteristicas: Dict[str, Any], _observacoes: str, _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"insights": "🤖 Análise descrição IA offline."}
    fmt_carac = [f"- {k}: {', '.join(i for i in v if i and i!='Selecione') if isinstance(v,list) and any(i for i in v if i and i!='Selecione') else (v if isinstance(v,str) and v and v!='Selecione' else 'Não informado')}" for k,v in _caracteristicas.items()]
    carac_txt = "\n".join(fmt_carac)
    obs_txt = _observacoes.strip() if _observacoes else "N/A."
    prompt = textwrap.dedent(f"""
        Analise as características e observações de uma denúncia de buraco. Extraia insights cruciais.
        Formato: texto claro, marcadores (-). Se não puder inferir com ALTA CONFIANÇA, indique "Não especificado/inferido".
        Características:
        {carac_txt}
        Observações: "{obs_txt}"
        Categorias para Extrair/Inferir:
        - Severidade/Tamanho Estimado: [Consolidado]
        - Profundidade Estimada: [Consolidado]
        - Presença de Água/Alagamento: [Consolidado]
        - Tráfego Estimado na Via: [Consolidado]
        - Contexto da Via: [Consolidado]
        - Perigos Potenciais e Impactos (Observações): [Riscos das observações]
        - Contexto Adicional Local/Histórico (Observações): [Info das observações]
        - Sugestões de Ação/Recursos (Observações): [Sugestões das observações]
        - Identificadores Visuais Adicionais (Observações): [Ref. visuais das observações]
        - Palavras-chave Principais: [3-7 palavras-chave de todos os dados]
        Resposta limpa e estruturada.
    """)
    res = _call_gemini_api(prompt, _model)
    return {"insights": res["text"]}

@st.cache_data(show_spinner="🧠 Calculando Prioridade Robótica...")
def categorizar_urgencia_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"urgencia_ia": "🤖 Sugestão urgência IA offline."}
    carac = _dados_denuncia.get('buraco',{}).get('caracteristicas_estruturadas',{})
    obs, ins_txt = _dados_denuncia.get('observacoes_adicionais','N/A.'), _insights_ia_result.get('insights','N/A.')
    loc_ex = _dados_denuncia.get('localizacao_exata_processada',{}); tipo_loc, in_orig_loc = loc_ex.get('tipo','N/I'), loc_ex.get('input_original','N/I.')
    loc_ctx = f"Localização: Tipo: {tipo_loc}."
    if in_orig_loc!='N/I.': loc_ctx+=f" Detalhes: '{in_orig_loc}'."
    if tipo_loc in ['Coordenadas Fornecidas/Extraídas Manualmente','Geocodificada (API)','Coordenadas Extraídas de Link (Manual)']:
        loc_ctx+=f" Coords: {loc_ex.get('latitude')},{loc_ex.get('longitude')}. Link: {loc_ex.get('google_maps_link_gerado','N/A')}."
    fmt_carac = [f"- {k}: {', '.join(i for i in v if i and i!='Selecione') if isinstance(v,list) and any(i for i in v if i and i!='Selecione') else (v if isinstance(v,str) and v and v!='Selecione' else 'N/I')}" for k,v in carac.items()]
    carac_txt_prompt = "\n".join(fmt_carac)
    prompt = textwrap.dedent(f"""
        Sugira a MELHOR categoria de urgência para o reparo. Categorias: Baixa, Média, Alta, Imediata/Crítica.
        Dados:
        Local: Rua {(_dados_denuncia.get('buraco',{}).get('endereco',{})).get('rua','N/I')}, Nº Prox: {(_dados_denuncia.get('buraco',{})).get('numero_proximo','N/I')}. Cidade: {(_dados_denuncia.get('buraco',{}).get('endereco',{})).get('cidade_buraco','N/I')}, Estado: {(_dados_denuncia.get('buraco',{}).get('endereco',{})).get('estado_buraco','N/I')}.
        {loc_ctx}
        Características:
        {carac_txt_prompt}
        Observações: "{obs}"
        Insights: {ins_txt}
        Qual categoria e justificativa (máx. 2 frases)? Formato:
        Categoria Sugerida: [Categoria]
        Justificativa: [Justificativa]
    """)
    res = _call_gemini_api(prompt, _model)
    return {"urgencia_ia": res["text"]}

@st.cache_data(show_spinner="🧠 IA pensando em causas e ações...")
def sugerir_causa_e_acao_gemini(_dados_denuncia: Dict[str, Any], _insights_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"sugestao_acao_ia": "🤖 Sugestões causa/ação IA offline."}
    carac = _dados_denuncia.get('buraco',{}).get('caracteristicas_estruturadas',{})
    obs, ins_txt = _dados_denuncia.get('observacoes_adicionais','N/A.'), _insights_ia_result.get('insights','N/A.')
    fmt_carac = [f"- {k}: {', '.join(i for i in v if i and i!='Selecione') if isinstance(v,list) and any(i for i in v if i and i!='Selecione') else (v if isinstance(v,str) and v and v!='Selecione' else 'N/I')}" for k,v in carac.items()]
    carac_txt_prompt = "\n".join(fmt_carac)
    prompt = textwrap.dedent(f"""
        Sugira: 1. PÓSSIVEIS CAUSAS. 2. TIPOS DE AÇÃO/REPARO. Se não houver pistas, indique "Não especificado/inferido".
        Dados:
        Características:
        {carac_txt_prompt}
        Observações: "{obs}"
        Insights: {ins_txt}
        Formato:
        Possíveis Causas Sugeridas: [Causas ou 'Não especificado/inferido']
        Sugestões de Ação/Reparo Sugeridas: [Ações ou 'Não especificado/inferido']
    """)
    res = _call_gemini_api(prompt, _model)
    return {"sugestao_acao_ia": res["text"]}

def gerar_resumo_completo_gemini(_dados_denuncia_completa: Dict[str, Any], _insights_ia_result: Dict[str, Any], _urgencia_ia_result: Dict[str, Any], _sugestao_acao_ia_result: Dict[str, Any], _model: Optional[genai.GenerativeModel]) -> Dict[str, Any]:
    if not _model: return {"resumo_ia": "🤖 Resumo inteligente IA offline."}
    den, bur, end, carac, obs = _dados_denuncia_completa.get('denunciante',{}), _dados_denuncia_completa.get('buraco',{}), _dados_denuncia_completa.get('buraco',{}).get('endereco',{}), _dados_denuncia_completa.get('buraco',{}).get('caracteristicas_estruturadas',{}), _dados_denuncia_completa.get('observacoes_adicionais','N/A.')
    loc_ex, ins_txt, urg_ia_txt, sug_ac_txt = _dados_denuncia_completa.get('localizacao_exata_processada',{}), _insights_ia_result.get('insights','N/A.'), _urgencia_ia_result.get('urgencia_ia','N/A.'), (_sugestao_acao_ia_result or {}).get('sugestao_acao_ia','N/A.')
    tipo_loc_proc, in_orig_loc = loc_ex.get('tipo','N/I'), loc_ex.get('input_original','N/I.')
    mot_falha_geo = loc_ex.get('motivo_falha_geocodificacao_anterior')
    loc_info_res = f"Localização: Tipo: {tipo_loc_proc}."
    if tipo_loc_proc in ['Coordenadas Fornecidas/Extraídas Manualmente','Geocodificada (API)','Coordenadas Extraídas de Link (Manual)']:
         tipo_disp = tipo_loc_proc.replace('(API)','').replace('(Manual)','').replace('Fornecidas/Extraídas','Manual')
         loc_info_res = f"Loc. Exata: Coords {loc_ex.get('latitude')},{loc_ex.get('longitude')} (Via: {tipo_disp}). Link: {loc_ex.get('google_maps_link_gerado','N/A')}."
    elif tipo_loc_proc == 'Descrição Manual Detalhada': loc_info_res = f"Loc. via descrição: '{loc_ex.get('descricao_manual','N/I')}'."
    if in_orig_loc!='N/I.': loc_info_res += f" (Input: '{in_orig_loc}')"
    if mot_falha_geo: loc_info_res += f" (Nota: {mot_falha_geo})"
    fmt_carac = [f"- {k}: {', '.join(i for i in v if i and i!='Selecione') if isinstance(v,list) and any(i for i in v if i and i!='Selecione') else (v if isinstance(v,str) and v and v!='Selecione' else 'N/I')}" for k,v in carac.items()]
    carac_txt_prompt = "\n".join(fmt_carac)
    data_h = _dados_denuncia_completa.get('metadata',{}).get('data_hora_utc','N/R')
    prompt = textwrap.dedent(f"""
        Resumo narrativo conciso (máx. 10-12 frases) da denúncia. Formal, objetivo.
        Inclua: Denunciante, localização (rua, ref, bairro, cidade, estado, CEP), loc. EXATA, lado rua, características, observações, Análise Texto, Urgência IA, Causas/Ação IA.
        Dados:
        Denunciante: {den.get('nome','N/I')}, de {den.get('cidade_residencia','N/I')}.
        Endereço: Rua {end.get('rua','N/I')}, Nº Prox: {bur.get('numero_proximo','N/I')}. Bairro: {end.get('bairro','N/I')}. Cidade: {end.get('cidade_buraco','N/I')}, Est: {end.get('estado_buraco','N/I')}. CEP: {bur.get('cep_informado','N/I')}.
        Lado Rua: {bur.get('lado_rua','N/I')}.
        Loc. Exata: {loc_info_res}
        Características:
        {carac_txt_prompt}
        Observações: "{obs}"
        Insights Análise Texto: {ins_txt}
        Sugestão Urgência IA: {urg_ia_txt}
        Sugestões Causa/Ação IA: {sug_ac_txt}
        Resumo em português. Comece "Relatório Krateras: Denúncia de buraco..."
    """)
    res = _call_gemini_api(prompt, _model)
    return {"resumo_ia": res["text"]}

def next_step():
    steps = ['start','collect_denunciante','collect_address','collect_buraco_details_and_location','processing_ia','show_report']
    try:
        idx = steps.index(st.session_state.step)
        if idx < len(steps)-1: st.session_state.step = steps[idx+1]; st.rerun()
    except ValueError: st.session_state.step = steps[0]; st.rerun()

def prev_step():
    steps = ['start','collect_denunciante','collect_address','collect_buraco_details_and_location','processing_ia','show_report']
    try:
        idx = steps.index(st.session_state.step)
        if idx > 0: st.session_state.step = steps[idx-1]; st.rerun()
    except ValueError: st.session_state.step = steps[0]; st.rerun()

st.subheader("O Especialista Robótico de Denúncia de Buracos")

if st.session_state.step == 'start':
    st.write("Olá! Krateras v10.1! Sua missão: denunciar buracos. Fluxo otimizado, imagem, geolocalização (Google/OSM). IA (Gemini), APIs (Geocoding, ViaCEP).")
    if st.button("Iniciar Missão Denúncia!"):
        st.session_state.denuncia_completa = {"metadata":{"data_hora_utc":datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}}
        st.session_state.update({'cep_input_consolidated':'','cep_error_consolidated':False,'cep_success_message':'','cep_error_message':''})
        if 'buraco' in st.session_state: del st.session_state.buraco
        gemini_key, geocoding_key = load_api_keys()
        st.session_state.geocoding_api_key = geocoding_key
        st.session_state.gemini_model = init_gemini_text_model(gemini_key)
        st.session_state.api_keys_loaded = True; next_step()

elif st.session_state.step == 'collect_denunciante':
    st.header("--- 👤 Dados do Herói/Heroína ---")
    with st.form("form_denunciante"):
        curr_den = st.session_state.denuncia_completa.get('denunciante',{})
        nome = st.text_input("Nome completo:",value=curr_den.get('nome',''),key='n_den')
        idade = st.number_input("Idade (opcional):",0,120,value=curr_den.get('idade'),format="%d",key='i_den')
        cid_res = st.text_input("Sua cidade:",value=curr_den.get('cidade_residencia',''),key='c_r_den')
        if st.form_submit_button("Avançar"):
            if not nome or not cid_res: st.error("❗ Nome e Cidade são obrigatórios.")
            else:
                st.session_state.denuncia_completa['denunciante'] = {"nome":nome.strip(),"idade":idade if idade and idade>0 else None,"cidade_residencia":cid_res.strip()}
                st.success(f"Olá, {nome}!"); next_step()
    st.button("Voltar", on_click=prev_step)

elif st.session_state.step == 'collect_address':
    st.header("--- 🚧 Endereço Base do Buraco ---")
    if 'buraco' not in st.session_state: st.session_state.buraco = {'endereco':{}}
    if 'endereco' not in st.session_state.buraco: st.session_state.buraco['endereco'] = {}
    if 'cep_input_consolidated' not in st.session_state: st.session_state.cep_input_consolidated = st.session_state.buraco.get('endereco',{}).get('cep_informado','')
    for k_msg in ['cep_error_consolidated','cep_success_message','cep_error_message']:
        if k_msg not in st.session_state: st.session_state[k_msg] = False if 'error' in k_msg else ''
    
    st.subheader("Opção 1: Buscar por CEP")
    c1_cep,c2_cep = st.columns([3,1])
    with c1_cep:
         cep_in_val = st.text_input("CEP (só números):",max_chars=8,key='cep_f_k',value=st.session_state.cep_input_consolidated)
         if cep_in_val != st.session_state.cep_input_consolidated: st.session_state.cep_input_consolidated=cep_in_val
    with c2_cep:
         if st.button("Buscar CEP",key='bus_cep_k'):
             st.session_state.cep_success_message, st.session_state.cep_error_message = '', ''
             if not st.session_state.cep_input_consolidated: st.session_state.cep_error_consolidated,st.session_state.cep_error_message=True,"❗ Digite CEP."
             else:
                 with st.spinner("⏳ Buscando..."): data_cep_res = buscar_cep_uncached(st.session_state.cep_input_consolidated)
                 if 'erro' in data_cep_res: st.session_state.cep_error_consolidated,st.session_state.cep_error_message=True,f"❌ {data_cep_res['erro']}"
                 else:
                     st.session_state.cep_error_consolidated,st.session_state.cep_success_message=False,"✅ Endereço Encontrado!"
                     curr_end_st = st.session_state.buraco.get('endereco',{})
                     curr_end_st.update({k:data_cep_res.get(v,curr_end_st.get(k,'')) for k,v in {'rua':'logradouro','bairro':'bairro','cidade_buraco':'localidade','estado_buraco':'uf'}.items()})
                     st.session_state.buraco['endereco'] = curr_end_st
                     st.session_state.buraco['cep_informado'] = st.session_state.cep_input_consolidated
             st.rerun()
    if st.session_state.cep_success_message: st.success(st.session_state.cep_success_message)
    if st.session_state.cep_error_message: st.error(st.session_state.cep_error_message)

    st.markdown("---"); st.subheader("Opção 2: Digitar Endereço Manualmente")
    with st.form("form_manual_address"):
        rua_m = st.text_input("Rua:", value=st.session_state.buraco.get('endereco',{}).get('rua',''),key='r_m_k')
        bairro_m = st.text_input("Bairro (opc):", value=st.session_state.buraco.get('endereco',{}).get('bairro',''),key='b_m_k')
        cidade_m = st.text_input("Cidade:", value=st.session_state.buraco.get('endereco',{}).get('cidade_buraco',''),key='c_m_k')
        estado_m = st.text_input("UF:", value=st.session_state.buraco.get('endereco',{}).get('estado_buraco',''),max_chars=2,key='e_m_k')
        if st.form_submit_button("Confirmar Endereço e Avançar"):
            if not all([rua_m,cidade_m,estado_m]): st.error("❗ Rua, Cidade e Estado obrigatórios.")
            else:
                st.session_state.buraco['endereco'] = {'rua':rua_m.strip(),'bairro':bairro_m.strip(),'cidade_buraco':cidade_m.strip(),'estado_buraco':estado_m.strip().upper()}
                if st.session_state.cep_input_consolidated and 'cep_informado' not in st.session_state.buraco:
                     st.session_state.buraco['cep_informado'] = st.session_state.cep_input_consolidated
                st.session_state.denuncia_completa['buraco'] = st.session_state.buraco.copy(); next_step()
    st.button("Voltar", on_click=prev_step)

elif st.session_state.step == 'collect_buraco_details_and_location':
    st.header("--- 🚧 Detalhes Finais e Localização Exata ---")
    bur_data_curr = st.session_state.denuncia_completa.get('buraco',{})
    end_base = bur_data_curr.get('endereco',{})
    if not all(end_base.get(k) for k in ['rua','cidade_buraco','estado_buraco']):
         st.error("❗ Erro: Endereço base faltando."); 
         if st.button("Voltar",key="v_det_err_k"):prev_step(); st.stop()
    st.write(f"Endereço: **{end_base.get('rua','N/I')}**, {end_base.get('cidade_buraco','N/I')} - {end_base.get('estado_buraco','N/I')}")
    if end_base.get('bairro'): st.write(f"Bairro: **{end_base.get('bairro')}**")
    if bur_data_curr.get('cep_informado'): st.write(f"CEP: **{bur_data_curr.get('cep_informado')}**")
    st.markdown("---")
    with st.form("form_buraco_details_location"):
        st.subheader("📋 Características"); c1,c2=st.columns(2)
        with c1:
             opts_tam = ['Selecione','Pequeno (pneu)','Médio (>pneu, <faixa)','Grande (>faixa)','Enorme (cratera)','Crítico (risco grave)']
             opts_per = ['Selecione','Baixo (estético)','Médio (dano leve)','Alto (risco acidente/dano sério)','Altíssimo (risco grave iminente)']
             opts_prof = ['Selecione','Raso (<5cm)','Médio (5-15cm)','Fundo (15-30cm)','Muito Fundo (>30cm)']
             st.selectbox("Tamanho:", opts_tam, key='t_b'); st.selectbox("Perigo:", opts_per, key='p_b'); st.selectbox("Profundidade:", opts_prof, key='pr_b')
        with c2:
             opts_agua = ['Selecione','Seco','Pouca água','Muita água (piscina)','Drenagem visível']
             opts_traf = ['Selecione','Muito Baixo','Baixo','Médio','Alto','Muito Alto']
             opts_ctx = ['Reta','Curva','Cruzamento','Subida','Descida','Perto faixa pedestre','Perto semáforo/lombada','Área escolar','Área hospitalar','Área comercial','Via principal','Via secundária','Perto pto. ônibus','Perto ciclovia']
             st.selectbox("Água/Alagamento:", opts_agua, key='a_b'); st.selectbox("Tráfego Via:", opts_traf, key='traf_b_k_f'); st.multiselect("Contexto Via:", opts_ctx, key='c_b')
        st.subheader("✍️ Localização Exata e Outros"); k_np,k_lr,k_lm,k_ob = 'npbk','lrbk','lmbk','obk'
        st.text_input("Nº próximo/referência (ESSENCIAL!):",key=k_np); st.text_input("Lado da rua:",key=k_lr)
        st.markdown("""<p style="font-weight:bold;">Loc. EXATA (opc, recomendado):</p><p>COORDS (Lat,Long) ou LINK Maps. Ou DESCRIÇÃO DETALHADA.</p>""",unsafe_allow_html=True)
        st.text_input("Coords/Link/Descrição:",key=k_lm)
        st.subheader("📷 Foto (Opcional)"); upl_img = st.file_uploader("Carregar Imagem:",type=['jpg','jpeg','png','webp'],key='img_b_k')
        if upl_img: st.info(f"'{upl_img.name}' carregada.")
        st.subheader("📝 Observações Adicionais"); st.text_area("Suas observações:",key=k_ob)
        if st.form_submit_button("Enviar Denúncia para Análise Robótica!"):
            req_sel={'t_b':'Tamanho','p_b':'Perigo','pr_b':'Profundidade','a_b':'Água','traf_b_k_f':'Tráfego'}
            missing=[l for k,l in req_sel.items() if st.session_state.get(k)=='Selecione']
            if not all(st.session_state.get(k) for k in [k_np,k_lr,k_ob]): st.error("❗ Nº próximo, Lado rua e Observações obrigatórios.")
            elif missing: st.error(f"❗ Selecione: {', '.join(missing)}.")
            else:
                if 'buraco' not in st.session_state.denuncia_completa: st.session_state.denuncia_completa['buraco'] = {}
                st.session_state.denuncia_completa['buraco'].update({
                    'numero_proximo':st.session_state[k_np].strip(),'lado_rua':st.session_state[k_lr].strip(),
                    'caracteristicas_estruturadas':{
                        'Tamanho Estimado':st.session_state.t_b,'Perigo Estimado':st.session_state.p_b,
                        'Profundidade Estimada':st.session_state.pr_b,'Presença de Água/Alagamento':st.session_state.a_b,
                        'Tráfego Estimado na Via':st.session_state.traf_b_k_f,
                        'Contexto da Via':st.session_state.c_b if st.session_state.c_b else []},
                    'observacoes_adicionais':st.session_state[k_ob].strip()})
                st.session_state.denuncia_completa['buraco']['imagem_denuncia']=None
                if upl_img:
                    try: st.session_state.denuncia_completa['buraco']['imagem_denuncia'] = {"filename":upl_img.name,"type":upl_img.type,"bytes":upl_img.getvalue()}
                    except Exception as e: st.error(f"❌ Erro imagem: {e}."); st.session_state.denuncia_completa['buraco']['imagem_denuncia']={"erro":f"Erro: {e}"}
                st.session_state.denuncia_completa['localizacao_exata_processada']={"tipo":"Não informada"}
                t_geo,geo_ok,geo_r=False,False,{}
                r_b,c_b,e_b=end_base.get('rua'),end_base.get('cidade_buraco'),end_base.get('estado_buraco')
                num_ref_g = st.session_state[k_np].strip()
                tem_d_g = (st.session_state.geocoding_api_key and r_b and num_ref_g and c_b and e_b)
                if tem_d_g:
                    t_geo=True
                    with st.spinner("⏳ Geocodificando..."): geo_r=geocodificar_endereco_uncached(r_b,num_ref_g,c_b,e_b,st.session_state.geocoding_api_key)
                    if 'erro' not in geo_r:
                        geo_ok=True
                        st.session_state.denuncia_completa['localizacao_exata_processada'] = {"tipo":"Geocodificada (API)","latitude":geo_r['latitude'],"longitude":geo_r['longitude'],"endereco_formatado_api":geo_r.get('endereco_formatado_api',''),"google_maps_link_gerado":geo_r['google_maps_link_gerado'],"google_embed_link_gerado":geo_r.get('google_embed_link_gerado'),"input_original":num_ref_g}
                loc_m_v = st.session_state[k_lm].strip(); lat_m,lon_m,tipo_m_p=None,None,"Descrição Manual Detalhada"
                if loc_m_v:
                     mc=re.search(r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)',loc_m_v)
                     if mc:
                         try: t_la,t_lo=float(mc.group(1)),float(mc.group(2)); 
                         except ValueError: t_la,t_lo = None,None # Garantir que são None se falhar
                         if t_la is not None and -90<=t_la<=90 and t_lo is not None and -180<=t_lo<=180: lat_m,lon_m,tipo_m_p=t_la,t_lo,"Coordenadas Fornecidas/Extraídas Manualmente"
                     if lat_m is None and loc_m_v.startswith("http"):
                          mml=re.search(r'(?:/@|/search/\?api=1&query=)(-?\d+\.?\d*),(-?\d+\.?\d*)',loc_m_v)
                          if mml:
                              try: t_la,t_lo=float(mml.group(1)),float(mml.group(2)); 
                              except ValueError: t_la,t_lo = None,None
                              if t_la is not None and -90<=t_la<=90 and t_lo is not None and -180<=t_lo<=180: lat_m,lon_m,tipo_m_p=t_la,t_lo,"Coordenadas Extraídas de Link (Manual)"
                     if lat_m and lon_m:
                         st.session_state.denuncia_completa['localizacao_exata_processada']={"tipo":tipo_m_p,"input_original":loc_m_v,"latitude":lat_m,"longitude":lon_m,"google_maps_link_gerado":f"https://www.google.com/maps/search/?api=1&query={lat_m},{lon_m}","google_embed_link_gerado":f"https://www.google.com/maps/embed/v1/place?key={st.session_state.geocoding_api_key}&q={lat_m},{lon_m}" if st.session_state.geocoding_api_key else None}; geo_ok=True
                     elif loc_m_v and not geo_ok: st.session_state.denuncia_completa['localizacao_exata_processada']={"tipo":"Descrição Manual Detalhada","input_original":loc_m_v,"descricao_manual":loc_m_v}
                f_loc_d = st.session_state.denuncia_completa.get('localizacao_exata_processada',{}); f_loc_t=f_loc_d.get('tipo')
                if f_loc_t not in ['Coordenadas Fornecidas/Extraídas Manualmente','Coordenadas Extraídas de Link (Manual)','Geocodificada (API)']:
                     rsns=[];
                     if t_geo and 'erro' in geo_r: rsns.append(f"GeoAutoFalhou:{geo_r['erro']}")
                     elif not st.session_state.geocoding_api_key: rsns.append("ChaveGeoAPInãoFornecida.")
                     elif st.session_state.geocoding_api_key and not tem_d_g: rsns.append("DadosInsuficientesGeoAuto.")
                     if loc_m_v and not (lat_m and lon_m): rsns.append("CoordsNãoExtraídasInputManual.")
                     if rsns: f_loc_d['motivo_falha_geocodificacao_anterior']=" / ".join(rsns)
                     elif f_loc_t=="Não informada" and not f_loc_d.get('motivo_falha_geocodificacao_anterior'): f_loc_d['motivo_falha_geocodificacao_anterior']="CoordsNãoObtidas."
                     st.session_state.denuncia_completa['localizacao_exata_processada']=f_loc_d
                next_step()
    if st.button("Voltar",on_click=prev_step,key="v_det_btn_k"):pass

elif st.session_state.step == 'processing_ia':
    st.header("--- 🧠 Processamento Robótico de IA ---")
    bur_data,img_data_dict = st.session_state.denuncia_completa.get('buraco',{}), st.session_state.denuncia_completa.get('buraco',{}).get('imagem_denuncia')
    carac,obs = bur_data.get('caracteristicas_estruturadas',{}), bur_data.get('observacoes_adicionais','')
    st.session_state.denuncia_completa['resultado_analise_visual_krateras'] = None
    if img_data_dict and 'bytes' in img_data_dict:
        st.info("👁️‍🗨️ Iniciando Análise Visual..."); res_an_vis=processar_analise_imagem(img_data_dict)
        st.session_state.denuncia_completa['resultado_analise_visual_krateras']=res_an_vis
        if res_an_vis and res_an_vis.get("status")!="error" and "nivel_severidade" in res_an_vis:
            st.markdown("---");st.subheader("Feedback Adicional (Análise Visual)");mostrar_feedback_analise(res_an_vis["nivel_severidade"])
        elif res_an_vis and res_an_vis.get("status")=="error": st.caption("Nota: Análise visual reportou erro.")
        st.markdown("---")
    else:
        st.info("ℹ️ Nenhuma imagem, análise visual pulada.")
        st.session_state.denuncia_completa['resultado_analise_visual_krateras'] = {"status":"skipped","analise_visual":"Nenhuma imagem.","timestamp":datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
    fbks={'insights_ia':{"insights":"Análise IA Texto não realizada/erro."},'urgencia_ia':{"urgencia_ia":"Sugestão urgência IA Texto não gerada/erro."},'sugestao_acao_ia':{"sugestao_acao_ia":"Sugestões causa/ação IA Texto não geradas/erro."},'resumo_ia':{"resumo_ia":"Resumo IA Texto não gerado/erro."}}
    for k,v in fbks.items():
        if k not in st.session_state.denuncia_completa:st.session_state.denuncia_completa[k]=v.copy()
    with st.spinner("Executando análises IA (Texto)..."):
        st.session_state.denuncia_completa['insights_ia']=analisar_caracteristicas_e_observacoes_gemini(carac,obs,st.session_state.gemini_model)
        st.session_state.denuncia_completa['urgencia_ia']=categorizar_urgencia_gemini(st.session_state.denuncia_completa,st.session_state.denuncia_completa['insights_ia'],st.session_state.gemini_model)
        st.session_state.denuncia_completa['sugestao_acao_ia']=sugerir_causa_e_acao_gemini(st.session_state.denuncia_completa,st.session_state.denuncia_completa['insights_ia'],st.session_state.gemini_model)
        st.session_state.denuncia_completa['resumo_ia']=gerar_resumo_completo_gemini(st.session_state.denuncia_completa,st.session_state.denuncia_completa['insights_ia'],st.session_state.denuncia_completa['urgencia_ia'],st.session_state.denuncia_completa['sugestao_acao_ia'],st.session_state.gemini_model)
    next_step()

elif st.session_state.step == 'show_report':
    st.header("📊 RELATÓRIO FINAL DA DENÚNCIA KRATERAS 📊"); st.balloons()
    st.success("✅ MISSÃO CONCLUÍDA! RELATÓRIO GERADO. ✅")
    dados = st.session_state.denuncia_completa
    den, bur, end, carac, obs = dados.get('denunciante',{}), dados.get('buraco',{}), dados.get('buraco',{}).get('endereco',{}), dados.get('buraco',{}).get('caracteristicas_estruturadas',{}), dados.get('buraco',{}).get('observacoes_adicionais','N/A')
    loc_exata = dados.get('localizacao_exata_processada',{})
    res_analise_vis_rep = dados.get('resultado_analise_visual_krateras') # resultado_analise_visual_krateras é a chave correta
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
         if isinstance(carac, dict):
            carac_ex = {k:v for k,v in carac.items() if v and v!='Selecione' and (not isinstance(v,list) or any(i for i in v if i and i!='Selecione'))}
         if carac_ex:
             for k,v_li in carac_ex.items(): # v_list renomeado para v_li para não conflitar
                 if isinstance(v_li, list):
                     valid_v_it = [item for item in v_li if item and item != 'Selecione'] # valid_v_items renomeado
                     if valid_v_it: st.write(f"- **{k}:** {', '.join(valid_v_it)}")
                 else: st.write(f"- **{k}:** {v_li}")
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
                 delta_o = 0.005 
                 bbox_o = f"{lon_r-delta_o},{lat_r-delta_o},{lon_r+delta_o},{lat_r+delta_o}"
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
    
    # --- SEÇÃO DE ANÁLISE VISUAL MODIFICADA ---
    with st.expander("👁️‍🗨️ Resultado da Análise Visual da Imagem (Krateras Image Analyzer)", expanded=True):
        imagem_original_data = dados.get('buraco', {}).get('imagem_denuncia') # Pega os dados da imagem original

        # 1. Tenta exibir a imagem original primeiro
        if imagem_original_data and 'bytes' in imagem_original_data:
            try:
                st.image(io.BytesIO(imagem_original_data['bytes']), 
                         caption=f"Imagem original: {imagem_original_data.get('filename', 'Imagem Carregada')}", 
                         use_container_width=True)
            except Exception as e_img_display_report:
                st.error(f"❌ Não foi possível reexibir a imagem no relatório: {e_img_display_report}")
        elif imagem_original_data and 'erro' in imagem_original_data:
             st.warning(f"Houve um erro ao carregar a imagem originalmente: {imagem_original_data.get('erro')}")
        # Não exibir "nenhuma imagem" aqui ainda, pois a análise pode indicar isso.
        
        st.markdown("---") # Separador visual

        # 2. Processa o resultado da análise visual (res_analise_vis_rep)
        if res_analise_vis_rep: # Verifica se o dicionário de resultado da análise existe
            status_vis = res_analise_vis_rep.get("status") # Pega o status da análise visual
            
            if status_vis == "success":
                st.success("✅ Análise visual da imagem foi concluída com sucesso.")
                
                nivel_severidade_report = res_analise_vis_rep.get("nivel_severidade")
                cor_severidade_report = res_analise_vis_rep.get("cor_severidade")

                if nivel_severidade_report and cor_severidade_report:
                    st.markdown(
                        f"""<div style='padding:10px;border-radius:5px;background-color:{cor_severidade_report};color:white;text-align:center;'>
                            <h4 style='margin:0;'>Nível de Severidade (Análise Visual): {nivel_severidade_report}</h4>
                        </div><br>""", unsafe_allow_html=True)
                else:
                    st.info("Nível de severidade da análise visual não determinado ou não disponível.")

                analise_texto_visual_report = res_analise_vis_rep.get("analise_visual_ia", {}).get("analise_visual")
                if analise_texto_visual_report:
                    st.markdown("##### Análise Técnica Visual Detalhada (IA):")
                    st.markdown(analise_texto_visual_report) # Usar markdown para formatar
                else:
                    st.info("Texto da análise visual não disponível.")

                if nivel_severidade_report: # Mostrar feedback se o nível foi extraído
                    mostrar_feedback_analise(nivel_severidade_report) 
                
                qualidade_img_report = res_analise_vis_rep.get("qualidade_imagem", {})
                if qualidade_img_report and qualidade_img_report.get("status") is not None: 
                    status_qualidade_texto = 'Boa' if qualidade_img_report.get('status') else 'Com problemas detectados'
                    st.caption(f"Qualidade da Imagem Verificada: {status_qualidade_texto}")
                    if qualidade_img_report.get('problemas'):
                        st.caption(f"Problemas de qualidade: {', '.join(qualidade_img_report['problemas'])}")
                
                ts_visual_analise_ia = res_analise_vis_rep.get("analise_visual_ia", {}).get("timestamp")
                ts_geral_analise = res_analise_vis_rep.get("timestamp_geral")
                if ts_visual_analise_ia:
                    st.caption(f"Timestamp da análise Gemini Vision (UTC): {ts_visual_analise_ia}")
                elif ts_geral_analise : # Fallback para o timestamp geral se o da IA não estiver
                     st.caption(f"Timestamp do processamento da análise visual (UTC): {ts_geral_analise}")


            elif status_vis == "error":
                mensagem_erro_visual = res_analise_vis_rep.get('analise_visual', 'Detalhe do erro não disponível.')
                st.error(f"A análise visual da imagem encontrou um erro: {mensagem_erro_visual}")
                if not (imagem_original_data and 'bytes' in imagem_original_data): # Se não tinha imagem original
                    st.caption("Isso pode ter ocorrido porque nenhuma imagem foi fornecida ou houve falha no carregamento.")
            
            elif status_vis == "skipped":
                 mensagem_skip_visual = res_analise_vis_rep.get('analise_visual', 'Nenhuma imagem fornecida ou usuário optou por não analisar.')
                 st.info(f"ℹ️ Análise visual da imagem pulada: {mensagem_skip_visual}")
                 # Se foi pulada por falta de imagem, já foi indicado ao tentar exibir a imagem original.
            
            else: # Status não é 'success', 'error', nem 'skipped'
                st.warning("⚠️ Estado da análise visual indeterminado.")
                # Adicionar contexto se não havia imagem
                if not (imagem_original_data and 'bytes' in imagem_original_data):
                     st.caption("(Contexto: Nenhuma imagem foi fornecida para esta denúncia.)")
        else: 
            # res_analise_vis_rep é None ou não existe
            st.warning("⚠️ Dados da análise visual da imagem não encontrados no relatório.")
            # Verificar novamente se a imagem original existia para dar mais contexto
            if not (imagem_original_data and 'bytes' in imagem_original_data):
                 st.caption("(Contexto: Nenhuma imagem foi fornecida para esta denúncia.)")
    # --- FIM DA SEÇÃO DE ANÁLISE VISUAL MODIFICADA ---

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
        dados_json = dados.copy() # Trabalhar com uma cópia para não alterar o session_state
        
        # Omitir bytes da imagem principal da denúncia
        if 'buraco' in dados_json and 'imagem_denuncia' in dados_json['buraco']:
             img_d_main_json = dados_json['buraco'].get('imagem_denuncia')
             if img_d_main_json and isinstance(img_d_main_json, dict) and 'bytes' in img_d_main_json:
                  img_d_copy_main_json = img_d_main_json.copy()
                  img_d_copy_main_json['bytes'] = f"<dados binários omitidos - {len(img_d_main_json['bytes'])} bytes>"
                  dados_json['buraco']['imagem_denuncia'] = img_d_copy_main_json
        
        # O resultado da análise visual já deve ser JSON-friendly pelo image_analyzer.py
        # Não precisa de tratamento especial aqui, a menos que o image_analyzer.py retorne bytes.
        # No nosso caso, ele retorna o texto da análise e metadados.

        st.json(dados_json)

if __name__ == "__main__":
    pass
