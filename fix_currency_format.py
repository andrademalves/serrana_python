"""
Script para substituir floatformat:2 por currency nos templates
"""
import os
import re

# Diretórios para procurar
TEMPLATE_DIRS = [
    'financeiro/templates/financeiro',
    'dashboard/templates',
]

def fix_template(filepath):
    """Fix um template individual"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    modified = False
    
    # Verifica se já tem o load financeiro_tags
    if 'financeiro_tags' not in content and '|currency' not in content:
        # Adiciona após o {% load static %} ou no início
        if '{% load static %}' in content:
            content = content.replace(
                '{% load static %}',
                '{% load static %}\n{% load financeiro_tags %}'
            )
            modified = True
        elif '{% extends' in content:
            # Adiciona após o extends
            content = re.sub(
                r'({% extends [^%]+%})',
                r'\1\n{% load financeiro_tags %}',
                content,
                count=1
            )
            modified = True
    
    # Substitui R$ {{ valor|floatformat:2 }} por {{ valor|currency }}
    # Padrão 1: R$ {{ var|floatformat:2 }}
    pattern1 = r'R\$\s*{{\s*([^}|]+)\|floatformat:2\s*}}'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'{{ \1|currency }}', content)
        modified = True
    
    # Padrão 2: R$ {{ var|add:other|floatformat:2 }}
    pattern2 = r'R\$\s*{{\s*([^}]+)\|floatformat:2\s*}}'
    if re.search(pattern2, content):
        content = re.sub(pattern2, r'{{ \1|currency }}', content)
        modified = True
    
    if modified and content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Processa todos os templates"""
    total_files = 0
    modified_files = 0
    
    for template_dir in TEMPLATE_DIRS:
        if not os.path.exists(template_dir):
            print(f"Diretório não encontrado: {template_dir}")
            continue
            
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    total_files += 1
                    
                    if fix_template(filepath):
                        modified_files += 1
                        print(f"✓ Modificado: {filepath}")
    
    print(f"\n{'='*60}")
    print(f"Total de arquivos processados: {total_files}")
    print(f"Arquivos modificados: {modified_files}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
