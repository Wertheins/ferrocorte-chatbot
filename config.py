# config.py
import streamlit as st
import gspread
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Tenta carregar variáveis de ambiente de um arquivo .env (para desenvolvimento local)
load_dotenv()

# --- Lógica de Carregamento de Credenciais ---
# Verifica se está rodando no ambiente do Streamlit Cloud
if hasattr(st, 'secrets'):
    # Carrega do Streamlit Secrets
    print("Carregando credenciais do Streamlit Secrets...")
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    # O TOML pode interpretar o JSON como uma string, então precisamos fazer o parse
    google_sheets_credentials_str = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
    google_sheets_credentials = json.loads(google_sheets_credentials_str)
    
else:
    # Carrega de arquivos locais (para rodar na sua máquina)
    print("Carregando credenciais de arquivos locais...")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_sheets_credentials = 'credentials.json'

# Seta a variável de ambiente para o LangChain
os.environ["GOOGLE_API_KEY"] = google_api_key

# --- Conexão com a Planilha e LLM ---
try:
    gc = gspread.service_account(credentials=google_sheets_credentials)
    spreadsheet = gc.open("Ferrocorte")
    worksheet = spreadsheet.worksheet("New Report")
    print("Conexão com a planilha 'Ferrocorte' e aba 'New Report' bem-sucedida.")
except Exception as e:
    print(f"Erro fatal ao conectar com o Google Sheets: {e}")
    st.error(f"Erro ao conectar com o Google Sheets: {e}") # Mostra o erro na UI
    exit()

# A variável de sessão do Streamlit é diferente da nossa "session_state" do backend.
# Esta continua sendo um dicionário simples para a lógica do backend.
session_state = {
    "orcamento_atual": None
}

# OBS: Removi 'ultimo_produto_isolado' pois não é mais usado na lógica final.
# Manter o dicionário limpo ajuda a evitar confusão.

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)