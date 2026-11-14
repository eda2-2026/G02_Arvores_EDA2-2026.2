# árvore AVL (Adelson-Velsky e Landis, 1962)
#
# árvore binária de busca em que, para TODO nó, a diferença de altura entre
# as subárvores esquerda e direita (fator de balanceamento) é -1, 0 ou +1.
# isso garante altura <= ~1,44 log2(n): é a árvore balanceada MAIS BAIXA
# entre as vistas na disciplina, então as buscas fazem o menor número de
# comparações. o preço é manter esse balanceamento rígido: a cada inserção
# ou remoção as alturas do caminho são recalculadas e, na remoção, pode
# haver uma rotação em cada nível do caminho (O(log n) rotações).
#
# no projeto ela guarda o CADASTRO DE PRODUTOS (chave = código): consultado
# a cada venda, recebimento e consulta de preço, mas raramente alterado ->
# carga dominada por leitura, exatamente onde a AVL rende mais.
#
# interface comum (igual à da RubroNegra, em src/rubro_negra.py):
#   inserir, buscar, remover, minimo, intervalo, em_ordem, altura,
#   validar, len() e os contadores comparacoes / rotacoes.

class NoAVL:
    __slots__ = ("chave", "valor", "esquerda", "direita", "altura")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.esquerda: "NoAVL | None" = None
        self.direita: "NoAVL | None" = None
        self.altura = 1  # folha tem altura 1; árvore vazia tem altura 0

def _altura(no: NoAVL | None) -> int:
    return no.altura if no else 0

def _atualizar(no: NoAVL) -> None:
    no.altura = 1 + max(_altura(no.esquerda), _altura(no.direita))

def _fator(no: NoAVL) -> int:
    # fator de balanceamento = altura(esq) - altura(dir)
    return _altura(no.esquerda) - _altura(no.direita)

class AVL:
    def __init__(self):
        self.raiz: NoAVL | None = None
        self.tamanho = 0
        self.comparacoes = 0  # nós visitados nas descidas
        self.rotacoes = 0     # rotações simples (uma dupla conta 2)

    def __len__(self) -> int:
        return self.tamanho

    def resetar_contadores(self) -> None:
        self.comparacoes = 0
        self.rotacoes = 0

    # ---------------- rotações ----------------

    def _rotacao_direita(self, y: NoAVL) -> NoAVL:
        #       y            x
        #      / \          / \
        #     x   C  ->    A   y
        #    / \              / \
        #   A   B            B   C
        self.rotacoes += 1
        x = y.esquerda
        y.esquerda = x.direita
        x.direita = y
        _atualizar(y)
        _atualizar(x)
        return x

    def _rotacao_esquerda(self, x: NoAVL) -> NoAVL:
        # espelho da rotação à direita
        self.rotacoes += 1
        y = x.direita
        x.direita = y.esquerda
        y.esquerda = x
        _atualizar(x)
        _atualizar(y)
        return y

    def _balancear(self, no: NoAVL) -> NoAVL:
        # recalcula a altura e corrige o nó se |fator| chegou a 2
        _atualizar(no)
        fb = _fator(no)
        if fb > 1:  # pesado à esquerda
            if _fator(no.esquerda) < 0:           # caso esquerda-direita
                no.esquerda = self._rotacao_esquerda(no.esquerda)
            return self._rotacao_direita(no)      # caso esquerda-esquerda
        if fb < -1:  # pesado à direita
            if _fator(no.direita) > 0:            # caso direita-esquerda
                no.direita = self._rotacao_direita(no.direita)
            return self._rotacao_esquerda(no)     # caso direita-direita
        return no

    # ---------------- operações ----------------

    def buscar(self, chave):
        # O(log n): desce no máximo ~1,44 log2(n) níveis
        atual = self.raiz
        while atual is not None:
            self.comparacoes += 1
            if chave == atual.chave:
                return atual.valor
            atual = atual.esquerda if chave < atual.chave else atual.direita
        return None

    def __contains__(self, chave) -> bool:
        return self.buscar(chave) is not None

    def inserir(self, chave, valor) -> bool:
        # O(log n). retorna False se a chave já existe (chave única)
        antes = self.tamanho
        self.raiz = self._inserir(self.raiz, chave, valor)
        return self.tamanho > antes

    def _inserir(self, no: NoAVL | None, chave, valor) -> NoAVL:
        if no is None:
            self.tamanho += 1
            return NoAVL(chave, valor)
        self.comparacoes += 1
        if chave < no.chave:
            no.esquerda = self._inserir(no.esquerda, chave, valor)
        elif chave > no.chave:
            no.direita = self._inserir(no.direita, chave, valor)
        else:
            return no  # duplicada: não insere
        # na volta da recursão, rebalanceia cada nó do caminho
        return self._balancear(no)

    def remover(self, chave):
        # O(log n). retorna o valor removido ou None se não existia
        self._removido = None
        self.raiz = self._remover(self.raiz, chave)
        return self._removido

    def _remover(self, no: NoAVL | None, chave) -> NoAVL | None:
        if no is None:
            return None
        self.comparacoes += 1
        if chave < no.chave:
            no.esquerda = self._remover(no.esquerda, chave)
        elif chave > no.chave:
            no.direita = self._remover(no.direita, chave)
        else:
            self._removido = no.valor
            self.tamanho -= 1
            if no.esquerda is None:
                return no.direita
            if no.direita is None:
                return no.esquerda
            # dois filhos: copia o sucessor (menor da direita) e o remove
            sucessor = no.direita
            while sucessor.esquerda is not None:
                sucessor = sucessor.esquerda
            no.chave, no.valor = sucessor.chave, sucessor.valor
            no.direita = self._remover_minimo(no.direita)
        return self._balancear(no)

    def _remover_minimo(self, no: NoAVL) -> NoAVL | None:
        if no.esquerda is None:
            return no.direita
        no.esquerda = self._remover_minimo(no.esquerda)
        return self._balancear(no)

    def minimo(self):
        # menor chave: desce sempre à esquerda. O(log n)
        if self.raiz is None:
            return None
        atual = self.raiz
        while atual.esquerda is not None:
            atual = atual.esquerda
        return atual.chave, atual.valor

    def remover_minimo(self):
        # retira o menor elemento, rebalanceando o caminho. O(log n)
        par = self.minimo()
        if par is not None:
            self.raiz = self._remover_minimo(self.raiz)
            self.tamanho -= 1
        return par

    def intervalo(self, inicio, fim) -> list:
        # todos os pares com inicio <= chave <= fim, em ordem.
        # O(log n + k): só entra nas subárvores que podem ter chaves no intervalo
        saida = []
        pilha, atual = [], self.raiz
        while pilha or atual is not None:
            while atual is not None:
                pilha.append(atual)
                atual = atual.esquerda if inicio < atual.chave else None
            no = pilha.pop()
            if no.chave > fim:
                break
            if no.chave >= inicio:
                saida.append((no.chave, no.valor))
            atual = no.direita
        return saida

    def em_ordem(self) -> list:
        # percurso in-order (iterativo): lista ordenada por chave. O(n)
        saida, pilha, atual = [], [], self.raiz
        while pilha or atual is not None:
            while atual is not None:
                pilha.append(atual)
                atual = atual.esquerda
            atual = pilha.pop()
            saida.append((atual.chave, atual.valor))
            atual = atual.direita
        return saida

    def altura(self) -> int:
        return _altura(self.raiz)

    # ---------------- verificação ----------------

    def validar(self) -> None:
        # confere as propriedades da AVL; lança AssertionError se alguma falhar
        def verificar(no, minimo, maximo) -> int:
            if no is None:
                return 0
            assert minimo is None or no.chave > minimo, "ordem de busca violada"
            assert maximo is None or no.chave < maximo, "ordem de busca violada"
            he = verificar(no.esquerda, minimo, no.chave)
            hd = verificar(no.direita, no.chave, maximo)
            assert abs(he - hd) <= 1, f"nó {no.chave} desbalanceado ({he} x {hd})"
            assert no.altura == 1 + max(he, hd), f"altura errada no nó {no.chave}"
            return no.altura
        verificar(self.raiz, None, None)
        assert len(self.em_ordem()) == self.tamanho, "tamanho inconsistente"
