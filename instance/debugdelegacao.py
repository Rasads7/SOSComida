from main import app, db
from models import Usuario, Delegacao, SolicitacaoRecebimento, SolicitacaoDoacao

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def verificar_delegacoes():
    print_header("🔍 VERIFICANDO TODAS AS DELEGAÇÕES NO BANCO")
    
    todas_delegacoes = Delegacao.query.all()
    
    print(f"\n📊 Total de delegações no banco: {len(todas_delegacoes)}")
    
    if len(todas_delegacoes) == 0:
        print("\n❌ PROBLEMA: Nenhuma delegação encontrada no banco!")
        print("   Isso significa que a delegação não foi salva.")
        return False
    
    print("\n📋 Detalhes de cada delegação:")
    for i, del_ in enumerate(todas_delegacoes, 1):
        print(f"\n--- Delegação #{i} ---")
        print(f"ID: {del_.id}")
        print(f"Moderador ID: {del_.moderador_id}")
        print(f"Instituição ID: {del_.instituicao_id}")
        print(f"Status: {del_.status}")
        print(f"Data: {del_.data_delegacao}")
        print(f"Solicitação Doação ID: {del_.solicitacao_doacao_id}")
        print(f"Solicitação Recebimento ID: {del_.solicitacao_recebimento_id}")

        if del_.instituicao_id:
            instituicao = Usuario.query.get(del_.instituicao_id)
            if instituicao:
                print(f"✅ Instituição: {instituicao.instituicao_nome} (Tipo: {instituicao.tipo})")
            else:
                print(f"❌ PROBLEMA: Instituição ID {del_.instituicao_id} não existe!")
        else:
            print("❌ PROBLEMA: instituicao_id está NULL!")

        if del_.moderador:
            print(f"✅ Moderador carregado: {del_.moderador.nome}")
        else:
            print("❌ PROBLEMA: Moderador não carregado!")
        
        if del_.instituicao:
            print(f"✅ Instituição carregada: {del_.instituicao.instituicao_nome}")
        else:
            print("❌ PROBLEMA: Instituição não carregada!")
        
        if del_.doacao:
            print(f"✅ Doação carregada: {del_.doacao.nome_doador}")
        elif del_.recebimento:
            print(f"✅ Recebimento carregado: {del_.recebimento.nome}")
        else:
            print("❌ PROBLEMA: Nenhuma solicitação carregada!")
    
    return True

def verificar_instituicoes():
    print_header("🏢 VERIFICANDO INSTITUIÇÕES")
    
    todas_instituicoes = Usuario.query.filter_by(tipo='instituicao').all()
    
    print(f"\n📊 Total de instituições: {len(todas_instituicoes)}")
    
    for inst in todas_instituicoes:
        print(f"\n--- Instituição ---")
        print(f"ID: {inst.id}")
        print(f"Nome: {inst.instituicao_nome}")
        print(f"Email: {inst.email}")
        print(f"Status: {inst.status_aprovacao}")
        print(f"Tipo: {inst.tipo}")
        
        delegacoes = Delegacao.query.filter_by(instituicao_id=inst.id).all()
        print(f"Delegações para esta instituição: {len(delegacoes)}")
        
        if len(delegacoes) > 0:
            for d in delegacoes:
                print(f"  → Delegação #{d.id} - Status: {d.status}")

def verificar_query_instituicao(instituicao_id):
    print_header(f"🔎 SIMULANDO QUERY PARA INSTITUIÇÃO ID {instituicao_id}")

    delegacoes = Delegacao.query.filter_by(
        instituicao_id=instituicao_id
    ).all()
    
    print(f"\n📊 Resultado da query: {len(delegacoes)} delegação(ões)")
    
    if len(delegacoes) == 0:
        print("\n❌ PROBLEMA: A query não retornou nenhuma delegação!")
        print("   Possíveis causas:")
        print("   1. instituicao_id está NULL na tabela delegacoes")
        print("   2. instituicao_id tem valor diferente do esperado")
        print("   3. A delegação não foi commitada no banco")
    else:
        print("\n✅ Query funcionou! Delegações encontradas:")
        for d in delegacoes:
            print(f"   → Delegação #{d.id} - Status: {d.status}")

def verificar_status_solicitacoes():
    print_header("📝 VERIFICANDO STATUS DAS SOLICITAÇÕES")
    
    recebimentos_delegados = SolicitacaoRecebimento.query.filter_by(status='delegada').all()
    
    print(f"\n📊 Solicitações de recebimento com status 'delegada': {len(recebimentos_delegados)}")
    
    for rec in recebimentos_delegados:
        print(f"\n--- Solicitação #{rec.id} ---")
        print(f"Nome: {rec.nome}")
        print(f"Status: {rec.status}")

        delegacao = Delegacao.query.filter_by(solicitacao_recebimento_id=rec.id).first()
        if delegacao:
            print(f"✅ Tem delegação: ID {delegacao.id}")
            print(f"   Instituição ID: {delegacao.instituicao_id}")
            print(f"   Status delegação: {delegacao.status}")
        else:
            print(f"❌ PROBLEMA: Marcada como 'delegada' mas sem registro em Delegacao!")

def executar_query_sql():
    print_header("💾 EXECUTANDO QUERY SQL DIRETA")
    
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            d.id as delegacao_id,
            d.moderador_id,
            d.instituicao_id,
            d.status,
            d.solicitacao_recebimento_id,
            u.instituicao_nome,
            sr.nome as solicitacao_nome
        FROM delegacoes d
        LEFT JOIN usuarios u ON d.instituicao_id = u.id
        LEFT JOIN solicitacoes_recebimento sr ON d.solicitacao_recebimento_id = sr.id
    """)
    
    result = db.session.execute(query)
    rows = result.fetchall()
    
    print(f"\n📊 Resultado da query SQL: {len(rows)} linha(s)")
    
    if len(rows) == 0:
        print("\n❌ Nenhuma delegação encontrada na query SQL!")
    else:
        print("\n✅ Delegações encontradas:")
        for row in rows:
            print(f"\n--- Delegação #{row[0]} ---")
            print(f"Moderador ID: {row[1]}")
            print(f"Instituição ID: {row[2]}")
            print(f"Status: {row[3]}")
            print(f"Recebimento ID: {row[4]}")
            print(f"Instituição Nome: {row[5] if row[5] else '❌ NULL'}")
            print(f"Solicitação Nome: {row[6] if row[6] else '❌ NULL'}")

def sugerir_solucoes():
    print_header("💡 SOLUÇÕES POSSÍVEIS")
    
    print("""
Se as delegações não aparecem para a instituição, verifique:

1️⃣  PROBLEMA: instituicao_id está NULL
   SOLUÇÃO: 
   - Verifique se o models.py tem nullable=False
   - Execute: rm instance/database.db
   - Execute: python teste_delegacao.py
   - Execute: python main.py

2️⃣  PROBLEMA: Delegação não foi salva no banco
   SOLUÇÃO:
   - Verifique os logs do Flask ao delegar
   - Deve aparecer: "✅ Delegação criada com sucesso!"
   - Se não aparecer, há um erro antes do commit

3️⃣  PROBLEMA: Relacionamento não está carregando
   SOLUÇÃO:
   - Verifique se models.py tem lazy='joined'
   - Reinstale o banco de dados

4️⃣  PROBLEMA: Query está incorreta
   SOLUÇÃO:
   - Use a rota /instituicao/solicitacoes
   - Não use /perfil para ver delegações

5️⃣  PROBLEMA: Cache do navegador
   SOLUÇÃO:
   - Aperte Ctrl+Shift+R no navegador
   - Ou abra em aba anônima
    """)

def criar_delegacao_teste():
    print_header("🔧 CRIAR DELEGAÇÃO DE TESTE")
    
    resposta = input("\nDeseja criar uma delegação de teste agora? (s/n): ")
    
    if resposta.lower() != 's':
        return

    moderador = Usuario.query.filter_by(tipo='moderador').first()
    instituicao = Usuario.query.filter_by(tipo='instituicao', status_aprovacao='aprovada').first()
    usuario = Usuario.query.filter_by(tipo='usuario').first()
    
    if not all([moderador, instituicao, usuario]):
        print("\n❌ Faltam usuários necessários!")
        return
    
    print(f"\n✅ Moderador: {moderador.nome} (ID: {moderador.id})")
    print(f"✅ Instituição: {instituicao.instituicao_nome} (ID: {instituicao.id})")
    print(f"✅ Usuário: {usuario.nome} (ID: {usuario.id})")

    solicitacao = SolicitacaoRecebimento(
        usuario_id=usuario.id,
        nome='TESTE DEBUG',
        telefone='(11) 99999-9999',
        endereco='Rua Debug, 123',
        qtd_pessoas=3,
        necessidades='Solicitação de teste para debug',
        qtd_cestas=2,
        status='pendente'
    )
    
    db.session.add(solicitacao)
    db.session.flush()
    
    print(f"\n✅ Solicitação criada: ID {solicitacao.id}")

    delegacao = Delegacao(
        moderador_id=moderador.id,
        instituicao_id=instituicao.id,
        solicitacao_recebimento_id=solicitacao.id,
        status='pendente'
    )
    
    solicitacao.status = 'delegada'
    
    db.session.add(delegacao)
    db.session.commit()
    
    print(f"\n✅ Delegação criada: ID {delegacao.id}")
    print(f"   Moderador ID: {delegacao.moderador_id}")
    print(f"   Instituição ID: {delegacao.instituicao_id}")
    print(f"   Status: {delegacao.status}")

    del_verificacao = Delegacao.query.get(delegacao.id)
    print(f"\n🔍 Verificação no banco:")
    print(f"   Encontrada? {del_verificacao is not None}")
    if del_verificacao:
        print(f"   Instituição ID: {del_verificacao.instituicao_id}")
        print(f"   Tem instituição carregada? {del_verificacao.instituicao is not None}")
        if del_verificacao.instituicao:
            print(f"   Nome instituição: {del_verificacao.instituicao.instituicao_nome}")
    
    print(f"\n✅ TESTE CONCLUÍDO!")
    print(f"\n📋 Para ver a delegação:")
    print(f"   1. Login: {instituicao.email} / senha: 1234")
    print(f"   2. Acesse: http://127.0.0.1:5000/instituicao/solicitacoes")
    print(f"   3. A delegação #TESTE DEBUG deve aparecer")

def main():
    with app.app_context():
        print("\n" + "🔍 DIAGNÓSTICO COMPLETO DE DELEGAÇÕES".center(70))
        print("="*70)
        
        try:
            if not verificar_delegacoes():
                print("\n⚠️  ATENÇÃO: Nenhuma delegação encontrada!")
                print("   A delegação não foi salva no banco de dados.")
                criar_delegacao_teste()
                return

            verificar_instituicoes()

            executar_query_sql()

            verificar_status_solicitacoes()

            print("\n" + "-"*70)
            instituicoes = Usuario.query.filter_by(
                tipo='instituicao',
                status_aprovacao='aprovada'
            ).all()
            
            if instituicoes:
                print("\n📋 Testando query para cada instituição:")
                for inst in instituicoes:
                    verificar_query_instituicao(inst.id)

            sugerir_solucoes()

            criar_delegacao_teste()
            
        except Exception as e:
            print(f"\n❌ ERRO durante diagnóstico:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()