import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from database import get_db_connection

# Criação do Blueprint para o Admin
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario == 'admin' and senha == '0001':
            session['admin'] = True
            return redirect(url_for('admin.index'))
        else:
            flash('Usuário ou senha incorretos.', 'erro')
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin')
def index():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    ferramentas = conn.execute('SELECT * FROM ferramentas ORDER BY CAST(SUBSTR(posicao, 2) AS INTEGER)').fetchall()
    historico = conn.execute('SELECT * FROM historico_trocas ORDER BY id DESC').fetchall()
    apontamentos = conn.execute('SELECT * FROM historico_apontamentos ORDER BY id DESC').fetchall()
    
    produtos_raw = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
    produtos = []
    for p in produtos_raw:
        ferrs = conn.execute('SELECT posicao FROM produto_ferramentas WHERE produto_id = ? ORDER BY CAST(SUBSTR(posicao, 2) AS INTEGER)', (p['id'],)).fetchall()
        produtos.append({
            'id': p['id'],
            'codigo': p['codigo'],
            'nome': p['nome'],
            'ferramentas': [f['posicao'] for f in ferrs]
        })
        
    conn.close()
    return render_template('admin.html', ferramentas=ferramentas, historico=historico, apontamentos=apontamentos, produtos=produtos)

@admin_bp.route('/cadastrar_ferramenta', methods=['POST'])
def cadastrar_ferramenta():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    posicao = request.form.get('posicao', '').strip().upper()
    nome = request.form.get('nome')
    
    # Validação rigorosa: Apenas T1 até T20 (rejeita T0, D9, A2, etc.)
    match = re.match(r'^T([1-9]|1[0-9]|20)$', posicao)
    if not match:
        flash('Posição inválida! O magazine CNC aceita estritamente apenas posições de T1 até T20.', 'erro')
        return redirect(url_for('admin.index'))

    try:
        vida_util = int(request.form.get('vida_util', 1000))
    except ValueError:
        vida_util = 1000
        
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO ferramentas (posicao, nome, vida_util_limite, pecas_produzidas) 
            VALUES (?, ?, ?, 0) 
            ON CONFLICT(posicao) DO UPDATE SET nome = ?, vida_util_limite = ?
        ''', (posicao, nome, vida_util, nome, vida_util))
        conn.commit()
        flash(f'Ferramenta {posicao} configurada com sucesso!', 'sucesso')
    except Exception as e:
        flash(f'Erro ao cadastrar ferramenta: {e}', 'erro')
    conn.close()
    return redirect(url_for('admin.index'))

@admin_bp.route('/editar_ferramenta/<posicao>', methods=['GET', 'POST'])
def editar_ferramenta(posicao):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    if request.method == 'POST':
        novo_nome = request.form.get('nome')
        try:
            vida_util = int(request.form.get('vida_util_limite', 1000))
        except ValueError:
            vida_util = 1000
        
        try:
            conn.execute('''
                UPDATE ferramentas 
                SET nome = ?, vida_util_limite = ? 
                WHERE posicao = ?
            ''', (novo_nome, vida_util, posicao))
            conn.commit()
            flash(f'Ferramenta da posição {posicao} atualizada com sucesso!', 'sucesso')
        except Exception as e:
            flash(f'Erro ao atualizar ferramenta: {e}', 'erro')
        finally:
            conn.close()
        return redirect(url_for('admin.index'))
        
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE posicao = ?', (posicao,)).fetchone()
    conn.close()
    
    if not ferramenta:
        flash('Ferramenta não encontrada.', 'erro')
        return redirect(url_for('admin.index'))
        
    return render_template('editar_ferramenta.html', ferramenta=ferramenta)

@admin_bp.route('/excluir_ferramenta/<posicao>', methods=['POST'])
def excluir_ferramenta(posicao):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM ferramentas WHERE posicao = ?', (posicao,))
        conn.commit()
        flash(f'Ferramenta da posição {posicao} removida com sucesso!', 'sucesso')
    except Exception as e:
        flash(f'Erro ao excluir ferramenta: {e}', 'erro')
    finally:
        conn.close()
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/cadastrar_produto', methods=['POST'])
def cadastrar_produto():
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    codigo = request.form.get('codigo')
    nome = request.form.get('nome')
    ferramentas_usadas = request.form.getlist('ferramentas_usadas')
    
    if codigo and nome and ferramentas_usadas:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO produtos (codigo, nome) VALUES (?, ?)', (codigo, nome))
            produto_id = cursor.lastrowid
            
            for pos in ferramentas_usadas:
                conn.execute('INSERT INTO produto_ferramentas (produto_id, posicao) VALUES (?, ?)', (produto_id, pos))
                
            conn.commit()
            flash(f'Produto "{nome}" cadastrado com sucesso!', 'sucesso')
        except sqlite3.IntegrityError:
            flash('Já existe um produto cadastrado com esse código.', 'erro')
        except Exception as e:
            flash(f'Erro ao cadastrar produto: {e}', 'erro')
        conn.close()
    else:
        flash('Preencha todos os campos e selecione ao menos uma ferramenta.', 'erro')
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        ferramentas_usadas = request.form.getlist('ferramentas_usadas')
        
        try:
            conn.execute('''
                UPDATE produtos 
                SET codigo = ?, nome = ? 
                WHERE id = ?
            ''', (codigo, nome, id))
            
            conn.execute('DELETE FROM produto_ferramentas WHERE produto_id = ?', (id,))
            for pos in ferramentas_usadas:
                conn.execute('INSERT INTO produto_ferramentas (produto_id, posicao) VALUES (?, ?)', (id, pos))
                
            conn.commit()
            flash(f'Produto "{nome}" atualizado com sucesso!', 'sucesso')
        except sqlite3.IntegrityError:
            flash('Já existe outro produto cadastrado com esse código.', 'erro')
        except Exception as e:
            flash(f'Erro ao atualizar produto: {e}', 'erro')
        finally:
            conn.close()
        return redirect(url_for('admin.index'))
        
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    if not produto:
        conn.close()
        flash('Produto não encontrado.', 'erro')
        return redirect(url_for('admin.index'))
        
    ferrs = conn.execute('SELECT posicao FROM produto_ferramentas WHERE produto_id = ?', (id,)).fetchall()
    ferramentas_selecionadas = [f['posicao'] for f in ferrs]
    ferramentas = conn.execute('SELECT * FROM ferramentas ORDER BY CAST(SUBSTR(posicao, 2) AS INTEGER)').fetchall()
    conn.close()
    
    return render_template('editar_produto.html', produto=produto, ferramentas_selecionadas=ferramentas_selecionadas, ferramentas=ferramentas)

@admin_bp.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM produto_ferramentas WHERE produto_id = ?', (id,))
        conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
        flash('Produto excluído com sucesso!', 'sucesso')
    except Exception as e:
        flash(f'Erro ao excluir produto: {e}', 'erro')
    finally:
        conn.close()
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/editar_troca/<int:id>', methods=['GET', 'POST'])
def editar_troca(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    if request.method == 'POST':
        try:
            motivo = request.form.get('motivo')
            operador = request.form.get('operador')
            data_troca = request.form.get('data')
            
            conn.execute('''
                UPDATE historico_trocas 
                SET motivo = ?, operador = ?, data_troca = ? 
                WHERE id = ?
            ''', (motivo, operador, data_troca, id))
            conn.commit()
            flash('Registro de troca atualizado com sucesso!', 'sucesso')
        except Exception as e:
            flash(f'Erro ao atualizar registro de troca: {e}', 'erro')
        finally:
            conn.close()
        return redirect(url_for('admin.index'))
        
    troca = conn.execute('SELECT * FROM historico_trocas WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not troca:
        flash('Registro de troca não encontrado.', 'erro')
        return redirect(url_for('admin.index'))
        
    return render_template('editar_troca.html', troca=troca)

@admin_bp.route('/excluir_troca/<int:id>', methods=['POST'])
def excluir_troca(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM historico_trocas WHERE id = ?', (id,))
        conn.commit()
        flash('Registro de troca excluído com sucesso!', 'sucesso')
    except Exception as e:
        flash(f'Erro ao excluir registro de troca: {e}', 'erro')
    finally:
        conn.close()
        
    return redirect(url_for('admin.index'))

@admin_bp.route('/editar_apontamento/<int:id>', methods=['GET', 'POST'])
def editar_apontamento(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    
    apontamento_antigo = conn.execute('SELECT * FROM historico_apontamentos WHERE id = ?', (id,)).fetchone()
    if not apontamento_antigo:
        conn.close()
        flash('Apontamento não encontrado.', 'erro')
        return redirect(url_for('admin.index'))
        
    if request.method == 'POST':
        try:
            novo_produto_id = int(request.form.get('produto_id'))
            nova_quantidade = int(request.form.get('quantidade', 0))
            ordem_producao = request.form.get('ordem_producao')
            status_producao = request.form.get('status_producao')
            data_apontamento = request.form.get('data')
            
            prod = conn.execute('SELECT codigo, nome FROM produtos WHERE id = ?', (novo_produto_id,)).fetchone()
            produto_nome = f"{prod['codigo']} - {prod['nome']}" if prod else "Produto Desconhecido"
            
            # 1. Atualiza o registro no histórico de apontamentos
            conn.execute('''
                UPDATE historico_apontamentos 
                SET produto_id = ?, produto_nome = ?, ordem_producao = ?, quantidade = ?, status_producao = ?, data_apontamento = ? 
                WHERE id = ?
            ''', (novo_produto_id, produto_nome, ordem_producao, nova_quantidade, status_producao, data_apontamento, id))
            
            # 2. Recálculo direto por somatório real (sem teto limite, permitindo ultrapassar para estudos de engenharia)
            ferramentas = conn.execute('SELECT posicao FROM ferramentas').fetchall()
            for f in ferramentas:
                pos = f['posicao']
                res = conn.execute('''
                    SELECT COALESCE(SUM(ha.quantidade), 0) as total 
                    FROM historico_apontamentos ha
                    JOIN produto_ferramentas pf ON ha.produto_id = pf.produto_id
                    WHERE pf.posicao = ?
                ''', (pos,)).fetchone()
                
                total_pecas = res['total'] if res else 0
                
                conn.execute('''
                    UPDATE ferramentas 
                    SET pecas_produzidas = ? 
                    WHERE posicao = ?
                ''', (total_pecas, pos))
            
            conn.commit()
            flash('Apontamento atualizado e vida útil recalculada com sucesso!', 'sucesso')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar apontamento: {e}', 'erro')
        finally:
            conn.close()
        return redirect(url_for('admin.index'))
        
    produtos = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
    conn.close()
    
    return render_template('editar_apontamento.html', apontamento=apontamento_antigo, produtos=produtos)

@admin_bp.route('/excluir_apontamento/<int:id>', methods=['POST'])
def excluir_apontamento(id):
    if not session.get('admin'):
        return redirect(url_for('admin.login'))
        
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM historico_apontamentos WHERE id = ?', (id,))
        
        # Recalcula o desgaste de todas as ferramentas para refletir a exclusão via somatório real
        ferramentas = conn.execute('SELECT posicao FROM ferramentas').fetchall()
        for f in ferramentas:
            pos = f['posicao']
            res = conn.execute('''
                SELECT COALESCE(SUM(ha.quantidade), 0) as total 
                FROM historico_apontamentos ha
                JOIN produto_ferramentas pf ON ha.produto_id = pf.produto_id
                WHERE pf.posicao = ?
            ''', (pos,)).fetchone()
            
            total_pecas = res['total'] if res else 0
            
            conn.execute('''
                UPDATE ferramentas 
                SET pecas_produzidas = ? 
                WHERE posicao = ?
            ''', (total_pecas, pos))
            
        conn.commit()
        flash('Apontamento excluído e vida útil recalculada com sucesso!', 'sucesso')
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao excluir apontamento: {e}', 'erro')
    finally:
        conn.close()
        
    return redirect(url_for('admin.index'))