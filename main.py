from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import Usuario, Campanha, Doacao, Pedido
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
            return render_template('login.html', errologin="Email ou senha incorretos")
        
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
            return render_template('registrar.html', erroregistrar="Email Já registrado")

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

@app.route('/formularioreceber', methods=['GET', 'POST'])
@login_required  
def formularioreceber():
    if request.method == 'GET':
        return render_template('formularioreceber.html')
    
    elif request.method == 'POST':
        nome = request.form['nomeFormReceber']
        telefone = request.form['telefoneFormReceber']
        endereco = request.form['enderecoFormReceber']
        qtd_pessoas = int(request.form['qtd_pessoasFormReceber'])
        necessidades = request.form['necessidadesFormReceber']

        novo_pedido = Pedido(
            nome=nome,
            telefone=telefone,
            endereco=endereco,
            qtd_pessoas=qtd_pessoas,
            necessidades=necessidades
        )

        db.session.add(novo_pedido)
        db.session.commit()
        return redirect(url_for('pesquisar'))

@app.route('/formulariodoar', methods=['GET', 'POST'])
@login_required  
def formulariodoar():
    if request.method == 'GET':
        return render_template('formulariodoar.html')
    
    elif request.method == 'POST':
        tipo = request.form['tipoFormDoar']
        nome = request.form['nomeFormDoar']
        telefone = request.form['telefoneFormDoar']
        endereco = request.form['enderecoFormDoar']

        if tipo == 'cesta':
            print("TIPO CESTA SELECIONADO")
            local_entrega = request.form.get('local_entregaFormDoar') or None
            data_entrega = request.form.get('data_entregaFormDoar') or None
            qtd_cestas = request.form.get('qtd_cestasFormDoar') or 1

            try:
                qtd_cestas = int(qtd_cestas)
            except ValueError:
                qtd_cestas = 1

            print("LOCAL ENTREGA:", local_entrega)
            print("DATA ENTREGA:", data_entrega)
            print("QTD CESTAS:", qtd_cestas)

            nova_doacao = Doacao(
                tipo='cesta',
                nome=nome,
                telefone=telefone,
                endereco=endereco,
                local_entrega=local_entrega,
                data_entrega=data_entrega,
                qtd_cestas=qtd_cestas
            )

        elif tipo == 'monetaria':
            valor_predefinido = request.form.get('valor_predefinido')
            if valor_predefinido == 'outro':
                valor = float(request.form.get('valorFormDoar', '0'))
            else:
                valor = float(valor_predefinido)
            
            nova_doacao = Doacao(
                tipo='monetaria',
                nome=nome,
                telefone=telefone,
                endereco=endereco,
                valor=valor,
            )

        db.session.add(nova_doacao)
        db.session.commit()
        return redirect(url_for('pesquisar'))

@app.route('/solicitarcampanha', methods=['GET', 'POST'])
@login_required
def solicitarcampanha():
    if request.method == 'GET':
        return render_template('solicitarcampanha.html')
    
    elif request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']

        nova_campanha = Campanha(
            titulo=titulo,
            descricao=descricao,
            criador_id=current_user.id
        )

        db.session.add(nova_campanha)
        db.session.commit()

        return redirect(url_for('campanhas'))

@app.route('/pesquisar')
@login_required
def pesquisar():
    doacoes = db.session.query(Doacao).all()
    pedidos = db.session.query(Pedido).all()
    return render_template('pesquisar.html', doacoes=doacoes, pedidos=pedidos)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)