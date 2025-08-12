import gspread
import streamlit as st
from dotenv import load_dotenv
import json
from langchain_google_genai import ChatGoogleGenerativeAI
import sys

load_dotenv()

try:
    # A forma mais simples de saber se estamos rodando via Streamlit é verificar
    # se 'streamlit' está no comando que iniciou o programa.
    # 'streamlit' in sys.argv[0] verifica se o executável é o do Streamlit.
    is_streamlit_running = any('streamlit' in arg for arg in sys.argv)

    # Cenário 1: Rodando via Streamlit (seja localmente ou na nuvem)
    if is_streamlit_running:
        # Se estiver na nuvem, st.secrets terá 'gcp_creds'
        if "gcp_creds" in st.secrets:
            print("Conectando via Streamlit Secrets (Nuvem)...")
            creds = st.secrets["gcp_creds"]
            gc = gspread.service_account_from_dict(creds)
        # Se estiver rodando localmente com 'streamlit run', usa o arquivo json
        else:
            print("Conectando via arquivo local 'credentials.json' (modo Streamlit)...")
            gc = gspread.service_account(filename='credentials.json')

    # Cenário 2: Rodando via 'python main.py'
    else:
        print("Conectando via arquivo local 'credentials.json' (modo Terminal)...")
        gc = gspread.service_account(filename='credentials.json')

    spreadsheet = gc.open("Ferrocorte")
    worksheet = spreadsheet.worksheet("New Report")
    print("Conexão com a planilha bem-sucedida.")

except Exception as e:
    error_message = f"Erro fatal ao conectar com o Google Sheets: {e}"
    print(error_message)
    # Tenta mostrar o erro no Streamlit se a biblioteca estiver disponível
    try:
        st.error(f"Erro de conexão com a base de dados: {e}. Verifique se o arquivo 'credentials.json' está na pasta correta ou se os Streamlit secrets estão configurados.")
    except:
        pass # Ignora se o st.error falhar (estamos no terminal)
    exit()

# Adicionamos uma "área de preparação" para os produtos encontrados
session_state = {
    "orcamento_atual": None,
    "ultimos_produtos_encontrados": [] # NOVA CHAVE
}

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)