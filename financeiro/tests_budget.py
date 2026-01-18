"""
Testes para validar o módulo de Budget e Cálculo de Impostos
Execute: python manage.py test financeiro.tests_budget
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from usuarios.models import Empresa
from cadastros.models import Pessoa
from financeiro.models import (
    RegimeTributario, AliquotaImposto, ProjectBudget, 
    ProjectExpense, JustificativaBudget
)
from financeiro.services_budget import (
    CalculadoraImpostos, ValidadorBudget, AnalisadorPerformance
)


class RegimeTributarioTestCase(TestCase):
    """Testes para Regime Tributário"""
    
    def setUp(self):
        self.regime = RegimeTributario.objects.create(
            nome='SIMPLES_NACIONAL',
            descricao='Simples Nacional para testes'
        )
    
    def test_criar_regime(self):
        """Teste criação de regime tributário"""
        self.assertEqual(self.regime.nome, 'SIMPLES_NACIONAL')
        self.assertTrue(self.regime.ativo)
    
    def test_str_representation(self):
        """Teste representação string"""
        self.assertEqual(str(self.regime), 'Simples Nacional')


class AliquotaImpostoTestCase(TestCase):
    """Testes para Alíquotas de Impostos"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.regime = RegimeTributario.objects.create(
            nome='LUCRO_PRESUMIDO',
            descricao='Lucro Presumido'
        )
        
        self.aliquota = AliquotaImposto.objects.create(
            empresa=self.empresa,
            regime_tributario=self.regime,
            tipo_imposto='IRPJ',
            aliquota_percentual=Decimal('1.20'),
            base_calculo='FATURAMENTO',
            criado_por=self.user
        )
    
    def test_criar_aliquota(self):
        """Teste criação de alíquota"""
        self.assertEqual(self.aliquota.tipo_imposto, 'IRPJ')
        self.assertEqual(self.aliquota.aliquota_percentual, Decimal('1.20'))
    
    def test_calcular_valor_imposto(self):
        """Teste cálculo de valor de imposto"""
        base_valor = Decimal('10000.00')
        valor_imposto = self.aliquota.calcular_valor_imposto(base_valor)
        self.assertEqual(valor_imposto, Decimal('120.00'))
    
    def test_aliquota_inativa_retorna_zero(self):
        """Teste que alíquota inativa retorna zero"""
        self.aliquota.ativo = False
        valor_imposto = self.aliquota.calcular_valor_imposto(Decimal('10000.00'))
        self.assertEqual(valor_imposto, Decimal('0.00'))


class CalculadoraImpostosTestCase(TestCase):
    """Testes para Calculadora de Impostos"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.regime = RegimeTributario.objects.create(
            nome='LUCRO_PRESUMIDO'
        )
        
        self.empresa.regime_tributario = self.regime
        self.empresa.save()
        
        # Criar alíquotas de teste
        AliquotaImposto.objects.create(
            empresa=self.empresa,
            regime_tributario=self.regime,
            tipo_imposto='IRPJ',
            aliquota_percentual=Decimal('1.20'),
            base_calculo='FATURAMENTO',
            criado_por=self.user
        )
        
        AliquotaImposto.objects.create(
            empresa=self.empresa,
            regime_tributario=self.regime,
            tipo_imposto='CSLL',
            aliquota_percentual=Decimal('1.08'),
            base_calculo='FATURAMENTO',
            criado_por=self.user
        )
        
        AliquotaImposto.objects.create(
            empresa=self.empresa,
            regime_tributario=self.regime,
            tipo_imposto='PIS',
            aliquota_percentual=Decimal('0.65'),
            base_calculo='FATURAMENTO',
            criado_por=self.user
        )
    
    def test_calcular_impostos_venda(self):
        """Teste cálculo de impostos sobre venda"""
        valor_venda = Decimal('10000.00')
        
        resultado = CalculadoraImpostos.calcular_impostos_venda(
            empresa=self.empresa,
            valor_venda=valor_venda
        )
        
        # Verificar estrutura do resultado
        self.assertIn('impostos', resultado)
        self.assertIn('total_impostos', resultado)
        self.assertIn('valor_liquido', resultado)
        
        # Verificar cálculos
        # IRPJ: 10000 * 1.20% = 120
        # CSLL: 10000 * 1.08% = 108
        # PIS:  10000 * 0.65% = 65
        # Total: 293
        
        self.assertEqual(len(resultado['impostos']), 3)
        self.assertEqual(resultado['total_impostos'], Decimal('293.00'))
        self.assertEqual(resultado['valor_liquido'], Decimal('9707.00'))
    
    def test_empresa_sem_regime(self):
        """Teste com empresa sem regime tributário"""
        empresa_sem_regime = Empresa.objects.create(
            razao_social='Empresa Sem Regime',
            nome_fantasia='Sem Regime',
            cnpj='98.765.432/0001-10',
            slug='sem-regime'
        )
        
        resultado = CalculadoraImpostos.calcular_impostos_venda(
            empresa=empresa_sem_regime,
            valor_venda=Decimal('10000.00')
        )
        
        self.assertIn('aviso', resultado)
        self.assertEqual(resultado['total_impostos'], Decimal('0.00'))


class ProjectBudgetTestCase(TestCase):
    """Testes para Budget de Projeto"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.budget = ProjectBudget.objects.create(
            empresa=self.empresa,
            descricao='Budget de Teste',
            custo_aluminio_previsto=Decimal('5000.00'),
            custo_vidro_previsto=Decimal('3000.00'),
            custo_acessorios_previsto=Decimal('1000.00'),
            km_estimado=Decimal('100.00'),
            valor_combustivel_litro=Decimal('5.50'),
            consumo_medio_km_litro=Decimal('10.00'),
            horas_fabricacao_previstas=Decimal('20.00'),
            valor_hora_fabricacao=Decimal('35.00'),
            horas_montagem_previstas=Decimal('10.00'),
            valor_hora_montagem=Decimal('45.00'),
            valor_venda=Decimal('15000.00'),
            criado_por=self.user
        )
    
    def test_criar_budget(self):
        """Teste criação de budget"""
        self.assertIsNotNone(self.budget.codigo)
        self.assertTrue(self.budget.codigo.startswith('BDG-'))
    
    def test_calcular_totais(self):
        """Teste cálculo automático de totais"""
        # Materiais: 5000 + 3000 + 1000 = 9000
        # Combustível: (100 / 10) * 5.50 = 55
        # Mão de obra fabricação: 20 * 35 = 700
        # Mão de obra montagem: 10 * 45 = 450
        # Total: 9000 + 55 + 700 + 450 = 10205
        
        self.assertEqual(self.budget.get_custo_material_total(), Decimal('9000.00'))
        self.assertEqual(self.budget.get_custo_operacional_total(), Decimal('55.00'))
        self.assertEqual(self.budget.get_custo_mao_obra_total(), Decimal('1150.00'))
        self.assertEqual(self.budget.custo_total_previsto, Decimal('10205.00'))
        
        # Lucro: 15000 - 10205 = 4795
        self.assertEqual(self.budget.lucro_previsto, Decimal('4795.00'))
        
        # Margem: 4795 / 15000 * 100 = 31.97%
        self.assertEqual(self.budget.margem_prevista_percentual, Decimal('31.97'))
    
    def test_semaforo_verde(self):
        """Teste semáforo verde (uso < 80%)"""
        self.budget.atualizar_semaforo()
        self.assertEqual(self.budget.semaforo, 'VERDE')
        self.assertFalse(self.budget.bloqueado)
    
    def test_pode_lancar_despesa(self):
        """Teste verificação se pode lançar despesa"""
        self.assertTrue(self.budget.pode_lancar_despesa())


class ProjectExpenseTestCase(TestCase):
    """Testes para Despesas de Projeto"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.budget = ProjectBudget.objects.create(
            empresa=self.empresa,
            descricao='Budget de Teste',
            custo_total_previsto=Decimal('10000.00'),
            valor_venda=Decimal('15000.00'),
            criado_por=self.user
        )
        
        # Criar pessoa (funcionário)
        self.funcionario = Pessoa.objects.create(
            empresa=self.empresa,
            tipo='F',
            nome='João Silva',
            cpf_cnpj='123.456.789-00',
            funcionario=True
        )
    
    def test_criar_despesa(self):
        """Teste criação de despesa"""
        despesa = ProjectExpense.objects.create(
            empresa=self.empresa,
            budget=self.budget,
            tipo_despesa='MATERIAL',
            descricao='Compra de alumínio',
            valor=Decimal('1000.00'),
            criado_por=self.user
        )
        
        self.assertEqual(despesa.status, 'PENDENTE')
        self.assertEqual(despesa.valor, Decimal('1000.00'))
    
    def test_aprovar_despesa(self):
        """Teste aprovação de despesa"""
        despesa = ProjectExpense.objects.create(
            empresa=self.empresa,
            budget=self.budget,
            tipo_despesa='MATERIAL',
            descricao='Compra de vidro',
            valor=Decimal('500.00'),
            criado_por=self.user
        )
        
        despesa.aprovar(self.user)
        
        self.assertEqual(despesa.status, 'APROVADO')
        self.assertIsNotNone(despesa.data_aprovacao)
        self.assertEqual(despesa.aprovado_por, self.user)
    
    def test_rejeitar_despesa(self):
        """Teste rejeição de despesa"""
        despesa = ProjectExpense.objects.create(
            empresa=self.empresa,
            budget=self.budget,
            tipo_despesa='OUTROS',
            descricao='Despesa irregular',
            valor=Decimal('200.00'),
            criado_por=self.user
        )
        
        despesa.rejeitar(self.user, 'Falta comprovação')
        
        self.assertEqual(despesa.status, 'REJEITADO')
        self.assertEqual(despesa.justificativa_rejeicao, 'Falta comprovação')


class ValidadorBudgetTestCase(TestCase):
    """Testes para Validador de Budget"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.budget = ProjectBudget.objects.create(
            empresa=self.empresa,
            descricao='Budget Teste Validação',
            custo_total_previsto=Decimal('10000.00'),
            valor_venda=Decimal('15000.00'),
            status='EM_EXECUCAO',
            criado_por=self.user
        )
    
    def test_validar_despesa_permitida(self):
        """Teste validação de despesa permitida"""
        pode, msg = ValidadorBudget.validar_lancamento_despesa(
            self.budget,
            Decimal('1000.00')
        )
        
        self.assertTrue(pode)
    
    def test_validar_despesa_zona_amarela(self):
        """Teste validação entrando em zona amarela"""
        # Lançar despesas até atingir 80%
        pode, msg = ValidadorBudget.validar_lancamento_despesa(
            self.budget,
            Decimal('8500.00')  # 85% do previsto
        )
        
        self.assertTrue(pode)
        self.assertIn('amarela', msg.lower())
    
    def test_validar_budget_bloqueado(self):
        """Teste validação de budget bloqueado"""
        self.budget.bloqueado = True
        self.budget.save()
        
        pode, msg = ValidadorBudget.validar_lancamento_despesa(
            self.budget,
            Decimal('100.00')
        )
        
        self.assertFalse(pode)
        self.assertIn('bloqueado', msg.lower())
    
    def test_validar_budget_minimo(self):
        """Teste validação de valores mínimos"""
        valido, erros = ValidadorBudget.validar_budget_minimo(self.budget)
        
        self.assertTrue(valido)
        self.assertEqual(len(erros), 0)
    
    def test_validar_budget_prejuizo(self):
        """Teste detecção de operação com prejuízo"""
        budget_prejuizo = ProjectBudget.objects.create(
            empresa=self.empresa,
            descricao='Budget com Prejuízo',
            custo_total_previsto=Decimal('20000.00'),
            valor_venda=Decimal('15000.00'),  # Menor que o custo
            criado_por=self.user
        )
        
        valido, erros = ValidadorBudget.validar_budget_minimo(budget_prejuizo)
        
        self.assertFalse(valido)
        self.assertTrue(any('menor que o custo' in erro for erro in erros))


class JustificativaBudgetTestCase(TestCase):
    """Testes para Justificativa de Budget"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste LTDA',
            nome_fantasia='Teste',
            cnpj='12.345.678/0001-90',
            slug='teste'
        )
        
        self.budget = ProjectBudget.objects.create(
            empresa=self.empresa,
            descricao='Budget Teste',
            custo_total_previsto=Decimal('10000.00'),
            valor_venda=Decimal('15000.00'),
            bloqueado=True,
            criado_por=self.user
        )
    
    def test_criar_justificativa(self):
        """Teste criação de justificativa"""
        justificativa = JustificativaBudget.objects.create(
            budget=self.budget,
            motivo='IMPREVISTO',
            descricao='Necessário material extra por erro de medição',
            valor_adicional_necessario=Decimal('2000.00'),
            solicitado_por=self.user
        )
        
        self.assertEqual(justificativa.status, 'PENDENTE')
    
    def test_aprovar_justificativa_desbloqueia_budget(self):
        """Teste que aprovação desbloqueia budget"""
        justificativa = JustificativaBudget.objects.create(
            budget=self.budget,
            motivo='VARIACAO_PRECO',
            descricao='Aumento de preço dos insumos',
            valor_adicional_necessario=Decimal('1500.00'),
            solicitado_por=self.user
        )
        
        self.assertTrue(self.budget.bloqueado)
        
        justificativa.aprovar(self.user, 'Aprovado após análise')
        
        # Recarregar budget do banco
        self.budget.refresh_from_db()
        
        self.assertFalse(self.budget.bloqueado)
        self.assertEqual(justificativa.status, 'APROVADO')


# ============================================================================
# EXECUTAR TESTES
# ============================================================================

if __name__ == '__main__':
    import django
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['financeiro.tests_budget'])
