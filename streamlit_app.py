<<<<<<< HEAD
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# É importante importar a configuração e o executor do agente
# As variáveis de ambiente serão carregadas aqui pela primeira vez
from config import llm  # Garante que o llm e os segredos sejam carregados
from agent import master_agent_executor

# --- Configuração da Página ---
st.set_page_config(page_title="Chatbot Ferrocorte Industrial", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Olá! Sou seu assistente virtual. Me diga qual produto você precisa e montarei seu orçamento.")

# --- Gerenciamento do Histórico do Chat ---
# O st.session_state funciona como uma memória para a sessão do usuário no app
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Exibe as mensagens do histórico na interface
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI", avatar="🤖"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="👤"):
            st.write(message.content)

# --- Lógica de Interação ---
user_prompt = st.chat_input("Descreva o produto que você precisa...")

if user_prompt:
    # Adiciona a mensagem do usuário ao histórico e à interface
    st.session_state.chat_history.append(HumanMessage(content=user_prompt))
    with st.chat_message("Human", avatar="👤"):
        st.write(user_prompt)

    # Gera e exibe a resposta do assistente
    with st.chat_message("AI", avatar="🤖"):
        with st.spinner("Analisando seu pedido..."):
            # Invoca o agente com o input e o histórico
            response = master_agent_executor.invoke({
                "input": user_prompt,
                "chat_history": st.session_state.chat_history
            })
            ai_response = response['output']
            st.write(ai_response)

    # Adiciona a resposta da IA ao histórico
=======
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# É importante importar a configuração e o executor do agente
# As variáveis de ambiente serão carregadas aqui pela primeira vez
from config import llm  # Garante que o llm e os segredos sejam carregados
from agent import master_agent_executor

# --- Configuração da Página ---
st.set_page_config(page_title="Chatbot Ferrocorte Industrial", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Olá! Sou seu assistente virtual. Me diga qual produto você precisa e montarei seu orçamento.")

# --- Gerenciamento do Histórico do Chat ---
# O st.session_state funciona como uma memória para a sessão do usuário no app
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Exibe as mensagens do histórico na interface
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI", avatar="🤖"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human", avatar="👤"):
            st.write(message.content)

# --- Lógica de Interação ---
user_prompt = st.chat_input("Descreva o produto que você precisa...")

if user_prompt:
    # Adiciona a mensagem do usuário ao histórico e à interface
    st.session_state.chat_history.append(HumanMessage(content=user_prompt))
    with st.chat_message("Human", avatar="👤"):
        st.write(user_prompt)

    # Gera e exibe a resposta do assistente
    with st.chat_message("AI", avatar="🤖"):
        with st.spinner("Analisando seu pedido..."):
            # Invoca o agente com o input e o histórico
            response = master_agent_executor.invoke({
                "input": user_prompt,
                "chat_history": st.session_state.chat_history
            })
            ai_response = response['output']
            st.write(ai_response)

    # Adiciona a resposta da IA ao histórico
>>>>>>> f160444e56a25990e580ea6273fecb4a4a433cb2
    st.session_state.chat_history.append(AIMessage(content=ai_response))