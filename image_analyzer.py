import base64
import time
import logging
import google.generativeai as genai
from PIL import Image
import io
from typing import Dict, Any, Optional
import streamlit as st
from datetime import datetime

# Configuração de logging mais detalhada
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
            }
        }

    def verificar_qualidade_imagem(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Verifica se a imagem tem qualidade suficiente para análise.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            problemas = []
            status = True
            
            # Verifica dimensões mínimas
            if width < 200 or height < 200:
                problemas.append("Resolução muito baixa (mínimo 200x200 pixels)")
                status = False
            
            # Verifica tamanho do arquivo
            tamanho_kb = len(image_bytes)/1024
            if tamanho_kb < 10:  # 10KB
                problemas.append("Tamanho do arquivo muito pequeno (mínimo 10KB)")
                status = False
            elif tamanho_kb > 20000:  # 20MB
                problemas.append("Tamanho do arquivo muito grande (máximo 20MB)")
                status = False
            
            # Verifica proporção
            if width/height > 3 or height/width > 3:
                problemas.append("Proporção da imagem inadequada (máximo 3:1)")
                status = False
            
            return {
                "status": status,
                "width": width,
                "height": height,
                "size_kb": tamanho_kb,
                "problemas": problemas
            }
        except Exception as e:
            logger.error(f"Erro ao verificar qualidade da imagem: {str(e)}")
            return {
                "status": False,
                "problemas": [f"Erro ao processar imagem: {str(e)}"]
            }

def analisar_imagem_com_gemini(self, image_bytes: bytes, api_key: str) -> Dict[str, Any]:
    """
    Analisa uma imagem usando o modelo Gemini 1.5 Pro.
    """
    try:
        # Configura o modelo
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')  # Mudando para o modelo correto
        
        # Prepara a imagem como objeto PIL primeiro
        image = Image.open(io.BytesIO(image_bytes))
        
        # Converte para RGB se necessário (alguns formatos como RGBA podem causar problemas)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Salva em um buffer de bytes novo
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
            
        # Prompt para análise
        prompt = """
        Você é um especialista em análise de problemas em vias públicas.
        Analise a imagem fornecida e forneça uma análise técnica detalhada sobre o buraco ou defeito na via.
        
        Siga EXATAMENTE este formato na sua resposta:

        DESCRIÇÃO FÍSICA:
        - Tamanho aparente do buraco:
        - Forma e características:
        - Profundidade estimada:
        - Condições do asfalto ao redor:

        AVALIAÇÃO DE SEVERIDADE:
        - Nível: [BAIXO/MÉDIO/ALTO/CRÍTICO]
        - Justificativa:

        RISCOS IDENTIFICADOS:
        - Para veículos:
        - Para pedestres/ciclistas:
        - Outros riscos:

        CONDIÇÕES AGRAVANTES:
        - Problemas adicionais:
        - Fatores de risco:

        RECOMENDAÇÕES:
        - Tipo de intervenção:
        - Urgência do reparo:
        - Medidas temporárias:
        """

        logger.info("Iniciando análise com Gemini Pro Vision...")
        
        # Configurações de geração mais conservadoras
        generation_config = {
            "temperature": 0.7,  # Aumentando a temperatura para mais criatividade
            "top_p": 1.0,       # Aumentando para maior variedade
            "top_k": 40,
            "max_output_tokens": 2048,  # Aumentando o limite de tokens
        }
        
        # Configurações de segurança mais permissivas
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        # Gera a análise com retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Tentativa {attempt + 1} de {max_retries}")
                
                # Cria o conteúdo da mensagem
                message = genai.types.ContentDict(
                    parts = [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(img_byte_arr).decode('utf-8')
                            }
                        }
                    ],
                    role = "user"
                )
                
                # Gera o conteúdo
                response = model.generate_content(
                    message,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=False
                )
                
                logger.info(f"Resposta recebida na tentativa {attempt + 1}")
                logger.info(f"Response completo: {response}")
                
                if hasattr(response, 'text') and response.text:
                    logger.info("Análise concluída com sucesso")
                    return {
                        "status": "success",
                        "analise_visual": response.text.strip(),
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    }
                else:
                    logger.warning(f"Resposta vazia na tentativa {attempt + 1}")
                    if attempt == max_retries - 1:
                        raise ValueError("Todas as tentativas retornaram resposta vazia")
                    time.sleep(2)  # Espera 2 segundos antes da próxima tentativa
                    
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)  # Espera 2 segundos antes da próxima tentativa

    except Exception as e:
        logger.error(f"Erro fatal na análise de imagem: {str(e)}")
        return {
            "status": "error",
            "analise_visual": f"❌ Erro ao analisar imagem com IA: {str(e)}",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    def extrair_nivel_severidade(self, analise: str) -> str:
        """
        Extrai o nível de severidade da análise.
        """
        try:
            if "AVALIAÇÃO DE SEVERIDADE:" in analise:
                linhas = analise.split("\n")
                for linha in linhas:
                    if "Nível:" in linha:
                        for nivel in self.SEVERITY_LEVELS:
                            if nivel in linha:
                                return nivel
        except Exception as e:
            logger.error(f"Erro ao extrair nível de severidade: {str(e)}")
        return "INDEFINIDO"

    def get_severity_color(self, nivel: str) -> str:
        """
        Retorna a cor correspondente ao nível de severidade.
        """
        return self.SEVERITY_COLORS.get(nivel, self.SEVERITY_COLORS["INDEFINIDO"])

    def processar_analise_imagem(self, imagem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa e exibe a análise de imagem.
        """
        if not imagem_data or 'bytes' not in imagem_data:
            st.error("❌ Nenhuma imagem fornecida para análise.")
            return None

        # Verifica se temos a chave da API
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("❌ Chave da API Google (GOOGLE_API_KEY) não encontrada.")
            return None
            
        # Verifica qualidade da imagem
        qualidade = self.verificar_qualidade_imagem(imagem_data['bytes'])
        if not qualidade["status"]:
            st.warning("⚠️ Aviso sobre a qualidade da imagem:")
            for problema in qualidade["problemas"]:
                st.write(f"- {problema}")
            
            if not st.button("Continuar mesmo assim"):
                return None

            st.warning("Prosseguindo com a análise, mas os resultados podem não ser ideais.")

        # Análise da imagem
        with st.spinner("🔍 Analisando imagem com IA..."):
            try:
                logger.info(f"Processando imagem de {qualidade['size_kb']:.2f} KB")
                
                resultado_analise = self.analisar_imagem_com_gemini(
                    image_bytes=imagem_data['bytes'],
                    api_key=st.secrets["GOOGLE_API_KEY"]
                )

                if resultado_analise["status"] == "success":
                    # Extrai o nível de severidade
                    nivel = self.extrair_nivel_severidade(resultado_analise["analise_visual"])
                    cor = self.get_severity_color(nivel)

                    # Exibe o resultado
                    st.success("✅ Análise de imagem concluída!")
                    
                    # Cabeçalho com nível de severidade
                    st.markdown(
                        f"""
                        <div style='padding: 10px; border-radius: 5px; background-color: {cor}; color: white;'>
                            <h3 style='margin: 0; text-align: center;'>Nível de Severidade: {nivel}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Análise detalhada
                    st.markdown("### Análise Técnica Detalhada")
                    st.markdown(resultado_analise["analise_visual"])

                    # Prepara resultado
                    resultado_final = {
                        "analise_visual_ia": resultado_analise,
                        "nivel_severidade": nivel,
                        "qualidade_imagem": qualidade
                    }

                    return resultado_final

                else:
                    st.error(resultado_analise["analise_visual"])
                    return {"erro": resultado_analise["analise_visual"]}

            except Exception as e:
                error_msg = f"❌ Erro durante a análise: {str(e)}"
                st.error(error_msg)
                logger.error(f"Erro no processamento: {str(e)}")
                return {"erro": error_msg}

    def mostrar_feedback_analise(self, nivel: str) -> None:
        """
        Mostra feedback e recomendações baseadas no nível de severidade.
        """
        info = self.FEEDBACK_INFO.get(nivel, {
            "icon": "ℹ️",
            "mensagem": "Nível de severidade não determinado.",
            "prazo": "Prazo não definido."
        })

        st.info(f"{info['icon']} {info['mensagem']}\n\n{info['prazo']}")

# Funções para uso externo (mantendo compatibilidade com código existente)
def processar_analise_imagem(imagem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    analyzer = ImageAnalyzer()
    return analyzer.processar_analise_imagem(imagem_data)

def mostrar_feedback_analise(nivel: str) -> None:
    analyzer = ImageAnalyzer()
    analyzer.mostrar_feedback_analise(nivel)
