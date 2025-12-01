import customtkinter as ctk
from tkinter import messagebox
import sys
import mysql.connector
from mysql.connector import errorcode

#  Configurações Iniciais do CustomTkinter 
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

#  Credenciais de Login 
ADMIN_USER = "admin"
ADMIN_PASS = "senha123"


# CONFIG BANCO
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '991071692',
    'database': 'estoque_pyz'
}


# FUNÇÕES DO BANCO DE DADOS 

def get_db_conn():
    """Cria e retorna uma conexão com o banco de dados MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            messagebox.showerror("Erro de DB", "Usuário ou senha do MySQL incorretos.\nVerifique a configuração 'DB_CONFIG'.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            messagebox.showerror("Erro de DB", f"O banco de dados '{DB_CONFIG['database']}' não existe.\nExecute o setup primeiro.")
        else:
            messagebox.showerror("Erro de DB", f"Erro ao conectar: {err}")
        sys.exit()

def setup_database():
    """
    Cria o banco de dados (se não existir) e as tabelas (se não existirem),
    e popula dados de exemplo incluindo as relações mouse_pecas.
    """
    try:
        temp_conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = temp_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} DEFAULT CHARACTER SET utf8")
        cursor.close()
        temp_conn.close()
    except mysql.connector.Error as err:
        messagebox.showerror("Erro Crítico de DB", f"Não foi possível conectar ao MySQL ou criar o banco de dados: {err}\n\nVerifique suas credenciais em DB_CONFIG e se o servidor MySQL está rodando.")
        sys.exit()

    conn = get_db_conn()
    cursor = conn.cursor()

    # Tabelas base
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mouses (
        id INT PRIMARY KEY AUTO_INCREMENT,
        nome VARCHAR(255) NOT NULL,
        modelo VARCHAR(255) NOT NULL,
        quantidade INT NOT NULL,
        preco DECIMAL(10, 2) NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pecas (
        id INT PRIMARY KEY AUTO_INCREMENT,
        nome VARCHAR(255) NOT NULL,
        modelo VARCHAR(255) NOT NULL,
        quantidade INT NOT NULL,
        custo DECIMAL(10, 2) NOT NULL
    )
    """)

    # Tabela que relaciona quantas peças são necessárias para montar 1 mouse de determinado id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mouse_pecas (
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_mouse INT NOT NULL,
        id_peca INT NOT NULL,
        quantidade_necessaria INT NOT NULL,
        FOREIGN KEY (id_mouse) REFERENCES mouses(id) ON DELETE CASCADE,
        FOREIGN KEY (id_peca) REFERENCES pecas(id) ON DELETE CASCADE
    )
    """)

    #  exemplos se tabelas estiverem vazias
    dict_cursor = conn.cursor(dictionary=True)
    dict_cursor.execute("SELECT COUNT(*) AS count FROM mouses")
    if dict_cursor.fetchone()['count'] == 0:
        cursor.executemany("INSERT INTO mouses (nome, modelo, quantidade, preco) VALUES (%s, %s, %s, %s)", [
            ("Mouse Gamer", "Logitech G Pro X", 10, 399.99),
            ("Mouse Ergonômico", "Dell WM527", 5, 89.50),
            ("Mouse Sem Fio", "Razer Viper Mini", 8, 249.90)
        ])

    dict_cursor.execute("SELECT COUNT(*) AS count FROM pecas")
    if dict_cursor.fetchone()['count'] == 0:
        cursor.executemany("INSERT INTO pecas (nome, modelo, quantidade, custo) VALUES (%s, %s, %s, %s)", [
            ("Sensor Óptico", "PixArt 3360", 100, 15.00),
            ("Bateria Recarregável", "Li-Po 500mAh", 60, 8.50),
            ("Micro Switch", "Omron D2FC-F-7N", 300, 1.20),
            ("Cabo USB", "USB-C 1.8m", 80, 3.50),
            ("Carcaça Plástica", "ABS Preto", 90, 5.00)
        ])

    conn.commit()

    # Inserir relações de exemplo entre mouses e peças (somente se mouse_pecas estiver vazio)
    dict_cursor.execute("SELECT COUNT(*) AS count FROM mouse_pecas")
    if dict_cursor.fetchone()['count'] == 0:
        dict_cursor.execute("SELECT id, nome FROM mouses")
        mouses = {row['nome']: row['id'] for row in dict_cursor.fetchall()}

        dict_cursor.execute("SELECT id, nome FROM pecas")
        pecas_rows = dict_cursor.fetchall()
        pecas_map = {r['nome'].lower().strip(): r['id'] for r in pecas_rows}

        relations = []
        if "Mouse Gamer" in mouses:
            mid = mouses["Mouse Gamer"]
            if "sensor óptico" in pecas_map:
                relations.append((mid, pecas_map["sensor óptico"], 1))
            if "micro switch" in pecas_map:
                relations.append((mid, pecas_map["micro switch"], 2))
            if "cabo usb" in pecas_map:
                relations.append((mid, pecas_map["cabo usb"], 1))
            for candidate in ("carcaça plástica", "carcaca plastica", "carcaça", "carcaça abs"):
                if candidate in pecas_map:
                    relations.append((mid, pecas_map[candidate], 1))
                    break

        if "Mouse Sem Fio" in mouses:
            mid = mouses["Mouse Sem Fio"]
            if "sensor óptico" in pecas_map:
                relations.append((mid, pecas_map["sensor óptico"], 1))
            if "micro switch" in pecas_map:
                relations.append((mid, pecas_map["micro switch"], 2))
            if "bateria recarregável" in pecas_map:
                relations.append((mid, pecas_map["bateria recarregável"], 1))

        if "Mouse Ergonômico" in mouses:
            mid = mouses["Mouse Ergonômico"]
            if "sensor óptico" in pecas_map:
                relations.append((mid, pecas_map["sensor óptico"], 1))
            if "micro switch" in pecas_map:
                relations.append((mid, pecas_map["micro switch"], 2))
            for candidate in ("carcaça plástica", "carcaca plastica", "carcaça"):
                if candidate in pecas_map:
                    relations.append((mid, pecas_map[candidate], 1))
                    break

        # Remove duplicatas e quantidades inválidas
        unique = {}
        for mid, pid, q in relations:
            if q <= 0:
                continue
            unique[(mid, pid)] = q
        to_insert = [(mid, pid, q) for (mid, pid), q in unique.items()]

        if to_insert:
            cursor.executemany("INSERT INTO mouse_pecas (id_mouse, id_peca, quantidade_necessaria) VALUES (%s, %s, %s)", to_insert)
            conn.commit()

    dict_cursor.close()
    cursor.close()
    conn.close()


# CLASSE DO PAINEL DE CONTROLE ADMINISTRATIVO (ESTOQUE + PRODUÇÃO + COMPOSIÇÃO)


class AdminDashboard(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("Dashboard Administrativo - Gestão de Estoques (MySQL)")
        self.geometry("1280x820")
        self.minsize(1000, 700)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.grab_set()

        # Grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Tabs
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Estoque de Mouses")
        self.tabview.add("Estoque de Peças")
        self.tabview.add("Produção de Mouses")
        self.tabview.add("Composição de Mouses")

        # Configure tabs
        for name in ("Estoque de Mouses", "Estoque de Peças", "Produção de Mouses", "Composição de Mouses"):
            tab = self.tabview.tab(name)
            tab.grid_columnconfigure(1, weight=3)
            tab.grid_rowconfigure(0, weight=1)

        # Cria abas
        self._criar_aba_mouses()
        self._criar_aba_pecas()
        self._criar_aba_producao()
        self._criar_aba_composicao()

        # Carrega dados iniciais
        self.mostrar_estoque(tipo="mouses")
        self.mostrar_estoque(tipo="pecas")

        # IMPORTANTE: garante que comboboxes reflitam o estado atual do DB
        self.carregar_modelos_para_producao()
        self.carregar_modelos_para_composicao()
        self.carregar_pecas_para_composicao()

    #  Abas mouses e pecas 

    def _criar_aba_mouses(self):
        tab = self.tabview.tab("Estoque de Mouses")
        self.frame_controles_mouses = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_controles_mouses.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_controles_mouses.grid_rowconfigure(7, weight=1)
        self._criar_controles(self.frame_controles_mouses, tipo="mouses")

        self.frame_visualizacao_mouses = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_visualizacao_mouses.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.frame_visualizacao_mouses.grid_columnconfigure(0, weight=1)
        self.frame_visualizacao_mouses.grid_rowconfigure(2, weight=1)
        self._criar_visualizacao(self.frame_visualizacao_mouses, tipo="mouses")

    def _criar_aba_pecas(self):
        tab = self.tabview.tab("Estoque de Peças")
        self.frame_controles_pecas = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_controles_pecas.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_controles_pecas.grid_rowconfigure(7, weight=1)
        self._criar_controles(self.frame_controles_pecas, tipo="pecas")

        self.frame_visualizacao_pecas = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_visualizacao_pecas.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.frame_visualizacao_pecas.grid_columnconfigure(0, weight=1)
        self.frame_visualizacao_pecas.grid_rowconfigure(2, weight=1)
        self._criar_visualizacao(self.frame_visualizacao_pecas, tipo="pecas")

    #   Produção de Mouses 

    def _criar_aba_producao(self):
        tab = self.tabview.tab("Produção de Mouses")
        # Left: controles de produção
        self.frame_controles_producao = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_controles_producao.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_controles_producao.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(self.frame_controles_producao, text="Produção de Mouses", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(18, 8))

        ctk.CTkLabel(self.frame_controles_producao, text="Modelo de Mouse (selecionar)").pack(fill="x", padx=20, pady=(8, 2))
        self.combo_modelos = ctk.CTkComboBox(self.frame_controles_producao, values=[], command=self.on_modelo_selected)
        self.combo_modelos.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.frame_controles_producao, text="Quantidade a fabricar").pack(fill="x", padx=20, pady=(8, 2))
        self.entry_qtd_producao = ctk.CTkEntry(self.frame_controles_producao, placeholder_text="Ex: 10")
        self.entry_qtd_producao.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(self.frame_controles_producao, text="Verificar Peças Necessárias", command=self.mostrar_composicao_selecionada).pack(pady=(8, 6), padx=20, fill="x")
        ctk.CTkButton(self.frame_controles_producao, text="Fabricar Mouse(s)", command=self.fabricar_mouses, fg_color="#2ecc71").pack(pady=(6, 6), padx=20, fill="x")

        ctk.CTkLabel(self.frame_controles_producao, text="Observação: O sistema irá verificar estoque de peças e, se suficiente, debitará automaticamente.").pack(pady=(8, 4), padx=20)

        # Right: visualização da composição e resultado
        self.frame_visualizacao_producao = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_visualizacao_producao.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.frame_visualizacao_producao.grid_columnconfigure(0, weight=1)
        self.frame_visualizacao_producao.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.frame_visualizacao_producao, text="Peças Necessárias por Unidade", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(16, 6), padx=20, sticky="w")

        self.scroll_frame_composicao = ctk.CTkScrollableFrame(self.frame_visualizacao_producao, label_text="Composição do Modelo")
        self.scroll_frame_composicao.grid(row=1, column=0, padx=20, pady=(6, 10), sticky="nsew")
        self.scroll_frame_composicao.columnconfigure(0, weight=1)

        self.label_status_producao = ctk.CTkLabel(self.frame_visualizacao_producao, text="", font=ctk.CTkFont(size=14))
        self.label_status_producao.grid(row=2, column=0, pady=10, padx=20, sticky="w")

    #  Composição de Mouses

    def _criar_aba_composicao(self):
        tab = self.tabview.tab("Composição de Mouses")
        # Left: controles para adicionar peças a um mouse
        self.frame_controles_composicao = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_controles_composicao.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_controles_composicao.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(self.frame_controles_composicao, text="Composição de Mouses", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(18, 8))

        ctk.CTkLabel(self.frame_controles_composicao, text="Modelo de Mouse (selecionar)").pack(fill="x", padx=20, pady=(8, 2))
        self.combo_modelos_comp = ctk.CTkComboBox(self.frame_controles_composicao, values=[], command=self.on_modelo_comp_selected)
        self.combo_modelos_comp.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.frame_controles_composicao, text="Peça (selecionar)").pack(fill="x", padx=20, pady=(8, 2))
        self.combo_pecas_comp = ctk.CTkComboBox(self.frame_controles_composicao, values=[])
        self.combo_pecas_comp.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(self.frame_controles_composicao, text="Quantidade necessária por unidade").pack(fill="x", padx=20, pady=(8, 2))
        self.entry_qtd_peca = ctk.CTkEntry(self.frame_controles_composicao, placeholder_text="Ex: 2")
        self.entry_qtd_peca.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(self.frame_controles_composicao, text="Adicionar Peça ao Mouse", command=self.adicionar_peca_ao_mouse).pack(pady=(8, 6), padx=20, fill="x")
        ctk.CTkButton(self.frame_controles_composicao, text="Remover Relação Selecionada", command=self.remover_relacao_selecionada, fg_color="#e74c3c").pack(pady=(6, 6), padx=20, fill="x")

        ctk.CTkLabel(self.frame_controles_composicao, text="Selecione um modelo e adicione as peças necessárias. A lista à direita mostra as peças já associadas.", wraplength=260, text_color="gray").pack(pady=(8, 4), padx=20)

        # Right: lista de peças associadas ao modelo (com possibilidade de selecionar para remoção)
        self.frame_visualizacao_composicao = ctk.CTkFrame(tab, corner_radius=15)
        self.frame_visualizacao_composicao.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.frame_visualizacao_composicao.grid_columnconfigure(0, weight=1)
        self.frame_visualizacao_composicao.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_visualizacao_composicao, text="Peças associadas ao modelo", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(16, 6), padx=20, sticky="w")

        self.scroll_frame_assoc = ctk.CTkScrollableFrame(self.frame_visualizacao_composicao, label_text="Associações")
        self.scroll_frame_assoc.grid(row=1, column=0, padx=20, pady=(6, 10), sticky="nsew")
        self.scroll_frame_assoc.columnconfigure(0, weight=1)

        # controle interno: id selecionado para remoção (de mouse_pecas)
        self.selected_assoc_id = None

    #  UI genérica (controles e visualizações para mouses/pecas)

    def _criar_controles(self, parent_frame, tipo):
        if tipo == "mouses":
            titulo = "Gerenciamento de Mouses (Produto)"
            fields = [("ID (Atualizar/Remover)", "id"), ("Nome do Produto", "nome"), ("Modelo", "modelo"),
                      ("Quantidade", "quantidade"), ("Preço (R$)", "preco")]
            self.campos_mouses = {}
            target_dict = self.campos_mouses
            adicionar_cmd = lambda: self.adicionar_produto(tipo="mouses")
            atualizar_cmd = lambda: self.atualizar_produto(tipo="mouses")
            remover_cmd = lambda: self.remover_produto(tipo="mouses")
        else:
            titulo = "Gerenciamento de Peças (Insumo)"
            fields = [("ID (Atualizar/Remover)", "id"), ("Nome da Peça", "nome"), ("Modelo/Código", "modelo"),
                      ("Quantidade", "quantidade"), ("Custo (R$)", "custo")]
            self.campos_pecas = {}
            target_dict = self.campos_pecas
            adicionar_cmd = lambda: self.adicionar_produto(tipo="pecas")
            atualizar_cmd = lambda: self.atualizar_produto(tipo="pecas")
            remover_cmd = lambda: self.remover_produto(tipo="pecas")

        ctk.CTkLabel(parent_frame, text=titulo, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        for label_text, key in fields:
            ctk.CTkLabel(parent_frame, text=label_text, anchor="w").pack(fill="x", padx=25, pady=(5, 0))
            entry = ctk.CTkEntry(parent_frame, placeholder_text=label_text)
            entry.pack(fill="x", padx=25, pady=(0, 10))
            target_dict[key] = entry

        ctk.CTkButton(parent_frame, text="Adicionar Novo Item", command=adicionar_cmd).pack(pady=10, padx=25, fill="x")
        ctk.CTkButton(parent_frame, text="Atualizar Estoque", command=atualizar_cmd).pack(pady=10, padx=25, fill="x")
        ctk.CTkButton(parent_frame, text="Remover Item (Por ID)", command=remover_cmd).pack(pady=10, padx=25, fill="x")
        ctk.CTkLabel(parent_frame, text="Utilize o ID para Atualizar ou Remover", text_color="gray").pack(side="bottom", pady=20)

    def _criar_visualizacao(self, parent_frame, tipo):
        if tipo == "mouses":
            titulo, label_total_attr, scroll_frame_attr, color, frame_label = \
                "Estoque Atual de Mouses (Produtos)", "label_total_mouses", "scroll_frame_mouses", "blue", "Lista Detalhada de Mouses"
        else:
            titulo, label_total_attr, scroll_frame_attr, color, frame_label = \
                "Estoque Atual de Peças (Insumos)", "label_total_pecas", "scroll_frame_pecas", "orange", "Lista Detalhada de Componentes"

        ctk.CTkLabel(parent_frame, text=titulo, font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, pady=(20, 10), sticky="w", padx=20)

        frame_resumo = ctk.CTkFrame(parent_frame, fg_color=("gray90", "gray20"))
        frame_resumo.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        frame_resumo.grid_columnconfigure(0, weight=1)
        label_total = ctk.CTkLabel(frame_resumo, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=color)
        label_total.pack(pady=10)
        setattr(self, label_total_attr, label_total)

        scroll_frame = ctk.CTkScrollableFrame(parent_frame, label_text=frame_label)
        scroll_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        scroll_frame.columnconfigure(0, weight=1)
        setattr(self, scroll_frame_attr, scroll_frame)
        self._criar_cabecalho(scroll_frame, tipo=tipo)

    def _criar_cabecalho(self, parent_frame, tipo):
        cabecalho_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        cabecalho_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 5))

        if tipo == "mouses":
            colunas = [("ID", 1), ("Produto", 3), ("Modelo", 3), ("Quantidade", 2), ("Preço (R$)", 2)]
        else:
            colunas = [("ID", 1), ("Peça", 3), ("Modelo/Cód.", 3), ("Quantidade", 2), ("Custo (R$)", 2)]

        for i, (text, weight) in enumerate(colunas):
            cabecalho_frame.columnconfigure(i, weight=weight)
            label = ctk.CTkLabel(cabecalho_frame, text=text, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=i, sticky="ew", padx=5)

    #  Funções de CRUD e exibição 

    def _get_estoque_data(self, tipo):
        if tipo == "mouses":
            return ("mouses", self.campos_mouses, "mouse", "preco",
                    "label_total_mouses", "scroll_frame_mouses")
        else:
            return ("pecas", self.campos_pecas, "peça", "custo",
                    "label_total_pecas", "scroll_frame_pecas")

    def _limpar_campos(self, campos):
        for key in campos:
            try:
                campos[key].delete(0, 'end')
            except:
                pass

    def mostrar_estoque(self, tipo):
        """ Lê os dados do DB e atualiza a interface."""
        table_name, _, item_name, price_key, label_attr, scroll_attr = self._get_estoque_data(tipo)

        label_total = getattr(self, label_attr)
        scroll_frame = getattr(self, scroll_attr)

        # Remove linhas anteriores (exceto cabeçalho linha 0)
        for widget in list(scroll_frame.winfo_children()):
            info = widget.grid_info()
            if info and int(info.get("row", 0)) > 0:
                widget.destroy()

        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
        estoque = cursor.fetchall()
        conn.close()

        total = sum(item['quantidade'] for item in estoque)
        label_total.configure(text=f"📦 TOTAL DE {item_name.upper()}S EM ESTOQUE: {total}")

        if not estoque:
            ctk.CTkLabel(scroll_frame, text="O estoque está vazio.", anchor="center").grid(row=1, column=0, pady=20)
            return

        row_num = 1
        for item in estoque:
            item_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray20"))
            item_frame.grid(row=row_num, column=0, sticky="ew", padx=5, pady=2)

            colunas_display = [("id", 1), ("nome", 3), ("modelo", 3), ("quantidade", 2), (price_key, 2)]

            for i, (key, weight) in enumerate(colunas_display):
                item_frame.columnconfigure(i, weight=weight)
                text_content = str(item[key])
                if key == price_key:
                    text_content = f"R$ {float(item[price_key]):.2f}"
                label = ctk.CTkLabel(item_frame, text=text_content, anchor="w")
                label.grid(row=0, column=i, sticky="ew", padx=5)

            row_num += 1

    def adicionar_produto(self, tipo):
        table_name, campos, item_name, price_key, _, _ = self._get_estoque_data(tipo)

        try:
            nome = campos["nome"].get()
            modelo = campos["modelo"].get()
            quantidade = int(campos["quantidade"].get())
            price_value = float(campos[price_key].get().replace(',', '.'))

            if not nome or not modelo or quantidade < 0 or price_value < 0:
                raise ValueError("Preencha todos os campos obrigatórios corretamente (exceto ID).")

            conn = get_db_conn()
            cursor = conn.cursor()
            sql = f"INSERT INTO {table_name} (nome, modelo, quantidade, {price_key}) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (nome, modelo, quantidade, price_value))
            conn.commit()
            conn.close()

            self.mostrar_estoque(tipo)
            self._limpar_campos(campos)
            messagebox.showinfo("Sucesso", f"{item_name.capitalize()} '{nome}' adicionado ao banco de dados.")
            # Se foi adicionado um mouse, recarrega comboboxs relacionados
            if tipo == "mouses":
                # atualiza combobox de produção e composição
                self.carregar_modelos_para_producao()
                self.carregar_modelos_para_composicao()
            elif tipo == "pecas":
                # atualiza combobox de peças na aba composição
                self.carregar_pecas_para_composicao()
        except ValueError as e:
            messagebox.showerror("Erro de Entrada", f"Dados inválidos: {e}.")
        except Exception as e:
            messagebox.showerror("Erro no DB", f"Ocorreu um erro ao adicionar: {e}")

    def atualizar_produto(self, tipo):
        table_name, campos, item_name, price_key, _, _ = self._get_estoque_data(tipo)

        try:
            item_id = int(campos["id"].get())
            nova_quantidade = campos["quantidade"].get()
            novo_price_str = campos[price_key].get()

            if not item_id:
                raise ValueError(f"O ID da {item_name} é obrigatório para atualização.")

            conn = get_db_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (item_id,))
            item_encontrado = cursor.fetchone()

            if item_encontrado:
                quantidade_final = int(nova_quantidade) if nova_quantidade else item_encontrado['quantidade']
                price_final = float(novo_price_str.replace(',', '.')) if novo_price_str else float(item_encontrado[price_key])

                update_cursor = conn.cursor()
                sql = f"UPDATE {table_name} SET quantidade = %s, {price_key} = %s WHERE id = %s"
                update_cursor.execute(sql, (quantidade_final, price_final, item_id))
                conn.commit()
                update_cursor.close()

                self.mostrar_estoque(tipo)
                self._limpar_campos(campos)
                messagebox.showinfo("Sucesso", f"Estoque da {item_name} ID {item_id} atualizado com sucesso.")
                if table_name == "mouses":
                    self.carregar_modelos_para_producao()
                    self.carregar_modelos_para_composicao()
                elif table_name == "pecas":
                    self.carregar_pecas_para_composicao()
            else:
                messagebox.showerror("Erro", f"{item_name.capitalize()} com ID {item_id} não encontrado.")

            cursor.close()
            conn.close()

        except ValueError as e:
            messagebox.showerror("Erro de Entrada", f"Dados inválidos. {e}. Verifique se ID, Quantidade e Valor são números.")
        except Exception as e:
            messagebox.showerror("Erro no DB", f"Ocorreu um erro ao atualizar: {e}")

    def remover_produto(self, tipo):
        table_name, campos, item_name, _, _, _ = self._get_estoque_data(tipo)

        try:
            item_id = int(campos["id"].get())
            if not item_id:
                raise ValueError(f"O ID da {item_name} é obrigatório para remoção.")

            if not messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o item ID {item_id} da tabela '{table_name}'?"):
                return

            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (item_id,))
            conn.commit()
            conn.close()

            self.mostrar_estoque(tipo)
            self._limpar_campos(campos)
            messagebox.showinfo("Sucesso", f"{item_name.capitalize()} ID {item_id} removida do banco de dados.")
            # atualiza comboboxes conforme o tipo removido
            if table_name == "mouses":
                self.carregar_modelos_para_producao()
                self.carregar_modelos_para_composicao()
            elif table_name == "pecas":
                self.carregar_pecas_para_composicao()
        except ValueError as e:
            messagebox.showerror("Erro de Entrada", f"Dados inválidos. {e}. Verifique se o ID é um número.")
        except Exception as e:
            messagebox.showerror("Erro no DB", f"Ocorreu um erro ao remover: {e}")

    #  Funções de produção

    def carregar_modelos_para_producao(self):
        """Carrega mouses do DB e popula o combo de produção (texto: 'id - nome (modelo)')"""
        try:
            conn = get_db_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nome, modelo FROM mouses ORDER BY id")
            rows = cursor.fetchall()
            conn.close()

            self.modelos_map = {}  # display_text -> id
            values = []
            for r in rows:
                disp = f"{r['id']} - {r['nome']} ({r['modelo']})"
                self.modelos_map[disp] = r['id']
                values.append(disp)

            self.combo_modelos.configure(values=values)
            if values:
                # preserve selection if possible
                try:
                    current = self.combo_modelos.get()
                except:
                    current = ""
                if current in values:
                    self.combo_modelos.set(current)
                else:
                    self.combo_modelos.set(values[0])
                self.on_modelo_selected(values[0])
            else:
                self.combo_modelos.set("")
                for w in list(self.scroll_frame_composicao.winfo_children()):
                    w.destroy()
        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha ao carregar modelos para produção: {e}")

    def on_modelo_selected(self, event_or_value):
        """Chamado quando o combo muda; event_or_value pode ser string ou event."""
        try:
            # mostra composição automaticamente
            self.mostrar_composicao_selecionada()
        except:
            pass

    def mostrar_composicao_selecionada(self):
        """Mostra as peças e quantidades necessárias para o mouse selecionado (na aba Produção)."""
        display = self.combo_modelos.get()
        if not display:
            messagebox.showinfo("Produção", "Nenhum modelo selecionado.")
            return

        mouse_id = self.modelos_map.get(display)
        if not mouse_id:
            messagebox.showerror("Erro", "Não foi possível identificar o modelo selecionado.")
            return

        # limpa frame
        for w in list(self.scroll_frame_composicao.winfo_children()):
            w.destroy()

        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT mp.quantidade_necessaria, p.id AS peca_id, p.nome AS peca_nome, p.quantidade AS estoque
            FROM mouse_pecas mp
            JOIN pecas p ON mp.id_peca = p.id
            WHERE mp.id_mouse = %s
            ORDER BY p.id
        """, (mouse_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(self.scroll_frame_composicao, text="Nenhuma composição definida para esse modelo.\nAdicione relações na aba 'Composição de Mouses'.", anchor="w").grid(row=1, column=0, pady=10, padx=8, sticky="w")
            return

        # Cabeçalho simples
        header = ctk.CTkFrame(self.scroll_frame_composicao, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 6))
        header.columnconfigure(0, weight=4)
        header.columnconfigure(1, weight=2)
        header.columnconfigure(2, weight=2)
        ctk.CTkLabel(header, text="Peça", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Necessária (unid/un.)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(header, text="Estoque Atual", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w")

        row = 1
        for r in rows:
            frame = ctk.CTkFrame(self.scroll_frame_composicao, fg_color=("gray90", "gray20"))
            frame.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
            frame.columnconfigure(0, weight=4)
            frame.columnconfigure(1, weight=2)
            frame.columnconfigure(2, weight=2)

            ctk.CTkLabel(frame, text=f"{r['peca_nome']}").grid(row=0, column=0, sticky="w", padx=8)
            ctk.CTkLabel(frame, text=str(r['quantidade_necessaria'])).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(frame, text=str(r['estoque'])).grid(row=0, column=2, sticky="w")

            row += 1

    def fabricar_mouses(self):
        """Verifica se há peças suficientes e, em transação, deduz peças e adiciona mouses ao estoque."""
        display = self.combo_modelos.get()
        if not display:
            messagebox.showerror("Erro", "Selecione um modelo de mouse para fabricar.")
            return
        mouse_id = self.modelos_map.get(display)
        if not mouse_id:
            messagebox.showerror("Erro", "Modelo inválido.")
            return

        qtd_text = self.entry_qtd_producao.get().strip()
        try:
            qtd = int(qtd_text)
            if qtd <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Erro de Entrada", "Informe uma quantidade válida (inteiro > 0).")
            return

        conn = get_db_conn()
        try:
            cursor = conn.cursor(dictionary=True)
            # Busca composição
            cursor.execute("""
                SELECT mp.quantidade_necessaria, p.id AS peca_id, p.nome AS peca_nome, p.quantidade AS estoque
                FROM mouse_pecas mp
                JOIN pecas p ON mp.id_peca = p.id
                WHERE mp.id_mouse = %s
            """, (mouse_id,))
            comps = cursor.fetchall()

            if not comps:
                messagebox.showerror("Erro de Produção", "Não há composição definida para esse modelo. Defina na aba 'Composição de Mouses' antes.")
                cursor.close()
                conn.close()
                return

            faltantes = []
            for c in comps:
                necessario_total = c['quantidade_necessaria'] * qtd
                if c['estoque'] < necessario_total:
                    faltantes.append((c['peca_nome'], c['estoque'], necessario_total))

            if faltantes:
                msg = "Estoque insuficiente para fabricar.\nPeças faltantes:\n"
                for nome, estoque, req in faltantes:
                    msg += f"- {nome}: estoque {estoque}, necessário {req}\n"
                messagebox.showwarning("Sem Estoque Suficiente", msg)
                cursor.close()
                conn.close()
                return

            # Se chegou aqui, há peças suficientes — executa em transação
            try:
                update_cursor = conn.cursor()
                for c in comps:
                    quantidade_necessaria = c['quantidade_necessaria'] * qtd
                    update_cursor.execute("UPDATE pecas SET quantidade = quantidade - %s WHERE id = %s", (quantidade_necessaria, c['peca_id']))

                update_cursor.execute("UPDATE mouses SET quantidade = quantidade + %s WHERE id = %s", (qtd, mouse_id))

                conn.commit()
                update_cursor.close()

                # Atualiza UI
                self.mostrar_estoque(tipo="pecas")
                self.mostrar_estoque(tipo="mouses")
                self.mostrar_composicao_selecionada()
                self.label_status_producao.configure(text=f"Produção concluída: {qtd} unidade(s) fabricada(s). Sucesso ✅")
                messagebox.showinfo("Produção Concluída", f"Foram fabricadas {qtd} unidade(s) do modelo selecionado. Estoques atualizados.")
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Erro na Produção", f"Ocorreu um erro ao atualizar o estoque: {e}")
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            messagebox.showerror("Erro DB", f"Erro ao verificar composição/estoque: {e}")
            try:
                conn.close()
            except:
                pass

    #  Funções da aba Composição 

    def carregar_modelos_para_composicao(self):
        """Carrega mouses do DB e popula o combo de composição (texto: 'id - nome (modelo)')"""
        try:
            conn = get_db_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nome, modelo FROM mouses ORDER BY id")
            rows = cursor.fetchall()
            conn.close()

            self.modelos_comp_map = {}
            values = []
            for r in rows:
                disp = f"{r['id']} - {r['nome']} ({r['modelo']})"
                self.modelos_comp_map[disp] = r['id']
                values.append(disp)

            self.combo_modelos_comp.configure(values=values)
            if values:
                try:
                    current = self.combo_modelos_comp.get()
                except:
                    current = ""
                if current in values:
                    self.combo_modelos_comp.set(current)
                else:
                    self.combo_modelos_comp.set(values[0])
                self.on_modelo_comp_selected(values[0])
            else:
                self.combo_modelos_comp.set("")
                for w in list(self.scroll_frame_assoc.winfo_children()):
                    w.destroy()
        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha ao carregar modelos para composição: {e}")

    def carregar_pecas_para_composicao(self):
        """Carrega peças do DB e popula o combo de peças na aba Composição."""
        try:
            conn = get_db_conn()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nome, modelo FROM pecas ORDER BY id")
            rows = cursor.fetchall()
            conn.close()

            self.pecas_comp_map = {}
            values = []
            for r in rows:
                disp = f"{r['id']} - {r['nome']} ({r['modelo']})"
                self.pecas_comp_map[disp] = r['id']
                values.append(disp)

            self.combo_pecas_comp.configure(values=values)
            if values:
                try:
                    current = self.combo_pecas_comp.get()
                except:
                    current = ""
                if current in values:
                    self.combo_pecas_comp.set(current)
                else:
                    self.combo_pecas_comp.set(values[0])
            else:
                self.combo_pecas_comp.set("")
        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha ao carregar peças para composição: {e}")

    def on_modelo_comp_selected(self, event_or_value):
        """Ao selecionar um modelo na aba Composição, atualiza lista de associações."""
        try:
            self.mostrar_associacoes_do_modelo()
        except:
            pass

    def mostrar_associacoes_do_modelo(self):
        """Lista as peças (com seus ids de associação) associadas ao modelo selecionado (Composição)."""
        display = self.combo_modelos_comp.get()
        if not display:
            messagebox.showinfo("Composição", "Nenhum modelo selecionado.")
            return

        mouse_id = self.modelos_comp_map.get(display)
        if not mouse_id:
            messagebox.showerror("Erro", "Não foi possível identificar o modelo selecionado.")
            return

        # limpa frame
        for w in list(self.scroll_frame_assoc.winfo_children()):
            w.destroy()

        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT mp.id AS assoc_id, p.nome AS peca_nome, mp.quantidade_necessaria, p.quantidade AS estoque, p.id AS peca_id
            FROM mouse_pecas mp
            JOIN pecas p ON mp.id_peca = p.id
            WHERE mp.id_mouse = %s
            ORDER BY mp.id
        """, (mouse_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(self.scroll_frame_assoc, text="Nenhuma peça associada a este modelo.", anchor="w").grid(row=1, column=0, pady=10, padx=8, sticky="w")
            self.selected_assoc_id = None
            return

        header = ctk.CTkFrame(self.scroll_frame_assoc, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 6))
        header.columnconfigure(0, weight=4)
        header.columnconfigure(1, weight=2)
        header.columnconfigure(2, weight=2)
        header.columnconfigure(3, weight=1)
        ctk.CTkLabel(header, text="Peça", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Necessária", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(header, text="Estoque Atual", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(header, text="Remover", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, sticky="w")

        row = 1
        for r in rows:
            frame = ctk.CTkFrame(self.scroll_frame_assoc, fg_color=("gray90", "gray20"))
            frame.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
            frame.columnconfigure(0, weight=4)
            frame.columnconfigure(1, weight=2)
            frame.columnconfigure(2, weight=2)
            frame.columnconfigure(3, weight=1)

            ctk.CTkLabel(frame, text=f"{r['peca_nome']}").grid(row=0, column=0, sticky="w", padx=8)
            ctk.CTkLabel(frame, text=str(r['quantidade_necessaria'])).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(frame, text=str(r['estoque'])).grid(row=0, column=2, sticky="w")
            # botão remover para essa associação específica
            btn = ctk.CTkButton(frame, text="Remover", width=80, command=lambda assoc_id=r['assoc_id']: self.remover_relacao_por_id(assoc_id))
            btn.grid(row=0, column=3, sticky="e", padx=6)

            row += 1

    def adicionar_peca_ao_mouse(self):
        """Adiciona uma linha em mouse_pecas ligando o mouse selecionado à peça escolhida."""
        display_mouse = self.combo_modelos_comp.get()
        display_peca = self.combo_pecas_comp.get()
        if not display_mouse or not display_peca:
            messagebox.showerror("Erro", "Selecione modelo e peça.")
            return
        try:
            qtd = int(self.entry_qtd_peca.get())
            if qtd <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Erro de Entrada", "Informe uma quantidade válida (inteiro > 0).")
            return

        mouse_id = self.modelos_comp_map.get(display_mouse)
        peca_id = self.pecas_comp_map.get(display_peca)
        if not mouse_id or not peca_id:
            messagebox.showerror("Erro", "Modelo ou peça inválidos.")
            return

        # Inserir, evitando duplicata (se já existir, atualiza quantidade)
        conn = get_db_conn()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, quantidade_necessaria FROM mouse_pecas WHERE id_mouse = %s AND id_peca = %s", (mouse_id, peca_id))
            existing = cursor.fetchone()
            if existing:
                # Atualiza somando (pode ser substituído se preferir)
                nova_qtd = int(existing['quantidade_necessaria']) + qtd
                upd = conn.cursor()
                upd.execute("UPDATE mouse_pecas SET quantidade_necessaria = %s WHERE id = %s", (nova_qtd, existing['id']))
                conn.commit()
                upd.close()
            else:
                ins = conn.cursor()
                ins.execute("INSERT INTO mouse_pecas (id_mouse, id_peca, quantidade_necessaria) VALUES (%s, %s, %s)", (mouse_id, peca_id, qtd))
                conn.commit()
                ins.close()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Peça associada ao modelo com sucesso.")
            # limpa campo e atualiza lista
            self.entry_qtd_peca.delete(0, 'end')
            # atualiza a lista de associações e a aba de produção
            self.mostrar_associacoes_do_modelo()
            self.mostrar_composicao_selecionada()
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            messagebox.showerror("Erro DB", f"Falha ao associar peça: {e}")

    def remover_relacao_por_id(self, assoc_id):
        """Remove uma associação específica por seu id (mouse_pecas.id)."""
        if not messagebox.askyesno("Confirmar", "Remover essa relação?"):
            return
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mouse_pecas WHERE id = %s", (assoc_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Removido", "Relação removida com sucesso.")
            self.mostrar_associacoes_do_modelo()
            self.mostrar_composicao_selecionada()
        except Exception as e:
            messagebox.showerror("Erro DB", f"Falha ao remover relação: {e}")

    def remover_relacao_selecionada(self):
        """Remover relação selecionada (se tivermos implementado seleção)."""
        # A interface atual usa botão 'Remover' por linha, então aqui apenas informa o usuário.
        messagebox.showinfo("Remover Relação", "Use o botão 'Remover' ao lado da associação que deseja excluir.")

    # Eventos de janela / encerramento 

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza que deseja fechar o Painel e encerrar o programa?"):
            self.master.destroy()
            sys.exit()


# CLASSE PRINCIPAL DE LOGIN


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login Administrativo")
        self.geometry("600x600")
        self.resizable(True, True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.bind("<Configure>", self.on_resize)

        self.login_frame = ctk.CTkFrame(self, corner_radius=15)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.login_frame.columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.login_frame, text="Acesso de Administrador",
                                        font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(40, 20))

        self.username_entry = ctk.CTkEntry(self.login_frame, width=280, placeholder_text="Usuário", height=40)
        self.username_entry.pack(pady=15)

        self.password_entry = ctk.CTkEntry(self.login_frame, width=280, placeholder_text="Senha", show="*", height=40)
        self.password_entry.pack(pady=15)

        self.login_button = ctk.CTkButton(self.login_frame, text="Fazer Login", command=self.verificar_login,
                                          width=280, height=45, font=ctk.CTkFont(size=16, weight="bold"))
        self.login_button.pack(pady=(20, 40))

        self.bind('<Return>', lambda event: self.verificar_login())

        self.update_idletasks()
        self.on_resize(None)

    def on_resize(self, event):
        try:
            new_width = self.winfo_width() * 0.50
            max_width = 450
            min_width = 350
            final_width = max(min_width, min(max_width, new_width))

            internal_width = final_width - 70
            self.username_entry.configure(width=internal_width)
            self.password_entry.configure(width=internal_width)
            self.login_button.configure(width=internal_width)
        except:
            pass

    def verificar_login(self):
        usuario = self.username_entry.get()
        senha = self.password_entry.get()

        if usuario == ADMIN_USER and senha == ADMIN_PASS:
            self.withdraw()
            AdminDashboard(self)
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos.")
            self.password_entry.delete(0, 'end')
            self.username_entry.focus()


# INICIALIZAÇÃO DA APLICAÇÃO


if __name__ == "__main__":
    setup_database()
    app = LoginApp()
    app.mainloop()
