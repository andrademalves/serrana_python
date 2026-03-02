# 📊 Dashboard CRM - Sistema Serrana

## 🎯 Visão Geral

O Dashboard CRM foi completamente reformulado para ser uma ferramenta **gerencial e estratégica**, transformando o CRM em um **Mini BI Comercial** com controle completo de funil, gestão de vendedores e previsões de faturamento.

---

## ✨ Funcionalidades Implementadas

### 1️⃣ **Padronização Visual**

✅ Utiliza `base.html` padrão do sistema  
✅ Partials integradas (head, header, sidebar, footer)  
✅ Visual Bootstrap/Nifty consistente  
✅ Totalmente integrado ao menu lateral

**Acesso:**
- Menu Módulos → CRM
- Sidebar CRM → **Dashboard BI** (primeiro item)

---

### 2️⃣ **Controle de Acesso**

#### 👤 **Vendedor**
- Vê apenas seus próprios leads
- Ranking mostra apenas sua posição
- Dashboard exibe apenas seus dados
- Não pode filtrar por outros vendedores

#### 👑 **Admin** (is_superuser ou is_staff)
- Vê todos os leads de todos os vendedores
- Pode filtrar por vendedor específico
- Visualiza ranking completo
- Acesso total aos filtros

**Implementação:** 
- `views_dashboard.py` - linha 29: `is_admin = request.user.is_superuser or request.user.is_staff`
- `services/metricas_crm.py` - linha 31-35: filtro por responsável

---

### 3️⃣ **Tela Principal: /crm/dashboard/**

**Estrutura de Arquivos:**
```
crm/
├── services/
│   ├── __init__.py
│   └── metricas_crm.py          # ✅ Lógica de negócio separada
├── views_dashboard.py            # ✅ Views do dashboard
├── templates/crm/
│   └── dashboard.html            # ✅ Template com gráficos
└── urls.py                       # ✅ Rota /crm/dashboard/
```

**Separação de Responsabilidades:**
- `metricas_crm.py`: Cálculos, queries ORM, lógica de BI
- `views_dashboard.py`: Processa requisição, aplica filtros, renderiza
- `dashboard.html`: Apresentação visual com Chart.js

---

## 📈 Componentes do Dashboard

### 4.1 - **KPIs Principais** (Cards no Topo)

Métricas essenciais em cards visuais:

1. **Total de Leads**
   - Quantidade total
   - Leads em andamento

2. **Taxa de Conversão**
   - Percentual de fechamento
   - Fechados / Total

3. **Ticket Médio**
   - Valor médio dos deals fechados
   - Baseado em `valor_fechado`

4. **Tempo Médio de Fechamento**
   - Em dias
   - Da entrada ao fechamento

**Código:** `services/metricas_crm.py` - método `kpis_principais()`

---

### 4.2 - **Gráfico: Leads por Etapa**

**Tipo:** Barra horizontal (Chart.js)  
**Dados:** ORM com `annotate(Count('id'))`  
**Cores:** Dinâmicas (vem do banco - `EtapaFunil.cor`)

**Mostra:**
- Nome da etapa
- Quantidade de leads por etapa
- Ordem correta do funil

**Query:**
```python
dados = qs.values('etapa__nome', 'etapa__cor', 'etapa__ordem').annotate(
    total=Count('id')
).order_by('etapa__ordem')
```

**Visualização:** Gráfico de barras coloridas por etapa

---

### 4.3 - **Ranking de Vendedores** 🏆

**Critérios de Ordenação:**
1. Maior valor fechado (principal)
2. Maior quantidade de fechamentos
3. Taxa de conversão

**Colunas:**
- Posição (🏆 para top 3)
- Nome do vendedor
- Total de leads
- Fechados (badge verde)
- Perdidos (badge vermelho)
- Em andamento (badge azul)
- **Valor fechado** (R$)
- **Taxa de conversão** (%)

**Destaques:**
- 🥇 1º lugar: Troféu dourado
- 🥈 2º lugar: Troféu prata
- 🥉 3º lugar: Troféu bronze

**Exibição:** Apenas para admin (vendedor vê apenas sua performance nos KPIs)

---

### 4.4 - **Gráfico de Performance**

**Tipo:** Donut (Chart.js)  
**Segmentos:**
- Prospectados (azul)
- Fechados (verde)
- Perdidos (vermelho)

**Mostra:**
- Quantidade absoluta
- Percentual de cada segmento

---

### 4.5 - **Gráfico de Funil** 🔻

**Funcionalidade Avançada:**

Mostra a progressão real do funil com:
- Quantidade em cada etapa
- **Percentual em relação ao total inicial**
- **Taxa de conversão entre etapas**
- **Conversão final global**

**Cálculo:**
```python
# Usa HistoricoEtapa para rastrear passagem por cada etapa
qtd_etapa = HistoricoEtapa.objects.filter(
    oportunidade__in=qs,
    etapa_para=etapa
).values('oportunidade').distinct().count()

conversao = (qtd_etapa / etapa_anterior_qtd * 100)
```

**Visual:** Barras horizontais com largura proporcional + badges com %

**Código:** `services/metricas_crm.py` - método `grafico_funil()`

---

## 🔍 Filtros do Dashboard

**Formulário no Topo:**

1. **Data Início** (date input)
2. **Data Fim** (date input)
3. **Vendedor** (select - **apenas admin**)
4. **Pipeline** (select)

**Padrão:** Mês atual (primeiro ao último dia)

**Aplicação:** Todos os gráficos e indicadores filtram simultaneamente

**Persistência:** Via GET params (`?data_inicio=2026-02-01&vendedor=2`)

---

## 💰 Meta Mensal por Vendedor

### Model: `MetaVendedor`

**Campos:**
- `empresa`: FK para Empresa
- `vendedor`: FK para User
- `mes`, `ano`: Período
- `meta_valor`: Decimal (R$)
- `meta_quantidade`: Integer (nº de deals)
- `ativo`: Boolean

**Método Integrado:**
```python
meta.calcular_realizado()
# Retorna: valor, quantidade, percentual_valor, percentual_quantidade
```

**Visualização no Dashboard:**
- Card com 2 barras de progresso
- Verde (≥100%), Amarelo (≥70%), Vermelho (<70%)
- Mostra meta vs realizado em R$ e quantidade

**Exemplo:**
```
Meta de Valor: R$ 100.000,00
[████████████████░░░░] 78% (R$ 78.000,00)

Meta de Quantidade: 5 negócios
[█████████████████░░░] 80% (4)
```

---

## 🔮 Previsão de Faturamento

**Baseada em:**
1. Leads em andamento (status: aberto, em_andamento)
2. Campo `valor_previsto` de cada lead
3. Campo `probabilidade_conversao` (0-100%)

**Cálculo:**

**Receita Potencial:**
```python
sum(oportunidade.valor_previsto for all leads em andamento)
```

**Receita Provável** (ponderada):
```python
sum(oportunidade.valor_previsto * probabilidade / 100)
```

**Exemplo:**
- Lead A: R$ 50.000 (80% prob) → Contribui R$ 40.000
- Lead B: R$ 30.000 (50% prob) → Contribui R$ 15.000
- **Total Provável:** R$ 55.000

**Visualização:** Card com 2 valores lado a lado + tooltip explicativo

---

## 🔄 Integração Futura: Lead → Orçamento → Projeto

### Novos Campos em `Oportunidade`:

✅ `valor_previsto` (Decimal) - Valor esperado  
✅ `valor_fechado` (Decimal) - Valor real quando ganho  
✅ `probabilidade_conversao` (Integer 0-100) - %  
✅ `numero_projeto` (CharField) - Código quando vira projeto

**Preparação:**
- `orcamento` (FK) - Já existe
- `projeto` (FK) - Já existe
- Signals em `crm/signals.py` - Já implementados

**Fluxo Futuro:**
```
Oportunidade (Ganho) → 
  criar_orcamento_de_oportunidade() → 
    aprovar_orcamento() → 
      Signal cria Projeto → 
        oportunidade.numero_projeto = projeto.codigo
```

---

## 🛠️ Estrutura Técnica

### Backend

**Arquivo:** `services/metricas_crm.py`

**Classe Principal:** `MetricasCRM`

**Métodos:**
- `leads_por_etapa()` - Gráfico de barras
- `ranking_vendedores()` - Tabela ranking
- `grafico_performance()` - Donut chart
- `grafico_funil()` - Funil com conversão
- `meta_vendedor()` - Meta e realizado
- `previsao_faturamento()` - Receita potencial/provável
- `kpis_principais()` - Cards do topo

**ORM Utilizado:**
- `annotate(Count())`
- `Sum()`, `Avg()`
- `Coalesce()` - Fallback para valores nulos
- `Case/When` - Não utilizado (queries diretas)
- `F()` - Para cálculos de datas

**Exemplo de Query:**
```python
ranking = Oportunidade.objects.filter(
    empresa=empresa,
    responsavel=vendedor,
    status='ganho'
).aggregate(
    total=Coalesce(Sum('valor_fechado'), Value(0))
)
```

### Frontend

**Bibliotecas:**
- **Chart.js 4.4.0** (gráficos)
- **Bootstrap 5.3** (layout)
- **Bootstrap Icons** (ícones)

**Passagem de Dados:**
```python
# View
context = {
    'dados_etapas_json': json.dumps(dados_etapas, default=str)
}

# Template
<script>
const dadosEtapas = {{ dados_etapas_json|safe }};
new Chart(ctx, { data: dadosEtapas });
</script>
```

**Sem API externa** - Tudo server-side rendering

---

## 📊 Models Criados/Atualizados

### 1. `Oportunidade` (atualizada)

**Novos campos:**
```python
valor_previsto = DecimalField(...)           # Para previsão
valor_fechado = DecimalField(...)            # Quando ganha
probabilidade_conversao = IntegerField(...)  # 0-100%
numero_projeto = CharField(...)              # FK textual
```

### 2. `MetaVendedor` (nova)

```python
class MetaVendedor(models.Model):
    empresa = FK(Empresa)
    vendedor = FK(User)
    mes = IntegerField()
    ano = IntegerField()
    meta_valor = DecimalField()
    meta_quantidade = IntegerField()
    # ... + método calcular_realizado()
```

**Unique Together:** `[empresa, vendedor, mes, ano]`

### 3. `EtapaFunilConfig` (nova)

```python
class EtapaFunilConfig(models.Model):
    etapa = OneToOneField(EtapaFunil)
    probabilidade_padrao = IntegerField(0-100)
    sla_dias = IntegerField()
```

**Uso:** Define probabilidade padrão por etapa para novos leads

---

## 🚀 Como Usar

### 1. Acessar Dashboard

**URL:** `http://127.0.0.1:8000/crm/dashboard/`

**Ou:**
1. Menu lateral → Módulos → CRM
2. Sidebar CRM → **Dashboard BI**

### 2. Popular Dados (Primeira Vez)

```bash
python popular_dashboard_crm.py
```

**O script:**
- Configura probabilidades por etapa
- Atualiza valores previstos nas oportunidades
- Cria metas mensais para vendedores
- Mostra estatísticas e previsão

### 3. Criar Meta Manual (Admin)

```python
from crm.models import MetaVendedor
from django.contrib.auth.models import User
from usuarios.models import Empresa

MetaVendedor.objects.create(
    empresa=Empresa.objects.first(),
    vendedor=User.objects.get(username='joao'),
    mes=2,
    ano=2026,
    meta_valor=150000.00,
    meta_quantidade=8
)
```

### 4. Filtrar Dashboard

**Exemplo de Filtros:**
- Data: 01/02/2026 a 28/02/2026
- Vendedor: João Silva (admin only)
- Pipeline: Vendas Padrão

---

## 📁 Arquivos Criados/Modificados

### ✅ Criados:

```
crm/
├── services/
│   ├── __init__.py                    # Módulo services
│   └── metricas_crm.py               # BI completo (455 linhas)
├── views_dashboard.py                 # Views dashboard (222 linhas)
└── templates/crm/
    └── dashboard.html                 # Template completo (488 linhas)

scripts/
└── popular_dashboard_crm.py           # Script população (173 linhas)
```

### ✅ Modificados:

```
crm/
├── models.py                          # +4 campos Oportunidade, +2 models
├── urls.py                            # + rota dashboard
└── migrations/
    └── 0002_*.py                      # Migration automática

templates/partials/
└── sidebar.html                       # + Link Dashboard BI
```

---

## 🎯 Indicadores Implementados

| Indicador | Localização | Fonte de Dados |
|-----------|-------------|----------------|
| Total Leads | Card KPI | `Oportunidade.count()` |
| Taxa Conversão | Card KPI | `fechados/total * 100` |
| Ticket Médio | Card KPI | `Avg(valor_fechado)` |
| Tempo Médio | Card KPI | `data_fechamento - data_entrada` |
| Leads por Etapa | Gráfico Barras | `Group by etapa` |
| Performance | Gráfico Donut | Status: aberto/ganho/perdido |
| Funil Conversão | Visual Custom | `HistoricoEtapa` tracking |
| Ranking Vendedores | Tabela | `Group by responsavel` |
| Meta Mensal | Card Progressos | `MetaVendedor.calcular_realizado()` |
| Previsão Faturamento | Card | `Sum(valor * prob/100)` |

---

## 🔐 Segurança

**Controles Implementados:**

1. `@login_required` em todas as views
2. Filtro automático por vendedor (não admin)
3. Validação de filtros server-side
4. Empresa ativa verificada
5. Queries otimizadas com índices

**Permissões:**
- Admin: `is_superuser` ou `is_staff`
- Vendedor: Usuário autenticado padrão

---

## 📈 Performance

**Otimizações:**

1. **Queries ORM:**
   - `select_related()` para FKs
   - `annotate()` para agregações
   - `values()` para apenas campos necessários
   - Índices em `Oportunidade`: empresa, etapa, responsavel, status

2. **Template:**
   - JSON inline (sem requisições AJAX)
   - Gráficos rendem client-side
   - Cache de dados no contexto

3. **Cálculos:**
   - Lógica em Python (não JS)
   - Uma query por métrica
   - Reutilização de querysets

---

## ✅ Checklist Completo

- [x] Base.html padrão
- [x] Partials integradas
- [x] Visual Bootstrap/Nifty
- [x] Controle Admin vs Vendedor
- [x] Dashboard /crm/dashboard/
- [x] Separação services/views
- [x] Gráfico leads por etapa
- [x] Ranking vendedores
- [x] Gráfico performance
- [x] Gráfico funil com conversão
- [x] Filtros (data, vendedor, pipeline)
- [x] Meta mensal
- [x] Previsão faturamento
- [x] Campos preparados (valor_previsto, etc)
- [x] Models MetaVendedor
- [x] Models EtapaFunilConfig
- [x] KPIs principais
- [x] Chart.js integrado
- [x] Dados reais (ORM)
- [x] Migrations aplicadas
- [x] Script população
- [x] Sidebar atualizado
- [x] Documentação completa

---

## 🎓 Próximos Passos (Sugestões)

1. **Dashboards Personalizados**
   - Salvar configuração de filtros
   - Dashboards favoritos

2. **Alertas Inteligentes**
   - Lead parado há X dias
   - Meta em risco
   - Oportunidades quentes

3. **Relatórios Exportáveis**
   - PDF do ranking
   - Excel com dados filtrados
   - Agendamento automático

4. **Gamificação**
   - Badges por conquistas
   - Metas cumpridas
   - Leaderboard mensal

5. **Integrações**
   - WhatsApp Business API
   - E-mail marketing
   - Calendário compartilhado

---

## 📞 Suporte

**Desenvolvido por:** GitHub Copilot + Claude Sonnet 4.5  
**Data:** Fevereiro 2026  
**Sistema:** Serrana - Gestão Empresarial

**Documentação adicional:**
- `MAPA_DO_PROJETO_SERRANA.txt` - Visão geral do sistema
- `CHECKLIST_CRM.md` - Testes do módulo CRM
- `inicializar_crm.py` - Setup inicial

---

**🚀 Sistema pronto para uso em produção!**
