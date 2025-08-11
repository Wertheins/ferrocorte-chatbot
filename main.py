from langchain_core.messages import AIMessage, HumanMessage
# Importa o executor do agente, como antes
from agent import master_agent_executor
# Novas importações necessárias para a memória
from langchain.memory import ConversationBufferWindowMemory
from config import llm

# --- INICIALIZAÇÃO DA MEMÓRIA INTELIGENTE ---
# Em vez de uma lista vazia, agora temos um objeto de memória inteligente.
# Ele usará o mesmo LLM para criar os resumos.
memory = ConversationBufferWindowMemory(
    k=10, # Mantém as últimas 5 trocas (pergunta/resposta). Ajuste conforme necessário.
    memory_key="chat_history",
    return_messages=True
)

# --- O LOOP DE CONVERSA (AGORA USANDO A MEMÓRIA INTELIGENTE) ---
print("Olá! Bem-vindo(a) à Ferrocorte Industrial. Para começar, como posso te ajudar hoje?")
while True:
    user_input = input("Você: ")
    if user_input.lower() in ["sair", "exit"]:
        print("Até logo!")
        break
    
    # 1. Carrega as variáveis da memória (o resumo + mensagens recentes)
    # O `{}` indica que não há inputs novos para a memória neste momento
    memory_variables = memory.load_memory_variables({})

    # 2. Prepara os inputs para o agente, combinando o input atual com o histórico da memória
    inputs = {
        "input": user_input,
        "chat_history": memory_variables['chat_history']
    }
    
    # 3. Invoca o agente com os inputs corretos
    response = master_agent_executor.invoke(inputs)

    # 4. Salva o contexto da interação atual (pergunta e resposta) na memória
    # para que possa ser usado no próximo turno.
    memory.save_context(inputs, {"output": response["output"]})

    print(f"Assistente: {response['output']}")