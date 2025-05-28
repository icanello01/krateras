1  from google.adk.agents import Agent
2  from google.adk.runners import Runner
3  from google.adk.sessions import InMemorySessionService
4  from google.genai import types
5  from PIL import Image
6  import io
7  from typing import Dict, Any
8  import streamlit as st
9  
10 def verificar_qualidade_imagem(image_bytes: bytes) -> Dict[str, Any]:
11     """
12     Verifica se a imagem tem qualidade suficiente para análise.
13     """
14     try:
15         img = Image.open(io.BytesIO(image_bytes))
16         width, height = img.size
17         
18         problemas = []
19         status = True
20         
21         # Verifica dimensões
22         if width < 200 or height < 200:
23             problemas.append("Resolução muito baixa")
24             status = False
25             
26         # Verifica tamanho do arquivo
27         if len(image_bytes) < 10000:  # 10KB
28             problemas.append("Tamanho do arquivo muito pequeno")
29             status = False
30             
31         # Verifica proporção
32         if width/height > 3 or height/width > 3:
33             problemas.append("Proporção da imagem inadequada")
34             status = False
35             
36         return {
37             "status": status,
38             "width": width,
39             "height": height,
40             "size_kb": len(image_bytes)/1024,
41             "problemas": problemas
42         }
43     except Exception as e:
44         return {
45             "status": False,
46             "problemas": [f"Erro ao processar imagem: {str(e)}"]
47         }
48 
49 def analisar_imagem_com_agent(image_bytes: bytes, api_key: str) -> Dict[str, Any]:
50     """
51     Analisa uma imagem usando um Agente Gemini Vision especializado.
52     """
53     try:
54         # Configura o agente
55         agente_analise = Agent(
56             name="analista_buracos",
57             model="gemini-pro-vision",
58             description="Agente especializado em análise de buracos e problemas em vias públicas",
59             instruction="""Você é um especialista em análise de problemas em vias públicas.
60             Analise a imagem fornecida e forneça uma análise técnica detalhada seguindo EXATAMENTE este formato:
61 
62             DESCRIÇÃO FÍSICA:
63             - Tamanho aparente do buraco:
64             - Forma e características:
65             - Profundidade estimada:
66             - Condições do asfalto ao redor:
67 
68             AVALIAÇÃO DE SEVERIDADE:
69             - Nível: [BAIXO/MÉDIO/ALTO/CRÍTICO]
70             - Justificativa:
71 
72             RISCOS IDENTIFICADOS:
73             - Para veículos:
74             - Para pedestres/ciclistas:
75             - Outros riscos:
76 
77             CONDIÇÕES AGRAVANTES:
78             - Problemas adicionais:
79             - Fatores de risco:
80 
81             RECOMENDAÇÕES:
82             - Tipo de intervenção:
83             - Urgência do reparo:
84             - Medidas temporárias:
85 
86             ATENÇÃO: Mantenha EXATAMENTE este formato na resposta.
87             """
88         )
89 
90         # Configura sessão e runner
91         session_service = InMemorySessionService()
92         session = session_service.create_session(
93             app_name=agente_analise.name,
94             user_id="user1",
95             session_id="session1"
96         )
97 
98         runner = Runner(
99             agent=agente_analise,
100            app_name=agente_analise.name,
101            session_service=session_service
102        )
103
104        # Prepara conteúdo
105        content = types.Content(
106            role="user",
107            parts=[
108                types.Part(text="Analise esta imagem e forneça um relatório detalhado:"),
109                types.Part(inline_data=types.InlineData(
110                    mime_type="image/jpeg",
111                    data=image_bytes
112                ))
113            ]
114        )
115
116        # Coleta resposta
117        resposta_final = ""
118        for event in runner.run(
119            user_id="user1",
120            session_id="session1",
121            new_message=content
122        ):
123            if event.is_final_response():
124                for part in event.content.parts:
125                    if part.text is not None:
126                        resposta_final += part.text
127                        resposta_final += "\n"
128
129        if not resposta_final:
130            return {
131                "status": "error",
132                "analise_visual": "❌ Não foi possível gerar uma análise para esta imagem."
133            }
134
135        return {
136            "status": "success",
137            "analise_visual": resposta_final.strip()
138        }
139
140    except Exception as e:
141        return {
142            "status": "error",
143            "analise_visual": f"❌ Erro na análise de imagem: {str(e)}"
144        }
145
146 def extrair_nivel_severidade(analise: str) -> str:
147     """
148     Extrai o nível de severidade da análise.
149     """
150     try:
151         if "AVALIAÇÃO DE SEVERIDADE:" in analise:
152             linhas = analise.split("\n")
153             for linha in linhas:
154                 if "Nível:" in linha:
155                     nivel = linha.split("[")[1].split("]")[0]
156                     return nivel
157     except:
158         pass
159     return "INDEFINIDO"
160
161 def get_severity_color(nivel: str) -> str:
162     """
163     Retorna a cor correspondente ao nível de severidade.
164     """
165     cores = {
166         "BAIXO": "#28a745",    # Verde
167         "MÉDIO": "#ffc107",    # Amarelo
168         "ALTO": "#dc3545",     # Vermelho
169         "CRÍTICO": "#6c1420",  # Vermelho escuro
170         "INDEFINIDO": "#6c757d" # Cinza
171     }
172     return cores.get(nivel, cores["INDEFINIDO"])
173
174 def processar_analise_imagem(imagem_data: Dict[str, Any]) -> None:
175     """
176     Processa e exibe a análise de imagem.
177     """
178     if not imagem_data or 'bytes' not in imagem_data:
179         st.error("❌ Nenhuma imagem fornecida para análise.")
180         return
181
182     # Verifica qualidade da imagem
183     qualidade = verificar_qualidade_imagem(imagem_data['bytes'])
184     if not qualidade["status"]:
185         st.warning("⚠️ Aviso sobre a qualidade da imagem:")
186         for problema in qualidade["problemas"]:
187             st.write(f"- {problema}")
188         
189         if st.button("Continuar mesmo assim"):
190             st.warning("Prosseguindo com a análise, mas os resultados podem não ser ideais.")
191         else:
192             st.stop()
193
194     # Análise da imagem
195     with st.spinner("🔍 Analisando imagem com IA..."):
196         try:
197             resultado_analise = analisar_imagem_com_agent(
198                 image_bytes=imagem_data['bytes'],
199                 api_key=st.secrets["GOOGLE_API_KEY"]
200             )
201
202             if resultado_analise["status"] == "success":
203                 # Extrai o nível de severidade
204                 nivel = extrair_nivel_severidade(resultado_analise["analise_visual"])
205                 cor = get_severity_color(nivel)
206
207                 # Exibe o resultado
208                 st.success("✅ Análise de imagem concluída!")
209                 
210                 # Cabeçalho com nível de severidade
211                 st.markdown(
212                     f"""
213                     <div style='padding: 10px; border-radius: 5px; background-color: {cor}; color: white;'>
214                         <h3 style='margin: 0; text-align: center;'>Nível de Severidade: {nivel}</h3>
215                     </div>
216                     """,
217                     unsafe_allow_html=True
218                 )
219
220                 # Análise detalhada
221                 st.markdown("### Análise Técnica Detalhada")
222                 st.markdown(resultado_analise["analise_visual"])
223
224                 # Salva na sessão
225                 st.session_state.denuncia_completa['analise_visual_ia'] = resultado_analise
226                 st.session_state.denuncia_completa['nivel_severidade'] = nivel
227
228             else:
229                 st.error(resultado_analise["analise_visual"])
230
231         except Exception as e:
232             st.error(f"❌ Erro durante a análise: {str(e)}")
233
234 def mostrar_feedback_analise(nivel: str) -> None:
235     """
236     Mostra feedback e recomendações baseadas no nível de severidade.
237     """
238     feedback = {
239         "BAIXO": {
240             "icon": "✅",
241             "mensagem": "O problema identificado é de baixa severidade, mas ainda requer atenção.",
242             "prazo": "Recomenda-se resolução em até 30 dias."
243         },
244         "MÉDIO": {
245             "icon": "⚠️",
246             "mensagem": "O problema requer atenção moderada.",
247             "prazo": "Recomenda-se resolução em até 15 dias."
248         },
249         "ALTO": {
250             "icon": "🚨",
251             "mensagem": "O problema requer atenção urgente!",
252             "prazo": "Recomenda-se resolução em até 7 dias."
253         },
254         "CRÍTICO": {
255             "icon": "🆘",
256             "mensagem": "Situação crítica que requer ação imediata!",
257             "prazo": "Recomenda-se resolução em 24 horas."
258         }
259     }
260
261     info = feedback.get(nivel, {
262         "icon": "ℹ️",
263         "mensagem": "Nível de severidade não determinado.",
264         "prazo": "Prazo não definido."
265     })
266
267     st.info(f"{info['icon']} {info['mensagem']}\n\n{info['prazo']}")
