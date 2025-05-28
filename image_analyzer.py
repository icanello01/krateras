import base64
import time
import logging
import google.generativeai as genai
from PIL import Image
import io
from typing import Dict, Any # Optional removido de Dict
import streamlit as st 
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """
    Classe principal para análise de imagens de buracos em vias públicas.
    """
    
    def __init__(self):
        self.SEVERITY_LEVELS = ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"]
        self.SEVERITY_COLORS = {
            "BAIXO": "#28a745",    # Verde
            "MÉDIO": "#ffc107",    # Amarelo
            "ALTO": "#dc3545",     # Vermelho
            "CRÍTICO": "#6c1420",  # Vermelho escuro
            "INDEFINIDO": "#6c757d" # Cinza
        }
        self.FEEDBACK_INFO = {
            "BAIXO": {
                "icon": "✅",
                "mensagem": "O problema identificado é de baixa severidade, mas ainda requer atenção.",
                "prazo": "Recomenda-se resolução em até 30 dias."
            },
            "MÉDIO": {
                "icon": "⚠️",
                "mensagem": "O problema requer atenção moderada.",
                "prazo": "Recomenda-se resolução em até 15 dias."
            },
            "ALTO": {
                "icon": "🚨",
                "mensagem": "O problema requer atenção urgente!",
                "prazo": "Recomenda-se resolução em até 7 dias."
            },
            "CRÍTICO": {
                "icon": "🆘",
                "mensagem": "Situação crítica que requer ação imediata!",
                "prazo": "Recomenda-se resolução em 24 horas."
            },
            "INDEFINIDO": { # Adicionado feedback para nível indefinido
                "icon": "ℹ️",
                "mensagem": "Nível de severidade não pôde ser determinado a partir da análise visual.",
                "prazo": "Verifique manualmente e defina a urgência."
            }
        }

    def check_image_quality(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Verifica se a imagem tem qualidade suficiente para análise.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            problemas = []
            status = True
            
            if width < 200 or height < 200:
                problemas.append("Resolução muito baixa (mínimo 200x200 pixels)")
                status = False
            
            tamanho_kb = len(image_bytes) / 1024.0
            if tamanho_kb < 10:
                problemas.append("Tamanho do arquivo muito pequeno (mínimo 10KB)")
                status = False
            elif tamanho_kb > 20000: # 20MB é um limite alto, Gemini Vision geralmente prefere < 4MB
                problemas.append("Tamanho do arquivo muito grande (máximo 20MB, recomendado < 4MB)")
                status = False # Manter como False se for realmente um problema para a API
            
            if width > 0 and height > 0: # Evitar divisão por zero
                if max(width, height) / min(width, height) > 3 :
                    problemas.append("Proporção da imagem inadequada (máximo 3:1 ou 1:3)")
                    status = False
            else:
                problemas.append("Dimensões da imagem inválidas (largura ou altura é zero).")
                status = False

            return {
                "status": status,
                "width": width,
                "height": height,
                "size_kb": round(tamanho_kb, 2),
                "problemas": problemas
            }
        except Exception as e:
            logger.error(f"Erro ao verificar qualidade da imagem: {str(e)}")
            return {
                "status": False,
                "problemas": [f"Erro ao processar imagem: {str(e)}"],
                "width": 0, "height": 0, "size_kb": 0
            }

    def analyze_image_with_gemini(self, image_bytes: bytes, api_key: str) -> Dict[str, Any]:
        """
        Analisa uma imagem usando o modelo Gemini.
        """
        timestamp_agora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest') 
            
            image_pil = Image.open(io.BytesIO(image_bytes))
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')
            
            img_byte_arr_jpeg = io.BytesIO()
            # Adicionar otimização de qualidade para reduzir tamanho se necessário, mantendo qualidade razoável
            image_pil.save(img_byte_arr_jpeg, format='JPEG', quality=85, optimize=True)
            img_byte_arr_val = img_byte_arr_jpeg.getvalue()

            # Verificar tamanho após compressão para JPEG
            tamanho_processado_kb = len(img_byte_arr_val) / 1024.0
            logger.info(f"Tamanho da imagem para API Gemini (após conversão JPEG): {tamanho_processado_kb:.2f} KB")
            if tamanho_processado_kb > 3800: # Gemini Vision tem um limite de ~4MB para a imagem em si
                 logger.warning(f"Imagem para API ainda é grande ({tamanho_processado_kb:.2f} KB), pode causar problemas.")
                 # Poderia retornar um erro aqui ou tentar redimensionar mais agressivamente
                 # return {"status": "error", "analise_visual": "Imagem muito grande para processamento pela API após compressão.", "timestamp": timestamp_agora}


            prompt = textwrap.dedent("""
            Você é um especialista em análise de problemas em vias públicas.
            Analise a imagem fornecida e forneça uma análise técnica detalhada sobre o buraco ou defeito na via.
            
            Siga EXATAMENTE este formato na sua resposta:

            DESCRIÇÃO FÍSICA:
            - Tamanho aparente do buraco: [Descreva o tamanho, por exemplo, pequeno, médio, grande, ou dimensões aproximadas se visível]
            - Forma e características: [Descreva a forma, por exemplo, circular, irregular, bordas afiadas, etc.]
            - Profundidade estimada: [Descreva a profundidade, por exemplo, rasa, moderada, profunda, ou estimativa em cm/polegadas se possível]
            - Condições do asfalto ao redor: [Descreva o asfalto, por exemplo, rachado, desgastado, intacto, etc.]

            AVALIAÇÃO DE SEVERIDADE:
            - Nível: [BAIXO/MÉDIO/ALTO/CRÍTICO]
            - Justificativa: [Explique o porquê do nível de severidade escolhido]

            RISCOS IDENTIFICADOS:
            - Para veículos: [Descreva os riscos, por exemplo, danos a pneus/suspensão, perda de controle]
            - Para pedestres/ciclistas: [Descreva os riscos, por exemplo, tropeços, quedas, desvio para tráfego]
            - Outros riscos: [Se houver, por exemplo, acúmulo de água, etc.]

            CONDIÇÕES AGRAVANTES:
            - Problemas adicionais: [Se houver, por exemplo, múltiplos buracos, má iluminação na área, etc.]
            - Fatores de risco: [Se houver, por exemplo, tráfego intenso, área escolar, curva perigosa]

            RECOMENDAÇÕES:
            - Tipo de intervenção: [Sugira o tipo de reparo, por exemplo, tapa-buraco, recapeamento parcial, etc.]
            - Urgência do reparo: [Com base na severidade, por exemplo, imediato, em poucos dias, planejado]
            - Medidas temporárias: [Se aplicável, por exemplo, sinalização, cones, placa metálica]
            """)

            generation_config = {
                "temperature": 0.4, 
                "top_p": 1.0,
                "top_k": 32, 
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            max_retries = 3
            for attempt in range(max_retries):
                logger.info(f"Tentativa {attempt + 1} de {max_retries} para análise com Gemini.")
                try:
                    parts = [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg", # Enviando como JPEG
                                "data": base64.b64encode(img_byte_arr_val).decode('utf-8')
                            }
                        }
                    ]
                    
                    response = model.generate_content(
                        parts,
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                        stream=False
                    )
                    
                    logger.info(f"Resposta recebida da API Gemini na tentativa {attempt + 1}.")

                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                        block_reason_name = response.prompt_feedback.block_reason.name
                        logger.error(f"Tentativa {attempt + 1}: Conteúdo bloqueado pela API Gemini. Razão: {block_reason_name}")
                        if attempt == max_retries - 1:
                            return {
                                "status": "error", 
                                "analise_visual": f"Conteúdo bloqueado pela API após {max_retries} tentativas. Razão: {block_reason_name}",
                                "timestamp": timestamp_agora
                            }
                        time.sleep(2 + attempt) 
                        continue # Próxima tentativa

                    text_content = None
                    if hasattr(response, 'text') and response.text is not None:
                        text_content = response.text.strip()

                    if text_content:
                        logger.info(f"Análise de texto obtida com sucesso na tentativa {attempt + 1}.")
                        return {
                            "status": "success",
                            "analise_visual": text_content,
                            "timestamp": timestamp_agora # Usar o timestamp do início da função
                        }
                    else:
                        logger.warning(f"Resposta de texto vazia ou inválida na tentativa {attempt + 1} da API Gemini.")
                
                except Exception as e:
                    logger.error(f"Erro durante a chamada da API Gemini na tentativa {attempt + 1}: {str(e)}", exc_info=True)
                
                if attempt < max_retries - 1:
                    logger.info(f"Aguardando para a próxima tentativa...")
                    time.sleep(2 + attempt) 
                else: 
                    logger.error(f"Todas as {max_retries} tentativas de análise de imagem falharam em obter uma resposta válida da API Gemini.")
                    return {
                        "status": "error",
                        "analise_visual": f"Falha ao obter análise da imagem da API Gemini após {max_retries} tentativas.",
                        "timestamp": timestamp_agora
                    }
            # Se o loop terminar sem return (não deveria acontecer com a lógica acima)
            return {
                "status": "error", 
                "analise_visual": "Falha inesperada no loop de tentativas da API Gemini.",
                "timestamp": timestamp_agora
            }

        except genai.types.BlockedPromptException as bpe:
            logger.error(f"Erro fatal na análise: Prompt bloqueado pela API Gemini. {bpe}")
            return {
                "status": "error",
                "analise_visual": f"❌ Erro: A solicitação foi bloqueada pela política de segurança da API Gemini. {bpe}",
                "timestamp": timestamp_agora
            }
        except Exception as e:
            logger.error(f"Erro fatal e inesperado na configuração ou chamada inicial da API Gemini: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "analise_visual": f"❌ Erro inesperado ao configurar ou chamar API Gemini: {str(e)}",
                "timestamp": timestamp_agora
            }

    def extract_severity_level(self, analise: str) -> str:
        try:
            if not isinstance(analise, str):
                logger.warning("Tentativa de extrair severidade de um valor não string.")
                return "INDEFINIDO"
            
            for linha in analise.splitlines():
                if "nível:" in linha.lower(): 
                    partes = linha.split(":")
                    if len(partes) > 1:
                        nivel_texto = partes[1].strip().upper() 
                        for nivel_valido in self.SEVERITY_LEVELS:
                            if nivel_valido == nivel_texto: 
                                return nivel_valido
                        logger.warning(f"Nível de severidade encontrado ('{nivel_texto}') mas não reconhecido. Linha: '{linha}'")
                        return "INDEFINIDO" 
            logger.info(f"Padrão 'Nível:' não encontrado na análise para extração de severidade.") # Mudado para INFO
        except Exception as e:
            logger.error(f"Erro ao extrair nível de severidade: {str(e)}")
        return "INDEFINIDO"


    def get_severity_color(self, nivel: str) -> str:
        return self.SEVERITY_COLORS.get(nivel, self.SEVERITY_COLORS["INDEFINIDO"])

    def analyze_image(self, imagem_data: Dict[str, Any]) -> Dict[str, Any]: # MUDADO: Retorno sempre Dict
        """
        Processa e exibe a análise de imagem.
        """
        timestamp_geral_inicio = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if not imagem_data or 'bytes' not in imagem_data:
            msg = "Nenhuma imagem fornecida para análise."
            st.error(f"❌ {msg}")
            logger.warning("analyze_image chamada sem imagem_data ou sem 'bytes'.")
            return {"status": "error", "analise_visual": msg, "timestamp_geral": timestamp_geral_inicio}

        if "GOOGLE_API_KEY" not in st.secrets:
            msg = "Chave da API Google (GOOGLE_API_KEY) não configurada nos segredos."
            st.error(f"❌ {msg}")
            logger.error("GOOGLE_API_KEY não encontrada nos segredos do Streamlit.")
            return {"status": "error", "analise_visual": msg, "timestamp_geral": timestamp_geral_inicio}
            
        qualidade = self.check_image_quality(imagem_data['bytes'])
        logger.info(f"Qualidade da imagem: Status={qualidade['status']}, Problemas={qualidade.get('problemas', [])}, Tamanho KB: {qualidade.get('size_kb')}")


        if not qualidade["status"]:
            st.warning("⚠️ Aviso sobre a qualidade da imagem:")
            for problema in qualidade["problemas"]:
                st.write(f"- {problema}")
            
            # Usar uma chave única para o botão para evitar problemas de estado do Streamlit
            if not st.button("Continuar com a análise mesmo assim", key=f"continuar_qualidade_ruim_{int(time.time())}"):
                msg = "Usuário optou por não continuar devido à qualidade da imagem."
                logger.info(msg)
                return {
                    "status": "skipped", 
                    "analise_visual": msg, 
                    "qualidade_imagem": qualidade, # Inclui info da qualidade
                    "timestamp_geral": timestamp_geral_inicio
                } 

            st.warning("Prosseguindo com a análise, mas os resultados podem não ser ideais.")

        # Análise da imagem
        # O spinner já é gerenciado pelo image_analyzer se chamado de um app Streamlit.
        # Se este módulo for usado fora do Streamlit, o spinner não aparecerá, o que é ok.
        # Usar st.spinner aqui pode causar spinners aninhados se o app.py também usar.
        # É melhor deixar o app.py gerenciar o spinner principal.
        # No entanto, para feedback visual que esta parte está rodando:
        if hasattr(st, 'spinner'): # Checa se estamos em um contexto Streamlit
            spinner_msg = "🔍 Analisando imagem com IA (Krateras Image Analyzer)..."
        else:
            spinner_msg = None # Não usar spinner se não for Streamlit

        try:
            if spinner_msg:
                with st.spinner(spinner_msg):
                    logger.info(f"Iniciando análise da imagem de {qualidade.get('size_kb', 0):.2f} KB com Gemini.")
                    resultado_analise_gemini = self.analyze_image_with_gemini(
                        image_bytes=imagem_data['bytes'],
                        api_key=st.secrets["GOOGLE_API_KEY"]
                    )
            else: # Executa sem spinner
                logger.info(f"Iniciando análise da imagem de {qualidade.get('size_kb', 0):.2f} KB com Gemini (sem spinner st).")
                resultado_analise_gemini = self.analyze_image_with_gemini(
                    image_bytes=imagem_data['bytes'],
                    api_key=st.secrets["GOOGLE_API_KEY"]
                )


            if resultado_analise_gemini and resultado_analise_gemini.get("status") == "success":
                analise_texto_visual = resultado_analise_gemini["analise_visual"]
                nivel = self.extract_severity_level(analise_texto_visual)
                cor = self.get_severity_color(nivel)
                logger.info(f"Análise visual bem-sucedida. Nível de severidade extraído: {nivel}")

                # A UI de sucesso é gerenciada pelo image_analyzer.py
                st.success("✅ Análise de imagem concluída pelo Krateras Image Analyzer!")
                st.markdown(
                    f"""<div style='padding: 10px; border-radius: 5px; background-color: {cor}; color: white; text-align: center;'>
                        <h3 style='margin: 0;'>Nível de Severidade (Análise Visual): {nivel}</h3>
                    </div><br>""", unsafe_allow_html=True)
                st.markdown("### Análise Técnica Visual Detalhada (IA)")
                st.markdown(analise_texto_visual)

                resultado_final = {
                    "status": "success", # ADICIONADO STATUS NO NÍVEL RAIZ
                    "analise_visual_ia": resultado_analise_gemini, 
                    "nivel_severidade": nivel,
                    "cor_severidade": cor,
                    "qualidade_imagem": qualidade,
                    "timestamp_geral": timestamp_geral_inicio 
                }
                return resultado_final
            else:
                erro_msg = resultado_analise_gemini.get("analise_visual", "Erro desconhecido na análise com IA Gemini.")
                st.error(f"Falha na análise com IA Gemini: {erro_msg}")
                logger.error(f"Falha reportada por analyze_image_with_gemini: {erro_msg}")
                return {
                    "status": "error", 
                    "analise_visual": erro_msg, 
                    "qualidade_imagem": qualidade, # Inclui info da qualidade mesmo em erro
                    "timestamp_geral": timestamp_geral_inicio
                }

        except Exception as e: 
            error_msg = f"❌ Erro inesperado durante o processo de análise da imagem: {str(e)}"
            st.error(error_msg)
            logger.error(f"Erro no método analyze_image: {str(e)}", exc_info=True)
            return {
                "status": "error", 
                "analise_visual": error_msg,
                "qualidade_imagem": qualidade, # Inclui info da qualidade mesmo em erro
                "timestamp_geral": timestamp_geral_inicio
            }

    def show_analysis_feedback(self, nivel: str) -> None:
        """
        Mostra feedback e recomendações baseadas no nível de severidade.
        """
        # Usa get com um dicionário padrão para o caso de 'INDEFINIDO' ou outro nível não mapeado
        info = self.FEEDBACK_INFO.get(nivel, self.FEEDBACK_INFO.get("INDEFINIDO", {
            "icon": "ℹ️",
            "mensagem": "Nível de severidade não determinado ou feedback não disponível.",
            "prazo": "Prazo não definido."
        }))

        st.info(f"{info['icon']} **{info['mensagem']}**\n\n*Prazo recomendado para resolução: {info['prazo']}*")


# Funções wrapper para uso externo
def processar_analise_imagem(imagem_data: Dict[str, Any]) -> Dict[str, Any]: # MUDADO: Retorno sempre Dict
    analyzer = ImageAnalyzer()
    return analyzer.analyze_image(imagem_data)

def mostrar_feedback_analise(nivel: str) -> None:
    analyzer = ImageAnalyzer()
    analyzer.show_analysis_feedback(nivel)
