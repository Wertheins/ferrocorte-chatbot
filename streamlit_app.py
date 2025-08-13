# streamlit_app.py
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.agents import AgentFinish
from graph import app # Importa o grafo compilado

# --- Configuração da Página ---
st.set_page_config(page_title="🤖 Assistente Ferrocorte", page_icon="🤖")
st.title("🤖 Assistente de Vendas Ferrocorte")
st.caption("Um chatbot para cotação de produtos siderúrgicos.")

# --- Gerenciamento de Estado da Sessão ---
def reset_conversation():
    # Inicializa o histórico de mensagens
    st.session_state.messages = [AIMessage(content="Olá! Bem-vindo(a) à Ferrocorte Industrial. Como posso te ajudar hoje?")]
    # Inicializa o orçamento no estado da sessão do Streamlit
    st.session_state.orcamento_atual = {"itens": [], "subtotal": 0.0}
    st.session_state.session_ended = False

st.sidebar.button("Nova Cotação", on_click=reset_conversation, use_container_width=True)

if "messages" not in st.session_state:
    reset_conversation()

# --- Lógica da Interface do Chat ---
for message in st.session_state.messages:
    with st.chat_message("assistant" if isinstance(message, AIMessage) else "user", avatar="🤖" if isinstance(message, AIMessage) else "👤"):
        st.markdown(message.content)

if prompt := st.chat_input("Sua mensagem...", disabled=st.session_state.session_ended):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analisando seu pedido..."):
            
            # Define o estado inicial para o grafo, passando o orçamento do st.session_state
            initial_state = {
                "input": prompt,
                "chat_history": st.session_state.messages[:-1],
                "orcamento_atual": st.session_state.orcamento_atual # Passa o estado
            }

            # Executa o grafo
            final_state = app.invoke(initial_state)

            # Atualiza o orçamento no estado do Streamlit com o resultado do grafo
            st.session_state.orcamento_atual = final_state.get("orcamento_atual")
            
            agent_outcome = final_state.get("agent_outcome")
            if isinstance(agent_outcome, AgentFinish):
                final_response_text = agent_outcome.return_values["output"]
            else:
                final_response_text = "Desculpe, ocorreu um erro inesperado. Por favor, tente novamente."

            st.markdown(final_response_text)

    st.session_state.messages.append(AIMessage(content=final_response_text))

    if "um de nossos consultores já te retorna" in final_response_text:
        st.session_state.session_ended = True
        st.info("Sessão de cotação finalizada. Para iniciar uma nova, clique em 'Nova Cotação' na barra lateral.")
        st.rerun()