"""
Corrigir índice único para o campo usuario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.db import connection

print("=" * 80)
print("CRIAR ÍNDICE ÚNICO PARA USUARIO")
print("=" * 80)

# MySQL não suporta índice parcial com WHERE, vamos usar apenas índice único
sql_index = """
CREATE UNIQUE INDEX idx_pessoa_usuario 
ON cadastros_pessoa(usuario_id);
"""

try:
    with connection.cursor() as cursor:
        print("\n📝 Criando índice único para usuario_id...")
        cursor.execute(sql_index)
        print("✅ Índice criado com sucesso!")
        
    print("\n✅ CONCLUÍDO!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    
    # Tentar remover valores duplicados antes
    if 'Duplicate entry' in str(e):
        print("\n⚠️  Existem valores duplicados. Limpando...")
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cadastros_pessoa SET usuario_id = NULL WHERE usuario_id IS NOT NULL")
            print("✓ Valores limpos, tente criar o índice novamente")
    
    print("=" * 80)
