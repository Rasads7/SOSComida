from flask_login import current_user
from flask import request
from models import LogAcaoModerador
from db import db
from datetime import datetime

def registrar_acao_moderador(acao, tipo_item, item_id, item_nome, detalhes=None):
    """
    Registra uma ação realizada por um moderador no sistema.
    
    Args:
        acao (str): Tipo de ação realizada (ex: 'aprovou_campanha', 'rejeitou_recebimento')
        tipo_item (str): Tipo do item afetado (ex: 'campanha', 'recebimento', 'instituicao')
        item_id (int): ID do item afetado
        item_nome (str): Nome/título do item para facilitar visualização
        detalhes (str, optional): Informações adicionais sobre a ação
    
    Returns:
        LogAcaoModerador: Objeto do log criado, ou None em caso de erro
    """
    try:
        if not current_user or not current_user.is_authenticated:
            print("Erro: Nenhum usuário autenticado para registrar log")
            return None

        if current_user.tipo != 'moderador':
            print(f"Aviso: Usuário {current_user.nome} não é moderador, mas tentou registrar log")
            return None

        novo_log = LogAcaoModerador(
            moderador_id=current_user.id,
            acao=acao,
            tipo_item=tipo_item,
            item_id=item_id,
            item_nome=item_nome,
            detalhes=detalhes,
            ip_address=request.remote_addr if request else None,
            data_acao=datetime.utcnow()
        )

        db.session.add(novo_log)
        db.session.commit()
        
        print(f"Log registrado: {current_user.nome} - {acao} - {tipo_item} #{item_id}")
        return novo_log
        
    except Exception as e:
        print(f"Erro ao registrar log de ação: {e}")
        db.session.rollback()
        return None

def obter_logs_recentes(limite=50):
    """
    Obtém os logs mais recentes de ações dos moderadores.
    
    Args:
        limite (int): Número máximo de logs a retornar
    
    Returns:
        list: Lista de objetos LogAcaoModerador
    """
    try:
        logs = LogAcaoModerador.query.order_by(
            LogAcaoModerador.data_acao.desc()
        ).limit(limite).all()
        return logs
    except Exception as e:
        print(f"Erro ao obter logs recentes: {e}")
        return []

def obter_logs_por_moderador(moderador_id, limite=50):
    """
    Obtém os logs de um moderador específico.
    
    Args:
        moderador_id (int): ID do moderador
        limite (int): Número máximo de logs a retornar
    
    Returns:
        list: Lista de objetos LogAcaoModerador
    """
    try:
        logs = LogAcaoModerador.query.filter_by(
            moderador_id=moderador_id
        ).order_by(
            LogAcaoModerador.data_acao.desc()
        ).limit(limite).all()
        return logs
    except Exception as e:
        print(f"Erro ao obter logs do moderador: {e}")
        return []

def obter_logs_por_tipo(tipo_item, limite=50):
    """
    Obtém logs filtrados por tipo de item.
    
    Args:
        tipo_item (str): Tipo do item ('campanha', 'recebimento', etc.)
        limite (int): Número máximo de logs a retornar
    
    Returns:
        list: Lista de objetos LogAcaoModerador
    """
    try:
        logs = LogAcaoModerador.query.filter_by(
            tipo_item=tipo_item
        ).order_by(
            LogAcaoModerador.data_acao.desc()
        ).limit(limite).all()
        return logs
    except Exception as e:
        print(f"Erro ao obter logs por tipo: {e}")
        return []

def obter_estatisticas_moderador(moderador_id):
    """
    Obtém estatísticas de ações de um moderador.
    
    Args:
        moderador_id (int): ID do moderador
    
    Returns:
        dict: Dicionário com estatísticas
    """
    try:
        total_acoes = LogAcaoModerador.query.filter_by(moderador_id=moderador_id).count()
        
        aprovacoes = LogAcaoModerador.query.filter(
            LogAcaoModerador.moderador_id == moderador_id,
            LogAcaoModerador.acao.like('%aprovou%')
        ).count()
        
        rejeicoes = LogAcaoModerador.query.filter(
            LogAcaoModerador.moderador_id == moderador_id,
            LogAcaoModerador.acao.like('%rejeitou%')
        ).count()
        
        delegacoes = LogAcaoModerador.query.filter(
            LogAcaoModerador.moderador_id == moderador_id,
            LogAcaoModerador.acao.like('%delegou%')
        ).count()
        
        return {
            'total_acoes': total_acoes,
            'aprovacoes': aprovacoes,
            'rejeicoes': rejeicoes,
            'delegacoes': delegacoes
        }
    except Exception as e:
        print(f"Erro ao obter estatísticas do moderador: {e}")
        return {
            'total_acoes': 0,
            'aprovacoes': 0,
            'rejeicoes': 0,
            'delegacoes': 0
        }