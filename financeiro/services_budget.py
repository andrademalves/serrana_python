"""
Services para Budget e Controle de Lucratividade
Sistema de cálculos, validações e regras de negócio
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.exceptions import ValidationError


class CalculadoraImpostos:
    """
    Calculadora de impostos baseada no regime tributário da empresa
    Provisionamento automático no fechamento da venda
    """
    
    @staticmethod
    def calcular_impostos_venda(empresa, valor_venda):
        """
        Calcula todos os impostos sobre uma venda
        
        Args:
            empresa: Instância do modelo Empresa
            valor_venda: Decimal - Valor total da venda
            
        Returns:
            dict com:
                - impostos: lista de dicionários com cada imposto
                - total_impostos: Decimal - Total de impostos
                - valor_liquido: Decimal - Valor após impostos
        """
        if not empresa.regime_tributario:
            return {
                'impostos': [],
                'total_impostos': Decimal('0.00'),
                'valor_liquido': valor_venda,
                'aviso': 'Empresa sem regime tributário configurado'
            }
        
        from financeiro.models import AliquotaImposto
        
        aliquotas = AliquotaImposto.objects.filter(
            empresa=empresa,
            regime_tributario=empresa.regime_tributario,
            ativo=True
        )
        
        impostos_calculados = []
        total_impostos = Decimal('0.00')
        
        for aliquota in aliquotas:
            # Determina base de cálculo
            if aliquota.base_calculo == 'FATURAMENTO':
                base_valor = valor_venda
            else:
                # Para outras bases, usar valor venda como padrão
                # Pode ser refinado posteriormente
                base_valor = valor_venda
            
            valor_imposto = aliquota.calcular_valor_imposto(base_valor)
            
            impostos_calculados.append({
                'tipo': aliquota.get_tipo_imposto_display(),
                'tipo_codigo': aliquota.tipo_imposto,
                'aliquota': aliquota.aliquota_percentual,
                'base_calculo': base_valor,
                'valor': valor_imposto,
                'base_descricao': aliquota.get_base_calculo_display()
            })
            
            total_impostos += valor_imposto
        
        valor_liquido = valor_venda - total_impostos
        
        return {
            'impostos': impostos_calculados,
            'total_impostos': total_impostos,
            'valor_liquido': valor_liquido,
            'percentual_total_impostos': (
                (total_impostos / valor_venda * Decimal('100.00')).quantize(Decimal('0.01'))
                if valor_venda > 0 else Decimal('0.00')
            )
        }
    
    @staticmethod
    def provisionar_impostos_orcamento(orcamento):
        """
        Cria provisionamento de impostos para um orçamento aprovado
        Pode criar títulos a pagar no financeiro
        
        Args:
            orcamento: Instância do modelo Orcamento (vendas.Orcamento)
            
        Returns:
            dict com informações do provisionamento
        """
        from vendas.models import Orcamento
        
        if not hasattr(orcamento, 'empresa'):
            # Buscar empresa via cliente ou outro relacionamento
            empresa = orcamento.cliente.empresa if hasattr(orcamento, 'cliente') else None
        else:
            empresa = orcamento.empresa
        
        if not empresa:
            raise ValidationError('Não foi possível determinar a empresa do orçamento')
        
        calculo = CalculadoraImpostos.calcular_impostos_venda(
            empresa=empresa,
            valor_venda=orcamento.valor_final
        )
        
        # TODO: Criar títulos a pagar no financeiro para cada imposto
        # Isso será implementado na integração com o módulo financeiro
        
        return calculo


class ValidadorBudget:
    """
    Validações e regras de negócio para Budget
    """
    
    @staticmethod
    def validar_lancamento_despesa(budget, valor_despesa):
        """
        Valida se uma despesa pode ser lançada no budget
        
        Args:
            budget: Instância de ProjectBudget
            valor_despesa: Decimal - Valor da despesa a ser lançada
            
        Returns:
            tuple (bool, str) - (pode_lancar, mensagem)
        """
        # Budget bloqueado
        if budget.bloqueado:
            return False, 'Budget bloqueado por estouro de limite. Necessária justificativa aprovada.'
        
        # Budget cancelado ou finalizado
        if budget.status in ['CANCELADO', 'FINALIZADO']:
            return False, f'Budget está {budget.get_status_display()}. Não é possível lançar despesas.'
        
        # Calcular novo percentual após a despesa
        from financeiro.models import ProjectExpense
        
        gastos_atuais = ProjectExpense.objects.filter(
            budget=budget,
            status__in=['APROVADO', 'PAGO']
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        gastos_projetados = gastos_atuais + valor_despesa
        
        if budget.custo_total_previsto > 0:
            percentual_projetado = (
                (gastos_projetados / budget.custo_total_previsto) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            percentual_projetado = Decimal('0.00')
        
        # Verifica limites
        if percentual_projetado >= 95:
            return False, f'Esta despesa elevaria o uso do budget para {percentual_projetado}%. Limite de segurança: 95%.'
        
        if percentual_projetado >= 80:
            return True, f'ATENÇÃO: Despesa aprovada, mas budget atingirá {percentual_projetado}% de uso (zona amarela).'
        
        return True, f'Despesa aprovada. Budget ficará em {percentual_projetado}% de uso.'
    
    @staticmethod
    def validar_budget_minimo(budget):
        """
        Valida se budget tem valores mínimos preenchidos
        
        Args:
            budget: Instância de ProjectBudget
            
        Returns:
            tuple (bool, list) - (valido, lista_erros)
        """
        erros = []
        
        if budget.custo_total_previsto <= 0:
            erros.append('Custo total previsto deve ser maior que zero')
        
        if budget.valor_venda <= 0:
            erros.append('Valor de venda deve ser maior que zero')
        
        if budget.valor_venda < budget.custo_total_previsto:
            erros.append('Valor de venda não pode ser menor que o custo previsto (operação com prejuízo)')
        
        if budget.margem_prevista_percentual < 0:
            erros.append('Margem prevista está negativa - revisar custos ou valor de venda')
        
        return len(erros) == 0, erros


class AnalisadorPerformance:
    """
    Análise de performance de vendedores e instaladores
    Cálculo de KPIs e alertas
    """
    
    @staticmethod
    def calcular_assertividade_vendedor(vendedor, periodo_inicio=None, periodo_fim=None):
        """
        Calcula assertividade do vendedor (Lucro Orçado vs Lucro Real)
        
        Args:
            vendedor: Instância de Pessoa (vendedor=True)
            periodo_inicio: date opcional
            periodo_fim: date opcional
            
        Returns:
            dict com métricas de performance
        """
        from financeiro.models import ProjectBudget
        from projetos.models import Projeto
        
        # Filtrar budgets de projetos deste vendedor
        query = ProjectBudget.objects.filter(
            projeto__orcamento__vendedor=vendedor,
            status__in=['EM_EXECUCAO', 'FINALIZADO']
        )
        
        if periodo_inicio:
            query = query.filter(criado_em__gte=periodo_inicio)
        if periodo_fim:
            query = query.filter(criado_em__lte=periodo_fim)
        
        total_projetos = query.count()
        
        if total_projetos == 0:
            return {
                'vendedor': vendedor.nome,
                'total_projetos': 0,
                'assertividade_media': 0,
                'vendas_com_prejuizo': 0,
                'alerta': 'Nenhum projeto no período'
            }
        
        # Análise por projeto
        projetos_analisados = []
        total_assertividade = Decimal('0.00')
        vendas_prejuizo = 0
        
        for budget in query:
            lucro_orcado = budget.lucro_previsto
            
            # Lucro real = valor venda - gastos reais
            from financeiro.models import ProjectExpense
            gastos_reais = ProjectExpense.objects.filter(
                budget=budget,
                status__in=['APROVADO', 'PAGO']
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            lucro_real = budget.valor_venda - gastos_reais
            
            # Assertividade: quão próximo o lucro real ficou do orçado
            if lucro_orcado > 0:
                assertividade = (lucro_real / lucro_orcado * Decimal('100.00')).quantize(Decimal('0.01'))
            else:
                assertividade = Decimal('0.00')
            
            total_assertividade += assertividade
            
            if lucro_real < 0:
                vendas_prejuizo += 1
            
            projetos_analisados.append({
                'projeto': str(budget.projeto) if budget.projeto else budget.codigo,
                'lucro_orcado': lucro_orcado,
                'lucro_real': lucro_real,
                'assertividade': assertividade,
                'prejuizo': lucro_real < 0
            })
        
        assertividade_media = (total_assertividade / total_projetos).quantize(Decimal('0.01'))
        
        # Determinar alerta
        if vendas_prejuizo > 0:
            alerta = f'CRÍTICO: {vendas_prejuizo} venda(s) com prejuízo'
        elif assertividade_media < 70:
            alerta = 'ATENÇÃO: Assertividade abaixo de 70%'
        elif assertividade_media < 85:
            alerta = 'Assertividade OK, mas pode melhorar'
        else:
            alerta = 'Excelente performance'
        
        return {
            'vendedor': vendedor.nome,
            'total_projetos': total_projetos,
            'assertividade_media': assertividade_media,
            'vendas_com_prejuizo': vendas_prejuizo,
            'projetos': projetos_analisados,
            'alerta': alerta
        }
    
    @staticmethod
    def calcular_indice_retrabalho_instalador(instalador, periodo_inicio=None, periodo_fim=None):
        """
        Calcula índice de retrabalho do instalador
        Identifica visitas extras ao mesmo projeto
        
        Args:
            instalador: Instância de Pessoa (funcionario=True)
            periodo_inicio: date opcional
            periodo_fim: date opcional
            
        Returns:
            dict com métricas de retrabalho
        """
        from financeiro.models import ProjectExpense
        
        # Buscar despesas de mão de obra deste instalador
        query = ProjectExpense.objects.filter(
            funcionario=instalador,
            tipo_despesa__in=['MAO_OBRA', 'RETRABALHO']
        )
        
        if periodo_inicio:
            query = query.filter(data_despesa__gte=periodo_inicio)
        if periodo_fim:
            query = query.filter(data_despesa__lte=periodo_fim)
        
        # Agrupar por budget (projeto)
        budgets_trabalhados = query.values('budget').distinct()
        
        total_projetos = budgets_trabalhados.count()
        
        if total_projetos == 0:
            return {
                'instalador': instalador.nome,
                'total_projetos': 0,
                'visitas_retrabalho': 0,
                'indice_retrabalho': 0,
                'alerta': 'Nenhum projeto no período'
            }
        
        # Analisar cada projeto
        projetos_com_retrabalho = 0
        total_visitas_retrabalho = 0
        total_desperdicio = Decimal('0.00')
        
        detalhes_projetos = []
        
        for budget_data in budgets_trabalhados:
            budget_id = budget_data['budget']
            
            # Contar visitas ao mesmo projeto
            visitas = ProjectExpense.objects.filter(
                budget_id=budget_id,
                funcionario=instalador,
                tipo_despesa='MAO_OBRA'
            ).count()
            
            # Contar retrabalhos
            retrabalhos = ProjectExpense.objects.filter(
                budget_id=budget_id,
                funcionario=instalador,
                tipo_despesa='RETRABALHO'
            ).count()
            
            # Desperdício de material
            desperdicio = ProjectExpense.objects.filter(
                budget_id=budget_id,
                funcionario=instalador,
                tipo_despesa='DESPERDICIO'
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            
            if retrabalhos > 0 or visitas > 1:
                projetos_com_retrabalho += 1
                total_visitas_retrabalho += retrabalhos
                total_desperdicio += desperdicio
                
                detalhes_projetos.append({
                    'budget_id': budget_id,
                    'visitas': visitas,
                    'retrabalhos': retrabalhos,
                    'desperdicio': desperdicio
                })
        
        # Índice de retrabalho: % de projetos com retrabalho
        indice_retrabalho = (
            (Decimal(projetos_com_retrabalho) / Decimal(total_projetos) * Decimal('100.00'))
            .quantize(Decimal('0.01'))
        )
        
        # Determinar alerta
        if indice_retrabalho > 30:
            alerta = 'CRÍTICO: Índice de retrabalho muito alto (>30%)'
        elif indice_retrabalho > 15:
            alerta = 'ATENÇÃO: Índice de retrabalho elevado (>15%)'
        elif indice_retrabalho > 5:
            alerta = 'Índice de retrabalho dentro do aceitável'
        else:
            alerta = 'Excelente - Baixo índice de retrabalho'
        
        return {
            'instalador': instalador.nome,
            'total_projetos': total_projetos,
            'projetos_com_retrabalho': projetos_com_retrabalho,
            'indice_retrabalho': indice_retrabalho,
            'total_visitas_retrabalho': total_visitas_retrabalho,
            'total_desperdicio': total_desperdicio,
            'detalhes': detalhes_projetos,
            'alerta': alerta
        }


class GeradorRelatorios:
    """
    Gerador de relatórios gerenciais de Budget
    """
    
    @staticmethod
    def relatorio_projetos_criticos():
        """
        Lista projetos em situação crítica (semáforo vermelho ou amarelo)
        
        Returns:
            dict com listas de projetos críticos
        """
        from financeiro.models import ProjectBudget
        
        vermelhos = ProjectBudget.objects.filter(
            semaforo='VERMELHO',
            status__in=['EM_EXECUCAO']
        ).select_related('projeto', 'empresa')
        
        amarelos = ProjectBudget.objects.filter(
            semaforo='AMARELO',
            status__in=['EM_EXECUCAO']
        ).select_related('projeto', 'empresa')
        
        return {
            'criticos': [{
                'budget': b.codigo,
                'projeto': str(b.projeto) if b.projeto else b.descricao,
                'percentual_uso': b.percentual_uso_budget,
                'bloqueado': b.bloqueado,
                'empresa': b.empresa.nome_fantasia
            } for b in vermelhos],
            'alertas': [{
                'budget': b.codigo,
                'projeto': str(b.projeto) if b.projeto else b.descricao,
                'percentual_uso': b.percentual_uso_budget,
                'empresa': b.empresa.nome_fantasia
            } for b in amarelos]
        }
    
    @staticmethod
    def relatorio_lucratividade_geral(empresa, periodo_inicio=None, periodo_fim=None):
        """
        Relatório geral de lucratividade da empresa
        
        Args:
            empresa: Instância de Empresa
            periodo_inicio: date opcional
            periodo_fim: date opcional
            
        Returns:
            dict com métricas gerais
        """
        from financeiro.models import ProjectBudget, ProjectExpense
        
        query = ProjectBudget.objects.filter(empresa=empresa)
        
        if periodo_inicio:
            query = query.filter(criado_em__gte=periodo_inicio)
        if periodo_fim:
            query = query.filter(criado_em__lte=periodo_fim)
        
        # Totalizadores
        total_budgets = query.count()
        total_valor_vendas = query.aggregate(total=Sum('valor_venda'))['total'] or Decimal('0.00')
        total_custo_previsto = query.aggregate(total=Sum('custo_total_previsto'))['total'] or Decimal('0.00')
        total_lucro_previsto = query.aggregate(total=Sum('lucro_previsto'))['total'] or Decimal('0.00')
        
        # Custos reais
        despesas_query = ProjectExpense.objects.filter(
            budget__empresa=empresa,
            status__in=['APROVADO', 'PAGO']
        )
        
        if periodo_inicio:
            despesas_query = despesas_query.filter(data_despesa__gte=periodo_inicio)
        if periodo_fim:
            despesas_query = despesas_query.filter(data_despesa__lte=periodo_fim)
        
        total_custo_real = despesas_query.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Lucro real
        total_lucro_real = total_valor_vendas - total_custo_real
        
        # Margens
        margem_prevista = (
            (total_lucro_previsto / total_valor_vendas * Decimal('100.00')).quantize(Decimal('0.01'))
            if total_valor_vendas > 0 else Decimal('0.00')
        )
        
        margem_real = (
            (total_lucro_real / total_valor_vendas * Decimal('100.00')).quantize(Decimal('0.01'))
            if total_valor_vendas > 0 else Decimal('0.00')
        )
        
        return {
            'empresa': empresa.nome_fantasia,
            'periodo': {
                'inicio': periodo_inicio,
                'fim': periodo_fim
            },
            'total_budgets': total_budgets,
            'valor_vendas': total_valor_vendas,
            'custo_previsto': total_custo_previsto,
            'custo_real': total_custo_real,
            'lucro_previsto': total_lucro_previsto,
            'lucro_real': total_lucro_real,
            'margem_prevista': margem_prevista,
            'margem_real': margem_real,
            'desvio_custos': total_custo_real - total_custo_previsto,
            'desvio_lucro': total_lucro_real - total_lucro_previsto
        }
