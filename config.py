# config.py
import streamlit as st
import gspread
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Tenta carregar variáveis de ambiente de um arquivo .env (para desenvolvimento local)
load_dotenv()

# --- Lógica de Carregamento de Credenciais e Configs ---

# Verifica se está rodando no ambiente do Streamlit Cloud
if hasattr(st, 'secrets'):
    print("Carregando credenciais e configurações do Streamlit Secrets...")
    
    # 1. Carrega as chaves da raiz do secrets.toml
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = google_api_key
    
    # Configurações do LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
    os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
    os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
    os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]

    # 2. Reconstrói o dicionário de credenciais do Google Sheets a partir da seção [gcp_creds]
    google_sheets_credentials = {
        "type": st.secrets.gcp_creds.type,
        "project_id": st.secrets.gcp_creds.project_id,
        "private_key_id": st.secrets.gcp_creds.private_key_id,
        "private_key": st.secrets.gcp_creds.private_key,
        "client_email": st.secrets.gcp_creds.client_email,
        "client_id": st.secrets.gcp_creds.client_id,
        "auth_uri": st.secrets.gcp_creds.auth_uri,
        "token_uri": st.secrets.gcp_creds.token_uri,
        "auth_provider_x509_cert_url": st.secrets.gcp_creds.auth_provider_x509_cert_url,
        "client_x509_cert_url": st.secrets.gcp_creds.client_x509_cert_url
        # "universe_domain" geralmente não é necessário para gspread, mas pode ser adicionado se preciso.
    }

else:
    # Carrega de arquivos locais (para rodar na sua máquina)
    print("Carregando credenciais e configurações de arquivos locais (.env e credentials.json)...")
    
    # A função load_dotenv() já carregou as variáveis de ambiente do .env
    # e o LangChain/Google as lerá automaticamente.
    google_sheets_credentials = 'credentials.json'

# --- Conexão com a Planilha e LLM ---
try:
    gc = gspread.service_account(credentials=google_sheets_credentials)
    spreadsheet = gc.open("Ferrocorte")
    worksheet = spreadsheet.worksheet("New Report")
    print("Conexão com a planilha 'Ferrocorte' e aba 'New Report' bem-sucedida.")
except Exception as e:
    error_message = f"Erro fatal ao conectar com o Google Sheets: {e}"
    print(error_message)
    # Se estiver no Streamlit, exibe o erro na UI
    if hasattr(st, 'secrets'):
        st.error(error_message)
    exit()

# Dicionário de estado para a lógica do backend.
# A sessão de chat do Streamlit (st.session_state) é separada e gerenciada no streamlit_app.py
session_state = {
    "orcamento_atual": None
}

# Inicializa o LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)