# modelos do domínio (produto e lote) e geradores de dados para testes
import random
from dataclasses import dataclass, field
from datetime import date, timedelta

@dataclass
class Lote:
    lote_id: int          # número do lote impresso na embalagem
    codigo_produto: int   # código do produto a que o lote pertence
    validade: date
    quantidade: int

    @property
    def chave(self) -> tuple[date, int]:
        # chave usada nas árvores rubro-negras: primeiro a validade,
        # depois o número do lote (desempata lotes que vencem no mesmo dia)
        return (self.validade, self.lote_id)

    def __str__(self) -> str:
        return (f"L{self.lote_id:06d} | produto {self.codigo_produto} | "
                f"vence {self.validade.strftime('%d/%m/%Y')} | {self.quantidade} un.")

@dataclass
class Produto:
    codigo: int           # chave única (código de barras / sku)
    nome: str
    categoria: str
    preco: float
    # árvore rubro-negra com os lotes deste produto, ordenados por validade.
    # é preenchida pelo Estoque (src/estoque.py) ao cadastrar o produto.
    lotes: object = field(default=None, repr=False, compare=False)
    quantidade: int = 0   # soma das quantidades dos lotes em estoque

    def __str__(self) -> str:
        return (f"{self.codigo} | {self.nome} ({self.categoria}) | "
                f"R$ {self.preco:.2f} | {self.quantidade} un.")

# catálogo base de uma drogaria: (nome, categoria)
CATALOGO = [
    ("Dipirona 500mg", "Medicamentos"), ("Paracetamol 750mg", "Medicamentos"),
    ("Ibuprofeno 400mg", "Medicamentos"), ("Amoxicilina 500mg", "Medicamentos"),
    ("Losartana 50mg", "Medicamentos"), ("Omeprazol 20mg", "Medicamentos"),
    ("Loratadina 10mg", "Medicamentos"), ("Soro Fisiológico 500ml", "Medicamentos"),
    ("Vitamina C 1g", "Suplementos"), ("Protetor Solar FPS50", "Perfumaria"),
    ("Shampoo Anticaspa", "Higiene"), ("Creme Dental", "Higiene"),
    ("Fralda Infantil M", "Infantil"), ("Álcool 70%", "Higiene"),
    ("Leite em Pó 400g", "Infantil"), ("Sabonete Líquido", "Higiene"),
]

def gerar_produtos(n: int, sequencial: bool = False) -> list[Produto]:
    # gera N produtos. sequencial=True simula códigos emitidos em ordem
    # crescente (cadastro em massa vindo do fornecedor) -> pior caso da BST
    if sequencial:
        codigos = list(range(100_000, 100_000 + n))
    else:
        codigos = random.sample(range(100_000, 1_000_000 + n * 10), n)
    produtos = []
    for i, cod in enumerate(codigos):
        nome, categoria = random.choice(CATALOGO)
        produtos.append(Produto(codigo=cod, nome=f"{nome} #{i + 1}",
                                categoria=categoria,
                                preco=round(random.uniform(2.0, 150.0), 2)))
    return produtos

def gerar_lotes(produtos: list[Produto], n: int, hoje: date,
                em_ordem: bool = False, primeiro_id: int = 1) -> list[Lote]:
    # gera N lotes para produtos sorteados, vencendo entre hoje e ~2 anos.
    # em_ordem=True simula o caso real mais comum: cada remessa nova chega
    # com validade mais distante que a anterior (chaves quase crescentes)
    if em_ordem:
        dias = sorted(random.randint(0, 730) for _ in range(n))
    else:
        dias = [random.randint(0, 730) for _ in range(n)]
    return [
        Lote(
            lote_id=primeiro_id + i,
            codigo_produto=random.choice(produtos).codigo,
            validade=hoje + timedelta(days=d),
            quantidade=random.randint(10, 200),
        )
        for i, d in enumerate(dias)
    ]
