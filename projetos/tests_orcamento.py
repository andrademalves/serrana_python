"""
Testes automatizados para o módulo de Orçamentos
Cobertura: código automático, desconto, auditoria, segurança
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from cadastros.models import Pessoa
from .models import Orcamento, OrcamentoItem, OrcamentoParcela, OrcamentoHistorico
from estoque.models import Item


class CodigoAutomaticoTestCase(TestCase):
    """Testes para geração automática de código"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Pessoa.objects.create(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            cliente=True,
            ativo=True
        )
        self.vendedor = Pessoa.objects.create(
            nome='Vendedor Teste',
            cpf_cnpj='98765432100',
            vendedor=True,
            ativo=True
        )
    
    def test_gerar_codigo_automatico_primeiro(self):
        """Testa geração do primeiro código do ano"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        ano = timezone.now().year
        self.assertEqual(orcamento.codigo, f'ORC-{ano}-0001')
    
    def test_gerar_codigo_automatico_sequencial(self):
        """Testa geração sequencial de códigos"""
        # Criar primeiro orçamento
        orc1 = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        # Criar segundo orçamento
        orc2 = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        ano = timezone.now().year
        self.assertEqual(orc1.codigo, f'ORC-{ano}-0001')
        self.assertEqual(orc2.codigo, f'ORC-{ano}-0002')
    
    def test_codigo_unico(self):
        """Testa unicidade do código"""
        orc1 = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        # Tentar criar com mesmo código deve falhar
        with self.assertRaises(Exception):
            Orcamento.objects.create(
                codigo=orc1.codigo,
                cliente=self.cliente,
                vendedor=self.vendedor,
                data_orcamento=timezone.now().date(),
                criado_por=self.user
            )


class DescontoGlobalTestCase(TestCase):
    """Testes para sistema de desconto global"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Pessoa.objects.create(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            cliente=True,
            ativo=True
        )
        self.vendedor = Pessoa.objects.create(
            nome='Vendedor Teste',
            cpf_cnpj='98765432100',
            vendedor=True,
            ativo=True
        )
    
    def test_desconto_percentual(self):
        """Testa desconto percentual"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            tipo_desconto='PERCENTUAL',
            desconto_valor=Decimal('10.00'),  # 10%
            criado_por=self.user
        )
        
        self.assertEqual(orcamento.desconto, Decimal('100.00'))  # 10% de 1000
        self.assertEqual(orcamento.valor_final, Decimal('900.00'))
    
    def test_desconto_valor_fixo(self):
        """Testa desconto valor fixo"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            tipo_desconto='VALOR_FIXO',
            desconto_valor=Decimal('150.00'),
            criado_por=self.user
        )
        
        self.assertEqual(orcamento.desconto, Decimal('150.00'))
        self.assertEqual(orcamento.valor_final, Decimal('850.00'))
    
    def test_desconto_maior_que_total(self):
        """Testa que desconto não pode ser maior que total"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('500.00'),
            tipo_desconto='VALOR_FIXO',
            desconto_valor=Decimal('1000.00'),  # Maior que total
            criado_por=self.user
        )
        
        # Desconto deve ser limitado ao valor total
        self.assertEqual(orcamento.desconto, Decimal('500.00'))
        self.assertEqual(orcamento.valor_final, Decimal('0.00'))
    
    def test_desconto_percentual_maximo(self):
        """Testa limite de 100% no desconto percentual"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            tipo_desconto='PERCENTUAL',
            desconto_valor=Decimal('150.00'),  # 150% (inválido)
            criado_por=self.user
        )
        
        # Deve ser limitado a 100%
        self.assertEqual(orcamento.desconto, Decimal('1000.00'))
        self.assertEqual(orcamento.valor_final, Decimal('0.00'))
    
    def test_valor_final_nunca_negativo(self):
        """Testa que valor final nunca é negativo"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('100.00'),
            tipo_desconto='PERCENTUAL',
            desconto_valor=Decimal('100.00'),  # 100%
            criado_por=self.user
        )
        
        self.assertEqual(orcamento.valor_final, Decimal('0.00'))
        self.assertGreaterEqual(orcamento.valor_final, Decimal('0.00'))


class AuditoriaTestCase(TestCase):
    """Testes para auditoria de alterações"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Pessoa.objects.create(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            cliente=True,
            ativo=True
        )
        self.vendedor = Pessoa.objects.create(
            nome='Vendedor Teste',
            cpf_cnpj='98765432100',
            vendedor=True,
            ativo=True
        )
    
    def test_auditoria_criacao(self):
        """Testa registro de auditoria na criação"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            criado_por=self.user
        )
        
        # Deve ter 1 registro de histórico
        historico = OrcamentoHistorico.objects.filter(orcamento=orcamento)
        self.assertEqual(historico.count(), 1)
        self.assertEqual(historico.first().acao, 'CRIADO')
    
    def test_auditoria_alteracao(self):
        """Testa registro de alteração"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            criado_por=self.user,
            atualizado_por=self.user
        )
        
        # Alterar desconto
        orcamento.tipo_desconto = 'PERCENTUAL'
        orcamento.desconto_valor = Decimal('10.00')
        orcamento.save()
        
        # Deve ter 2 registros (criação + alteração)
        historico = OrcamentoHistorico.objects.filter(orcamento=orcamento).order_by('timestamp')
        self.assertEqual(historico.count(), 2)
        self.assertEqual(historico.last().acao, 'ALTERADO')
    
    def test_diff_alteracao(self):
        """Testa que o diff registra apenas o que mudou"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            valor_total=Decimal('1000.00'),
            criado_por=self.user,
            atualizado_por=self.user
        )
        
        # Alterar status
        orcamento.status = 'APROVADO'
        orcamento.save()
        
        # Verificar diff
        ultimo_historico = OrcamentoHistorico.objects.filter(orcamento=orcamento).last()
        self.assertIn('status', ultimo_historico.diff)
        self.assertEqual(ultimo_historico.diff['status']['antes'], 'PENDENTE')
        self.assertEqual(ultimo_historico.diff['status']['depois'], 'APROVADO')
    
    def test_auditoria_usuario_deletado(self):
        """Testa que auditoria persiste mesmo com usuário deletado"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        # Deletar usuário
        user_id = self.user.id
        self.user.delete()
        
        # Histórico deve existir
        historico = OrcamentoHistorico.objects.filter(orcamento=orcamento)
        self.assertEqual(historico.count(), 1)
        self.assertIsNone(historico.first().usuario)  # SET_NULL


class IntegracaoTestCase(TestCase):
    """Testes de integração com itens e parcelas"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Pessoa.objects.create(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            cliente=True,
            ativo=True
        )
        self.vendedor = Pessoa.objects.create(
            nome='Vendedor Teste',
            cpf_cnpj='98765432100',
            vendedor=True,
            ativo=True
        )
    
    def test_total_consistente_com_itens(self):
        """Testa que total do orçamento corresponde aos itens"""
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            vendedor=self.vendedor,
            data_orcamento=timezone.now().date(),
            criado_por=self.user
        )
        
        # Adicionar itens
        OrcamentoItem.objects.create(
            orcamento=orcamento,
            tipo='SERVICO',
            descricao='Serviço 1',
            quantidade=Decimal('2'),
            valor_unitario=Decimal('100.00')
        )
        OrcamentoItem.objects.create(
            orcamento=orcamento,
            tipo='SERVICO',
            descricao='Serviço 2',
            quantidade=Decimal('1'),
            valor_unitario=Decimal('300.00')
        )
        
        # Atualizar orçamento
        orcamento.valor_total = sum(item.valor_total for item in orcamento.itens.all())
        orcamento.save()
        
        self.assertEqual(orcamento.valor_total, Decimal('500.00'))


class SegurancaTestCase(TestCase):
    """Testes de segurança e permissões"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Pessoa.objects.create(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            cliente=True,
            ativo=True
        )
        self.vendedor = Pessoa.objects.create(
            nome='Vendedor Teste',
            cpf_cnpj='98765432100',
            vendedor=True,
            ativo=True
        )
    
    def test_usuario_nao_autenticado(self):
        """Testa que usuário não autenticado não acessa"""
        response = self.client.get('/projetos/orcamentos/criar/')
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
    
    def test_usuario_autenticado(self):
        """Testa que usuário autenticado acessa"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/projetos/orcamentos/criar/')
        self.assertEqual(response.status_code, 200)
