"""
Script para adicionar campo intervalos_personalizados
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
    print("Adicionando campo intervalos_personalizados...")
    cursor.execute("""
        ALTER TABLE titulos_financeiros 
        ADD COLUMN intervalos_personalizados VARCHAR(200) NULL 
        AFTER intervalo_dias
    """)
    
    conn.commit()
    print("\n✅ Campo intervalos_personalizados adicionado com sucesso!")
    print("Agora execute: python manage.py migrate financeiro --fake 0006")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro: {e}")

finally:
    cursor.close()
    conn.close()
