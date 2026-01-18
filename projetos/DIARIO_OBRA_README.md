# Diário da Obra - Documentação

## Visão Geral

O **Diário da Obra** é uma funcionalidade completa para registro diário das atividades executadas em projetos/obras. Permite documentar de forma estruturada todas as informações relevantes do dia a dia da execução, incluindo equipe, clima, materiais, problemas e segurança.

## Características Principais

### 📋 Informações Registradas

#### 1. Informações Básicas
- **Data**: Data do registro
- **Período**: Manhã, Tarde, Dia Integral ou Noite
- **Clima**: Ensolarado, Nublado, Chuvoso ou Tempestade
- **Temperatura**: Temperatura do dia (opcional)

#### 2. Equipe e Recursos
- **Número de Trabalhadores**: Quantidade de trabalhadores presentes
- **Descrição da Equipe**: Funções e nomes dos trabalhadores
- **Equipamentos Utilizados**: Lista dos equipamentos usados no dia

#### 3. Atividades
- **Atividades Realizadas**: Descrição detalhada das atividades executadas
- **Percentual de Progresso**: Percentual de conclusão das atividades planejadas (0-100%)

#### 4. Materiais
- **Materiais Recebidos**: Materiais que chegaram na obra
- **Materiais Utilizados**: Materiais consumidos durante o dia

#### 5. Problemas e Soluções
- **Problemas Encontrados**: Descrição de problemas ou imprevistos
- **Soluções Aplicadas**: Como os problemas foram resolvidos
- **Visitas e Fiscalização**: Registro de visitas de fiscais, engenheiros, clientes

#### 6. Segurança do Trabalho
- **Incidentes de Segurança**: Acidentes, quase-acidentes ou questões de segurança
- **EPIs Utilizados**: Flag indicando se todos usaram EPIs adequados

#### 7. Observações Gerais
- Campo livre para outras informações relevantes

## Funcionalidades

### CRUD Completo
- ✅ **Criar** nova entrada no diário
- ✅ **Visualizar** entradas existentes
- ✅ **Editar** entradas
- ✅ **Deletar** entradas (com confirmação)

### Listagem e Filtros
- **Filtros disponíveis**:
  - Data Início
  - Data Fim
  - Período (Manhã/Tarde/Integral/Noite)
- **Estatísticas**:
  - Total de registros
  - Média de trabalhadores
  - Status do projeto

### Visualização Rica
- Cards coloridos por categoria
- Ícones para clima (sol, nuvem, chuva, raio)
- Barra de progresso visual
- Badges para EPIs e status
- Destaque para problemas e soluções

## URLs da Funcionalidade

```python
# Listagem do diário de um projeto
/projetos/<projeto_id>/diario/

# Adicionar nova entrada
/projetos/<projeto_id>/diario/adicionar/

# Visualizar entrada específica
/diario/<pk>/

# Editar entrada
/diario/<pk>/editar/

# Deletar entrada
/diario/<pk>/deletar/
```

## Acesso à Funcionalidade

### 1. Pela Listagem de Projetos
- Acesse **Projetos** → **Listar Projetos**
- Clique no botão verde com ícone de livro **📖** na coluna Ações

### 2. Pela Visualização do Projeto
- Acesse um projeto específico
- Clique no botão **"Diário da Obra"** no topo da página

### 3. Pelo Admin Django
- Acesse `/admin/projetos/diarioobra/`

## Modelo de Dados

### DiarioObra

```python
class DiarioObra(models.Model):
    # Relacionamento
    projeto = ForeignKey(Projeto)
    
    # Básico
    data = DateField
    periodo = CharField (MANHA, TARDE, INTEGRAL, NOITE)
    clima = CharField (ENSOLARADO, NUBLADO, CHUVOSO, TEMPESTADE)
    temperatura = CharField
    
    # Equipe
    num_trabalhadores = IntegerField
    equipe_descricao = TextField
    equipamentos_utilizados = TextField
    
    # Atividades
    atividades_realizadas = TextField (obrigatório)
    percentual_progresso = DecimalField (0-100)
    
    # Materiais
    materiais_recebidos = TextField
    materiais_utilizados = TextField
    
    # Problemas
    problemas_encontrados = TextField
    solucoes_aplicadas = TextField
    visitas_fiscalizacao = TextField
    
    # Segurança
    incidentes_seguranca = TextField
    epi_utilizado = BooleanField
    
    # Geral
    observacoes = TextField
    
    # Auditoria
    criado_em, criado_por
    atualizado_em, atualizado_por
```

### Constraints
- **unique_together**: `['projeto', 'data', 'periodo']` 
  - Evita duplicação de registro para mesmo dia/período

## Admin Interface

Registrado no Django Admin com:
- **Filtros**: Data, Período, Clima, EPIs
- **Busca**: Código do projeto, descrição, atividades
- **Hierarquia**: Por data
- **Fieldsets organizados**:
  - Informações Básicas
  - Equipe e Recursos
  - Atividades
  - Materiais (collapsible)
  - Problemas e Soluções (collapsible)
  - Segurança
  - Observações (collapsible)
  - Auditoria (collapsible)

## Benefícios

### 1. Documentação Legal
- Registro cronológico completo da obra
- Comprovação de execução de atividades
- Evidência para questões trabalhistas
- Histórico para auditorias

### 2. Gestão de Qualidade
- Rastreabilidade de problemas e soluções
- Controle de progresso diário
- Registro de visitas técnicas
- Documentação de decisões

### 3. Segurança do Trabalho
- Registro de uso de EPIs
- Histórico de incidentes
- Evidência de conformidade
- Base para treinamentos

### 4. Gestão de Materiais
- Controle de recebimento
- Registro de consumo
- Rastreabilidade de uso

### 5. Gestão de Equipe
- Registro de presença
- Controle de produtividade
- Histórico de alocação

## Melhorias Futuras

### Recursos Planejados
- [ ] **Upload de Fotos**: Anexar fotos do dia
- [ ] **Assinatura Digital**: Responsável técnico assina diário
- [ ] **Exportação PDF**: Gerar relatório em PDF
- [ ] **Dashboard Analytics**: Gráficos de produtividade
- [ ] **Integração com Estoque**: Link direto com consumo de materiais
- [ ] **Notificações**: Alertas de problemas críticos
- [ ] **Comparação de Progresso**: vs. planejamento inicial
- [ ] **Registro de Horas**: Por trabalhador/atividade
- [ ] **Condições Climáticas API**: Puxar dados reais de clima
- [ ] **Template de Atividades**: Atividades padrão pré-cadastradas

## Exemplo de Uso

### Fluxo Típico

1. **Início do dia/Fim do dia**:
   - Acesse o projeto
   - Clique em "Diário da Obra"
   - Clique em "Nova Entrada"

2. **Preencha as informações**:
   - Selecione data e período
   - Informe clima e temperatura
   - Registre equipe e equipamentos
   - Descreva atividades realizadas
   - Informe progresso (%)
   - Registre materiais (se houver)
   - Documente problemas e soluções (se houver)
   - Marque uso de EPIs
   - Adicione observações

3. **Salve o registro**:
   - Clique em "Salvar"
   - Registro fica disponível para consulta

4. **Consulta posterior**:
   - Use filtros de data para encontrar registros
   - Visualize estatísticas
   - Exporte relatórios

## Permissões

A funcionalidade respeita o sistema de permissões do módulo Projetos:
- Requer login (`@login_required`)
- Requer empresa selecionada (`@require_empresa`)
- Requer permissão no menu `/projetos/` (`@verificar_permissao_menu`)

## Migration

```bash
# Criada automaticamente
python manage.py makemigrations projetos
# Output: projetos/migrations/0015_diarioobra.py

# Aplicada ao banco
python manage.py migrate projetos
# Output: Applying projetos.0015_diarioobra... OK
```

## Arquivos Criados/Modificados

### Novos Arquivos
- `projetos/templates/projetos/diario/listar_diario_obra.html`
- `projetos/templates/projetos/diario/form_diario_obra.html`
- `projetos/templates/projetos/diario/visualizar_diario_obra.html`
- `projetos/templates/projetos/diario/deletar_diario_obra.html`
- `projetos/migrations/0015_diarioobra.py`

### Arquivos Modificados
- `projetos/models.py` - Modelo DiarioObra
- `projetos/views.py` - 5 views (listar, adicionar, visualizar, editar, deletar)
- `projetos/forms.py` - DiarioObraForm
- `projetos/urls.py` - 5 URLs
- `projetos/admin.py` - DiarioObraAdmin
- `projetos/templates/projetos/visualizar_projeto.html` - Botão "Diário da Obra"
- `projetos/templates/projetos/listar_projetos.html` - Botão na listagem

## Suporte

Para dúvidas ou problemas:
1. Verifique se as migrations foram aplicadas
2. Confirme permissões do usuário
3. Verifique logs do Django para erros
4. Consulte o Admin para verificação de dados

---

**Versão**: 1.0
**Data**: Janeiro 2026
**Autor**: Sistema Serrana Empresarial
