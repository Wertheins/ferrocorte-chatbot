# config.py
import streamlit as st
import gspread
import os
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Carregamento de Configurações e Credenciais do Streamlit Secrets ---

print("Carregando configurações e credenciais do Streamlit Secrets...")

# 1. Carrega as chaves da raiz do secrets.toml e define como variáveis de ambiente
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]

# 2. Reconstrói o dicionário de credenciais do Google Sheets a partir da seção [gcp_creds]
google_sheets_credentials_dict = {
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
}

# --- Conexão com a Planilha e LLM ---
try:
    # CORREÇÃO: Usa gspread.service_account_from_dict para passar as credenciais como um dicionário
    gc = gspread.service_account_from_dict(google_sheets_credentials_dict)
    
    spreadsheet = gc.open("Ferrocorte")
    worksheet = spreadsheet.worksheet("New Report")
    print("Conexão com a planilha 'Ferrocorte' e aba 'New Report' bem-sucedida.")
except Exception as e:
    error_message = f"Erro fatal ao conectar com o Google Sheets: {e}"
    print(error_message)
    st.error(error_message) # Mostra o erro na UI do Streamlit
    st.stop() # Interrompe a execução do script para evitar mais erros

# Dicionário de estado para a lógica do backend.
session_state = {
    "orcamento_atual": None
}

# Inicializa o LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)