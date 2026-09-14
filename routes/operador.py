from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
from database import get_db_connection

operador_bp = Blueprint('operador', __name__)

@operador_bp.route('/')
def index():
    # Tela Inicial / Dashboard do Operador.
    conn = get_db_connection()
    ferramentas = conn.execute('SELECT * FROM ferramentas ORDER BY CAST(SUBSTR(posicao, 2) AS INTEGER)').fetchall()
    produtos = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', ferramentas=ferramentas, produtos=produtos)

@operador_bp.route('/apontar')
def tela_apontar():
    # Exibe a tela dedicada para o operador registrar a produção.
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos ORDER BY nome ASC').fetchall()
    conn.close()
    return render_template('apontar.html', produtos=produtos)

@operador_bp.route('/apontar_producao', methods=['POST'])
def apontar_producao():
    produto_id = request.form.get('produto_id')
    ordem_producao = request.form.get('ordem_producao')
    status_producao = request.form.get('status_producao', 'Produção Normal')
    data_apontamento = request.form.get('data')

    try:
        quantidade = int(request.form.get('quantidade', 0))
    except ValueError:
        quantidade = 0

    if not produto_id or quantidade <= 0 or not data_apontamento:
        flash('Preencha todos os campos corretamente.', 'erro')
        return redirect(url_for('operador.tela_apontar'))

    conn = get_db_connection()
    
    # CHECK 1: O produto existe no banco de dados?
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    if not produto:
        conn.close()
        flash('Erro: O produto informado não existe no sistema.', 'erro')
        return redirect(url_for('operador.tela_apontar'))

    produto_nome = f"{produto['codigo']} - {produto['nome']}"

    # CHECK 2: O produto possui ferramentas configuradas na receita?
    ferramentas_receita = conn.execute('''
        SELECT posicao FROM produto_ferramentas
        WHERE produto_id = ?
    ''', (produto_id,)).fetchall()

    if not ferramentas_receita:
        conn.close()
        flash(f'Erro: O produto "{produto_nome}" não possui ferramentas cadastradas na sua receita.', 'erro')
        return redirect(url_for('operador.tela_apontar'))

    # Passou nos checks: Executa o apontamento e o motor de desgaste
    try:
        conn.execute('''
            INSERT INTO historico_apontamentos (produto_nome, quantidade, ordem_producao, status_producao, data_apontamento)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto_nome, quantidade, ordem_producao, status_producao, data_apontamento))

        for item in ferramentas_receita:
            pos = item['posicao']
            ferr_atual = conn.execute('SELECT pecas_produzidas FROM ferramentas WHERE posicao = ?', (pos,)).fetchone()
            if ferr_atual:
                novo_total = ferr_atual['pecas_produzidas'] + quantidade
                conn.execute('''
                    UPDATE ferramentas 
                    SET pecas_produzidas = ?
                    WHERE posicao = ?
                ''', (novo_total, pos))

        conn.commit()
        flash(f'Apontamento de {quantidade} peças registrado para o produto "{produto_nome}"!', 'sucesso')
    except Exception as e:
        conn.rollback()
        flash(f'Erro interno ao salvar apontamento: {str(e)}', 'erro')
    finally:
        conn.close()

    return redirect(url_for('operador.index'))

@operador_bp.route('/trocar_ferramenta/<posicao>', methods=['GET', 'POST'])
def trocar_ferramenta(posicao):
    conn = get_db_connection()
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE posicao = ?', (posicao,)).fetchone()
    
    if not ferramenta:
        conn.close()
        flash('Ferramenta não encontrada.', 'erro')
        return redirect(url_for('operador.index'))

    if request.method == 'POST':
        operador = request.form.get('operador', 'Operador Padrão')
        motivo = request.form.get('motivo', 'Desgaste Normal')
        data_troca = request.form.get('data')

        conn.execute('''
            INSERT INTO historico_trocas (posicao, nome_ferramenta, pecas_produzidas, vida_util_limite, motivo, operador, data_troca)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ferramenta['posicao'], 
            ferramenta['nome'], 
            ferramenta['pecas_produzidas'], 
            ferramenta['vida_util_limite'], 
            motivo, 
            operador, 
            data_troca
        ))

        conn.execute('''
            UPDATE ferramentas 
            SET pecas_produzidas = 0 
            WHERE posicao = ?
        ''', (posicao,))

        conn.commit()
        conn.close()
        flash(f'Ferramenta {posicao} substituída com sucesso ({motivo}). Contador resetado!', 'sucesso')
        return redirect(url_for('operador.index'))

    conn.close()
    return render_template('trocar.html', ferramenta=ferramenta)