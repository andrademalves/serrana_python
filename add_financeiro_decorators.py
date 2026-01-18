import re

# Ler o arquivo
with open('financeiro/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Padrão para encontrar funções com @login_required mas sem verificar_permissao_menu
# Procura por @login_required seguido de def nome_funcao sem ter @verificar_permissao ou @require_empresa antes
pattern = r'(@login_required\n)(def \w+\(request)'

# Substituir adicionando os decorators necessários
def add_decorators(match):
    login_decorator = match.group(1)
    func_def = match.group(2)
    
    # Adicionar os decorators antes do @login_required
    return f"@login_required\n@require_empresa\n@verificar_permissao_menu('/financeiro/')\n{func_def}"

# Aplicar a substituição
new_content = re.sub(pattern, add_decorators, content)

# Salvar o arquivo modificado
with open('financeiro/views.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Decorators adicionados em todas as views do financeiro!")
print("⚠️ IMPORTANTE: Revise o arquivo para garantir que não haja duplicatas")
