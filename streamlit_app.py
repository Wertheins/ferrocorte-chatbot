# streamlit_app.py

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# Importe não apenas o executor, mas também a ferramenta que vamos chamar diretamente
from agent import master_agent_executor
from tools import buscar_produtos
from config import session_state

# --- Configuração da Página ---
st.set_page_config(page_title="Chatbot Ferrocorte Industrial", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Olá! Sou seu assistente virtual. Me diga qual produto você precisa e montarei seu orçamento.")

# --- Inicialização do Estado da Sessão ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "awaiting_refinement" not in st.session_state:
    st.session_state.awaiting_refinement = False

# --- Exibe o histórico do chat ---
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI", avatar="🤖"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="👤"):
            st.write(message.content)

# --- Lógica de Interação ---
# A CORREÇÃO ESTÁ AQUI: Adicionamos o argumento 'key'
user_prompt = st.chat_input("Descreva o produto que você precisa...", key="user_chat_input")

if user_prompt:
    # Adiciona a mensagem do usuário à UI e ao histórico
    st.session_state.chat_history.append(HumanMessage(content=user_prompt))
    with st.chat_message("Human", avatar="👤"):
        st.write(user_prompt)

    # --- O ORQUESTRADOR LÓGICO ---
    if st.session_state.awaiting_refinement:
        with st.chat_message("AI", avatar="🤖"):
            with st.spinner("Confirmando sua seleção..."):
                buscar_produtos(termo_de_busca=user_prompt)
                
                produto_encontrado = session_state.get("ultimos_produtos_encontrados", [{}])[0]
                nome_produto = produto_encontrado.get("descricao", "O produto selecionado")

                ai_response = f"Ok, produto selecionado: **{nome_produto}**. Quantas unidades você precisa?"
                st.write(ai_response)

        st.session_state.chat_history.append(AIMessage(content=ai_response))
        st.session_state.awaiting_refinement = False

    # --- FLUXO NORMAL DO AGENTE ---
    else:
        with st.chat_message("AI", avatar="🤖"):
            with st.spinner("Analisando seu pedido..."):
                response = master_agent_executor.invoke({
                    "input": user_prompt,
                    "chat_history": st.session_state.chat_history
                })
                ai_response = response['output']
                st.write(ai_response)

        st.session_state.chat_history.append(AIMessage(content=ai_response))

        ultimos_produtos = session_state.get("ultimos_produtos_encontrados", [])
        if len(ultimos_produtos) > 1:
            st.session_state.awaiting_refinement = True
        else:
            st.session_state.awaiting_refinement = False