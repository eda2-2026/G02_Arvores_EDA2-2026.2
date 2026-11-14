# benchmark: BST x AVL x Rubro-Negra nas duas cargas do sistema de estoque
#
# uso:
#   python comparacao.py                -> testa com 1.000, 10.000 e 100.000
#   python comparacao.py 500 5000      -> testa com os tamanhos passados
#
# a pergunta do experimento: cada árvore está no lugar certo do sistema?
#
# CENÁRIO 1 — cadastro de produtos (carga de LEITURA, onde usamos a AVL)
#   monta a árvore com N códigos e faz 10.000 buscas de códigos existentes.
#   mede: tempo médio por busca, comparações por busca e altura.
#   repete com códigos SEQUENCIAIS (cadastro em massa vindo do fornecedor):
#   a BST degenera, AVL e rubro-negra não.
#
# CENÁRIO 2 — fluxo de lotes (carga de ESCRITA, onde usamos a rubro-negra)
#   começa com N lotes e executa N operações alternando:
#     - recebimento: insere um lote novo, que vence DEPOIS dos atuais
#       (o caso real: remessas novas têm validade mais longa);
#     - venda FEFO:  remove o lote que vence primeiro (mínimo).
#   mede: tempo médio por operação, rotações por operação e o máximo de
#   rotações numa única operação.
#
# a BST degenerada custa O(n²), então os cenários em que ela degenera (cadastro
# sequencial e fluxo de lotes) só rodam a BST para bases de até 10.000 registros.
import json
import os
import random
import sys
import time

from src.avl import AVL
from src.bst import BST
from src.rubro_negra import RubroNegra

LIMITE_BST_EM_ORDEM = 10_000
NUM_BUSCAS = 10_000
REPETICOES = 5  # o tempo reportado é o menor de 5 repetições (reduz ruído)
ARVORES = {"bst": BST, "avl": AVL, "rn": RubroNegra}

def montar(classe, chaves):
    arvore = classe()
    for c in chaves:
        arvore.inserir(c, c)
    return arvore

def medir_buscas(arvore, chaves) -> tuple[float, float]:
    # retorna (µs por busca, comparações por busca)
    melhor = float("inf")
    for _ in range(REPETICOES):
        arvore.resetar_contadores()
        inicio = time.perf_counter()
        for c in chaves:
            arvore.buscar(c)
        melhor = min(melhor, time.perf_counter() - inicio)
    return melhor / len(chaves) * 1e6, arvore.comparacoes / len(chaves)

def cenario_cadastro(n: int, sequencial: bool) -> dict:
    if sequencial:
        chaves = list(range(100_000, 100_000 + n))
    else:
        chaves = random.sample(range(100_000, 1_000_000 + n * 10), n)
    buscas = random.choices(chaves, k=NUM_BUSCAS)

    resultado = {}
    for nome, classe in ARVORES.items():
        if nome == "bst" and sequencial and n > LIMITE_BST_EM_ORDEM:
            resultado[nome] = None
            continue
        arvore = montar(classe, chaves)
        rotacoes = arvore.rotacoes  # lido antes: medir_buscas zera os contadores
        us, comp = medir_buscas(arvore, buscas)
        resultado[nome] = {
            "busca_us": us,
            "comparacoes": comp,
            "altura": arvore.altura(),
            "rotacoes_montagem": rotacoes,
        }
    return resultado

def gerar_fluxo(n: int):
    # lotes iniciais com validades aleatórias (dias a partir de hoje) e uma
    # sequência de N operações: 'r' recebe lote mais novo, 'v' vende o mínimo
    iniciais = [(random.randint(0, 730), i) for i in range(n)]
    ops, dia_novo = [], 730
    for i in range(n):
        if i % 2 == 0:
            dia_novo += random.randint(0, 2)
            ops.append(("r", (dia_novo, n + i)))
        else:
            ops.append(("v", None))
    return iniciais, ops

def executar_fluxo(arvore, ops, contar: bool) -> int:
    # executa as operações; se contar=True devolve o máximo de rotações
    # observado numa única operação
    maximo = 0
    for tipo, chave in ops:
        antes = arvore.rotacoes
        if tipo == "r":
            arvore.inserir(chave, chave)
        else:
            arvore.remover_minimo()
        if contar:
            maximo = max(maximo, arvore.rotacoes - antes)
    return maximo

def cenario_fluxo(n: int, em_ordem: bool) -> dict:
    iniciais, ops = gerar_fluxo(n)
    if em_ordem:
        iniciais.sort()  # lotes iniciais cadastrados por ordem de validade
    resultado = {}
    for nome, classe in ARVORES.items():
        # no fluxo a BST degenera mesmo com estoque inicial aleatório: os
        # lotes novos vencem depois de todos e formam uma "lista" à direita
        if nome == "bst" and n > LIMITE_BST_EM_ORDEM:
            resultado[nome] = None
            continue
        # passada 1: tempo (sem instrumentação extra)
        arvore = montar(classe, iniciais)
        arvore.rotacoes = 0
        inicio = time.perf_counter()
        executar_fluxo(arvore, ops, contar=False)
        total = time.perf_counter() - inicio
        # passada 2: mesmas operações, contando rotações por operação
        arvore = montar(classe, iniciais)
        arvore.rotacoes = 0
        recolor_antes = getattr(arvore, "recoloracoes", 0)
        maximo = executar_fluxo(arvore, ops, contar=True)
        resultado[nome] = {
            "op_us": total / len(ops) * 1e6,
            "rotacoes_por_op": arvore.rotacoes / len(ops),
            "max_rotacoes_op": maximo,
            "recoloracoes_por_op": (getattr(arvore, "recoloracoes", 0) - recolor_antes)
                                   / len(ops) if nome == "rn" else None,
            "altura_final": arvore.altura(),
        }
    return resultado

def fmt(valor, casas=2) -> str:
    return "—" if valor is None else f"{valor:.{casas}f}"

def imprimir(resultados: list[dict]) -> None:
    for chave, titulo in [("cadastro_aleatorio", "códigos aleatórios"),
                          ("cadastro_sequencial", "códigos sequenciais")]:
        print(f"\nCENÁRIO 1 — busca no cadastro ({titulo}), {NUM_BUSCAS} buscas")
        print(f"{'N':>8} | {'árvore':<11} | {'µs/busca':>9} | {'comparações':>11} | "
              f"{'altura':>6} | {'rotações (montagem)':>19}")
        print("-" * 80)
        for r in resultados:
            for nome, rotulo in [("bst", "BST"), ("avl", "AVL"), ("rn", "Rubro-Negra")]:
                d = r[chave][nome]
                if d is None:
                    print(f"{r['n']:>8} | {rotulo:<11} | {'(degenera em lista: O(n²), inviável)':>53}")
                else:
                    print(f"{r['n']:>8} | {rotulo:<11} | {d['busca_us']:>9.2f} | "
                          f"{d['comparacoes']:>11.1f} | {d['altura']:>6} | "
                          f"{d['rotacoes_montagem']:>19}")
    for chave, titulo in [("fluxo_aleatorio", "estoque inicial aleatório"),
                          ("fluxo_em_ordem", "estoque inicial em ordem de validade")]:
        print(f"\nCENÁRIO 2 — fluxo de lotes ({titulo}), N operações recebe/vende")
        print(f"{'N':>8} | {'árvore':<11} | {'µs/op':>7} | {'rotações/op':>11} | "
              f"{'máx. rot./op':>12} | {'recolorações/op':>15} | {'altura':>6}")
        print("-" * 88)
        for r in resultados:
            for nome, rotulo in [("bst", "BST"), ("avl", "AVL"), ("rn", "Rubro-Negra")]:
                d = r[chave][nome]
                if d is None:
                    print(f"{r['n']:>8} | {rotulo:<11} | {'(degenera em lista: O(n²), inviável)':>58}")
                else:
                    print(f"{r['n']:>8} | {rotulo:<11} | {d['op_us']:>7.2f} | "
                          f"{d['rotacoes_por_op']:>11.3f} | {d['max_rotacoes_op']:>12} | "
                          f"{fmt(d['recoloracoes_por_op'], 3):>15} | {d['altura_final']:>6}")

def main():
    tamanhos = [int(a) for a in sys.argv[1:]] or [1_000, 10_000, 100_000]
    random.seed(2026)

    resultados = []
    for n in tamanhos:
        print(f"Testando base de {n} registros...")
        resultados.append({
            "n": n,
            "cadastro_aleatorio": cenario_cadastro(n, sequencial=False),
            "cadastro_sequencial": cenario_cadastro(n, sequencial=True),
            "fluxo_aleatorio": cenario_fluxo(n, em_ordem=False),
            "fluxo_em_ordem": cenario_fluxo(n, em_ordem=True),
        })

    imprimir(resultados)

    # salva os resultados em json para plot_results.py
    os.makedirs("assets", exist_ok=True)
    with open("assets/ultimos_resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4)
    print("\nResultados salvos em assets/ultimos_resultados.json")

if __name__ == "__main__":
    main()
