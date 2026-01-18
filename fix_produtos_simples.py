# Corrigir listar_produtos.html
with open(r'cadastros\templates\cadastros\listar_produtos.html', 'r', encoding='utf-8') as f:
    all_lines = f.readlines()

print(f'Total original: {len(all_lines)}')

# Extrair linhas 2131-2251 (índices 2130-2250 inclusive)
correct_lines = all_lines[2130:2251]

print(f'Linhas extraídas: {len(correct_lines)}')
print(f'Primeira: {correct_lines[0].strip()}')

with open(r'cadastros\templates\cadastros\listar_produtos.html', 'w', encoding='utf-8') as f:
    f.writelines(correct_lines)

print('Salvo!')

# Verificar
with open(r'cadastros\templates\cadastros\listar_produtos.html', 'r', encoding='utf-8') as f:
    verify = f.readlines()

print(f'Verificação: {len(verify)} linhas')
print(f'Primeira linha: {verify[0].strip()}')
print(f'Título correto: {"Produtos" in verify[2]}')
