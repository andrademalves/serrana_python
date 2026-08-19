from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from .models import Pessoa, Produto, Cidade, Estado
from financeiro.models import Banco
from usuarios.decorators import verificar_permissao_menu, verificar_permissao_acao, require_empresa
from .utils import processar_foto_3x4

# Create your views here.

# ==================== DASHBOARD ====================

@login_required
@require_empresa
def dashboard_cadastros(request):
    """
    Dashboard do módulo de cadastros
    """
    context = {
        'total_pessoas': Pessoa.objects.filter(empresa=request.empresa, ativo=True).count(),
        'total_clientes': Pessoa.objects.filter(empresa=request.empresa, cliente=True, ativo=True).count(),
        'total_fornecedores': Pessoa.objects.filter(empresa=request.empresa, fornecedor=True, ativo=True).count(),
        'total_produtos': Produto.objects.filter(empresa=request.empresa, ativo=True).count(),
        'produtos_estoque_baixo': Produto.objects.filter(
            empresa=request.empresa,
            ativo=True,
            estoque_atual__lte=models.F('estoque_minimo')
        ).count(),
    }
    return render(request, 'cadastros/dashboard.html', context)


# ==================== VIEWS DE PESSOAS ====================

@login_required
@require_empresa
@verificar_permissao_menu('/cadastros/pessoas/')
def listar_pessoas(request):
    """
    Lista todas as pessoas cadastradas da empresa ativa
    """
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')
    classificacao = request.GET.get('classificacao', '')
    
    pessoas = Pessoa.objects.filter(empresa=request.empresa)
    
    if q:
        pessoas = pessoas.filter(
            Q(nome__icontains=q) |
            Q(nome_fantasia__icontains=q) |
            Q(cpf_cnpj__icontains=q) |
            Q(email__icontains=q)
        )
    
    if tipo:
        pessoas = pessoas.filter(tipo=tipo)
    
    if classificacao == 'cliente':
        pessoas = pessoas.filter(cliente=True)
    elif classificacao == 'fornecedor':
        pessoas = pessoas.filter(fornecedor=True)
    elif classificacao == 'funcionario':
        pessoas = pessoas.filter(funcionario=True)
    
    pessoas = pessoas.order_by('nome')
    
    context = {
        'pessoas': pessoas,
        'q': q,
        'tipo': tipo,
        'classificacao': classificacao,
    }
    return render(request, 'cadastros/listar_pessoas.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/pessoas/', 'criar')
def criar_pessoa(request):
    """
    Cria uma nova pessoa
    """
    if request.method == 'POST':
        try:
            # Converter datas vazias para None
            def parse_date(date_str):
                return date_str if date_str else None
            
            # Remover máscaras do CPF/CNPJ
            cpf_cnpj = request.POST.get('cpf_cnpj', '')
            if cpf_cnpj:
                cpf_cnpj = cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
            
            pessoa = Pessoa.objects.create(
                empresa=request.empresa,  # Empresa ativa
                tipo=request.POST.get('tipo'),
                nome=request.POST.get('nome', '').strip().upper(),
                nome_fantasia=(request.POST.get('nome_fantasia', '') or '').strip().upper() or None,
                cpf_cnpj=cpf_cnpj or None,
                rg=(request.POST.get('rg', '') or '').strip().upper() or None,
                ie=(request.POST.get('ie', '') or '').strip().upper() or None,
                data_emissao_rg=parse_date(request.POST.get('data_emissao_rg')),
                orgao_emissor=(request.POST.get('orgao_emissor', '') or '').strip().upper() or None,
                sexo=request.POST.get('sexo', '') or None,
                data_nascimento=parse_date(request.POST.get('data_nascimento')),
                cep=request.POST.get('cep', '') or None,
                logradouro=(request.POST.get('logradouro', '') or '').strip().upper() or None,
                numero=request.POST.get('numero', '') or None,
                complemento=(request.POST.get('complemento', '') or '').strip().upper() or None,
                bairro=(request.POST.get('bairro', '') or '').strip().upper() or None,
                cidade=(request.POST.get('cidade', '') or '').strip().upper() or None,
                uf=(request.POST.get('uf', '') or '').strip().upper() or None,
                telefone=request.POST.get('telefone', '') or None,
                celular1=request.POST.get('celular1', '') or None,
                celular2=request.POST.get('celular2', '') or None,
                email=request.POST.get('email', '') or None,
                email2=request.POST.get('email2', '') or None,
                cliente=request.POST.get('cliente') == 'on',
                fornecedor=request.POST.get('fornecedor') == 'on',
                funcionario=request.POST.get('funcionario') == 'on',
                terceiro=request.POST.get('terceiro') == 'on',
                vendedor=request.POST.get('vendedor') == 'on',
                ramo_atividade=(request.POST.get('ramo_atividade', '') or '').strip().upper() or None,
                descricao_ramo=(request.POST.get('descricao_ramo', '') or '').strip().upper() or None,
                titulo_eleitoral=(request.POST.get('titulo_eleitoral', '') or '').strip().upper() or None,
                zona=(request.POST.get('zona', '') or '').strip().upper() or None,
                secao=(request.POST.get('secao', '') or '').strip().upper() or None,
                ctps=(request.POST.get('ctps', '') or '').strip().upper() or None,
                serie=(request.POST.get('serie', '') or '').strip().upper() or None,
                uf_ctps=(request.POST.get('uf_ctps', '') or '').strip().upper() or None,
                data_expedicao_ctps=parse_date(request.POST.get('data_expedicao_ctps')),
                cnh=(request.POST.get('cnh', '') or '').strip().upper() or None,
                cnh_categoria=request.POST.get('cnh_categoria', '') or None,
                escolaridade=request.POST.get('escolaridade', '') or None,
                deficiencia=request.POST.get('deficiencia') == 'on',
                cargo=(request.POST.get('cargo', '') or '').strip().upper() or None,
                data_admissao=parse_date(request.POST.get('data_admissao')),
                data_demissao=parse_date(request.POST.get('data_demissao')),
                tipo_pix=request.POST.get('tipo_pix', '') or None,
                chave_pix=request.POST.get('chave_pix', '').strip().upper() or None,
                banco_id=request.POST.get('banco') or None,
                agencia=request.POST.get('agencia', '').strip().upper() or None,
                conta=request.POST.get('conta', '').strip().upper() or None,
                observacoes=request.POST.get('observacoes', '') or None,
                criado_por=request.user
            )
            # Processar foto do funcionário se enviada
            if request.POST.get('funcionario') == 'on' and 'foto_funcionario' in request.FILES:
                foto = request.FILES['foto_funcionario']
                foto_processada = processar_foto_3x4(foto)
                if foto_processada:
                    pessoa.foto_funcionario = foto_processada
                    pessoa.save()

            
            messages.success(request, f'Pessoa {pessoa.nome} criada com sucesso!')
            return redirect('cadastros:listar_pessoas')
        except Exception as e:
            erro_msg = str(e)
            if 'Duplicate entry' in erro_msg and 'cpf_cnpj' in erro_msg:
                cpf_cnpj_formatado = request.POST.get('cpf_cnpj', '')
                messages.error(request, f'Erro: CPF/CNPJ {cpf_cnpj_formatado} já está cadastrado no sistema!')
            elif 'Duplicate entry' in erro_msg:
                messages.error(request, 'Erro: Já existe um cadastro com essas informações!')
            elif 'cannot be null' in erro_msg.lower():
                messages.error(request, 'Erro: Alguns campos obrigatórios não foram preenchidos!')
            else:
                messages.error(request, f'Erro ao criar pessoa: {erro_msg}')
    
    context = {
        'fornecedores': Pessoa.objects.filter(empresa=request.empresa, fornecedor=True, ativo=True),
        'bancos': Banco.objects.filter(ativo=True).order_by('nome'),
    }
    return render(request, 'cadastros/criar_pessoa.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/pessoas/', 'editar')
def editar_pessoa(request, pessoa_id):
    """
    Edita uma pessoa existente
    """
    pessoa = get_object_or_404(Pessoa, id=pessoa_id, empresa=request.empresa)
    
    if request.method == 'POST':
        try:
            # Converter datas vazias para None
            def parse_date(date_str):
                return date_str if date_str else None
            
            # Remover máscaras do CPF/CNPJ
            cpf_cnpj = request.POST.get('cpf_cnpj', '')
            if cpf_cnpj:
                cpf_cnpj = cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
            
            pessoa.tipo = request.POST.get('tipo')
            pessoa.nome = request.POST.get('nome', '').strip().upper()
            pessoa.nome_fantasia = (request.POST.get('nome_fantasia', '') or '').strip().upper() or None
            pessoa.cpf_cnpj = cpf_cnpj or None
            pessoa.rg = (request.POST.get('rg', '') or '').strip().upper() or None
            pessoa.ie = (request.POST.get('ie', '') or '').strip().upper() or None
            pessoa.data_emissao_rg = parse_date(request.POST.get('data_emissao_rg'))
            pessoa.orgao_emissor = (request.POST.get('orgao_emissor', '') or '').strip().upper() or None
            pessoa.sexo = request.POST.get('sexo', '') or None
            pessoa.data_nascimento = parse_date(request.POST.get('data_nascimento'))
            pessoa.cep = request.POST.get('cep', '') or None
            pessoa.logradouro = (request.POST.get('logradouro', '') or '').strip().upper() or None
            pessoa.numero = request.POST.get('numero', '') or None
            pessoa.complemento = (request.POST.get('complemento', '') or '').strip().upper() or None
            pessoa.bairro = (request.POST.get('bairro', '') or '').strip().upper() or None
            pessoa.cidade = (request.POST.get('cidade', '') or '').strip().upper() or None
            pessoa.uf = (request.POST.get('uf', '') or '').strip().upper() or None
            pessoa.telefone = request.POST.get('telefone', '') or None
            pessoa.celular1 = request.POST.get('celular1', '') or None
            pessoa.celular2 = request.POST.get('celular2', '') or None
            pessoa.email = request.POST.get('email', '') or None
            pessoa.email2 = request.POST.get('email2', '') or None
            pessoa.cliente = request.POST.get('cliente') == 'on'
            pessoa.fornecedor = request.POST.get('fornecedor') == 'on'
            pessoa.funcionario = request.POST.get('funcionario') == 'on'
            pessoa.terceiro = request.POST.get('terceiro') == 'on'
            pessoa.vendedor = request.POST.get('vendedor') == 'on'
            pessoa.ramo_atividade = (request.POST.get('ramo_atividade', '') or '').strip().upper() or None
            pessoa.descricao_ramo = (request.POST.get('descricao_ramo', '') or '').strip().upper() or None
            pessoa.titulo_eleitoral = (request.POST.get('titulo_eleitoral', '') or '').strip().upper() or None
            pessoa.zona = (request.POST.get('zona', '') or '').strip().upper() or None
            pessoa.secao = (request.POST.get('secao', '') or '').strip().upper() or None
            pessoa.ctps = (request.POST.get('ctps', '') or '').strip().upper() or None
            pessoa.serie = (request.POST.get('serie', '') or '').strip().upper() or None
            pessoa.uf_ctps = (request.POST.get('uf_ctps', '') or '').strip().upper() or None
            pessoa.data_expedicao_ctps = parse_date(request.POST.get('data_expedicao_ctps'))
            pessoa.cnh = (request.POST.get('cnh', '') or '').strip().upper() or None
            pessoa.cnh_categoria = request.POST.get('cnh_categoria', '') or None
            pessoa.escolaridade = request.POST.get('escolaridade', '') or None
            pessoa.deficiencia = request.POST.get('deficiencia') == 'on'
            pessoa.cargo = (request.POST.get('cargo', '') or '').strip().upper() or None
            pessoa.data_admissao = parse_date(request.POST.get('data_admissao'))
            pessoa.data_demissao = parse_date(request.POST.get('data_demissao'))
            pessoa.tipo_pix = request.POST.get('tipo_pix', '') or None
            pessoa.chave_pix = request.POST.get('chave_pix', '').strip().upper() or None
            pessoa.banco_id = request.POST.get('banco') or None
            pessoa.agencia = request.POST.get('agencia', '').strip().upper() or None
            pessoa.conta = request.POST.get('conta', '').strip().upper() or None
            pessoa.observacoes = request.POST.get('observacoes', '') or None
            pessoa.atualizado_por = request.user
            # Processar foto do funcionário se enviada
            if request.POST.get('funcionario') == 'on' and 'foto_funcionario' in request.FILES:
                foto = request.FILES['foto_funcionario']
                foto_processada = processar_foto_3x4(foto)
                if foto_processada:
                    pessoa.foto_funcionario = foto_processada

            pessoa.save()
            
            messages.success(request, f'Pessoa {pessoa.nome} atualizada com sucesso!')
            return redirect('cadastros:listar_pessoas')
        except Exception as e:
            print(f"ERRO ao salvar pessoa: {e}")  # DEBUG
            import traceback
            traceback.print_exc()  # DEBUG
            
            erro_msg = str(e)
            
            # Erros de duplicação
            if 'Duplicate entry' in erro_msg and 'cpf_cnpj' in erro_msg:
                cpf_cnpj_formatado = request.POST.get('cpf_cnpj', '')
                messages.error(request, f'⚠️ Este CPF/CNPJ ({cpf_cnpj_formatado}) já pertence a outro cadastro. Por favor, verifique os dados.')
            elif 'Duplicate entry' in erro_msg:
                messages.error(request, '⚠️ Já existe outro cadastro com essas informações. Por favor, verifique os dados informados.')
            
            # Erros de campo obrigatório
            elif 'cannot be null' in erro_msg.lower():
                campo_faltante = ''
                if 'tipo' in erro_msg.lower():
                    campo_faltante = 'Tipo de Pessoa (Física ou Jurídica)'
                elif 'nome' in erro_msg.lower():
                    campo_faltante = 'Nome/Razão Social'
                elif 'cpf_cnpj' in erro_msg.lower():
                    campo_faltante = 'CPF/CNPJ'
                else:
                    campo_faltante = 'campo obrigatório'
                
                messages.error(request, f'⚠️ Por favor, preencha o campo: {campo_faltante}')
            
            # Erro genérico mais amigável
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao atualizar pessoa {pessoa.id}: {erro_msg}')
                messages.error(request, '⚠️ Não foi possível salvar as alterações. Por favor, verifique os dados e tente novamente.')
    
    context = {
        'pessoa': pessoa,
        'bancos': Banco.objects.filter(ativo=True).order_by('nome'),
    }
    return render(request, 'cadastros/editar_pessoa.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/pessoas/', 'excluir')
def excluir_pessoa(request, pessoa_id):
    """
    Exclui uma pessoa (inativa ao invés de deletar)
    """
    pessoa = get_object_or_404(Pessoa, id=pessoa_id, empresa=request.empresa)
    pessoa.ativo = False
    pessoa.atualizado_por = request.user
    pessoa.save()
    messages.success(request, f'Pessoa {pessoa.nome} inativada com sucesso!')
    return redirect('cadastros:listar_pessoas')


@login_required
def get_pessoa_json(request, pessoa_id):
    """
    Retorna dados da pessoa em JSON (para AJAX)
    """
    pessoa = get_object_or_404(Pessoa, id=pessoa_id)
    
    data = {
        'id': pessoa.id,
        'nome': pessoa.nome,
        'logradouro': pessoa.logradouro or '',
        'numero': pessoa.numero or '',
        'complemento': pessoa.complemento or '',
        'bairro': pessoa.bairro or '',
        'cidade': pessoa.cidade or '',
        'uf': pessoa.uf or '',
        'cep': pessoa.cep or '',
        'telefone': pessoa.telefone or '',
        'celular1': pessoa.celular1 or '',
        'email': pessoa.email or '',
    }
    
    return JsonResponse(data)


# ==================== VIEWS DE PRODUTOS ====================

@login_required
@require_empresa
@verificar_permissao_menu('/cadastros/produtos/')
def listar_produtos(request):
    """
    Lista todos os produtos cadastrados da empresa ativa
    """
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')
    
    produtos = Produto.objects.filter(empresa=request.empresa)
    
    if q:
        produtos = produtos.filter(
            Q(codigo__icontains=q) |
            Q(descricao__icontains=q)
        )
    
    if tipo:
        produtos = produtos.filter(tipo=tipo)
    
    produtos = produtos.order_by('descricao')
    
    context = {
        'produtos': produtos,
        'q': q,
        'tipo': tipo,
    }
    return render(request, 'cadastros/listar_produtos.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/produtos/', 'criar')
def criar_produto(request):
    """
    Cria um novo produto
    """
    if request.method == 'POST':
        try:
            from decimal import Decimal
            from django.db.models.functions import Cast
            from django.db.models import IntegerField
            
            fornecedor_id = request.POST.get('fornecedor')
            fornecedor = Pessoa.objects.get(id=fornecedor_id, empresa=request.empresa) if fornecedor_id else None
            
            # Gerar código automaticamente - sempre ignora o que vier do formulário
            # Buscar o último código numérico da empresa
            ultimo_produto = Produto.objects.filter(
                empresa=request.empresa,
                codigo__regex=r'^\d+$'  # Apenas códigos numéricos
            ).annotate(
                codigo_num=Cast('codigo', IntegerField())
            ).order_by('-codigo_num').first()
            
            if ultimo_produto and ultimo_produto.codigo.isdigit():
                proximo_numero = int(ultimo_produto.codigo) + 1
            else:
                proximo_numero = 1
            
            codigo = str(proximo_numero).zfill(4)  # Preenche com zeros à esquerda (ex: 0001)
            
            # Converter campos numéricos
            estoque_atual = request.POST.get('estoque_atual', '').strip()
            estoque_minimo = request.POST.get('estoque_minimo', '').strip()
            custo = request.POST.get('custo', '').strip()
            preco_venda = request.POST.get('preco_venda', '').strip()
            
            produto = Produto.objects.create(
                empresa=request.empresa,
                tipo=request.POST.get('tipo'),
                codigo=codigo,
                descricao=request.POST.get('descricao'),
                descricao_detalhada=request.POST.get('descricao_detalhada', ''),
                unidade=request.POST.get('unidade'),
                estoque_atual=Decimal(estoque_atual) if estoque_atual else Decimal('0'),
                estoque_minimo=Decimal(estoque_minimo) if estoque_minimo else Decimal('0'),
                custo=Decimal(custo) if custo else Decimal('0'),
                preco_venda=Decimal(preco_venda) if preco_venda else Decimal('0'),
                fornecedor=fornecedor,
                criado_por=request.user
            )
            
            messages.success(request, f'Produto {produto.descricao} criado com sucesso! Código: {produto.codigo}')
            return redirect('cadastros:listar_produtos')
        except Exception as e:
            erro_msg = str(e)
            if 'Duplicate entry' in erro_msg and 'codigo' in erro_msg:
                codigo = request.POST.get('codigo', '')
                messages.error(request, f'Erro: Código {codigo} já está cadastrado para outro produto!')
            elif 'Duplicate entry' in erro_msg:
                messages.error(request, 'Erro: Já existe um produto com essas informações!')
            elif 'cannot be null' in erro_msg.lower():
                messages.error(request, 'Erro: Alguns campos obrigatórios não foram preenchidos!')
            else:
                messages.error(request, f'Erro ao criar produto: {erro_msg}')
    
    # Gerar próximo código para exibir no template
    ultimo_produto = Produto.objects.filter(
        empresa=request.empresa,
        codigo__regex=r'^\d+$'
    ).order_by('-codigo').first()
    
    if ultimo_produto and ultimo_produto.codigo.isdigit():
        proximo_codigo = str(int(ultimo_produto.codigo) + 1).zfill(4)
    else:
        proximo_codigo = '0001'
    
    context = {
        'fornecedores': Pessoa.objects.filter(empresa=request.empresa, fornecedor=True, ativo=True).order_by('nome'),
        'proximo_codigo': proximo_codigo,
    }
    return render(request, 'cadastros/criar_produto.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/produtos/', 'editar')
def editar_produto(request, produto_id):
    """
    Edita um produto existente
    """
    produto = get_object_or_404(Produto, id=produto_id, empresa=request.empresa)
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            fornecedor_id = request.POST.get('fornecedor')
            fornecedor = Pessoa.objects.get(id=fornecedor_id, empresa=request.empresa) if fornecedor_id else None
            
            produto.tipo = request.POST.get('tipo')
            produto.codigo = request.POST.get('codigo')
            produto.descricao = request.POST.get('descricao')
            produto.descricao_detalhada = request.POST.get('descricao_detalhada', '')
            produto.unidade = request.POST.get('unidade')
            
            # Converter campos numéricos, tratando valores vazios
            estoque_atual = request.POST.get('estoque_atual', '').strip()
            produto.estoque_atual = Decimal(estoque_atual) if estoque_atual else Decimal('0')
            
            estoque_minimo = request.POST.get('estoque_minimo', '').strip()
            produto.estoque_minimo = Decimal(estoque_minimo) if estoque_minimo else Decimal('0')
            
            custo = request.POST.get('custo', '').strip()
            produto.custo = Decimal(custo) if custo else Decimal('0')
            
            preco_venda = request.POST.get('preco_venda', '').strip()
            produto.preco_venda = Decimal(preco_venda) if preco_venda else Decimal('0')
            
            produto.fornecedor = fornecedor
            produto.atualizado_por = request.user
            produto.save()
            
            messages.success(request, f'Produto {produto.descricao} atualizado com sucesso!')
            return redirect('cadastros:listar_produtos')
        except Exception as e:
            erro_msg = str(e)
            if 'Duplicate entry' in erro_msg and 'codigo' in erro_msg:
                codigo = request.POST.get('codigo', '')
                messages.error(request, f'Erro: Código {codigo} já está cadastrado para outro produto!')
            elif 'Duplicate entry' in erro_msg:
                messages.error(request, 'Erro: Já existe outro produto com essas informações!')
            elif 'cannot be null' in erro_msg.lower():
                messages.error(request, 'Erro: Alguns campos obrigatórios não foram preenchidos!')
            else:
                messages.error(request, f'Erro ao atualizar produto: {erro_msg}')
    
    context = {
        'produto': produto,
        'fornecedores': Pessoa.objects.filter(empresa=request.empresa, fornecedor=True, ativo=True).order_by('nome'),
    }
    return render(request, 'cadastros/editar_produto.html', context)


@login_required
@require_empresa
@verificar_permissao_acao('/cadastros/produtos/', 'excluir')
def excluir_produto(request, produto_id):
    """
    Exclui um produto (inativa ao invés de deletar)
    """
    produto = get_object_or_404(Produto, id=produto_id, empresa=request.empresa)
    produto.ativo = False
    produto.atualizado_por = request.user
    produto.save()
    messages.success(request, f'Produto {produto.descricao} inativado com sucesso!')
    return redirect('cadastros:listar_produtos')
