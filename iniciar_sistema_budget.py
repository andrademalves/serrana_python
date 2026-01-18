#!/usr/bin/env python
"""
============================================================================
SCRIPT DE INICIALIZAÇÃO DO SISTEMA DE BUDGET
Serrana Gestão 360 - Controle de Lucratividade
============================================================================

Este script executa todas as etapas necessárias para iniciar o sistema:
1. Verifica dependências
2. Executa migrations
3. Inicializa regimes tributários e alíquotas
4. Cria views SQL de BI
5. Valida configurações
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.conf import settings
from usuarios.models import Empresa
from financeiro.models import RegimeTributario, AliquotaImposto
import subprocess


def print_header(texto):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {texto}")
    print("=" * 80 + "\n")


def print_success(texto):
    """Imprime mensagem de sucesso"""
    print(f"✅ {texto}")


def print_error(texto):
    """Imprime mensagem de erro"""
    print(f"❌ {texto}")


def print_info(texto):
    """Imprime mensagem de informação"""
    print(f"ℹ️  {texto}")


def step_1_verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print_header("ETAPA 1: Verificando Dependências")
    
    dependencias_ok = True
    
    # Django
    try:
        import django
        print_success(f"Django {django.get_version()} instalado")
    except ImportError:
        print_error("Django não instalado")
        dependencias_ok = False
    
    # MySQL Client
    try:
        import MySQLdb
        print_success("MySQL Client instalado")
    except ImportError:
        print_error("MySQL Client (mysqlclient) não instalado")
        dependencias_ok = False
    
    # Celery
    try:
        import celery
        print_success(f"Celery instalado")
    except ImportError:
        print_info("Celery não instalado (opcional para tarefas agendadas)")
    
    # Redis (para Celery)
    try:
        import redis
        print_success("Redis instalado")
    except ImportError:
        print_info("Redis não instalado (opcional para Celery)")
    
    if not dependencias_ok:
        print_error("Instale as dependências faltantes: pip install -r requirements.txt")
        return False
    
    return True


def step_2_executar_migrations():
    """Executa as migrations do Django"""
    print_header("ETAPA 2: Executando Migrations")
    
    try:
        # Criar migrations
        print_info("Criando migrations para financeiro...")
        call_command('makemigrations', 'financeiro', interactive=False)
        
        print_info("Criando migrations para usuarios...")
        call_command('makemigrations', 'usuarios', interactive=False)
        
        # Executar migrations
        print_info("Aplicando migrations...")
        call_command('migrate', interactive=False)
        
        print_success("Migrations executadas com sucesso!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao executar migrations: {e}")
        return False


def step_3_inicializar_impostos():
    """Inicializa regimes tributários e alíquotas"""
    print_header("ETAPA 3: Inicializando Regimes Tributários e Alíquotas")
    
    try:
        # Verificar se já existem regimes
        if RegimeTributario.objects.exists():
            print_info("Regimes tributários já existem. Pulando...")
            return True
        
        print_info("Criando regimes tributários...")
        
        # Simples Nacional
        simples = RegimeTributario.objects.create(
            nome="Simples Nacional",
            codigo="SIMPLES",
            descricao="Regime tributário simplificado para micro e pequenas empresas"
        )
        print_success(f"Criado: {simples.nome}")
        
        # Lucro Presumido
        presumido = RegimeTributario.objects.create(
            nome="Lucro Presumido",
            codigo="PRESUMIDO",
            descricao="Regime para empresas com faturamento até R$ 78 milhões"
        )
        print_success(f"Criado: {presumido.nome}")
        
        # Lucro Real
        real = RegimeTributario.objects.create(
            nome="Lucro Real",
            codigo="REAL",
            descricao="Regime obrigatório para grandes empresas"
        )
        print_success(f"Criado: {real.nome}")
        
        # MEI
        mei = RegimeTributario.objects.create(
            nome="MEI",
            codigo="MEI",
            descricao="Microempreendedor Individual"
        )
        print_success(f"Criado: {mei.nome}")
        
        # Criar alíquotas padrão para cada regime
        print_info("\nCriando alíquotas padrão...")
        
        empresas = Empresa.objects.all()
        if not empresas.exists():
            print_info("Nenhuma empresa cadastrada. Alíquotas serão criadas ao cadastrar empresas.")
        else:
            for empresa in empresas:
                # Definir regime padrão se não tiver
                if not empresa.regime_tributario:
                    empresa.regime_tributario = simples
                    empresa.save()
                    print_info(f"Empresa {empresa.nome_fantasia}: regime definido como Simples Nacional")
                
                # Criar alíquotas padrão
                AliquotaImposto.objects.get_or_create(
                    empresa=empresa,
                    regime=empresa.regime_tributario,
                    defaults={
                        'pis': 0.65,
                        'cofins': 3.00,
                        'irpj': 0.00,
                        'csll': 0.00,
                        'iss': 2.00,
                        'icms': 0.00,
                        'outros': 0.00
                    }
                )
                print_success(f"Alíquotas criadas para: {empresa.nome_fantasia}")
        
        print_success("\nRegimes tributários e alíquotas inicializados!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao inicializar impostos: {e}")
        import traceback
        traceback.print_exc()
        return False


def step_4_executar_sql_bi():
    """Executa as queries SQL de Business Intelligence"""
    print_header("ETAPA 4: Criando Views SQL de Business Intelligence")
    
    sql_file = BASE_DIR / 'financeiro' / 'queries_bi.sql'
    
    if not sql_file.exists():
        print_error(f"Arquivo SQL não encontrado: {sql_file}")
        return False
    
    try:
        print_info("Lendo arquivo SQL...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Separar por comandos (views e índices)
        comandos = []
        comando_atual = []
        
        for linha in sql_content.split('\n'):
            # Ignorar comentários
            if linha.strip().startswith('--') or linha.strip() == '':
                continue
            
            comando_atual.append(linha)
            
            # Final de comando (ponto e vírgula)
            if linha.strip().endswith(';'):
                comandos.append('\n'.join(comando_atual))
                comando_atual = []
        
        print_info(f"Executando {len(comandos)} comandos SQL...")
        
        with connection.cursor() as cursor:
            for i, comando in enumerate(comandos, 1):
                if comando.strip():
                    try:
                        cursor.execute(comando)
                        # Extrair nome da view/índice para exibir
                        if 'CREATE' in comando.upper():
                            palavras = comando.split()
                            for j, p in enumerate(palavras):
                                if p.upper() in ['VIEW', 'INDEX']:
                                    nome = palavras[j+1] if j+1 < len(palavras) else 'desconhecido'
                                    print_success(f"[{i}/{len(comandos)}] Criado: {nome}")
                                    break
                    except Exception as e:
                        # Ignorar erro de "já existe"
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print_info(f"[{i}/{len(comandos)}] Já existe (ignorado)")
                        else:
                            print_error(f"Erro no comando {i}: {e}")
        
        print_success("\nViews SQL de BI criadas com sucesso!")
        return True
        
    except Exception as e:
        print_error(f"Erro ao executar SQL: {e}")
        import traceback
        traceback.print_exc()
        return False


def step_5_validar_configuracoes():
    """Valida as configurações do sistema"""
    print_header("ETAPA 5: Validando Configurações")
    
    tudo_ok = True
    
    # URLs
    print_info("Verificando configuração de URLs...")
    if hasattr(settings, 'ROOT_URLCONF'):
        print_success("ROOT_URLCONF configurado")
    else:
        print_error("ROOT_URLCONF não configurado")
        tudo_ok = False
    
    # INSTALLED_APPS
    print_info("Verificando INSTALLED_APPS...")
    if 'financeiro.apps.FinanceiroConfig' in settings.INSTALLED_APPS or 'financeiro' in settings.INSTALLED_APPS:
        print_success("App financeiro configurado")
    else:
        print_error("App financeiro não encontrado em INSTALLED_APPS")
        tudo_ok = False
    
    # Email
    print_info("Verificando configuração de Email...")
    if hasattr(settings, 'EMAIL_BACKEND'):
        print_success(f"Email backend: {settings.EMAIL_BACKEND}")
        if 'console' in settings.EMAIL_BACKEND:
            print_info("  ⚠️  Usando console backend (desenvolvimento). Configure SMTP para produção.")
    else:
        print_error("EMAIL_BACKEND não configurado")
        tudo_ok = False
    
    # Celery
    print_info("Verificando configuração de Celery...")
    if hasattr(settings, 'CELERY_BROKER_URL'):
        print_success(f"Celery broker: {settings.CELERY_BROKER_URL}")
    else:
        print_info("  ℹ️  Celery não configurado (opcional)")
    
    # Database
    print_info("Verificando conexão com banco de dados...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print_success(f"Conectado ao banco: {settings.DATABASES['default']['NAME']}")
    except Exception as e:
        print_error(f"Erro na conexão: {e}")
        tudo_ok = False
    
    # Gestores
    print_info("Verificando emails de gestores...")
    if hasattr(settings, 'GESTORES_EMAILS'):
        print_success(f"Gestores configurados: {len(settings.GESTORES_EMAILS)} email(s)")
        for email in settings.GESTORES_EMAILS:
            print(f"    - {email}")
    else:
        print_info("  ⚠️  GESTORES_EMAILS não configurado. Configure para receber notificações.")
    
    if tudo_ok:
        print_success("\n✅ Todas as configurações estão OK!")
    else:
        print_error("\n❌ Existem problemas nas configurações. Verifique acima.")
    
    return tudo_ok


def step_6_criar_superuser():
    """Pergunta se deseja criar superusuário"""
    print_header("ETAPA 6: Criação de Superusuário (Opcional)")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(is_superuser=True).exists():
            print_info("Já existe um superusuário cadastrado.")
            return True
        
        resposta = input("Deseja criar um superusuário agora? (s/n): ").lower()
        
        if resposta == 's':
            print_info("Criando superusuário...")
            call_command('createsuperuser', interactive=True)
            print_success("Superusuário criado!")
        else:
            print_info("Pulando criação de superusuário.")
        
        return True
        
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def main():
    """Função principal"""
    print_header("INICIALIZAÇÃO DO SISTEMA DE BUDGET - SERRANA GESTÃO 360")
    
    print("""
    Este script irá:
    1. Verificar dependências
    2. Executar migrations do Django
    3. Inicializar regimes tributários e alíquotas
    4. Criar views SQL de Business Intelligence
    5. Validar configurações do sistema
    6. (Opcional) Criar superusuário
    """)
    
    input("Pressione ENTER para continuar...")
    
    # Executar etapas
    etapas = [
        ("Verificar Dependências", step_1_verificar_dependencias),
        ("Executar Migrations", step_2_executar_migrations),
        ("Inicializar Impostos", step_3_inicializar_impostos),
        ("Criar Views SQL BI", step_4_executar_sql_bi),
        ("Validar Configurações", step_5_validar_configuracoes),
        ("Criar Superusuário", step_6_criar_superuser),
    ]
    
    resultados = []
    
    for nome, funcao in etapas:
        try:
            sucesso = funcao()
            resultados.append((nome, sucesso))
            
            if not sucesso and nome != "Criar Superusuário":
                print_error(f"\nFalha na etapa: {nome}")
                resposta = input("Deseja continuar mesmo assim? (s/n): ").lower()
                if resposta != 's':
                    print_info("Inicialização interrompida.")
                    sys.exit(1)
        
        except Exception as e:
            print_error(f"Erro na etapa {nome}: {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nome, False))
            
            resposta = input("Deseja continuar? (s/n): ").lower()
            if resposta != 's':
                sys.exit(1)
    
    # Resumo final
    print_header("RESUMO DA INICIALIZAÇÃO")
    
    for nome, sucesso in resultados:
        status = "✅ OK" if sucesso else "❌ FALHA"
        print(f"{status} - {nome}")
    
    total_sucesso = sum(1 for _, s in resultados if s)
    total = len(resultados)
    
    print(f"\nTotal: {total_sucesso}/{total} etapas concluídas com sucesso")
    
    if total_sucesso == total:
        print_header("🎉 SISTEMA INICIALIZADO COM SUCESSO! 🎉")
        print("""
        Próximos passos:
        
        1. Iniciar o servidor:
           python manage.py runserver
        
        2. Acessar o Django Admin:
           http://localhost:8000/admin/
        
        3. Testar o Dashboard de Budget:
           http://localhost:8000/financeiro/budget/dashboard/
        
        4. (Opcional) Iniciar Celery para tarefas agendadas:
           celery -A serrana worker --loglevel=info
           celery -A serrana beat --loglevel=info
        
        📚 Documentação completa:
           - RESUMO_EXECUTIVO_BUDGET.md
           - INSTRUCOES_INTEGRACAO_BUDGET.py
           - ETAPAS_2_3_COMPLETO.md
        """)
    else:
        print_header("⚠️  INICIALIZAÇÃO PARCIAL")
        print("\nAlgumas etapas falharam. Revise os erros acima e tente novamente.")
        print("\nPara executar apenas uma etapa específica, edite este script.")


if __name__ == '__main__':
    main()
