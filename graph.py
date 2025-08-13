# graph.py
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.agents import AgentAction, AgentFinish
from langgraph.graph import StateGraph, END
import json

# Importa o agente e as ferramentas
from agent import agent
from tools import all_tools, Orcamento

tool_executor = {tool.name: tool for tool in all_tools}

class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    agent_outcome: AgentFinish | List[AgentAction]
    intermediate_steps: Annotated[list[tuple[AgentAction, ToolMessage]], "operator.__add__"]
    orcamento_atual: Orcamento # <-- NOVO ESTADO AQUI

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

def execute_tools(state: AgentState) -> dict:
    """Executa as ferramentas e atualiza o estado do orçamento."""
    print("---EXECUTANDO FERRAMENTA---")
    agent_actions = state["agent_outcome"]
    orcamento = state["orcamento_atual"]
    
    actions = agent_actions if isinstance(agent_actions, list) else [agent_actions]
    outputs = []
    
    for action in actions:
        print(f"  [DEBUG] Chamando ferramenta '{action.tool}' com input: {action.tool_input}")
        tool_function = tool_executor[action.tool]
        
        # Passa o orçamento atual para as ferramentas que precisam dele
        tool_input = action.tool_input
        if action.tool in ["criar_orcamento", "finalizar_atendimento_e_passar_para_humano"]:
            tool_input["orcamento_atual"] = orcamento

        # Invoca a ferramenta
        observation = tool_function.invoke(tool_input)
        
        # As ferramentas agora retornam um dicionário.
        # Precisamos extrair a mensagem para o agente e atualizar nosso estado do orçamento.
        if isinstance(observation, dict):
            if 'orcamento_novo' in observation:
                orcamento = observation['orcamento_novo'] # Atualiza o orçamento
            
            # A mensagem para o agente é o que sobrou no dicionário
            message_for_agent = {k: v for k, v in observation.items() if k != 'orcamento_novo'}
            observation_str = json.dumps(message_for_agent)
        else:
            observation_str = str(observation)

        outputs.append(ToolMessage(content=observation_str, tool_call_id=action.tool_call_id))
    
    return {
        "intermediate_steps": list(zip(actions, outputs)),
        "orcamento_atual": orcamento # Retorna o orçamento atualizado para o estado do grafo
    }

def should_continue(state: AgentState) -> str:
    # ... (código de should_continue permanece o mesmo) ...
    print("---AVALIANDO RESPOSTA DO AGENTE---")
    if isinstance(state["agent_outcome"], AgentFinish):
        print("---AGENTE RESPONDEU, FIM DO TURNO---")
        return "end"
    else:
        print("---AGENTE DECIDIU USAR FERRAMENTA, CONTINUANDO---")
        return "continue"

# --- CONSTRUÇÃO DO GRAFO ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", execute_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "action", "end": END},
)
workflow.add_edge("action", "agent")

app = workflow.compile()
print("Grafo compilado com sucesso!")