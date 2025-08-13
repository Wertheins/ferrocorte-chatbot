# tools.py

from langchain_core.tools import tool
from config import worksheet, session_state
from thefuzz import fuzz
import re

# Colunas (sem alteração)
COLUNA_CODIGO = "codigo"
COLUNA_DESCRICAO = "descricao"
COLUNA_FAMILIA = "descricao_familia"
COLUNA_VALOR = "valor_unitario"

def format_price(value):
    # (sem alteração)
    if isinstance(value, str):
        value = value.replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@tool
def buscar_produtos(termo_de_busca: str) -> str:
    """
    Busca produtos no catálogo. Essencial para encontrar produtos e seus códigos.
    Use para buscas gerais e para refinar uma busca. A busca é refinada até que esta ferramenta retorne um único produto.
    """
    print(f"--- TOOL: Buscando produtos por '{termo_de_busca}'... ---")
    
    try:
        produtos = worksheet.get_all_records()
        print(f"  [DEBUG] {len(produtos)} registros lidos da planilha.")
        
        termo_de_busca_normalizado = termo_de_busca.lower().strip()
        query_words = set(re.sub(r'[^\w\s]', '', termo_de_busca_normalizado).split())
        
        resultados_com_pontuacao = []
        for produto in produtos:
            descricao_principal = str(produto.get(COLUNA_DESCRICAO, '')).lower().strip()
            familia = str(produto.get(COLUNA_FAMILIA, '')).lower().strip()
            texto_produto_completo = f"{descricao_principal} {familia}"
            
            product_words = set(re.sub(r'[^\w\s]', '', texto_produto_completo).split())
            
            todas_palavras_correspondem = True
            for query_word in query_words:
                match_found = False
                for product_word in product_words:
                    if query_word.startswith(product_word) or product_word.startswith(query_word):
                        match_found = True
                        break
                if not match_found:
                    todas_palavras_correspondem = False
                    break
            
            if not todas_palavras_correspondem:
                continue
                
            score = fuzz.token_set_ratio(termo_de_busca_normalizado, descricao_principal)
            resultados_com_pontuacao.append({'produto': produto, 'score': score})

        if not resultados_com_pontuacao:
            return "Nenhum produto encontrado com esses termos."

        # --- LÓGICA DE RETORNO CORRIGIDA ---
        # Se a busca filtrou para APENAS UM resultado, é uma correspondência exata.
        if len(resultados_com_pontuacao) == 1:
            produto_isolado = resultados_com_pontuacao[0]['produto']
            codigo = produto_isolado.get(COLUNA_CODIGO, "N/A")
            descricao = produto_isolado.get(COLUNA_DESCRICAO, "N/A")
            string_de_retorno = f"codigo:{codigo}, descricao:{descricao}"
            print(f"  [DEBUG] Busca resultou em 1 item. Retornando para o agente:\n{string_de_retorno}")
            return string_de_retorno

        # Se houver múltiplos resultados, ordena por relevância e retorna uma lista para o agente escolher.
        resultados_ordenados = sorted(resultados_com_pontuacao, key=lambda x: x['score'], reverse=True)
        melhores_resultados = [r['produto'] for r in resultados_ordenados][:7] # Aumentado o limite para 7
        resultados_formatados = []
        for item in melhores_resultados:
            codigo = item.get(COLUNA_CODIGO, "N/A")
            descricao = item.get(COLUNA_DESCRICAO, "N/A")
            resultados_formatados.append(f"codigo:{codigo}, descricao:{descricao}")
        
        string_de_retorno = "\n".join(resultados_formatados)
        print(f"  [DEBUG] Busca resultou em múltiplos itens. Retornando lista para o agente:\n{string_de_retorno}")
        return string_de_retorno
    except Exception as e:
        print(f"Erro em buscar_produtos: {e}")
        return f"Erro interno na ferramenta de busca: {e}"

@tool
def criar_orcamento(codigo_do_produto: str, quantidade: int) -> str:
    """
    Adiciona um produto com um 'codigo_do_produto' específico e uma 'quantidade' ao orçamento.
    Use esta ferramenta SOMENTE após ter um código de produto único da ferramenta 'buscar_produtos'.
    """
    print(f"--- TOOL: Adicionando produto CÓDIGO '{codigo_do_produto}' (Qtd: {quantidade}) ao orçamento... ---")
    
    try:
        # Busca o produto pelo código na planilha (muito mais confiável)
        produtos = worksheet.get_all_records()
        produto_para_adicionar = None
        for produto in produtos:
            # Garante que a comparação seja feita com strings para evitar erros de tipo
            if str(produto.get(COLUNA_CODIGO)).strip() == str(codigo_do_produto).strip():
                produto_para_adicionar = produto
                break
        
        if not produto_para_adicionar:
            return f"Erro: O produto com o código '{codigo_do_produto}' não foi encontrado no catálogo."
            
        print(f"  [DEBUG] Produto encontrado pelo código: {produto_para_adicionar.get(COLUNA_DESCRICAO)}")
        descricao_produto = produto_para_adicionar.get(COLUNA_DESCRICAO, 'Produto selecionado')
        orcamento = session_state.get("orcamento_atual") or {"itens": [], "subtotal": 0.0}
        
        item_encontrado_no_orcamento = False
        for item_existente in orcamento["itens"]:
            if item_existente.get("codigo") == codigo_do_produto:
                item_existente["quantidade"] += int(quantidade)
                item_existente["subtotal_item"] = item_existente["preco_unitario"] * item_existente["quantidade"]
                item_encontrado_no_orcamento = True
                break
        
        if not item_encontrado_no_orcamento:
            preco_unitario = format_price(produto_para_adicionar.get(COLUNA_VALOR, 0.0))
            int_quantidade = int(quantidade)
            subtotal_item = preco_unitario * int_quantidade
            orcamento["itens"].append({
                "codigo": codigo_do_produto, 
                "produto": descricao_produto,
                "quantidade": int_quantidade, 
                "preco_unitario": preco_unitario, 
                "subtotal_item": subtotal_item
            })
        
        orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
        session_state["orcamento_atual"] = orcamento
        
        return f"Adicionado: {int(quantidade)} unidade(s) de '{descricao_produto}'. Seu subtotal agora é de R$ {orcamento['subtotal']:.2f}. Deseja adicionar mais algum item ou podemos finalizar o pedido?"

    except Exception as e:
        print(f"Erro em criar_orcamento: {e}")
        return f"Ocorreu um erro ao tentar adicionar o item: {e}."

@tool
def finalizar_atendimento_e_passar_para_humano() -> str:
    """
    Finaliza a cotação, informa o valor total para o cliente e passa para um vendedor humano.
    Use esta ferramenta quando o cliente indicar que não quer mais adicionar itens.
    """
    print("--- TOOL: FINALIZANDO ATENDIMENTO E CALCULANDO TOTAL ---")
    orcamento_atual = session_state.get("orcamento_atual")
    
    if not orcamento_atual or not orcamento_atual["itens"]:
        return "Claro, mas não temos um orçamento ativo para finalizar."
    
    # Pega o subtotal final do orçamento antes de limpá-lo
    subtotal_final = orcamento_atual.get("subtotal", 0.0)
    
    # Limpa o orçamento para a próxima sessão
    session_state["orcamento_atual"] = None
    
    # Retorna a mensagem final e correta para o agente
    return f"Perfeito! Sua cotação está pronta. O valor total é de R$ {subtotal_final:.2f}. Vou apenas verificar os detalhes finais e um de nossos consultores já te retorna. Só um momento."

all_tools = [buscar_produtos, criar_orcamento, finalizar_atendimento_e_passar_para_humano]