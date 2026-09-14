import sqlite3

def get_db_connection():
    conn = sqlite3.connect('banco.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db_connection()
    
    # Tabela principal das ferramentas no magazine (T1 a T20)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ferramentas (
            posicao TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            pecas_produzidas INTEGER DEFAULT 0,
            vida_util_limite INTEGER DEFAULT 1000
        )
    ''')
    
    # Tabela de histórico de trocas para análise gerencial (BI)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_trocas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posicao TEXT,
            nome_ferramenta TEXT,
            pecas_produzidas INTEGER,
            vida_util_limite INTEGER,
            motivo TEXT,
            operador TEXT,
            data_troca TEXT
        )
    ''')

    # Tabela de Produtos cadastrados no painel admin
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL
        )
    ''')

    # Tabela de Vínculo entre Produtos e Ferramentas do Magazine
    conn.execute('''
        CREATE TABLE IF NOT EXISTS produto_ferramentas (
            produto_id INTEGER,
            posicao TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
            FOREIGN KEY(posicao) REFERENCES ferramentas(posicao) ON DELETE CASCADE
        )
    ''')

    # Tabela de histórico de apontamentos de produção (Modelagem Relacional para BI)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_trocas_dummy (id INTEGER)''') # Apenas separador visual, mantendo a estrutura abaixo:
        
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_apontamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            produto_nome TEXT,
            quantidade INTEGER,
            ordem_producao TEXT,
            status_producao TEXT,
            data_apontamento TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id) ON DELETE SET NULL
        )
    ''')
    
    # Popular dados iniciais de T1 a T20 caso a tabela esteja vazia
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ferramentas')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 21):
            pos = f"T{i}"
            nome = f"Ferramenta Padrão T{i}"
            conn.execute('INSERT INTO ferramentas (posicao, nome, pecas_produzidas, vida_util_limite) VALUES (?, ?, 0, 1000)', (pos, nome))
            
    conn.commit()
    conn.close()