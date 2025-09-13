from db import db
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(), nullable=False)

class Campanha(db.Model):
    __tablename__ = 'campanhas'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    criador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    criador = db.relationship('Usuario', backref='campanhas')
