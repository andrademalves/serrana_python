# Script para corrigir o arquivo listar_produtos.html
import sys

arquivo = r'cadastros\templates\cadastros\listar_produtos.html'

print(f'Lendo {arquivo}...')
with open(arquivo, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total de linhas: {len(lines)}')
print(f'Extraindo linhas 2131-2251 (índices 2130-2250)...')

# Extrair apenas o template de produtos (linhas 2131-2251, índices 2130-2250)
new_lines = lines[2130:2251]

print(f'Linhas extraídas: {len(new_lines)}')
print(f'Primeira linha: {new_lines[0][:50]}...')
print(f'Última linha: {new_lines[-1][:50]}...')

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'✓ Arquivo salvo com {len(new_lines)} linhas')
