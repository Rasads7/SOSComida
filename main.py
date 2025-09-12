from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import Usuario
from db import db
import hashlib

app = Flask(__name__)
app.secret_key = 'teste'
lm = LoginManager(app)
lm.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db.init_app(app)

def hash(txt):
    hash_obj = hashlib.sha256(txt.encode('utf-8'))
    return hash_obj.hexdigest()

@lm.user_loader
def user_loader(id):
    usuario = db.session.query(Usuario).filter_by(id=id).first()
    return usuario

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('homecomlogin.html')
    else:
        return render_template('homesemlogin.html')

@app.route('/campanhas')
@login_required
def campanhas():
    return render_template('campanhas.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['EmailFormLogin']
        senha = request.form['SenhaFormLogin']

        user = db.session.query(Usuario).filter_by(email=email, senha=hash(senha)).first()
        if not user:
            return 'Email ou senha incorretos'
        
        login_user(user)
        return redirect(url_for('home'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'GET':
        return render_template('registrar.html')
    elif request.method == 'POST':
        nome = request.form['NomeFormRegistrar']
        email = request.form['EmailFormRegistrar']
        senha = request.form['SenhaFormRegistrar']

        existente = db.session.query(Usuario).filter_by(email=email).first()
        if existente:
            return 'Este email já está cadastrado.'

        novo_usuario = Usuario(nome=nome, email=email, senha=hash(senha))
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)

        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/formulariodoar', methods=['GET', 'POST'])
@login_required  
def formulariodoar():
    if request.method == 'GET':
        return render_template('formulariodoar.html')
    
    tipo = request.form['tipoFormDoar']
    nome = request.form['nomeFormDoar']
    telefone = request.form['telefoneFormDoar']
    endereco = request.form['enderecoFormDoar']

    if tipo == 'cesta':
        local_entrega = request.form.get('local_entregaFormDoar', '')
        data_entrega = request.form.get('data_entregaFormDoar', '')
        qtd_cestas = request.form.get('qtd_cestasFormDoar', '1')
        return (
            f'Cesta(s) registrada(s) para {nome}. '
            f'Quantidade: {qtd_cestas}. '
            f'Entrega em: {local_entrega} na data {data_entrega}.'
        )

    elif tipo == 'monetaria':
        valor_predefinido = request.form['valor_predefinido']
        forma_pagamento = request.form['forma_pagamentoFormDoar']

        if valor_predefinido == 'outro':
            valor = request.form.get('valorFormDoar', '0')
        else:
            valor = valor_predefinido

        if forma_pagamento == 'pix':
            return f'Doação monetária via PIX de R${valor} registrada para {nome}.'
        elif forma_pagamento == 'cartao':
            nome_cartao = request.form['nome_cartaoFormDoar']
            numero_cartao = request.form['numero_cartaoFormDoar']
            validade_cartao = request.form['validade_cartaoFormDoar']
            cvv_cartao = request.form['cvv_cartaoFormDoar']
            final_cartao = numero_cartao[-4:] if len(numero_cartao) >= 4 else '****'
            return (
                f'Doação monetária via Cartão de R${valor} registrada para {nome}. '
                f'Cartão final {final_cartao}.'
            )


        return 'Forma de pagamento inválida'

    return 'Tipo de doação inválido'



@app.route('/formularioreceber', methods=['GET', 'POST'])
@login_required  
def formularioreceber():
    if request.method == 'GET':
        return render_template('formularioreceber.html')
    
    elif request.method == 'POST':
        nome = request.form['nomeFormReceber']
        telefone = request.form['telefoneFormReceber']
        endereco = request.form['enderecoFormReceber']
        qtd_pessoas = request.form['qtd_pessoasFormReceber']
        necessidades = request.form['necessidadesFormReceber']

        return f'Cadastro para receber doação: {nome}, {telefone}, {endereco}, {qtd_pessoas} pessoas. Necessidades: {necessidades}'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)