# testes da AVL: compara com um dict/sorted (força bruta) e confere as
# propriedades da árvore após cada operação
#
# uso: python -m unittest -v
import math
import random
import unittest

from src.avl import AVL

# altura máxima da AVL: ~1,44 log2(n + 2)
def LIMITE_ALTURA(n):
    return int(1.4405 * math.log2(n + 2) - 0.3277)

class TestAVL(unittest.TestCase):
    def test_insercao_aleatoria_mantem_propriedades(self):
        arvore, ref = AVL(), {}
        for chave in random.sample(range(100_000), 2_000):
            self.assertTrue(arvore.inserir(chave, str(chave)))
            ref[chave] = str(chave)
        arvore.validar()
        self.assertEqual(arvore.em_ordem(), sorted(ref.items()))

    def test_insercao_ordenada_nao_degenera(self):
        # pior caso da BST: chaves crescentes
        arvore = AVL()
        for chave in range(4_096):
            arvore.inserir(chave, chave)
        arvore.validar()
        self.assertLessEqual(arvore.altura(), LIMITE_ALTURA(4_096))

    def test_duplicada_nao_insere(self):
        arvore = AVL()
        self.assertTrue(arvore.inserir(10, "a"))
        self.assertFalse(arvore.inserir(10, "b"))
        self.assertEqual(len(arvore), 1)
        self.assertEqual(arvore.buscar(10), "a")

    def test_busca(self):
        arvore = AVL()
        for chave in range(0, 1_000, 2):
            arvore.inserir(chave, chave * 10)
        self.assertEqual(arvore.buscar(500), 5_000)
        self.assertIsNone(arvore.buscar(501))
        self.assertIsNone(AVL().buscar(1))

    def test_operacoes_misturadas(self):
        # 5.000 operações aleatórias de inserir/remover/remover_minimo
        arvore, ref = AVL(), {}
        for i in range(5_000):
            op, chave = random.random(), random.randint(0, 800)
            if op < 0.5:
                arvore.inserir(chave, chave)
                ref.setdefault(chave, chave)
            elif op < 0.85:
                self.assertEqual(arvore.remover(chave), ref.pop(chave, None))
            else:
                esperado = min(ref.items()) if ref else None
                self.assertEqual(arvore.remover_minimo(), esperado)
                if esperado:
                    del ref[esperado[0]]
            self.assertEqual(len(arvore), len(ref))
            if i % 250 == 0:
                arvore.validar()
        arvore.validar()
        self.assertEqual(arvore.em_ordem(), sorted(ref.items()))

    def test_intervalo_e_minimo(self):
        arvore = AVL()
        chaves = random.sample(range(10_000), 1_000)
        for c in chaves:
            arvore.inserir(c, c)
        self.assertEqual(arvore.minimo(), (min(chaves), min(chaves)))
        for _ in range(200):
            a, b = sorted(random.sample(range(-10, 10_010), 2))
            esperado = [(c, c) for c in sorted(chaves) if a <= c <= b]
            self.assertEqual(arvore.intervalo(a, b), esperado)

    def test_arvore_vazia(self):
        arvore = AVL()
        self.assertIsNone(arvore.minimo())
        self.assertIsNone(arvore.remover_minimo())
        self.assertIsNone(arvore.remover(5))
        self.assertEqual(arvore.intervalo(0, 10), [])
        self.assertEqual(arvore.altura(), 0)
        arvore.validar()

if __name__ == "__main__":
    unittest.main()
