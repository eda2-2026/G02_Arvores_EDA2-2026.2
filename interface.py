# interface gráfica do sistema de estoque FEFO (tkinter, já vem com o python)
#
# uso: python interface.py
#
# aba "Estoque": produtos (AVL), lotes do produto (rubro-negra do produto),
#               relatório de vencimento (rubro-negra global) e as operações.
# aba "Árvores": desenho das duas árvores, atualizado a cada operação.
# embaixo: painel com altura e contadores das árvores + registro das operações.
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, simpledialog, ttk

from main import carregar_demonstracao
from src.estoque import Estoque
from src.models import Lote, Produto

HOJE = date.today()
DIAS_ALERTA = 30

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, CINZA, FUNDO, LINHA = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
FUNDO_VENCIDO, FUNDO_ALERTA = "#fde2dd", "#fff1cc"
VERMELHO_NO, PRETO_NO = "#d03b2a", "#1f1f1f"

def fmt_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def situacao(lote: Lote) -> tuple[str, str]:
    # (texto, tag de cor da linha)
    if lote.validade < HOJE:
        return "VENCIDO", "vencido"
    dias = (lote.validade - HOJE).days
    if dias <= DIAS_ALERTA:
        return f"vence em {dias} dia(s)", "alerta"
    return "ok", ""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Estoque FEFO — AVL + Rubro-Negra (G02 · EDA2)")
        self.geometry("1320x820")
        self.minsize(1100, 700)
        try:
            self.state("zoomed")  # abre maximizada no windows
        except tk.TclError:
            pass
        self.configure(bg=FUNDO)
        self._estilo()

        self.estoque = Estoque()
        carregar_demonstracao(self.estoque)
        self.proximo_lote = 1000

        self._montar_topo()
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.aba_estoque = ttk.Frame(abas, style="Fundo.TFrame")
        self.aba_arvores = ttk.Frame(abas, style="Fundo.TFrame")
        abas.add(self.aba_estoque, text="  Estoque  ")
        abas.add(self.aba_arvores, text="  Árvores  ")
        abas.bind("<<NotebookTabChanged>>", lambda e: self.desenhar_arvores())

        self._montar_aba_estoque()
        self._montar_aba_arvores()
        self._montar_rodape()

        self.registrar(f"Base de demonstração carregada: {len(self.estoque.produtos)} produtos "
                       f"na AVL e {len(self.estoque.vencimentos)} lotes na Rubro-Negra.")
        self.atualizar_tudo()

    # ------------------------------------------------------------ estilo

    def _estilo(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        fonte = ("Segoe UI", 10)
        st.configure(".", font=fonte, background=FUNDO, foreground=TINTA)
        st.configure("Fundo.TFrame", background=FUNDO)
        st.configure("Cartao.TFrame", background="white", relief="solid", borderwidth=1)
        st.configure("Titulo.TLabel", font=("Segoe UI", 16, "bold"), background=FUNDO)
        st.configure("Sub.TLabel", font=("Segoe UI", 10), foreground=CINZA, background=FUNDO)
        st.configure("Secao.TLabel", font=("Segoe UI", 11, "bold"), background=FUNDO)
        st.configure("Treeview", rowheight=24, font=("Segoe UI", 10), fieldbackground="white")
        st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#f0efec")
        st.map("Treeview", background=[("selected", "#cfe2fb")], foreground=[("selected", TINTA)])
        st.configure("TButton", padding=(10, 4))
        st.configure("Acao.TButton", font=("Segoe UI", 10, "bold"))
        st.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(12, 5))

    def _montar_topo(self):
        topo = ttk.Frame(self, style="Fundo.TFrame")
        topo.pack(fill="x", padx=14, pady=(10, 6))
        ttk.Label(topo, text="Estoque FEFO", style="Titulo.TLabel").pack(side="left")
        ttk.Label(topo, text="   vende primeiro o lote que vence primeiro · produtos na AVL, "
                             "lotes na Rubro-Negra", style="Sub.TLabel").pack(side="left", pady=(6, 0))
        ttk.Label(topo, text=f"Hoje: {fmt_data(HOJE)}", style="Secao.TLabel").pack(side="right")

    # ------------------------------------------------------------ aba estoque

    def _tabela(self, pai, colunas, alturas=10):
        quadro = ttk.Frame(pai, style="Fundo.TFrame")
        tv = ttk.Treeview(quadro, columns=[c[0] for c in colunas], show="headings", height=alturas)
        for nome, titulo, largura, ancora in colunas:
            tv.heading(nome, text=titulo)
            tv.column(nome, width=largura, anchor=ancora, stretch=nome in ("nome", "situacao"))
        barra = ttk.Scrollbar(quadro, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=barra.set)
        tv.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        tv.tag_configure("vencido", background=FUNDO_VENCIDO)
        tv.tag_configure("alerta", background=FUNDO_ALERTA)
        return quadro, tv

    def _montar_aba_estoque(self):
        raiz = self.aba_estoque
        raiz.columnconfigure(0, weight=5)
        raiz.columnconfigure(1, weight=4)
        raiz.rowconfigure(0, weight=1)

        # ---- esquerda: produtos (AVL)
        esq = ttk.Frame(raiz, style="Fundo.TFrame")
        esq.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=8)
        cab = ttk.Frame(esq, style="Fundo.TFrame")
        cab.pack(fill="x")
        ttk.Label(cab, text="Produtos", style="Secao.TLabel").pack(side="left")
        ttk.Label(cab, text="  AVL · chave = código · listados pelo percurso em ordem",
                  style="Sub.TLabel").pack(side="left")

        busca = ttk.Frame(esq, style="Fundo.TFrame")
        busca.pack(fill="x", pady=6)
        ttk.Label(busca, text="Código:").pack(side="left")
        self.ent_busca = ttk.Entry(busca, width=12)
        self.ent_busca.pack(side="left", padx=6)
        self.ent_busca.bind("<Return>", lambda e: self.buscar())
        ttk.Button(busca, text="Buscar na AVL", command=self.buscar).pack(side="left")
        ttk.Button(busca, text="Cadastrar produto", command=self.cadastrar).pack(side="right")

        quadro, self.tv_produtos = self._tabela(esq, [
            ("codigo", "Código", 80, "center"), ("nome", "Produto", 200, "w"),
            ("categoria", "Categoria", 110, "w"), ("qtd", "Estoque", 70, "e"),
            ("preco", "Preço", 80, "e")], alturas=18)
        quadro.pack(fill="both", expand=True)
        self.tv_produtos.bind("<<TreeviewSelect>>", lambda e: self.mostrar_lotes())

        # ---- direita: lotes + ações + relatório
        dir_ = ttk.Frame(raiz, style="Fundo.TFrame")
        dir_.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=8)

        self.lbl_lotes = ttk.Label(dir_, text="Lotes do produto", style="Secao.TLabel")
        self.lbl_lotes.pack(anchor="w")
        ttk.Label(dir_, text="Rubro-Negra do produto · chave = (validade, lote) · ordem FEFO",
                  style="Sub.TLabel").pack(anchor="w")
        quadro, self.tv_lotes = self._tabela(dir_, [
            ("lote", "Lote", 80, "center"), ("validade", "Validade", 90, "center"),
            ("qtd", "Qtd.", 55, "e"), ("situacao", "Situação", 140, "w")], alturas=5)
        quadro.pack(fill="x", pady=(4, 8))

        acoes = ttk.Frame(dir_, style="Fundo.TFrame")
        acoes.pack(fill="x")
        acoes.columnconfigure(1, weight=1)

        ttk.Label(acoes, text="Venda FEFO", style="Secao.TLabel").grid(row=0, column=0, sticky="w")
        linha = ttk.Frame(acoes, style="Fundo.TFrame")
        linha.grid(row=0, column=1, sticky="w", padx=8, pady=3)
        self.sp_venda = ttk.Spinbox(linha, from_=1, to=999, width=6)
        self.sp_venda.set(10)
        self.sp_venda.pack(side="left")
        ttk.Label(linha, text=" un.  ").pack(side="left")
        ttk.Button(linha, text="Vender", style="Acao.TButton", command=self.vender).pack(side="left")

        ttk.Label(acoes, text="Receber lote", style="Secao.TLabel").grid(row=1, column=0, sticky="w")
        linha = ttk.Frame(acoes, style="Fundo.TFrame")
        linha.grid(row=1, column=1, sticky="w", padx=8, pady=3)
        ttk.Label(linha, text="validade").pack(side="left")
        self.ent_validade = ttk.Entry(linha, width=11)
        self.ent_validade.insert(0, fmt_data(HOJE + timedelta(days=180)))
        self.ent_validade.pack(side="left", padx=4)
        self.sp_receber = ttk.Spinbox(linha, from_=1, to=999, width=6)
        self.sp_receber.set(50)
        self.sp_receber.pack(side="left")
        ttk.Label(linha, text=" un.  ").pack(side="left")
        ttk.Button(linha, text="Receber", command=self.receber).pack(side="left")

        linha = ttk.Frame(acoes, style="Fundo.TFrame")
        linha.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Button(linha, text="Recall do lote selecionado", command=self.recall).pack(side="left")
        ttk.Button(linha, text="Descartar vencidos", command=self.descartar).pack(side="left", padx=8)
        ttk.Button(linha, text="Recarregar base", command=self.recarregar).pack(side="left")

        ttk.Separator(dir_).pack(fill="x", pady=10)
        cab = ttk.Frame(dir_, style="Fundo.TFrame")
        cab.pack(fill="x")
        ttk.Label(cab, text="Vencendo nos próximos", style="Secao.TLabel").pack(side="left")
        self.sp_dias = ttk.Spinbox(cab, from_=1, to=730, width=5)
        self.sp_dias.set(DIAS_ALERTA)
        self.sp_dias.pack(side="left", padx=6)
        ttk.Label(cab, text="dias", style="Secao.TLabel").pack(side="left")
        ttk.Button(cab, text="Consultar", command=self.relatorio).pack(side="right")
        ttk.Label(dir_, text="Rubro-Negra global · consulta por intervalo O(log n + k)",
                  style="Sub.TLabel").pack(anchor="w")
        quadro, self.tv_relatorio = self._tabela(dir_, [
            ("lote", "Lote", 80, "center"), ("nome", "Produto", 170, "w"),
            ("validade", "Validade", 90, "center"), ("qtd", "Qtd.", 55, "e")], alturas=6)
        quadro.pack(fill="both", expand=True, pady=(4, 0))

    # ------------------------------------------------------------ aba árvores

    def _montar_aba_arvores(self):
        raiz = self.aba_arvores
        topo = ttk.Frame(raiz, style="Fundo.TFrame")
        topo.pack(fill="x", padx=4, pady=(8, 2))
        ttk.Label(topo, text="As duas árvores, desenhadas a partir da estrutura real",
                  style="Secao.TLabel").pack(side="left")
        ttk.Label(topo, text="   AVL: últimos 3 dígitos do código · Rubro-Negra: validade do lote",
                  style="Sub.TLabel").pack(side="left")
        quadro = ttk.Frame(raiz, style="Fundo.TFrame")
        quadro.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas = tk.Canvas(quadro, bg="white", highlightthickness=1,
                                highlightbackground=LINHA)
        sx = ttk.Scrollbar(quadro, orient="horizontal", command=self.canvas.xview)
        sy = ttk.Scrollbar(quadro, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.desenhar_arvores())

    # ------------------------------------------------------------ rodapé

    def _montar_rodape(self):
        rod = ttk.Frame(self, style="Fundo.TFrame")
        rod.pack(fill="x", padx=12, pady=(0, 10))
        rod.columnconfigure(2, weight=1)

        self.lbl_avl = self._cartao(rod, 0, "AVL · produtos", AZUL)
        self.lbl_rn = self._cartao(rod, 1, "Rubro-Negra · lotes por validade", LARANJA)

        log = ttk.Frame(rod, style="Fundo.TFrame")
        log.grid(row=0, column=2, sticky="nsew")
        ttk.Label(log, text="Registro das operações", style="Secao.TLabel").pack(anchor="w")
        self.txt_log = tk.Text(log, height=6, font=("Consolas", 9), bg="white", fg=TINTA,
                               relief="solid", borderwidth=1, wrap="word")
        self.txt_log.pack(fill="both", expand=True)
        self.txt_log.configure(state="disabled")

    def _cartao(self, pai, coluna, titulo, cor):
        c = tk.Frame(pai, bg="white", highlightthickness=1, highlightbackground=LINHA)
        c.grid(row=0, column=coluna, sticky="nsew", padx=(0, 10))
        tk.Frame(c, bg=cor, height=4).pack(fill="x")
        tk.Label(c, text=titulo, bg="white", fg=TINTA, font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        lbl = tk.Label(c, text="", bg="white", fg=CINZA, font=("Segoe UI", 10),
                       justify="left", anchor="w")
        lbl.pack(fill="x", padx=10, pady=(2, 8))
        return lbl

    # ------------------------------------------------------------ atualização

    def registrar(self, texto: str):
        self.txt_log.configure(state="normal")
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("1.0", f"[{hora}] {texto}\n")
        self.txt_log.configure(state="disabled")

    def _contadores(self):
        avl, rn = self.estoque.produtos, self.estoque.vencimentos
        return avl.rotacoes, avl.comparacoes, rn.rotacoes, rn.recoloracoes

    def _delta(self, antes) -> str:
        depois = self._contadores()
        partes = []
        if depois[0] - antes[0]:
            partes.append(f"AVL +{depois[0] - antes[0]} rotação(ões)")
        if depois[2] - antes[2] or depois[3] - antes[3]:
            partes.append(f"Rubro-Negra +{depois[2] - antes[2]} rotação(ões), "
                          f"+{depois[3] - antes[3]} recoloração(ões)")
        return ("  [" + "; ".join(partes) + "]") if partes else ""

    def atualizar_tudo(self, manter_codigo=None):
        codigo = manter_codigo or self.codigo_selecionado()
        self.tv_produtos.delete(*self.tv_produtos.get_children())
        for p in self.estoque.listar_produtos():
            self.tv_produtos.insert("", "end", iid=str(p.codigo), values=(
                p.codigo, p.nome, p.categoria, p.quantidade, f"R$ {p.preco:.2f}"))
        if codigo and self.tv_produtos.exists(str(codigo)):
            self.tv_produtos.selection_set(str(codigo))
            self.tv_produtos.see(str(codigo))
        self.mostrar_lotes()
        self.relatorio(registrar=False)
        self.atualizar_paineis()
        self.desenhar_arvores()

    def atualizar_paineis(self):
        avl, rn = self.estoque.produtos, self.estoque.vencimentos
        self.lbl_avl.configure(text=(
            f"{len(avl)} nós · altura {avl.altura()}\n"
            f"{avl.rotacoes} rotações desde o início"))
        self.lbl_rn.configure(text=(
            f"{len(rn)} nós · altura {rn.altura()}\n"
            f"{rn.rotacoes} rotações · {rn.recoloracoes} recolorações desde o início"))

    def codigo_selecionado(self):
        sel = self.tv_produtos.selection() if hasattr(self, "tv_produtos") else ()
        return int(sel[0]) if sel else None

    def mostrar_lotes(self):
        self.tv_lotes.delete(*self.tv_lotes.get_children())
        codigo = self.codigo_selecionado()
        if codigo is None:
            self.lbl_lotes.configure(text="Lotes do produto (selecione um produto)")
            return
        p = self.estoque.buscar_produto(codigo)
        self.lbl_lotes.configure(text=f"Lotes de {p.nome}")
        for _, lote in p.lotes.em_ordem():
            texto, tag = situacao(lote)
            self.tv_lotes.insert("", "end", iid=str(lote.lote_id), tags=(tag,), values=(
                f"L{lote.lote_id:06d}", fmt_data(lote.validade), lote.quantidade, texto))

    def relatorio(self, registrar=True):
        try:
            dias = int(self.sp_dias.get())
        except ValueError:
            dias = DIAS_ALERTA
        self.tv_relatorio.delete(*self.tv_relatorio.get_children())
        lotes = self.estoque.vencendo_ate(HOJE, dias)
        for lote in lotes:
            p = self.estoque.buscar_produto(lote.codigo_produto)
            _, tag = situacao(lote)
            self.tv_relatorio.insert("", "end", tags=(tag,), values=(
                f"L{lote.lote_id:06d}", p.nome, fmt_data(lote.validade), lote.quantidade))
        if registrar:
            self.registrar(f"Consulta por intervalo: {len(lotes)} lote(s) vencem nos próximos "
                           f"{dias} dias (já em ordem de validade).")

    # ------------------------------------------------------------ operações

    def _exigir_produto(self):
        codigo = self.codigo_selecionado()
        if codigo is None:
            messagebox.showinfo("Estoque", "Selecione um produto na tabela.")
        return codigo

    def buscar(self):
        try:
            codigo = int(self.ent_busca.get())
        except ValueError:
            messagebox.showwarning("Busca", "Digite um código numérico.")
            return
        avl = self.estoque.produtos
        antes = avl.comparacoes
        p = self.estoque.buscar_produto(codigo)
        comp = avl.comparacoes - antes
        if p is None:
            self.registrar(f"Busca na AVL: código {codigo} não existe "
                           f"({comp} comparações, altura {avl.altura()}).")
            return
        self.tv_produtos.selection_set(str(codigo))
        self.tv_produtos.see(str(codigo))
        self.registrar(f"Busca na AVL: {p.nome} encontrado em {comp} comparação(ões) "
                       f"(altura da árvore: {avl.altura()}).")

    def cadastrar(self):
        codigo = simpledialog.askinteger("Cadastrar produto", "Código:", parent=self)
        if codigo is None:
            return
        nome = simpledialog.askstring("Cadastrar produto", "Nome:", parent=self)
        if not nome:
            return
        preco = simpledialog.askfloat("Cadastrar produto", "Preço (R$):", parent=self,
                                      minvalue=0)
        if preco is None:
            return
        antes = self._contadores()
        if not self.estoque.cadastrar_produto(Produto(codigo, nome, "Geral", preco)):
            messagebox.showwarning("Cadastro", f"O código {codigo} já está cadastrado.")
            return
        self.registrar(f"Produto {codigo} ({nome}) inserido na AVL.{self._delta(antes)}")
        self.atualizar_tudo(manter_codigo=codigo)

    def vender(self):
        codigo = self._exigir_produto()
        if codigo is None:
            return
        try:
            qtd = int(self.sp_venda.get())
            antes = self._contadores()
            retirado = self.estoque.vender(codigo, qtd, HOJE)
        except ValueError as erro:
            messagebox.showwarning("Venda", str(erro))
            return
        partes = ", ".join(f"{q} do L{l.lote_id:06d} (vence {fmt_data(l.validade)})"
                           for l, q in retirado)
        self.registrar(f"Venda FEFO de {qtd} un.: {partes}.{self._delta(antes)}")
        self.atualizar_tudo()

    def receber(self):
        codigo = self._exigir_produto()
        if codigo is None:
            return
        try:
            validade = datetime.strptime(self.ent_validade.get().strip(), "%d/%m/%Y").date()
            qtd = int(self.sp_receber.get())
        except ValueError:
            messagebox.showwarning("Receber lote", "Use a data no formato dd/mm/aaaa.")
            return
        antes = self._contadores()
        lote = Lote(self.proximo_lote, codigo, validade, qtd)
        self.estoque.receber_lote(lote)
        self.proximo_lote += 1
        self.registrar(f"Lote L{lote.lote_id:06d} recebido ({qtd} un., vence "
                       f"{fmt_data(validade)}): inserido nas duas rubro-negras.{self._delta(antes)}")
        self.atualizar_tudo()

    def recall(self):
        codigo = self._exigir_produto()
        if codigo is None:
            return
        sel = self.tv_lotes.selection()
        if not sel:
            messagebox.showinfo("Recall", "Selecione um lote na tabela de lotes.")
            return
        antes = self._contadores()
        lote = self.estoque.recall(codigo, int(sel[0]))
        self.registrar(f"Recall: lote L{lote.lote_id:06d} removido das duas rubro-negras."
                       f"{self._delta(antes)}")
        self.atualizar_tudo()

    def descartar(self):
        antes = self._contadores()
        descartados = self.estoque.descartar_vencidos(HOJE)
        if not descartados:
            self.registrar("Descarte: nenhum lote vencido.")
            return
        ids = ", ".join(f"L{l.lote_id:06d}" for l in descartados)
        self.registrar(f"Descarte: {len(descartados)} lote(s) vencido(s) removido(s) "
                       f"pelo mínimo da Rubro-Negra ({ids}).{self._delta(antes)}")
        self.atualizar_tudo()

    def recarregar(self):
        self.estoque = Estoque()
        carregar_demonstracao(self.estoque)
        self.proximo_lote = 1000
        self.registrar("Base de demonstração recarregada.")
        self.atualizar_tudo()

    # ------------------------------------------------------------ desenho

    def desenhar_arvores(self):
        # desenha as duas árvores ajustadas ao tamanho atual da janela:
        # x = posição no percurso em ordem, y = profundidade do nó
        cv = self.canvas
        cv.delete("all")
        avl, rn = self.estoque.produtos, self.estoque.vencimentos
        largura = max(cv.winfo_width(), 900)
        altura = max(cv.winfo_height(), 480)
        ha, hr = max(avl.altura(), 1), max(rn.altura(), 1)

        titulo, margem = 30, 18
        r_max = 16
        livre = altura - 2 * titulo - 4 * r_max - 3 * margem
        passo_y = max(28, min(62, livre / max(ha - 1 + hr - 1, 1)))

        y = margem
        y = self._desenhar(
            avl.raiz, None, y, largura, passo_y,
            rotulo=lambda n, r: str(n.chave)[-3:],
            cor=lambda n: AZUL,
            titulo=f"AVL — produtos ({len(avl)} nós, altura {avl.altura()})",
            cor_titulo=AZUL)
        self._desenhar(
            rn.raiz, rn.NIL, y + margem, largura, passo_y,
            rotulo=self._rotulo_validade,
            cor=lambda n: VERMELHO_NO if n.cor else PRETO_NO,
            titulo=(f"Rubro-Negra — lotes de todos os produtos por validade "
                    f"({len(rn)} nós, altura {rn.altura()})"),
            cor_titulo=LARANJA, legenda=True)
        cv.configure(scrollregion=cv.bbox("all"))

    @staticmethod
    def _rotulo_validade(no, raio):
        v = no.chave[0]
        if raio >= 17:
            return v.strftime("%d/%m")
        if raio >= 10:
            return v.strftime("%d\n%m")  # dia em cima, mês embaixo
        return ""

    def _desenhar(self, raiz, nulo, y0, largura, passo_y, rotulo, cor, titulo,
                  cor_titulo, legenda=False):
        cv = self.canvas
        cv.create_text(20, y0 + 10, text=titulo, anchor="w", fill=cor_titulo,
                       font=("Segoe UI", 11, "bold"))
        if legenda:
            x = 20 + len(titulo) * 7.6 + 30
            for texto, c in (("vermelho", VERMELHO_NO), ("preto", PRETO_NO)):
                cv.create_oval(x, y0 + 4, x + 12, y0 + 16, fill=c, outline="")
                cv.create_text(x + 17, y0 + 10, text=texto, anchor="w", fill=CINZA,
                               font=("Segoe UI", 9))
                x += 85
            cv.create_text(x + 10, y0 + 10, anchor="w", fill=CINZA, font=("Segoe UI", 9),
                           text="rótulo = validade (dia / mês)")
        if raiz is nulo:
            return y0 + 50

        # percurso em ordem iterativo, guardando a profundidade de cada nó
        ordem, prof = [], {}
        pilha, atual, d = [], raiz, 0
        while pilha or atual is not nulo:
            while atual is not nulo:
                pilha.append((atual, d))
                atual, d = atual.esquerda, d + 1
            atual, d = pilha.pop()
            ordem.append(atual)
            prof[id(atual)] = d
            atual, d = atual.direita, d + 1

        passo_x = min(44, (largura - 40) / len(ordem))
        raio = max(6, min(16, passo_x / 2 - 1.5))
        topo = y0 + 30 + raio
        pos = {id(no): (20 + passo_x / 2 + i * passo_x, topo + prof[id(no)] * passo_y)
               for i, no in enumerate(ordem)}

        for no in ordem:  # arestas primeiro, nós por cima
            x, y = pos[id(no)]
            for filho in (no.esquerda, no.direita):
                if filho is not nulo:
                    fx, fy = pos[id(filho)]
                    cv.create_line(x, y, fx, fy, fill="#b9b8b4", width=1.5)
        fonte = ("Segoe UI", 8 if raio >= 14 else 7, "bold")
        for no in ordem:
            x, y = pos[id(no)]
            cv.create_oval(x - raio, y - raio, x + raio, y + raio, fill=cor(no),
                           outline="white", width=1.5)
            texto = rotulo(no, raio)
            if texto:
                cv.create_text(x, y, text=texto, fill="white", font=fonte, justify="center")
        return topo + max(prof.values()) * passo_y + raio

if __name__ == "__main__":
    App().mainloop()
