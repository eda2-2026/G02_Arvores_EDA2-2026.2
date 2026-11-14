# lê o json salvo pelo comparacao.py e gera os gráficos em assets/
#
# uso: python comparacao.py && python plot_results.py
import json
import math
import os
import sys

import matplotlib.pyplot as plt

ARQUIVO_DADOS = "assets/ultimos_resultados.json"

# cores fixas por estrutura (a mesma árvore tem sempre a mesma cor)
COR = {"avl": "#2a78d6", "rn": "#eb6834", "bst": "#1baf7a"}
ROTULO = {"avl": "AVL", "rn": "Rubro-Negra", "bst": "BST (sem balanceamento)"}
MARCADOR = {"avl": "o", "rn": "s", "bst": "^"}
TEXTO, TEXTO_SEC, GRADE = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_SEC,
    "xtick.color": TEXTO_SEC, "ytick.color": TEXTO_SEC, "axes.titlecolor": TEXTO,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
})

def novo_grafico(titulo, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.set_title(titulo, fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax

def linha(ax, x, y, nome, estilo="-"):
    ax.plot(x, y, estilo, color=COR[nome], marker=MARCADOR[nome], markersize=7,
            linewidth=2, label=ROTULO[nome],
            markeredgecolor="#fcfcfb", markeredgewidth=1.5)

def eixo_n(ax, ns):
    ax.set_xscale("log")
    ax.set_xticks(ns, labels=[f"{n:,}".replace(",", ".") for n in ns])
    ax.minorticks_off()

def salvar(fig, ax, arquivo):
    ax.legend(frameon=False, labelcolor=TEXTO_SEC)
    fig.tight_layout()
    fig.savefig(f"assets/{arquivo}", dpi=200)
    plt.close(fig)
    print(f"-> Gráfico 'assets/{arquivo}' gerado!")

def serie(resultados, cenario, nome, campo):
    pares = [(r["n"], r[cenario][nome][campo]) for r in resultados
             if r[cenario][nome] is not None]
    return [p[0] for p in pares], [p[1] for p in pares]

def main():
    if not os.path.exists(ARQUIVO_DADOS):
        print(f"Erro: arquivo '{ARQUIVO_DADOS}' não encontrado.")
        print("Execute primeiro o benchmark: python comparacao.py")
        sys.exit(1)
    with open(ARQUIVO_DADOS, encoding="utf-8") as f:
        resultados = json.load(f)
    ns = [r["n"] for r in resultados]

    # 1. cenário de leitura: tempo de busca no cadastro (códigos aleatórios)
    fig, ax = novo_grafico("Cadastro de produtos: tempo por busca (códigos aleatórios)",
                           "Tamanho da base (N)", "Tempo médio por busca (µs)")
    for nome in ("bst", "rn", "avl"):
        linha(ax, *serie(resultados, "cadastro_aleatorio", nome, "busca_us"), nome)
    eixo_n(ax, ns)
    ax.set_ylim(bottom=0)
    salvar(fig, ax, "tempo_busca_cadastro.png")

    # 2. altura com códigos sequenciais x limites teóricos
    fig, ax = novo_grafico("Altura com códigos sequenciais (pior caso da BST)",
                           "Tamanho da base (N)", "Altura da árvore (níveis)")
    for nome in ("rn", "avl"):
        linha(ax, *serie(resultados, "cadastro_sequencial", nome, "altura"), nome)
    ax.plot(ns, [2 * math.log2(n + 1) for n in ns], ":", color=COR["rn"], linewidth=1.5,
            label="limite Rubro-Negra: 2·log₂(n+1)")
    ax.plot(ns, [1.44 * math.log2(n + 2) for n in ns], ":", color=COR["avl"], linewidth=1.5,
            label="limite AVL: 1,44·log₂(n+2)")
    ax.plot(ns, [math.log2(n) for n in ns], "--", color=TEXTO_SEC, linewidth=1,
            label="ótimo: log₂(n)")
    eixo_n(ax, ns)
    ax.set_ylim(bottom=0)
    salvar(fig, ax, "altura_cadastro_sequencial.png")

    # 3. cenário de escrita: tempo por operação no fluxo de lotes
    fig, ax = novo_grafico("Fluxo de lotes: tempo por operação (recebe / vende FEFO)",
                           "Tamanho do estoque (N)", "Tempo médio por operação (µs)")
    for nome in ("avl", "rn"):
        linha(ax, *serie(resultados, "fluxo_aleatorio", nome, "op_us"), nome)
    eixo_n(ax, ns)
    ax.set_ylim(bottom=0)
    salvar(fig, ax, "tempo_fluxo_lotes.png")

    # 4. máximo de rotações numa única operação do fluxo
    fig, ax = novo_grafico("Fluxo de lotes: máximo de rotações numa única operação",
                           "Tamanho do estoque (N)", "Rotações (pior operação)")
    largura = 0.36
    pos = range(len(ns))
    for desloc, nome in ((-largura / 2, "avl"), (largura / 2, "rn")):
        valores = [r["fluxo_aleatorio"][nome]["max_rotacoes_op"] for r in resultados]
        barras = ax.bar([p + desloc for p in pos], valores, largura * 0.94,
                        color=COR[nome], label=ROTULO[nome])
        ax.bar_label(barras, padding=3, color=TEXTO_SEC)
    ax.axhline(3, color=TEXTO_SEC, linestyle="--", linewidth=1,
               label="limite teórico da Rubro-Negra (3 rotações)")
    ax.set_xticks(list(pos), labels=[f"{n:,}".replace(",", ".") for n in ns])
    ax.grid(axis="x", visible=False)
    salvar(fig, ax, "max_rotacoes_fluxo.png")

    # 5. degradação da BST com códigos sequenciais
    fig, ax = novo_grafico("Degradação da BST com códigos sequenciais",
                           "Tamanho da base (N)", "Comparações por busca (escala log)")
    for nome in ("bst", "rn", "avl"):
        linha(ax, *serie(resultados, "cadastro_sequencial", nome, "comparacoes"), nome)
    eixo_n(ax, ns)
    ax.set_yscale("log")
    salvar(fig, ax, "degradacao_bst.png")

if __name__ == "__main__":
    main()
