# árvore rubro-negra (red-black tree)
#
# árvore binária de busca em que cada nó é VERMELHO ou PRETO e valem:
#   1. a raiz é preta;
#   2. as folhas nulas (NIL) são pretas;
#   3. um nó vermelho nunca tem filho vermelho;
#   4. todo caminho de um nó até suas folhas NIL tem o mesmo número de
#      nós pretos (altura negra).
# daí sai altura <= 2 log2(n + 1): é mais "frouxa" que a AVL (busca um pouco
# mais funda), mas cada inserção faz no máximo 2 rotações e cada remoção no
# máximo 3 — o resto do conserto é só recolorir. por isso é a escolha
# clássica para estruturas que mudam o tempo todo (TreeMap do Java,
# std::map do C++, escalonador CFS do Linux).
#
# no projeto ela guarda os LOTES ordenados por (validade, número do lote):
# lotes entram a cada recebimento e saem a cada venda, descarte ou recall ->
# carga dominada por escrita. além disso, a ordem por validade permite:
#   - minimo()     -> o lote que vence primeiro (venda FEFO)
#   - intervalo()  -> "o que vence até a data X" em O(log n + k)
#
# implementação baseada em Cormen et al. (CLRS), cap. 13, com nó sentinela.
# interface comum (igual à da AVL, em src/avl.py).

VERMELHO = True
PRETO = False

class NoRN:
    __slots__ = ("chave", "valor", "cor", "esquerda", "direita", "pai")

    def __init__(self, chave, valor, cor, nil):
        self.chave = chave
        self.valor = valor
        self.cor = cor
        self.esquerda = nil
        self.direita = nil
        self.pai = nil

class RubroNegra:
    def __init__(self):
        # sentinela: representa todas as folhas NIL (sempre preta)
        self.NIL = NoRN(None, None, PRETO, None)
        self.NIL.esquerda = self.NIL.direita = self.NIL.pai = self.NIL
        self.raiz = self.NIL
        self.tamanho = 0
        self.comparacoes = 0   # nós visitados nas descidas
        self.rotacoes = 0      # rotações simples
        self.recoloracoes = 0  # trocas de cor durante os consertos

    def __len__(self) -> int:
        return self.tamanho

    def resetar_contadores(self) -> None:
        self.comparacoes = 0
        self.rotacoes = 0
        self.recoloracoes = 0

    # ---------------- rotações ----------------

    def _rotacao_esquerda(self, x: NoRN) -> None:
        self.rotacoes += 1
        y = x.direita
        x.direita = y.esquerda
        if y.esquerda is not self.NIL:
            y.esquerda.pai = x
        y.pai = x.pai
        if x.pai is self.NIL:
            self.raiz = y
        elif x is x.pai.esquerda:
            x.pai.esquerda = y
        else:
            x.pai.direita = y
        y.esquerda = x
        x.pai = y

    def _rotacao_direita(self, y: NoRN) -> None:
        self.rotacoes += 1
        x = y.esquerda
        y.esquerda = x.direita
        if x.direita is not self.NIL:
            x.direita.pai = y
        x.pai = y.pai
        if y.pai is self.NIL:
            self.raiz = x
        elif y is y.pai.direita:
            y.pai.direita = x
        else:
            y.pai.esquerda = x
        x.direita = y
        y.pai = x

    def _pintar(self, no: NoRN, cor: bool) -> None:
        if no.cor != cor:
            self.recoloracoes += 1
            no.cor = cor

    # ---------------- busca ----------------

    def _buscar_no(self, chave) -> NoRN:
        atual = self.raiz
        while atual is not self.NIL:
            self.comparacoes += 1
            if chave == atual.chave:
                return atual
            atual = atual.esquerda if chave < atual.chave else atual.direita
        return self.NIL

    def buscar(self, chave):
        # O(log n): desce no máximo 2 log2(n + 1) níveis
        no = self._buscar_no(chave)
        return None if no is self.NIL else no.valor

    def __contains__(self, chave) -> bool:
        return self._buscar_no(chave) is not self.NIL

    # ---------------- inserção ----------------

    def inserir(self, chave, valor) -> bool:
        # O(log n): desce como numa BST, insere o nó VERMELHO e conserta.
        # retorna False se a chave já existe (chave única)
        pai, atual = self.NIL, self.raiz
        while atual is not self.NIL:
            self.comparacoes += 1
            pai = atual
            if chave == atual.chave:
                return False
            atual = atual.esquerda if chave < atual.chave else atual.direita

        novo = NoRN(chave, valor, VERMELHO, self.NIL)
        novo.pai = pai
        if pai is self.NIL:
            self.raiz = novo
        elif chave < pai.chave:
            pai.esquerda = novo
        else:
            pai.direita = novo
        self.tamanho += 1
        self._consertar_insercao(novo)
        return True

    def _consertar_insercao(self, z: NoRN) -> None:
        # só a propriedade 3 (vermelho com filho vermelho) pode ter quebrado
        while z.pai.cor == VERMELHO:
            avo = z.pai.pai
            if z.pai is avo.esquerda:
                tio = avo.direita
                if tio.cor == VERMELHO:
                    # caso 1: tio vermelho -> recolore e sobe o problema
                    self._pintar(z.pai, PRETO)
                    self._pintar(tio, PRETO)
                    self._pintar(avo, VERMELHO)
                    z = avo
                else:
                    if z is z.pai.direita:
                        # caso 2: "joelho" -> rotação vira o caso 3
                        z = z.pai
                        self._rotacao_esquerda(z)
                    # caso 3: "linha" -> recolore e gira o avô
                    self._pintar(z.pai, PRETO)
                    self._pintar(z.pai.pai, VERMELHO)
                    self._rotacao_direita(z.pai.pai)
            else:  # espelho: pai é filho direito do avô
                tio = avo.esquerda
                if tio.cor == VERMELHO:
                    self._pintar(z.pai, PRETO)
                    self._pintar(tio, PRETO)
                    self._pintar(avo, VERMELHO)
                    z = avo
                else:
                    if z is z.pai.esquerda:
                        z = z.pai
                        self._rotacao_direita(z)
                    self._pintar(z.pai, PRETO)
                    self._pintar(z.pai.pai, VERMELHO)
                    self._rotacao_esquerda(z.pai.pai)
        self._pintar(self.raiz, PRETO)

    # ---------------- remoção ----------------

    def _transplantar(self, u: NoRN, v: NoRN) -> None:
        # coloca a subárvore v no lugar de u
        if u.pai is self.NIL:
            self.raiz = v
        elif u is u.pai.esquerda:
            u.pai.esquerda = v
        else:
            u.pai.direita = v
        v.pai = u.pai

    def _minimo_no(self, no: NoRN) -> NoRN:
        while no.esquerda is not self.NIL:
            no = no.esquerda
        return no

    def remover(self, chave):
        # O(log n). retorna o valor removido ou None se não existia
        z = self._buscar_no(chave)
        if z is self.NIL:
            return None
        valor = z.valor
        self._remover_no(z)
        return valor

    def _remover_no(self, z: NoRN) -> None:
        y = z
        cor_original = y.cor
        if z.esquerda is self.NIL:
            x = z.direita
            self._transplantar(z, z.direita)
        elif z.direita is self.NIL:
            x = z.esquerda
            self._transplantar(z, z.esquerda)
        else:
            # dois filhos: o sucessor y ocupa o lugar de z
            y = self._minimo_no(z.direita)
            cor_original = y.cor
            x = y.direita
            if y.pai is z:
                x.pai = y
            else:
                self._transplantar(y, y.direita)
                y.direita = z.direita
                y.direita.pai = y
            self._transplantar(z, y)
            y.esquerda = z.esquerda
            y.esquerda.pai = y
            y.cor = z.cor
        self.tamanho -= 1
        # remover um nó PRETO quebra a altura negra -> conserta
        if cor_original == PRETO:
            self._consertar_remocao(x)

    def _consertar_remocao(self, x: NoRN) -> None:
        # x carrega um "preto extra"; os casos empurram esse preto para cima
        # ou o eliminam com no máximo 3 rotações no total
        while x is not self.raiz and x.cor == PRETO:
            if x is x.pai.esquerda:
                w = x.pai.direita  # irmão
                if w.cor == VERMELHO:
                    # caso 1: irmão vermelho -> vira um dos casos 2-4
                    self._pintar(w, PRETO)
                    self._pintar(x.pai, VERMELHO)
                    self._rotacao_esquerda(x.pai)
                    w = x.pai.direita
                if w.esquerda.cor == PRETO and w.direita.cor == PRETO:
                    # caso 2: irmão preto com filhos pretos -> recolore e sobe
                    self._pintar(w, VERMELHO)
                    x = x.pai
                else:
                    if w.direita.cor == PRETO:
                        # caso 3: sobrinho distante preto -> vira o caso 4
                        self._pintar(w.esquerda, PRETO)
                        self._pintar(w, VERMELHO)
                        self._rotacao_direita(w)
                        w = x.pai.direita
                    # caso 4: sobrinho distante vermelho -> resolve e termina
                    self._pintar(w, x.pai.cor)
                    self._pintar(x.pai, PRETO)
                    self._pintar(w.direita, PRETO)
                    self._rotacao_esquerda(x.pai)
                    x = self.raiz
            else:  # espelho
                w = x.pai.esquerda
                if w.cor == VERMELHO:
                    self._pintar(w, PRETO)
                    self._pintar(x.pai, VERMELHO)
                    self._rotacao_direita(x.pai)
                    w = x.pai.esquerda
                if w.direita.cor == PRETO and w.esquerda.cor == PRETO:
                    self._pintar(w, VERMELHO)
                    x = x.pai
                else:
                    if w.esquerda.cor == PRETO:
                        self._pintar(w.direita, PRETO)
                        self._pintar(w, VERMELHO)
                        self._rotacao_esquerda(w)
                        w = x.pai.esquerda
                    self._pintar(w, x.pai.cor)
                    self._pintar(x.pai, PRETO)
                    self._pintar(w.esquerda, PRETO)
                    self._rotacao_direita(x.pai)
                    x = self.raiz
        self._pintar(x, PRETO)

    # ---------------- consultas ordenadas ----------------

    def minimo(self):
        # menor chave = lote que vence primeiro. O(log n)
        if self.raiz is self.NIL:
            return None
        no = self._minimo_no(self.raiz)
        return no.chave, no.valor

    def remover_minimo(self):
        # retira o lote que vence primeiro (base da venda FEFO). O(log n)
        if self.raiz is self.NIL:
            return None
        no = self._minimo_no(self.raiz)
        par = (no.chave, no.valor)
        self._remover_no(no)
        return par

    def intervalo(self, inicio, fim) -> list:
        # todos os pares com inicio <= chave <= fim, em ordem. O(log n + k)
        saida, pilha, atual = [], [], self.raiz
        while pilha or atual is not self.NIL:
            while atual is not self.NIL:
                pilha.append(atual)
                atual = atual.esquerda if inicio < atual.chave else self.NIL
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
        while pilha or atual is not self.NIL:
            while atual is not self.NIL:
                pilha.append(atual)
                atual = atual.esquerda
            atual = pilha.pop()
            saida.append((atual.chave, atual.valor))
            atual = atual.direita
        return saida

    def altura(self) -> int:
        # altura em nós (iterativa, por níveis)
        if self.raiz is self.NIL:
            return 0
        h, nivel = 0, [self.raiz]
        while nivel:
            h += 1
            nivel = [f for no in nivel for f in (no.esquerda, no.direita)
                     if f is not self.NIL]
        return h

    # ---------------- verificação ----------------

    def validar(self) -> None:
        # confere as 4 propriedades; lança AssertionError se alguma falhar
        assert self.raiz.cor == PRETO, "raiz vermelha"
        assert self.NIL.cor == PRETO, "sentinela vermelha"

        def verificar(no, minimo, maximo) -> int:
            # retorna a altura negra da subárvore
            if no is self.NIL:
                return 1
            assert minimo is None or no.chave > minimo, "ordem de busca violada"
            assert maximo is None or no.chave < maximo, "ordem de busca violada"
            if no.cor == VERMELHO:
                assert no.esquerda.cor == PRETO and no.direita.cor == PRETO, \
                    f"nó vermelho {no.chave} com filho vermelho"
            if no.esquerda is not self.NIL:
                assert no.esquerda.pai is no, "ponteiro de pai inconsistente"
            if no.direita is not self.NIL:
                assert no.direita.pai is no, "ponteiro de pai inconsistente"
            he = verificar(no.esquerda, minimo, no.chave)
            hd = verificar(no.direita, no.chave, maximo)
            assert he == hd, f"altura negra diferente no nó {no.chave}"
            return he + (1 if no.cor == PRETO else 0)

        verificar(self.raiz, None, None)
        assert len(self.em_ordem()) == self.tamanho, "tamanho inconsistente"
