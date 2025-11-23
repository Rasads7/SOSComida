from main import app
from models import Campanha, Usuario
from db import db

with app.app_context():
    print("\n" + "="*70)
    print("TESTE: CRIANDO CAMPANHA PENDENTE")
    print("="*70)
    
    # Buscar usuário
    usuario = Usuario.query.filter_by(email='exemplo@email.com').first()
    
    if not usuario:
        print("❌ Usuário não encontrado!")
    else:
        # Criar campanha de teste
        nova_campanha = Campanha(
            titulo="TESTE - Campanha Automática",
            descricao="Esta é uma campanha de teste para verificar se o status pendente é mantido.",
            localizacao="Teste, TS",
            meta_voluntarios=10,
            meta_doacoes=1000.00,
            imagem='campanha_default.jpg',
            status='pendente',
            solicitante_id=usuario.id
        )
        
        print(f"\n✅ Criando campanha com status: {nova_campanha.status}")
        
        db.session.add(nova_campanha)
        db.session.commit()
        
        print(f"✅ Campanha salva no banco. ID: {nova_campanha.id}")
        
        # Verificar se o status foi mantido
        campanha_salva = Campanha.query.get(nova_campanha.id)
        print(f"\n🔍 Verificação após commit:")
        print(f"   Status atual: {campanha_salva.status}")
        print(f"   Solicitante ID: {campanha_salva.solicitante_id}")
        
        if campanha_salva.status == 'pendente':
            print("✅ STATUS CORRETO - Campanha ficou pendente!")
        else:
            print(f"❌ ERRO - Status mudou para: {campanha_salva.status}")
    
    print("\n" + "="*70)
    print("CAMPANHAS PENDENTES NO BANCO:")
    print("="*70)
    
    pendentes = Campanha.query.filter_by(status='pendente').all()
    print(f"Total: {len(pendentes)}")
    for c in pendentes:
        print(f"  - ID {c.id}: {c.titulo} (Solicitante: {c.solicitante.nome if c.solicitante else 'N/A'})")
    
    print("="*70 + "\n")
