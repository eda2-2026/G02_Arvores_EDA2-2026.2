# árvore binária de busca SEM balanceamento (linha de base)
#
# BST clássica com a interface comum das árvores do projeto. não é
# usada pelo sistema de estoque: serve só no benchmark para mostrar
# o problema que a AVL e a rubro-negra resolvem.
# quando as chaves chegam em ordem (códigos sequenciais, lotes com
# validades crescentes), ela degenera em lista e tudo vira O(n).
#
# todas as operações são iterativas de propósito: a versão recursiva
# estoura o limite de recursão do python justamente na árvore degenerada.

class NoBST:
    __slots__ = ("chave", "valor", "esquerda", "direita")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.esquerda: "NoBST | None" = None
        self.direita: "NoBST | None" = None

class BST:
    def __init__(self):
        self.raiz: NoBST | None = None
        self.tamanho = 0
        self.comparacoes = 0
        self.rotacoes = 0  # sempre 0: a BST nunca rebalanceia

    def __len__(self) -> int:
        return self.tamanho

    def resetar_contadores(self) -> None:
        self.comparacoes = 0

    def inserir(self, chave, valor) -> bool:
        # O(log n) médio; O(n) quando as chaves chegam em ordem
        novo = NoBST(chave, valor)
        if self.raiz is None:
            self.raiz = novo
            self.tamanho += 1
            return True
        atual = self.raiz
        while True:
            self.comparacoes += 1
            if chave == atual.chave:
                return False
            if chave < atual.chave:
                if atual.esquerda is None:
                    atual.esquerda = novo
                    break
                atual = atual.esquerda
            else:
                if atual.direita is None:
                    atual.direita = novo
                    break
                atual = atual.direita
        self.tamanho += 1
        return True

    def buscar(self, chave):
        atual = self.raiz
        while atual is not None:
            self.comparacoes += 1
            if chave == atual.chave:
                return atual.valor
            atual = atual.esquerda if chave < atual.chave else atual.direita
        return None

    def remover_minimo(self):
        # retira o menor: desce à esquerda e "pula" o nó
        if self.raiz is None:
            return None
        pai, atual = None, self.raiz
        while atual.esquerda is not None:
            pai, atual = atual, atual.esquerda
        if pai is None:
            self.raiz = atual.direita
        else:
            pai.esquerda = atual.direita
        self.tamanho -= 1
        return atual.chave, atual.valor

    def altura(self) -> int:
        if self.raiz is None:
            return 0
        h, nivel = 0, [self.raiz]
        while nivel:
            h += 1
            nivel = [f for no in nivel for f in (no.esquerda, no.direita)
                     if f is not None]
        return h
