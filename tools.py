# ferrocorte-chatbot/tools.py

from langchain_core.tools import tool
from config import worksheet, session_state
from thefuzz import fuzz # <-- IMPORTANTE: Nova importação

def format_price(value):
    """Função auxiliar para formatar preços para cálculo."""
    if isinstance(value, str):
        value = value.replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@tool
def buscar_produtos(termo_de_busca: str) -> list:
    """
    Busca produtos no catálogo de forma inteligente, lidando com abreviações e erros. 
    Retorna uma lista de produtos encontrados.
    """
    print(f"--- TOOL: Buscando produtos por '{termo_de_busca}'... ---")
    try:
        produtos = worksheet.get_all_records()
        termo_de_busca_normalizado = termo_de_busca.lower().strip()

        if not termo_de_busca_normalizado:
            session_state["ultimos_produtos_encontrados"] = []
            return []

        resultados_com_pontuacao = []
        for produto in produtos:
            # Combina os campos relevantes do produto para uma busca mais completa
            texto_produto = (f"{produto.get('descricao', '')} "
                             f"{produto.get('descricao_familia', '')}").lower().strip()

            if not texto_produto:
                continue
            
            # A MÁGICA ACONTECE AQUI:
            # Usamos 'partial_ratio' para encontrar a melhor correspondência parcial.
            # Isso é ótimo para abreviações ("galv" vs "galvanizada") e erros.
            score = fuzz.partial_ratio(termo_de_busca_normalizado, texto_produto)
            
            # Damos um bônus se a busca do usuário for o início exato de uma palavra no produto
            # Isso ajuda a priorizar resultados mais diretos para buscas curtas como "chapa".
            if texto_produto.startswith(termo_de_busca_normalizado):
                 score += 10

            if score > 75: # Define um "corte" de relevância. Só considera produtos com score acima de 75.
                resultados_com_pontuacao.append({'produto': produto, 'score': score})
        
        if not resultados_com_pontuacao:
            print("  [DEBUG] Nenhum produto encontrado com a busca inteligente.")
            session_state["ultimos_produtos_encontrados"] = []
            return []
        
        # Ordena os resultados pela pontuação, do maior para o menor
        resultados_ordenados = sorted(resultados_com_pontuacao, key=lambda x: x['score'], reverse=True)
        
        # Pega os 5 melhores resultados para não sobrecarregar o agente com muitas opções.
        melhores_resultados = [r['produto'] for r in resultados_ordenados][:5]
        
        print(f"  [DEBUG] Melhores resultados (códigos): {[item.get('codigo') for item in melhores_resultados]}")
        session_state["ultimos_produtos_encontrados"] = melhores_resultados
        
        print(f"  [DEBUG] Retornando para o agente: {melhores_resultados}")
        return melhores_resultados
    except Exception as e:
        print(f"Erro em buscar_produtos: {e}")
        session_state["ultimos_produtos_encontrados"] = []
        return []

@tool
def criar_orcamento(quantidade: int) -> str:
    """
    Adiciona o produto MAIS RECENTEMENTE encontrado ao orçamento e retorna uma mensagem de confirmação para o cliente.
    Use esta ferramenta IMEDIATAMENTE após o cliente confirmar a quantidade de um item que foi isolado pela busca.
    A ferramenta adiciona o item e prepara a próxima pergunta para o cliente.
    """
    print(f"--- TOOL: Adicionando {quantidade} item(ns) e preparando a resposta de confirmação... ---")
    
    ultimos_encontrados = session_state.get("ultimos_produtos_encontrados")
    if not ultimos_encontrados or len(ultimos_encontrados) != 1:
        return "Desculpe, parece que perdi o contexto do produto que estávamos falando. Poderíamos começar a busca por este item novamente?"
    
    produto_para_adicionar = ultimos_encontrados[0]
    descricao_produto = produto_para_adicionar.get('descricao', 'Produto selecionado')

    try:
        # Lógica de adição ao orçamento (a mesma de antes)
        orcamento = session_state.get("orcamento_atual") or {"itens": [], "subtotal": 0.0}
        codigo_pedido = str(produto_para_adicionar.get("codigo"))
        
        # ... (a lógica interna para adicionar ou atualizar a quantidade no orcamento["itens"] continua a mesma) ...
        # [COPIE E COLE A LÓGICA DE DENTRO DO SEU 'try' ANTERIOR AQUI]
        # Vou reescrevê-la para garantir:
        item_encontrado_no_orcamento = False
        for item_existente in orcamento["itens"]:
            if item_existente.get("codigo") == codigo_pedido:
                item_existente["quantidade"] += quantidade
                item_existente["subtotal_item"] = item_existente["preco_unitario"] * item_existente["quantidade"]
                item_encontrado_no_orcamento = True
                break
        
        if not item_encontrado_no_orcamento:
            preco_unitario = format_price(produto_para_adicionar.get("valor_unitario", 0.0))
            subtotal_item = preco_unitario * quantidade
            orcamento["itens"].append({
                "codigo": codigo_pedido, 
                "produto": descricao_produto,
                "quantidade": quantidade, 
                "preco_unitario": preco_unitario, 
                "subtotal_item": subtotal_item
            })
        
        orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
        session_state["orcamento_atual"] = orcamento
        
        # A MÁGICA ESTÁ AQUI: a ferramenta retorna a próxima fala do bot
        return f"Adicionado: {quantidade} unidade(s) de '{descricao_produto}'. Seu subtotal agora é de R$ {orcamento['subtotal']:.2f}. Deseja adicionar mais algum item ou podemos finalizar o pedido?"

    except Exception as e:
        print(f"Erro em criar_orcamento: {e}")
        return f"Ocorreu um erro ao tentar adicionar o item: {e}. Por favor, tente novamente."

@tool
def atualizar_quantidade_item(codigo_do_produto: str, nova_quantidade: int) -> dict:
    """
    Atualiza a quantidade de um item que JÁ ESTÁ no orçamento.
    Use se o cliente mudar de ideia sobre a quantidade de um item.
    """
    print(f"--- TOOL: Atualizando quantidade do item '{codigo_do_produto}' para '{nova_quantidade}'... ---")
    orcamento = session_state.get("orcamento_atual")
    if not orcamento or not orcamento["itens"]:
        return {"erro": "Não há nenhum orçamento ativo para atualizar."}
    
    item_encontrado = False
    for item in orcamento["itens"]:
        if str(item.get("codigo")) == str(codigo_do_produto):
            item["quantidade"] = nova_quantidade
            item["subtotal_item"] = item["preco_unitario"] * nova_quantidade
            item_encontrado = True
            break
            
    if not item_encontrado:
        return {"erro": f"O produto com código {codigo_do_produto} não foi encontrado no orçamento."}

    orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
    session_state["orcamento_atual"] = orcamento
    return orcamento

@tool
def remover_item_orcamento(codigo_do_produto: str) -> dict:
    """Remove um item do orçamento atual com base no seu código."""
    print(f"--- TOOL: Removendo item com código '{codigo_do_produto}' do orçamento... ---")
    orcamento = session_state.get("orcamento_atual")
    if not orcamento or not orcamento["itens"]:
        return {"erro": "Não há nenhum orçamento ativo para remover itens."}
    orcamento["itens"] = [item for item in orcamento["itens"] if item.get("codigo") != codigo_do_produto]
    orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
    session_state["orcamento_atual"] = orcamento
    return orcamento

@tool
def finalizar_atendimento_e_passar_para_humano() -> str:
    """Finaliza o atendimento e passa para um vendedor humano."""
    print("--- TOOL: SINALIZANDO HANDOFF PARA VENDEDOR HUMANO ---")
    orcamento_atual = session_state.get("orcamento_atual")
    if not orcamento_atual or not orcamento_atual["itens"]:
        return "Claro, mas não temos um orçamento ativo. Sobre quais produtos você gostaria de prosseguir?"
    session_state["orcamento_atual"] = None 
    session_state["ultimos_produtos_encontrados"] = []
    return "Perfeito! Sua cotação está pronta. Vou apenas verificar os detalhes finais e um de nossos consultores já te retorna. Só um momento."

@tool
def get_info_geral(pergunta_sobre: str) -> str:
    """Responde perguntas gerais sobre a empresa, como endereço ou horário de funcionamento."""
    print(f"--- TOOL: Respondendo à pergunta sobre '{pergunta_sobre}'... ---")
    pergunta_sobre = pergunta_sobre.lower()
    if "endereço" in pergunta_sobre or "localização" in pergunta_sobre:
        return "Nossa empresa fica na Av. Principal, 123, São Paulo, SP."
    elif "horário" in pergunta_sobre or "funcionamento" in pergunta_sobre:
        return "Nosso horário de funcionamento é de Segunda a Sexta, das 8h às 18h, e aos Sábados, das 8h às 12h."
    else:
        return "Não tenho essa informação, mas um de nossos atendentes pode ajudar."

all_tools = [buscar_produtos, criar_orcamento, atualizar_quantidade_item, remover_item_orcamento, get_info_geral, finalizar_atendimento_e_passar_para_humano]