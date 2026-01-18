"""
Script para adicionar campo empresa aos models do financeiro
"""

# Lê o arquivo original
with open('financeiro/models.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# Adiciona campo empresa em ContaFinanceira
content = content.replace(
    '    nome = models.CharField(\'Nome da Conta\', max_length=100',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'contas_financeiras\', verbose_name=\'Empresa\')\n    \n    nome = models.CharField(\'Nome da Conta\', max_length=100'
)

# Adiciona campo empresa em FormaPagamento e remove unique do codigo
content = content.replace(
    '    codigo = models.CharField(\'Código\', max_length=20, unique=True)\n    descricao',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'formas_pagamento\', verbose_name=\'Empresa\')\n    \n    codigo = models.CharField(\'Código\', max_length=20)\n    descricao'
)

# Adiciona unique_together em FormaPagamento
content = content.replace(
    '    class Meta:\n        db_table = \'formas_pagamento\'\n        verbose_name = \'Forma de Pagamento\'\n        verbose_name_plural = \'Formas de Pagamento\'\n        ordering = [\'descricao\']',
    '    class Meta:\n        db_table = \'formas_pagamento\'\n        verbose_name = \'Forma de Pagamento\'\n        verbose_name_plural = \'Formas de Pagamento\'\n        ordering = [\'descricao\']\n        unique_together = [(\'empresa\', \'codigo\')]'
)

# Adiciona campo empresa em CentroCusto e remove unique do codigo
content = content.replace(
    '    codigo = models.CharField(\'Código\', max_length=20, unique=True)\n    nome = models.CharField(\'Nome\', max_length=100)\n    tipo = models.CharField(\'Tipo\', max_length=20, choices=TIPO_CHOICES)',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'centros_custo\', verbose_name=\'Empresa\')\n    \n    codigo = models.CharField(\'Código\', max_length=20)\n    nome = models.CharField(\'Nome\', max_length=100)\n    tipo = models.CharField(\'Tipo\', max_length=20, choices=TIPO_CHOICES)'
)

# Adiciona unique_together em CentroCusto
content = content.replace(
    '    class Meta:\n        db_table = \'centros_custo\'\n        verbose_name = \'Centro de Custo\'\n        verbose_name_plural = \'Centros de Custo\'\n        ordering = [\'codigo\']',
    '    class Meta:\n        db_table = \'centros_custo\'\n        verbose_name = \'Centro de Custo\'\n        verbose_name_plural = \'Centros de Custo\'\n        ordering = [\'codigo\']\n        unique_together = [(\'empresa\', \'codigo\')]'
)

# Adiciona campo empresa em PlanoConta e remove unique do codigo
content = content.replace(
    '    codigo = models.CharField(\'Código\', max_length=20, unique=True, help_text=\'Ex: 1.1.01, 3.2.01.001\')\n    nome = models.CharField(\'Nome\', max_length=150)\n    tipo = models.CharField(\'Tipo\', max_length=15, choices=TIPO_CHOICES)\n    natureza = models.CharField(\'Natureza\', max_length=10, choices=NATUREZA_CHOICES, default=\'ANALITICA\')',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'planos_conta\', verbose_name=\'Empresa\')\n    \n    codigo = models.CharField(\'Código\', max_length=20, help_text=\'Ex: 1.1.01, 3.2.01.001\')\n    nome = models.CharField(\'Nome\', max_length=150)\n    tipo = models.CharField(\'Tipo\', max_length=15, choices=TIPO_CHOICES)\n    natureza = models.CharField(\'Natureza\', max_length=10, choices=NATUREZA_CHOICES, default=\'ANALITICA\')'
)

# Adiciona unique_together em PlanoConta
content = content.replace(
    '    class Meta:\n        db_table = \'plano_contas\'\n        verbose_name = \'Plano de Conta\'\n        verbose_name_plural = \'Plano de Contas\'\n        ordering = [\'codigo\']',
    '    class Meta:\n        db_table = \'plano_contas\'\n        verbose_name = \'Plano de Conta\'\n        verbose_name_plural = \'Plano de Contas\'\n        ordering = [\'codigo\']\n        unique_together = [(\'empresa\', \'codigo\')]'
)

# Adiciona campo empresa em CategoriaCustoVariabilidade (após nome = )
content = content.replace(
    '    nome = models.CharField(\'Nome da Categoria\', max_length=100)\n    tipo = models.CharField(\'Tipo de Custo\', max_length=10, choices=TIPO_CHOICES, default=\'MISTO\')',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'categorias_custo\', verbose_name=\'Empresa\')\n    \n    nome = models.CharField(\'Nome da Categoria\', max_length=100)\n    tipo = models.CharField(\'Tipo de Custo\', max_length=10, choices=TIPO_CHOICES, default=\'MISTO\')'
)

# Adiciona campo empresa em TituloFinanceiro (após # Identificação)
content = content.replace(
    '    # Identificação\n    tipo = models.CharField(\'Tipo\', max_length=10, choices=TIPO_CHOICES)',
    '    # Multiempresa\n    empresa = models.ForeignKey(\'usuarios.Empresa\', on_delete=models.PROTECT, related_name=\'titulos_financeiros\', verbose_name=\'Empresa\')\n    \n    # Identificação\n    tipo = models.CharField(\'Tipo\', max_length=10, choices=TIPO_CHOICES)'
)

# Salva o arquivo corrigido
with open('financeiro/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Arquivo models.py atualizado com sucesso!")
