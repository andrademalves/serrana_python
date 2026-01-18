# 📚 GUIA DE IMPLEMENTAÇÃO - ESTOQUE PROFISSIONAL

## 🎯 Visão Geral

Este guia detalha os passos para implementar o sistema de estoque profissional em sua aplicação Django existente, aproveitando os cadastros de Pessoa e Produto já existentes.

---

## ✅ PRÉ-REQUISITOS

### 1. Models Existentes Necessários

Verifique se você tem os seguintes models:

**cadastros/models.py:**
```python
class Pessoa(models.Model):
    # Campos obrigatórios
    nome_razao_social
    # Flags obrigatórias
    fornecedor = BooleanField()
    cliente = BooleanField()
    funcionario = BooleanField()
    terceiro = BooleanField()

class Produto(models.Model):
    codigo
    descricao
    unidade
    tipo  # produto/servico
    ativo
    # Campos que serão adicionados/ajustados:
    fornecedor = FK(Pessoa)  # fornecedor padrão
```

### 2. Model de Obra/Projeto

Você deve ter um model de Obra ou Projeto. Exemplos:
- `projetos.Obra`
- `cadastros.Obra`
- `cadastros.Projeto`

**AÇÃO NECESSÁRIA:** Ajustar os imports nos arquivos:
- `estoque/models_profissional.py` (linhas comentadas com obra)
- `estoque/services_profissional.py`

---

## 🚀 PASSO A PASSO DA IMPLEMENTAÇÃO

### FASE 1: PREPARAÇÃO DO AMBIENTE

#### 1.1. Backup Completo

```bash
# Backup do banco de dados
python manage.py dumpdata > backup_completo_$(date +%Y%m%d_%H%M%S).json

# Backup dos arquivos
cd /caminho/para/seu/projeto
tar -czf backup_projeto_$(date +%Y%m%d).tar.gz .
```

#### 1.2. Adicionar Campos ao Model Produto

Edite `cadastros/models.py` e adicione os campos para estoque mínimo:

```python
class Produto(models.Model):
    # ... campos existentes ...
    
    # NOVOS CAMPOS PARA ESTOQUE MÍNIMO (adicionar)
    consumo_medio_diario = models.DecimalField(
        'Consumo Médio Diário',
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Calculado automaticamente com base no histórico'
    )
    lead_time_dias = models.IntegerField(
        'Lead Time (dias)',
        default=0,
        help_text='Prazo médio de entrega do fornecedor'
    )
    estoque_seguranca = models.DecimalField(
        'Estoque de Segurança',
        max_digits=12,
        decimal_places=3,
        default=0
    )
    estoque_minimo = models.DecimalField(
        'Estoque Mínimo',
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text='Ponto de ressuprimento'
    )
```

**Criar e aplicar migration:**
```bash
python manage.py makemigrations cadastros
python manage.py migrate cadastros
```

---

### FASE 2: COPIAR ARQUIVOS DO NOVO SISTEMA

#### 2.1. Fazer Backup dos Arquivos Atuais

```bash
# Backup do models.py atual
cp estoque/models.py estoque/models_OLD_BACKUP.py

# Backup do admin.py atual (se existir)
cp estoque/admin.py estoque/admin_OLD_BACKUP.py
```

#### 2.2. Copiar Novos Arquivos

Os seguintes arquivos foram criados e devem ser copiados para seu projeto:

**Estrutura:**
```
estoque/
  ├── models_profissional.py          ← NOVO (substituirá models.py)
  ├── services_profissional.py        ← NOVO
  ├── DESIGN_ESTOQUE_PROFISSIONAL.md ← DOCUMENTAÇÃO
  └── management/
      └── commands/
          ├── atualizar_consumo_medio.py        ← NOVO
          └── criar_dados_iniciais_estoque.py   ← NOVO
```

#### 2.3. Ajustar Imports de Obra

**No arquivo `estoque/models_profissional.py`:**

Procure pelas linhas comentadas e descomente/ajuste:

```python
# ANTES (linha ~28):
# from projetos.models import Obra
# OU
# from cadastros.models import Obra

# DEPOIS (descomente a linha correta):
from projetos.models import Obra  # ou o path correto do seu projeto
```

Depois, procure o campo `obra` em `MovimentoEstoque` e `CustoObra` e descomente:

```python
# ANTES (temporário):
obra = models.CharField('Obra/Projeto', max_length=100, ...)

# DEPOIS (definitivo):
obra = models.ForeignKey(
    'projetos.Obra',  # ajustar conforme seu app
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='movimentos_estoque',
    verbose_name='Obra/Projeto'
)
```

**No arquivo `estoque/services_profissional.py`:**

Não há imports diretos, mas ajuste as tipagens se necessário.

---

### FASE 3: SUBSTITUIR MODELS

#### 3.1. Renomear Arquivos

```bash
# Renomear models antigo
mv estoque/models.py estoque/models_old.py

# Ativar novo models
mv estoque/models_profissional.py estoque/models.py
```

**OU** edite `models_profissional.py` e cole o conteúdo em `models.py`.

#### 3.2. Criar Migrations

```bash
python manage.py makemigrations estoque

# Você verá migrations para:
# - LocalEstoque
# - DestinoEstoque
# - MovimentoEstoque
# - SaldoEstoque
# - CustoObra
# - ProdutoFornecedor
```

#### 3.3. Revisar Migrations Geradas

```bash
# Ver o que será aplicado
python manage.py showmigrations estoque

# Ver SQL que será executado
python manage.py sqlmigrate estoque XXXX  # número da migration
```

#### 3.4. Aplicar Migrations

```bash
python manage.py migrate estoque
```

---

### FASE 4: POPULAR DADOS INICIAIS

#### 4.1. Criar Locais e Destinos Padrão

```bash
python manage.py criar_dados_iniciais_estoque
```

**Saída esperada:**
```
==================================================================
CRIAÇÃO DE DADOS INICIAIS DO ESTOQUE
==================================================================

1. Criando Locais de Estoque...
  ✓ Criado: ALMOX_MP - Almoxarifado de Matéria-Prima
  ✓ Criado: PRODUCAO - Área de Produção/Fabricação
  ✓ Criado: ALMOX_PA - Almoxarifado de Produto Acabado
  ✓ Criado: LOJA - Loja/Showroom

2. Criando Destinos de Estoque...
  ✓ Criado: OBRA - Obra/Projeto
  ✓ Criado: LOJA - Loja/Venda Balcão
  ...
```

---

### FASE 5: MIGRAÇÃO DE DADOS ANTIGOS (SE HOUVER)

#### 5.1. Migrar Saldo Atual do Produto

Se você tem `Produto.estoque_atual` populado, crie um comando para migrar:

**Criar arquivo:** `estoque/management/commands/migrar_saldo_inicial.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from cadastros.models import Produto
from estoque.models import LocalEstoque, MovimentoEstoque
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Migra estoque_atual do Produto para MovimentoEstoque'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Local padrão para saldo inicial
        local_padrao = LocalEstoque.objects.get(codigo='ALMOX_MP')
        
        # Usuário admin
        user = User.objects.filter(is_superuser=True).first()
        
        produtos_migrados = 0
        
        with transaction.atomic():
            for produto in Produto.objects.filter(ativo=True):
                # Verificar se tem estoque_atual
                if hasattr(produto, 'estoque_atual') and produto.estoque_atual > 0:
                    
                    if not dry_run:
                        # Criar movimento de ajuste (saldo inicial)
                        MovimentoEstoque.objects.create(
                            tipo_movimento='AJUSTE',
                            documento='SALDO_INICIAL',
                            documento_tipo='INV',
                            data_operacao=timezone.now(),
                            produto=produto,
                            local_destino=local_padrao,
                            quantidade=produto.estoque_atual,
                            custo_unitario_aplicado=getattr(produto, 'custo', Decimal('0')),
                            observacao='Migração de saldo inicial do sistema antigo',
                            criado_por=user
                        )
                    
                    self.stdout.write(
                        f"{'[DRY RUN] ' if dry_run else ''}Migrado: {produto.codigo} - Qtd: {produto.estoque_atual}"
                    )
                    produtos_migrados += 1
            
            if dry_run:
                # Não commitar em dry-run
                transaction.set_rollback(True)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total de produtos migrados: {produtos_migrados}')
        )
```

**Executar:**
```bash
# Simular primeiro
python manage.py migrar_saldo_inicial --dry-run

# Se estiver tudo OK, executar de verdade
python manage.py migrar_saldo_inicial
```

---

### FASE 6: ATUALIZAR ADMIN

#### 6.1. Criar Admin para Novos Models

Edite `estoque/admin.py`:

```python
from django.contrib import admin
from .models import (
    LocalEstoque,
    DestinoEstoque,
    MovimentoEstoque,
    SaldoEstoque,
    CustoObra,
    ProdutoFornecedor
)

@admin.register(LocalEstoque)
class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo', 'permite_saldo_negativo', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['codigo', 'nome']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(DestinoEstoque)
class DestinoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'exige_obra', 'gera_custo_obra', 'ativo']
    list_filter = ['exige_obra', 'gera_custo_obra', 'ativo']
    search_fields = ['codigo', 'nome']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['documento', 'tipo_movimento', 'data_operacao', 'produto', 
                    'quantidade', 'local_origem', 'local_destino', 'estornado']
    list_filter = ['tipo_movimento', 'documento_tipo', 'estornado', 'data_operacao']
    search_fields = ['documento', 'produto__codigo', 'produto__descricao']
    readonly_fields = ['custo_total', 'criado_em', 'criado_por', 'estornado']
    date_hierarchy = 'data_operacao'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('tipo_movimento', 'documento_tipo', 'documento', 'data_operacao')
        }),
        ('Produto e Locais', {
            'fields': ('produto', 'local_origem', 'local_destino', 'destino', 'obra')
        }),
        ('Quantidade e Custos', {
            'fields': ('quantidade', 'custo_unitario_aplicado', 'custo_total')
        }),
        ('Pessoas', {
            'fields': ('fornecedor', 'solicitante', 'entregador')
        }),
        ('Estorno', {
            'fields': ('movimento_origem', 'estornado'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacao',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        # Movimentos são imutáveis após criação
        if obj and obj.pk:
            return False
        return super().has_change_permission(request, obj)

@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'local', 'saldo_quantidade', 'custo_medio', 'valor_total', 'atualizado_em']
    list_filter = ['local']
    search_fields = ['produto__codigo', 'produto__descricao']
    readonly_fields = ['produto', 'local', 'saldo_quantidade', 'custo_medio', 'atualizado_em']
    
    def has_add_permission(self, request):
        # Saldos são criados automaticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Saldos são atualizados automaticamente
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Não permitir exclusão manual
        return False

@admin.register(CustoObra)
class CustoObraAdmin(admin.ModelAdmin):
    list_display = ['obra', 'data', 'categoria', 'origem', 'descricao', 'valor']
    list_filter = ['categoria', 'origem', 'data']
    search_fields = ['descricao', 'documento']
    readonly_fields = ['criado_em', 'criado_por']
    date_hierarchy = 'data'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProdutoFornecedor)
class ProdutoFornecedorAdmin(admin.ModelAdmin):
    list_display = ['produto', 'fornecedor', 'preferencial', 'prazo_entrega_dias', 
                    'custo_ultima_compra', 'ativo']
    list_filter = ['preferencial', 'ativo']
    search_fields = ['produto__codigo', 'produto__descricao', 'fornecedor__nome_razao_social']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
```

---

### FASE 7: TESTAR O SISTEMA

#### 7.1. Acessar Admin

```bash
python manage.py runserver
```

Acesse: `http://localhost:8000/admin`

**Verificar:**
- ✅ Locais de Estoque aparecem
- ✅ Destinos de Estoque aparecem
- ✅ Produtos com novos campos
- ✅ Criar um MovimentoEstoque de teste

#### 7.2. Teste de Entrada

No admin, criar um MovimentoEstoque:
- Tipo: ENTRADA
- Local Destino: ALMOX_MP
- Produto: (selecionar)
- Quantidade: 100
- Custo Unitário: 10.50
- Fornecedor: (selecionar)

**Verificar:**
- ✅ Saldo criado automaticamente em SaldoEstoque
- ✅ Custo médio = 10.50

#### 7.3. Teste de Saída

Criar MovimentoEstoque:
- Tipo: SAIDA
- Local Origem: ALMOX_MP
- Destino: LOJA
- Produto: (mesmo anterior)
- Quantidade: 30

**Verificar:**
- ✅ Saldo reduzido de 100 para 70
- ✅ Custo unitário aplicado = 10.50 (custo médio vigente)

---

### FASE 8: ATUALIZAR CONSUMO MÉDIO (PRIMEIRO RUN)

```bash
python manage.py atualizar_consumo_medio --dias=30
```

**Verificar:**
- ✅ Produtos com campo `consumo_medio_diario` atualizado
- ✅ `estoque_minimo` recalculado

---

### FASE 9: CRIAR VIEWS E TEMPLATES (Próxima Etapa)

Agora que os models estão funcionando, você pode criar:
- Views para entrada de estoque
- Views para saída/requisição
- Relatórios
- Dashboard

**Exemplo de próximos passos:**
```
estoque/
  ├── views_operacoes.py  (entrada, saída, transferência)
  ├── views_relatorios.py (posição, extrato, abaixo mínimo)
  ├── forms.py            (forms para operações)
  └── templates/estoque/
      ├── entrada.html
      ├── saida.html
      ├── posicao_estoque.html
      └── produtos_abaixo_minimo.html
```

---

## 🔄 MANUTENÇÃO E BOAS PRÁTICAS

### Jobs Automáticos Recomendados

1. **Atualizar Consumo Médio (Semanal)**
```bash
# Crontab (Linux) - toda segunda às 01:00
0 1 * * 1 cd /caminho/projeto && python manage.py atualizar_consumo_medio
```

2. **Alertas de Estoque Mínimo (Diário)**
Criar comando customizado que envia email/notificação.

### Permissões Sugeridas

Criar grupos:
- **Almoxarife**: pode entrada, saída, transferência
- **Gestor Estoque**: pode tudo + estorno + relatórios
- **Visualizador**: apenas relatórios

---

## 📋 CHECKLIST FINAL

- [ ] Backup completo realizado
- [ ] Campos adicionados ao Produto
- [ ] Imports de Obra ajustados
- [ ] Migrations criadas e aplicadas
- [ ] Dados iniciais criados (locais e destinos)
- [ ] Saldos iniciais migrados (se aplicável)
- [ ] Admin configurado
- [ ] Teste de entrada funcionando
- [ ] Teste de saída funcionando
- [ ] Consumo médio atualizado
- [ ] Documentação lida e compreendida

---

## 🆘 TROUBLESHOOTING

### Erro: "No module named estoque.models_profissional"

**Solução:** Renomeie o arquivo para `models.py` ou ajuste imports.

### Erro: "Cannot resolve keyword 'obra' into field"

**Solução:** Ajuste o FK de obra nos models conforme o path correto do seu app.

### Erro: "User matching query does not exist" ao criar dados iniciais

**Solução:** Crie um superusuário:
```bash
python manage.py createsuperuser
```

### Saldo não está atualizando

**Solução:** Verifique:
1. O método `save()` do MovimentoEstoque está sendo chamado?
2. Há erros no console/log?
3. Transaction está commitando?

---

## 📞 SUPORTE

Para dúvidas sobre implementação:
1. Revise a documentação em `DESIGN_ESTOQUE_PROFISSIONAL.md`
2. Verifique o código em `models.py` e `services.py`
3. Consulte logs do Django

**Próximo documento:** Criar Views e Templates (guia separado)
