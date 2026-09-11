
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "barbearia.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            disponivel INTEGER NOT NULL DEFAULT 1,
            UNIQUE(data, hora)
        );

        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horario_id INTEGER NOT NULL,
            nome_cliente TEXT NOT NULL,
            telefone TEXT,
            criado_em TEXT NOT NULL,
            FOREIGN KEY (horario_id) REFERENCES horarios(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT,
            ordem INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS planos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT,
            beneficios TEXT,
            ordem INTEGER DEFAULT 0
        );
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM servicos")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO servicos (nome, preco, descricao, ordem) VALUES (?, ?, ?, ?)",
            [
                ("Corte clássico", 45.00, "Tesoura e máquina, acabamento na navalha.", 1),
                ("Corte + Barba", 70.00, "Corte completo com barba desenhada.", 2),
                ("Barba", 35.00, "Toalha quente, navalha e acabamento.", 3),
            ],
        )

    cur.execute("SELECT COUNT(*) FROM planos")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO planos (nome, preco, descricao, beneficios, ordem) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    "Plano Essencial",
                    99.00,
                    "Para quem gosta de manter o corte sempre em dia.",
                    "2 cortes por mês\nDesconto em produtos\nPrioridade na agenda",
                    1,
                ),
                (
                    "Plano Completo",
                    159.00,
                    "Cuidado completo, sem se preocupar com a agenda.",
                    "4 cortes por mês\n1 barba por mês\nDesconto em produtos\nPrioridade na agenda",
                    2,
                ),
            ],
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# HORÁRIOS
# ---------------------------------------------------------------------------

def listar_horarios_disponiveis():
    conn = get_conn()
    hoje = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM horarios WHERE disponivel = 1 AND data >= ? ORDER BY data, hora",
        (hoje,),
    ).fetchall()
    conn.close()
    return rows


def listar_horarios_todos():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT h.*, a.id AS agendamento_id, a.nome_cliente, a.telefone
        FROM horarios h
        LEFT JOIN agendamentos a ON a.horario_id = h.id
        ORDER BY h.data, h.hora
        """
    ).fetchall()
    conn.close()
    return rows


def criar_horario(data, hora):
    conn = get_conn()
    ok = True
    try:
        conn.execute(
            "INSERT INTO horarios (data, hora, disponivel) VALUES (?, ?, 1)",
            (data, hora),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok


def obter_horario(horario_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM horarios WHERE id = ?", (horario_id,)).fetchone()
    conn.close()
    return row


def excluir_horario(horario_id):
    conn = get_conn()
    conn.execute("DELETE FROM horarios WHERE id = ?", (horario_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# AGENDAMENTOS
# ---------------------------------------------------------------------------

def criar_agendamento(horario_id, nome_cliente, telefone):
    conn = get_conn()
    horario = conn.execute(
        "SELECT * FROM horarios WHERE id = ?", (horario_id,)
    ).fetchone()
    if not horario or horario["disponivel"] == 0:
        conn.close()
        return False

    conn.execute(
        "INSERT INTO agendamentos (horario_id, nome_cliente, telefone, criado_em) "
        "VALUES (?, ?, ?, ?)",
        (horario_id, nome_cliente, telefone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.execute("UPDATE horarios SET disponivel = 0 WHERE id = ?", (horario_id,))
    conn.commit()
    conn.close()
    return True


def listar_agendamentos():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT a.*, h.data, h.hora
        FROM agendamentos a
        JOIN horarios h ON h.id = a.horario_id
        ORDER BY h.data, h.hora
        """
    ).fetchall()
    conn.close()
    return rows


def excluir_agendamento(agendamento_id):
    conn = get_conn()
    ag = conn.execute(
        "SELECT * FROM agendamentos WHERE id = ?", (agendamento_id,)
    ).fetchone()
    if ag:
        conn.execute(
            "UPDATE horarios SET disponivel = 1 WHERE id = ?", (ag["horario_id"],)
        )
        conn.execute("DELETE FROM agendamentos WHERE id = ?", (agendamento_id,))
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# SERVIÇOS (valores dos cortes)
# ---------------------------------------------------------------------------

def listar_servicos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM servicos ORDER BY ordem, id").fetchall()
    conn.close()
    return rows


def obter_servico(servico_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM servicos WHERE id = ?", (servico_id,)).fetchone()
    conn.close()
    return row


def criar_servico(nome, preco, descricao):
    conn = get_conn()
    conn.execute(
        "INSERT INTO servicos (nome, preco, descricao) VALUES (?, ?, ?)",
        (nome, preco, descricao),
    )
    conn.commit()
    conn.close()


def atualizar_servico(servico_id, nome, preco, descricao):
    conn = get_conn()
    conn.execute(
        "UPDATE servicos SET nome = ?, preco = ?, descricao = ? WHERE id = ?",
        (nome, preco, descricao, servico_id),
    )
    conn.commit()
    conn.close()


def excluir_servico(servico_id):
    conn = get_conn()
    conn.execute("DELETE FROM servicos WHERE id = ?", (servico_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# PLANOS MENSAIS
# ---------------------------------------------------------------------------

def listar_planos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM planos ORDER BY ordem, id").fetchall()
    conn.close()
    return rows


def obter_plano(plano_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM planos WHERE id = ?", (plano_id,)).fetchone()
    conn.close()
    return row


def criar_plano(nome, preco, descricao, beneficios):
    conn = get_conn()
    conn.execute(
        "INSERT INTO planos (nome, preco, descricao, beneficios) VALUES (?, ?, ?, ?)",
        (nome, preco, descricao, beneficios),
    )
    conn.commit()
    conn.close()


def atualizar_plano(plano_id, nome, preco, descricao, beneficios):
    conn = get_conn()
    conn.execute(
        "UPDATE planos SET nome = ?, preco = ?, descricao = ?, beneficios = ? WHERE id = ?",
        (nome, preco, descricao, beneficios, plano_id),
    )
    conn.commit()
    conn.close()


def excluir_plano(plano_id):
    conn = get_conn()
    conn.execute("DELETE FROM planos WHERE id = ?", (plano_id,))
    conn.commit()
    conn.close()
