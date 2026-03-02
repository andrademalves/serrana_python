"""
Script para adicionar campo usuario na model Pessoa
e permitir vincular vendedores a usuários do sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.db import connection

print("=" * 80)
print("ADICIONAR CAMPO USUARIO EM PESSOA")
print("=" * 80)

# SQL para adicionar campo usuario (OneToOne com User)
sql = """
ALTER TABLE cadastros_pessoa 
ADD COLUMN usuario_id INT NULL,
ADD CONSTRAINT fk_pessoa_usuario 
    FOREIGN KEY (usuario_id) 
    REFERENCES auth_user(id) 
    ON DELETE SET NULL;
"""

sql_index = """
CREATE UNIQUE INDEX idx_pessoa_usuario 
ON cadastros_pessoa(usuario_id) 
WHERE usuario_id IS NOT NULL;
"""

try:
    with connection.cursor() as cursor:
        print("\n📝 Adicionando campo usuario_id...")
        cursor.execute(sql)
        print("✅ Campo usuario_id adicionado com sucesso!")
        
        print("\n📝 Criando índice único...")
        cursor.execute(sql_index)
        print("✅ Índice criado com sucesso!")
        
    print("\n✅ CONCLUÍDO!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print("\nSe o campo já existe, ignore este erro.")
    print("=" * 80)
