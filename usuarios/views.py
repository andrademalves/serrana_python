from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User, Group
from django.db.models import Q
from .models import PerfilUsuario, PermissaoMenu, Modulo, Menu, Empresa, UsuarioEmpresa
from .decorators import verificar_permissao_menu, verificar_permissao_acao

# Create your views here.


@login_required
def modulos(request):
    """Landing page com os módulos disponíveis conforme permissões."""
    user = request.user

    def build_modulo_entry(modulo, menus):
        menus_list = list(menus)
        if not menus_list:
            return None
        primary_url = menus_list[0].url
        primary_label = "Acessar"
        nome_normalizado = modulo.nome.lower().strip()

        if nome_normalizado == 'sistema':
            alvo = next((m for m in menus_list if m.url == '/usuarios/' or m.nome.lower().startswith('usu')), menus_list[0])
            primary_url = alvo.url
            primary_label = "Gestão de Acessos"
        
        # Determinar se é um nome de URL (ex: 'projetos:dashboard') ou URL direta (ex: '/usuarios/')
        is_url_name = not primary_url.startswith('/')
        
        return {
            'modulo': modulo,
            'menus': menus_list,
            'primary_url': primary_url,
            'primary_label': primary_label,
            'is_url_name': is_url_name,
        }

    # Superusuário enxerga todos os módulos com menus ativos
    if user.is_superuser:
        modulos_qs = Modulo.objects.filter(ativo=True).prefetch_related('menus')
        modulos_permitidos = []
        for modulo in modulos_qs:
            menus_modulo = modulo.menus.filter(ativo=True, menu_pai__isnull=True).order_by('ordem', 'nome')
            entry = build_modulo_entry(modulo, menus_modulo)
            if entry:
                modulos_permitidos.append(entry)
        context = {
            'modulos': modulos_permitidos,
            'hide_sidebar': True,
        }
        return render(request, 'usuarios/modulos.html', context)

    # Permissões por usuário e grupos
    permissoes_usuario = PermissaoMenu.objects.filter(
        usuario=user,
        pode_visualizar=True,
        menu__ativo=True
    ).select_related('menu', 'menu__modulo')

    grupos_usuario = user.groups.all()
    permissoes_grupo = PermissaoMenu.objects.filter(
        grupo__in=grupos_usuario,
        pode_visualizar=True,
        menu__ativo=True
    ).select_related('menu', 'menu__modulo')

    menu_ids = {p.menu.id for p in permissoes_usuario} | {p.menu.id for p in permissoes_grupo}

    menus_permitidos = Menu.objects.filter(
        id__in=menu_ids,
        ativo=True,
        menu_pai__isnull=True
    ).select_related('modulo').order_by('modulo__ordem', 'ordem', 'nome')

    modulos_dict = {}
    for menu in menus_permitidos:
        modulo = menu.modulo
        if not modulo.ativo:
            continue
        if modulo.id not in modulos_dict:
            modulos_dict[modulo.id] = {
                'modulo': modulo,
                'menus': [],
            }
        modulos_dict[modulo.id]['menus'].append(menu)

    modulos_list = []
    for data in modulos_dict.values():
        entry = build_modulo_entry(data['modulo'], data['menus'])
        if entry:
            modulos_list.append(entry)

    context = {
        'modulos': modulos_list,
        'hide_sidebar': True,
    }
    return render(request, 'usuarios/modulos.html', context)


def logout_custom(request):
    """Logout via GET e redireciona para a tela de login."""
    logout(request)
    return redirect('/accounts/login/')

@login_required
def dashboard(request):
    """
    Dashboard principal - exibe informações gerais
    """
    context = {
        'total_usuarios': User.objects.filter(is_active=True).count(),
        'total_modulos': Modulo.objects.filter(ativo=True).count(),
        'total_menus': Menu.objects.filter(ativo=True).count(),
    }
    return render(request, 'usuarios/dashboard.html', context)


@login_required
@verificar_permissao_menu('/usuarios/')
def listar_usuarios(request):
    """
    Lista usuários vinculados à empresa ativa
    """
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'username').strip() or 'username'

    # Whitelist de ordenação para evitar SQL injection
    allowed_sorts = {
        'username': 'username',
        '-username': '-username',
        'nome': 'first_name',
        '-nome': '-first_name',
        'sobrenome': 'last_name',
        '-sobrenome': '-last_name',
        'email': 'email',
        '-email': '-email',
        'cargo': 'perfil__cargo',
        '-cargo': '-perfil__cargo',
        'departamento': 'perfil__departamento',
        '-departamento': '-perfil__departamento',
        'status': 'is_active',
        '-status': '-is_active',
    }
    order_field = allowed_sorts.get(sort, 'username')

    # Filtrar apenas usuários da empresa ativa
    empresa_ativa_id = request.session.get('empresa_ativa_id')
    
    if empresa_ativa_id:
        # Filtrar usuários vinculados à empresa ativa (incluindo superuser)
        usuarios = User.objects.filter(
            usuario_empresas__empresa_id=empresa_ativa_id,
            usuario_empresas__ativo=True
        ).select_related('perfil').distinct()
    else:
        # Sem empresa ativa, não mostra nenhum usuário
        usuarios = User.objects.none()

    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(perfil__cargo__icontains=q)
            | Q(perfil__departamento__icontains=q)
        )

    usuarios = usuarios.order_by(order_field)
    context = {
        'usuarios': usuarios,
        'hide_sidebar': True,
        'q': q,
        'sort': sort,
    }
    return render(request, 'usuarios/listar_usuarios.html', context)


@login_required
@verificar_permissao_acao('/usuarios/', 'criar')
def criar_usuario(request):
    """
    Cria um novo usuário
    """
    if request.method == 'POST':
        # Processa o formulário
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        try:
            # Cria o usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Cria o perfil
            PerfilUsuario.objects.create(
                usuario=user,
                telefone=request.POST.get('telefone', ''),
                celular=request.POST.get('celular', ''),
                cargo=request.POST.get('cargo', ''),
                departamento=request.POST.get('departamento', '')
            )
            
            # Vincular automaticamente à empresa ativa do admin que está criando
            empresa_ativa_id = request.session.get('empresa_ativa_id')
            if empresa_ativa_id:
                try:
                    empresa = Empresa.objects.get(pk=empresa_ativa_id)
                    UsuarioEmpresa.objects.create(
                        usuario=user,
                        empresa=empresa,
                        papel='Usuário',
                        ativo=True,
                        criado_por=request.user
                    )
                except Empresa.DoesNotExist:
                    pass  # Se empresa não existir, continua sem vincular
            
            messages.success(request, f'Usuário {username} criado com sucesso!')
            return redirect('usuarios:listar_usuarios')
        except Exception as e:
            messages.error(request, f'Erro ao criar usuário: {str(e)}')
    
    context = {
        'grupos': Group.objects.all()
    }
    context['hide_sidebar'] = True
    return render(request, 'usuarios/criar_usuario.html', context)


@login_required
@verificar_permissao_acao('/usuarios/', 'editar')
def editar_usuario(request, user_id):
    """
    Edita um usuário existente
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.is_active = request.POST.get('is_active') == 'on'
            user.save()
            
            # Atualiza o perfil
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=user)
            perfil.telefone = request.POST.get('telefone', '')
            perfil.celular = request.POST.get('celular', '')
            perfil.cargo = request.POST.get('cargo', '')
            perfil.departamento = request.POST.get('departamento', '')
            perfil.save()
            
            messages.success(request, f'Usuário {user.username} atualizado com sucesso!')
            return redirect('usuarios:listar_usuarios')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar usuário: {str(e)}')
    
    context = {
        'usuario': user,
        'grupos': Group.objects.all(),
        'hide_sidebar': True,
    }
    return render(request, 'usuarios/editar_usuario.html', context)


@login_required
@verificar_permissao_acao('/usuarios/', 'editar')
def alternar_status_usuario(request, user_id):
    """Ativa ou inativa um usuário e retorna à lista."""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "ativado" if user.is_active else "inativado"
    messages.success(request, f"Usuário {user.username} {status} com sucesso.")
    return redirect('usuarios:listar_usuarios')




@login_required
@verificar_permissao_acao('/usuarios/', 'editar')
def alterar_senha_usuario(request, user_id):
    """Altera a senha de um usuário."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        if not nova_senha or not confirmar_senha:
            messages.error(request, 'Preencha todos os campos.')
        elif nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
        elif len(nova_senha) < 6:
            messages.error(request, 'A senha deve ter no mínimo 6 caracteres.')
        else:
            user.set_password(nova_senha)
            user.save()
            messages.success(request, f'Senha do usuário {user.username} alterada com sucesso!')
            return redirect('usuarios:listar_usuarios')
    
    context = {
        'usuario': user,
        'hide_sidebar': True,
    }
    return render(request, 'usuarios/alterar_senha.html', context)

@login_required
@verificar_permissao_acao('/usuarios/', 'editar')
def alterar_senha_usuario(request, user_id):
    """Altera a senha de um usuário."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        if not nova_senha or not confirmar_senha:
            messages.error(request, 'Preencha todos os campos.')
        elif nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
        elif len(nova_senha) < 6:
            messages.error(request, 'A senha deve ter no mínimo 6 caracteres.')
        else:
            user.set_password(nova_senha)
            user.save()
            messages.success(request, f'Senha do usuário {user.username} alterada com sucesso!')
            return redirect('usuarios:listar_usuarios')
    
    context = {
        'usuario': user,
        'hide_sidebar': True,
    }
    return render(request, 'usuarios/alterar_senha.html', context)


@login_required
@verificar_permissao_menu('/permissoes/')
def gerenciar_permissoes(request, user_id):
    """
    Gerencia as permissões de um usuário
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Remove permissões antigas do usuário
        PermissaoMenu.objects.filter(usuario=user).delete()
        
        # Cria novas permissões baseadas no formulário
        menus_selecionados = request.POST.getlist('menus')
        for menu_id in menus_selecionados:
            menu = Menu.objects.get(id=menu_id)
            PermissaoMenu.objects.create(
                tipo='usuario',
                usuario=user,
                menu=menu,
                pode_visualizar=True,
                pode_criar=f'criar_{menu_id}' in request.POST,
                pode_editar=f'editar_{menu_id}' in request.POST,
                pode_excluir=f'excluir_{menu_id}' in request.POST
            )
        
        messages.success(request, f'Permissões de {user.username} atualizadas com sucesso!')
        return redirect('usuarios:listar_usuarios')
    
    # Busca permissões atuais do usuário
    permissoes_atuais = PermissaoMenu.objects.filter(usuario=user).select_related('menu')
    menus_com_permissao = {p.menu.id: p for p in permissoes_atuais}
    
    # Busca todos os módulos e menus
    modulos = Modulo.objects.filter(ativo=True).prefetch_related('menus')
    
    context = {
        'usuario': user,
        'modulos': modulos,
        'menus_com_permissao': menus_com_permissao,
        'hide_sidebar': True,
    }
    return render(request, 'usuarios/gerenciar_permissoes.html', context)


# ============================================================================
# VIEWS DE GESTÃO DE EMPRESAS
# ============================================================================

@login_required
def listar_empresas(request):
    """Lista todas as empresas do sistema."""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar empresas.')
        return redirect('usuarios:home_modulos')
    
    busca = request.GET.get('busca', '')
    
    empresas = Empresa.objects.all().order_by('-empresa_matriz', 'nome_fantasia')
    
    if busca:
        empresas = empresas.filter(
            Q(nome_fantasia__icontains=busca) |
            Q(razao_social__icontains=busca) |
            Q(cnpj__icontains=busca)
        )
    
    context = {
        'empresas': empresas,
        'busca': busca,
    }
    return render(request, 'usuarios/listar_empresas.html', context)


@login_required
def criar_empresa(request):
    """Cria uma nova empresa no sistema."""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem criar empresas.')
        return redirect('usuarios:home_modulos')
    
    if request.method == 'POST':
        try:
            # Dados básicos
            razao_social = request.POST.get('razao_social')
            nome_fantasia = request.POST.get('nome_fantasia')
            cnpj = request.POST.get('cnpj')
            
            # Validações básicas
            if not razao_social or not nome_fantasia or not cnpj:
                messages.error(request, 'Razão Social, Nome Fantasia e CNPJ são obrigatórios.')
                return render(request, 'usuarios/criar_empresa.html', {'form_data': request.POST})
            
            # Verificar se CNPJ já existe
            if Empresa.objects.filter(cnpj=cnpj).exists():
                messages.error(request, f'Já existe uma empresa cadastrada com o CNPJ {cnpj}.')
                return render(request, 'usuarios/criar_empresa.html', {'form_data': request.POST})
            
            # Criar empresa
            empresa = Empresa.objects.create(
                razao_social=razao_social,
                nome_fantasia=nome_fantasia,
                cnpj=cnpj,
                inscricao_estadual=request.POST.get('inscricao_estadual', ''),
                inscricao_municipal=request.POST.get('inscricao_municipal', ''),
                cep=request.POST.get('cep', ''),
                logradouro=request.POST.get('logradouro', ''),
                numero=request.POST.get('numero', ''),
                complemento=request.POST.get('complemento', ''),
                bairro=request.POST.get('bairro', ''),
                cidade=request.POST.get('cidade', ''),
                uf=request.POST.get('uf', ''),
                telefone=request.POST.get('telefone', ''),
                email=request.POST.get('email', ''),
                website=request.POST.get('website', ''),
                cor_primaria=request.POST.get('cor_primaria', '#0066cc'),
                cor_secundaria=request.POST.get('cor_secundaria', '#333333'),
                ativa=request.POST.get('ativa') == 'on',
                empresa_matriz=request.POST.get('empresa_matriz') == 'on',
                criado_por=request.user,
                atualizado_por=request.user,
            )
            
            # Upload de logo se fornecido
            if 'logo' in request.FILES:
                empresa.logo = request.FILES['logo']
                empresa.save()
            
            messages.success(request, f'Empresa "{empresa.nome_fantasia}" cadastrada com sucesso!')
            return redirect('usuarios:listar_empresas')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar empresa: {str(e)}')
            return render(request, 'usuarios/criar_empresa.html', {'form_data': request.POST})
    
    return render(request, 'usuarios/criar_empresa.html')


@login_required
def editar_empresa(request, empresa_id):
    """Edita uma empresa existente."""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem editar empresas.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    if request.method == 'POST':
        try:
            # Atualizar dados básicos
            empresa.razao_social = request.POST.get('razao_social')
            empresa.nome_fantasia = request.POST.get('nome_fantasia')
            
            # Verificar CNPJ único
            novo_cnpj = request.POST.get('cnpj')
            if novo_cnpj != empresa.cnpj:
                if Empresa.objects.filter(cnpj=novo_cnpj).exists():
                    messages.error(request, f'Já existe uma empresa cadastrada com o CNPJ {novo_cnpj}.')
                    return render(request, 'usuarios/editar_empresa.html', {'empresa': empresa})
                empresa.cnpj = novo_cnpj
            
            # Atualizar demais campos
            empresa.inscricao_estadual = request.POST.get('inscricao_estadual', '')
            empresa.inscricao_municipal = request.POST.get('inscricao_municipal', '')
            empresa.cep = request.POST.get('cep', '')
            empresa.logradouro = request.POST.get('logradouro', '')
            empresa.numero = request.POST.get('numero', '')
            empresa.complemento = request.POST.get('complemento', '')
            empresa.bairro = request.POST.get('bairro', '')
            empresa.cidade = request.POST.get('cidade', '')
            empresa.uf = request.POST.get('uf', '')
            empresa.telefone = request.POST.get('telefone', '')
            empresa.email = request.POST.get('email', '')
            empresa.website = request.POST.get('website', '')
            empresa.cor_primaria = request.POST.get('cor_primaria', '#0066cc')
            empresa.cor_secundaria = request.POST.get('cor_secundaria', '#333333')
            empresa.ativa = request.POST.get('ativa') == 'on'
            empresa.empresa_matriz = request.POST.get('empresa_matriz') == 'on'
            
            # Regime Tributário
            regime_id = request.POST.get('regime_tributario')
            if regime_id:
                from financeiro.models import RegimeTributario
                empresa.regime_tributario = RegimeTributario.objects.get(id=regime_id)
            else:
                empresa.regime_tributario = None
            
            # Configurações SMTP
            empresa.smtp_ativo = request.POST.get('smtp_ativo') == 'on'
            empresa.smtp_host = request.POST.get('smtp_host', '')
            smtp_port = request.POST.get('smtp_port', '')
            empresa.smtp_port = int(smtp_port) if smtp_port else 587
            
            # TLS e SSL são mutuamente exclusivos
            smtp_use_tls = request.POST.get('smtp_use_tls') == 'on'
            smtp_use_ssl = request.POST.get('smtp_use_ssl') == 'on'
            
            # Se ambos estão marcados, priorizar TLS
            if smtp_use_tls and smtp_use_ssl:
                empresa.smtp_use_tls = True
                empresa.smtp_use_ssl = False
            else:
                empresa.smtp_use_tls = smtp_use_tls
                empresa.smtp_use_ssl = smtp_use_ssl
            
            empresa.smtp_username = request.POST.get('smtp_username', '')
            empresa.smtp_password = request.POST.get('smtp_password', '')
            empresa.smtp_from_email = request.POST.get('smtp_from_email', '')
            empresa.smtp_from_name = request.POST.get('smtp_from_name', '')
            
            empresa.atualizado_por = request.user
            
            # Upload de logo se fornecido
            if 'logo' in request.FILES:
                empresa.logo = request.FILES['logo']
            
            empresa.save()
            
            messages.success(request, f'Empresa "{empresa.nome_fantasia}" atualizada com sucesso!')
            return redirect('usuarios:listar_empresas')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar empresa: {str(e)}')
    
    # Buscar usuários que ainda não estão vinculados a esta empresa
    usuarios_vinculados_ids = UsuarioEmpresa.objects.filter(empresa=empresa).values_list('usuario_id', flat=True)
    usuarios_disponiveis = User.objects.exclude(id__in=usuarios_vinculados_ids).filter(is_active=True).order_by('username')
    
    # Buscar regimes tributários disponíveis
    from financeiro.models import RegimeTributario
    regimes = RegimeTributario.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'empresa': empresa,
        'usuarios_vinculados': UsuarioEmpresa.objects.filter(empresa=empresa).select_related('usuario'),
        'usuarios_disponiveis': usuarios_disponiveis,
        'regimes_tributarios': regimes,
    }
    return render(request, 'usuarios/editar_empresa.html', context)


@login_required
def vincular_usuario_empresa(request, empresa_id):
    """Vincula um usuário a uma empresa."""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        papel = request.POST.get('papel', '')
        
        try:
            usuario = User.objects.get(pk=usuario_id)
            
            # Verificar se já existe vínculo
            if UsuarioEmpresa.objects.filter(usuario=usuario, empresa=empresa).exists():
                messages.warning(request, f'Usuário {usuario.username} já está vinculado a esta empresa.')
            else:
                UsuarioEmpresa.objects.create(
                    usuario=usuario,
                    empresa=empresa,
                    papel=papel,
                    ativo=True,
                    criado_por=request.user
                )
                messages.success(request, f'Usuário {usuario.username} vinculado com sucesso!')
        except User.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
        except Exception as e:
            messages.error(request, f'Erro ao vincular usuário: {str(e)}')
    
    return redirect('usuarios:editar_empresa', empresa_id=empresa_id)


@login_required
def selecionar_empresa(request):
    """
    View para selecionar qual empresa o usuário deseja administrar.
    Lista todas as empresas que o usuário tem acesso.
    """
    user = request.user
    
    # Superuser tem acesso a todas as empresas ativas
    if user.is_superuser:
        empresas_disponiveis = Empresa.objects.filter(ativa=True).order_by('-empresa_matriz', 'nome_fantasia')
    else:
        # Buscar empresas vinculadas ao usuário
        empresas_disponiveis = Empresa.objects.filter(
            empresa_usuarios__usuario=user,
            empresa_usuarios__ativo=True,
            ativa=True
        ).distinct().order_by('-empresa_matriz', 'nome_fantasia')
    
    # Se tiver apenas uma empresa, selecionar automaticamente
    if empresas_disponiveis.count() == 1:
        empresa = empresas_disponiveis.first()
        request.session['empresa_ativa_id'] = empresa.id
        messages.success(request, f'Empresa "{empresa.nome_fantasia}" selecionada automaticamente.')
        return redirect('usuarios:home_modulos')
    
    # Se não tiver nenhuma empresa
    if empresas_disponiveis.count() == 0:
        messages.error(request, 'Você não tem acesso a nenhuma empresa. Entre em contato com o administrador do sistema.')
        # Redirecionar para logout ao invés de login para evitar loop
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    # Múltiplas empresas - mostrar seleção
    messages.info(request, f'Você tem acesso a {empresas_disponiveis.count()} empresas. Selecione uma para continuar.')
    
    context = {
        'empresas': empresas_disponiveis,
        'total_empresas': empresas_disponiveis.count(),
    }
    return render(request, 'usuarios/selecionar_empresa.html', context)


@login_required
def trocar_empresa(request, empresa_id):
    """
    View para trocar a empresa ativa na sessão do usuário.
    """
    user = request.user
    
    try:
        empresa = Empresa.objects.get(pk=empresa_id, ativa=True)
        
        # Verificar se usuário tem acesso
        tem_acesso = False
        if user.is_superuser:
            tem_acesso = True
        else:
            tem_acesso = UsuarioEmpresa.objects.filter(
                usuario=user,
                empresa=empresa,
                ativo=True
            ).exists()
        
        if not tem_acesso:
            messages.error(request, 'Você não tem acesso a esta empresa.')
            return redirect('usuarios:selecionar_empresa')
        
        # Salvar empresa na sessão
        request.session['empresa_ativa_id'] = empresa.id
        messages.success(request, f'Empresa alterada para "{empresa.nome_fantasia}".')
        
        # Redirecionar para home ou URL de origem
        next_url = request.GET.get('next', 'usuarios:home_modulos')
        return redirect(next_url)
        
    except Empresa.DoesNotExist:
        messages.error(request, 'Empresa não encontrada ou inativa.')
        return redirect('usuarios:selecionar_empresa')


@login_required
def testar_smtp(request, empresa_id):
    """Testa configurações SMTP da empresa"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:listar_empresas')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    if not empresa.tem_smtp_configurado():
        messages.warning(request, 'Configure o SMTP da empresa antes de testar.')
        return redirect('usuarios:editar_empresa', empresa_id=empresa.id)
    
    # Importar EmailService
    from financeiro.services.email_service import EmailService
    
    try:
        sucesso = EmailService.testar_configuracao(empresa)
        
        if sucesso:
            messages.success(
                request,
                f'✅ E-mail de teste enviado com sucesso para {empresa.smtp_from_email}! '
                f'Verifique sua caixa de entrada.'
            )
        else:
            messages.error(
                request,
                '❌ Falha ao enviar e-mail de teste. Verifique as configurações SMTP.'
            )
    except Exception as e:
        messages.error(
            request,
            f'❌ Erro ao testar SMTP: {str(e)}'
        )
    
    return redirect('usuarios:editar_empresa', empresa_id=empresa.id)


def logout_view(request):
    """View customizada para logout que aceita GET e POST"""
    auth_logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')


# ============================================================================
# VIEWS - CONFIGURAÇÃO DE IMPOSTOS DA EMPRESA
# ============================================================================

@login_required
def configurar_impostos_empresa(request, empresa_id):
    """Configura as alíquotas de impostos da empresa"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado. Apenas administradores podem configurar impostos.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    from financeiro.models import AliquotaImposto, RegimeTributario, HistoricoRegimeEmpresa
    from datetime import date
    
    # Buscar regime ativo no histórico
    historico_ativo = HistoricoRegimeEmpresa.objects.filter(
        empresa=empresa,
        ativo=True
    ).first()
    
    # Se não tem histórico mas tem regime na empresa, criar histórico
    if not historico_ativo and empresa.regime_tributario:
        historico_ativo = HistoricoRegimeEmpresa.objects.create(
            empresa=empresa,
            regime_tributario=empresa.regime_tributario,
            data_inicio=date.today(),
            ativo=True,
            criado_por=request.user,
            motivo_mudanca='Regime inicial'
        )
    
    regime_atual = historico_ativo.regime_tributario if historico_ativo else None
    
    if not regime_atual:
        messages.warning(request, 'Configure primeiro o Regime Tributário da empresa.')
        return redirect('usuarios:editar_empresa', empresa_id=empresa.id)
    
    # Buscar todos os regimes disponíveis
    regimes = RegimeTributario.objects.filter(ativo=True).order_by('nome')
    
    # Buscar alíquotas ativas do regime atual
    aliquotas = AliquotaImposto.objects.filter(
        empresa=empresa,
        regime_tributario=regime_atual,
        ativo=True,
        data_fim_vigencia__isnull=True
    ).order_by('tipo_imposto')
    
    # Buscar histórico de regimes
    historico = HistoricoRegimeEmpresa.objects.filter(
        empresa=empresa
    ).select_related('regime_tributario', 'criado_por').order_by('-data_inicio')
    
    context = {
        'empresa': empresa,
        'regime_atual': regime_atual,
        'regimes_disponiveis': regimes,
        'aliquotas': aliquotas,
        'historico_regimes': historico,
    }
    
    return render(request, 'usuarios/configurar_impostos_empresa.html', context)


@login_required
def criar_aliquota_empresa(request, empresa_id):
    """Cria uma nova alíquota de imposto para a empresa"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    from financeiro.models import AliquotaImposto, HistoricoRegimeEmpresa
    from financeiro.forms import AliquotaImpostoForm
    from datetime import date
    
    # Buscar regime ativo
    historico_ativo = HistoricoRegimeEmpresa.objects.filter(
        empresa=empresa,
        ativo=True
    ).first()
    
    if not historico_ativo:
        messages.error(request, 'Configure primeiro o Regime Tributário da empresa.')
        return redirect('usuarios:editar_empresa', empresa_id=empresa.id)
    
    regime_atual = historico_ativo.regime_tributario
    
    if request.method == 'POST':
        form = AliquotaImpostoForm(request.POST, empresa=empresa)
        if form.is_valid():
            aliquota = form.save(commit=False)
            aliquota.empresa = empresa
            aliquota.regime_tributario = regime_atual
            aliquota.data_inicio_vigencia = historico_ativo.data_inicio
            aliquota.criado_por = request.user
            aliquota.save()
            messages.success(request, f'Alíquota de {aliquota.get_tipo_imposto_display()} cadastrada com sucesso!')
            return redirect('usuarios:configurar_impostos_empresa', empresa_id=empresa.id)
    else:
        form = AliquotaImpostoForm(empresa=empresa, initial={'regime_tributario': regime_atual})
    
    context = {
        'empresa': empresa,
        'regime_atual': regime_atual,
        'form': form,
        'titulo': 'Nova Alíquota de Imposto',
    }
    
    return render(request, 'usuarios/form_aliquota_empresa.html', context)


@login_required
def editar_aliquota_empresa(request, empresa_id, aliquota_id):
    """Edita uma alíquota de imposto da empresa"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    from financeiro.models import AliquotaImposto
    from financeiro.forms import AliquotaImpostoForm
    
    aliquota = get_object_or_404(AliquotaImposto, pk=aliquota_id, empresa=empresa)
    
    if request.method == 'POST':
        form = AliquotaImpostoForm(request.POST, instance=aliquota, empresa=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Alíquota de {aliquota.get_tipo_imposto_display()} atualizada com sucesso!')
            return redirect('usuarios:configurar_impostos_empresa', empresa_id=empresa.id)
    else:
        form = AliquotaImpostoForm(instance=aliquota, empresa=empresa)
    
    context = {
        'empresa': empresa,
        'form': form,
        'titulo': 'Editar Alíquota de Imposto',
        'aliquota': aliquota,
    }
    
    return render(request, 'usuarios/form_aliquota_empresa.html', context)


@login_required
def excluir_aliquota_empresa(request, empresa_id, aliquota_id):
    """Exclui uma alíquota de imposto da empresa"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    from financeiro.models import AliquotaImposto
    
    aliquota = get_object_or_404(AliquotaImposto, pk=aliquota_id, empresa=empresa)
    
    if request.method == 'POST':
        tipo_imposto = aliquota.get_tipo_imposto_display()
        aliquota.delete()
        messages.success(request, f'Alíquota de {tipo_imposto} excluída com sucesso!')
        return redirect('usuarios:configurar_impostos_empresa', empresa_id=empresa.id)
    
    context = {
        'empresa': empresa,
        'aliquota': aliquota,
    }
    
    return render(request, 'usuarios/confirmar_exclusao_aliquota.html', context)


@login_required
def mudar_regime_empresa(request, empresa_id):
    """Muda o regime tributário da empresa (arquivando o anterior)"""
    if not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:home_modulos')
    
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    from financeiro.models import RegimeTributario, HistoricoRegimeEmpresa, AliquotaImposto
    from datetime import date
    
    if request.method == 'POST':
        novo_regime_id = request.POST.get('novo_regime')
        data_mudanca = request.POST.get('data_mudanca')
        motivo = request.POST.get('motivo', '')
        
        if not novo_regime_id:
            messages.error(request, 'Selecione um regime tributário.')
            return redirect('usuarios:mudar_regime_empresa', empresa_id=empresa.id)
        
        try:
            novo_regime = RegimeTributario.objects.get(id=novo_regime_id)
            data_mudanca_obj = date.fromisoformat(data_mudanca) if data_mudanca else date.today()
            
            # Desativar regime atual
            historico_atual = HistoricoRegimeEmpresa.objects.filter(
                empresa=empresa,
                ativo=True
            ).first()
            
            if historico_atual:
                historico_atual.ativo = False
                historico_atual.data_fim = data_mudanca_obj
                historico_atual.save()
                
                # Encerrar vigência das alíquotas do regime antigo
                AliquotaImposto.objects.filter(
                    empresa=empresa,
                    regime_tributario=historico_atual.regime_tributario,
                    ativo=True,
                    data_fim_vigencia__isnull=True
                ).update(
                    data_fim_vigencia=data_mudanca_obj,
                    ativo=False
                )
            
            # Criar novo histórico
            HistoricoRegimeEmpresa.objects.create(
                empresa=empresa,
                regime_tributario=novo_regime,
                data_inicio=data_mudanca_obj,
                ativo=True,
                motivo_mudanca=motivo,
                criado_por=request.user
            )
            
            # Atualizar regime na empresa
            empresa.regime_tributario = novo_regime
            empresa.save()
            
            messages.success(
                request,
                f'Regime alterado para "{novo_regime.get_nome_display()}" com sucesso! '
                f'Agora configure as alíquotas do novo regime.'
            )
            return redirect('usuarios:configurar_impostos_empresa', empresa_id=empresa.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao mudar regime: {str(e)}')
    
    # GET - Mostrar formulário
    regimes = RegimeTributario.objects.filter(ativo=True).order_by('nome')
    
    historico_atual = HistoricoRegimeEmpresa.objects.filter(
        empresa=empresa,
        ativo=True
    ).first()
    
    context = {
        'empresa': empresa,
        'regime_atual': historico_atual.regime_tributario if historico_atual else None,
        'regimes_disponiveis': regimes,
    }
    
    return render(request, 'usuarios/mudar_regime_empresa.html', context)


# ============================================================================
# VIEWS DE BACKUP DE BANCO DE DADOS
# ============================================================================

from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import BackupBancoDados
from .services import BackupService
import logging

logger = logging.getLogger(__name__)


@login_required
def listar_backups(request):
    """
    Lista todos os backups de banco de dados gerados
    Apenas administradores ou usuários com permissão específica
    """
    # Verificar permissão
    if not (request.user.is_superuser or request.user.has_perm('usuarios.gerar_backup')):
        messages.error(request, 'Você não tem permissão para acessar backups do banco de dados.')
        return redirect('usuarios:home_modulos')
    
    # Filtrar backups
    backups = BackupBancoDados.objects.select_related('empresa', 'usuario').all()
    
    # Se não for superuser, mostrar apenas backups da empresa ativa
    if not request.user.is_superuser:
        empresa_ativa_id = request.session.get('empresa_ativa_id')
        if empresa_ativa_id:
            backups = backups.filter(empresa_id=empresa_ativa_id)
        else:
            backups = backups.none()
    
    # Estatísticas
    total_backups = backups.count()
    backups_concluidos = backups.filter(status='concluido').count()
    backups_erro = backups.filter(status='erro').count()
    
    # Tamanho total
    tamanho_total = sum(b.tamanho_bytes for b in backups.filter(status='concluido'))
    
    def formatar_tamanho(bytes_value):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    context = {
        'backups': backups[:50],  # Últimos 50 backups
        'total_backups': total_backups,
        'backups_concluidos': backups_concluidos,
        'backups_erro': backups_erro,
        'tamanho_total': formatar_tamanho(tamanho_total),
    }
    
    return render(request, 'usuarios/listar_backups.html', context)


@login_required
@transaction.atomic
def gerar_backup(request):
    """
    Gera um novo backup do banco de dados
    POST apenas, retorna JSON para requisições AJAX
    """
    # Verificar permissão
    if not (request.user.is_superuser or request.user.has_perm('usuarios.gerar_backup')):
        messages.error(request, 'Você não tem permissão para gerar backups.')
        return redirect('usuarios:listar_backups')
    
    if request.method != 'POST':
        return redirect('usuarios:listar_backups')
    
    try:
        # Obter empresa ativa
        empresa_ativa_id = request.session.get('empresa_ativa_id')
        
        if not empresa_ativa_id:
            messages.error(request, 'Nenhuma empresa ativa. Selecione uma empresa primeiro.')
            return redirect('usuarios:listar_backups')
        
        empresa = get_object_or_404(Empresa, id=empresa_ativa_id)
        
        # Inicializar serviço e gerar backup
        backup_service = BackupService()
        backup = backup_service.gerar_backup(empresa, request.user)
        
        messages.success(
            request, 
            f'Backup gerado com sucesso! Arquivo: {backup.nome_arquivo} ({backup.tamanho_formatado})'
        )
        
        logger.info(f"Backup gerado por {request.user.username}: {backup.nome_arquivo}")
        
    except Exception as e:
        messages.error(request, f'Erro ao gerar backup: {str(e)}')
        logger.error(f"Erro ao gerar backup (usuário: {request.user.username}): {str(e)}")
    
    return redirect('usuarios:listar_backups')


@login_required
def download_backup(request, backup_id):
    """
    Faz download de um arquivo de backup
    Valida permissões e existência do arquivo antes de servir
    """
    # Verificar permissão
    if not (request.user.is_superuser or request.user.has_perm('usuarios.download_backup')):
        raise PermissionDenied('Você não tem permissão para fazer download de backups.')
    
    # Buscar backup
    backup = get_object_or_404(BackupBancoDados, id=backup_id)
    
    # Se não for superuser, verificar se o backup é da empresa ativa
    if not request.user.is_superuser:
        empresa_ativa_id = request.session.get('empresa_ativa_id')
        if backup.empresa_id != empresa_ativa_id:
            raise PermissionDenied('Você não tem permissão para baixar este backup.')
    
    # Verificar se o backup foi concluído
    if backup.status != 'concluido':
        messages.error(request, 'Este backup não está disponível para download.')
        return redirect('usuarios:listar_backups')
    
    # Verificar se o arquivo existe
    import os
    if not os.path.exists(backup.caminho_arquivo):
        messages.error(request, 'Arquivo de backup não encontrado no servidor.')
        logger.error(f"Arquivo de backup não encontrado: {backup.caminho_arquivo}")
        return redirect('usuarios:listar_backups')
    
    try:
        # Servir arquivo usando FileResponse (streaming para arquivos grandes)
        response = FileResponse(
            open(backup.caminho_arquivo, 'rb'),
            as_attachment=True,
            filename=backup.nome_arquivo
        )
        
        # Adicionar headers
        response['Content-Type'] = 'application/sql'
        response['Content-Length'] = backup.tamanho_bytes
        
        logger.info(f"Download de backup por {request.user.username}: {backup.nome_arquivo}")
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erro ao fazer download do backup: {str(e)}')
        logger.error(f"Erro ao fazer download de backup {backup.nome_arquivo}: {str(e)}")
        return redirect('usuarios:listar_backups')


@login_required
@transaction.atomic
def excluir_backup(request, backup_id):
    """
    Exclui um backup (arquivo e registro)
    Apenas superusuários podem excluir backups
    """
    # Verificar permissão - apenas superuser
    if not request.user.is_superuser:
        messages.error(request, 'Apenas administradores podem excluir backups.')
        return redirect('usuarios:listar_backups')
    
    if request.method != 'POST':
        return redirect('usuarios:listar_backups')
    
    backup = get_object_or_404(BackupBancoDados, id=backup_id)
    
    try:
        import os
        
        # Remover arquivo do disco se existir
        if os.path.exists(backup.caminho_arquivo):
            os.remove(backup.caminho_arquivo)
            logger.info(f"Arquivo de backup removido: {backup.caminho_arquivo}")
        
        nome_arquivo = backup.nome_arquivo
        
        # Remover registro do banco
        backup.delete()
        
        messages.success(request, f'Backup {nome_arquivo} excluído com sucesso.')
        logger.info(f"Backup excluído por {request.user.username}: {nome_arquivo}")
        
    except Exception as e:
        messages.error(request, f'Erro ao excluir backup: {str(e)}')
        logger.error(f"Erro ao excluir backup {backup.nome_arquivo}: {str(e)}")
    
    return redirect('usuarios:listar_backups')

@login_required
@permission_required('usuarios.gerar_backup', raise_exception=True)
def configurar_backup_automatico(request):
    """
    View para configurar backups automáticos agendados
    Apenas superusuários podem acessar
    """
    if not request.user.is_superuser:
        messages.error(request, 'Apenas administradores podem configurar backups automáticos.')
        return redirect('usuarios:listar_backups')
    
    from .forms import BackupConfigForm
    from .models import BackupConfig
    
    config = BackupConfig.get_config()
    
    if request.method == 'POST':
        form = BackupConfigForm(request.POST, instance=config)
        
        if form.is_valid():
            config = form.save(commit=False)
            config.atualizado_por = request.user
            config.save()
            
            messages.success(request, 'Configuração de backup automático salva com sucesso!')
            logger.info(f"Configuração de backup atualizada por {request.user.username}")
            
            return redirect('usuarios:configurar_backup_automatico')
    else:
        form = BackupConfigForm(instance=config)
    
    # Estatísticas
    from .models import BackupBancoDados
    
    total_agendados = BackupBancoDados.objects.filter(tipo_backup='agendado').count()
    total_manuais = BackupBancoDados.objects.filter(tipo_backup='manual').count()
    total_protegidos = BackupBancoDados.objects.filter(protegido=True).count()
    
    # Calcular próxima execução estimada
    proxima_execucao = None
    if config.habilitado:
        from datetime import datetime, timedelta
        agora = datetime.now()
        hora_exec = config.hora_execucao
        
        proxima = agora.replace(
            hour=hora_exec.hour,
            minute=hora_exec.minute,
            second=0,
            microsecond=0
        )
        
        # Se já passou da hora hoje, próxima execução é amanhã
        if proxima <= agora:
            if config.frequencia == 'diaria':
                proxima += timedelta(days=1)
            elif config.frequencia == 'semanal':
                dias_ate_proximo = (int(config.dia_semana) - agora.weekday()) % 7
                if dias_ate_proximo == 0:
                    dias_ate_proximo = 7  # Próxima semana
                proxima += timedelta(days=dias_ate_proximo)
            elif config.frequencia == 'mensal':
                # Próximo dia do mês
                if agora.day >= config.dia_mes:
                    # Próximo mês
                    if agora.month == 12:
                        proxima = proxima.replace(year=agora.year + 1, month=1, day=config.dia_mes)
                    else:
                        proxima = proxima.replace(month=agora.month + 1, day=config.dia_mes)
                else:
                    proxima = proxima.replace(day=config.dia_mes)
        
        proxima_execucao = proxima
    
    context = {
        'form': form,
        'config': config,
        'total_agendados': total_agendados,
        'total_manuais': total_manuais,
        'total_protegidos': total_protegidos,
        'proxima_execucao': proxima_execucao,
    }
    
    return render(request, 'usuarios/configurar_backup_automatico.html', context)


@login_required
@permission_required('usuarios.gerar_backup', raise_exception=True)
def proteger_backup(request, backup_id):
    """
    Marca/desmarca um backup como protegido
    Backups protegidos não são excluídos pela política de retenção
    """
    from .models import BackupBancoDados
    
    backup = get_object_or_404(BackupBancoDados, id=backup_id)
    
    # Alternar proteção
    backup.protegido = not backup.protegido
    backup.save()
    
    status = "protegido" if backup.protegido else "desprotegido"
    messages.success(request, f'Backup {status} com sucesso!')
    logger.info(f"Backup {backup.nome_arquivo} {status} por {request.user.username}")
    
    return redirect('usuarios:listar_backups')