from langchain_core.messages import AIMessage, HumanMessage
from agent import master_agent_executor
import time

def run_test_scenario(scenario_name, steps):
    print("\n" + "="*60)
    print(f"INICIANDO CENÁRIO DE TESTE: {scenario_name}")
    print("="*60)
    chat_history = []
    for i, user_input in enumerate(steps):
        print(f"\n[PASSO {i+1}] Você: {user_input}")
        time.sleep(1)
        response = master_agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response['output']))
        print(f"Assistente: {response['output']}")
    print(f"\n--- CENÁRIO '{scenario_name}' FINALIZADO ---")

# --- 10 CENÁRIOS DE TESTE DE FOGO ---

cenario_1 = {
    "nome": "O Cliente Decidido (Múltiplos Itens de uma Vez)",
    "passos": [
        "preciso de 3 chapas xadrez de alumínio 2x1 de 1,5mm e 10 barras de alumínio 203,2 x 3000 mm",
        "isso mesmo, pode fechar"
    ]
}

cenario_2 = {
    "nome": "O Cliente Indeciso com Correção (Adiciona e Remove)",
    "passos": [
        "quero uma chapa xadrez de aço carbono 2x1",
        "a de 1/8 de polegada",
        "pode por 2 no orçamento",
        "adicione também 1 chapa expandida de aço 2x1",
        "a de 3/16 polegadas",
        "sim",
        "na verdade, a chapa expandida não vou querer mais. pode tirar do orçamento?",
        "agora sim, pode fechar"
    ]
}

cenario_3 = {
    "nome": "O Cliente com Erro de Digitação (Teste de Busca 'Fuzzy')",
    "passos": [
        "vcs tem chapa chadres de aluminio?",
        "a de 2000 por 1000 com espessura de 1,50",
        "uma só",
        "pode prosseguir"
    ]
}

cenario_4 = {
    "nome": "O Cliente Curioso (Crossover no Início)",
    "passos": [
        "qual o horário de vcs no sábado?",
        "entendi. então, queria ver o preço da chapa perfurada de aço 2x1 de 3mm",
        "a de furo 3/8",
        "2 peças",
        "ok, fechar pedido"
    ]
}

cenario_5 = {
    "nome": "O Cliente Confuso (Múltiplos Refinamentos)",
    "passos": [
        "chapa lisa galvanizada",
        "3000mm de comprimento",
        "a de 1.25mm de espessura",
        "isso, 1200 de largura, qual o preço?",
        "quero 10",
        "pode fechar"
    ]
}

cenario_6 = {
    "nome": "O Cliente Apressado (Crossover no Final)",
    "passos": [
        "preciso de 5 chapas de aço inox 304 2x1.25 de 4mm com urgência",
        "sim, pode adicionar",
        "antes de fechar, qual o endereço para retirada?",
        "beleza, pode prosseguir com a compra"
    ]
}

cenario_7 = {
    "nome": "O Cliente que Desiste e Volta",
    "passos": [
        "quanto custa a barra de alumínio?",
        "a de 203,2mm",
        "hmmm, ok, vou pensar. obrigado",
        "voltei. decidi levar aquela barra de alumínio. pode adicionar 1 no orçamento.",
        "fechar"
    ]
}

cenario_8 = {
    "nome": "O Cliente do Varejo (Múltiplos Itens Pequenos)",
    "passos": [
        "preciso de uma chapa fina de aço carbono 2x1 de 0,90mm",
        "sim, uma só",
        "e também uma peça de aço 50x50 de 12,5mm",
        "pode adicionar",
        "só isso, pode fechar"
    ]
}

cenario_9 = {
    "nome": "A Busca Impossível (Tratamento de 'Não Encontrado')",
    "passos": [
        "vocês têm viga de titânio?",
        "entendi, e chapa de cobre?",
        "ok, obrigado"
    ]
}

cenario_10 = {
    "nome": "O Cliente que Muda de Ideia na Quantidade (Teste de Atualização)",
    "passos": [
        "quero 2 chapas xadrez de alumínio 2x1 de 4mm",
        "sim",
        "pensando bem, mude a quantidade para 3 por favor",
        "ok, agora sim pode fechar"
    ]
}


# --- Execução Principal do Teste ---
if __name__ == "__main__":
    todos_os_testes = [
        cenario_1, cenario_2, cenario_3, cenario_4, cenario_5,
        cenario_6, cenario_7, cenario_8, cenario_9, cenario_10
    ]

    for teste in todos_os_testes:
        run_test_scenario(teste["nome"], teste["passos"])