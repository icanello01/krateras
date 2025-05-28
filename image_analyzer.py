import google.generativeai as genai
from PIL import Image
import io
from typing import Dict, Any
import streamlit as st

def verificar_qualidade_imagem(image_bytes: bytes) -> Dict[str, Any]:
    """
    Verifica se a imagem tem qualidade suficiente para análise.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        problemas = []
        status = True
        
        # Verifica dimensões
        if width < 200 or height < 200:
            problemas.append("Resolução muito baixa")
            status = False
            
        # Verifica tamanho do arquivo
        if len(image_bytes) < 10000:  # 10KB
            problemas.append("Tamanho do arquivo muito pequeno")
            status = False
            
        # Verifica proporção
        if width/height > 3 or height/width > 3:
            problemas.append("Proporção da imagem inadequada")
            status = False
            
        return {
            "status": status,
            "width": width,
            "height": height,
            "size_kb": len(image_bytes)/1024,
            "problemas": problemas
        }
    except Exception as e:
        return {
            "status": False,
            "problemas": [f"Erro ao processar imagem: {str(e)}"]
        }

def analisar_imagem_com_gemini(image_bytes: bytes, api_key: str) -> Dict[str, Any]:
    """
    Analisa uma imagem usando o modelo Gemini Vision Pro.
    """
    try:
        # Configura o modelo
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Configurações de segurança
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Prompt para análise
        prompt = """
        Você é um especialista em análise de problemas em vias públicas.
        Analise a imagem fornecida e forneça uma análise técnica detalhada seguindo EXATAMENTE este formato:

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

        # Gera a análise
        response = model.generate_content([prompt, image_bytes], safety_settings=safety_settings)
        
        if not response.text:
            return {
                "status": "error",
                "analise_visual": "❌ Não foi possível gerar uma análise para esta imagem."
            }

        return {
            "status": "success",
            "analise_visual": response.text.strip()
        }

    except Exception as e:
        return {
            "status": "error",
            "analise_visual": f"❌ Erro na análise de imagem: {str(e)}"
        }

def extrair_nivel_severidade(analise: str) -> str:
    """
    Extrai o nível de severidade da análise.
    """
    try:
        if "AVALIAÇÃO DE SEVERIDADE:" in analise:
            linhas = analise.split("\n")
            for linha in linhas:
                if "Nível:" in linha:
                    nivel = linha.split("[")[1].split("]")[0]
                    return nivel
    except:
        pass
    return "INDEFINIDO"

def get_severity_color(nivel: str) -> str:
    """
    Retorna a cor correspondente ao nível de severidade.
    """
    cores = {
        "BAIXO": "#28a745",    # Verde
        "MÉDIO": "#ffc107",    # Amarelo
        "ALTO": "#dc3545",     # Vermelho
        "CRÍTICO": "#6c1420",  # Vermelho escuro
        "INDEFINIDO": "#6c757d" # Cinza
    }
    return cores.get(nivel, cores["INDEFINIDO"])

def processar_analise_imagem(imagem_data: Dict[str, Any]) -> None:
    """
    Processa e exibe a análise de imagem.
    """
    if not imagem_data or 'bytes' not in imagem_data:
        st.error("❌ Nenhuma imagem fornecida para análise.")
        return

    # Verifica qualidade da imagem
    qualidade = verificar_qualidade_imagem(imagem_data['bytes'])
    if not qualidade["status"]:
        st.warning("⚠️ Aviso sobre a qualidade da imagem:")
        for problema in qualidade["problemas"]:
            st.write(f"- {problema}")
        
        if st.button("Continuar mesmo assim"):
            st.warning("Prosseguindo com a análise, mas os resultados podem não ser ideais.")
        else:
            st.stop()

    # Análise da imagem
    with st.spinner("🔍 Analisando imagem com IA..."):
        try:
            resultado_analise = analisar_imagem_com_gemini(
                image_bytes=imagem_data['bytes'],
                api_key=st.secrets["GOOGLE_API_KEY"]
            )

            if resultado_analise["status"] == "success":
                # Extrai o nível de severidade
                nivel = extrair_nivel_severidade(resultado_analise["analise_visual"])
                cor = get_severity_color(nivel)

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

                # Salva na sessão
                st.session_state.denuncia_completa['analise_visual_ia'] = resultado_analise
                st.session_state.denuncia_completa['nivel_severidade'] = nivel

            else:
                st.error(resultado_analise["analise_visual"])

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")

def mostrar_feedback_analise(nivel: str) -> None:
    """
    Mostra feedback e recomendações baseadas no nível de severidade.
    """
    feedback = {
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

    info = feedback.get(nivel, {
        "icon": "ℹ️",
        "mensagem": "Nível de severidade não determinado.",
        "prazo": "Prazo não definido."
    })

    st.info(f"{info['icon']} {info['mensagem']}\n\n{info['prazo']}")
