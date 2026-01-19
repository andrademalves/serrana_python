#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from usuarios.models import Modulo, Menu

print("=== DEBUG: Testando view modulos() ===\n")

client = Client()
admin = User.objects.get(username='admin')

# Test 1: Com sessão limpa
print("TESTE 1: Acessando /usuarios/ (sessão limpa)")
client.force_login(admin)
session = client.session
session.clear()
session.save()

response = client.get('/usuarios/')
print(f"Status: {response.status_code}")

# Salvar HTML para análise
with open('/tmp/modulos_output.html', 'w') as f:
    f.write(response.content.decode('utf-8'))

# Contar ocorrências
html = response.content.decode('utf-8')
print(f"Tamanho do HTML: {len(html)} bytes")
print(f"'{% if modulos %}' encontrado: {'{% if modulos %}' in html}")
print(f"'module-card' encontrado: {'module-card' in html}")
print(f"'Nenhum módulo disponível' encontrado: {'Nenhum módulo disponível' in html}")
print(f"'empty-state' encontrado: {'empty-state' in html}")

print("\nArquivo salvo em: /tmp/modulos_output.html")
print("Analise o HTML para ver o que foi renderizado.")

# Verificar o que o banco retorna
print("\n=== Dados do Banco ===")
modulos_db = Modulo.objects.filter(ativo=True).count()
print(f"Módulos ativos: {modulos_db}")

menus_db = Menu.objects.filter(ativo=True, menu_pai__isnull=True).count()
print(f"Menus raiz ativos: {menus_db}")
