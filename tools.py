# tools.py
from langchain_core.tools import tool
from config import worksheet # Não importa mais o session_state
from thefuzz import fuzz
import re
from typing import TypedDict, List

# Define a estrutura do orçamento para clareza
class Orcamento(TypedDict):
    itens: List[dict]
    subtotal: float

# Colunas
COLUNA_CODIGO = "codigo"
COLUNA_DESCRICAO = "descricao"
COLUNA_FAMILIA = "descricao_familia"
COLUNA_VALOR = "valor_unitario"

def format_price(value):
    if isinstance(value, str):
        value = value.replace("R$", "").strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@tool
def buscar_produtos(termo_de_busca: str) -> str:
    # Esta ferramenta não precisa do estado, então permanece igual.
    # ... (código de buscar_produtos permanece o mesmo) ...
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

        if len(resultados_com_pontuacao) == 1:
            produto_isolado = resultados_com_pontuacao[0]['produto']
            codigo = produto_isolado.get(COLUNA_CODIGO, "N/A")
            descricao = produto_isolado.get(COLUNA_DESCRICAO, "N/A")
            string_de_retorno = f"codigo:{codigo}, descricao:{descricao}"
            print(f"  [DEBUG] Busca resultou em 1 item. Retornando para o agente:\n{string_de_retorno}")
            return string_de_retorno

        resultados_ordenados = sorted(resultados_com_pontuacao, key=lambda x: x['score'], reverse=True)
        melhores_resultados = [r['produto'] for r in resultados_ordenados][:7]
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
def criar_orcamento(codigo_do_produto: str, quantidade: int, orcamento_atual: Orcamento) -> dict:
    """
    Adiciona um produto ao orçamento. Recebe o 'orcamento_atual' e retorna o 'orcamento_novo' e uma 'mensagem_confirmacao'.
    """
    print(f"--- TOOL: Adicionando produto CÓDIGO '{codigo_do_produto}' (Qtd: {quantidade}) ao orçamento... ---")
    
    try:
        produtos = worksheet.get_all_records()
        produto_para_adicionar = next((p for p in produtos if str(p.get(COLUNA_CODIGO)).strip() == str(codigo_do_produto).strip()), None)
        
        if not produto_para_adicionar:
            return {
                "orcamento_novo": orcamento_atual,
                "mensagem_confirmacao": f"Erro: O produto com o código '{codigo_do_produto}' não foi encontrado."
            }
            
        descricao_produto = produto_para_adicionar.get(COLUNA_DESCRICAO, 'Produto selecionado')
        orcamento = orcamento_atual.copy() # Trabalha com uma cópia

        item_existente = next((item for item in orcamento["itens"] if item.get("codigo") == codigo_do_produto), None)
        if item_existente:
            item_existente["quantidade"] += int(quantidade)
            item_existente["subtotal_item"] = item_existente["preco_unitario"] * item_existente["quantidade"]
        else:
            preco_unitario = format_price(produto_para_adicionar.get(COLUNA_VALOR, 0.0))
            subtotal_item = preco_unitario * int(quantidade)
            orcamento["itens"].append({
                "codigo": codigo_do_produto, 
                "produto": descricao_produto,
                "quantidade": int(quantidade), 
                "preco_unitario": preco_unitario, 
                "subtotal_item": subtotal_item
            })
        
        orcamento["subtotal"] = sum(item['subtotal_item'] for item in orcamento['itens'])
        
        mensagem = f"Adicionado: {int(quantidade)} unidade(s) de '{descricao_produto}'. Seu subtotal agora é de R$ {orcamento['subtotal']:.2f}. Deseja adicionar mais algum item ou podemos finalizar o pedido?"
        
        return {"orcamento_novo": orcamento, "mensagem_confirmacao": mensagem}

    except Exception as e:
        print(f"Erro em criar_orcamento: {e}")
        return {"orcamento_novo": orcamento_atual, "mensagem_confirmacao": f"Ocorreu um erro: {e}."}


@tool
def finalizar_atendimento_e_passar_para_humano(orcamento_atual: Orcamento) -> dict:
    """
    Finaliza a cotação. Recebe o 'orcamento_atual' e retorna o 'orcamento_novo' (zerado) e a 'mensagem_final'.
    """
    print("--- TOOL: FINALIZANDO ATENDIMENTO E CALCULANDO TOTAL ---")
    
    if not orcamento_atual or not orcamento_atual["itens"]:
        return {
            "orcamento_novo": orcamento_atual,
            "mensagem_final": "Claro, mas não temos um orçamento ativo para finalizar."
        }
    
    subtotal_final = orcamento_atual.get("subtotal", 0.0)
    orcamento_zerado = {"itens": [], "subtotal": 0.0}
    
    mensagem = f"Perfeito! Sua cotação está pronta. O valor total é de R$ {subtotal_final:.2f}. Vou apenas verificar os detalhes finais e um de nossos consultores já te retorna. Só um momento."

    return {"orcamento_novo": orcamento_zerado, "mensagem_final": mensagem}

# A lista de ferramentas não muda, pois o LangGraph se encarrega de passar os parâmetros
all_tools = [buscar_produtos, criar_orcamento, finalizar_atendimento_e_passar_para_humano]