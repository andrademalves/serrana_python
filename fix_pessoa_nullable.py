"""
Script para alterar a coluna pessoa_id para aceitar NULL
"""
import os
import django
import MySQLdb

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.conf import settings

# Pegar credenciais do settings
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
    print("Verificando constraints existentes...")
    cursor.execute("""
        SELECT CONSTRAINT_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'titulos_financeiros' 
        AND COLUMN_NAME = 'pessoa_id'
        AND CONSTRAINT_NAME LIKE 'titulos_financeiros%%'
    """, (db_settings['NAME'],))
    
    constraints = cursor.fetchall()
    
    # Remover constraint se existir
    for constraint in constraints:
        constraint_name = constraint[0]
        if 'fk' in constraint_name.lower() or 'ibfk' in constraint_name.lower():
            print(f"Removendo constraint: {constraint_name}")
            cursor.execute(f"ALTER TABLE titulos_financeiros DROP FOREIGN KEY {constraint_name}")
    
    print("Alterando coluna pessoa_id para aceitar NULL...")
    cursor.execute("ALTER TABLE titulos_financeiros MODIFY COLUMN pessoa_id BIGINT NULL")
    
    print("Recriando foreign key constraint...")
    cursor.execute("""
        ALTER TABLE titulos_financeiros 
        ADD CONSTRAINT titulos_financeiros_pessoa_fk 
        FOREIGN KEY (pessoa_id) REFERENCES pessoas(id) 
        ON DELETE RESTRICT
    """)
    
    conn.commit()
    print("\n✅ Coluna pessoa_id alterada com sucesso!")
    print("Agora execute: python manage.py migrate financeiro --fake 0004")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro: {e}")
    print("\nTentando abordagem alternativa...")
    
    try:
        # Tentar sem remover constraint primeiro
        cursor.execute("ALTER TABLE titulos_financeiros MODIFY COLUMN pessoa_id BIGINT NULL")
        conn.commit()
        print("✅ Coluna alterada com sucesso!")
        print("Agora execute: python manage.py migrate financeiro --fake 0004")
    except Exception as e2:
        conn.rollback()
        print(f"❌ Erro na alternativa: {e2}")

finally:
    cursor.close()
    conn.close()
