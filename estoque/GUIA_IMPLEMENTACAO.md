# Guia de Implementação - Novo Sistema de Estoque

## 📋 Checklist de Implementação

### Fase 1: Preparação (1-2 horas)

- [ ] **1.1. Backup Completo**
  ```powershell
  # Fazer backup do banco de dados
  python manage.py dumpdata > backup_antes_estoque.json
  
  # Fazer backup dos arquivos
  # Copiar pasta inteira para local seguro
  ```

- [ ] **1.2. Revisar Documentação**
  - Ler [NOVO_MODELO_ESTOQUE.md](NOVO_MODELO_ESTOQUE.md)
  - Entender o novo modelo de dados
  - Revisar regras de negócio (WAC, movimentações, etc)

- [ ] **1.3. Preparar Ambiente**
  ```powershell
  # Criar branch no git (se usar)
  git checkout -b feature/novo-estoque
  
  # Instalar dependências (se houver novas)
  pip install -r requirements.txt
  ```

---

### Fase 2: Implementação do Código (2-3 horas)

- [ ] **2.1. Substituir Arquivos**
  
  **Models:**
  ```powershell
  # Backup do antigo
  Copy-Item estoque\models.py estoque\models_old.py
  
  # O novo já está em models.py (você já criou)
  ```
  
  **Forms:**
  ```powershell
  # Criar/substituir forms.py
  # Arquivo: estoque\forms.py (já criado)
  ```
  
  **Views:**
  ```powershell
  # Backup do antigo
  Copy-Item estoque\views.py estoque\views_old.py
  
  # Substituir pelo novo
  Copy-Item estoque\views_new.py estoque\views.py
  ```
  
  **URLs:**
  ```powershell
  # Backup do antigo
  Copy-Item estoque\urls.py estoque\urls_old.py
  
  # Substituir pelo novo
  Copy-Item estoque\urls_new.py estoque\urls.py
  ```
  
  **Admin:**
  ```powershell
  # Backup do antigo
  Copy-Item estoque\admin.py estoque\admin_old.py
  
  # Substituir pelo novo
  Copy-Item estoque\admin_new.py estoque\admin.py
  ```

- [ ] **2.2. Criar Migrations**
  ```powershell
  # Criar migrations para os novos models
  python manage.py makemigrations estoque
  
  # Revisar as migrations criadas
  # Verificar se está tudo correto
  ```

- [ ] **2.3. Verificar Erros**
  ```powershell
  # Verificar sintaxe Python
  python manage.py check
  
  # Se houver erros, corrija antes de prosseguir
  ```

---

### Fase 3: Migração do Banco de Dados (1-2 horas)

- [ ] **3.1. Aplicar Migrations (Teste)**
  ```powershell
  # IMPORTANTE: Fazer em ambiente de teste primeiro!
  # Ou usar --dry-run se disponível
  
  python manage.py migrate estoque --plan
  # Revisar o plano de migração
  
  # Se tudo OK, aplicar
  python manage.py migrate estoque
  ```

- [ ] **3.2. Criar Dados Iniciais**
  ```powershell
  # Executar comando de migração em modo dry-run primeiro
  python manage.py migrar_estoque_antigo --dry-run
  
  # Revisar saída e corrigir problemas
  
  # Se tudo OK, executar para valer
  python manage.py migrar_estoque_antigo
  ```

- [ ] **3.3. Validar Migração**
  ```powershell
  # Verificar dados migrados
  python manage.py shell
  ```
  ```python
  from estoque.models import Item, LocalEstoque, MovimentoEstoque, SaldoEstoque
  
  # Verificar itens
  print(f"Itens criados: {Item.objects.count()}")
  
  # Verificar locais
  print(f"Locais criados: {LocalEstoque.objects.count()}")
  
  # Verificar movimentos
  print(f"Movimentos criados: {MovimentoEstoque.objects.count()}")
  
  # Verificar saldos
  print(f"Saldos criados: {SaldoEstoque.objects.count()}")
  
  # Mostrar alguns exemplos
  for item in Item.objects.all()[:5]:
      print(f"  {item.codigo}: {item.descricao}")
  ```

---

### Fase 4: Templates (3-4 horas)

Como templates são personalizados, você precisará criar baseado nos existentes:

- [ ] **4.1. Templates de Cadastro**
  - `estoque/templates/estoque/form_item.html`
  - `estoque/templates/estoque/form_local.html`
  - `estoque/templates/estoque/form_destino.html`

- [ ] **4.2. Templates de Listagem**
  - `estoque/templates/estoque/listar_itens.html`
  - `estoque/templates/estoque/listar_locais.html`
  - `estoque/templates/estoque/listar_destinos.html`
  - `estoque/templates/estoque/listar_movimentos.html`

- [ ] **4.3. Templates de Movimentação**
  - `estoque/templates/estoque/form_movimento.html` (genérico para todos os tipos)

- [ ] **4.4. Templates de Relatórios**
  - `estoque/templates/estoque/relatorio_posicao.html`
  - `estoque/templates/estoque/relatorio_minimo.html`
  - `estoque/templates/estoque/relatorio_valorizacao.html`
  - `estoque/templates/estoque/relatorio_consumo_projeto.html`

- [ ] **4.5. Dashboard Atualizado**
  - `estoque/templates/estoque/dashboard.html`

**Dica:** Use o template atual como base e adapte para os novos campos/modelos.

---

### Fase 5: Testes (2-3 horas)

- [ ] **5.1. Testes Manuais de Cadastro**
  - Criar um item novo
  - Criar um local novo
  - Criar um destino novo
  - Verificar validações

- [ ] **5.2. Testes de Movimentação**
  - Registrar uma entrada
  - Verificar se saldo foi atualizado
  - Verificar se custo médio foi calculado
  - Registrar uma saída
  - Verificar se saldo foi reduzido
  - Testar transferência entre locais
  - Testar ajuste de estoque

- [ ] **5.3. Testes de Validação**
  - Tentar saída sem saldo (deve dar erro)
  - Tentar transferência para mesmo local (deve dar erro)
  - Tentar saída sem destino (deve dar erro)
  - Testar todas as validações do modelo

- [ ] **5.4. Testes de Relatórios**
  - Verificar posição de estoque
  - Verificar itens abaixo do mínimo
  - Verificar valorização
  - Verificar consumo por projeto (se tiver projetos)

- [ ] **5.5. Testes de Performance**
  - Verificar tempo de carregamento das telas
  - Verificar queries (usar Django Debug Toolbar)
  - Otimizar se necessário

---

### Fase 6: Ajustes e Melhorias (1-2 horas)

- [ ] **6.1. Ajustar Templates**
  - Melhorar layout/CSS
  - Adicionar botões de ação
  - Melhorar UX

- [ ] **6.2. Adicionar Permissões**
  - Configurar permissões por grupo de usuário
  - Testar acesso de diferentes perfis

- [ ] **6.3. Documentação de Usuário**
  - Criar manual básico de uso
  - Documentar fluxos principais

---

### Fase 7: Deploy em Produção (1 hora)

- [ ] **7.1. Preparar Produção**
  ```powershell
  # Fazer backup COMPLETO do banco de produção
  # Copiar arquivos novos para servidor
  # Testar em ambiente de homologação se possível
  ```

- [ ] **7.2. Executar em Produção**
  ```powershell
  # Parar servidor (se necessário)
  
  # Aplicar migrations
  python manage.py migrate estoque
  
  # Executar migração de dados
  python manage.py migrar_estoque_antigo
  
  # Verificar saldos
  python manage.py recalcular_saldos_estoque --dry-run
  
  # Se OK, recalcular para valer
  python manage.py recalcular_saldos_estoque
  
  # Coletar statics
  python manage.py collectstatic --noinput
  
  # Reiniciar servidor
  ```

- [ ] **7.3. Validação Pós-Deploy**
  - Acessar sistema
  - Verificar dados
  - Testar operações básicas
  - Monitorar logs de erro

---

## 🔧 Comandos Úteis

### Criar Dados de Teste
```powershell
python manage.py shell
```
```python
from django.contrib.auth.models import User
from estoque.models import *
from decimal import Decimal

# Criar local
local = LocalEstoque.objects.create(
    codigo='ALMOX01',
    descricao='Almoxarifado Geral',
    ativo=True
)

# Criar destino
destino = DestinoEstoque.objects.create(
    codigo='LOJA',
    descricao='Loja Pronta Entrega',
    tipo='LOJA',
    controla_custo=True,
    ativo=True
)

# Criar item
item = Item.objects.create(
    codigo='TEST001',
    descricao='Item de Teste',
    tipo_item='MP',
    unidade_medida='UN',
    estoque_minimo=Decimal('10.000'),
    ativo=True
)

print("Dados de teste criados!")
```

### Verificar Saldos
```python
from estoque.models import SaldoEstoque

for saldo in SaldoEstoque.objects.all()[:10]:
    print(f"{saldo.item.codigo} @ {saldo.local.codigo}: {saldo.quantidade} (R$ {saldo.custo_medio})")
```

### Consultar Movimentações
```python
from estoque.models import MovimentoEstoque

movimentos = MovimentoEstoque.objects.all()[:10]
for mov in movimentos:
    print(f"{mov.data_movimento} - {mov.tipo_movimento} - {mov.item.codigo} - {mov.quantidade}")
```

---

## ⚠️ Problemas Comuns e Soluções

### Erro: "Saldo insuficiente"
**Causa:** Tentando saída sem saldo disponível  
**Solução:** 
1. Verificar saldo: `SaldoEstoque.objects.get(item=..., local=...)`
2. Registrar entrada antes da saída
3. Ou ajustar estoque

### Erro: "Item não possui saldo no local"
**Causa:** Item nunca teve entrada no local  
**Solução:** Registrar entrada primeiro ou criar saldo inicial com ajuste

### Erro: "Local origem e destino não podem ser iguais"
**Causa:** Transferência para mesmo local  
**Solução:** Escolher local diferente

### Custo Médio Incorreto
**Causa:** Movimentos fora de ordem ou erro de cálculo  
**Solução:** 
```powershell
python manage.py recalcular_saldos_estoque
```

### Migrations com Conflito
**Causa:** Mudanças no banco que não batem com models  
**Solução:**
```powershell
# Reverter migrations
python manage.py migrate estoque zero

# Refazer
python manage.py migrate estoque
```

---

## 📊 Validação Final

Após implementação, validar:

✅ Todos os itens foram migrados  
✅ Saldos estão corretos  
✅ Custo médio está calculado  
✅ Movimentações funcionam  
✅ Relatórios exibem dados  
✅ Validações estão ativas  
✅ Performance está adequada  
✅ Usuários conseguem operar  

---

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. Verificar logs de erro: `python manage.py runserver` ou logs do servidor
2. Consultar documentação: `NOVO_MODELO_ESTOQUE.md`
3. Usar Django shell para investigar: `python manage.py shell`
4. Verificar este guia de implementação

---

## ✨ Próximos Passos (Futuro)

Após MVP estável, considerar:

- [ ] Implementar BOM (Bill of Materials) completo
- [ ] Implementar Ordens de Produção
- [ ] Relatórios mais avançados (gráficos, dashboards)
- [ ] Integração com compras
- [ ] Integração com vendas
- [ ] API REST para mobile/integrações
- [ ] Código de barras
- [ ] Inventário rotativo
- [ ] Lote e validade (para itens que precisam)

---

**Boa implementação! 🚀**
