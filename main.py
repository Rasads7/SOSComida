from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_cors import CORS
from models import Usuario, SolicitacaoDoacao, SolicitacaoRecebimento, Campanha, VoluntarioCampanha, Delegacao, DoacaoCampanha, LogAcaoModerador, DenunciaVoluntario
from db import db
from requests_oauthlib import OAuth2Session
import hashlib
import os
from datetime import datetime
import uuid
import pyotp
import qrcode
import io
import base64
import json


app = Flask(__name__, static_folder='static')
CORS(app)
app.secret_key = 'soscomida_secret_key_2024'


lm = LoginManager(app)
lm.login_view = 'login'


basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
db.init_app(app)


def hash_password(txt):
    return hashlib.sha256(txt.encode('utf-8')).hexdigest()

def registrar_log(acao, tipo_item, item_id, item_nome, detalhes=None):
    try:
        novo_log = LogAcaoModerador(
            moderador_id=current_user.id,
            acao=acao,
            tipo_item=tipo_item,
            item_id=item_id,
            item_nome=item_nome,
            detalhes=detalhes,
            ip_address=request.remote_addr
        )
        db.session.add(novo_log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        db.session.rollback()

def create_initial_data():
    with app.app_context():
        print("Verificando se o banco de dados está populado...")

        if not Usuario.query.first():
            print("Criando usuários e instituições de exemplo...")

            moderador = Usuario(
                nome='Moderador',
                email='moderador@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            
            moderador_pedro = Usuario(
                nome='Pedro Moderador',
                email='pedro@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            moderador_davi = Usuario(
                nome='Davi Moderador',
                email='davi@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            moderador_pablo = Usuario(
                nome='Pablo',
                email='pablo@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            moderador_bruno = Usuario(
                nome='Bruno',
                email='bruno@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            moderador_rafael = Usuario(
                nome='Rafael',
                email='rafael@soscomida.com',
                senha=hash_password('1234'),
                tipo='moderador'
            )
            
            instituicao1 = Usuario(
                nome='ONG Amigos da Cidade',
                email='instituicao1@ongs.org',
                senha=hash_password('1234'),
                tipo='instituicao',
                instituicao_nome='ONG Amigos da Cidade',
                instituicao_endereco='Rua da Esperança, 123',
                instituicao_cep='01234-567',
                instituicao_tipo='privada',
                status_aprovacao='aprovada'
            )
            
            instituicao2 = Usuario(
                nome='Prefeitura de Ajuda Alimentar',
                email='instituicao2@prefeitura.gov.br',
                senha=hash_password('1234'),
                tipo='instituicao',
                instituicao_nome='Prefeitura de Ajuda Alimentar',
                instituicao_endereco='Av. Principal, 500',
                instituicao_cep='76543-210',
                instituicao_tipo='publica',
                status_aprovacao='aprovada'
            )
            
            usuario_exemplo = Usuario(
                nome='Usuario Exemplo',
                email='exemplo@email.com',
                senha=hash_password('123456'),
                tipo='usuario',
                cpf='111.111.111-11',
                cidade='São Paulo',
                endereco='Rua Exemplo, 123, São Paulo'
            )

            db.session.add_all([moderador, moderador_pedro, moderador_davi, moderador_pablo, 
                               moderador_bruno, moderador_rafael, instituicao1, instituicao2, usuario_exemplo])
            db.session.commit()
            print("Usuários e instituições criados com sucesso.")

        if not Campanha.query.first():
            print("Criando campanhas de exemplo...")
            
            usuario_solicitante = Usuario.query.filter_by(email='exemplo@email.com').first()
            if not usuario_solicitante:
                print("ERRO: Usuário de exemplo não encontrado.")
                return

            campanhas_ativas = [
                Campanha(
                    titulo="Natal Solidário 2024",
                    descricao="Campanha para arrecadar cestas básicas e brinquedos para famílias carentes durante o período natalino.",
                    localizacao="São Paulo, SP",
                    meta_voluntarios=25,
                    meta_doacoes=5000.00,
                    arrecadado=1250.00,
                    imagem="campanha1.jpg",
                    status="ativa"
                ),
                Campanha(
                    titulo="Alimentação Escolar",
                    descricao="Projeto para garantir alimentação adequada para crianças em escolas públicas.",
                    localizacao="Rio de Janeiro, RJ",
                    meta_voluntarios=15,
                    meta_doacoes=3000.00,
                    arrecadado=800.00,
                    imagem="campanha2.jpg",
                    status="ativa"
                ),
            ]
            
            campanhas_teste = [
                Campanha(
                    titulo="Campanha Emergencial - Enchentes RS",
                    descricao="Campanha de emergência para ajudar as vítimas das enchentes no Rio Grande do Sul.",
                    localizacao="Porto Alegre, RS",
                    meta_voluntarios=50,
                    meta_doacoes=15000.00,
                    arrecadado=0.00,
                    imagem="campanha_emergencia.jpg",
                    status="pendente",
                    solicitante_id=usuario_solicitante.id
                ),
                Campanha(
                    titulo="Páscoa Solidária 2025",
                    descricao="Campanha para distribuir ovos de páscoa e cestas básicas para crianças.",
                    localizacao="Salvador, BA",
                    meta_voluntarios=30,
                    meta_doacoes=8000.00,
                    arrecadado=0.00,
                    imagem="campanha_pascoa.jpg",
                    status="pendente",
                    solicitante_id=usuario_solicitante.id
                ),
            ]
            
            todas_campanhas = campanhas_ativas + campanhas_teste
            db.session.add_all(todas_campanhas)
            db.session.commit()
            print("Campanhas criadas com sucesso.")

        if not SolicitacaoRecebimento.query.first():
            print("Criando solicitações de exemplo...")

            SolicitacaoDoacao.query.delete()
            SolicitacaoRecebimento.query.delete()
            Delegacao.query.delete()
            db.session.commit()

            usuario_exemplo = Usuario.query.filter_by(email='exemplo@email.com').first()
            if usuario_exemplo:
                solicitacoes_aprovadas = [
                    SolicitacaoRecebimento(
                        usuario_id=usuario_exemplo.id, nome='Dona Lúcia', telefone='(11) 99111-2222', 
                        endereco='Rua Principal, 550, Bairro Novo, São Paulo', qtd_pessoas=2, 
                        necessidades='Leite, Pão, Arroz', status='aprovada'
                    ),
                ]
                
                solicitacoes_pendentes = [
                    SolicitacaoRecebimento(
                        usuario_id=usuario_exemplo.id, nome='Família Pereira', telefone='(11) 99888-7777', 
                        endereco='Rua da Solidariedade, 50, Bairro Centro, São Paulo', qtd_pessoas=4, 
                        necessidades='Cesta básica e fraldas para bebê', status='pendente',
                        qtd_cestas=2, qtd_higiene=1, qtd_fraldas_infantis=3, tipo_pix='cpf', chave_pix='111.111.111-11'
                    ),
                    SolicitacaoRecebimento(
                        usuario_id=usuario_exemplo.id, nome='Maria Silva', telefone='(21) 98765-4321', 
                        endereco='Av. das Flores, 789, Rio de Janeiro', qtd_pessoas=6, 
                        necessidades='Família com 4 crianças pequenas, desempregada há 3 meses.', 
                        status='pendente', qtd_cestas=3, qtd_higiene=2, qtd_absorventes=2, 
                        tipo_pix='telefone', chave_pix='(21) 98765-4321'
                    ),
                ]

                db.session.add_all(solicitacoes_aprovadas + solicitacoes_pendentes)
                db.session.commit()
                print("Solicitações criadas com sucesso.")
        
        print("Inicialização de dados concluída.")


@lm.user_loader
def user_loader(id):
    return Usuario.query.get(int(id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('homecomlogin.html', usuario=current_user)
    return render_template('homesemlogin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        codigo_2fa = request.form.get('codigo_2fa')

        if codigo_2fa:
            
            user_id = session.get('user_id_pending_2fa')
            
            if not user_id:
                flash('Sessão expirada. Faça login novamente.', 'error')
                return redirect(url_for('login'))
            
            
            user = Usuario.query.get(user_id)
            
            if not user:
                session.pop('user_id_pending_2fa', None)
                flash('Usuário não encontrado. Faça login novamente.', 'error')
                return redirect(url_for('login'))

            totp = pyotp.TOTP(user.two_factor_secret)
            if totp.verify(codigo_2fa):
                session.pop('user_id_pending_2fa', None)
                login_user(user)
                flash(f'Bem-vindo(a), {user.nome}!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Código de autenticação inválido. Tente novamente.', 'error')
                return render_template('login.html', show_2fa=True, usuario=None)

        else:
            email = request.form.get('EmailFormLogin')
            senha = request.form.get('SenhaFormLogin')
            
            
            if not email or not senha:
                flash('Email e senha são obrigatórios.', 'error')
                return render_template('login.html', show_2fa=False, usuario=None)
            
            
            user = Usuario.query.filter_by(email=email, senha=hash_password(senha)).first()
            
            if user:
                if user.two_factor_enabled:
                    session['user_id_pending_2fa'] = user.id
                    flash('Digite o código de autenticação de 2 fatores.', 'info')
                    return render_template('login.html', show_2fa=True, usuario=None)
                else:
                    login_user(user)
                    flash(f'Bem-vindo(a), {user.nome}!', 'success')
                    return redirect(url_for('home'))
            else:
                flash('Email ou senha incorretos', 'error')
                return render_template('login.html', show_2fa=False, usuario=None)

    session.pop('user_id_pending_2fa', None)
    return render_template('login.html', show_2fa=False, usuario=None)

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        tipo_cadastro = request.form.get('tipo')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if not email or '@' not in email:
            flash('Email inválido.', 'error')
            return render_template('registrar.html')
        
        if not senha or len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('registrar.html')
            
        if confirmar_senha and senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
            return render_template('registrar.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'error')
            return render_template('registrar.html')
            
        if tipo_cadastro == 'pessoa':
            nome = request.form.get('nome')
            telefone = request.form.get('telefone')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            cpf = request.form.get('cpf', '')


#AQUI EU SEPAREI O VALIDADOR DE CPF P NN DAR CONFLITO COM OS DEMAIS
            def is_valid_cpf(cpf_str: str) -> bool:
                cpf = ''.join([c for c in cpf_str if c.isdigit()])
                if len(cpf) != 11 or cpf == cpf[0] * 11:
                    return False
                def calc_dv(cpf_base: str) -> str:
                    soma = sum(int(d) * peso for d, peso in zip(cpf_base, range(len(cpf_base)+1, 1, -1)))
                    resto = (soma * 10) % 11
                    return '0' if resto == 10 else str(resto)
                dv1 = calc_dv(cpf[:9])
                dv2 = calc_dv(cpf[:9] + dv1)
                return cpf[-2:] == dv1 + dv2

#AQUI O DE TELEFONE     OBS: TESTAR NOVAMENTE, PQ DEU CRASH QUANDO CRIEI UMA COM CPF E TELEFONE CORRETOS
            def is_valid_tel_br(phone_str: str) -> bool:
                digits = ''.join(c for c in phone_str if c.isdigit())
                if len(digits) not in (10, 11):
                    return False
                ddd = digits[:2]
                if ddd[0] == '0':  
                    return False
                return True

            def only_digits(s: str) -> str:
                return ''.join(c for c in s if c.isdigit())

            cpf_digits = only_digits(cpf)
            telefone_digits = only_digits(telefone)

            if not all([nome, telefone_digits, endereco, cidade, cpf_digits]):
                flash('Todos os campos para pessoa são obrigatórios.', 'error')
                return render_template('registrar.html')

            if not is_valid_cpf(cpf_digits):
                flash('CPF inválido. Verifique e tente novamente.', 'error')
                return render_template('registrar.html')

            if not is_valid_tel_br(telefone_digits):
                flash('Telefone inválido. Informe com DDD (2 dígitos) e 10 ou 11 dígitos no total, ex.: (11) 2345-6789 ou (11) 91234-5678.', 'error')
                return render_template('registrar.html')

            if Usuario.query.filter_by(cpf=cpf_digits).first():
                flash('Este CPF já está cadastrado.', 'error')
                return render_template('registrar.html')

            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha=hash_password(senha),
                telefone=telefone,
                endereco=endereco,
                cidade=cidade,
                cpf=cpf_digits,   
                tipo='usuario'
            )
            flash_msg = f'Cadastro realizado com sucesso! Bem-vindo(a), {nome}!'
            
        elif tipo_cadastro == 'instituicao':
            nome_inst = request.form.get('nome')
            telefone = request.form.get('telefone')
            endereco_inst = request.form.get('endereco')
            cep_inst = request.form.get('cep')
            tipo_inst = request.form.get('tipo_instituicao')
            
            if not all([nome_inst, telefone, endereco_inst, cep_inst, tipo_inst]):
                flash('Todos os campos para instituição são obrigatórios.', 'error')
                return render_template('registrar.html')

            novo_usuario = Usuario(
                nome=nome_inst,
                email=email,
                senha=hash_password(senha),
                telefone=telefone,
                endereco=endereco_inst,
                instituicao_nome=nome_inst,
                instituicao_endereco=endereco_inst,
                instituicao_cep=cep_inst,
                instituicao_tipo=tipo_inst,
                status_aprovacao='pendente',
                tipo='instituicao'
            )
            flash_msg = f'Cadastro da instituição "{nome_inst}" realizado! Aguarde aprovação.'
            
        else:
            flash('Tipo de cadastro inválido.', 'error')
            return render_template('registrar.html')
            
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            login_user(novo_usuario)
            flash(flash_msg, 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar: {str(e)}', 'error')
            return render_template('registrar.html')
        
    return render_template('registrar.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/configurar_2fa')
@login_required
def configurar_2fa():
    if current_user.two_factor_enabled:
        flash('A autenticação de 2 fatores já está habilitada.', 'info')
        return redirect(url_for('perfil'))
    
    if not current_user.two_factor_secret:
        secret = pyotp.random_base32()
        current_user.two_factor_secret = secret
        db.session.commit()
    else:
        secret = current_user.two_factor_secret
    
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="SOS Comida"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('configurar_2fa.html', 
                           qr_code=img_base64, 
                           secret=secret,
                           usuario=current_user)

@app.route('/ativar_2fa', methods=['POST'])
@login_required
def ativar_2fa():
    codigo = request.form.get('codigo_verificacao')
    
    if not current_user.two_factor_secret:
        flash('Erro: segredo 2FA não encontrado.', 'error')
        return redirect(url_for('configurar_2fa'))
    
    totp = pyotp.TOTP(current_user.two_factor_secret)
    
    if totp.verify(codigo):
        current_user.two_factor_enabled = True
        db.session.commit()
        flash('Autenticação de 2 fatores ativada com sucesso!', 'success')
        return redirect(url_for('perfil'))
    else:
        flash('Código inválido. Tente novamente.', 'error')
        return redirect(url_for('configurar_2fa'))

@app.route('/desativar_2fa', methods=['POST'])
@login_required
def desativar_2fa():
    codigo = request.form.get('codigo_verificacao')
    
    if not current_user.two_factor_enabled:
        flash('A autenticação de 2 fatores não está ativada.', 'info')
        return redirect(url_for('perfil'))
    
    totp = pyotp.TOTP(current_user.two_factor_secret)
    
    if totp.verify(codigo):
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        db.session.commit()
        flash('Autenticação de 2 fatores desativada com sucesso!', 'success')
    else:
        flash('Código inválido. Não foi possível desativar o 2FA.', 'error')
    
    return redirect(url_for('perfil'))

@app.route('/solicitarcampanha', methods=['GET', 'POST'])
@login_required
def solicitarcampanha():
    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem solicitar campanhas.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        localizacao = request.form.get('localizacao')
        meta_voluntarios = int(request.form.get('meta_voluntarios', 10))
        meta_doacoes = float(request.form.get('meta_doacoes', 1000.00))
        
        if len(titulo) < 5 or len(descricao) < 20:
            flash('Título deve ter pelo menos 5 e descrição 20 caracteres.', 'error')
            return render_template('solicitarcampanha.html', usuario=current_user)
        
        nova_campanha = Campanha(
            titulo=titulo, 
            descricao=descricao, 
            localizacao=localizacao,
            meta_voluntarios=meta_voluntarios, 
            meta_doacoes=meta_doacoes,
            imagem='campanha_default.jpg', 
            status='pendente',
            solicitante_id=current_user.id
        )
        db.session.add(nova_campanha)
        db.session.commit()
        
        flash(f'Sua solicitação de campanha "{titulo}" foi enviada para moderação!', 'success')
        return redirect(url_for('minhas_solicitacoes'))
        
    return render_template('solicitarcampanha.html', usuario=current_user)

@app.route('/formulariodoar', methods=['GET'])
@login_required
def formulariodoar():
    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem fazer doações.', 'error')
        return redirect(url_for('home'))
        
    solicitacoes = SolicitacaoRecebimento.query.filter_by(status='aprovada').order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    
    return render_template('formulariodoar.html', usuario=current_user, solicitacoes=solicitacoes)

@app.route('/doar_monetario/<int:recebimento_id>', methods=['POST'])
@login_required
def doar_monetario(recebimento_id):
    if current_user.tipo != 'usuario':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    valor_str = request.form.get('valor_pix')
    
    try:
        valor = float(valor_str)
        if valor <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Valor de doação inválido.', 'error')
        return redirect(url_for('formulariodoar'))

    nova_doacao = SolicitacaoDoacao(
        usuario_id=current_user.id,
        tipo='monetaria',
        nome_doador=current_user.nome,
        telefone=current_user.telefone if hasattr(current_user, 'telefone') else 'Não informado',
        endereco=current_user.endereco if hasattr(current_user, 'endereco') else 'Não informado',
        valor=valor,
        solicitacao_recebimento_id=recebimento_id,
        status='aceita'
    )
    db.session.add(nova_doacao)
    db.session.commit()
    
    flash(f'Sua doação de R${valor:.2f} foi registrada!', 'success')
    return redirect(url_for('formulariodoar'))

@app.route('/doar_item/<int:recebimento_id>', methods=['POST'])
@login_required
def doar_item(recebimento_id):
    if current_user.tipo != 'usuario':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))

    local_entrega = request.form.get('local_entrega')
    data_entrega_str = request.form.get('data_entrega')
    
    if not local_entrega or not data_entrega_str:
        flash('Preencha todos os campos para a entrega.', 'error')
        return redirect(url_for('formulariodoar'))
        
    data_entrega = datetime.strptime(data_entrega_str, '%Y-%m-%d').date()

    nova_doacao = SolicitacaoDoacao(
        usuario_id=current_user.id,
        tipo='cesta',
        nome_doador=current_user.nome,
        telefone=current_user.telefone if hasattr(current_user, 'telefone') else 'Não informado',
        endereco=current_user.endereco if hasattr(current_user, 'endereco') else 'Não informado',
        local_entrega=local_entrega,
        data_entrega=data_entrega,
        solicitacao_recebimento_id=recebimento_id,
        status='pendente'
    )
    db.session.add(nova_doacao)
    db.session.commit()
    
    flash('Sua doação foi registrada!', 'success')
    return redirect(url_for('formulariodoar'))

@app.route('/formularioreceber', methods=['GET', 'POST'])
@login_required  
def formularioreceber():
    if not current_user.gov_br_linked:
        flash('Para solicitar ajuda, é obrigatório vincular sua conta com o Gov.br.', 'warning')
        return redirect(url_for('perfil'))

    if current_user.tipo != 'usuario':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        nome = request.form.get('nomeAjuda')
        telefone = request.form.get('telefoneAjuda')
        endereco = request.form.get('enderecoAjuda')
        qtd_pessoas = int(request.form.get('qtdPessoasAjuda', 1))
        necessidades = request.form.get('explicarSituacaoAjuda')
        qtd_cestas = int(request.form.get('qtdCestas', 0))
        qtd_higiene = int(request.form.get('qtd_higiene', 0))
        qtd_absorventes = int(request.form.get('qtd_absorventes', 0))
        qtd_fraldas_infantis = int(request.form.get('qtd_fraldas_infantis', 0))
        qtd_fraldas_geriatricas = int(request.form.get('qtd_fraldas_geriatricas', 0))
        tipo_pix = request.form.get('tipo_pix')
        chave_pix = request.form.get('chave_pix')

        novo_recebimento = SolicitacaoRecebimento(
            usuario_id=current_user.id,
            nome=nome,
            telefone=telefone,
            endereco=endereco,
            qtd_pessoas=qtd_pessoas,
            necessidades=necessidades,
            qtd_cestas=qtd_cestas,
            qtd_higiene=qtd_higiene,
            qtd_absorventes=qtd_absorventes,
            qtd_fraldas_infantis=qtd_fraldas_infantis,
            qtd_fraldas_geriatricas=qtd_fraldas_geriatricas,
            tipo_pix=tipo_pix,
            chave_pix=chave_pix,
            status='pendente'
        )
        db.session.add(novo_recebimento)
        db.session.commit()
        
        flash('Sua solicitação foi enviada para análise!', 'success')
        return redirect(url_for('minhas_solicitacoes'))
        
    return render_template('formularioreceber.html', usuario=current_user)

@app.route('/minhas_solicitacoes')
@login_required
def minhas_solicitacoes():
    doacoes = SolicitacaoDoacao.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoDoacao.data_criacao.desc()).all()
    recebimentos = SolicitacaoRecebimento.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    campanhas_solicitadas = Campanha.query.filter_by(solicitante_id=current_user.id).order_by(Campanha.data_criacao.desc()).all()
    
    return render_template('minhas_solicitacoes.html', 
                           doacoes=doacoes, 
                           recebimentos=recebimentos, 
                           campanhas_solicitadas=campanhas_solicitadas,
                           usuario=current_user)

@app.route('/campanhas')
def campanhas():
    termo_busca = request.args.get('busca', '').strip()
    localizacao_filtro = request.args.get('localizacao', '').strip()
    ordenacao = request.args.get('ordenacao', 'recentes')

    query = Campanha.query.filter_by(status='ativa')

    if termo_busca:
        query = query.filter(Campanha.titulo.ilike(f'%{termo_busca}%'))

    if localizacao_filtro:
        query = query.filter(Campanha.localizacao.ilike(f'%{localizacao_filtro}%'))

    if ordenacao == 'alfabetica':
        query = query.order_by(Campanha.titulo.asc())
    elif ordenacao == 'proximas_meta':
        pass
    elif ordenacao == 'mais_voluntarios':
        from sqlalchemy import func
        query = query.outerjoin(VoluntarioCampanha).group_by(Campanha.id).order_by(
            func.count(VoluntarioCampanha.id).desc()
        )
    else:
        query = query.order_by(Campanha.data_criacao.desc())

    campanhas_ativas = query.all()

    for campanha in campanhas_ativas:
        campanha.num_voluntarios = len(campanha.voluntarios)
        if campanha.meta_doacoes and campanha.meta_doacoes > 0:
            progresso = (float(campanha.arrecadado) / float(campanha.meta_doacoes)) * 100
            campanha.progresso = min(100, progresso)
        else:
            campanha.progresso = 0

    todas_campanhas = Campanha.query.filter_by(status='ativa').all()
    localizacoes_unicas = sorted(list(set([c.localizacao for c in todas_campanhas if c.localizacao])))
    
    campanhas_pendentes_count = 0
    if current_user.is_authenticated and current_user.tipo == 'moderador':
        campanhas_pendentes_count = Campanha.query.filter_by(status='pendente').count()
    
    usuario_logado = current_user if current_user.is_authenticated else None
    
    total_encontradas = len(campanhas_ativas)
    
    return render_template('campanhas.html', 
                         usuario=usuario_logado, 
                         campanhas=campanhas_ativas,
                         campanhas_pendentes_count=campanhas_pendentes_count,
                         termo_busca=termo_busca,
                         localizacao_filtro=localizacao_filtro,
                         ordenacao=ordenacao,
                         localizacoes_unicas=localizacoes_unicas,
                         total_encontradas=total_encontradas)

@app.route('/detalhes_campanha/<int:campanha_id>')
@login_required
def detalhes_campanha(campanha_id):
    campanha = Campanha.query.get_or_404(campanha_id)
    
    campanha.num_voluntarios = len(campanha.voluntarios)
    campanha.progresso = min(100, (float(campanha.arrecadado) / float(campanha.meta_doacoes)) * 100) if campanha.meta_doacoes > 0 else 0
    
    dias_restantes = None
    if campanha.data_fim:
        delta = campanha.data_fim - datetime.utcnow().date()
        if delta.days >= 0:
            dias_restantes = delta.days

    return render_template(
        'detalhes_campanha.html', 
        usuario=current_user, 
        campanha=campanha,
        dias_restantes=dias_restantes
    )

@app.route('/voluntariar/<int:campanha_id>')
@login_required
def voluntariar(campanha_id):
    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem se voluntariar.', 'error')
        return redirect(url_for('campanhas'))

    campanha = Campanha.query.get_or_404(campanha_id)
    
    voluntario_existente = VoluntarioCampanha.query.filter_by(usuario_id=current_user.id, campanha_id=campanha.id).first()
    if voluntario_existente:
        flash('Você já está inscrito como voluntário nesta campanha.', 'info')
    else:
        novo_voluntario = VoluntarioCampanha(
            usuario_id=current_user.id,
            campanha_id=campanha.id
        )
        db.session.add(novo_voluntario)
        db.session.commit()
        flash(f'Parabéns! Você agora é voluntário na campanha "{campanha.titulo}".', 'success')
        
    return redirect(url_for('campanhas'))

@app.route('/doar_campanha_pix/<int:campanha_id>', methods=['POST'])
@login_required
def doar_campanha_pix(campanha_id):
    campanha = Campanha.query.get_or_404(campanha_id)
    valor = request.form.get('valor_pix')
    
    try:
        valor_doado = float(valor)
        if valor_doado <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Valor de doação inválido.', 'error')
        return redirect(url_for('campanhas'))

    campanha.arrecadado = float(campanha.arrecadado) + valor_doado
    db.session.commit()

    flash(f'Sua doação de R${valor_doado:.2f} para a campanha "{campanha.titulo}" foi registrada!', 'success')
    return redirect(url_for('campanhas'))

@app.route('/moderacao')
@login_required
def moderacao():
    """Painel principal de moderação"""
    if current_user.tipo != 'moderador':
        flash('Acesso negado. Apenas moderadores podem acessar esta página.', 'error')
        return redirect(url_for('home'))

    recebimentos_pendentes = SolicitacaoRecebimento.query.filter_by(status='pendente').all()
    campanhas_pendentes = Campanha.query.filter_by(status='pendente').all()

    campanhas_ativas = Campanha.query.filter_by(status='ativa').order_by(Campanha.data_criacao.desc()).all()
    
    instituicoes_pendentes = Usuario.query.filter_by(tipo='instituicao', status_aprovacao='pendente').all()
    instituicoes = Usuario.query.filter_by(tipo='instituicao', status_aprovacao='aprovada').all()
    
    
    denuncias_pendentes = DenunciaVoluntario.query.filter_by(status='pendente').order_by(DenunciaVoluntario.data_denuncia.desc()).all()
    
    
    logs_recentes = LogAcaoModerador.query.order_by(LogAcaoModerador.data_acao.desc()).limit(50).all()
    
    now = datetime.utcnow()

    return render_template('moderacao.html',
                           recebimentos_pendentes=recebimentos_pendentes,
                           campanhas_pendentes=campanhas_pendentes,
                           campanhas_ativas=campanhas_ativas,
                           instituicoes_pendentes=instituicoes_pendentes,
                           instituicoes=instituicoes,
                           denuncias_pendentes=denuncias_pendentes,
                           logs_recentes=logs_recentes,
                           now=now,
                           usuario=current_user)

@app.route('/moderacao/editar_campanha/<int:campanha_id>', methods=['GET', 'POST'])
@login_required
def editar_campanha_moderacao(campanha_id):
    """Permite moderadores editarem campanhas"""
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)
    instituicoes = Usuario.query.filter_by(tipo='instituicao', status_aprovacao='aprovada').all()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        localizacao = request.form.get('localizacao')
        meta_voluntarios = int(request.form.get('meta_voluntarios', 10))
        meta_doacoes = float(request.form.get('meta_doacoes', 1000.00))
        status = request.form.get('status', campanha.status)

        if len(titulo) < 5 or len(descricao) < 20:
            flash('Título deve ter pelo menos 5 e descrição 20 caracteres.', 'error')
            return render_template('editar_campanha_moderacao.html', 
                                 campanha=campanha, 
                                 usuario=current_user)

        campanha.titulo = titulo
        campanha.descricao = descricao
        campanha.localizacao = localizacao
        campanha.meta_voluntarios = meta_voluntarios
        campanha.meta_doacoes = meta_doacoes
        
        # Atualizar instituição delegada
        instituicao_id_nova = request.form.get('instituicao_id')
        instituicao_id_antiga = campanha.instituicao_id
        
        # Verificar se a instituição mudou
        instituicao_mudou = False
        if instituicao_id_nova and instituicao_id_nova != '':
            nova_id = int(instituicao_id_nova)
            if nova_id != instituicao_id_antiga:
                instituicao_mudou = True
                campanha.instituicao_id = nova_id
        else:
            if instituicao_id_antiga is not None:
                instituicao_mudou = True
            campanha.instituicao_id = None
        
        # Se a instituição mudou e a campanha estava ativa, voltar para pendente
        if instituicao_mudou and campanha.status == 'ativa':
            campanha.status = 'pendente'
            flash('A campanha foi alterada para status PENDENTE pois a instituição responsável foi modificada.', 'warning')
        else:
            campanha.status = status

        if 'imagem' in request.files:
            arquivo = request.files['imagem']
            if arquivo and arquivo.filename != '':
                ext = arquivo.filename.rsplit('.', 1)[1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    imagem_nome = f"campanha_{uuid.uuid4().hex[:8]}.{ext}"
                    img_dir = os.path.join(app.static_folder, 'img')
                    os.makedirs(img_dir, exist_ok=True)
                    arquivo.save(os.path.join(img_dir, imagem_nome))
                    campanha.imagem = imagem_nome
                else:
                    flash('Formato de imagem não suportado. Use JPG, PNG ou GIF.', 'warning')
        
        try:
            db.session.commit()

            registrar_log(
                acao='editou_campanha',
                tipo_item='campanha',
                item_id=campanha.id,
                item_nome=titulo,
                detalhes=f'Campanha editada - Status: {status}, Meta: R${meta_doacoes:.2f}'
            )
            
            flash(f'Campanha "{titulo}" editada com sucesso!', 'success')
            return redirect(url_for('moderacao'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao editar campanha: {str(e)}', 'error')

    return render_template('editar_campanha_moderacao.html', 
                         campanha=campanha, 
                         instituicoes=instituicoes,
                         usuario=current_user)



@app.route('/moderacao/apagar_campanha/<int:campanha_id>', methods=['POST'])
@login_required
def apagar_campanha(campanha_id):
    """Apaga permanentemente uma campanha"""
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)
    titulo_campanha = campanha.titulo
    
    try:
        VoluntarioCampanha.query.filter_by(campanha_id=campanha.id).delete()
        
        DoacaoCampanha.query.filter_by(campanha_id=campanha.id).delete()
        
        DenunciaVoluntario.query.filter_by(campanha_id=campanha.id).delete()
        
        registrar_log(
            acao='apagou_campanha',
            tipo_item='campanha',
            item_id=campanha.id,
            item_nome=titulo_campanha,
            detalhes=f'Campanha APAGADA permanentemente - Localização: {campanha.localizacao}, Arrecadado: R${campanha.arrecadado:.2f}'
        )

        db.session.delete(campanha)
        db.session.commit()
        
        flash(f'Campanha "{titulo_campanha}" foi apagada permanentemente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao apagar campanha: {str(e)}', 'error')
    
    return redirect(url_for('moderacao'))


@app.route('/moderacao/suspender_campanha/<int:campanha_id>', methods=['POST'])
@login_required
def suspender_campanha(campanha_id):
    """Suspende uma campanha (muda status para 'suspensa')"""
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)

    if campanha.status == 'suspensa':
        campanha.status = 'ativa'
        mensagem = f'Campanha "{campanha.titulo}" foi reativada.'
        acao_log = 'reativou_campanha'
    else:
        campanha.status = 'suspensa'
        mensagem = f'Campanha "{campanha.titulo}" foi suspensa.'
        acao_log = 'suspendeu_campanha'
    
    try:
        db.session.commit()

        registrar_log(
            acao=acao_log,
            tipo_item='campanha',
            item_id=campanha.id,
            item_nome=campanha.titulo,
            detalhes=f'Status alterado para: {campanha.status}'
        )
        
        flash(mensagem, 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao suspender campanha: {str(e)}', 'error')
    
    return redirect(url_for('moderacao'))

@app.route('/rejeitar/<string:tipo>/<int:id>', methods=['POST'])
@login_required
def rejeitar_solicitacao(tipo, id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    solicitacao = None
    item_nome = None
    
    if tipo == 'doacao':
        solicitacao = SolicitacaoDoacao.query.get_or_404(id)
        item_nome = solicitacao.nome_doador
    elif tipo == 'recebimento':
        solicitacao = SolicitacaoRecebimento.query.get_or_404(id)
        item_nome = solicitacao.nome
    elif tipo == 'campanha':
        solicitacao = Campanha.query.get_or_404(id)
        item_nome = solicitacao.titulo
    
    if solicitacao:
        solicitacao.status = 'rejeitada'
        db.session.commit()

        registrar_log(
            acao=f'rejeitou_{tipo}',
            tipo_item=tipo,
            item_id=id,
            item_nome=item_nome,
            detalhes=f'Solicitação de {tipo} rejeitada'
        )
        
        flash(f'Solicitação de {tipo} rejeitada com sucesso.', 'warning')
    else:
        flash('Tipo de solicitação inválido.', 'error')
        
    return redirect(url_for('moderacao'))

@app.route('/aprovar_campanha/<int:campanha_id>', methods=['POST'])
@login_required
def aprovar_campanha(campanha_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)
    
    instituicao_id = request.form.get('instituicao_id')
    if not instituicao_id:
        flash('Você deve selecionar uma instituição para delegar a campanha.', 'error')
        return redirect(url_for('moderacao'))

    campanha.status = 'pendente'  # Fica pendente até a instituição aceitar
    campanha.instituicao_id = int(instituicao_id)
    db.session.commit()

    instituicao = Usuario.query.get(instituicao_id)
    registrar_log(
        acao='aprovou_campanha',
        tipo_item='campanha',
        item_id=campanha_id,
        item_nome=campanha.titulo,
        detalhes=f'Campanha delegada para {instituicao.instituicao_nome if instituicao else "instituição desconhecida"} (ID: {instituicao_id}) - Aguardando aceitação'
    )
    
    flash(f'Campanha "{campanha.titulo}" foi delegada para {instituicao.instituicao_nome}. Aguardando aceitação da instituição.', 'success')
    return redirect(url_for('moderacao'))

@app.route('/aprovar_instituicao/<int:instituicao_id>', methods=['POST'])
@login_required
def aprovar_instituicao(instituicao_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    instituicao = Usuario.query.get_or_404(instituicao_id)
    
    if instituicao.tipo != 'instituicao':
        flash('Usuário não é uma instituição.', 'error')
        return redirect(url_for('moderacao'))
    
    instituicao.status_aprovacao = 'aprovada'
    db.session.commit()

    registrar_log(
        acao='aprovou_instituicao',
        tipo_item='instituicao',
        item_id=instituicao_id,
        item_nome=instituicao.instituicao_nome,
        detalhes=f'Instituição {instituicao.instituicao_tipo} aprovada - Email: {instituicao.email}'
    )
    
    flash(f'Instituição "{instituicao.instituicao_nome}" aprovada com sucesso!', 'success')
    return redirect(url_for('moderacao'))

@app.route('/rejeitar_instituicao/<int:instituicao_id>', methods=['POST'])
@login_required
def rejeitar_instituicao(instituicao_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    instituicao = Usuario.query.get_or_404(instituicao_id)
    if instituicao.tipo != 'instituicao':
        flash('Usuário não é uma instituição.', 'error')
        return redirect(url_for('moderacao'))
    
    instituicao.status_aprovacao = 'rejeitada'
    db.session.commit()

    registrar_log(
        acao='rejeitou_instituicao',
        tipo_item='instituicao',
        item_id=instituicao_id,
        item_nome=instituicao.instituicao_nome,
        detalhes=f'Instituição {instituicao.instituicao_tipo} rejeitada - Email: {instituicao.email}'
    )
    
    flash(f'Instituição "{instituicao.instituicao_nome}" rejeitada.', 'warning')
    return redirect(url_for('moderacao'))

@app.route('/delegar/<string:tipo>/<int:solicitacao_id>', methods=['POST'])
@login_required
def delegar_solicitacao(tipo, solicitacao_id):
    print(f"\n{'='*70}")
    print(f"🔄 DELEGANDO SOLICITAÇÃO")
    print(f"{'='*70}")
    print(f"Moderador: {current_user.nome} (ID: {current_user.id})")
    print(f"Tipo: {tipo}")
    print(f"Solicitação ID: {solicitacao_id}")
    
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    instituicao_id = request.form.get('instituicao_id')
    print(f"Instituição selecionada ID: {instituicao_id}")
    
    if not instituicao_id:
        flash('Nenhuma instituição selecionada.', 'error')
        return redirect(url_for('moderacao'))
    
    try:
        instituicao_id = int(instituicao_id)
    except (ValueError, TypeError):
        flash('ID de instituição inválido.', 'error')
        return redirect(url_for('moderacao'))

    instituicao = Usuario.query.get(instituicao_id)
    if not instituicao:
        print(f"❌ Instituição não encontrada!")
        flash('Instituição não encontrada.', 'error')
        return redirect(url_for('moderacao'))
    
    if instituicao.tipo != 'instituicao':
        print(f"❌ Usuário não é uma instituição!")
        flash('O usuário selecionado não é uma instituição.', 'error')
        return redirect(url_for('moderacao'))
    
    if instituicao.status_aprovacao != 'aprovada':
        print(f"❌ Instituição não está aprovada!")
        flash('A instituição selecionada não está aprovada.', 'error')
        return redirect(url_for('moderacao'))
    
    print(f"✅ Instituição válida: {instituicao.instituicao_nome}")
    
    solicitacao = None
    item_nome = None
    
    try:
        if tipo == 'doacao':
            solicitacao = SolicitacaoDoacao.query.get_or_404(solicitacao_id)
            item_nome = solicitacao.nome_doador

            del_existente = Delegacao.query.filter_by(
                solicitacao_doacao_id=solicitacao.id
            ).first()
            
            if del_existente:
                flash('Esta doação já foi delegada.', 'warning')
                return redirect(url_for('moderacao'))
            
            print(f"📦 Delegando doação de: {item_nome}")

            solicitacao.status = 'delegada'
            
            nova_delegacao = Delegacao(
                moderador_id=current_user.id,
                instituicao_id=instituicao_id,
                solicitacao_doacao_id=solicitacao.id,
                status='pendente'
            )
            
        elif tipo == 'recebimento':
            solicitacao = SolicitacaoRecebimento.query.get_or_404(solicitacao_id)
            item_nome = solicitacao.nome

            del_existente = Delegacao.query.filter_by(
                solicitacao_recebimento_id=solicitacao.id
            ).first()
            
            if del_existente:
                flash('Esta solicitação de recebimento já foi delegada.', 'warning')
                return redirect(url_for('moderacao'))
            
            print(f"🤝 Delegando recebimento para: {item_nome}")

            solicitacao.status = 'delegada'
            
            nova_delegacao = Delegacao(
                moderador_id=current_user.id,
                instituicao_id=instituicao_id,
                solicitacao_recebimento_id=solicitacao.id,
                status='pendente'
            )
        else:
            flash('Tipo de solicitação inválido.', 'error')
            return redirect(url_for('moderacao'))

        db.session.add(nova_delegacao)
        db.session.commit()
        
        print(f"✅ Delegação criada com sucesso!")
        print(f"   ID da delegação: {nova_delegacao.id}")
        print(f"   Moderador ID: {nova_delegacao.moderador_id}")
        print(f"   Instituição ID: {nova_delegacao.instituicao_id}")
        print(f"   Status: {nova_delegacao.status}")

        delegacao_verificacao = Delegacao.query.get(nova_delegacao.id)
        if delegacao_verificacao:
            print(f"✅ Verificação: Delegação foi salva corretamente no banco!")
            print(f"   Instituição da delegação: {delegacao_verificacao.instituicao_id}")
        else:
            print(f"❌ ERRO: Delegação não foi encontrada após commit!")
        
        print(f"{'='*70}\n")

        registrar_log(
            acao=f'delegou_{tipo}',
            tipo_item=tipo,
            item_id=solicitacao_id,
            item_nome=item_nome,
            detalhes=f'Solicitação delegada para {instituicao.instituicao_nome} (ID: {instituicao_id})'
        )
        
        flash(f'✅ Solicitação de {tipo} delegada com sucesso para {instituicao.instituicao_nome}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO ao delegar:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao delegar solicitação: {str(e)}', 'error')

    return redirect(url_for('moderacao'))

@app.route('/criar_campanha', methods=['GET', 'POST'])
@login_required
def criar_campanha():
    if current_user.tipo != 'moderador':
        flash('Acesso negado. Apenas moderadores podem criar campanhas.', 'error')
        return redirect(url_for('campanhas'))
    
    instituicoes = Usuario.query.filter_by(tipo='instituicao', status_aprovacao='aprovada').all()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        localizacao = request.form.get('localizacao')
        meta_voluntarios = int(request.form.get('meta_voluntarios', 10))
        meta_doacoes = float(request.form.get('meta_doacoes', 1000.00))
        status = request.form.get('status', 'ativa')
        instituicao_id = request.form.get('instituicao_id')
        
        if len(titulo) < 5 or len(descricao) < 20:
            flash('Título deve ter pelo menos 5 e descrição 20 caracteres.', 'error')
            return render_template('criar_campanha.html', usuario=current_user)
        
        imagem_nome = 'campanha_default.jpg'
        if 'imagem' in request.files:
            arquivo = request.files['imagem']
            if arquivo and arquivo.filename != '':
                ext = arquivo.filename.rsplit('.', 1)[1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    imagem_nome = f"campanha_{uuid.uuid4().hex[:8]}.{ext}"
                    img_dir = os.path.join(app.static_folder, 'img')
                    os.makedirs(img_dir, exist_ok=True)
                    arquivo.save(os.path.join(img_dir, imagem_nome))
        
        nova_campanha = Campanha(
            titulo=titulo, 
            descricao=descricao, 
            localizacao=localizacao,
            meta_voluntarios=meta_voluntarios, 
            meta_doacoes=meta_doacoes,
            imagem=imagem_nome, 
            status=status,
            instituicao_id=int(instituicao_id) if instituicao_id and instituicao_id != '' else None
        )
        db.session.add(nova_campanha)
        db.session.commit()

        registrar_log(
            acao='criou_campanha',
            tipo_item='campanha',
            item_id=nova_campanha.id,
            item_nome=titulo,
            detalhes=f'Campanha criada com status "{status}" - Meta: R${meta_doacoes:.2f}'
        )
        
        flash(f'Campanha "{titulo}" criada com sucesso!', 'success')
        return redirect(url_for('campanhas'))
        
    return render_template('criar_campanha.html', instituicoes=instituicoes, usuario=current_user)

@app.route('/aprovar_recebimento/<int:id>', methods=['POST'])
@login_required
def aprovar_recebimento(id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
        
    solicitacao = SolicitacaoRecebimento.query.get_or_404(id)
    solicitacao.status = 'aprovada'
    db.session.commit()

    registrar_log(
        acao='aprovou_recebimento',
        tipo_item='recebimento',
        item_id=id,
        item_nome=solicitacao.nome,
        detalhes=f'Solicitação de {solicitacao.qtd_pessoas} pessoas aprovada - {solicitacao.qtd_cestas} cestas solicitadas'
    )
    
    flash(f'Solicitação de ajuda de "{solicitacao.nome}" aprovada com sucesso!', 'success')
    return redirect(url_for('moderacao'))

@app.route('/denunciar_voluntario', methods=['POST'])
@login_required
def denunciar_voluntario():
    """Rota para criar uma denúncia contra um voluntário"""
    print("🔍 DEBUG: Função denunciar_voluntario foi chamada!")
    print(f"   Usuário: {current_user.nome}")
    print(f"   Tipo: {current_user.tipo}")

    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem denunciar.', 'error')
        return redirect(url_for('home'))

    denunciado_id = request.form.get('denunciado_id')
    campanha_id = request.form.get('campanha_id')
    motivo = request.form.get('motivo')
    descricao = request.form.get('descricao')
    
    print(f"   Denunciado ID: {denunciado_id}")
    print(f"   Campanha ID: {campanha_id}")
    print(f"   Motivo: {motivo}")
    print(f"   Descrição (primeiros 50 chars): {descricao[:50] if descricao else 'None'}...")

    if not all([denunciado_id, campanha_id, motivo, descricao]):
        flash('Todos os campos são obrigatórios.', 'error')
        return redirect(url_for('campanhas'))

    try:
        denunciado_id = int(denunciado_id)
        campanha_id = int(campanha_id)
    except (ValueError, TypeError) as e:
        print(f"❌ Erro ao converter IDs: {e}")
        flash('Dados inválidos.', 'error')
        return redirect(url_for('campanhas'))

    voluntario = VoluntarioCampanha.query.filter_by(
        usuario_id=denunciado_id,
        campanha_id=campanha_id
    ).first()
    
    if not voluntario:
        print(f"❌ Usuário {denunciado_id} não é voluntário da campanha {campanha_id}")
        flash('O usuário não é voluntário desta campanha.', 'error')
        return redirect(url_for('campanhas'))
    
    print(f"✅ Voluntário encontrado: {voluntario.usuario.nome}")

    denuncia_existente = DenunciaVoluntario.query.filter_by(
        denunciante_id=current_user.id,
        denunciado_id=denunciado_id,
        campanha_id=campanha_id,
        status='pendente'
    ).first()
    
    if denuncia_existente:
        print(f"⚠️ Denúncia duplicada detectada: ID {denuncia_existente.id}")
        flash('Você já possui uma denúncia pendente contra este voluntário nesta campanha.', 'warning')
        return redirect(url_for('detalhes_campanha', campanha_id=campanha_id))

    nova_denuncia = DenunciaVoluntario(
        denunciante_id=current_user.id,
        denunciado_id=denunciado_id,
        campanha_id=campanha_id,
        motivo=motivo,
        descricao=descricao,
        status='pendente'
    )
    
    try:
        db.session.add(nova_denuncia)
        db.session.commit()
        print(f"✅ Denúncia criada com sucesso! ID: {nova_denuncia.id}")
        flash('Denúncia enviada com sucesso! Será analisada por nossa equipe.', 'success')
        return redirect(url_for('detalhes_campanha', campanha_id=campanha_id))
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar denúncia: {e}")
        flash(f'Erro ao enviar denúncia: {str(e)}', 'error')
        return redirect(url_for('campanhas'))

@app.route('/analisar_denuncia/<int:denuncia_id>', methods=['POST'])
@login_required
def analisar_denuncia(denuncia_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    denuncia = DenunciaVoluntario.query.get_or_404(denuncia_id)
    acao = request.form.get('acao')
    observacoes = request.form.get('observacoes', '')
    
    if not acao:
        flash('Selecione uma ação.', 'error')
        return redirect(url_for('moderacao'))

    denuncia.status = 'resolvida'
    denuncia.moderador_id = current_user.id
    denuncia.data_resolucao = datetime.utcnow()
    denuncia.acao_tomada = acao
    denuncia.observacoes_moderador = observacoes

    if acao == 'removido_campanha':
        voluntario = VoluntarioCampanha.query.filter_by(
            usuario_id=denuncia.denunciado_id,
            campanha_id=denuncia.campanha_id
        ).first()
        
        if voluntario:
            db.session.delete(voluntario)
            flash(f'Voluntário {denuncia.denunciado.nome} foi removido da campanha.', 'success')
    
    elif acao == 'advertencia':
        flash(f'Advertência aplicada ao voluntário {denuncia.denunciado.nome}.', 'success')
    
    elif acao == 'denuncia_improcedente':
        flash('Denúncia marcada como improcedente.', 'info')
    
    elif acao == 'sem_acao':
        flash('Denúncia arquivada sem ação.', 'info')
    
    try:
        db.session.commit()

        registrar_log(
            acao='analisou_denuncia',
            tipo_item='denuncia',
            item_id=denuncia_id,
            item_nome=f'{denuncia.denunciante.nome} → {denuncia.denunciado.nome}',
            detalhes=f'Ação tomada: {acao} - Motivo: {denuncia.motivo}'
        )
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar denúncia: {str(e)}', 'error')
    
    return redirect(url_for('moderacao'))

@app.route('/arquivar_denuncia/<int:denuncia_id>', methods=['POST'])
@login_required
def arquivar_denuncia(denuncia_id):
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    denuncia = DenunciaVoluntario.query.get_or_404(denuncia_id)
    denuncia.status = 'arquivada'
    denuncia.moderador_id = current_user.id
    denuncia.data_resolucao = datetime.utcnow()
    
    try:
        db.session.commit()

        registrar_log(
            acao='arquivou_denuncia',
            tipo_item='denuncia',
            item_id=denuncia_id,
            item_nome=f'{denuncia.denunciante.nome} → {denuncia.denunciado.nome}',
            detalhes=f'Denúncia arquivada - Motivo original: {denuncia.motivo}'
        )
        
        flash('Denúncia arquivada com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao arquivar denúncia: {str(e)}', 'error')
    
    return redirect(url_for('moderacao'))

@app.route('/instituicao/solicitacoes')
@login_required
def solicitacoes_instituicao():
    if current_user.tipo != 'instituicao':
        flash('Acesso negado. Apenas instituições podem acessar esta página.', 'error')
        return redirect(url_for('home'))
    
    print(f"\n{'='*70}")
    print(f"🔍 DEBUG: Buscando solicitações para instituição {current_user.id}")
    print(f"{'='*70}")

    todas_delegacoes = Delegacao.query.filter_by(
        instituicao_id=current_user.id
    ).all()
    
    print(f"\n📊 Total de delegações encontradas: {len(todas_delegacoes)}")

    campanhas_delegadas = Campanha.query.filter_by(
        instituicao_id=current_user.id
    ).all()
    
    print(f"📊 Total de campanhas delegadas: {len(campanhas_delegadas)}")

    delegacoes_pendentes = [d for d in todas_delegacoes if d.status == 'pendente']
    delegacoes_aceitas = [d for d in todas_delegacoes if d.status == 'aceita']
    delegacoes_concluidas = [d for d in todas_delegacoes if d.status == 'concluida']
    delegacoes_recusadas = [d for d in todas_delegacoes if d.status == 'recusada']

    campanhas_pendentes = [c for c in campanhas_delegadas if c.status == 'pendente']
    campanhas_ativas = [c for c in campanhas_delegadas if c.status == 'ativa']
    campanhas_suspensas = [c for c in campanhas_delegadas if c.status == 'suspensa']
    campanhas_concluidas = [c for c in campanhas_delegadas if c.status in ['concluida', 'finalizada']]
    
    print(f"\n📋 Distribuição por status:")
    print(f"   Delegações Pendentes: {len(delegacoes_pendentes)}")
    print(f"   Delegações Aceitas: {len(delegacoes_aceitas)}")
    print(f"   Delegações Concluídas: {len(delegacoes_concluidas)}")
    print(f"   Delegações Recusadas: {len(delegacoes_recusadas)}")
    print(f"   Campanhas Pendentes: {len(campanhas_pendentes)}")
    print(f"   Campanhas Ativas: {len(campanhas_ativas)}")
    print(f"   Campanhas Suspensas: {len(campanhas_suspensas)}")
    print(f"   Campanhas Concluídas: {len(campanhas_concluidas)}")

    total_cestas = db.session.query(
        db.func.sum(SolicitacaoRecebimento.cestas_entregues)
    ).join(
        Delegacao,
        Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
    ).filter(
        Delegacao.instituicao_id == current_user.id,
        SolicitacaoRecebimento.status == 'entregue'
    ).scalar() or 0
    
    total_kg = db.session.query(
        db.func.sum(SolicitacaoRecebimento.alimento_kg_entregues)
    ).join(
        Delegacao,
        Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
    ).filter(
        Delegacao.instituicao_id == current_user.id,
        SolicitacaoRecebimento.status == 'entregue'
    ).scalar() or 0.0
    
    total_monetario = db.session.query(
        db.func.sum(SolicitacaoRecebimento.valor_entregue)
    ).join(
        Delegacao,
        Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
    ).filter(
        Delegacao.instituicao_id == current_user.id,
        SolicitacaoRecebimento.status == 'entregue'
    ).scalar() or 0.0
    
    projetos_ajudados = SolicitacaoRecebimento.query.join(
        Delegacao,
        Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
    ).filter(
        Delegacao.instituicao_id == current_user.id,
        SolicitacaoRecebimento.status == 'entregue'
    ).count()

    projetos_ajudados += len(campanhas_delegadas)
    
    print(f"\n📈 Estatísticas:")
    print(f"   Projetos ajudados: {projetos_ajudados}")
    print(f"   Cestas entregues: {total_cestas}")
    print(f"   Alimentos (kg): {total_kg}")
    print(f"   Valor distribuído: R$ {total_monetario}")
    print(f"{'='*70}\n")
    
    return render_template('solicitacoes_instituicao.html',
                          usuario=current_user,
                          delegacoes_pendentes=delegacoes_pendentes,
                          delegacoes_aceitas=delegacoes_aceitas,
                          delegacoes_concluidas=delegacoes_concluidas,
                          delegacoes_recusadas=delegacoes_recusadas,
                          campanhas_pendentes=campanhas_pendentes,
                          campanhas_ativas=campanhas_ativas,
                          campanhas_suspensas=campanhas_suspensas,
                          campanhas_concluidas=campanhas_concluidas,
                          total_cestas=total_cestas,
                          total_kg=total_kg,
                          total_monetario=total_monetario,
                          projetos_ajudados=projetos_ajudados)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        cidade = request.form.get('cidade')
        endereco = request.form.get('endereco')
        bio = request.form.get('bio')
        cnpj = request.form.get('cnpj')
        
        if not nome or len(nome) < 2:
            flash('Nome deve ter pelo menos 2 caracteres.', 'error')
            return redirect(url_for('perfil'))
            
        if not email:
            flash('Email é obrigatório.', 'error')
            return redirect(url_for('perfil'))
            
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente and usuario_existente.id != current_user.id:
            flash('Este email já está sendo usado por outro usuário.', 'error')
            return redirect(url_for('perfil'))
        
        if 'foto_perfil' in request.files:
            arquivo = request.files['foto_perfil']
            if arquivo and arquivo.filename != '':
                ext = arquivo.filename.rsplit('.', 1)[1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    nome_arquivo = f"perfil_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
                    img_dir = os.path.join(app.static_folder, 'img')
                    os.makedirs(img_dir, exist_ok=True)
                    caminho_arquivo = os.path.join(img_dir, nome_arquivo)
                    
                    arquivo.save(caminho_arquivo)
                    
                    if current_user.foto_perfil:
                        caminho_antigo = os.path.join(app.static_folder, 'img', current_user.foto_perfil)
                        if os.path.exists(caminho_antigo) and 'perfil_default' not in current_user.foto_perfil:
                            os.remove(caminho_antigo)
                    
                    current_user.foto_perfil = nome_arquivo
                else:
                    flash('Formato de imagem não suportado. Use JPG, PNG ou GIF.', 'error')
                    return redirect(url_for('perfil'))
        
        current_user.nome = nome
        current_user.email = email
        current_user.telefone = telefone
        current_user.cidade = cidade
        current_user.endereco = endereco
        current_user.bio = bio
        
        if current_user.tipo == 'instituicao':
            current_user.instituicao_nome = nome
            current_user.instituicao_endereco = endereco
            current_user.instituicao_cep = cidade
            if cnpj:
                current_user.instituicao_cnpj = cnpj
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))
        
    if current_user.tipo == 'instituicao':
        delegacoes_pendentes = Delegacao.query.filter_by(
            instituicao_id=current_user.id, 
            status='pendente'
        ).all()
        
        delegacoes_aceitas = Delegacao.query.filter_by(
            instituicao_id=current_user.id, 
            status='aceita'
        ).all()

        total_cestas = db.session.query(
            db.func.sum(SolicitacaoRecebimento.cestas_entregues)
        ).join(
            Delegacao, 
            Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
        ).filter(
            Delegacao.instituicao_id == current_user.id,
            SolicitacaoRecebimento.status == 'entregue'
        ).scalar() or 0
        
        total_kg_alimentos = db.session.query(
            db.func.sum(SolicitacaoRecebimento.alimento_kg_entregues)
        ).join(
            Delegacao,
            Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
        ).filter(
            Delegacao.instituicao_id == current_user.id,
            SolicitacaoRecebimento.status == 'entregue'
        ).scalar() or 0.0
        
        total_monetario = db.session.query(
            db.func.sum(SolicitacaoRecebimento.valor_entregue)
        ).join(
            Delegacao,
            Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
        ).filter(
            Delegacao.instituicao_id == current_user.id,
            SolicitacaoRecebimento.status == 'entregue'
        ).scalar() or 0.0
        
        projetos_ajudados = SolicitacaoRecebimento.query.join(
            Delegacao,
            Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id
        ).filter(
            Delegacao.instituicao_id == current_user.id,
            SolicitacaoRecebimento.status == 'entregue'
        ).count()
        
        campanhas_pendentes = Campanha.query.filter_by(
            instituicao_id=current_user.id,
            status='pendente'
        ).all()
        
        campanhas_ativas = Campanha.query.filter_by(
            instituicao_id=current_user.id,
            status='ativa'
        ).all()
        
        return render_template('perfil_instituicao.html', 
                                delegacoes_pendentes=delegacoes_pendentes, 
                                delegacoes_aceitas=delegacoes_aceitas,
                                campanhas_pendentes=campanhas_pendentes,
                                campanhas_ativas=campanhas_ativas,
                                usuario=current_user,
                                total_cestas=total_cestas,
                                total_kg=total_kg_alimentos,
                                total_monetario=total_monetario,
                                projetos_ajudados=projetos_ajudados)
    
    doacoes = SolicitacaoDoacao.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoDoacao.data_criacao.desc()).all()
    recebimentos = SolicitacaoRecebimento.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    
    return render_template('perfil.html', doacoes=doacoes, recebimentos=recebimentos, usuario=current_user)

@app.route('/aceitar_delegacao/<int:delegacao_id>')
@login_required
def aceitar_delegacao(delegacao_id):
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))

    delegacao = Delegacao.query.get_or_404(delegacao_id)
    
    if delegacao.instituicao_id != current_user.id:
        flash('Você não tem permissão para aceitar esta delegação.', 'error')
        return redirect(url_for('solicitacoes_instituicao'))
    
    delegacao.status = 'aceita'
    
    if delegacao.solicitacao_doacao_id:
        solicitacao = SolicitacaoDoacao.query.get(delegacao.solicitacao_doacao_id)
        if solicitacao:
            solicitacao.status = 'aceita'
    elif delegacao.solicitacao_recebimento_id:
        solicitacao = SolicitacaoRecebimento.query.get(delegacao.solicitacao_recebimento_id)
        if solicitacao:
            solicitacao.status = 'aceita'
    
    try:
        db.session.commit()
        flash('Solicitação aceita com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao aceitar solicitação.', 'error')
    
    return redirect(url_for('solicitacoes_instituicao'))

@app.route('/aceitar_campanha/<int:campanha_id>')
@login_required
def aceitar_campanha(campanha_id):
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)
    
    if campanha.instituicao_id != current_user.id:
        flash('Você não tem permissão para aceitar esta campanha.', 'error')
        return redirect(url_for('solicitacoes_instituicao'))
    
    campanha.status = 'ativa'
    
    try:
        db.session.commit()
        flash(f'Campanha "{campanha.titulo}" aceita e ativada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao aceitar campanha.', 'error')
    
    return redirect(url_for('solicitacoes_instituicao'))

@app.route('/recusar_campanha/<int:campanha_id>')
@login_required
def recusar_campanha(campanha_id):
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    campanha = Campanha.query.get_or_404(campanha_id)
    
    if campanha.instituicao_id != current_user.id:
        flash('Você não tem permissão para recusar esta campanha.', 'error')
        return redirect(url_for('solicitacoes_instituicao'))
    
    campanha.status = 'pendente'
    campanha.instituicao_id = None
    
    try:
        db.session.commit()
        flash(f'Campanha "{campanha.titulo}" recusada. Ela retornou para o painel de moderação.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao recusar campanha.', 'error')
    
    return redirect(url_for('solicitacoes_instituicao'))

@app.route('/recusar_delegacao/<int:delegacao_id>')
@login_required
def recusar_delegacao(delegacao_id):
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
        
    delegacao = Delegacao.query.get_or_404(delegacao_id)
    
    if delegacao.instituicao_id != current_user.id:
        flash('Você não tem permissão para recusar esta delegação.', 'error')
        return redirect(url_for('solicitacoes_instituicao'))
    
    delegacao.status = 'recusada'

    if delegacao.solicitacao_doacao_id:
        solicitacao = SolicitacaoDoacao.query.get(delegacao.solicitacao_doacao_id)
        if solicitacao:
            solicitacao.status = 'pendente'
    elif delegacao.solicitacao_recebimento_id:
        solicitacao = SolicitacaoRecebimento.query.get(delegacao.solicitacao_recebimento_id)
        if solicitacao:
            solicitacao.status = 'pendente'

    try:
        db.session.commit()
        flash('Solicitação recusada. Ela retornou para o painel de moderação.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao recusar solicitação.', 'error')
    
    return redirect(url_for('solicitacoes_instituicao'))
    
@app.route('/reportar_entrega/<int:delegacao_id>', methods=['POST'])
@login_required
def reportar_entrega(delegacao_id):
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))

    delegacao = Delegacao.query.get_or_404(delegacao_id)
    
    if delegacao.instituicao_id != current_user.id:
        flash('Você não tem permissão para reportar esta entrega.', 'error')
        return redirect(url_for('solicitacoes_instituicao'))

    cestas_entregues = int(request.form.get('cestas_entregues', 0))
    alimento_kg_entregues = float(request.form.get('alimento_kg_entregues', 0.0))
    valor_entregue = float(request.form.get('valor_entregue', 0.0))

    if delegacao.solicitacao_recebimento_id:
        recebimento = SolicitacaoRecebimento.query.get(delegacao.solicitacao_recebimento_id)
        if recebimento:
            recebimento.cestas_entregues = cestas_entregues
            recebimento.alimento_kg_entregues = alimento_kg_entregues
            recebimento.valor_entregue = valor_entregue
            recebimento.data_entrega_final = datetime.utcnow()
            recebimento.status = 'entregue'
            delegacao.status = 'concluida'
            
            try:
                db.session.commit()
                flash('Entrega reportada com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Erro ao reportar entrega.', 'error')
        else:
            flash('Solicitação de recebimento não encontrada.', 'error')
    else:
        flash('Não foi possível reportar a entrega.', 'error')

    return redirect(url_for('solicitacoes_instituicao'))

@app.route('/cancelar_solicitacao/<string:tipo>/<int:id>', methods=['POST'])
@login_required
def cancelar_solicitacao(tipo, id):
    item = None
    if tipo == 'recebimento':
        item = SolicitacaoRecebimento.query.get_or_404(id)
    elif tipo == 'doacao':
        item = SolicitacaoDoacao.query.get_or_404(id)
    
    if item and item.usuario_id == current_user.id:
        if item.status == 'pendente':
            db.session.delete(item)
            db.session.commit()
            flash('Sua solicitação foi cancelada com sucesso.', 'success')
        else:
            flash('Não é possível cancelar uma solicitação que já foi processada.', 'warning')
    else:
        flash('Ação não permitida.', 'error')
        
    return redirect(url_for('minhas_solicitacoes'))

@app.route('/doar_itens_campanha/<int:campanha_id>', methods=['POST'])
@login_required
def doar_itens_campanha(campanha_id):
    campanha = Campanha.query.get_or_404(campanha_id)
    
    qtd_cestas = request.form.get('qtd_cestas', 0, type=int)
    qtd_higiene = request.form.get('qtd_higiene', 0, type=int)
    qtd_agua = request.form.get('qtd_agua', 0, type=int)
    qtd_fraldas_infantis = request.form.get('qtd_fraldas_infantis', 0, type=int)

    total_itens = qtd_cestas + qtd_higiene + qtd_agua + qtd_fraldas_infantis

    if total_itens <= 0:
        flash('Você precisa especificar a quantidade de pelo menos um item para doar.', 'warning')
        return redirect(url_for('detalhes_campanha', campanha_id=campanha_id))
    
    nova_doacao = DoacaoCampanha(
        campanha_id=campanha.id,
        usuario_id=current_user.id,
        qtd_cestas=qtd_cestas,
        qtd_higiene=qtd_higiene,
        qtd_agua=qtd_agua,
        qtd_fraldas_infantis=qtd_fraldas_infantis
    )

    db.session.add(nova_doacao)
    db.session.commit()

    flash(f'Sua doação de {total_itens} item(ns) foi registrada com sucesso!', 'success')
    return redirect(url_for('detalhes_campanha', campanha_id=campanha_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_initial_data()
        
    app.run(host='0.0.0.0', port=5000, debug=True)