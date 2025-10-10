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
    
    cestas_entregues = db.Column(db.Integer, default=0)
    alimento_kg_entregues = db.Column(db.Numeric(10, 2), default=0.00)
    valor_entregue = db.Column(db.Numeric(10, 2), default=0.00)
    data_entrega_final = db.Column(db.DateTime)

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

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

    moderador = db.relationship('Usuario', foreign_keys=[moderador_id], backref='delegacoes_feitas')
    instituicao = db.relationship('Usuario', foreign_keys=[instituicao_id], backref='delegacoes_recebidas')
    doacao = db.relationship('SolicitacaoDoacao', backref='delegacao', uselist=False)
    recebimento = db.relationship('SolicitacaoRecebimento', backref='delegacao', uselist=False)
