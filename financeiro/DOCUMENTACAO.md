# MÓDULO FINANCEIRO - DOCUMENTAÇÃO COMPLETA

## 📊 VISÃO GERAL

Sistema profissional de gestão financeira com contas a pagar e receber, controle bancário, projeções, indicadores de saúde financeira e ponto de equilíbrio.

---

## 🏗️ ARQUITETURA

### Models (financeiro/models.py)

#### **CADASTROS BASE**

1. **Banco**
   - Instituições financeiras
   - Campos: codigo_compe, nome, ativo

2. **ContaFinanceira**
   - Contas bancárias, caixas, carteiras digitais
   - Tipos: CONTA_CORRENTE, CONTA_POUPANCA, CAIXA, CARTEIRA_DIGITAL
   - Controla: saldo_inicial, limite_credito
   - Método: `saldo_atual()` - calcula baseado em movimentações

3. **FormaPagamento**
   - PIX, Boleto, Cartão Crédito/Débito, Transferência, Dinheiro
   - Campos: prazo_compensacao, taxa_percentual, taxa_fixa

4. **CentroCusto**
   - Departamentos, Obras, Projetos
   - Tipos: OBRA, ADMINISTRATIVO, PRODUCAO, COMERCIAL, LOJA
   - Relacionamento opcional com módulo de projetos

5. **CategoriaCustoVariabilidade**
   - Classifica categorias do plano de contas como FIXO/VARIAVEL/MISTO
   - Usado para cálculo de ponto de equilíbrio

#### **OPERAÇÃO FINANCEIRA**

6. **TituloFinanceiro**
   - Documento original (NF, Contrato, Ordem)
   - Tipo: PAGAR ou RECEBER
   - Status: ABERTO, PARCIAL, QUITADO, CANCELADO
   - Gera automaticamente parcelas no save()
   - Métodos:
     - `gerar_parcelas()` - cria ParcelaFinanceira
     - `atualizar_status()` - baseado nas parcelas
     - `valor_pago()` e `saldo_aberto()`

7. **ParcelaFinanceira**
   - Cada vencimento individual de um título
   - Campos: data_vencimento, valor_original, saldo_aberto
   - Pode ter múltiplas baixas (parciais)
   - Métodos:
     - `esta_vencida()` e `dias_atraso()`
     - `atualizar_status()`

8. **BaixaFinanceira**
   - Pagamento/Recebimento efetivo
   - **REGRA CRÍTICA**: baixa não pode exceder saldo aberto (validação no clean())
   - Campos de cálculo: valor_principal, juros, multa, desconto, taxas, valor_liquido
   - Controle de estorno
   - Métodos:
     - `save()` - atualiza parcela e cria movimentação
     - `estornar()` - revert baixa, reabre parcela, cria movimentação reversa

9. **MovimentacaoConta**
   - Extrato interno da conta financeira
   - Gerado automaticamente pelas baixas
   - Tipos: ENTRADA ou SAIDA
   - Campo estornado controla se é válido

10. **TransferenciaEntreContas**
    - Movimenta valores entre contas
    - Cria 2 movimentações (saída + entrada)

---

## 🧮 SERVICES (Lógica de Negócio)

### financeiro/services/calculadora.py

#### **CalculadoraSaldos**
```python
saldo_conta(conta_id, data_ref=None)  # Saldo de uma conta
saldo_contas_resumo()  # Todas as contas ativas
total_a_pagar_aberto()  # Total em aberto
total_a_receber_aberto()  # Total a receber
total_vencido(tipo, data_ref)  # Vencidos
```

#### **ProjecaoFluxoCaixa**
```python
projecao_periodo(data_inicio, data_fim)  # Entradas/saídas previstas
projecoes_multiplas()  # 7, 30, 60, 90 dias
fluxo_mensal(ano, mes)  # Previsto x Realizado
```

### financeiro/services/indicadores.py

#### **IndicadoresSaudeFinanceira**
```python
inadimplencia()  # Taxa de vencidos / total
liquidez_curto_prazo(dias)  # Entradas / Saídas
prazo_medio_recebimento()  # PMR (últimos 90 dias)
prazo_medio_pagamento()  # PMP (últimos 90 dias)
resultado_mensal(ano, mes)  # DRE simplificada
dashboard_resumo()  # TODOS os indicadores consolidados
```

**Status dos Indicadores:**
- inadimplência: OK < 5% | ALERTA 5-10% | CRITICO > 10%
- liquidez: OK >= 1.2 | ALERTA 1.0-1.2 | CRITICO < 1.0
- PMR: OK <= 30d | ALERTA 30-45d | CRITICO > 45d

### financeiro/services/ponto_equilibrio.py

#### **AnalisePontoEquilibrio**
```python
classificacao_custos_periodo(data_inicio, data_fim)
calcular_break_even(periodo_meses=3)
projecao_break_even_futuro(receita_projetada)
```

**Fórmulas:**
- Margem de Contribuição = (Receitas - Custos Variáveis) / Receitas
- Ponto de Equilíbrio = Custos Fixos / (Margem de Contribuição %)

---

## 🌐 VIEWS E URLs

### Dashboard e Principais
- `/financeiro/` - Dashboard com todos os indicadores
- `/financeiro/titulos/` - Lista títulos
- `/financeiro/titulos/criar/` - Cria novo título
- `/financeiro/titulos/<id>/` - Detalhe com parcelas

### Contas a Pagar/Receber
- `/financeiro/contas-pagar/` - Lista parcelas a pagar
- `/financeiro/contas-receber/` - Lista parcelas a receber
- `/financeiro/parcelas/<id>/baixar/` - Realiza baixa
- `/financeiro/baixas/<id>/estornar/` - Estorna baixa

### Contas Financeiras
- `/financeiro/contas-financeiras/` - Lista contas com saldo
- `/financeiro/contas-financeiras/<id>/extrato/` - Extrato completo

### Calendário
- `/financeiro/calendario/` - Calendário mensal com vencimentos
  - Parâmetros: ?mes=12&ano=2025
  - Mostra vencidos/hoje/futuro/quitados

### Relatórios Operacionais
- `/financeiro/relatorios/contas-pagar/` - Com filtros detalhados
- `/financeiro/relatorios/contas-receber/` - Com filtros de cliente

### Relatórios Gerenciais
- `/financeiro/relatorios/fluxo-caixa/` - Previsto x Realizado
- `/financeiro/relatorios/dre/` - Por categoria
- `/financeiro/relatorios/ponto-equilibrio/` - Break-even analysis
- `/financeiro/relatorios/resultado-centro-custo/` - Por obra/depto

---

## 📈 DASHBOARD - Componentes

### Cards de Resumo
1. **Caixa Atual** - Soma de todas as contas ativas
2. **A Receber** - Total aberto + vencido
3. **A Pagar** - Total aberto + vencido
4. **Projeção 30 Dias** - Entradas - Saídas previstas

### Indicadores de Saúde
- Inadimplência com status colorido
- Liquidez 30 dias
- PMR e PMP

### Projeções de Fluxo
- Tabela com 7, 30, 60, 90 dias
- Entradas/Saídas/Saldo projetado

### Resultado do Mês
- Receitas vs Despesas vs Margem

### Links Rápidos
- Novo Título, Contas Pagar/Receber, Calendário
- Relatórios gerenciais

---

## 🔄 MIGRAÇÃO DO LEGADO

### Comando: migrar_financeiro_legado.py

```bash
# Teste (não salva)
python manage.py migrar_financeiro_legado --dry-run

# Teste limitado
python manage.py migrar_financeiro_legado --dry-run --limite 100

# Execução real
python manage.py migrar_financeiro_legado
```

### Processo de Migração

1. **Lê tabela `financeiro` (legado)**
   - Converte datas varchar → date
   - Mapeia TIPOCONTA → tipo (PAGAR/RECEBER)

2. **Cria TituloFinanceiro**
   - Mapeia IDCREDOR → Pessoa
   - Mapeia CONTA/SUBCONTA → PlanoConta
   - Mapeia IDPROJETO → CentroCusto
   - Documento: usa DOCUMENTO ou gera LEG-{id}

3. **Cria ParcelaFinanceira**
   - data_vencimento = VENCIMENTO
   - valor_original = VALORPARCELA ou VALORTOTAL

4. **Cria BaixaFinanceira (se baixado)**
   - Se BAIXADO = 1 e (VALORPAGO ou VALORRECEBIDO)
   - Mapeia IDBANCO → ContaFinanceira
   - Converte JUROS, MULTA, DESCONTO

5. **Atualiza status**
   - Parcela → ABERTO ou QUITADO
   - Título → baseado nas parcelas

### Mapeamentos

- **Pessoa**: IDCREDOR → cadastros.Pessoa(id)
- **PlanoConta**: CONTA.SUBCONTA → codigo
- **CentroCusto**: IDPROJETO → projeto_id
- **ContaFinanceira**: IDBANCO → id (ou cria padrão)
- **FormaPagamento**: Usa padrão DINHEIRO

---

## 🚀 INSTALAÇÃO E CONFIGURAÇÃO

### 1. Adicionar ao INSTALLED_APPS

```python
# serrana/settings.py
INSTALLED_APPS = [
    ...
    'financeiro',
    ...
]
```

### 2. Incluir URLs

```python
# serrana/urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('financeiro/', include('financeiro.urls')),
    ...
]
```

### 3. Criar migrações e aplicar

```bash
python manage.py makemigrations financeiro
python manage.py migrate financeiro
```

### 4. Criar dados iniciais

```bash
# Banco exemplo
python manage.py shell
>>> from financeiro.models import Banco, ContaFinanceira, FormaPagamento, CentroCusto
>>> Banco.objects.create(codigo_compe='001', nome='Banco do Brasil', ativo=True)
>>> Banco.objects.create(codigo_compe='237', nome='Bradesco', ativo=True)
>>> Banco.objects.create(codigo_compe='104', nome='Caixa Econômica', ativo=True)

# Formas de pagamento
>>> FormaPagamento.objects.create(codigo='PIX', descricao='PIX', tipo='PIX', ativo=True)
>>> FormaPagamento.objects.create(codigo='DINHEIRO', descricao='Dinheiro', tipo='DINHEIRO', ativo=True)
>>> FormaPagamento.objects.create(codigo='BOLETO', descricao='Boleto Bancário', tipo='BOLETO', prazo_compensacao=1, ativo=True)

# Conta financeira
>>> bb = Banco.objects.get(codigo_compe='001')
>>> ContaFinanceira.objects.create(
...     nome='Conta Corrente BB',
...     tipo='CONTA_CORRENTE',
...     banco=bb,
...     agencia='1234',
...     conta='56789-0',
...     saldo_inicial=10000.00,
...     ativo=True
... )
```

### 5. Migrar dados legados (opcional)

```bash
python manage.py migrar_financeiro_legado
```

---

## 📋 REGRAS DE NEGÓCIO CRÍTICAS

### ✅ Título ≠ Parcela ≠ Baixa
- **Título**: Documento original (NF, contrato)
- **Parcela**: Vencimento individual
- **Baixa**: Pagamento/recebimento efetivo

### ✅ Baixas Parciais
- Uma parcela pode ter N baixas
- Saldo atualizado automaticamente
- Status: ABERTO → PARCIAL → QUITADO

### ✅ Validações
- Baixa não pode exceder saldo aberto
- Transferência: contas origem ≠ destino
- Ajuste: pelo menos um local

### ✅ Estorno
- Reabre saldo da parcela
- Cria movimentação reversa na conta
- Mantém histórico completo (não deleta)

### ✅ Movimentações Automáticas
- Toda baixa gera MovimentacaoConta
- Tipo depende de PAGAR/RECEBER
- Estornos criam movimentação reversa

---

## 🎨 TEMPLATES E UI

### Estrutura
```
financeiro/templates/financeiro/
├── dashboard.html (completo)
├── listar_titulos.html
├── criar_titulo.html
├── detalhe_titulo.html
├── listar_contas_pagar.html
├── listar_contas_receber.html
├── baixar_parcela.html
├── estornar_baixa.html
├── listar_contas_financeiras.html
├── extrato_conta.html
├── calendario.html
├── relatorio_contas_pagar.html
├── relatorio_contas_receber.html
├── relatorio_fluxo_caixa.html
├── relatorio_dre.html
├── relatorio_ponto_equilibrio.html
└── relatorio_resultado_centro_custo.html
```

### Classes CSS Usadas
- Bootstrap 5 padrão
- Bootstrap Icons
- Cores semânticas: success, danger, warning, info, primary

---

## 📊 QUERIES E PERFORMANCE

### Índices Criados
- parcelas: (titulo, numero_parcela), (data_vencimento, status)
- baixas: (parcela), (data_pagamento), (conta_financeira)
- movimentacoes: (conta_financeira, data_movimentacao), (tipo)
- titulos: (tipo, status), (pessoa), (data_emissao)

### Otimizações
- `select_related()` para ForeignKeys
- `prefetch_related()` para reverse FKs
- Agregações no banco (Sum, Count)
- Cálculos em Services (não nas views)

### Cache (Futuro)
- Dashboard: cache 5min
- Saldos: cache por conta/data
- Invalidar em save/delete de baixas

---

## 🔐 SEGURANÇA E AUDITORIA

### Campos de Auditoria
- criado_em, criado_por
- atualizado_em (títulos)
- data_estorno, estornado_por (baixas)

### Permissões (Futuro)
- Criar títulos
- Realizar baixas
- Estornar baixas (gerente)
- Visualizar relatórios

---

## 📝 PRÓXIMAS MELHORIAS (ROADMAP)

### Fase 2
- [ ] Integração CNAB (remessa/retorno)
- [ ] Conciliação bancária automatizada
- [ ] Recorrência de títulos (mensalidades)
- [ ] Renegociação de parcelas
- [ ] Cobrança automática (emails, WhatsApp)

### Fase 3
- [ ] API REST (DRF)
- [ ] Mobile app (React Native)
- [ ] Dashboards interativos (Chart.js/Plotly)
- [ ] Exportação Excel/PDF avançada
- [ ] BI integrado

### Otimizações
- [ ] Cache distribuído (Redis)
- [ ] Filas para cálculos pesados (Celery)
- [ ] Elasticsearch para buscas
- [ ] Particionamento de tabelas antigas

---

## 🆘 TROUBLESHOOTING

### Erro: "Baixa excede saldo aberto"
- Verificar se já existe baixa para esta parcela
- Conferir se valor_principal está correto
- Checar se parcela não foi estornada

### Saldo de conta incorreto
- Verificar movimentações estornadas
- Conferir saldo_inicial da conta
- Recalcular com: `CalculadoraSaldos.saldo_conta(id)`

### Status não atualiza
- Chamar manualmente: `parcela.atualizar_status()`
- Verificar signals se foram desconectados
- Conferir transações no banco

---

## 📚 REFERÊNCIAS

- Django ORM: https://docs.djangoproject.com/en/6.0/topics/db/
- Decimal para moeda: sempre usar `DecimalField`
- Boas práticas financeiras: separação título/parcela/baixa
- Auditoria: never delete, sempre flag de inativo/estornado

---

## 📞 SUPORTE

Para dúvidas ou problemas:
1. Consultar esta documentação
2. Verificar logs do Django
3. Executar testes: `python manage.py test financeiro`
4. Revisar código nos models e services

---

**Versão:** 1.0  
**Data:** Dezembro/2025  
**Autor:** Sistema Serrana Empresarial
