# graph.py

from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.agents import AgentAction, AgentFinish
from langgraph.graph import StateGraph, END

# Importa o agente e as ferramentas
from agent import agent
from tools import all_tools

# --- SOLUÇÃO DEFINITIVA: Criamos um mapa de ferramentas para chamá-las diretamente ---
tool_executor = {tool.name: tool for tool in all_tools}

# Define a ESTRUTURA CORRETA e completa do nosso estado
# O formato de intermediate_steps que o agente espera é uma lista de tuplas.
class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: AgentFinish | List[AgentAction]
    intermediate_steps: Annotated[list[tuple[AgentAction, ToolMessage]], "operator.__add__"]

# --- NÓS DO GRAFO ---

# Nó 1: Chama o agente para decidir a próxima ação
def call_model(state: AgentState):
    """Chama o LLM para obter a próxima ação ou resposta."""
    print("---CHAMANDO O AGENTE---")
    inputs = {
        "input": state["input"],
        "chat_history": state["chat_history"],
        "intermediate_steps": state.get("intermediate_steps", [])
    }
    response = agent.invoke(inputs)
    return {"agent_outcome": response}

# NÓ DE FERRAMENTA CORRIGIDO: Esta função substitui o ToolNode e resolve o erro.
def execute_tools(state: AgentState) -> dict:
    """
    Executa as ferramentas decididas pelo agente e retorna os resultados.
    Esta abordagem explícita é mais robusta do que usar o ToolNode pré-construído.
    """
    print("---EXECUTANDO FERRAMENTA---")
    agent_actions = state["agent_outcome"]
    
    # Garantimos que agent_actions seja sempre uma lista para o loop
    if not isinstance(agent_actions, list):
        actions = [agent_actions]
    else:
        actions = agent_actions

    outputs = []
    for action in actions:
        print(f"  [DEBUG] Chamando ferramenta '{action.tool}' com input: {action.tool_input}")
        # Encontra a função da ferramenta correspondente no nosso mapa
        tool_function = tool_executor[action.tool]
        # Invoca a ferramenta com o input correto
        observation = tool_function.invoke(action.tool_input)
        # Cria uma ToolMessage com o resultado e o ID da chamada original
        outputs.append(
            ToolMessage(content=str(observation), tool_call_id=action.tool_call_id)
        )
    
    # O agente espera uma lista de tuplas (Ação, Resultado da Ação)
    # Nós recriamos esse formato para a próxima chamada do agente.
    return {"intermediate_steps": list(zip(actions, outputs))}


# Nó 3: Decide para onde ir após a chamada do agente
def should_continue(state: AgentState) -> str:
    """Decide se a execução continua ou se finaliza."""
    print("---AVALIANDO RESPOSTA DO AGENTE---")
    if isinstance(state["agent_outcome"], AgentFinish):
        print("---AGENTE RESPONDEU, FIM DO TURNO---")
        return "end"
    else:
        print("---AGENTE DECIDIU USAR FERRAMENTA, CONTINUANDO---")
        return "continue"

# --- CONSTRUÇÃO DO GRAFO ---
workflow = StateGraph(AgentState)

# Adiciona os nós ao grafo, usando nossa nova função 'execute_tools'
workflow.add_node("agent", call_model)
workflow.add_node("action", execute_tools)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END,
    },
)

# Após a ação, o fluxo sempre volta para o agente para que ele possa interpretar o resultado.
workflow.add_edge("action", "agent")

app = workflow.compile()
print("Grafo compilado com sucesso!")