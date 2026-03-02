"""
Script para adicionar campo primeiro_atendente na model Oportunidade
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.db import connection

print("=" * 80)
print("ADICIONAR CAMPO primeiro_atendente EM OPORTUNIDADE")
print("=" * 80)

# SQL para adicionar campo primeiro_atendente
sql = """
ALTER TABLE crm_oportunidade 
ADD COLUMN primeiro_atendente_id INT NULL,
ADD CONSTRAINT fk_oportunidade_primeiro_atendente 
    FOREIGN KEY (primeiro_atendente_id) 
    REFERENCES auth_user(id) 
    ON DELETE SET NULL;
"""

sql_index = """
CREATE INDEX idx_oportunidade_primeiro_atendente 
ON crm_oportunidade(primeiro_atendente_id);
"""

# Atualizar registros existentes: primeiro_atendente = responsavel atual
sql_update = """
UPDATE crm_oportunidade 
SET primeiro_atendente_id = responsavel_id 
WHERE primeiro_atendente_id IS NULL;
"""

try:
    with connection.cursor() as cursor:
        print("\n📝 Adicionando campo primeiro_atendente_id...")
        cursor.execute(sql)
        print("✅ Campo adicionado com sucesso!")
        
        print("\n📝 Criando índice...")
        cursor.execute(sql_index)
        print("✅ Índice criado com sucesso!")
        
        print("\n📝 Atualizando oportunidades existentes...")
        cursor.execute(sql_update)
        affected_rows = cursor.rowcount
        print(f"✅ {affected_rows} oportunidades atualizadas!")
        
    print("\n✅ CONCLUÍDO!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print("\nSe o campo já existe, ignore este erro.")
    print("=" * 80)
