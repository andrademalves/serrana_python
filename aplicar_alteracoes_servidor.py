#!/usr/bin/env python3
"""
Script para aplicar alterações no servidor SSH
Execute no servidor: python3 aplicar_alteracoes_servidor.py
"""

import os
import sys
import re

# Caminho do projeto (ajuste se necessário)
PROJECT_PATH = '/root/serrana_python'

def aplicar_alteracoes():
    print("=" * 60)
    print("APLICANDO ALTERAÇÕES NO CADASTRO DE PESSOAS")
    print("=" * 60)
    
    os.chdir(PROJECT_PATH)
    print(f"\n✓ Diretório do projeto: {os.getcwd()}")
    
    # 1. ATUALIZAR MODELS.PY
    print("\n[1/6] Atualizando models.py...")
    models_path = 'cadastros/models.py'
    
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar data_nascimento após sexo
    if 'data_nascimento' not in content:
        content = content.replace(
            "sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name='Sexo')",
            "sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name='Sexo')\n    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')"
        )
        with open(models_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Campo data_nascimento adicionado ao modelo")
    else:
        print("✓ Campo data_nascimento já existe no modelo")
    
    # 2. ATUALIZAR TEMPLATE editar_pessoa.html
    print("\n[2/6] Atualizando template editar_pessoa.html...")
    template_path = 'cadastros/templates/cadastros/editar_pessoa.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Remover obrigatoriedade de CTPS
    template_content = re.sub(
        r'<label class="form-label">CTPS <span class="text-danger" id="asterisco-ctps" style="display:none;">\*</span></label>',
        '<label class="form-label">CTPS</label>',
        template_content
    )
    template_content = re.sub(
        r'<div class="invalid-feedback">CTPS é obrigatório para funcionários</div>',
        '',
        template_content
    )
    
    # Remover obrigatoriedade de Data Admissão
    template_content = re.sub(
        r'<label class="form-label">Data Admissão <span class="text-danger" id="asterisco-admissao" style="display:none;">\*</span></label>',
        '<label class="form-label">Data Admissão</label>',
        template_content
    )
    template_content = re.sub(
        r'<div class="invalid-feedback">Data de admissão é obrigatória para funcionários</div>',
        '',
        template_content
    )
    
    # Limpar array de campos obrigatórios
    template_content = re.sub(
        r'const camposObrigatorios = \[\s*\{[^}]+\},\s*\{[^}]+\}\s*\];',
        'const camposObrigatorios = [];',
        template_content,
        flags=re.DOTALL
    )
    
    # Adicionar campo data_nascimento após sexo
    if 'data_nascimento' not in template_content:
        # Procurar o bloco do campo Sexo e adicionar data_nascimento
        sexo_pattern = r'(<div class="col-md-3">\s*<label class="form-label">Sexo</label>.*?</select>\s*</div>)(\s*</div>)'
        replacement = r'\1\n                <div class="col-md-3">\n                    <label class="form-label">Data de Nascimento</label>\n                    <input type="date" class="form-control" name="data_nascimento" value="{{ pessoa.data_nascimento|date:\'Y-m-d\'|default:\'\' }}">\n                </div>\2'
        template_content = re.sub(sexo_pattern, replacement, template_content, flags=re.DOTALL)
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    print("✓ Template editar_pessoa.html atualizado")
    
    # 3. ATUALIZAR VIEWS.PY
    print("\n[3/6] Atualizando views.py...")
    views_path = 'cadastros/views.py'
    
    with open(views_path, 'r', encoding='utf-8') as f:
        views_content = f.read()
    
    # Adicionar data_nascimento na criação
    if "data_nascimento=parse_date(request.POST.get('data_nascimento'))" not in views_content:
        views_content = re.sub(
            r"(sexo=request\.POST\.get\('sexo', ''\) or None,)",
            r"\1\n                data_nascimento=parse_date(request.POST.get('data_nascimento')),",
            views_content
        )
        
        # Adicionar na edição
        views_content = re.sub(
            r"(pessoa\.sexo = request\.POST\.get\('sexo', ''\) or None)",
            r"\1\n            pessoa.data_nascimento = parse_date(request.POST.get('data_nascimento'))",
            views_content
        )
        
        with open(views_path, 'w', encoding='utf-8') as f:
            f.write(views_content)
        print("✓ Views.py atualizado")
    else:
        print("✓ Views.py já contém data_nascimento")
    
    # 4. CRIAR MIGRATION
    print("\n[4/6] Criando migration...")
    migration_content = """# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0007_rename_pessoa_emp_ativo_idx_cadastros_p_empresa_b3572f_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pessoa',
            name='data_nascimento',
            field=models.DateField(blank=True, null=True, verbose_name='Data de Nascimento'),
        ),
    ]
"""
    
    migration_path = 'cadastros/migrations/0008_pessoa_data_nascimento.py'
    if not os.path.exists(migration_path):
        with open(migration_path, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        print("✓ Migration criada")
    else:
        print("✓ Migration já existe")
    
    # 5. APLICAR MIGRATION
    print("\n[5/6] Aplicando migration...")
    os.system('python3 manage.py migrate cadastros')
    
    # 6. REINICIAR SERVIÇO
    print("\n[6/6] Reiniciando serviço...")
    if os.system('systemctl is-active --quiet gunicorn') == 0:
        os.system('systemctl restart gunicorn')
        print("✓ Gunicorn reiniciado")
    elif os.system('systemctl is-active --quiet uwsgi') == 0:
        os.system('systemctl restart uwsgi')
        print("✓ uWSGI reiniciado")
    else:
        print("⚠ Nenhum serviço web encontrado (gunicorn/uwsgi)")
        print("  Você pode precisar reiniciar manualmente")
    
    print("\n" + "=" * 60)
    print("✓ ALTERAÇÕES APLICADAS COM SUCESSO!")
    print("=" * 60)
    print("\nResumo das alterações:")
    print("  • CTPS: campo opcional (não obrigatório)")
    print("  • Data Admissão: campo opcional (não obrigatório)")
    print("  • Data de Nascimento: novo campo adicionado (opcional)")

if __name__ == '__main__':
    try:
        aplicar_alteracoes()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
