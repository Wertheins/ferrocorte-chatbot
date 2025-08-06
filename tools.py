from langchain_core.tools import tool
from config import worksheet, session_state

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
    """Busca produtos no catálogo. Retorna uma lista de produtos encontrados."""
    print(f"--- TOOL: Buscando produtos por '{termo_de_busca}'... ---")
    try:
        produtos = worksheet.get_all_records()
        stop_words = ['de', 'da', 'do', 'para', 'com', 'o', 'a', 'e', 'quero', 'gostaria', 'preciso', 'duas', 'peças']
        termo_de_busca_normalizado = termo_de_busca.lower().replace(',', '.')
        keywords = [word for word in termo_de_busca_normalizado.split() if word not in stop_words]
        
        print(f"  [DEBUG] Keywords extraídas para busca: {keywords}")

        if not keywords: 
            session_state["ultimos_produtos_encontrados"] = []
            return []
        
        resultados_com_pontuacao = []
        for produto in produtos:
            texto_produto = (f"{produto.get('Código', '')} {produto.get('Família / Tipo', '')} {produto.get('Material', '')} "
                             f"{produto.get('Dimensões (Largura x Comprimento)', '')} {produto.get('Espessura', '')} "
                             f"{produto.get('Observações / Atributos', '')} {produto.get('Descrição Original', '')}").lower().replace(',', '.')
            score = sum(1 for keyword in keywords if keyword in texto_produto)
            if score > 0:
                resultados_com_pontuacao.append({'produto': produto, 'score': score})
        
        if not resultados_com_pontuacao:
            print("  [DEBUG] Nenhum produto encontrado com a busca.")
            session_state["ultimos_produtos_encontrados"] = []
            return []
        
        resultados_ordenados = sorted(resultados_com_pontuacao, key=lambda x: x['score'], reverse=True)
        maior_pontuacao = resultados_ordenados[0]['score']
        melhores_resultados = [r['produto'] for r in resultados_ordenados if r['score'] == maior_pontuacao]
        
        print(f"  [DEBUG] Melhores resultados encontrados (códigos): {[item.get('Código') for item in melhores_resultados]}")
        
        session_state["ultimos_produtos_encontrados"] = melhores_resultados
        
        print(f"  [DEBUG] Retornando para o agente: {melhores_resultados}")
        return melhores_resultados
    except Exception as e:
        print(f"Erro em buscar_produtos: {e}")
        session_state["ultimos_produtos_encontrados"] = []
        return []

@tool
def criar_orcamento(codigo_do_produto: str, quantidade: int) -> dict:
    """
    Adiciona um produto específico e sua quantidade ao orçamento usando seu código.
    Use esta função DEPOIS que o cliente confirmar o produto e a quantidade.
    """
    print(f"--- TOOL: Adicionando {quantidade} item(ns) do código '{codigo_do_produto}' ao orçamento... ---")
    try:
        # A ferramenta agora busca o produto por código, garantindo a seleção correta.
        todos_produtos = worksheet.get_all_records()
        produto_para_adicionar = None
        for p in todos_produtos:
            if str(p.get("Código")) == str(codigo_do_produto):
                produto_para_adicionar = p
                break
        
        if not produto_para_adicionar:
            return {"erro": f"Produto com código '{codigo_do_produto}' não encontrado no catálogo."}

        print(f"  [DEBUG] Produto selecionado para adicionar: {produto_para_adicionar.get('Descrição Original')}")

        orcamento = session_state.get("orcamento_atual") or {"itens": [], "subtotal": 0.0}
        print(f"  [DEBUG] Orçamento ANTES da adição: {orcamento}")

        codigo_pedido = str(produto_para_adicionar.get("Código"))
        item_encontrado_no_orcamento = False
        for item_existente in orcamento["itens"]:
            if item_existente.get("codigo") == codigo_pedido:
                item_existente["quantidade"] += quantidade
                item_existente["subtotal_item"] = item_existente["preco_unitario"] * item_existente["quantidade"]
                item_encontrado_no_orcamento = True
                break
        
        if not item_encontrado_no_orcamento:
            preco_unitario = format_price(produto_para_adicionar.get("PreçoMatriz", 0.0))
            subtotal_item = preco_unitario * quantidade
            orcamento["itens"].append({
                "codigo": codigo_pedido, 
                "produto": produto_para_adicionar.get('Descrição Original'),
                "quantidade": quantidade, 
                "preco_unitario": preco_unitario, 
                "subtotal_item": subtotal_item
            })
        
        orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
        session_state["orcamento_atual"] = orcamento
        print(f"  [DEBUG] Orçamento DEPOIS da adição (salvo na sessão): {orcamento}")
        return orcamento
    except Exception as e:
        print(f"Erro em criar_orcamento: {e}")
        return {"erro": str(e)}

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
        # Garantir a comparação correta entre os tipos de dados do código
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