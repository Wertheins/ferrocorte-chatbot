import gspread
import streamlit as st
from dotenv import load_dotenv
import json
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

try:
    # Verifica se está rodando no ambiente do Streamlit e usa os secrets de forma estruturada
    if "gcp_creds" in st.secrets:
        # O Streamlit já converte o TOML para um dicionário, então podemos passar diretamente
        creds = st.secrets["gcp_creds"]
        gc = gspread.service_account_from_dict(creds)
    else:
        # Se não, usa o arquivo local (para rodar na sua máquina)
        gc = gspread.service_account(filename='credentials.json')

    spreadsheet = gc.open("Ferrocorte")
    worksheet = spreadsheet.worksheet("New Report")
    print("Conexão com a planilha bem-sucedida.")
except Exception as e:
    print(f"Erro fatal ao conectar com o Google Sheets: {e}")
    st.error(f"Erro de conexão com a base de dados: {e}")
    exit()

# Adicionamos uma "área de preparação" para os produtos encontrados
session_state = {
    "orcamento_atual": None,
    "ultimos_produtos_encontrados": [] # NOVA CHAVE
}

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)