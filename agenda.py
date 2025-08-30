import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Nome do arquivo do banco de dados.
NOME_DB = 'agenda.db'

def conectar_bd():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(NOME_DB)
        return conn
    except sqlite3.Error as e:
        messagebox.showerror("Erro de Conexão", f"Erro ao conectar ao banco de dados: {e}")
        return None

def inicializar_bd():
    """Cria a tabela de tarefas se ela ainda não existir."""
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                data_inicial TEXT NOT NULL,
                data_final TEXT,
                tipo_de_tarefa TEXT,
                situacao TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

def cadastrar_tarefa(nome, descricao, data_inicial, data_final, tipo_de_tarefa):
    """Insere uma nova tarefa no banco de dados."""
    situacao = "Não feito"
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO tarefas (nome, descricao, data_inicial, data_final, tipo_de_tarefa, situacao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nome, descricao, data_inicial, data_final, tipo_de_tarefa, situacao))
            conn.commit()
            messagebox.showinfo("Sucesso", "Tarefa cadastrada com sucesso!")
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Cadastro", f"Erro ao cadastrar a tarefa: {e}")
        finally:
            conn.close()

def ver_todas_as_tarefas():
    """Busca e retorna todas as tarefas do banco de dados."""
    conn = conectar_bd()
    tarefas = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tarefas ORDER BY data_inicial")
        tarefas = cursor.fetchall()
        conn.close()
    return tarefas

def buscar_tarefas_por_texto(texto_busca):
    """Busca tarefas que contenham o texto_busca no nome ou na descrição."""
    conn = conectar_bd()
    tarefas = []
    if conn:
        cursor = conn.cursor()
        termo_busca = f"%{texto_busca}%"
        try:
            cursor.execute("""
                SELECT * FROM tarefas 
                WHERE nome LIKE ? OR descricao LIKE ?
                ORDER BY data_inicial
            """, (termo_busca, termo_busca))
            tarefas = cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Busca", f"Erro ao buscar tarefas: {e}")
        finally:
            conn.close()
    return tarefas

def remover_tarefa(tarefa_id):
    """Remove uma tarefa do banco de dados pelo ID."""
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Tarefa removida com sucesso!")

def apagar_tarefas_nao_feitas():
    """Remove todas as tarefas com a situação 'Não feito'."""
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE situacao = 'Não feito'")
        conn.commit()
        messagebox.showinfo("Limpeza", "Todas as tarefas não feitas foram removidas.")
        conn.close()

def marcar_como_feita(tarefa_id):
    """Atualiza a situação de uma tarefa para 'Feito'."""
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tarefas SET situacao = 'Feito' WHERE id = ?", (tarefa_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Atualização", "Tarefa marcada como Feita!")

# --- Classe da Interface Gráfica ---

class AgendaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Agenda de Tarefas")
        self.geometry("650x550")

        inicializar_bd()
        self.criar_widgets()
        self.carregar_tarefas()

    def criar_widgets(self):
        # Frame para os campos de entrada
        frame_input = ttk.LabelFrame(self, text="Cadastrar Tarefa", padding=(10, 5))
        frame_input.pack(fill="x", padx=10, pady=10)

        # Labels e campos de entrada
        ttk.Label(frame_input, text="Nome:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.nome_entry = ttk.Entry(frame_input)
        self.nome_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_input, text="Descrição:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.descricao_entry = ttk.Entry(frame_input)
        self.descricao_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(frame_input, text="Data Início (DD-MM-AAAA):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.data_inicial_entry = ttk.Entry(frame_input)
        self.data_inicial_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_input, text="Data Fim (DD-MM-AAAA):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.data_final_entry = ttk.Entry(frame_input)
        self.data_final_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame_input, text="Tipo:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.tipo_entry = ttk.Entry(frame_input)
        self.tipo_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        ttk.Button(frame_input, text="Cadastrar", command=self.adicionar_tarefa).grid(row=5, column=0, columnspan=2, pady=10)

        # Frame para a busca
        frame_busca = ttk.LabelFrame(self, text="Buscar Tarefas", padding=(10, 5))
        frame_busca.pack(fill="x", padx=10, pady=5)

        self.busca_entry = ttk.Entry(frame_busca)
        self.busca_entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
        self.busca_entry.bind('<Return>', lambda event: self.buscar_tarefas_na_interface())

        ttk.Button(frame_busca, text="Buscar", command=self.buscar_tarefas_na_interface).pack(side="left", padx=5)
        ttk.Button(frame_busca, text="Limpar Busca", command=self.carregar_tarefas).pack(side="right", padx=5)


        # Frame para a lista de tarefas
        frame_lista = ttk.LabelFrame(self, text="Tarefas Cadastradas", padding=(10, 5))
        frame_lista.pack(fill="both", expand=True, padx=10, pady=10)

        # Lista de tarefas
        self.tarefas_listbox = tk.Listbox(frame_lista, height=10)
        self.tarefas_listbox.pack(fill="both", expand=True)
        
        # Frame para os botões de ação
        frame_botoes = ttk.Frame(self, padding=(10, 5))
        frame_botoes.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_botoes, text="Marcar como Feita", command=self.marcar_feita).pack(side="left", expand=True, padx=5)
        ttk.Button(frame_botoes, text="Remover Selecionada", command=self.remover_tarefa).pack(side="left", expand=True, padx=5)
        ttk.Button(frame_botoes, text="Limpar Não Feitas", command=self.limpar_tarefas).pack(side="right", expand=True, padx=5)

    def adicionar_tarefa(self):
        nome = self.nome_entry.get()
        descricao = self.descricao_entry.get()
        data_inicial = self.data_inicial_entry.get()
        data_final = self.data_final_entry.get()
        tipo = self.tipo_entry.get()

        if not nome or not data_inicial:
            messagebox.showerror("Erro de Validação", "Nome e Data Inicial são obrigatórios.")
            return

        try:
            datetime.datetime.strptime(data_inicial, '%d-%m-%Y')
            if data_final:
                datetime.datetime.strptime(data_final, '%d-%m-%Y')
        except ValueError:
            messagebox.showerror("Erro de Validação", "Formato de data inválido. Use DD-MM-AAAA.")
            return

        cadastrar_tarefa(nome, descricao, data_inicial, data_final, tipo)
        self.limpar_campos()
        self.carregar_tarefas()

    def carregar_tarefas(self):
        """Carrega e exibe as tarefas na lista."""
        self.tarefas_listbox.delete(0, tk.END)
        tarefas = ver_todas_as_tarefas()
        for tarefa in tarefas:
            self.tarefas_listbox.insert(tk.END, f"ID: {tarefa[0]} | Nome: {tarefa[1]} | Data: {tarefa[3]} | Situação: {tarefa[6]}")

    def buscar_tarefas_na_interface(self):
        """Busca tarefas na interface com base no texto inserido."""
        texto_busca = self.busca_entry.get().strip()
        if not texto_busca:
            self.carregar_tarefas()
            return

        self.tarefas_listbox.delete(0, tk.END)
        tarefas = buscar_tarefas_por_texto(texto_busca)
        if tarefas:
            for tarefa in tarefas:
                self.tarefas_listbox.insert(tk.END, f"ID: {tarefa[0]} | Nome: {tarefa[1]} | Data: {tarefa[3]} | Situação: {tarefa[6]}")
        else:
            self.tarefas_listbox.insert(tk.END, "Nenhuma tarefa encontrada com este termo.")


    def remover_tarefa(self):
        try:
            item_selecionado = self.tarefas_listbox.curselection()
            if item_selecionado:
                linha_tarefa = self.tarefas_listbox.get(item_selecionado[0])
                tarefa_id = int(linha_tarefa.split(" |")[0].split(":")[1].strip())
                
                remover_tarefa(tarefa_id)
                self.carregar_tarefas()
            else:
                messagebox.showwarning("Atenção", "Selecione uma tarefa para remover.")
        except Exception:
            messagebox.showerror("Erro", "Não foi possível remover a tarefa selecionada.")

    def marcar_feita(self):
        try:
            item_selecionado = self.tarefas_listbox.curselection()
            if item_selecionado:
                linha_tarefa = self.tarefas_listbox.get(item_selecionado[0])
                tarefa_id = int(linha_tarefa.split(" |")[0].split(":")[1].strip())
                
                marcar_como_feita(tarefa_id)
                self.carregar_tarefas()
            else:
                messagebox.showwarning("Atenção", "Selecione uma tarefa para marcar como feita.")
        except Exception:
            messagebox.showerror("Erro", "Não foi possível marcar a tarefa como feita.")

    def limpar_tarefas(self):
        apagar_tarefas_nao_feitas()
        self.carregar_tarefas()

    def limpar_campos(self):
        self.nome_entry.delete(0, tk.END)
        self.descricao_entry.delete(0, tk.END)
        self.data_inicial_entry.delete(0, tk.END)
        self.data_final_entry.delete(0, tk.END)
        self.tipo_entry.delete(0, tk.END)

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = AgendaApp()
    app.mainloop()