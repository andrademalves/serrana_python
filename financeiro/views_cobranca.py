"""
Views para Painel de Cobrança
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta, date
from financeiro.models import ParcelaFinanceira, LogCobranca, ReguaCobranca, ReguaEtapa
from financeiro.services.regua_service import ReguaService
from financeiro.services.email_service import EmailService
from financeiro.tasks import enviar_email_task


@login_required
def painel_cobranca(request):
    """
    Painel de Controle de Cobrança
    """
    empresa = request.empresa
    hoje = timezone.now().date()
    
    # Filtros
    periodo = request.GET.get('periodo', '')  # Padrão: TODOS (não filtrar)
    status_cobranca = request.GET.get('status_cobranca', '')
    regua_id = request.GET.get('regua', '')
    
    # Query base - mostrar TODAS as parcelas a receber (independente do status de pagamento)
    parcelas = ParcelaFinanceira.objects.filter(
        titulo__empresa=empresa,
        titulo__tipo='RECEBER'  # Apenas contas a receber
    ).select_related(
        'titulo',
        'titulo__pessoa',
        'regua'
    ).order_by('data_vencimento')
    
    # DEBUG: Verificar total antes de filtros
    total_sem_filtro = parcelas.count()
    print(f"DEBUG: Total parcelas a receber: {total_sem_filtro}")
    print(f"DEBUG: Empresa: {empresa}")
    
    # DEBUG: Verificar campos das parcelas
    if parcelas.exists():
        primeira = parcelas.first()
        print(f"DEBUG: Primeira parcela - ID: {primeira.id}")
        print(f"DEBUG: - valor_original: {primeira.valor_original}")
        print(f"DEBUG: - valor_pago: {primeira.valor_pago}")
        print(f"DEBUG: - saldo_aberto: {primeira.saldo_aberto}")
        print(f"DEBUG: - Cliente: {primeira.titulo.pessoa.nome}")
        print(f"DEBUG: - Número parcela: {primeira.numero_parcela}")
    
    # Aplicar filtros
    if status_cobranca:
        parcelas = parcelas.filter(status_cobranca=status_cobranca)
    
    if regua_id:
        parcelas = parcelas.filter(regua_id=regua_id)
    
    # Filtro por período (opcional)
    if periodo == '7':
        parcelas = parcelas.filter(
            data_vencimento__lte=hoje + timedelta(days=7)
        )
    elif periodo == '15':
        parcelas = parcelas.filter(
            data_vencimento__lte=hoje + timedelta(days=15)
        )
    elif periodo == '30':
        parcelas = parcelas.filter(
            data_vencimento__lte=hoje + timedelta(days=30)
        )
    # Se não especificar período, mostra todas
    
    # KPIs
    disparos_hoje = LogCobranca.objects.filter(
        parcela__titulo__empresa=empresa,
        data_criacao__date=hoje
    ).count()
    
    a_vencer_7d = ParcelaFinanceira.objects.filter(
        titulo__empresa=empresa,
        status__in=['PENDENTE', 'PARCIAL'],
        data_vencimento__gte=hoje,
        data_vencimento__lte=hoje + timedelta(days=7)
    ).count()
    
    vencidas = ParcelaFinanceira.objects.filter(
        titulo__empresa=empresa,
        status__in=['PENDENTE', 'PARCIAL'],
        data_vencimento__lt=hoje
    ).count()
    
    falhas = LogCobranca.objects.filter(
        parcela__titulo__empresa=empresa,
        status='FALHA'
    ).filter(
        Q(tentativas__lt=3) | Q(tentativas__isnull=True)
    ).count()
    
    em_negociacao = ParcelaFinanceira.objects.filter(
        titulo__empresa=empresa,
        status__in=['PENDENTE', 'PARCIAL'],
        status_cobranca__in=['NEGOCIACAO', 'PROMESSA']
    ).count()
    
    # Réguas disponíveis
    reguas = ReguaCobranca.objects.filter(
        empresa=empresa,
        ativa=True
    ).order_by('nome')
    
    context = {
        'parcelas': parcelas[:100],  # Limita exibição
        'total_parcelas': parcelas.count(),
        'disparos_hoje': disparos_hoje,
        'a_vencer_7d': a_vencer_7d,
        'vencidas': vencidas,
        'falhas': falhas,
        'em_negociacao': em_negociacao,
        'reguas': reguas,
        'periodo_selecionado': periodo,
        'status_selecionado': status_cobranca,
        'regua_selecionada': regua_id,
    }
    
    return render(request, 'financeiro/painel_cobranca.html', context)


@login_required
def disparar_cobranca_manual(request, parcela_id):
    """
    Dispara cobrança manual para uma parcela
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    try:
        # Atualizar status
        ReguaService.atualizar_status_cobranca(parcela)
        
        # Verificar se pode enviar
        if not parcela.pode_enviar_cobranca():
            # Mensagem mais detalhada
            if not parcela.regua:
                messages.warning(request, 'Esta parcela não possui régua de cobrança configurada.')
            elif not parcela.regua_ativa:
                messages.warning(
                    request,
                    f'A régua "{parcela.regua.nome}" está INATIVA nesta parcela. '
                    f'Ative a régua antes de disparar a cobrança.'
                )
            elif parcela.status_cobranca == 'BLOQUEADA':
                messages.warning(request, 'Parcela bloqueada para cobrança.')
            elif parcela.status in ['QUITADO', 'CANCELADO']:
                messages.warning(request, f'Parcela está {parcela.get_status_display()}.')
            else:
                messages.warning(
                    request,
                    f'Parcela não pode receber cobrança. Status: {parcela.status} / {parcela.status_cobranca}'
                )
            return redirect('financeiro:painel_cobranca')
        
        # Calcular etapas disponíveis
        etapas = ReguaService.calcular_etapas_disponiveis(parcela)
        
        if not etapas:
            messages.warning(request, 'Nenhuma etapa disponível para disparo no momento.')
            return redirect('financeiro:painel_cobranca')
        
        # Disparar primeira etapa
        etapa = etapas.first()
        
        log = ReguaService.criar_log_cobranca(
            parcela=parcela,
            etapa=etapa,
            canal='EMAIL'
        )
        
        # Enviar de forma síncrona (manual)
        EmailService.enviar_cobranca(log.id)
        
        messages.success(
            request,
            f'Cobrança disparada com sucesso para {parcela.titulo.pessoa.nome}'
        )
        
    except ValueError as e:
        messages.error(request, f'Erro: {str(e)}')
    except Exception as e:
        messages.error(request, f'Erro ao disparar cobrança: {str(e)}')
    
    return redirect('financeiro:painel_cobranca')


@login_required
def pausar_regua(request, parcela_id):
    """
    Pausa régua de cobrança de uma parcela
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    if request.method == 'POST':
        dias = int(request.POST.get('dias', 7))
        motivo = request.POST.get('motivo', 'Pausado manualmente')
        
        ate_data = timezone.now().date() + timedelta(days=dias)
        
        ReguaService.pausar_regua(parcela, ate_data, motivo)
        
        messages.success(
            request,
            f'Régua pausada por {dias} dias até {ate_data.strftime("%d/%m/%Y")}'
        )
    
    return redirect('financeiro:painel_cobranca')


@login_required
def retomar_regua(request, parcela_id):
    """
    Retoma régua de cobrança pausada
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    ReguaService.retomar_regua(parcela)
    
    messages.success(request, 'Régua de cobrança retomada com sucesso')
    
    return redirect('financeiro:painel_cobranca')


@login_required
def marcar_promessa(request, parcela_id):
    """
    Marca promessa de pagamento
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    if request.method == 'POST':
        data_promessa = request.POST.get('data_promessa')
        observacao = request.POST.get('observacao', '')
        
        if data_promessa:
            from datetime import datetime
            data_promessa = datetime.strptime(data_promessa, '%Y-%m-%d').date()
            
            ReguaService.marcar_promessa_pagamento(parcela, data_promessa, observacao)
            
            messages.success(
                request,
                f'Promessa registrada para {data_promessa.strftime("%d/%m/%Y")}'
            )
        else:
            messages.error(request, 'Data da promessa é obrigatória')
    
    return redirect('financeiro:painel_cobranca')


@login_required
def marcar_negociacao(request, parcela_id):
    """
    Marca parcela como em negociação
    Útil quando está em tratativa com o cliente para parcelamento, desconto, etc.
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    if request.method == 'POST':
        observacao = request.POST.get('observacao_negociacao', '')
        
        parcela.status_cobranca = 'NEGOCIACAO'
        parcela.observacao_promessa = observacao  # Reutilizando campo existente
        parcela.save()
        
        messages.success(
            request,
            f'Parcela marcada como "Em Negociação". A régua de cobrança automática está pausada.'
        )
    else:
        # Se não for POST, marca sem observação
        parcela.status_cobranca = 'NEGOCIACAO'
        parcela.save()
        
        messages.success(
            request,
            f'Parcela marcada como "Em Negociação". A régua de cobrança automática está pausada.'
        )
    
    return redirect('financeiro:painel_cobranca')


@login_required
def marcar_normal(request, parcela_id):
    """
    Volta parcela ao status normal de cobrança
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    parcela.status_cobranca = 'NORMAL'
    parcela.save()
    
    messages.success(
        request,
        f'Parcela voltou ao status "Normal". A régua de cobrança está ativa novamente.'
    )
    
    return redirect('financeiro:painel_cobranca')


@login_required
def ativar_regua_parcela(request, parcela_id):
    """
    Ativa a régua de cobrança em uma parcela
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    if not parcela.regua:
        messages.error(request, 'Esta parcela não possui régua de cobrança configurada.')
        return redirect('financeiro:painel_cobranca')
    
    if parcela.regua_ativa:
        messages.info(request, f'A régua "{parcela.regua.nome}" já está ativa.')
    else:
        parcela.regua_ativa = True
        parcela.save()
        messages.success(
            request,
            f'Régua "{parcela.regua.nome}" ativada com sucesso! '
            f'Agora você pode disparar cobranças para esta parcela.'
        )
    
    return redirect('financeiro:painel_cobranca')


@login_required
def desativar_regua_parcela(request, parcela_id):
    """
    Desativa a régua de cobrança em uma parcela
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    parcela.regua_ativa = False
    parcela.save()
    
    messages.success(request, 'Régua desativada. Cobranças automáticas foram pausadas.')
    return redirect('financeiro:painel_cobranca')


@login_required
def reenviar_cobranca_manual(request, parcela_id):
    """
    Reenvia cobrança manualmente IGNORANDO se já foi enviado
    Útil para testes e reenvios
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    try:
        # Verificações básicas
        if not parcela.regua:
            messages.warning(request, 'Esta parcela não possui régua de cobrança configurada.')
            return redirect('financeiro:painel_cobranca')
            
        if not parcela.regua_ativa:
            messages.warning(
                request,
                f'A régua "{parcela.regua.nome}" está INATIVA. Ative antes de reenviar.'
            )
            return redirect('financeiro:painel_cobranca')
        
        if parcela.status in ['QUITADO', 'CANCELADO']:
            messages.warning(request, f'Parcela está {parcela.get_status_display()}.')
            return redirect('financeiro:painel_cobranca')
        
        # Busca TODAS etapas da régua (ignora se já enviou)
        offset_atual = (date.today() - parcela.data_vencimento).days
        
        etapas = ReguaEtapa.objects.filter(
            regua=parcela.regua,
            ativo=True,
            offset_dias=offset_atual
        ).order_by('ordem')
        
        if not etapas.exists():
            messages.warning(
                request,
                f'Nenhuma etapa configurada para {offset_atual} dias '
                f'{"após" if offset_atual > 0 else "antes do"} vencimento.'
            )
            return redirect('financeiro:painel_cobranca')
        
        # Pega primeira etapa
        etapa = etapas.first()
        
        # Cria log e envia
        log = ReguaService.criar_log_cobranca(
            parcela=parcela,
            etapa=etapa,
            canal='EMAIL'
        )
        
        EmailService.enviar_cobranca(log.id)
        
        messages.success(
            request,
            f'Cobrança REENVIADA com sucesso para {parcela.titulo.pessoa.nome}! '
            f'Etapa: {etapa.nome}'
        )
        
    except ValueError as e:
        messages.error(request, f'Erro: {str(e)}')
    except Exception as e:
        messages.error(request, f'Erro ao reenviar: {str(e)}')
    
    return redirect('financeiro:painel_cobranca')


@login_required
def reprocessar_falhas(request):
    """
    Reprocessa todas as falhas
    """
    from financeiro.tasks import reprocessar_falhas_task
    
    # Enfileira task assíncrona
    reprocessar_falhas_task.delay()
    
    messages.success(request, 'Reprocessamento de falhas iniciado em background')
    
    return redirect('financeiro:painel_cobranca')


@login_required
def historico_cobranca(request, parcela_id):
    """
    Mostra histórico de cobranças de uma parcela
    """
    parcela = get_object_or_404(
        ParcelaFinanceira,
        id=parcela_id,
        titulo__empresa=request.empresa
    )
    
    logs = LogCobranca.objects.filter(
        parcela=parcela
    ).select_related('etapa').order_by('-data_criacao')
    
    context = {
        'parcela': parcela,
        'logs': logs,
    }
    
    return render(request, 'financeiro/historico_cobranca.html', context)


@login_required
def criar_regua(request):
    """
    Cria uma nova régua de cobrança com interface amigável
    """
    from financeiro.forms import ReguaCobrancaForm, ReguaEtapaFormSet
    
    if request.method == 'POST':
        print("=" * 60)
        print("DEBUG CRIAR RÉGUA - POST recebido")
        print("=" * 60)
        print(f"POST data: {request.POST}")
        
        form = ReguaCobrancaForm(request.POST)
        formset = ReguaEtapaFormSet(request.POST)
        
        print(f"Form is_valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        
        print(f"Formset is_valid: {formset.is_valid()}")
        if not formset.is_valid():
            print(f"Formset errors: {formset.errors}")
        
        if form.is_valid() and formset.is_valid():
            print("✓ Formulários válidos! Salvando...")
            regua = form.save()
            print(f"✓ Régua salva: ID={regua.id}, Nome={regua.nome}")
            
            formset.instance = regua
            etapas_salvas = formset.save()
            print(f"✓ Etapas salvas: {len(etapas_salvas)}")
            
            messages.success(
                request,
                f'Régua "{regua.nome}" criada com sucesso!'
            )
            return redirect('financeiro:editar_regua', regua_id=regua.id)
        else:
            print("✗ Formulários inválidos!")
            messages.error(request, 'Erro ao salvar a régua. Verifique os campos.')
    else:
        form = ReguaCobrancaForm(initial={'empresa': request.empresa, 'ativa': True})
        formset = ReguaEtapaFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'acao': 'criar',
    }
    
    return render(request, 'financeiro/regua_form.html', context)


@login_required
def editar_regua(request, regua_id):
    """
    Edita uma régua de cobrança existente
    """
    from financeiro.forms import ReguaCobrancaForm, ReguaEtapaFormSet
    
    regua = get_object_or_404(
        ReguaCobranca,
        id=regua_id,
        empresa=request.empresa
    )
    
    if request.method == 'POST':
        form = ReguaCobrancaForm(request.POST, instance=regua)
        formset = ReguaEtapaFormSet(request.POST, instance=regua)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'Régua "{regua.nome}" atualizada com sucesso!')
            return redirect('financeiro:editar_regua', regua_id=regua.id)
    else:
        form = ReguaCobrancaForm(instance=regua)
        formset = ReguaEtapaFormSet(instance=regua)
    
    context = {
        'form': form,
        'formset': formset,
        'regua': regua,
        'acao': 'editar',
    }
    
    return render(request, 'financeiro/regua_form.html', context)


@login_required
def listar_reguas(request):
    """
    Lista todas as réguas da empresa
    """
    print(f"DEBUG RÉGUAS: Empresa = {request.empresa}")
    print(f"DEBUG RÉGUAS: Empresa ID = {request.empresa.id}")
    
    reguas = ReguaCobranca.objects.filter(
        empresa=request.empresa
    ).annotate(
        total_etapas=Count('etapas')
    ).order_by('-ativa', 'nome')
    
    print(f"DEBUG RÉGUAS: Total encontradas = {reguas.count()}")
    
    # DEBUG: Listar todas as réguas no banco
    todas_reguas = ReguaCobranca.objects.all()
    print(f"DEBUG RÉGUAS: Total no banco = {todas_reguas.count()}")
    for r in todas_reguas:
        print(f"  - ID: {r.id}, Nome: {r.nome}, Empresa: {r.empresa} (ID: {r.empresa.id})")
    
    context = {
        'reguas': reguas,
    }
    
    return render(request, 'financeiro/regua_list.html', context)
