import os

templates_dir = r'cadastros\templates\cadastros'

# Mapa de templates: (arquivo, linha_inicio, linha_fim, titulo_esperado)
templates_corretos = {
    'criar_pessoa.html': (0, 591, 'Nova Pessoa'),
    'listar_pessoas.html': (1985, 2129, 'Pessoas -'),
    'criar_produto.html': (763, None, 'Novo Produto'),
    'listar_produtos.html': (2130, 2251, 'Produtos -'),
    'editar_pessoa.html': (1074, None, 'Editar Pessoa'),
    'editar_produto.html': (1853, None, 'Editar Produto'),
    'dashboard.html': (899, None, 'Dashboard Cadastros'),
}

for filename, (inicio, fim, titulo) in templates_corretos.items():
    filepath = os.path.join(templates_dir, filename)
    
    if not os.path.exists(filepath):
        print(f'❌ Arquivo não existe: {filename}')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_linhas = len(lines)
    print(f'\n📄 {filename}: {total_linhas} linhas')
    
    # Verificar se precisa corrigir
    if total_linhas > 1000:  # Provavelmente está com conteúdo duplicado
        print(f'   ⚠️  Arquivo grande demais, extraindo linhas {inicio+1}-{fim if fim else "final"}...')
        
        if fim:
            new_lines = lines[inicio:fim]
        else:
            new_lines = lines[inicio:]
        
        # Verificar se tem o título esperado
        titulo_encontrado = any(titulo in line for line in new_lines[:10])
        
        if titulo_encontrado:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f'   ✅ Corrigido: {len(new_lines)} linhas')
        else:
            print(f'   ❌ Título esperado não encontrado: {titulo}')
    else:
        # Verificar se tem o título correto
        titulo_encontrado = any(titulo in line for line in lines[:10])
        if titulo_encontrado:
            print(f'   ✅ OK')
        else:
            print(f'   ⚠️  Título não encontrado, mas tamanho OK')

print('\n✅ Processo concluído!')
