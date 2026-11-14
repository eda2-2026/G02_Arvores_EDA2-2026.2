# sistema de estoque com controle de validade (FEFO)
#
# FEFO = "first expired, first out": na venda sai sempre o lote que vence
# primeiro. evita perda de produto vencido na prateleira e é exigido no
# controle de lotes de medicamentos.
#
# como as árvores se combinam:
#
#   produtos   : AVL         código -> Produto
#                (muita consulta, pouca alteração)
#   p.lotes    : RubroNegra  (validade, lote) -> Lote, uma por produto
#                (lotes do produto em ordem de validade -> venda FEFO)
#   vencimentos: RubroNegra  (validade, lote) -> Lote, de TODOS os produtos
#                (relatórios "vence até a data X" e descarte de vencidos)
#
# cada lote fica em duas rubro-negras (a do produto e a global); toda
# entrada ou saída de lote atualiza as duas.
from datetime import date, timedelta

from src.avl import AVL
from src.models import Lote, Produto
from src.rubro_negra import RubroNegra

_INF = float("inf")

def _faixa(inicio: date, fim: date) -> tuple[tuple, tuple]:
    # chaves que cobrem todos os lotes com inicio <= validade <= fim
    return (inicio, -1), (fim, _INF)

class Estoque:
    def __init__(self):
        self.produtos = AVL()
        self.vencimentos = RubroNegra()

    # ---------------- produtos (AVL) ----------------

    def cadastrar_produto(self, produto: Produto) -> bool:
        # O(log n). retorna False se o código já está cadastrado
        produto.lotes = RubroNegra()
        produto.quantidade = 0
        return self.produtos.inserir(produto.codigo, produto)

    def buscar_produto(self, codigo: int) -> Produto | None:
        # O(log n): consulta no caixa / leitor de código de barras
        return self.produtos.buscar(codigo)

    def atualizar_preco(self, codigo: int, preco: float) -> None:
        self._exigir_produto(codigo).preco = preco

    def remover_produto(self, codigo: int) -> Produto:
        # tira o produto de linha junto com todos os lotes dele
        produto = self._exigir_produto(codigo)
        for _, lote in produto.lotes.em_ordem():
            self.vencimentos.remover(lote.chave)
        self.produtos.remover(codigo)
        return produto

    def listar_produtos(self) -> list[Produto]:
        # percurso in-order da AVL: produtos ordenados por código. O(n)
        return [p for _, p in self.produtos.em_ordem()]

    def _exigir_produto(self, codigo: int) -> Produto:
        produto = self.produtos.buscar(codigo)
        if produto is None:
            raise KeyError(f"produto {codigo} não cadastrado")
        return produto

    # ---------------- lotes (rubro-negras) ----------------

    def receber_lote(self, lote: Lote) -> None:
        # entrada de mercadoria: O(log n) na AVL + O(log m) nas rubro-negras
        produto = self._exigir_produto(lote.codigo_produto)
        if not self.vencimentos.inserir(lote.chave, lote):
            raise ValueError(f"lote L{lote.lote_id:06d} já registrado")
        produto.lotes.inserir(lote.chave, lote)
        produto.quantidade += lote.quantidade

    def _retirar_lote(self, produto: Produto, lote: Lote) -> None:
        produto.lotes.remover(lote.chave)
        self.vencimentos.remover(lote.chave)
        produto.quantidade -= lote.quantidade

    def vender(self, codigo: int, quantidade: int, hoje: date) -> list[tuple[Lote, int]]:
        # venda FEFO: consome os lotes NÃO vencidos do que vence primeiro
        # para o que vence por último. retorna [(lote, unidades tiradas)].
        # lote vencido nunca é vendido: fica para descarte.
        produto = self._exigir_produto(codigo)
        validos = [l for _, l in produto.lotes.intervalo(*_faixa(hoje, date.max))]
        disponivel = sum(l.quantidade for l in validos)
        if quantidade > disponivel:
            raise ValueError(f"estoque válido insuficiente: {disponivel} un. "
                             f"de {produto.nome}")
        retirado, falta = [], quantidade
        for lote in validos:  # já em ordem de validade
            if falta == 0:
                break
            tirar = min(falta, lote.quantidade)
            retirado.append((lote, tirar))
            falta -= tirar
            if tirar == lote.quantidade:
                self._retirar_lote(produto, lote)  # lote esvaziou
            else:
                lote.quantidade -= tirar
                produto.quantidade -= tirar
        return retirado

    def vencendo_ate(self, hoje: date, dias: int) -> list[Lote]:
        # lotes que vencem entre hoje e hoje + dias. O(log m + k)
        return [l for _, l in self.vencimentos.intervalo(
            *_faixa(hoje, hoje + timedelta(days=dias)))]

    def vencidos(self, hoje: date) -> list[Lote]:
        # lotes com validade anterior a hoje. O(log m + k)
        return [l for _, l in self.vencimentos.intervalo(
            *_faixa(date.min, hoje - timedelta(days=1)))]

    def descartar_vencidos(self, hoje: date) -> list[Lote]:
        # retira todos os vencidos: o menor da árvore global é sempre o
        # próximo a vencer, então basta remover o mínimo enquanto ele estiver
        # vencido. O(k log m) para k lotes descartados.
        descartados = []
        while True:
            menor = self.vencimentos.minimo()
            if menor is None or menor[1].validade >= hoje:
                return descartados
            lote = menor[1]
            self._retirar_lote(self._exigir_produto(lote.codigo_produto), lote)
            descartados.append(lote)

    def recall(self, codigo: int, lote_id: int) -> Lote:
        # recolhimento de um lote específico (ex.: alerta sanitário).
        # o aviso informa produto + lote; os lotes de um produto são poucos,
        # então basta percorrer a rubro-negra dele.
        produto = self._exigir_produto(codigo)
        for _, lote in produto.lotes.em_ordem():
            if lote.lote_id == lote_id:
                self._retirar_lote(produto, lote)
                return lote
        raise KeyError(f"lote L{lote_id:06d} não encontrado em {produto.nome}")
