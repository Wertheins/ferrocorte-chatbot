# streamlit_app.py

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from agent import master_agent_executor

# --- Configuração da Página ---
st.set_page_config(page_title="Chatbot Ferrocorte Industrial", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Olá! Sou seu assistente virtual. Me diga qual produto você precisa e montarei seu orçamento.")

# --- Inicialização do Estado da Sessão ---
# A única coisa que precisamos guardar é o histórico do chat para exibi-lo.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Olá! Sou seu assistente de vendas da Ferrocorte. Como posso te ajudar hoje?")
    ]

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
    # Adiciona a mensagem do usuário à UI e ao histórico
    st.session_state.chat_history.append(HumanMessage(content=user_prompt))
    with st.chat_message("Human", avatar="👤"):
        st.write(user_prompt)

    # A interface agora é muito mais simples.
    # Ela apenas invoca o agente e espera a resposta.
    # Toda a lógica de "o que fazer agora" está dentro do agente.
    with st.chat_message("AI", avatar="🤖"):
        with st.spinner("Pensando..."):
            # O agente agora recebe o histórico de chat completo para ter contexto
            response = master_agent_executor.invoke({
                "input": user_prompt,
                "chat_history": st.session_state.chat_history
            })
            ai_response = response['output']
            st.write(ai_response)

    # Adiciona a resposta do agente ao histórico para a próxima rodada
    st.session_state.chat_history.append(AIMessage(content=ai_response))

    # Força a UI a rolar para a última mensagem
    st.rerun()