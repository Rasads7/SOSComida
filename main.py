from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_cors import CORS
from models import Usuario, SolicitacaoDoacao, SolicitacaoRecebimento, Campanha, VoluntarioCampanha, Delegacao
from db import db
import hashlib
import os
from datetime import datetime
import uuid

app = Flask(__name__)

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
    """
    Função de utilidade para gerar o hash SHA256 de uma senha.
    Isso garante que as senhas não sejam armazenadas em texto simples.
    """
    return hashlib.sha256(txt.encode('utf-8')).hexdigest()

def create_initial_data():
    """
    Função para criar dados de exemplo no banco de dados.
    Ela é executada apenas na primeira vez que a aplicação é iniciada
    ou quando o arquivo do banco de dados é recriado.
    """
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
            instituicao1 = Usuario(
                nome='ONG Amigos da Cidade',
                email='instituicao1@ongs.org',
                senha=hash_password('1234'),
                tipo='instituicao',
                instituicao_nome='ONG Amigos da Cidade',
                instituicao_endereco='Rua da Esperança, 123',
                instituicao_cep='01234-567',
                instituicao_tipo='privada'
            )
            instituicao2 = Usuario(
                nome='Prefeitura de Ajuda Alimentar',
                email='instituicao2@prefeitura.gov.br',
                senha=hash_password('1234'),
                tipo='instituicao',
                instituicao_nome='Prefeitura de Ajuda Alimentar',
                instituicao_endereco='Av. Principal, 500',
                instituicao_cep='76543-210',
                instituicao_tipo='publica'
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

            db.session.add_all([moderador, instituicao1, instituicao2, usuario_exemplo])
            db.session.commit()
            print("Usuários e instituições de exemplo criados com sucesso.")

        if not Campanha.query.first():
            print("Criando campanhas de exemplo...")
            campanhas = [
                Campanha(
                    titulo="Natal Solidário 2024",
                    descricao="Campanha para arrecadar cestas básicas e brinquedos para famílias carentes durante o período natalino. Sua doação pode fazer a diferença na vida de muitas pessoas.",
                    localizacao="São Paulo, SP",
                    meta_voluntarios=25,
                    meta_doacoes=5000.00,
                    arrecadado=1250.00,
                    imagem="campanha1.jpg",
                    status="ativa"
                ),
                Campanha(
                    titulo="Alimentação Escolar",
                    descricao="Projeto para garantir alimentação adequada para crianças em escolas públicas. Ajude a combater a fome infantil e promover o desenvolvimento educacional.",
                    localizacao="Rio de Janeiro, RJ",
                    meta_voluntarios=15,
                    meta_doacoes=3000.00,
                    arrecadado=800.00,
                    imagem="campanha2.jpg",
                    status="ativa"
                ),
                Campanha(
                    titulo="Refeições Comunitárias",
                    descricao="Distribuição de refeições nutritivas para pessoas em situação de vulnerabilidade social. Juntos podemos garantir que ninguém passe fome.",
                    localizacao="Belo Horizonte, MG",
                    meta_voluntarios=20,
                    meta_doacoes=4000.00,
                    arrecadado=2100.00,
                    imagem="campanha3.jpg",
                    status="ativa"
                )
            ]
            db.session.add_all(campanhas)
            db.session.commit()
            print("Campanhas de exemplo criadas com sucesso.")

        if not SolicitacaoRecebimento.query.first():
            print("Criando solicitações de exemplo para moderação e doação...")

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
                    SolicitacaoRecebimento(
                        usuario_id=usuario_exemplo.id, nome='Família Santos', telefone='(11) 99333-4444', 
                        endereco='Travessa da Paz, 10, Bairro Esperança, São Paulo', qtd_pessoas=5, 
                        necessidades='Feijão, Macarrão, Óleo', status='aprovada'
                    )
                ]
                
                solicitacao_pendente = SolicitacaoRecebimento(
                    usuario_id=usuario_exemplo.id, nome='Família Pereira', telefone='(11) 99888-7777', 
                    endereco='Rua da Solidariedade, 50, Bairro Centro, São Paulo', qtd_pessoas=4, 
                    necessidades='Cesta básica e fraldas para bebê', status='pendente'
                )

                db.session.add_all(solicitacoes_aprovadas + [solicitacao_pendente])
                db.session.commit()
                print("Solicitações de exemplo criadas com sucesso.")
            else:
                print("Usuário de exemplo não encontrado. Não foi possível criar as solicitações.")
        
        print("Inicialização de dados concluída.")

@lm.user_loader
def user_loader(id):
    """
    Função obrigatória do Flask-Login para carregar um usuário
    a partir de seu ID na sessão.
    """
    return Usuario.query.get(int(id))

@app.route('/')
def home():
    """
    Rota da página inicial. Exibe um template diferente
    para usuários autenticados e não autenticados.
    """
    if current_user.is_authenticated:
        return render_template('homecomlogin.html', usuario=current_user)
    return render_template('homesemlogin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para a página de login. Processa a autenticação do usuário.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('EmailFormLogin')
        senha = request.form.get('SenhaFormLogin')
        
        user = Usuario.query.filter_by(email=email, senha=hash_password(senha)).first()
        
        if user:
            login_user(user)
            flash(f'Bem-vindo(a), {user.nome}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email ou senha incorretos', 'error')
            
    return render_template('login.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    """
    Rota para a página de registro. Permite o cadastro de pessoas ou instituições.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        tipo_cadastro = request.form.get('tipo')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        print(f"DEBUG: tipo_cadastro={tipo_cadastro}, email={email}")
        
        if not senha or len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('registrar.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'error')
            return render_template('registrar.html')
            
        if tipo_cadastro == 'pessoa':
            nome = request.form.get('nome')
            if not nome or len(nome) < 2:
                flash('Nome deve ter pelo menos 2 caracteres.', 'error')
                return render_template('registrar.html')
                
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha=hash_password(senha),
                telefone=request.form.get('telefone'),
                endereco=request.form.get('endereco', ''),
                tipo='usuario'
            )
            flash_msg = f'Cadastro de pessoa física realizado com sucesso! Bem-vindo(a), {nome}!'
            
        elif tipo_cadastro == 'instituicao':
            nome_inst = request.form.get('nome')
            if not nome_inst or len(nome_inst) < 2:
                flash('O nome da instituição deve ter pelo menos 2 caracteres.', 'error')
                return render_template('registrar.html')
                
            novo_usuario = Usuario(
                nome=nome_inst,
                email=email,
                senha=hash_password(senha),
                telefone=request.form.get('telefone'),
                endereco=request.form.get('endereco'),
                instituicao_nome=nome_inst,
                tipo='instituicao'
            )
            flash_msg = f'Cadastro da instituição "{nome_inst}" realizado com sucesso!'
            
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
            print(f"DEBUG: Erro ao salvar usuário: {e}")
            flash('Erro interno. Tente novamente.', 'error')
            return render_template('registrar.html')
        
    return render_template('registrar.html')

@app.route('/logout')
@login_required
def logout():
    """
    Rota para sair da sessão do usuário.
    """
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/formulariodoar', methods=['GET'])
@login_required
def formulariodoar():
    """
    Exibe a página para o usuário fazer uma doação a partir de
    uma lista de solicitações de recebimento aprovadas.
    """
    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem fazer doações.', 'error')
        return redirect(url_for('home'))
        
    solicitacoes = SolicitacaoRecebimento.query.filter_by(status='aprovada').order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    
    return render_template('formulariodoar.html', usuario=current_user, solicitacoes=solicitacoes)

@app.route('/doar_monetario/<int:recebimento_id>', methods=['POST'])
@login_required
def doar_monetario(recebimento_id):
    """
    Processa a doação monetária de um usuário para uma solicitação de recebimento.
    """
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
    
    flash(f'Sua doação de R${valor:.2f} foi registrada e irá ajudar a solicitação.', 'success')
    return redirect(url_for('formulariodoar'))

@app.route('/doar_item/<int:recebimento_id>', methods=['POST'])
@login_required
def doar_item(recebimento_id):
    """
    Processa a doação de itens, agendando a entrega.
    """
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
    
    flash('Sua doação foi registrada e será analisada para a entrega.', 'success')
    return redirect(url_for('formulariodoar'))


@app.route('/formularioreceber', methods=['GET', 'POST'])
@login_required  
def formularioreceber():
    """
    Permite que um usuário solicite ajuda.
    """
    if current_user.tipo != 'usuario':
        flash('Acesso negado. Apenas usuários podem solicitar ajuda.', 'error')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        nome = request.form.get('nomeAjuda')
        telefone = request.form.get('telefoneAjuda')
        endereco = request.form.get('enderecoAjuda')
        qtd_pessoas = int(request.form.get('qtdPessoasAjuda', 1))
        necessidades = request.form.get('explicarSituacaoAjuda')

        novo_recebimento = SolicitacaoRecebimento(
            usuario_id=current_user.id,
            nome=nome,
            telefone=telefone,
            endereco=endereco,
            qtd_pessoas=qtd_pessoas,
            necessidades=necessidades,
            status='pendente'
        )
        db.session.add(novo_recebimento)
        db.session.commit()
        
        flash('Sua solicitação de ajuda foi enviada para análise!', 'success')
        return redirect(url_for('minhas_solicitacoes'))
        
    return render_template('formularioreceber.html', usuario=current_user)

@app.route('/minhas_solicitacoes')
@login_required
def minhas_solicitacoes():
    """
    Exibe as solicitações feitas pelo usuário logado.
    """
    doacoes = SolicitacaoDoacao.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoDoacao.data_criacao.desc()).all()
    recebimentos = SolicitacaoRecebimento.query.filter_by(usuario_id=current_user.id).order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    
    return render_template('minhas_solicitacoes.html', doacoes=doacoes, recebimentos=recebimentos, usuario=current_user)

@app.route('/campanhas')
@login_required
def campanhas():
    """
    Exibe a lista de campanhas ativas.
    """
    campanhas_ativas = Campanha.query.filter_by(status='ativa').all()
    
    for campanha in campanhas_ativas:
        campanha.num_voluntarios = len(campanha.voluntarios)
        campanha.progresso = min(100, (float(campanha.arrecadado) / float(campanha.meta_doacoes)) * 100) if campanha.meta_doacoes > 0 else 0
        
    return render_template('campanhas.html', usuario=current_user, campanhas=campanhas_ativas)

@app.route('/detalhes_campanha/<int:campanha_id>')
@login_required
def detalhes_campanha(campanha_id):
    """
    Exibe os detalhes de uma campanha específica.
    """
    campanha = Campanha.query.get_or_404(campanha_id)
    
    # Calcular progresso
    campanha.num_voluntarios = len(campanha.voluntarios)
    campanha.progresso = min(100, (float(campanha.arrecadado) / float(campanha.meta_doacoes)) * 100) if campanha.meta_doacoes > 0 else 0

    return render_template('detalhes_campanha.html', usuario=current_user, campanha=campanha)

@app.route('/voluntariar/<int:campanha_id>')
@login_required
def voluntariar(campanha_id):
    """
    Rota para um usuário se voluntariar para uma campanha.
    """
    campanha = Campanha.query.get_or_404(campanha_id)
    if VoluntarioCampanha.query.filter_by(usuario_id=current_user.id, campanha_id=campanha_id).first():
        flash('Você já é voluntário desta campanha!', 'warning')
    else:
        novo_voluntario = VoluntarioCampanha(usuario_id=current_user.id, campanha_id=campanha_id)
        db.session.add(novo_voluntario)
        db.session.commit()
        flash(f'Parabéns! Você agora é voluntário da campanha "{campanha.titulo}"!', 'success')
    return redirect(url_for('campanhas'))

@app.route('/doar_campanha_pix/<int:campanha_id>', methods=['POST'])
@login_required
def doar_campanha_pix(campanha_id):
    """
    Processa a doação via Pix para uma campanha.
    """
    campanha = Campanha.query.get_or_404(campanha_id)
    valor = request.form.get('valor_pix')
    
    try:
        valor_doado = float(valor)
        if valor_doado <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Valor de doação inválido.', 'error')
        return redirect(url_for('campanhas'))

    campanha.arrecadado += valor_doado
    db.session.commit()

    flash(f'Sua doação de R${valor_doado:.2f} para a campanha "{campanha.titulo}" foi registrada. Muito obrigado!', 'success')
    return redirect(url_for('campanhas'))

@app.route('/moderacao')
@login_required
def moderacao():
    """
    Painel de moderação para gerenciar solicitações pendentes.
    """
    if current_user.tipo != 'moderador':
        flash('Acesso negado. Apenas moderadores podem acessar esta página.', 'error')
        return redirect(url_for('home'))
    
    doacoes_pendentes = SolicitacaoDoacao.query.filter_by(status='pendente').order_by(SolicitacaoDoacao.data_criacao.desc()).all()
    recebimentos_pendentes = SolicitacaoRecebimento.query.filter_by(status='pendente').order_by(SolicitacaoRecebimento.data_criacao.desc()).all()
    instituicoes = Usuario.query.filter_by(tipo='instituicao').all()

    return render_template('moderacao.html', 
                           doacoes_pendentes=doacoes_pendentes, 
                           recebimentos_pendentes=recebimentos_pendentes,
                           usuario=current_user, 
                           instituicoes=instituicoes)

@app.route('/rejeitar/<string:tipo>/<int:id>')
@login_required
def rejeitar_solicitacao(tipo, id):
    """
    Rota para rejeitar uma solicitação de doação ou recebimento.
    """
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    solicitacao = None
    if tipo == 'doacao':
        solicitacao = SolicitacaoDoacao.query.get_or_404(id)
    elif tipo == 'recebimento':
        solicitacao = SolicitacaoRecebimento.query.get_or_404(id)
    
    if solicitacao:
        solicitacao.status = 'rejeitada'
        db.session.commit()
        flash(f'Solicitação de {tipo} rejeitada com sucesso.', 'warning')
    else:
        flash('Tipo de solicitação inválido.', 'error')
        
    return redirect(url_for('moderacao'))

@app.route('/delegar/<string:tipo>/<int:solicitacao_id>', methods=['POST'])
@login_required
def delegar_solicitacao(tipo, solicitacao_id):
    """
    Rota para delegar uma solicitação para uma instituição.
    """
    if current_user.tipo != 'moderador':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
    
    instituicao_id = request.form.get('instituicao_id')
    if not instituicao_id:
        flash('Nenhuma instituição selecionada.', 'error')
        return redirect(url_for('moderacao'))
    
    solicitacao = None
    delegacao_params = {'moderador_id': current_user.id, 'instituicao_id': instituicao_id}
    
    if tipo == 'doacao':
        solicitacao = SolicitacaoDoacao.query.get_or_404(solicitacao_id)
        delegacao_params['solicitacao_doacao_id'] = solicitacao.id
    elif tipo == 'recebimento':
        solicitacao = SolicitacaoRecebimento.query.get_or_404(solicitacao_id)
        delegacao_params['solicitacao_recebimento_id'] = solicitacao.id
    
    if solicitacao:
        solicitacao.status = 'delegada'
        delegacao = Delegacao(**delegacao_params)
        db.session.add(delegacao)
        db.session.commit()
        flash(f'Solicitação de {tipo} delegada com sucesso para a instituição.', 'success')
    else:
        flash('Tipo de solicitação inválido.', 'error')

    return redirect(url_for('moderacao'))

@app.route('/criar_campanha', methods=['GET', 'POST'])
@login_required
def criar_campanha():
    """
    Rota para moderadores criarem novas campanhas.
    """
    if current_user.tipo != 'moderador':
        flash('Acesso negado. Apenas moderadores podem criar campanhas.', 'error')
        return redirect(url_for('campanhas'))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        localizacao = request.form.get('localizacao')
        meta_voluntarios = int(request.form.get('meta_voluntarios', 10))
        meta_doacoes = float(request.form.get('meta_doacoes', 1000.00))
        status = request.form.get('status', 'ativa')
        
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
                    arquivo.save(os.path.join(app.static_folder, imagem_nome))
        
        nova_campanha = Campanha(
            titulo=titulo, descricao=descricao, localizacao=localizacao,
            meta_voluntarios=meta_voluntarios, meta_doacoes=meta_doacoes,
            imagem=imagem_nome, status=status
        )
        db.session.add(nova_campanha)
        db.session.commit()
        
        flash(f'Campanha "{titulo}" criada com sucesso!', 'success')
        return redirect(url_for('campanhas'))
        
    return render_template('criar_campanha.html', usuario=current_user)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """
    Rota de perfil que exibe um painel diferente dependendo do tipo de usuário.
    Também permite edição de perfil via POST.
    """
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        cidade = request.form.get('cidade')
        endereco = request.form.get('endereco')
        bio = request.form.get('bio')
        
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
                    caminho_arquivo = os.path.join(app.static_folder, nome_arquivo)
                    
                    arquivo.save(caminho_arquivo)
                    
                    if current_user.foto_perfil:
                        caminho_antigo = os.path.join(app.static_folder, current_user.foto_perfil)
                        if os.path.exists(caminho_antigo):
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
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))
    if current_user.tipo == 'instituicao':
 
        delegacoes_pendentes = Delegacao.query.filter_by(instituicao_id=current_user.id, status='pendente').all()
        delegacoes_aceitas = Delegacao.query.filter_by(instituicao_id=current_user.id, status='aceita').all()

        total_cestas = db.session.query(db.func.sum(SolicitacaoRecebimento.cestas_entregues)).join(Delegacao, Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id).filter(Delegacao.instituicao_id == current_user.id, SolicitacaoRecebimento.status == 'entregue').scalar() or 0
        total_kg_alimentos = db.session.query(db.func.sum(SolicitacaoRecebimento.alimento_kg_entregues)).join(Delegacao, Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id).filter(Delegacao.instituicao_id == current_user.id, SolicitacaoRecebimento.status == 'entregue').scalar() or 0.0
        total_monetario = db.session.query(db.func.sum(SolicitacaoRecebimento.valor_entregue)).join(Delegacao, Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id).filter(Delegacao.instituicao_id == current_user.id, SolicitacaoRecebimento.status == 'entregue').scalar() or 0.0
        projetos_ajudados = SolicitacaoRecebimento.query.join(Delegacao, Delegacao.solicitacao_recebimento_id == SolicitacaoRecebimento.id).filter(Delegacao.instituicao_id == current_user.id, SolicitacaoRecebimento.status == 'entregue').count()
        
        return render_template('perfil_instituicao.html', 
                               delegacoes_pendentes=delegacoes_pendentes, 
                               delegacoes_aceitas=delegacoes_aceitas, 
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
    """
    Rota para a instituição aceitar uma solicitação delegada.
    """
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))

    delegacao = Delegacao.query.get_or_404(delegacao_id)
    delegacao.status = 'aceita'
    
    if delegacao.solicitacao_doacao_id:
        solicitacao = SolicitacaoDoacao.query.get(delegacao.solicitacao_doacao_id)
        if solicitacao:
            solicitacao.status = 'aceita'
    elif delegacao.solicitacao_recebimento_id:
        solicitacao = SolicitacaoRecebimento.query.get(delegacao.solicitacao_recebimento_id)
        if solicitacao:
            solicitacao.status = 'aceita'
    
    db.session.commit()
    flash('Solicitação aceita com sucesso!', 'success')
    return redirect(url_for('perfil'))

@app.route('/recusar_delegacao/<int:delegacao_id>')
@login_required
def recusar_delegacao(delegacao_id):
    """
    Rota para a instituição recusar uma solicitação delegada.
    """
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))
        
    delegacao = Delegacao.query.get_or_404(delegacao_id)
    delegacao.status = 'recusada'

    if delegacao.solicitacao_doacao_id:
        solicitacao = SolicitacaoDoacao.query.get(delegacao.solicitacao_doacao_id)
        if solicitacao:
            solicitacao.status = 'pendente'
    elif delegacao.solicitacao_recebimento_id:
        solicitacao = SolicitacaoRecebimento.query.get(delegacao.solicitacao_recebimento_id)
        if solicitacao:
            solicitacao.status = 'pendente'

    db.session.commit()
    flash('Solicitação delegada recusada. Ela retornou para o painel de moderação.', 'warning')
    return redirect(url_for('perfil'))
    
@app.route('/reportar_entrega/<int:delegacao_id>', methods=['POST'])
@login_required
def reportar_entrega(delegacao_id):
    """
    Rota para a instituição reportar a conclusão de uma entrega.
    """
    if current_user.tipo != 'instituicao':
        flash('Acesso negado.', 'error')
        return redirect(url_for('home'))

    delegacao = Delegacao.query.get_or_404(delegacao_id)

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
            db.session.commit()
            flash('Entrega reportada com sucesso e solicitação concluída!', 'success')
        else:
            flash('Solicitação de recebimento não encontrada.', 'error')
    else:
        flash('Não foi possível reportar a entrega. Solicitação inválida.', 'error')

    return redirect(url_for('perfil'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_initial_data()
        
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/campanhas')
def campanhas():
    campanhas_ativas = Campanha.query.filter_by(status='ativa').order_by(Campanha.data_criacao.desc()).all()
    for campanha in campanhas_ativas:
        campanha.num_voluntarios = VoluntarioCampanha.query.filter_by(campanha_id=campanha.id).count()
        campanha.progresso = (campanha.arrecadado / campanha.meta_doacoes * 100) if campanha.meta_doacoes > 0 else 0
    return render_template('campanhas.html', campanhas=campanhas_ativas, usuario=current_user if current_user.is_authenticated else None)




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
        return redirect(url_for('campanhas'))

    novo_voluntario = VoluntarioCampanha(
        usuario_id=current_user.id,
        campanha_id=campanha.id
    )
    db.session.add(novo_voluntario)
    db.session.commit()

    flash(f'Parabéns! Você agora é voluntário na campanha "{campanha.titulo}".', 'success')
    return redirect(url_for('campanhas'))