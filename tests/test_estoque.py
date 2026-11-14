# testes do sistema de estoque FEFO (AVL + rubro-negras trabalhando juntas)
#
# uso: python -m unittest -v
import unittest
from datetime import date, timedelta

from src.estoque import Estoque
from src.models import Lote, Produto

HOJE = date(2026, 11, 13)

def dia(n: int) -> date:
    return HOJE + timedelta(days=n)

class TestEstoque(unittest.TestCase):
    def setUp(self):
        self.e = Estoque()
        self.e.cadastrar_produto(Produto(1001, "Dipirona 500mg", "Medicamentos", 9.9))
        self.e.cadastrar_produto(Produto(1002, "Álcool 70%", "Higiene", 7.5))
        self.e.receber_lote(Lote(1, 1001, dia(90), 10))
        self.e.receber_lote(Lote(2, 1001, dia(10), 5))
        self.e.receber_lote(Lote(3, 1001, dia(-3), 8))   # vencido
        self.e.receber_lote(Lote(4, 1002, dia(20), 30))

    def test_cadastro_e_busca(self):
        self.assertEqual(self.e.buscar_produto(1001).nome, "Dipirona 500mg")
        self.assertIsNone(self.e.buscar_produto(9999))
        self.assertFalse(self.e.cadastrar_produto(Produto(1001, "x", "y", 1.0)))
        self.assertEqual([p.codigo for p in self.e.listar_produtos()], [1001, 1002])

    def test_quantidade_total(self):
        self.assertEqual(self.e.buscar_produto(1001).quantidade, 23)

    def test_venda_fefo_pula_vencido_e_consome_em_ordem(self):
        retirado = self.e.vender(1001, 7, HOJE)
        # lote 3 está vencido: sai primeiro o lote 2 (vence em 10 dias), depois o 1
        self.assertEqual([(l.lote_id, q) for l, q in retirado], [(2, 5), (1, 2)])
        produto = self.e.buscar_produto(1001)
        self.assertEqual(produto.quantidade, 16)  # 8 vencidas + 8 do lote 1
        self.assertNotIn((dia(10), 2), self.e.vencimentos)  # lote 2 esvaziou

    def test_venda_sem_estoque_valido_nao_altera_nada(self):
        with self.assertRaises(ValueError):
            self.e.vender(1001, 16, HOJE)  # só há 15 válidas
        self.assertEqual(self.e.buscar_produto(1001).quantidade, 23)

    def test_vencendo_ate(self):
        ids = [l.lote_id for l in self.e.vencendo_ate(HOJE, 30)]
        self.assertEqual(ids, [2, 4])  # em ordem de validade, de todos os produtos

    def test_descartar_vencidos(self):
        self.assertEqual([l.lote_id for l in self.e.vencidos(HOJE)], [3])
        self.assertEqual([l.lote_id for l in self.e.descartar_vencidos(HOJE)], [3])
        self.assertEqual(self.e.vencidos(HOJE), [])
        self.assertEqual(self.e.buscar_produto(1001).quantidade, 15)

    def test_recall(self):
        self.assertEqual(self.e.recall(1001, 1).lote_id, 1)
        self.assertEqual(self.e.buscar_produto(1001).quantidade, 13)
        with self.assertRaises(KeyError):
            self.e.recall(1001, 1)

    def test_lote_de_produto_inexistente(self):
        with self.assertRaises(KeyError):
            self.e.receber_lote(Lote(9, 5555, dia(5), 1))

    def test_remover_produto_tira_os_lotes(self):
        self.e.remover_produto(1001)
        self.assertIsNone(self.e.buscar_produto(1001))
        self.assertEqual([l.lote_id for _, l in self.e.vencimentos.em_ordem()], [4])

    def test_arvores_continuam_validas(self):
        self.e.vender(1001, 7, HOJE)
        self.e.descartar_vencidos(HOJE)
        self.e.produtos.validar()
        self.e.vencimentos.validar()
        self.e.buscar_produto(1001).lotes.validar()

if __name__ == "__main__":
    unittest.main()
