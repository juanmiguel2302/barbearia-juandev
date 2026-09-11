


import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

import db

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES GERAIS — edite aqui os dados da sua barbearia
# ---------------------------------------------------------------------------
NOME_BARBEARIA = "Barbearia Juandev"
TELEFONE_CONTATO = "(81) 99638-8838"
ENDERECO = "Rua ipanema"
INSTAGRAM = "@barbeariajuandev"

ADMIN_PASSWORD = os.environ.get("juan", "barbearia123")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

db.init_db()


@app.context_processor
def dados_gerais():
    return {
        "nome_barbearia": NOME_BARBEARIA,
        "telefone_contato": TELEFONE_CONTATO,
        "endereco": ENDERECO,
        "instagram": INSTAGRAM,
        "ano_atual": datetime.now().year,
    }


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


def formatar_data(data_iso):
    """Converte 2026-09-09 em 09/09/2026, mantendo o original se algo vier errado."""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data_iso


app.jinja_env.filters["data_br"] = formatar_data


# ---------------------------------------------------------------------------
# ÁREA DO CLIENTE
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    servicos = db.listar_servicos()
    planos = db.listar_planos()
    horarios = db.listar_horarios_disponiveis()

    horarios_por_data = {}
    for h in horarios:
        horarios_por_data.setdefault(h["data"], []).append(h)

    return render_template(
        "index.html",
        servicos=servicos,
        planos=planos,
        horarios_por_data=horarios_por_data,
    )


@app.route("/agendar", methods=["POST"])
def agendar():
    nome = request.form.get("nome", "").strip()
    telefone = request.form.get("telefone", "").strip()
    horario_id = request.form.get("horario_id")

    if not nome or not horario_id:
        flash("Preencha seu nome e escolha um horário para agendar.", "erro")
        return redirect(url_for("index") + "#agendar")

    horario = db.obter_horario(horario_id)
    ok = db.criar_agendamento(horario_id, nome, telefone)

    if ok and horario:
        flash(
            "Horário reservado, {}! Te esperamos no dia {} às {}.".format(
                nome, formatar_data(horario["data"]), horario["hora"]
            ),
            "sucesso",
        )
    else:
        flash("Esse horário acabou de ser reservado por outra pessoa. Escolha outro, por favor.", "erro")

    return redirect(url_for("index") + "#agendar")


# ---------------------------------------------------------------------------
# LOGIN / LOGOUT DO ADMIN
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Senha incorreta.", "erro")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------------------
# PAINEL ADMINISTRATIVO
# ---------------------------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    horarios = db.listar_horarios_todos()
    agendamentos = db.listar_agendamentos()
    hoje = datetime.now().strftime("%Y-%m-%d")

    total_disponiveis = sum(1 for h in horarios if h["disponivel"] == 1 and h["data"] >= hoje)
    total_reservados = sum(1 for h in horarios if h["disponivel"] == 0)
    proximos = [a for a in agendamentos if a["data"] >= hoje][:6]

    return render_template(
        "admin/dashboard.html",
        total_disponiveis=total_disponiveis,
        total_reservados=total_reservados,
        total_servicos=len(db.listar_servicos()),
        total_planos=len(db.listar_planos()),
        proximos_agendamentos=proximos,
    )


@app.route("/admin/horarios", methods=["GET", "POST"])
@admin_required
def admin_horarios():
    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "adicionar":
            data = request.form.get("data")
            hora = request.form.get("hora")
            if data and hora:
                if db.criar_horario(data, hora):
                    flash("Horário adicionado com sucesso.", "sucesso")
                else:
                    flash("Esse horário já existe na agenda.", "erro")

        elif acao == "gerar":
            data = request.form.get("data")
            hora_inicio = request.form.get("hora_inicio")
            hora_fim = request.form.get("hora_fim")
            try:
                intervalo = int(request.form.get("intervalo", 30))
            except ValueError:
                intervalo = 30

            if data and hora_inicio and hora_fim:
                try:
                    inicio = datetime.strptime(hora_inicio, "%H:%M")
                    fim = datetime.strptime(hora_fim, "%H:%M")
                except ValueError:
                    flash("Horário inicial ou final inválido.", "erro")
                    return redirect(url_for("admin_horarios"))

                criados = 0
                atual = inicio
                while atual < fim:
                    if db.criar_horario(data, atual.strftime("%H:%M")):
                        criados += 1
                    atual += timedelta(minutes=intervalo)
                flash(f"{criados} horário(s) gerado(s) para {formatar_data(data)}.", "sucesso")

        return redirect(url_for("admin_horarios"))

    horarios = db.listar_horarios_todos()
    horarios_por_data = {}
    for h in horarios:
        horarios_por_data.setdefault(h["data"], []).append(h)

    return render_template("admin/horarios.html", horarios_por_data=horarios_por_data)


@app.route("/admin/horarios/excluir/<int:horario_id>", methods=["POST"])
@admin_required
def admin_excluir_horario(horario_id):
    db.excluir_horario(horario_id)
    flash("Horário removido da agenda.", "sucesso")
    return redirect(url_for("admin_horarios"))


@app.route("/admin/servicos", methods=["GET", "POST"])
@admin_required
def admin_servicos():
    if request.method == "POST":
        servico_id = request.form.get("servico_id")
        nome = request.form.get("nome", "").strip()
        preco_texto = request.form.get("preco", "0").replace(",", ".")
        descricao = request.form.get("descricao", "").strip()

        try:
            preco = float(preco_texto)
        except ValueError:
            preco = 0.0

        if nome:
            if servico_id:
                db.atualizar_servico(servico_id, nome, preco, descricao)
                flash("Serviço atualizado.", "sucesso")
            else:
                db.criar_servico(nome, preco, descricao)
                flash("Serviço adicionado ao cardápio.", "sucesso")
        else:
            flash("Dê um nome ao serviço antes de salvar.", "erro")

        return redirect(url_for("admin_servicos"))

    editar_id = request.args.get("editar")
    servico_edicao = db.obter_servico(editar_id) if editar_id else None

    return render_template(
        "admin/servicos.html",
        servicos=db.listar_servicos(),
        servico_edicao=servico_edicao,
    )


@app.route("/admin/servicos/excluir/<int:servico_id>", methods=["POST"])
@admin_required
def admin_excluir_servico(servico_id):
    db.excluir_servico(servico_id)
    flash("Serviço removido.", "sucesso")
    return redirect(url_for("admin_servicos"))


@app.route("/admin/planos", methods=["GET", "POST"])
@admin_required
def admin_planos():
    if request.method == "POST":
        plano_id = request.form.get("plano_id")
        nome = request.form.get("nome", "").strip()
        preco_texto = request.form.get("preco", "0").replace(",", ".")
        descricao = request.form.get("descricao", "").strip()
        beneficios = request.form.get("beneficios", "").strip()

        try:
            preco = float(preco_texto)
        except ValueError:
            preco = 0.0

        if nome:
            if plano_id:
                db.atualizar_plano(plano_id, nome, preco, descricao, beneficios)
                flash("Plano atualizado.", "sucesso")
            else:
                db.criar_plano(nome, preco, descricao, beneficios)
                flash("Plano adicionado.", "sucesso")
        else:
            flash("Dê um nome ao plano antes de salvar.", "erro")

        return redirect(url_for("admin_planos"))

    editar_id = request.args.get("editar")
    plano_edicao = db.obter_plano(editar_id) if editar_id else None

    return render_template(
        "admin/planos.html",
        planos=db.listar_planos(),
        plano_edicao=plano_edicao,
    )


@app.route("/admin/planos/excluir/<int:plano_id>", methods=["POST"])
@admin_required
def admin_excluir_plano(plano_id):
    db.excluir_plano(plano_id)
    flash("Plano removido.", "sucesso")
    return redirect(url_for("admin_planos"))


@app.route("/admin/agendamentos")
@admin_required
def admin_agendamentos():
    return render_template("admin/agendamentos.html", agendamentos=db.listar_agendamentos())


@app.route("/admin/agendamentos/excluir/<int:agendamento_id>", methods=["POST"])
@admin_required
def admin_excluir_agendamento(agendamento_id):
    db.excluir_agendamento(agendamento_id)
    flash("Agendamento cancelado. O horário voltou a ficar disponível.", "sucesso")
    return redirect(url_for("admin_agendamentos"))


if __name__ == "__main__":
    app.run(debug=True)
