# Adicione estas rotas ao seu arquivo principal Flask (app.py)

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Usuario, DenunciaVoluntario, Advertencia, LogAcaoModerador

# Rota para aplicar advertência (moderador)
@app.route('/aplicar_advertencia/<int:denuncia_id>', methods=['POST'])
@login_required
def aplicar_advertencia(denuncia_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado. Apenas moderadores podem aplicar advertências.', 'error')
        return redirect(url_for('index'))
    
    denuncia = DenunciaVoluntario.query.get_or_404(denuncia_id)
    
    # Obtém dados do formulário
    tipo_acao = request.form.get('tipo_acao')  # 'advertencia', 'suspensao', 'revogacao'
    mensagem = request.form.get('mensagem')
    dias_suspensao = request.form.get('dias_suspensao', 0, type=int)
    
    # Cria a advertência
    advertencia = Advertencia(
        usuario_id=denuncia.denunciado_id,
        moderador_id=current_user.id,
        denuncia_id=denuncia_id,
        tipo=tipo_acao,
        mensagem=mensagem,
        motivo=denuncia.motivo,
        vista=False
    )
    
    # Se for suspensão, define as datas
    if tipo_acao == 'suspensao' and dias_suspensao > 0:
        advertencia.data_inicio_suspensao = datetime.utcnow()
        advertencia.data_fim_suspensao = datetime.utcnow() + timedelta(days=dias_suspensao)
        
        # Suspende o usuário
        usuario = Usuario.query.get(denuncia.denunciado_id)
        usuario.status = 'suspenso'
        
    # Se for revogação, revoga a conta
    elif tipo_acao == 'revogacao':
        usuario = Usuario.query.get(denuncia.denunciado_id)
        usuario.conta_revogada = True
        usuario.data_revogacao = datetime.utcnow()
        usuario.motivo_revogacao = f"Revogado por moderador: {mensagem}"
    
    # Atualiza o status da denúncia
    denuncia.status = 'resolvida'
    denuncia.data_resolucao = datetime.utcnow()
    denuncia.moderador_id = current_user.id
    denuncia.observacoes_moderador = mensagem
    denuncia.acao_tomada = tipo_acao
    
    # Registra a ação no log
    log = LogAcaoModerador(
        moderador_id=current_user.id,
        acao=f'Aplicou {tipo_acao}',
        tipo_item='advertencia',
        item_id=advertencia.id,
        item_nome=f'Advertência para {denuncia.denunciado.nome}',
        detalhes=mensagem,
        ip_address=request.remote_addr
    )
    
    db.session.add(advertencia)
    db.session.add(log)
    db.session.commit()
    
    flash(f'{tipo_acao.capitalize()} aplicada com sucesso!', 'success')
    return redirect(url_for('gerenciar_denuncias'))

# Rota para marcar advertência como vista
@app.route('/marcar_advertencia_vista/<int:advertencia_id>', methods=['POST'])
@login_required
def marcar_advertencia_vista(advertencia_id):
    advertencia = Advertencia.query.get_or_404(advertencia_id)
    
    # Verifica se a advertência é para o usuário atual
    if advertencia.usuario_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    # Marca como vista
    advertencia.vista = True
    advertencia.data_vista = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Advertência marcada como vista'})

# Rota atualizada do perfil
@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    usuario = current_user
    
    if request.method == 'POST':
        # Código existente para atualizar perfil...
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.telefone = request.form.get('telefone')
        usuario.cidade = request.form.get('cidade')
        usuario.endereco = request.form.get('endereco')
        usuario.bio = request.form.get('bio')
        
        # Upload de foto se houver
        if 'foto_perfil' in request.files:
            arquivo = request.files['foto_perfil']
            if arquivo and arquivo.filename:
                # Salvar arquivo (implemente a lógica de salvamento)
                pass
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))
    
    # Busca advertência não vista
    advertencia_nao_vista = Advertencia.query.filter_by(
        usuario_id=current_user.id,
        vista=False
    ).order_by(Advertencia.data_acao.desc()).first()
    
    # Busca atividades recentes (advertências, denúncias, etc.)
    atividades_recentes = []
    
    # Adiciona advertências às atividades
    advertencias = Advertencia.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Advertencia.data_acao.desc()).limit(5).all()
    
    for adv in advertencias:
        atividade = {
            'titulo': f'Você recebeu uma {adv.tipo}',
            'descricao': adv.mensagem[:100] + '...' if len(adv.mensagem) > 100 else adv.mensagem,
            'data_formatada': adv.data_acao.strftime('%d/%m/%Y às %H:%M'),
            'icone': 'fa-exclamation-triangle',
            'tipo_icone': 'warning' if adv.tipo == 'advertencia' else 'danger',
            'badge': True,
            'badge_tipo': adv.tipo,
            'badge_texto': adv.tipo.capitalize()
        }
        atividades_recentes.append(atividade)
    
    # Adiciona denúncias feitas pelo usuário
    denuncias_feitas = DenunciaVoluntario.query.filter_by(
        denunciante_id=current_user.id
    ).order_by(DenunciaVoluntario.data_denuncia.desc()).limit(3).all()
    
    for den in denuncias_feitas:
        atividade = {
            'titulo': 'Você fez uma denúncia',
            'descricao': f'Denunciou {den.denunciado.nome} - Status: {den.status}',
            'data_formatada': den.data_denuncia.strftime('%d/%m/%Y às %H:%M'),
            'icone': 'fa-flag',
            'tipo_icone': 'info',
            'badge': False
        }
        atividades_recentes.append(atividade)
    
    # Ordena atividades por data (mais recente primeiro)
    # Nota: Em produção, você faria isso de forma mais eficiente no banco
    
    return render_template('perfil_atualizado.html',
                         usuario=usuario,
                         advertencia_nao_vista=advertencia_nao_vista,
                         atividades_recentes=atividades_recentes)

# Rota para o moderador ver todas as advertências aplicadas
@app.route('/moderador/advertencias')
@login_required
def listar_advertencias():
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    advertencias = Advertencia.query.order_by(Advertencia.data_acao.desc()).all()
    return render_template('moderador_advertencias.html', advertencias=advertencias)

# Rota para verificar suspensões expiradas (deve ser executada periodicamente)
@app.route('/verificar_suspensoes')
def verificar_suspensoes():
    # Esta rota deveria ser protegida ou executada como job agendado
    suspensoes_expiradas = Advertencia.query.filter(
        Advertencia.tipo == 'suspensao',
        Advertencia.data_fim_suspensao <= datetime.utcnow()
    ).all()
    
    for suspensao in suspensoes_expiradas:
        usuario = Usuario.query.get(suspensao.usuario_id)
        if usuario and usuario.status == 'suspenso':
            usuario.status = 'ativo'
            
            # Cria log de reativação
            log = LogAcaoModerador(
                moderador_id=1,  # Sistema
                acao='Reativação automática',
                tipo_item='usuario',
                item_id=usuario.id,
                item_nome=usuario.nome,
                detalhes='Suspensão expirada automaticamente'
            )
            db.session.add(log)
    
    db.session.commit()
    return jsonify({'message': f'{len(suspensoes_expiradas)} suspensões expiradas processadas'})