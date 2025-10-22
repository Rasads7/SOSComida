from db import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), default='usuario')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    cpf = db.Column(db.String(14))
    cidade = db.Column(db.String(100))
    endereco = db.Column(db.String(255))
    telefone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    foto_perfil = db.Column(db.String(255))
    instituicao_nome = db.Column(db.String(200))
    instituicao_endereco = db.Column(db.String(255))
    instituicao_cep = db.Column(db.String(10))
    instituicao_tipo = db.Column(db.String(20))
    instituicao_cnpj = db.Column(db.String(18))
    status_aprovacao = db.Column(db.String(20), default='pendente')
    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=False)
    gov_br_id = db.Column(db.String(255), unique=True, nullable=True)
    gov_br_linked = db.Column(db.Boolean, default=False)
    gov_br_level = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='online', nullable=False)

class Campanha(db.Model):
    __tablename__ = 'campanhas'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    localizacao = db.Column(db.String(200), nullable=False)
    meta_voluntarios = db.Column(db.Integer, default=10)
    meta_doacoes = db.Column(db.Numeric(10, 2), default=1000.00)
    arrecadado = db.Column(db.Numeric(10, 2), default=0.00)
    imagem = db.Column(db.String(200), default='campanha1.jpg')
    status = db.Column(db.String(20), default='ativa')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime)
    
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref=db.backref('campanhas_solicitadas', lazy=True))
    
    instituicao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    instituicao_delegada = db.relationship('Usuario', foreign_keys=[instituicao_id], backref=db.backref('campanhas_delegadas', lazy=True))

class VoluntarioCampanha(db.Model):
    __tablename__ = 'voluntarios_campanhas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    campanha_id = db.Column(db.Integer, db.ForeignKey('campanhas.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref=db.backref('voluntariados', lazy=True))
    campanha = db.relationship('Campanha', backref=db.backref('voluntarios', lazy=True))

class SolicitacaoDoacao(db.Model):
    __tablename__ = 'solicitacoes_doacao'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    nome_doador = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    solicitacao_recebimento_id = db.Column(db.Integer, db.ForeignKey('solicitacoes_recebimento.id'), nullable=True)
    local_entrega = db.Column(db.String(200))
    data_entrega = db.Column(db.Date)
    valor = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='pendente')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref=db.backref('doacoes', lazy=True))
    recebimento_associado = db.relationship('SolicitacaoRecebimento', backref='doacoes_associadas', foreign_keys=[solicitacao_recebimento_id])

class SolicitacaoRecebimento(db.Model):
    __tablename__ = 'solicitacoes_recebimento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    qtd_pessoas = db.Column(db.Integer, nullable=False)
    necessidades = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    qtd_cestas = db.Column(db.Integer, default=0)
    qtd_higiene = db.Column(db.Integer, default=0)
    qtd_absorventes = db.Column(db.Integer, default=0)
    qtd_fraldas_infantis = db.Column(db.Integer, default=0)
    qtd_fraldas_geriatricas = db.Column(db.Integer, default=0)
    
    tipo_pix = db.Column(db.String(50))
    chave_pix = db.Column(db.String(200))
    
    cestas_entregues = db.Column(db.Integer, default=0)
    alimento_kg_entregues = db.Column(db.Numeric(10, 2), default=0.00)
    valor_entregue = db.Column(db.Numeric(10, 2), default=0.00)
    data_entrega_final = db.Column(db.DateTime)
    
    usuario = db.relationship('Usuario', backref=db.backref('recebimentos', lazy=True))  

class Delegacao(db.Model):

    __tablename__ = 'delegacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    moderador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    instituicao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    solicitacao_doacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes_doacao.id'), nullable=True)
    solicitacao_recebimento_id = db.Column(db.Integer, db.ForeignKey('solicitacoes_recebimento.id'), nullable=True)
    data_delegacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')

    moderador = db.relationship('Usuario', foreign_keys=[moderador_id], backref='delegacoes_feitas', lazy='joined')
    instituicao = db.relationship('Usuario', foreign_keys=[instituicao_id], backref='delegacoes_recebidas', lazy='joined')
    doacao = db.relationship('SolicitacaoDoacao', backref='delegacao', uselist=False, lazy='joined')
    recebimento = db.relationship('SolicitacaoRecebimento', backref='delegacao', uselist=False, lazy='joined')
    
    def __repr__(self):
        return f'<Delegacao #{self.id} - Instituição: {self.instituicao_id} - Status: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'moderador_id': self.moderador_id,
            'moderador_nome': self.moderador.nome if self.moderador else None,
            'instituicao_id': self.instituicao_id,
            'instituicao_nome': self.instituicao.instituicao_nome if self.instituicao else None,
            'tipo': 'doacao' if self.solicitacao_doacao_id else 'recebimento',
            'solicitacao_id': self.solicitacao_doacao_id or self.solicitacao_recebimento_id,
            'status': self.status,
            'data_delegacao': self.data_delegacao.strftime('%d/%m/%Y %H:%M') if self.data_delegacao else None
        }

class DoacaoCampanha(db.Model):
    __tablename__ = 'doacoes_campanha'
    
    id = db.Column(db.Integer, primary_key=True)
    campanha_id = db.Column(db.Integer, db.ForeignKey('campanhas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_doacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    qtd_cestas = db.Column(db.Integer, default=0)
    qtd_higiene = db.Column(db.Integer, default=0)
    qtd_agua = db.Column(db.Integer, default=0)
    qtd_fraldas_infantis = db.Column(db.Integer, default=0)
    
    campanha = db.relationship('Campanha', backref=db.backref('doacoes_itens', lazy='dynamic'))
    usuario = db.relationship('Usuario', backref=db.backref('doacoes_campanha', lazy=True))

class DenunciaVoluntario(db.Model):
    __tablename__ = 'denuncias_voluntarios'
    
    id = db.Column(db.Integer, primary_key=True)

    denunciante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    denunciado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    campanha_id = db.Column(db.Integer, db.ForeignKey('campanhas.id'), nullable=False)

    motivo = db.Column(db.String(50), nullable=False)

    descricao = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default='pendente', nullable=False)

    data_denuncia = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    moderador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    data_resolucao = db.Column(db.DateTime, nullable=True)

    observacoes_moderador = db.Column(db.Text, nullable=True)

    acao_tomada = db.Column(db.String(50), nullable=True)

    denunciante = db.relationship('Usuario', foreign_keys=[denunciante_id], backref=db.backref('denuncias_feitas', lazy=True))
    denunciado = db.relationship('Usuario', foreign_keys=[denunciado_id], backref=db.backref('denuncias_recebidas', lazy=True))
    campanha = db.relationship('Campanha', backref=db.backref('denuncias', lazy=True))
    moderador = db.relationship('Usuario', foreign_keys=[moderador_id], backref=db.backref('denuncias_analisadas', lazy=True))
    
    def __repr__(self):
        return f'<DenunciaVoluntario #{self.id}: {self.denunciante.nome} -> {self.denunciado.nome} na campanha {self.campanha.titulo}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'denunciante_nome': self.denunciante.nome if self.denunciante else 'Desconhecido',
            'denunciado_nome': self.denunciado.nome if self.denunciado else 'Desconhecido',
            'campanha_titulo': self.campanha.titulo if self.campanha else 'Desconhecida',
            'motivo': self.motivo,
            'descricao': self.descricao,
            'status': self.status,
            'data_denuncia': self.data_denuncia.strftime('%d/%m/%Y %H:%M') if self.data_denuncia else None,
            'moderador_nome': self.moderador.nome if self.moderador else None,
            'acao_tomada': self.acao_tomada
        }

class LogAcaoModerador(db.Model):

    __tablename__ = 'log_acoes_moderador'
    
    id = db.Column(db.Integer, primary_key=True)
    moderador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    tipo_item = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_nome = db.Column(db.String(200), nullable=True)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    detalhes = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    moderador = db.relationship('Usuario', backref=db.backref('acoes_log', lazy=True))
    
    def __repr__(self):
        return f'<LogAcaoModerador {self.moderador.nome if self.moderador else "Unknown"}: {self.acao} em {self.tipo_item} #{self.item_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'moderador_nome': self.moderador.nome if self.moderador else 'Desconhecido',
            'moderador_id': self.moderador_id,
            'acao': self.acao,
            'tipo_item': self.tipo_item,
            'item_id': self.item_id,
            'item_nome': self.item_nome,
            'data_acao': self.data_acao.strftime('%d/%m/%Y %H:%M:%S') if self.data_acao else None,
            'detalhes': self.detalhes,
            'ip_address': self.ip_address
        }