from main import app
from models import Campanha, Usuario
from db import db

with app.app_context():
    print("\n" + "="*70)
    print("DEBUG: CAMPANHAS NO BANCO DE DADOS")
    print("="*70)
    
    todas_campanhas = Campanha.query.all()
    print(f"\n📊 Total de campanhas: {len(todas_campanhas)}")
    
    if todas_campanhas:
        print("\n📋 Listagem de todas as campanhas:")
        print("-" * 70)
        for c in todas_campanhas:
            print(f"ID: {c.id}")
            print(f"Título: {c.titulo}")
            print(f"Status: {c.status}")
            print(f"Solicitante ID: {c.solicitante_id}")
            if c.solicitante:
                print(f"Solicitante Nome: {c.solicitante.nome}")
            print(f"Instituição ID: {c.instituicao_id}")
            if c.instituicao_delegada:
                print(f"Instituição Nome: {c.instituicao_delegada.instituicao_nome}")
            print("-" * 70)
    
    campanhas_pendentes = Campanha.query.filter_by(status='pendente').all()
    print(f"\n⏳ Campanhas PENDENTES: {len(campanhas_pendentes)}")
    
    if campanhas_pendentes:
        for c in campanhas_pendentes:
            print(f"  - ID {c.id}: {c.titulo}")
    else:
        print("  Nenhuma campanha pendente encontrada.")
    
    campanhas_ativas = Campanha.query.filter_by(status='ativa').all()
    print(f"\n✅ Campanhas ATIVAS: {len(campanhas_ativas)}")
    
    print("\n" + "="*70)
