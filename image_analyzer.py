import base64
import time
import logging
import google.generativeai as genai
from PIL import Image
import io
from typing import Dict, Any, Optional
import streamlit as st # Mantido aqui por causa de st.secrets e st.error/warning em analyze_image
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__) # Correto: usar __name__

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
            }
        }
        # Idealmente, a API Key seria passada aqui ou configurada uma vez.
        # Para manter a compatibilidade com o uso de st.secrets dentro dos métodos,
        # a configuração do genai é feita em analyze_image_with_gemini.

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
            
            tamanho_kb = len(image_bytes) / 1024.0 # Usar float para divisão
            if tamanho_kb < 10:
                problemas.append("Tamanho do arquivo muito pequeno (mínimo 10KB)")
                status = False
            elif tamanho_kb > 20000:
                problemas.append("Tamanho do arquivo muito grande (máximo 20MB)")
                status = False
            
            if max(width, height) / min(width, height) > 3 and min(width, height) > 0 : # Evitar divisão por zero
                problemas.append("Proporção da imagem inadequada (máximo 3:1 ou 1:3)")
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
                "width": 0, "height": 0, "size_kb": 0 # Adicionar valores padrão
            }

    def analyze_image_with_gemini(self, image_bytes: bytes, api_key: str) -> Dict[str, Any]:
        """
        Analisa uma imagem usando o modelo Gemini.
        """
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest') # Mantido conforme seu código
            
            image_pil = Image.open(io.BytesIO(image_bytes)) # Renomeado para evitar confusão
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')
            
            # O SDK do Python para Gemini pode aceitar objetos PIL.Image diretamente.
            # A conversão para bytes e base64 é mais comum para APIs REST diretas
            # ou se o SDK exigir explicitamente. Vamos tentar com PIL.Image diretamente
            # para simplificar, mas manteremos sua lógica de base64 se necessário.
            #
            # Para o SDK google-generativeai, a passagem de `image_pil` diretamente
            # em `model.generate_content([prompt, image_pil])` é geralmente suportada.
            # No entanto, seu código usa um formato `ContentDict` mais explícito, que espera `inline_data`.
            # Vamos manter sua abordagem com `inline_data` por enquanto, pois já está estruturada.

            img_byte_arr_jpeg = io.BytesIO()
            image_pil.save(img_byte_arr_jpeg, format='JPEG')
            img_byte_arr_val = img_byte_arr_jpeg.getvalue()

            prompt = """
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
            """
            # Removido o log "Iniciando análise com Gemini Pro Vision..." daqui, pois é mais genérico.
            # O nome do modelo já está definido.

            generation_config = {
                "temperature": 0.4, # Reduzir um pouco para respostas mais factuais e menos "criativas"
                "top_p": 1.0,
                "top_k": 32, # Ajustado ligeiramente
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
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(img_byte_arr_val).decode('utf-8')
                            }
                        }
                    ]
                    
                    response = model.generate_content(
                        parts, # Passando a lista de partes diretamente
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                        stream=False
                    )
                    
                    logger.info(f"Resposta recebida da API Gemini na tentativa {attempt + 1}.")

                    # Logar prompt_feedback se existir, pode indicar bloqueios ou outros problemas
                    if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                        logger.warning(f"Tentativa {attempt + 1}: Feedback do prompt: {response.prompt_feedback}")
                        # Se houver um bloqueio, o texto geralmente estará vazio
                        if response.prompt_feedback.block_reason:
                             logger.error(f"Tentativa {attempt + 1}: Conteúdo bloqueado. Razão: {response.prompt_feedback.block_reason}")
                             # Continua para a próxima tentativa, a menos que seja a última
                             if attempt == max_retries - 1:
                                 raise ValueError(f"Conteúdo bloqueado pela API após {max_retries} tentativas. Razão: {response.prompt_feedback.block_reason}")
                             time.sleep(2 + attempt) # Backoff incremental
                             continue


                    text_content = None
                    if hasattr(response, 'text') and response.text is not None:
                        text_content = response.text.strip()

                    if text_content:
                        logger.info(f"Análise de texto obtida com sucesso na tentativa {attempt + 1}.")
                        return {
                            "status": "success",
                            "analise_visual": text_content,
                            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    else:
                        logger.warning(f"Resposta de texto vazia ou inválida na tentativa {attempt + 1}.")
                        # Não levanta erro aqui ainda, deixa o loop de retry continuar
                
                except Exception as e:
                    logger.error(f"Erro durante a chamada da API Gemini na tentativa {attempt + 1}: {str(e)}")
                    # Se for um erro de cota (geralmente 429), pode ser útil não tentar novamente imediatamente
                    # ou ter uma estratégia de backoff mais longa. Por ora, o retry simples continua.
                
                # Se chegou aqui, a tentativa atual falhou em obter texto útil ou teve uma exceção não fatal
                if attempt < max_retries - 1:
                    logger.info(f"Aguardando para a próxima tentativa...")
                    time.sleep(2 + attempt) # Backoff incremental simples
                else: # Última tentativa
                    logger.error(f"Todas as {max_retries} tentativas de análise de imagem falharam em obter uma resposta válida.")
                    # Levanta o erro para ser pego pelo except externo da função.
                    # Se o último erro foi uma exceção específica (e não apenas texto vazio), e foi re-levantado,
                    # ele será pego aqui. Se foi texto vazio, levantamos um novo ValueError.
                    # Para simplificar, vamos levantar um ValueError genérico se sairmos do loop sem sucesso.
                    raise ValueError(f"Falha ao obter análise da imagem após {max_retries} tentativas.")

        except genai.types.BlockedPromptException as bpe: # Captura específica de bloqueio, se não pego antes
            logger.error(f"Erro fatal na análise: Prompt bloqueado. {bpe}")
            return {
                "status": "error",
                "analise_visual": f"❌ Erro: A solicitação foi bloqueada pela política de segurança. {bpe}",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Erro fatal e inesperado na análise de imagem: {str(e)}")
            return {
                "status": "error",
                "analise_visual": f"❌ Erro inesperado ao analisar imagem com IA: {str(e)}",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }

    def extract_severity_level(self, analise: str) -> str:
        try:
            if not isinstance(analise, str): # Checagem de tipo
                logger.warning("Tentativa de extrair severidade de um valor não string.")
                return "INDEFINIDO"
            
            # Busca mais robusta, case-insensitive e lidando com espaços
            for linha in analise.splitlines():
                if "nível:" in linha.lower(): # Case-insensitive
                    partes = linha.split(":")
                    if len(partes) > 1:
                        nivel_texto = partes[1].strip().upper() # Pega o texto após "Nível:", limpa e capitaliza
                        for nivel_valido in self.SEVERITY_LEVELS:
                            if nivel_valido == nivel_texto: # Comparação exata após normalização
                                return nivel_valido
                        # Se encontrar "Nível:" mas o valor não for um dos válidos, loga
                        logger.warning(f"Nível de severidade encontrado ('{nivel_texto}') mas não reconhecido. Linha: '{linha}'")
                        return "INDEFINIDO" # Ou continua procurando, dependendo da lógica desejada
            logger.warning(f"Padrão 'Nível:' não encontrado na análise para extração de severidade.")
        except Exception as e:
            logger.error(f"Erro ao extrair nível de severidade: {str(e)}")
        return "INDEFINIDO"


    def get_severity_color(self, nivel: str) -> str:
        return self.SEVERITY_COLORS.get(nivel, self.SEVERITY_COLORS["INDEFINIDO"])

    def analyze_image(self, imagem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not imagem_data or 'bytes' not in imagem_data:
            st.error("❌ Nenhuma imagem fornecida para análise.")
            logger.warning("analyze_image chamada sem imagem_data ou sem 'bytes'.")
            return None

        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("❌ Chave da API Google (GOOGLE_API_KEY) não configurada nos segredos.")
            logger.error("GOOGLE_API_KEY não encontrada nos segredos do Streamlit.")
            return {"erro": "Chave da API não configurada."} # Retornar dicionário de erro
            
        qualidade = self.check_image_quality(imagem_data['bytes'])
        logger.info(f"Qualidade da imagem: Status={qualidade['status']}, Problemas={qualidade.get('problemas', [])}")

        if not qualidade["status"]:
            st.warning("⚠️ Aviso sobre a qualidade da imagem:")
            for problema in qualidade["problemas"]:
                st.write(f"- {problema}")
            
            # Usar uma chave única para o botão para evitar problemas de estado do Streamlit
            if not st.button("Continuar com a análise mesmo assim", key="continuar_qualidade_ruim"):
                logger.info("Usuário optou por não continuar devido à qualidade da imagem.")
                return None 

            st.warning("Prosseguindo com a análise, mas os resultados podem não ser ideais.")

        with st.spinner("🔍 Analisando imagem com IA... Por favor, aguarde."):
            try:
                logger.info(f"Iniciando análise da imagem de {qualidade['size_kb']:.2f} KB com Gemini.")
                
                resultado_analise_gemini = self.analyze_image_with_gemini(
                    image_bytes=imagem_data['bytes'],
                    api_key=st.secrets["GOOGLE_API_KEY"]
                )

                if resultado_analise_gemini and resultado_analise_gemini.get("status") == "success":
                    analise_texto_visual = resultado_analise_gemini["analise_visual"]
                    nivel = self.extract_severity_level(analise_texto_visual)
                    cor = self.get_severity_color(nivel)
                    logger.info(f"Análise bem-sucedida. Nível de severidade extraído: {nivel}")

                    st.success("✅ Análise de imagem concluída!")
                    st.markdown(
                        f"""<div style='padding: 10px; border-radius: 5px; background-color: {cor}; color: white; text-align: center;'>
                            <h3 style='margin: 0;'>Nível de Severidade: {nivel}</h3>
                        </div><br>""", unsafe_allow_html=True)
                    st.markdown("### Análise Técnica Detalhada")
                    st.markdown(analise_texto_visual) # Usar st.markdown para melhor formatação

                    resultado_final = {
                        "analise_visual_ia": resultado_analise_gemini, # Contém status, texto, timestamp
                        "nivel_severidade": nivel,
                        "cor_severidade": cor,
                        "qualidade_imagem": qualidade,
                        "timestamp_geral": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    return resultado_final
                else:
                    # Erro vindo do analyze_image_with_gemini
                    erro_msg = resultado_analise_gemini.get("analise_visual", "Erro desconhecido na análise com IA.")
                    st.error(f"Falha na análise com IA: {erro_msg}")
                    logger.error(f"Falha reportada por analyze_image_with_gemini: {erro_msg}")
                    return {"erro": erro_msg}

            except Exception as e: # Captura exceções que podem ocorrer em analyze_image, fora de with_gemini
                error_msg = f"❌ Erro inesperado durante o processo de análise da imagem: {str(e)}"
                st.error(error_msg)
                logger.error(f"Erro no método analyze_image: {str(e)}", exc_info=True) # exc_info para traceback
                return {"erro": error_msg}

    def show_analysis_feedback(self, nivel: str) -> None:
        info = self.FEEDBACK_INFO.get(nivel) # Não precisa de valor padrão aqui se FEEDBACK_INFO cobre todos os SEVERITY_LEVELS + INDEFINIDO
        if not info: # Caso INDEFINIDO não esteja em FEEDBACK_INFO
             info = {
                "icon": "ℹ️",
                "mensagem": "Nível de severidade não determinado ou feedback não disponível.",
                "prazo": "Prazo não definido."
            }
        st.info(f"{info['icon']} **{info['mensagem']}**\n\n*Prazo recomendado para resolução: {info['prazo']}*")


# Funções wrapper para uso externo
def processar_analise_imagem(imagem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    analyzer = ImageAnalyzer()
    return analyzer.analyze_image(imagem_data)

def mostrar_feedback_analise(nivel: str) -> None:
    analyzer = ImageAnalyzer()
    analyzer.show_analysis_feedback(nivel)
