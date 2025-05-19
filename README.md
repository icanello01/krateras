# Krateras 🚀✨🔒: O Especialista Robótico de Denúncia de Buracos

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1MHVfh8aR8VeZwbV2wJfufL2ZNX9Hu1wb?usp=sharing)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[![Google Gemini](https://img.shields.io/badge/-Google_Gemini-blue?logo=google&logoColor=white)](https://ai.google.dev/)

[![Google Geocoding](https://img.shields.io/badge/-Google_Geocoding-blue?logo=googlemaps&logoColor=white)](https://developers.google.com/maps/documentation/geocoding)

[![ViaCEP](https://img.shields.io/badge/-ViaCEP-blue.svg)](https://viacep.com.br/)

[![Python 3.9](https://img.shields.io/badge/python-3.x-blue?logo=python&logoColor=white)](https://www.python.org/)

## Sobre o Projeto

Krateras (Cratera em grego antigo) é um projeto ambicioso e inteligente desenvolvido em Python para automatizar e aprimorar o processo de denúncia de buracos em ruas e vias públicas. Utilizando o poder da Inteligência Artificial (Google Gemini) e APIs de geolocalização (Google Maps Geocoding) e dados públicos (ViaCEP), Krateras transforma uma reclamação comum em um relatório técnico e priorizado, pronto para ser encaminhado às autoridades competentes.

**Versão Atual:** `v3.2 - Maximum Secure Colab Edition`
Esta versão foca na máxima segurança para suas chaves de API, prioritizando o uso de **Segredos do Google Colab** para mantê-las totalmente fora do código-fonte visível.

## Por Que Krateras?

Buracos são um problema persistente em muitas cidades, causando danos a veículos, acidentes e frustração. O processo de denúncia manual muitas vezes carece de detalhes técnicos e padronização, dificultando a triagem e priorização pelos órgãos públicos. Krateras visa resolver isso ao:

*   **Padronizar a Coleta de Dados:** Garante que informações essenciais (localização precisa, descrição detalhada) sejam coletadas de forma consistente.
*   **Aumentar a Precisão da Localização:** Utiliza Geocoding API (se disponível) ou coleta coordenadas/links manuais para identificar o ponto exato no mapa.
*   **Análise Inteligente:** O Google Gemini analisa a descrição do buraco, extraindo insights sobre severidade, perigos e contexto.
*   **Priorização Sugerida:** A IA sugere um nível de urgência (Baixa, Média, Alta, Crítica) com justificativa, ajudando na tomada de decisão de reparo.
*   **Sugestão de Causa e Ação:** A IA oferece palpites informados sobre a origem do problema e as ações necessárias.
*   **Geração de Relatório Completo:** Compila todos os dados coletados e as análises da IA em um resumo narrativo claro e objetivo.
*   **Segurança das Chaves:** Prioriza o uso de Segredos do Colab, protegendo suas credenciais de API.

## Como Funciona?

O script `krateras.ipynb` guia o usuário através de um processo interativo no ambiente Google Colab:

1.  **Inicialização:** Verifica e instala as dependências necessárias.
2.  **Gerenciamento de Chaves:** Tenta obter as chaves Google Gemini (`GOOGLE_API_KEY`) e Google Geocoding (`geocoding_api_key`) dos Segredos do Google Colab. Se não encontradas, solicita a entrada manual (com aviso de que a IA/Geocoding pode ser desabilitada).
3.  **Coleta de Dados do Denunciante:** Pede nome, idade e cidade de residência do usuário.
4.  **Coleta de Dados do Buraco:**
    *   Permite informar a localização pela rua/número/cidade/estado *manualmente* ou buscar por *CEP* (ViaCEP).
    *   Se o CEP for usado, preenche automaticamente os dados de endereço e pede confirmação.
    *   Pede o número mais próximo/referência e o lado da rua.
    *   **Processamento de Localização Exata:**
        *   Se uma chave de Geocoding for fornecida e dados básicos suficientes estiverem disponíveis (Rua, Número Próximo, Cidade, Estado), tenta obter Latitude/Longitude e um link do Google Maps via Google Maps Geocoding API.
        *   **Importante:** Se a geocodificação automática falhar ou não for possível (falta de chave/dados), solicita que o usuário forneça a localização *exata* manualmente (preferencialmente coordenadas Lat/Long ou um link do Google Maps que as contenha, ou uma descrição detalhada). O script tenta extrair coordenadas do input manual.
    *   Pede uma descrição *detalhada* do buraco (tamanho, profundidade, perigos, contexto, etc.).
5.  **Análise de IA (Google Gemini):** Se a chave Gemini foi fornecida e o modelo inicializado:
    *   Analisa a descrição detalhada para extrair insights estruturados.
    *   Sugere uma categoria de urgência e sua justificativa.
    *   Sugere possíveis causas e ações de reparo.
    *   Gera um resumo narrativo compilando todos os dados e análises.
6.  **Exibição do Relatório:** Apresenta um relatório final formatado contendo todos os dados coletados, a localização processada, e os resultados das análises e resumo gerados pela IA.

## Tecnologias Utilizadas

*   **Python:** Linguagem de programação principal.
*   **Google Colab:** Ambiente de execução baseado em notebook Jupyter, fornecendo acesso a GPUs (não usadas intensivamente aqui, mas útil para dependências e Secrets) e, crucialmente, o recurso de **Segredos (Secrets)**.
*   **`requests`:** Biblioteca Python para fazer requisições HTTP (usada para chamar APIs ViaCEP e Google Geocoding).
*   **`google-generativeai`:** Biblioteca Python para interagir com a API Google Gemini.
*   **ViaCEP API:** Serviço web para buscar dados de endereço a partir de um CEP.
*   **Google Maps Geocoding API:** Serviço web para converter endereços (como "Rua X, 123, Cidade Y") em coordenadas geográficas (Latitude, Longitude) e endereços formatados.
*   **Google Gemini API:** Modelo de linguagem grande usado para analisar a descrição do buraco, sugerir urgência, causas/ações e gerar o resumo final.
*   **Segredos do Google Colab:** Mecanismo seguro para armazenar variáveis de ambiente (como chaves de API) de forma segura *associadas à sua conta Google e ao notebook*, mas *separadas* do código visível.

## Segurança (O Ponto Forte desta Versão!)

A segurança das suas chaves de API é **prioridade máxima** em Krateras v3.2. Em vez de colar suas chaves diretamente no código (prática **NÃO** recomendada), o script tenta obtê-las dos **Segredos do Google Colab**.

**O que são Segredos do Colab?**
É uma forma de armazenar variáveis de ambiente (como chaves de API) de forma segura *associadas à sua conta Google e ao notebook*, mas *separadas* do código visível. Quando você compartilha o notebook, os segredos **NÃO** são compartilhados.

**Como Configurar Seus Segredos:**

1.  Abra este notebook no Google Colab.
2.  Clique no ícone de **chave** (🔑) na barra lateral esquerda.
3.  Clique em "Gerenciar segredos".
4.  Adicione dois novos segredos com os seguintes nomes **EXATOS**:
    *   Nome: `GOOGLE_API_KEY` | Valor: `[Sua Chave da API Google AI Studio/Vertex AI]`
    *   Nome: `geocoding_api_key` | Valor: `[Sua Chave da API Google Maps Geocoding]`
5.  Certifique-se de que o botão "Ativar acesso a segredos para este notebook" esteja ligado.

Pronto! Krateras agora pode acessar suas chaves sem que elas apareçam no código, mesmo se você compartilhar o notebook.

## Começando (Como Rodar)

1.  **Obtenha suas Chaves de API:**
    *   **Google Gemini API:** Crie uma chave em [Google AI Studio](https://aistudio.google.com/app/apikey) ou no Google Cloud Platform (Vertex AI). Esta chave é usada para as análises de IA.
    *   **Google Maps Geocoding API:** Crie uma chave API no [Google Cloud Platform Console](https://console.cloud.google.com/apis/credentials). Certifique-se de ativar a "Geocoding API" para o seu projeto nesta chave. Esta chave é usada para converter endereços em coordenadas automaticamente. **Atenção: O uso da Geocoding API PODE gerar custos dependendo do volume de requisições.**
2.  **Abra o Notebook:** Clique no badge "Open In Colab" no início deste README ou vá para o Google Colab e abra o arquivo `krateras.ipynb`.
3.  **Configure os Segredos:** Siga as instruções na seção [Segurança](#segurança) acima para adicionar suas chaves Gemini e Geocoding aos Segredos do Colab.
4.  **Execute as Células:** Rode as células do notebook sequencialmente no Google Colab. O script irá guiar você através da coleta de dados via input de texto no console.

O script instalará automaticamente as bibliotecas Python necessárias (`requests`, `google-generativeai`) se elas ainda não estiverem presentes.

## APIs Necessárias

*   **API Google AI Studio/Vertex AI (Gemini):** Nome do Segredo: `GOOGLE_API_KEY`
*   **API Google Maps Geocoding:** Nome do Segredo: `geocoding_api_key`

## Estrutura do Código (Alto Nível)

*   **Dependências:** Instalação via `subprocess`.
*   **Gerenciamento de Chaves:** Funções `get_api_keys` (lê de Segredos ou Input), `init_gemini`.
*   **Coleta de Dados:** Funções `coletar_dados_denunciante`, `buscar_cep` (integração ViaCEP), `coletar_dados_buraco` (lógica de input e geocodificação condicional).
*   **Análise de IA:** Funções `analisar_descricao_gemini`, `categorizar_urgencia_gemini`, `sugerir_causa_e_acao_gemini`, `gerar_resumo_completo_gemini` (interagem com o modelo Gemini).
*   **Saída:** Função `exibir_resumo_denuncia` (formata e imprime o relatório final).
*   **Fluxo Principal:** Função `main` orquestra a execução de todas as etapas.

## Melhorias Futuras Possíveis

*   Integração com outras APIs de mapas ou serviços públicos.
*   Interface de usuário mais amigável (ex: Streamlit, Gradio, ou integrar em um app web/móvel).
*   Suporte para upload e análise de imagens do buraco (utilizando modelos multimodais como Gemini Pro Vision).
*   Armazenamento dos relatórios gerados em banco de dados, planilha (Google Sheets) ou arquivo JSON automaticamente.
*   Validações de input mais robustas.
*   Re-execução de etapas específicas sem precisar rodar tudo de novo.

## Contribuindo

Sinta-se à vontade para abrir issues para sugestões ou reportar bugs, ou enviar Pull Requests com melhorias. Toda contribuição é bem-vinda!

## Autor

[Issame Canello / [GitHub](https://github.com/icanello01) / [LinkedIn](https://www.linkedin.com/in/issame-canello-006a2433b)

---

Espero que Krateras ajude a pavimentar um futuro com menos buracos! ✨
