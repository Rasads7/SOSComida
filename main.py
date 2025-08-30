from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import Usuario
from db import db
import hashlib

app = Flask(__name__)
app.secret_key = 'testelogin'
lm = LoginManager(app)
lm.Login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db.init_app(app)

def hash (txt):
    hash_obj = hashlib.sha256(txt.encode('utf-8'))
    return hash_obj.hexdigest()



@lm.user_loader
def user_loader(id):
    usuario = db.session.query(Usuario).filter_by(id=id).first()
    return usuario

@app.route('/')
@login_required
def home():
    print(current_user)
    return render_template('home.html')

@app.route('/campanhas')
@login_required
def campanhas():
    return render_template('campanhas.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        nome = request.form['nomeForm']
        senha = request.form['senhaForm']

        user = db.session.query(Usuario).filter_by(nome=nome, senha=hash(senha)).first()
        if not user:
            return 'Nome ou senha incorretos'
        
        login_user(user)
        return redirect(url_for('home'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'GET':
        return render_template('registrar.html')
    elif request.method == 'POST':
        nome = request.form['nomeForm']
        senha = request.form['senhaForm']

        novo_usuario = Usuario(nome=nome, senha=hash(senha))
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)

        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/formulario', methods=['GET', 'POST'])
@login_required  
def formulario():
    if request.method == 'GET':
        return render_template('formulario.html')
    
    elif request.method == 'POST':
        tipo = request.form['tipo']
        nome = request.form['nome']
        telefone = request.form['telefone']
        endereco = request.form['endereco']

        if tipo == 'cesta':
            local_entrega = request.form['local_entrega']
            data_entrega = request.form['data_entrega']
            return f'Cesta Básica registrada para {nome}'

        elif tipo == 'monetaria':
            valor = request.form['valor']
            return f'Doação monetária de R${valor} registrada para {nome}'

        return 'Tipo de doação inválido'

@app.route('/receber', methods=['GET', 'POST'])
@login_required  
def receber():
    if request.method == 'GET':
        return render_template('receber.html')
    
    elif request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        qtd_pessoas = request.form['qtd_pessoas']
        necessidades = request.form['necessidades']

        return f'Cadastro para receber doação: {nome}, {telefone}, {endereco}, {qtd_pessoas} pessoas. Necessidades: {necessidades}'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)