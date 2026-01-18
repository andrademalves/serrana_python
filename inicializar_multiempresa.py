"""
Script de Inicialização Multiempresa
Cria empresa padrão e configura sistema para multiempresa

Execute:
    python manage.py shell < inicializar_multiempresa.py
    
Ou:
    python manage.py runscript inicializar_multiempresa (se django-extensions instalado)
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models_empresa import Empresa, UsuarioEmpresa
from usuarios.models import PerfilUsuario


def criar_empresa_padrao():
    """Cria empresa padrão do sistema"""
    print("=" * 60)
    print("INICIALIZAÇÃO MULTIEMPRESA - SISTEMA SERRANA")
    print("=" * 60)
    print()
    
    # Verificar se já existe empresa
    if Empresa.objects.exists():
        print("⚠️  JÁ EXISTEM EMPRESAS CADASTRADAS:")
        for emp in Empresa.objects.all():
            print(f"   - {emp.nome_fantasia} ({emp.cnpj})")
        print()
        
        resposta = input("Deseja criar uma nova empresa mesmo assim? (s/N): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada.")
            return
    
    # Coletar dados da empresa
    print("\n📋 DADOS DA EMPRESA PADRÃO")
    print("-" * 60)
    
    razao_social = input("Razão Social: ").strip() or "Serrana Ltda"
    nome_fantasia = input("Nome Fantasia: ").strip() or "Serrana"
    cnpj = input("CNPJ (##.###.###/####-##): ").strip() or "00.000.000/0001-00"
    
    # Validar CNPJ único
    if Empresa.objects.filter(cnpj=cnpj).exists():
        print(f"\n❌ ERRO: CNPJ {cnpj} já cadastrado!")
        return
    
    # Buscar usuário admin
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        print("\n⚠️  Nenhum superuser encontrado.")
        criar_admin = input("Deseja criar um superuser agora? (S/n): ")
        
        if criar_admin.lower() != 'n':
            print("\n📝 CRIAR SUPERUSER")
            print("-" * 60)
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = input("Senha: ").strip()
            
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ Superuser '{username}' criado com sucesso!")
        else:
            admin_user = None
    
    # Criar empresa
    print("\n🏢 CRIANDO EMPRESA...")
    
    empresa = Empresa.objects.create(
        razao_social=razao_social,
        nome_fantasia=nome_fantasia,
        cnpj=cnpj,
        ativa=True,
        empresa_matriz=True,
        responsavel=admin_user,
        criado_por=admin_user
    )
    
    print(f"✅ Empresa '{empresa.nome_fantasia}' criada com sucesso!")
    print(f"   ID: {empresa.id}")
    print(f"   Slug: {empresa.slug}")
    print()
    
    # Vincular admin à empresa
    if admin_user:
        print("👤 VINCULANDO SUPERUSER À EMPRESA...")
        
        vinculo = UsuarioEmpresa.objects.create(
            usuario=admin_user,
            empresa=empresa,
            papel='Administrador',
            ativo=True,
            criado_por=admin_user
        )
        
        print(f"✅ {admin_user.username} vinculado à {empresa.nome_fantasia}")
        print()
        
        # Criar/Atualizar PerfilUsuario
        perfil, criado = PerfilUsuario.objects.get_or_create(usuario=admin_user)
        if not perfil.empresa_padrao:
            perfil.empresa_padrao = empresa
            perfil.save()
            print(f"✅ Empresa padrão definida para {admin_user.username}")
    
    # Resumo
    print("\n" + "=" * 60)
    print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("📊 RESUMO:")
    print(f"   - Empresa: {empresa.nome_fantasia}")
    print(f"   - CNPJ: {empresa.cnpj}")
    print(f"   - Slug: {empresa.slug}")
    print(f"   - Status: {'Ativa' if empresa.ativa else 'Inativa'}")
    if admin_user:
        print(f"   - Administrador: {admin_user.username}")
    print()
    
    print("🔄 PRÓXIMOS PASSOS:")
    print("   1. Execute as migrations para adicionar campo 'empresa' aos models")
    print("   2. Popule empresa_id para dados existentes")
    print("   3. Configure middleware em settings.py")
    print("   4. Teste isolamento de dados")
    print()
    
    return empresa


def popular_empresa_em_registros_existentes(empresa):
    """
    Popula campo empresa em registros existentes
    ATENÇÃO: Execute apenas uma vez!
    """
    print("\n🔄 POPULAR EMPRESA EM REGISTROS EXISTENTES")
    print("=" * 60)
    print()
    
    resposta = input(f"⚠️  Esta operação irá setar empresa_id={empresa.id} em TODOS os registros existentes.\n"
                    f"   Empresa: {empresa.nome_fantasia}\n\n"
                    f"   Tem certeza? (s/N): ")
    
    if resposta.lower() != 's':
        print("❌ Operação cancelada.")
        return
    
    # Importar models (adaptar conforme seus apps)
    apps_to_update = []
    
    # Cadastros
    try:
        from cadastros.models import Pessoa, Produto
        apps_to_update.append(('Pessoa', Pessoa))
        apps_to_update.append(('Produto', Produto))
    except ImportError:
        pass
    
    # Estoque
    try:
        from estoque.models import Item, LocalEstoque, MovimentoEstoque
        apps_to_update.append(('Item', Item))
        apps_to_update.append(('LocalEstoque', LocalEstoque))
        apps_to_update.append(('MovimentoEstoque', MovimentoEstoque))
    except ImportError:
        pass
    
    # Projetos
    try:
        from projetos.models import Orcamento, Projeto
        apps_to_update.append(('Orcamento', Orcamento))
        apps_to_update.append(('Projeto', Projeto))
    except ImportError:
        pass
    
    # Financeiro
    try:
        from financeiro.models import TituloFinanceiro, ContaFinanceira
        apps_to_update.append(('TituloFinanceiro', TituloFinanceiro))
        apps_to_update.append(('ContaFinanceira', ContaFinanceira))
    except ImportError:
        pass
    
    # Executar updates
    total_atualizados = 0
    
    for nome, Model in apps_to_update:
        try:
            # Contar registros sem empresa
            sem_empresa = Model.objects.filter(empresa__isnull=True).count()
            
            if sem_empresa > 0:
                print(f"   {nome}: {sem_empresa} registros sem empresa")
                
                # Atualizar
                Model.objects.filter(empresa__isnull=True).update(empresa=empresa)
                
                print(f"   ✅ {nome}: {sem_empresa} registros atualizados")
                total_atualizados += sem_empresa
            else:
                print(f"   ⏭️  {nome}: Nenhum registro para atualizar")
        
        except Exception as e:
            print(f"   ❌ {nome}: Erro - {e}")
    
    print()
    print(f"✅ Total de {total_atualizados} registros atualizados!")
    print()


def vincular_usuarios_a_empresa(empresa):
    """Vincula todos os usuários existentes à empresa padrão"""
    print("\n👥 VINCULAR USUÁRIOS À EMPRESA")
    print("=" * 60)
    print()
    
    usuarios = User.objects.exclude(usuario_empresas__empresa=empresa)
    
    if not usuarios.exists():
        print("ℹ️  Todos os usuários já estão vinculados.")
        return
    
    print(f"📊 {usuarios.count()} usuários sem vínculo encontrados:")
    for user in usuarios:
        print(f"   - {user.username} ({user.email})")
    print()
    
    resposta = input(f"Deseja vincular todos a '{empresa.nome_fantasia}'? (s/N): ")
    
    if resposta.lower() != 's':
        print("❌ Operação cancelada.")
        return
    
    vinculados = 0
    for user in usuarios:
        UsuarioEmpresa.objects.get_or_create(
            usuario=user,
            empresa=empresa,
            defaults={
                'ativo': True,
                'papel': 'Usuário'
            }
        )
        vinculados += 1
        print(f"   ✅ {user.username} vinculado")
    
    print()
    print(f"✅ {vinculados} usuários vinculados com sucesso!")
    print()


def menu_principal():
    """Menu interativo de inicialização"""
    while True:
        print("\n" + "=" * 60)
        print("INICIALIZAÇÃO MULTIEMPRESA - MENU PRINCIPAL")
        print("=" * 60)
        print()
        print("1. Criar Empresa Padrão")
        print("2. Popular Empresa em Registros Existentes")
        print("3. Vincular Usuários à Empresa")
        print("4. Executar Tudo (1 + 2 + 3)")
        print("0. Sair")
        print()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '0':
            print("\n👋 Até logo!")
            break
        
        elif opcao == '1':
            empresa = criar_empresa_padrao()
        
        elif opcao == '2':
            empresas = list(Empresa.objects.all())
            if not empresas:
                print("\n❌ Nenhuma empresa cadastrada. Execute opção 1 primeiro.")
                continue
            
            if len(empresas) == 1:
                empresa = empresas[0]
            else:
                print("\n📋 EMPRESAS DISPONÍVEIS:")
                for i, emp in enumerate(empresas, 1):
                    print(f"   {i}. {emp.nome_fantasia} ({emp.cnpj})")
                
                escolha = int(input("\nEscolha a empresa: ").strip()) - 1
                empresa = empresas[escolha]
            
            popular_empresa_em_registros_existentes(empresa)
        
        elif opcao == '3':
            empresas = list(Empresa.objects.all())
            if not empresas:
                print("\n❌ Nenhuma empresa cadastrada. Execute opção 1 primeiro.")
                continue
            
            if len(empresas) == 1:
                empresa = empresas[0]
            else:
                print("\n📋 EMPRESAS DISPONÍVEIS:")
                for i, emp in enumerate(empresas, 1):
                    print(f"   {i}. {emp.nome_fantasia} ({emp.cnpj})")
                
                escolha = int(input("\nEscolha a empresa: ").strip()) - 1
                empresa = empresas[escolha]
            
            vincular_usuarios_a_empresa(empresa)
        
        elif opcao == '4':
            empresa = criar_empresa_padrao()
            if empresa:
                popular_empresa_em_registros_existentes(empresa)
                vincular_usuarios_a_empresa(empresa)
        
        else:
            print("\n❌ Opção inválida!")


if __name__ == '__main__':
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
