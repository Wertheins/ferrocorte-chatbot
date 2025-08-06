import gspread
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

try:
    gc = gspread.service_account(filename='credentials.json')
    spreadsheet = gc.open("teste")
    worksheet = spreadsheet.worksheet("Sheet2") 
    print("Conexão com a planilha 'teste' e aba 'Sheet2' bem-sucedida.")
except Exception as e:
    print(f"Erro fatal ao conectar com o Google Sheets: {e}")
    exit()

# Adicionamos uma "área de preparação" para os produtos encontrados
session_state = {
    "orcamento_atual": None,
    "ultimos_produtos_encontrados": [] # NOVA CHAVE
}

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)