"""
Script para adicionar campo data_primeiro_vencimento
"""
import os
import django
import MySQLdb

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.conf import settings

db_settings = settings.DATABASES['default']

print("Conectando ao banco de dados...")
conn = MySQLdb.connect(
    host=db_settings['HOST'],
    user=db_settings['USER'],
    passwd=db_settings['PASSWORD'],
    db=db_settings['NAME']
)

cursor = conn.cursor()

try:
    print("Adicionando campo data_primeiro_vencimento...")
    cursor.execute("""
        ALTER TABLE titulos_financeiros 
        ADD COLUMN data_primeiro_vencimento DATE NULL 
        AFTER data_emissao
    """)
    
    conn.commit()
    print("\n✅ Campo data_primeiro_vencimento adicionado com sucesso!")
    print("Agora execute: python manage.py migrate financeiro --fake 0005")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro: {e}")

finally:
    cursor.close()
    conn.close()
