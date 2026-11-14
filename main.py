# sistema de estoque com controle de validade (FEFO) — interface de terminal
#
# uso:
#   python main.py          -> menu interativo
#   python main.py --demo   -> demonstração roteirizada (usada no vídeo)
import random
import sys
from datetime import date, timedelta

from src.estoque import Estoque
from src.models import CATALOGO, Lote, Produto

HOJE = date.today()

def carregar_demonstracao(estoque: Estoque) -> None:
    # base pequena e legível: 16 produtos de drogaria, 2 a 4 lotes cada,
    # alguns já vencidos e outros vencendo nos próximos dias
    random.seed(42)
    proximo_lote = 1
    for i, (nome, categoria) in enumerate(CATALOGO):
        codigo = 789100 + i * 37
        estoque.cadastrar_produto(Produto(codigo, nome, categoria,
                                          round(random.uniform(4, 90), 2)))
        for _ in range(random.randint(2, 4)):
            estoque.receber_lote(Lote(proximo_lote, codigo,
                                      HOJE + timedelta(days=random.randint(-20, 400)),
                                      random.randint(5, 60)))
            proximo_lote += 1

def mostrar_estatisticas(estoque: Estoque) -> None:
    avl, rn = estoque.produtos, estoque.vencimentos
    print(f"  AVL (produtos)          : {len(avl)} nós | altura {avl.altura()} | "
          f"{avl.rotacoes} rotações até agora")
    print(f"  Rubro-Negra (validades) : {len(rn)} nós | altura {rn.altura()} | "
          f"{rn.rotacoes} rotações, {rn.recoloracoes} recolorações até agora")

def titulo(texto: str) -> None:
    print(f"\n=== {texto} ===")

def demo() -> None:
    estoque = Estoque()
    carregar_demonstracao(estoque)
    print(f"Data de hoje: {HOJE.strftime('%d/%m/%Y')}")

    titulo("1. Produtos cadastrados (percurso in-order da AVL)")
    for p in estoque.listar_produtos():
        print(" ", p)

    # produto com um lote já vencido: mostra que a venda FEFO o ignora
    alvo = estoque.buscar_produto(estoque.vencidos(HOJE)[0].codigo_produto)
    titulo(f"2. Lotes de '{alvo.nome}' em ordem de validade (Rubro-Negra do produto)")
    for _, lote in alvo.lotes.em_ordem():
        marca = "  <- VENCIDO" if lote.validade < HOJE else ""
        print(" ", lote, marca)

    titulo(f"3. Venda FEFO de 15 un. de '{alvo.nome}' (o lote vencido é pulado)")
    try:
        for lote, qtd in estoque.vender(alvo.codigo, 15, HOJE):
            print(f"  {qtd:>3} un. do lote L{lote.lote_id:06d} "
                  f"(vence {lote.validade.strftime('%d/%m/%Y')})")
    except ValueError as erro:
        print(" ", erro)

    titulo("4. Lotes vencendo nos próximos 30 dias (consulta por intervalo)")
    for lote in estoque.vencendo_ate(HOJE, 30):
        print(" ", lote)

    titulo("5. Descarte dos lotes vencidos (remoção repetida do mínimo)")
    for lote in estoque.descartar_vencidos(HOJE):
        print("  descartado:", lote)

    _, primeiro = estoque.vencimentos.minimo()
    titulo(f"6. Recall do lote L{primeiro.lote_id:06d}")
    print("  recolhido:", estoque.recall(primeiro.codigo_produto, primeiro.lote_id))

    titulo("7. Estado das árvores")
    mostrar_estatisticas(estoque)
    estoque.produtos.validar()
    estoque.vencimentos.validar()
    print("  propriedades da AVL e da Rubro-Negra conferidas: OK")

def ler_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("  digite um número inteiro.")

def ler_data(msg: str) -> date:
    while True:
        texto = input(msg + " (dd/mm/aaaa): ").strip()
        try:
            d, m, a = (int(x) for x in texto.split("/"))
            return date(a, m, d)
        except ValueError:
            print("  data inválida.")

MENU = """
------------------------------------------------
 Estoque FEFO — hoje é {hoje}
------------------------------------------------
 1. Cadastrar produto          6. Vencidos / descartar
 2. Buscar produto             7. Recall de lote
 3. Receber lote               8. Listar produtos
 4. Vender (FEFO)              9. Estatísticas das árvores
 5. Lotes vencendo em X dias   D. Carregar base de demonstração
 0. Sair
"""

def menu() -> None:
    estoque = Estoque()
    proximo_lote = 1000
    while True:
        print(MENU.format(hoje=HOJE.strftime("%d/%m/%Y")))
        opcao = input("Opção: ").strip().upper()
        try:
            if opcao == "0":
                return
            elif opcao == "1":
                codigo = ler_int("Código: ")
                nome = input("Nome: ").strip()
                categoria = input("Categoria: ").strip() or "Geral"
                preco = float(input("Preço: ").replace(",", "."))
                ok = estoque.cadastrar_produto(Produto(codigo, nome, categoria, preco))
                print("  cadastrado." if ok else "  código já cadastrado.")
            elif opcao == "2":
                p = estoque.buscar_produto(ler_int("Código: "))
                if p is None:
                    print("  produto não encontrado.")
                else:
                    print(" ", p)
                    for _, lote in p.lotes.em_ordem():
                        print("   -", lote)
            elif opcao == "3":
                codigo = ler_int("Código do produto: ")
                validade = ler_data("Validade")
                qtd = ler_int("Quantidade: ")
                estoque.receber_lote(Lote(proximo_lote, codigo, validade, qtd))
                print(f"  lote L{proximo_lote:06d} registrado.")
                proximo_lote += 1
            elif opcao == "4":
                codigo = ler_int("Código do produto: ")
                qtd = ler_int("Quantidade: ")
                for lote, tirado in estoque.vender(codigo, qtd, HOJE):
                    print(f"  {tirado} un. do lote L{lote.lote_id:06d} "
                          f"(vence {lote.validade.strftime('%d/%m/%Y')})")
            elif opcao == "5":
                lotes = estoque.vencendo_ate(HOJE, ler_int("Dias: "))
                print(f"  {len(lotes)} lote(s):")
                for lote in lotes:
                    print("   -", lote)
            elif opcao == "6":
                vencidos = estoque.vencidos(HOJE)
                print(f"  {len(vencidos)} lote(s) vencido(s):")
                for lote in vencidos:
                    print("   -", lote)
                if vencidos and input("Descartar todos? (s/n): ").lower() == "s":
                    print(f"  {len(estoque.descartar_vencidos(HOJE))} descartado(s).")
            elif opcao == "7":
                codigo = ler_int("Código do produto: ")
                print("  recolhido:", estoque.recall(codigo, ler_int("Número do lote: ")))
            elif opcao == "8":
                for p in estoque.listar_produtos():
                    print(" ", p)
            elif opcao == "9":
                mostrar_estatisticas(estoque)
            elif opcao == "D":
                carregar_demonstracao(estoque)
                print("  base de demonstração carregada.")
            else:
                print("  opção inválida.")
        except (KeyError, ValueError) as erro:
            print("  erro:", erro.args[0] if erro.args else erro)

if __name__ == "__main__":
    demo() if "--demo" in sys.argv else menu()
