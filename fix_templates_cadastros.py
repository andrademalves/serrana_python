import os
import sys

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Mapa: arquivo -> (linha_inicio, linha_fim)
templates = {
    'criar_produto.html': (765, 896),
    'listar_produtos.html': (2130, 2251),
    'editar_produto.html': (1853, 1984),
    'editar_pessoa.html': (1074, 1393),
    'dashboard.html': (899, 1071),
}

base_dir = r'cadastros\templates\cadastros'

for filename, (start, end) in templates.items():
    filepath = os.path.join(base_dir, filename)
    
    if not os.path.exists(filepath):
        print(f'Nao existe: {filename}')
        continue
    
    print(f'\n{filename}:')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f'  Total: {len(lines)} linhas')
    
    if len(lines) <= end:
        print(f'  OK - Ja esta correto')
        continue
    
    # Extrair o trecho correto
    new_lines = lines[start:end]
    print(f'  Extraindo linhas {start+1}-{end}: {len(new_lines)} linhas')
    
    # Salvar
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'  SALVO!')

print('\nConcluido!')
