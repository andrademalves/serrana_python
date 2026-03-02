from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse
import json

from .models import (
    Pipeline, EtapaFunil, Oportunidade, AtividadeCRM,
    AlertaRetorno, AnexoOportunidade, HistoricoEtapa
)
from usuarios.models import Empresa
from cadastros.models import Pessoa
from projetos.models import Orcamento, OrcamentoItem, OrcamentoParcela
from django.contrib.auth.models import User


def is_admin_or_manager(user):
    """Verifica se usuário é admin ou gerente"""
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Gerente']).exists()


def get_user_empresa(request):
    """Pega empresa do usuário logado"""
    # Usa request.empresa que é injetado pelo middleware EmpresaAtivaMiddleware
    return request.empresa


@login_required
def kanban_view(request):
    """View principal do Kanban"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    # Filtros
    pipeline_id = request.GET.get('pipeline')
    vendedor_id = request.GET.get('vendedor')
    search = request.GET.get('search', '')
    
    # Pipeline padrão ou primeiro
    if pipeline_id:
        pipeline = get_object_or_404(Pipeline, id=pipeline_id, empresa=empresa)
    else:
        pipeline = Pipeline.objects.filter(empresa=empresa, ativo=True).order_by('-padrao', 'id').first()
        if not pipeline:
            # Criar pipeline padrão se não existir
            pipeline = Pipeline.objects.create(
                empresa=empresa,
                nome='Pipeline Principal',
                padrao=True,
                criado_por=request.user
            )
    
    # Etapas do pipeline
    etapas = EtapaFunil.objects.filter(pipeline=pipeline, ativo=True).order_by('ordem')
    
    # Oportunidades base query
    oportunidades_qs = Oportunidade.objects.filter(
        empresa=empresa,
        pipeline=pipeline
    ).select_related('etapa', 'responsavel', 'cliente', 'orcamento', 'projeto')
    
    # Filtro de permissão: vendedor vê apenas suas oportunidades
    if not is_admin:
        oportunidades_qs = oportunidades_qs.filter(responsavel=request.user)
    elif vendedor_id:
        # Filtrar por vendedor (Pessoa): buscar oportunidades cujo responsável está vinculado a esse vendedor
        vendedor_pessoa = Pessoa.objects.filter(id=vendedor_id, empresa=empresa).first()
        if vendedor_pessoa and vendedor_pessoa.usuario:
            oportunidades_qs = oportunidades_qs.filter(responsavel=vendedor_pessoa.usuario)
        else:
            # Se vendedor não tem usuário vinculado, buscar por descrição (temporário)
            oportunidades_qs = oportunidades_qs.filter(descricao__icontains=f"Vendedor atribuído:")
    
    # Busca
    if search:
        oportunidades_qs = oportunidades_qs.filter(
            Q(titulo__icontains=search) |
            Q(nome_contato__icontains=search) |
            Q(empresa_contato__icontains=search) |
            Q(email__icontains=search) |
            Q(telefone__icontains=search)
        )
    
    # Organizar oportunidades por etapa
    oportunidades_por_etapa = {}
    for etapa in etapas:
        oportunidades_por_etapa[etapa.id] = oportunidades_qs.filter(etapa=etapa).order_by('-updated_at')
    
    # Vendedores cadastrados (Pessoa) - para filtro E atribuição
    vendedores = None
    if is_admin:
        vendedores = Pessoa.objects.filter(
            empresa=empresa,
            vendedor=True,
            ativo=True
        ).order_by('nome')
    
    # Pipelines da empresa
    pipelines = Pipeline.objects.filter(empresa=empresa, ativo=True)
    
    context = {
        'pipeline': pipeline,
        'pipelines': pipelines,
        'etapas': etapas,
        'oportunidades_por_etapa': oportunidades_por_etapa,
        'is_admin': is_admin,
        'vendedores': vendedores,
        'vendedores_pessoa': vendedores,  # Mantém compatibilidade com modal
        'search': search,
        'vendedor_selecionado': vendedor_id,
        'current_module': 'crm',  # Para o sidebar
    }
    
    return render(request, 'crm/kanban.html', context)


@login_required
def oportunidade_detail(request, pk):
    """Detalhes da oportunidade"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, pk=pk, empresa=empresa)
    
    # Verificar permissão
    if not is_admin and oportunidade.responsavel != request.user:
        messages.error(request, 'Você não tem permissão para acessar esta oportunidade.')
        return redirect('crm:kanban')
    
    # Buscar dados relacionados
    atividades = oportunidade.atividades.all().order_by('-data_atividade')
    alertas = oportunidade.alertas.filter(status='pendente').order_by('data_hora')
    alertas_concluidos = oportunidade.alertas.filter(status='concluido').order_by('-concluido_em')[:10]
    anexos = oportunidade.anexos.all().order_by('-created_at')
    historico = oportunidade.historico_etapas.all().order_by('-data_hora')
    
    # Vendedores disponíveis para troca de responsável (apenas admin)
    vendedores = None
    if is_admin:
        vendedores = Pessoa.objects.filter(
            empresa=empresa,
            vendedor=True,
            ativo=True
        ).exclude(id=oportunidade.responsavel.id if hasattr(oportunidade.responsavel, 'pessoa') else None).order_by('nome')
    
    context = {
        'oportunidade': oportunidade,
        'atividades': atividades,
        'alertas': alertas,
        'alertas_concluidos': alertas_concluidos,
        'anexos': anexos,
        'historico': historico,
        'vendedores': vendedores,
        'is_admin': is_admin,
        'current_module': 'crm',  # Para o sidebar
    }
    
    return render(request, 'crm/oportunidade_detail.html', context)


@login_required
@require_POST
def criar_oportunidade_rapida(request):
    """Cria oportunidade rapidamente (modal)"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    try:
        pipeline_id = request.POST.get('pipeline_id')
        pipeline = get_object_or_404(Pipeline, id=pipeline_id, empresa=empresa)
        
        # Primeira etapa do pipeline
        etapa = EtapaFunil.objects.filter(pipeline=pipeline, ativo=True).order_by('ordem').first()
        if not etapa:
            return JsonResponse({'success': False, 'error': 'Pipeline sem etapas configuradas'}, status=400)
        
        # Determinar responsável: admin pode atribuir, vendedor recebe automaticamente
        responsavel = request.user  # Padrão: criador
        vendedor_nome = None
        
        if is_admin:
            # Admin pode atribuir a um vendedor específico
            vendedor_pessoa_id = request.POST.get('vendedor_pessoa_id')
            if vendedor_pessoa_id:
                # Buscar vendedor (Pessoa) selecionado
                vendedor_pessoa = Pessoa.objects.filter(
                    id=vendedor_pessoa_id,
                    empresa=empresa,
                    vendedor=True,
                    ativo=True
                ).first()
                
                if vendedor_pessoa:
                    vendedor_nome = vendedor_pessoa.nome
                    # Verificar se vendedor tem usuário vinculado
                    if vendedor_pessoa.usuario:
                        responsavel = vendedor_pessoa.usuario
                    # Senão, mantém admin como responsável e registra nas observações
        
        oportunidade = Oportunidade.objects.create(
            empresa=empresa,
            pipeline=pipeline,
            etapa=etapa,
            titulo=request.POST.get('titulo'),
            nome_contato=request.POST.get('nome_contato'),
            telefone=request.POST.get('telefone', ''),
            email=request.POST.get('email', ''),
            origem=request.POST.get('origem', 'outro'),
            responsavel=responsavel,
            primeiro_atendente=responsavel,  # Registrar primeiro atendente
            criado_por=request.user,
        )
        
        # Se vendedor foi selecionado mas não tem usuário, registrar nas observações
        if vendedor_nome and responsavel == request.user and is_admin:
            oportunidade.descricao = f"Vendedor atribuído: {vendedor_nome}\n(Sem usuário vinculado - responsável: {request.user.get_full_name() or request.user.username})"
            oportunidade.save()
        
        return JsonResponse({
            'success': True,
            'oportunidade_id': oportunidade.id,
            'message': 'Oportunidade criada com sucesso!'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def atualizar_etapa_oportunidade(request):
    """Atualiza etapa da oportunidade (drag & drop)"""
    import logging
    logger = logging.getLogger(__name__)
    
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    try:
        data = json.loads(request.body)
        oportunidade_id = data.get('oportunidade_id')
        etapa_id = data.get('etapa_id')
        
        logger.info(f"Recebido: oportunidade_id={oportunidade_id}, etapa_id={etapa_id}")
        
        oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
        logger.info(f"Oportunidade encontrada: {oportunidade.titulo}, etapa atual: {oportunidade.etapa.nome}")
        
        # Verificar permissão
        if not is_admin and oportunidade.responsavel != request.user:
            logger.warning(f"Usuário {request.user} sem permissão")
            return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
        
        nova_etapa = get_object_or_404(EtapaFunil, id=etapa_id, pipeline=oportunidade.pipeline)
        logger.info(f"Nova etapa: {nova_etapa.nome}")
        
        # Guardar etapa anterior para histórico
        etapa_anterior = oportunidade.etapa
        
        # Atualizar
        oportunidade.etapa = nova_etapa
        oportunidade.save()
        logger.info(f"Oportunidade atualizada no banco!")
        
        # Criar histórico de mudança
        HistoricoEtapa.objects.create(
            oportunidade=oportunidade,
            etapa_de=etapa_anterior,
            etapa_para=nova_etapa,
            usuario=request.user
        )
        logger.info(f"Histórico criado!")
        
        return JsonResponse({
            'success': True,
            'message': f'Oportunidade movida para {nova_etapa.nome}'
        })
    
    except Exception as e:
        logger.error(f"Erro ao atualizar etapa: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def criar_atividade(request, oportunidade_id):
    """Cria atividade na oportunidade"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
    
    # Verificar permissão
    if not is_admin and oportunidade.responsavel != request.user:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    try:
        atividade = AtividadeCRM.objects.create(
            oportunidade=oportunidade,
            tipo=request.POST.get('tipo', 'nota'),
            titulo=request.POST.get('titulo', ''),
            descricao=request.POST.get('descricao'),
            criado_por=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'atividade': {
                'id': atividade.id,
                'tipo': atividade.get_tipo_display(),
                'titulo': atividade.titulo,
                'descricao': atividade.descricao,
                'data': atividade.data_atividade.strftime('%d/%m/%Y %H:%M'),
                'usuario': atividade.criado_por.get_full_name() or atividade.criado_por.username,
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def criar_alerta(request, oportunidade_id):
    """Cria alerta/tarefa na oportunidade"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
    
    # Verificar permissão
    if not is_admin and oportunidade.responsavel != request.user:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    try:
        from datetime import datetime
        data_hora_str = request.POST.get('data_hora')
        data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        
        alerta = AlertaRetorno.objects.create(
            oportunidade=oportunidade,
            titulo=request.POST.get('titulo'),
            descricao=request.POST.get('descricao', ''),
            data_hora=data_hora,
            prioridade=request.POST.get('prioridade', 'media'),
            criado_por=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'alerta': {
                'id': alerta.id,
                'titulo': alerta.titulo,
                'data_hora': alerta.data_hora.strftime('%d/%m/%Y %H:%M'),
                'prioridade': alerta.get_prioridade_display(),
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def concluir_alerta(request, alerta_id):
    """Marca alerta como concluído"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    alerta = get_object_or_404(AlertaRetorno, id=alerta_id, oportunidade__empresa=empresa)
    
    # Verificar permissão
    if not is_admin and alerta.oportunidade.responsavel != request.user:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    alerta.marcar_concluido(request.user)
    
    return JsonResponse({'success': True, 'message': 'Alerta concluído'})


@login_required
def criar_orcamento_de_oportunidade(request, oportunidade_id):
    """Cria orçamento a partir de uma oportunidade"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
    
    # Verificar permissão
    if not is_admin and oportunidade.responsavel != request.user:
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('crm:oportunidade_detail', pk=oportunidade_id)
    
    # Verificar se já tem orçamento
    if oportunidade.orcamento:
        messages.warning(request, 'Esta oportunidade já possui um orçamento vinculado.')
        return redirect('projetos:visualizar_orcamento', pk=oportunidade.orcamento.id)
    
    if request.method == 'POST':
        # Criar orçamento
        try:
            cliente = oportunidade.cliente
            if not cliente:
                # Tentar criar cliente básico se não existir
                cliente = Pessoa.objects.create(
                    empresa=empresa,
                    tipo='F',  # F=Física ou J=Jurídica
                    nome=oportunidade.nome_contato,
                    telefone=oportunidade.telefone or '',
                    email=oportunidade.email or '',
                    cpf_cnpj='000.000.000-00',  # CPF temporário - deve ser editado depois
                    cliente=True,  # Marcar como cliente
                    ativo=True,
                )
            
            # Obter vendedor como Pessoa
            vendedor_pessoa = None
            if hasattr(oportunidade.responsavel, 'pessoa'):
                vendedor_pessoa = oportunidade.responsavel.pessoa
            else:
                # Buscar primeiro vendedor ativo
                vendedor_pessoa = Pessoa.objects.filter(
                    empresa=empresa,
                    vendedor=True,
                    ativo=True
                ).first()
                
            if not vendedor_pessoa:
                messages.error(request, 'Não há vendedor cadastrado no sistema. Por favor, cadastre um vendedor primeiro.')
                return redirect('crm:oportunidade_detail', pk=oportunidade_id)
            
            orcamento = Orcamento.objects.create(
                empresa=empresa,
                cliente=cliente,
                vendedor=vendedor_pessoa,  # Deve ser Pessoa, não User
                data_orcamento=timezone.now().date(),
                descricao=request.POST.get('descricao', oportunidade.descricao or oportunidade.titulo),
                observacoes=f"Gerado da oportunidade: {oportunidade.titulo}",
                criado_por=request.user,
                validade_dias=int(request.POST.get('validade_dias', 30)),
            )
            
            # Vincular
            oportunidade.orcamento = orcamento
            oportunidade.save()
            
            # Registrar atividade
            AtividadeCRM.objects.create(
                oportunidade=oportunidade,
                tipo='proposta',
                titulo='Orçamento Criado',
                descricao=f'Orçamento {orcamento.codigo} criado e vinculado',
                criado_por=request.user,
            )
            
            messages.success(request, f'Orçamento {orcamento.codigo} criado com sucesso!')
            return redirect('projetos:editar_orcamento', pk=orcamento.id)
        
        except Exception as e:
            import traceback
            erro_detalhado = traceback.format_exc()
            print(f"Erro ao criar orçamento: {erro_detalhado}")
            
            # Mensagem amigável baseada no tipo de erro
            if 'Data too long' in str(e):
                mensagem = 'Erro nos dados do cliente. Por favor, verifique as informações e tente novamente.'
            elif 'vendedor' in str(e).lower():
                mensagem = 'Erro ao vincular vendedor. Verifique se há vendedores cadastrados no sistema.'
            elif 'cliente' in str(e).lower():
                mensagem = 'Erro ao processar dados do cliente. Verifique se o cliente está cadastrado corretamente.'
            else:
                mensagem = 'Não foi possível criar o orçamento. Por favor, verifique os dados e tente novamente.'
            
            messages.error(request, mensagem)
            return redirect('crm:oportunidade_detail', pk=oportunidade_id)
    
    context = {
        'oportunidade': oportunidade,
        'current_module': 'crm',  # Para o sidebar
    }
    
    return render(request, 'crm/criar_orcamento.html', context)


@login_required
@require_POST
def trocar_responsavel(request, oportunidade_id):
    """Troca o responsável pelo lead mantendo histórico"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
    
    # Verificar permissão: apenas admin pode trocar responsável
    if not is_admin:
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)
    
    try:
        novo_responsavel_id = request.POST.get('novo_responsavel_id')
        
        # Buscar novo responsável
        # Pode ser vendedor (Pessoa) ou usuário (User)
        tipo = request.POST.get('tipo', 'pessoa')  # 'pessoa' ou 'usuario'
        
        novo_responsavel = None
        novo_responsavel_nome = None
        
        if tipo == 'pessoa':
            # Buscar vendedor (Pessoa)
            vendedor_pessoa = Pessoa.objects.filter(
                id=novo_responsavel_id,
                empresa=empresa,
                vendedor=True,
                ativo=True
            ).first()
            
            if not vendedor_pessoa:
                return JsonResponse({'success': False, 'error': 'Vendedor não encontrado'}, status=400)
            
            novo_responsavel_nome = vendedor_pessoa.nome
            
            # Verificar se vendedor tem usuário vinculado
            if vendedor_pessoa.usuario:
                novo_responsavel = vendedor_pessoa.usuario
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Vendedor {vendedor_pessoa.nome} não tem usuário vinculado no sistema'
                }, status=400)
        else:
            # Buscar usuário direto
            novo_responsavel = User.objects.filter(id=novo_responsavel_id).first()
            if not novo_responsavel:
                return JsonResponse({'success': False, 'error': 'Usuário não encontrado'}, status=400)
            novo_responsavel_nome = novo_responsavel.get_full_name() or novo_responsavel.username
        
        # Salvar responsável anterior
        responsavel_anterior = oportunidade.responsavel
        responsavel_anterior_nome = responsavel_anterior.get_full_name() or responsavel_anterior.username
        
        # Definir primeiro_atendente se ainda não foi definido
        if not oportunidade.primeiro_atendente:
            oportunidade.primeiro_atendente = responsavel_anterior
        
        # Atualizar responsável
        oportunidade.responsavel = novo_responsavel
        oportunidade.save()
        
        # Registrar mudança no histórico
        AtividadeCRM.objects.create(
            oportunidade=oportunidade,
            tipo='outro',
            titulo='Responsável Alterado',
            descricao=f"Responsável alterado de '{responsavel_anterior_nome}' para '{novo_responsavel_nome}' por {request.user.get_full_name() or request.user.username}",
            criado_por=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Responsável alterado para {novo_responsavel_nome}',
            'novo_responsavel': novo_responsavel_nome
        })
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def desvincular_orcamento(request, oportunidade_id):
    """Desvincula orçamento da oportunidade (não exclui o orçamento)"""
    empresa = get_user_empresa(request)
    is_admin = is_admin_or_manager(request.user)
    
    oportunidade = get_object_or_404(Oportunidade, id=oportunidade_id, empresa=empresa)
    
    # Verificar permissão
    if not is_admin and oportunidade.responsavel != request.user:
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('crm:oportunidade_detail', pk=oportunidade_id)
    
    # Verificar se tem orçamento vinculado
    if not oportunidade.orcamento:
        messages.warning(request, 'Esta oportunidade não possui orçamento vinculado.')
        return redirect('crm:oportunidade_detail', pk=oportunidade_id)
    
    try:
        orcamento_codigo = oportunidade.orcamento.codigo
        
        # Desvincular (não excluir o orçamento)
        oportunidade.orcamento = None
        oportunidade.save()
        
        # Registrar atividade
        AtividadeCRM.objects.create(
            oportunidade=oportunidade,
            tipo='nota',
            titulo='Orçamento Desvinculado',
            descricao=f'Orçamento {orcamento_codigo} foi desvinculado desta oportunidade',
            criado_por=request.user,
        )
        
        messages.success(request, f'Orçamento {orcamento_codigo} desvinculado com sucesso!')
        
    except Exception as e:
        messages.error(request, f'Erro ao desvincular orçamento: {str(e)}')
    
    return redirect('crm:oportunidade_detail', pk=oportunidade_id)


# ==================== ADMIN: GERENCIAR ETAPAS ====================

@login_required
@user_passes_test(is_admin_or_manager)
def gerenciar_etapas(request, pipeline_id):
    """Gerenciar etapas do funil (admin only)"""
    empresa = get_user_empresa(request)
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, empresa=empresa)
    
    etapas = EtapaFunil.objects.filter(pipeline=pipeline).order_by('ordem')
    
    context = {
        'pipeline': pipeline,
        'etapas': etapas,
        'current_module': 'crm',  # Para o sidebar
    }
    
    return render(request, 'crm/gerenciar_etapas.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
@require_POST
def criar_etapa(request, pipeline_id):
    """Cria nova etapa"""
    empresa = get_user_empresa(request)
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, empresa=empresa)
    
    try:
        # Próxima ordem
        ultima_ordem = EtapaFunil.objects.filter(pipeline=pipeline).order_by('-ordem').first()
        ordem = (ultima_ordem.ordem + 1) if ultima_ordem else 0
        
        etapa = EtapaFunil.objects.create(
            pipeline=pipeline,
            nome=request.POST.get('nome'),
            ordem=ordem,
            cor=request.POST.get('cor', '#3498db'),
            is_final=request.POST.get('is_final') == 'on',
            tipo_final=request.POST.get('tipo_final', 'none'),
        )
        
        messages.success(request, f'Etapa "{etapa.nome}" criada com sucesso!')
    
    except Exception as e:
        messages.error(request, f'Erro ao criar etapa: {str(e)}')
    
    return redirect('crm:gerenciar_etapas', pipeline_id=pipeline_id)


@login_required
@user_passes_test(is_admin_or_manager)
@require_POST
def deletar_etapa(request, etapa_id):
    """Deleta etapa (se não tiver oportunidades)"""
    empresa = get_user_empresa(request)
    etapa = get_object_or_404(EtapaFunil, id=etapa_id, pipeline__empresa=empresa)
    
    if etapa.oportunidades.exists():
        messages.error(request, 'Não é possível excluir etapa com oportunidades. Mova-as primeiro.')
    else:
        pipeline_id = etapa.pipeline.id
        etapa.delete()
        messages.success(request, 'Etapa excluída com sucesso!')
        return redirect('crm:gerenciar_etapas', pipeline_id=pipeline_id)
    
    return redirect('crm:gerenciar_etapas', pipeline_id=etapa.pipeline.id)
