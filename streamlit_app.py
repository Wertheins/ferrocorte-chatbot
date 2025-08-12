# streamlit_app.py

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Importamos o executor e a variável de estado que as ferramentas usam
from agent import master_agent_executor
from config import session_state # <-- Importação crucial

# --- Configuração da Página ---
st.set_page_config(page_title="Chatbot Ferrocorte Industrial", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Olá! Sou seu assistente virtual. Me diga qual produto você precisa e montarei seu orçamento.")

# --- Inicialização do Estado da Sessão ---
# Usamos o st.session_state, que é a forma correta de guardar dados no Streamlit
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Olá! Sou seu assistente de vendas da Ferrocorte. Como posso te ajudar hoje?")
    ]
if "orcamento_atual" not in st.session_state:
    st.session_state.orcamento_atual = None
if "ultimos_produtos_encontrados" not in st.session_state:
    st.session_state.ultimos_produtos_encontrados = []


# --- Exibe o histórico do chat ---
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI", avatar="🤖"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="👤"):
            st.write(message.content)

# --- Lógica de Interação ---
user_prompt = st.chat_input("Descreva o produto ou responda...", key="user_chat_input")

if user_prompt:
    st.session_state.chat_history.append(HumanMessage(content=user_prompt))
    with st.chat_message("Human", avatar="👤"):
        st.write(user_prompt)

    with st.chat_message("AI", avatar="🤖"):
        with st.spinner("Pensando..."):
            # ==================================================================
            # A CORREÇÃO CRÍTICA ESTÁ AQUI: SINCRONIZAÇÃO DE ESTADO
            # ==================================================================

            # 1. CARREGAR ESTADO: Antes de rodar, damos às ferramentas a memória
            #    salva na sessão do Streamlit.
            session_state["orcamento_atual"] = st.session_state.orcamento_atual
            session_state["ultimos_produtos_encontrados"] = st.session_state.ultimos_produtos_encontrados

            # Invoca o agente com o input e o histórico
            response = master_agent_executor.invoke({
                "input": user_prompt,
                "chat_history": st.session_state.chat_history
            })
            ai_response = response['output']

            # 2. SALVAR ESTADO: Depois que o agente roda, salvamos qualquer
            #    mudança de volta na sessão do Streamlit para a próxima rodada.
            st.session_state.orcamento_atual = session_state["orcamento_atual"]
            st.session_state.ultimos_produtos_encontrados = session_state["ultimos_produtos_encontrados"]

            # ==================================================================
            # FIM DA CORREÇÃO
            # ==================================================================

            st.write(ai_response)

    # Adiciona a resposta final ao histórico do chat
    st.session_state.chat_history.append(AIMessage(content=ai_response))

    # Força o rerender da página para mostrar a última mensagem
    st.rerun()