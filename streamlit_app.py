# streamlit_app.py

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.agents import AgentFinish

# É crucial importar o 'app' do seu grafo.
# O Streamlit executará os arquivos importados, inicializando o LLM,
# a conexão com a planilha e compilando o grafo uma única vez.
from graph import app

# --- Configuração da Página e Estado da Sessão ---

st.set_page_config(page_title="🤖 Assistente Ferrocorte", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Um chatbot para cotação de produtos siderúrgicos.")

# Função para reiniciar a conversa
def reset_conversation():
    st.session_state.messages = [
        AIMessage(content="Olá! Bem-vindo(a) à Ferrocorte Industrial. Como posso te ajudar hoje?")
    ]
    st.session_state.session_ended = False

# Adiciona um botão na barra lateral para iniciar um novo chat
st.sidebar.button("Nova Cotação", on_click=reset_conversation, use_container_width=True)

# Inicializa o estado da sessão se ainda não existir
if "messages" not in st.session_state:
    reset_conversation()

# --- Lógica da Interface do Chat ---

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    if isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.markdown(message.content)

# Campo de input para o usuário, desabilitado se a sessão terminou
if prompt := st.chat_input("Sua mensagem...", disabled=st.session_state.session_ended):
    # Adiciona e exibe a mensagem do usuário
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Mostra um "spinner" enquanto o bot está processando
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analisando seu pedido..."):
            # Define o estado inicial para esta chamada do grafo
            # O histórico precisa ser o estado atual da sessão
            initial_state = {
                "input": prompt,
                "chat_history": st.session_state.messages[:-1], # Passa todo o histórico, exceto a última mensagem do usuário
            }

            # Executa o grafo
            final_state = app.invoke(initial_state)

            # Extrai a resposta final (mesma lógica do seu main.py)
            agent_outcome = final_state.get("agent_outcome")
            if isinstance(agent_outcome, AgentFinish):
                final_response_text = agent_outcome.return_values["output"]
            else:
                # Caso de segurança
                final_response_text = "Desculpe, ocorreu um erro inesperado. Por favor, tente novamente."

            # Exibe a resposta do bot
            st.markdown(final_response_text)

    # Adiciona a resposta do bot ao histórico
    st.session_state.messages.append(AIMessage(content=final_response_text))

    # Verifica se a conversa deve ser encerrada
    if "um de nossos consultores já te retorna" in final_response_text:
        st.session_state.session_ended = True
        st.info("Sessão de cotação finalizada. Para iniciar uma nova, clique em 'Nova Cotação' na barra lateral.")
        st.rerun() # Força o re-render para desabilitar o input