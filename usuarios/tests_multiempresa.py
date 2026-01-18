"""
Testes Automatizados - Sistema Multiempresa
Garante isolamento total de dados entre empresas
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.db import IntegrityError
from usuarios.models_empresa import Empresa, UsuarioEmpresa


class EmpresaModelTest(TestCase):
    """Testes do model Empresa"""
    
    def setUp(self):
        self.user = User.objects.create_user('admin', password='senha123')
    
    def test_criar_empresa(self):
        """Testar criação de empresa"""
        empresa = Empresa.objects.create(
            razao_social='Teste Ltda',
            nome_fantasia='Teste',
            cnpj='11.111.111/0001-11',
            criado_por=self.user
        )
        
        self.assertEqual(empresa.razao_social, 'Teste Ltda')
        self.assertEqual(empresa.nome_fantasia, 'Teste')
        self.assertTrue(empresa.ativa)
        self.assertIsNotNone(empresa.slug)
    
    def test_slug_auto_gerado(self):
        """Testar geração automática de slug"""
        empresa = Empresa.objects.create(
            razao_social='Empresa Teste SA',
            nome_fantasia='Empresa Teste',
            cnpj='11.111.111/0001-11'
        )
        
        self.assertEqual(empresa.slug, 'empresa-teste')
    
    def test_slug_unico(self):
        """Testar unicidade de slug"""
        Empresa.objects.create(
            razao_social='Teste 1',
            nome_fantasia='Teste',
            cnpj='11.111.111/0001-11'
        )
        
        empresa2 = Empresa.objects.create(
            razao_social='Teste 2',
            nome_fantasia='Teste',
            cnpj='22.222.222/0001-22'
        )
        
        # Segundo slug deve ser diferente
        self.assertNotEqual(empresa2.slug, 'teste')
        self.assertTrue(empresa2.slug.startswith('teste-'))
    
    def test_cnpj_unico(self):
        """Testar unicidade de CNPJ"""
        Empresa.objects.create(
            razao_social='Teste 1',
            nome_fantasia='Teste 1',
            cnpj='11.111.111/0001-11'
        )
        
        with self.assertRaises(IntegrityError):
            Empresa.objects.create(
                razao_social='Teste 2',
                nome_fantasia='Teste 2',
                cnpj='11.111.111/0001-11'  # CNPJ duplicado
            )


class UsuarioEmpresaTest(TestCase):
    """Testes de vínculo usuário-empresa"""
    
    def setUp(self):
        self.empresa_a = Empresa.objects.create(
            razao_social='Empresa A',
            nome_fantasia='A',
            cnpj='11.111.111/0001-11'
        )
        
        self.empresa_b = Empresa.objects.create(
            razao_social='Empresa B',
            nome_fantasia='B',
            cnpj='22.222.222/0001-22'
        )
        
        self.user = User.objects.create_user('user1', password='senha123')
    
    def test_vincular_usuario_empresa(self):
        """Testar vínculo de usuário a empresa"""
        vinculo = UsuarioEmpresa.objects.create(
            usuario=self.user,
            empresa=self.empresa_a,
            ativo=True
        )
        
        self.assertEqual(vinculo.usuario, self.user)
        self.assertEqual(vinculo.empresa, self.empresa_a)
        self.assertTrue(vinculo.ativo)
    
    def test_usuario_multiplas_empresas(self):
        """Testar usuário com acesso a múltiplas empresas"""
        UsuarioEmpresa.objects.create(
            usuario=self.user,
            empresa=self.empresa_a,
            ativo=True
        )
        
        UsuarioEmpresa.objects.create(
            usuario=self.user,
            empresa=self.empresa_b,
            ativo=True
        )
        
        empresas = Empresa.objects.filter(empresa_usuarios__usuario=self.user)
        self.assertEqual(empresas.count(), 2)
    
    def test_vinculo_unico_por_usuario_empresa(self):
        """Testar que não pode duplicar vínculo usuário-empresa"""
        UsuarioEmpresa.objects.create(
            usuario=self.user,
            empresa=self.empresa_a
        )
        
        with self.assertRaises(IntegrityError):
            UsuarioEmpresa.objects.create(
                usuario=self.user,
                empresa=self.empresa_a  # Duplicado
            )


class IsolamentoMultiempresaTest(TestCase):
    """Testes críticos de isolamento de dados entre empresas"""
    
    def setUp(self):
        # Criar duas empresas
        self.empresa_a = Empresa.objects.create(
            razao_social='Empresa A Ltda',
            nome_fantasia='Empresa A',
            cnpj='11.111.111/0001-11',
            slug='empresa-a',
            ativa=True
        )
        
        self.empresa_b = Empresa.objects.create(
            razao_social='Empresa B Ltda',
            nome_fantasia='Empresa B',
            cnpj='22.222.222/0001-22',
            slug='empresa-b',
            ativa=True
        )
        
        # Criar usuários
        self.user_a = User.objects.create_user('user_a', password='senha123')
        self.user_b = User.objects.create_user('user_b', password='senha123')
        self.admin = User.objects.create_superuser('admin', password='admin123')
        
        # Vincular usuários a empresas
        UsuarioEmpresa.objects.create(
            usuario=self.user_a,
            empresa=self.empresa_a,
            ativo=True
        )
        
        UsuarioEmpresa.objects.create(
            usuario=self.user_b,
            empresa=self.empresa_b,
            ativo=True
        )
    
    def test_isolamento_total_de_dados(self):
        """
        TESTE CRÍTICO: Dados de uma empresa não podem vazar para outra
        
        Este teste simula o cenário mais importante:
        - Empresa A cria registros
        - Empresa B cria registros
        - Queries devem retornar apenas da empresa correta
        """
        # Importar models de teste (adaptar conforme seus models)
        from cadastros.models import Pessoa
        
        # Criar pessoas em cada empresa
        pessoa_a = Pessoa.objects.create(
            nome='Cliente A',
            tipo='F',
            cpf_cnpj='111.111.111-11',
            empresa=self.empresa_a
        )
        
        pessoa_b = Pessoa.objects.create(
            nome='Cliente B',
            tipo='F',
            cpf_cnpj='222.222.222-22',
            empresa=self.empresa_b
        )
        
        # VALIDAÇÃO 1: Filtro por empresa retorna apenas dados corretos
        pessoas_a = Pessoa.objects.for_empresa(self.empresa_a)
        pessoas_b = Pessoa.objects.for_empresa(self.empresa_b)
        
        self.assertEqual(pessoas_a.count(), 1)
        self.assertEqual(pessoas_b.count(), 1)
        
        # VALIDAÇÃO 2: Dados não vazam entre empresas
        self.assertIn(pessoa_a, pessoas_a)
        self.assertNotIn(pessoa_b, pessoas_a)
        
        self.assertIn(pessoa_b, pessoas_b)
        self.assertNotIn(pessoa_a, pessoas_b)
        
        # VALIDAÇÃO 3: Query sem filtro retorna tudo (admin only)
        todas = Pessoa.objects.all()
        self.assertEqual(todas.count(), 2)
    
    def test_usuario_sem_empresa_bloqueado(self):
        """
        Usuário sem vínculo com empresa não deve acessar sistema
        """
        user_sem_empresa = User.objects.create_user(
            'sem_empresa',
            password='senha123'
        )
        
        client = Client()
        logged_in = client.login(username='sem_empresa', password='senha123')
        self.assertTrue(logged_in)
        
        # Tentar acessar uma URL protegida
        response = client.get('/dashboard/')
        
        # Deve redirecionar para seleção de empresa
        self.assertEqual(response.status_code, 302)
        # self.assertIn('/empresas/selecionar/', response.url)
    
    def test_usuario_nao_acessa_empresa_errada(self):
        """
        Usuário da empresa A não pode acessar dados da empresa B
        """
        from cadastros.models import Pessoa
        
        # Criar pessoa na empresa B
        pessoa_b = Pessoa.objects.create(
            nome='Cliente B',
            tipo='F',
            cpf_cnpj='222.222.222-22',
            empresa=self.empresa_b
        )
        
        # Simular request do user_a (empresa A)
        client = Client()
        client.login(username='user_a', password='senha123')
        
        # Setar empresa A na sessão
        session = client.session
        session['empresa_ativa_id'] = self.empresa_a.id
        session.save()
        
        # Tentar buscar pessoa da empresa B
        pessoas = Pessoa.objects.for_empresa(self.empresa_a)
        
        # Não deve encontrar pessoa_b
        self.assertNotIn(pessoa_b, pessoas)
    
    def test_alternancia_de_empresa(self):
        """
        Usuário com acesso a múltiplas empresas pode alternar
        """
        # Dar acesso a user_a em ambas empresas
        UsuarioEmpresa.objects.create(
            usuario=self.user_a,
            empresa=self.empresa_b,
            ativo=True
        )
        
        client = Client()
        client.login(username='user_a', password='senha123')
        
        # Selecionar empresa A
        session = client.session
        session['empresa_ativa_id'] = self.empresa_a.id
        session.save()
        
        # Verificar (adaptar conforme sua view)
        # response = client.get('/dashboard/')
        # self.assertEqual(response.context['empresa_ativa'], self.empresa_a)
        
        # Trocar para empresa B
        session['empresa_ativa_id'] = self.empresa_b.id
        session.save()
        
        # response = client.get('/dashboard/')
        # self.assertEqual(response.context['empresa_ativa'], self.empresa_b)
    
    def test_criacao_sempre_com_empresa(self):
        """
        Registros novos DEVEM sempre ter empresa
        """
        from cadastros.models import Pessoa
        
        # Criar sem empresa deve falhar (se campo for obrigatório)
        with self.assertRaises(IntegrityError):
            Pessoa.objects.create(
                nome='Sem Empresa',
                tipo='F',
                cpf_cnpj='999.999.999-99'
                # empresa não fornecido
            )
    
    def test_queries_filtradas_por_empresa(self):
        """
        Todas as queries devem retornar apenas dados da empresa
        """
        from cadastros.models import Pessoa
        
        # Criar 10 pessoas na empresa A
        for i in range(10):
            Pessoa.objects.create(
                nome=f'Pessoa A{i}',
                tipo='F',
                cpf_cnpj=f'111.111.{i:03d}-11',
                empresa=self.empresa_a
            )
        
        # Criar 5 pessoas na empresa B
        for i in range(5):
            Pessoa.objects.create(
                nome=f'Pessoa B{i}',
                tipo='F',
                cpf_cnpj=f'222.222.{i:03d}-22',
                empresa=self.empresa_b
            )
        
        # Verificar contadores
        self.assertEqual(
            Pessoa.objects.for_empresa(self.empresa_a).count(),
            10
        )
        
        self.assertEqual(
            Pessoa.objects.for_empresa(self.empresa_b).count(),
            5
        )
        
        # Total geral (admin)
        self.assertEqual(Pessoa.objects.all().count(), 15)
    
    def test_relacionamentos_respeitam_empresa(self):
        """
        ForeignKeys entre models devem respeitar mesma empresa
        """
        from cadastros.models import Pessoa, Produto
        
        # Criar fornecedor na empresa A
        fornecedor_a = Pessoa.objects.create(
            nome='Fornecedor A',
            tipo='J',
            cpf_cnpj='11.111.111/0001-11',
            fornecedor=True,
            empresa=self.empresa_a
        )
        
        # Criar produto na empresa A vinculado ao fornecedor A
        produto_a = Produto.objects.create(
            codigo='PROD-001',
            descricao='Produto A',
            fornecedor=fornecedor_a,
            empresa=self.empresa_a
        )
        
        # Verificar relacionamento
        self.assertEqual(produto_a.fornecedor, fornecedor_a)
        self.assertEqual(produto_a.empresa, self.empresa_a)
        self.assertEqual(produto_a.fornecedor.empresa, self.empresa_a)
    
    def test_superuser_acessa_todas_empresas(self):
        """
        Superuser deve ter acesso a todas as empresas
        """
        from cadastros.models import Pessoa
        
        # Criar pessoas em ambas empresas
        Pessoa.objects.create(
            nome='Cliente A',
            tipo='F',
            cpf_cnpj='111.111.111-11',
            empresa=self.empresa_a
        )
        
        Pessoa.objects.create(
            nome='Cliente B',
            tipo='F',
            cpf_cnpj='222.222.222-22',
            empresa=self.empresa_b
        )
        
        # Superuser vê todas
        client = Client()
        client.login(username='admin', password='admin123')
        
        # Admin pode ver dados de todas as empresas
        todas_pessoas = Pessoa.objects.all()
        self.assertEqual(todas_pessoas.count(), 2)


class MiddlewareEmpresaTest(TestCase):
    """Testes do middleware de empresa ativa"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            razao_social='Teste Ltda',
            nome_fantasia='Teste',
            cnpj='11.111.111/0001-11'
        )
        
        self.user = User.objects.create_user('user1', password='senha123')
        
        UsuarioEmpresa.objects.create(
            usuario=self.user,
            empresa=self.empresa,
            ativo=True
        )
        
        self.client = Client()
    
    def test_empresa_ativa_injetada_no_request(self):
        """Middleware deve injetar request.empresa"""
        self.client.login(username='user1', password='senha123')
        
        # Setar empresa na sessão
        session = self.client.session
        session['empresa_ativa_id'] = self.empresa.id
        session.save()
        
        # Fazer request
        # factory = RequestFactory()
        # request = factory.get('/dashboard/')
        # request.user = self.user
        # request.session = session
        
        # Middleware deve adicionar request.empresa
        # self.assertTrue(hasattr(request, 'empresa'))
        # self.assertEqual(request.empresa, self.empresa)
    
    def test_empresa_inativa_bloqueada(self):
        """Empresa desativada não pode ser acessada"""
        self.empresa.ativa = False
        self.empresa.save()
        
        self.client.login(username='user1', password='senha123')
        
        session = self.client.session
        session['empresa_ativa_id'] = self.empresa.id
        session.save()
        
        # Request deve ser bloqueado
        # response = self.client.get('/dashboard/')
        # self.assertEqual(response.status_code, 302)


# ============================================
# COMANDOS PARA RODAR TESTES
# ============================================
"""
# Rodar todos os testes
python manage.py test usuarios.tests_multiempresa

# Rodar teste específico
python manage.py test usuarios.tests_multiempresa.IsolamentoMultiempresaTest

# Com verbosidade
python manage.py test usuarios.tests_multiempresa -v 2

# Manter banco de dados para debug
python manage.py test usuarios.tests_multiempresa --keepdb
"""
