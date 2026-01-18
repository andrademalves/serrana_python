"""
Views do Módulo Financeiro
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import date, timedelta
from decimal import Decimal
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from usuarios.decorators import verificar_permissao_menu, require_empresa

from .models import (
    TituloFinanceiro, ParcelaFinanceira, BaixaFinanceira,
    ContaFinanceira, FormaPagamento, CentroCusto, Banco, PlanoConta
)
from cadastros.models import Pessoa
from .services.indicadores import IndicadoresSaudeFinanceira
from .services.ponto_equilibrio import AnalisePontoEquilibrio
from .forms import TituloFinanceiroForm, BaixaFinanceiraForm, BancoForm, CentroCustoForm, FormaPagamentoForm, PlanoContaForm


# =========================================
# DASHBOARD PRINCIPAL
# =========================================

@login_required
@require_empresa
@verificar_permissao_menu('/financeiro/')
def dashboard(request):
    """Dashboard financeiro com indicadores e gráficos"""
    dados = IndicadoresSaudeFinanceira.dashboard_resumo(empresa=request.empresa)
    
    # Buscar contas financeiras com saldos
    contas_financeiras = ContaFinanceira.objects.filter(
        empresa=request.empresa,
        ativo=True
    ).select_related('banco').order_by('nome')
    
    # Calcular saldo total de todas as contas
    saldo_total_contas = sum([conta.saldo_atual() for conta in contas_financeiras])
    
    context = {
        'dados': dados,
        'hoje': date.today(),
        'contas_financeiras': contas_financeiras,
        'saldo_total_contas': saldo_total_contas,
    }
    
    return render(request, 'financeiro/dashboard.html', context)


# =========================================
# TÍTULOS FINANCEIROS
# =========================================

@login_required
def listar_titulos(request):
    """Lista títulos com filtros e paginação"""
    from django.core.paginator import Paginator
    
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    pessoa_id = request.GET.get('pessoa', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    por_pagina = request.GET.get('por_pagina', '20')
    
    titulos = TituloFinanceiro.objects.filter(empresa=request.empresa).select_related('pessoa', 'centro_custo', 'plano_conta').all()
    
    # Filtros
    if tipo:
        titulos = titulos.filter(tipo=tipo)
    
    if status:
        titulos = titulos.filter(status=status)
    
    if pessoa_id:
        titulos = titulos.filter(pessoa_id=pessoa_id)
    
    if data_inicio:
        titulos = titulos.filter(data_emissao__gte=data_inicio)
    
    if data_fim:
        titulos = titulos.filter(data_emissao__lte=data_fim)
    
    # Ordenar
    titulos = titulos.order_by('-data_emissao', '-id')
    
    # Calcular totais (antes da paginação)
    total_pagar = titulos.filter(tipo='PAGAR').aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    total_receber = titulos.filter(tipo='RECEBER').aggregate(total=Sum('valor_total'))['total'] or Decimal('0')
    saldo_total = total_receber - total_pagar
    
    # Paginação
    try:
        itens_por_pagina = int(por_pagina)
        if itens_por_pagina not in [10, 20, 30]:
            itens_por_pagina = 20
    except (ValueError, TypeError):
        itens_por_pagina = 20
    
    paginator = Paginator(titulos, itens_por_pagina)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    pessoas = Pessoa.objects.filter(empresa=request.empresa, ativo=True).order_by('nome')
    
    context = {
        'titulos': page_obj,
        'page_obj': page_obj,
        'pessoas': pessoas,
        'total_pagar': total_pagar,
        'total_receber': total_receber,
        'saldo_total': saldo_total,
        'por_pagina': por_pagina,
        'filtros': {
            'tipo': tipo,
            'status': status,
            'pessoa_id': pessoa_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'financeiro/listar_titulos.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/financeiro/')
def criar_titulo(request):
    """Cria novo título financeiro"""
    if request.method == 'POST':
        form = TituloFinanceiroForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            titulo = form.save(commit=False)
            titulo.empresa = request.empresa
            titulo.criado_por = request.user
            titulo.save()
            
            # Gerar parcelas automaticamente
            titulo.gerar_parcelas()
            
            # Aplicar régua de cobrança se selecionada
            regua = form.cleaned_data.get('regua_cobranca')
            ativar = form.cleaned_data.get('ativar_regua', False)
            
            if regua and titulo.tipo == 'RECEBER':
                for parcela in titulo.parcelas.all():
                    parcela.regua = regua
                    parcela.regua_ativa = ativar
                    parcela.save()
                
                if ativar:
                    messages.success(request, f'Título {titulo.numero_documento} criado com sucesso! Régua "{regua.nome}" ativada nas parcelas.')
                else:
                    messages.success(request, f'Título {titulo.numero_documento} criado com sucesso! Régua "{regua.nome}" associada (inativa).')
            else:
                messages.success(request, f'Título {titulo.numero_documento} criado com sucesso!')
            
            return redirect('financeiro:detalhe_titulo', titulo_id=titulo.id)
    else:
        # Preencher tipo se veio da URL
        tipo_inicial = request.GET.get('tipo', 'RECEBER')
        form = TituloFinanceiroForm(initial={'tipo': tipo_inicial}, empresa=request.empresa)
    
    context = {
        'form': form,
    }
    
    return render(request, 'financeiro/criar_titulo.html', context)


@login_required
def editar_titulo(request, titulo_id):
    """Edita título financeiro existente"""
    titulo = get_object_or_404(
        TituloFinanceiro.objects.filter(empresa=request.empresa),
        pk=titulo_id
    )
    
    # Não permitir editar títulos que já possuem baixas
    if titulo.parcelas.filter(baixas__isnull=False).exists():
        messages.error(request, 'Não é possível editar títulos que já possuem baixas. Estorne as baixas primeiro.')
        return redirect('financeiro:detalhe_titulo', titulo_id=titulo.id)
    
    if request.method == 'POST':
        form = TituloFinanceiroForm(request.POST, instance=titulo, empresa=request.empresa)
        if form.is_valid():
            titulo = form.save()
            
            # Atualizar régua nas parcelas
            regua = form.cleaned_data.get('regua_cobranca')
            ativar = form.cleaned_data.get('ativar_regua', False)
            
            if titulo.tipo == 'RECEBER':
                for parcela in titulo.parcelas.all():
                    parcela.regua = regua
                    parcela.regua_ativa = ativar
                    parcela.save()
            
            # Regenerar parcelas se necessário
            if 'valor_total' in form.changed_data or 'num_parcelas' in form.changed_data or 'data_primeiro_vencimento' in form.changed_data or 'intervalo_dias' in form.changed_data:
                # Deletar parcelas antigas
                titulo.parcelas.all().delete()
                # Gerar novas parcelas
                titulo.gerar_parcelas()
                
                # Reaplicar régua nas novas parcelas
                if regua and titulo.tipo == 'RECEBER':
                    for parcela in titulo.parcelas.all():
                        parcela.regua = regua
                        parcela.regua_ativa = ativar
                        parcela.save()
                
                messages.info(request, 'As parcelas foram regeneradas devido às alterações.')
            
            messages.success(request, f'Título {titulo.numero_documento} atualizado com sucesso!')
            return redirect('financeiro:detalhe_titulo', titulo_id=titulo.id)
    else:
        form = TituloFinanceiroForm(instance=titulo, empresa=request.empresa)
    
    context = {
        'form': form,
        'titulo': titulo,
        'editando': True,
    }
    
    return render(request, 'financeiro/criar_titulo.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/financeiro/')
def detalhe_titulo(request, titulo_id):
    """Detalhes de um título com suas parcelas"""
    titulo = get_object_or_404(
        TituloFinanceiro.objects.select_related('pessoa', 'centro_custo').filter(
            empresa=request.empresa
        ),
        pk=titulo_id
    )
    
    parcelas = titulo.parcelas.prefetch_related('baixas').all()
    
    context = {
        'titulo': titulo,
        'parcelas': parcelas,
    }
    
    return render(request, 'financeiro/detalhe_titulo.html', context)


# =========================================
# PARCELAS
# =========================================

@login_required
@require_empresa
@verificar_permissao_menu('/financeiro/')
def listar_parcelas(request, tipo='RECEBER'):
    """Lista parcelas com filtros (a pagar/receber)"""
    # Tipo pode vir da URL ou do GET
    tipo = tipo or request.GET.get('tipo', 'RECEBER')
    status = request.GET.get('status', 'ABERTO')
    vencimento = request.GET.get('vencimento', 'TODOS')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    parcelas = ParcelaFinanceira.objects.select_related(
        'titulo', 'titulo__pessoa'
    ).filter(
        titulo__tipo=tipo,
        titulo__empresa=request.empresa  # Filtrar por empresa
    )
    
    # Filtro de status
    if status == 'ABERTO':
        parcelas = parcelas.filter(status__in=['ABERTO', 'PARCIAL'])
    elif status != 'TODOS':
        parcelas = parcelas.filter(status=status)
    
    # Filtro de vencimento
    hoje = date.today()
    if vencimento == 'VENCIDAS':
        parcelas = parcelas.filter(data_vencimento__lt=hoje, status__in=['ABERTO', 'PARCIAL'])
    elif vencimento == 'HOJE':
        parcelas = parcelas.filter(data_vencimento=hoje)
    elif vencimento == '7_DIAS':
        parcelas = parcelas.filter(data_vencimento__lte=hoje + timedelta(days=7), data_vencimento__gte=hoje)
    elif vencimento == '30_DIAS':
        parcelas = parcelas.filter(data_vencimento__lte=hoje + timedelta(days=30), data_vencimento__gte=hoje)
    elif vencimento == 'PERSONALIZADO':
        # Filtro por data específica
        if data_inicio:
            from datetime import datetime
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            parcelas = parcelas.filter(data_vencimento__gte=data_inicio_obj)
        if data_fim:
            from datetime import datetime
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            parcelas = parcelas.filter(data_vencimento__lte=data_fim_obj)
    
    context = {
        'parcelas': parcelas.order_by('data_vencimento'),
        'tipo': tipo,
        'status': status,
        'vencimento': vencimento,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'hoje': hoje,
    }
    
    template = 'financeiro/listar_contas_pagar.html' if tipo == 'PAGAR' else 'financeiro/listar_contas_receber.html'
    return render(request, template, context)


@login_required
def baixar_parcela(request, parcela_id):
    """Realiza baixa de parcela"""
    parcela = get_object_or_404(
        ParcelaFinanceira.objects.select_related('titulo', 'titulo__pessoa').filter(
            titulo__empresa=request.empresa
        ),
        pk=parcela_id
    )
    
    if request.method == 'POST':
        try:
            valor_principal = Decimal(request.POST.get('valor_principal'))
            
            baixa = BaixaFinanceira(
                parcela=parcela,
                data_pagamento=request.POST.get('data_pagamento'),
                conta_financeira_id=request.POST.get('conta_financeira'),
                forma_pagamento_id=request.POST.get('forma_pagamento'),
                valor_principal=valor_principal,
                juros=Decimal(request.POST.get('juros', 0)),
                multa=Decimal(request.POST.get('multa', 0)),
                desconto=Decimal(request.POST.get('desconto', 0)),
                taxas=Decimal(request.POST.get('taxas', 0)),
                observacao=request.POST.get('observacao', ''),
                criado_por=request.user
            )
            baixa.save()
            
            messages.success(request, f'Baixa realizada com sucesso! Saldo restante: R$ {parcela.saldo_aberto}')
            return redirect('financeiro:detalhe_titulo', titulo_id=parcela.titulo.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao realizar baixa: {str(e)}')
    
    # Dados para formulário
    contas = ContaFinanceira.objects.filter(ativo=True, empresa=request.empresa)
    formas = FormaPagamento.objects.filter(ativo=True, empresa=request.empresa)
    
    context = {
        'parcela': parcela,
        'contas': contas,
        'formas': formas,
        'hoje': date.today(),
    }
    
    return render(request, 'financeiro/baixar_parcela.html', context)


@login_required
def estornar_baixa(request, baixa_id):
    """Estorna uma baixa"""
    baixa = get_object_or_404(BaixaFinanceira, pk=baixa_id)
    
    if request.method == 'POST':
        try:
            motivo = request.POST.get('motivo')
            if not motivo:
                raise ValueError('Motivo do estorno é obrigatório')
            
            baixa.estornar(motivo, request.user)
            
            messages.success(request, 'Baixa estornada com sucesso!')
            return redirect('financeiro:detalhe_titulo', titulo_id=baixa.parcela.titulo.id)
        
        except Exception as e:
            messages.error(request, f'Erro ao estornar: {str(e)}')
    
    context = {
        'baixa': baixa,
    }
    
    return render(request, 'financeiro/estornar_baixa.html', context)


# =========================================
# CONTAS FINANCEIRAS
# =========================================

@login_required
def listar_contas_financeiras(request):
    """Lista contas bancárias e caixas"""
    contas = ContaFinanceira.objects.select_related('banco').filter(ativo=True, empresa=request.empresa)
    
    # Calcular totais
    total_bancos = Decimal('0')
    total_caixa = Decimal('0')
    
    for conta in contas:
        if conta.tipo == 'BANCO':
            total_bancos += conta.saldo_atual()
        else:
            total_caixa += conta.saldo_atual()
    
    total_geral = total_bancos + total_caixa
    
    context = {
        'contas': contas,
        'total_bancos': total_bancos,
        'total_caixa': total_caixa,
        'total_geral': total_geral,
    }
    
    return render(request, 'financeiro/listar_contas_financeiras.html', context)


@login_required
def criar_conta_financeira(request):
    """Criar nova conta financeira"""
    if request.method == 'POST':
        form = ContaFinanceiraForm(request.POST)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.empresa = request.empresa
            conta.criado_por = request.user
            conta.save()
            messages.success(request, f'Conta financeira "{conta.nome}" criada com sucesso!')
            return redirect('financeiro:listar_contas_financeiras')
    else:
        form = ContaFinanceiraForm()
    
    return render(request, 'financeiro/form_conta_financeira.html', {
        'form': form,
        'titulo': 'Nova Conta Financeira'
    })


@login_required
def editar_conta_financeira(request, pk):
    """Editar conta financeira"""
    conta = get_object_or_404(ContaFinanceira, pk=pk, empresa=request.empresa)
    
    if request.method == 'POST':
        form = ContaFinanceiraForm(request.POST, instance=conta)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.atualizado_por = request.user
            conta.save()
            messages.success(request, f'Conta financeira "{conta.nome}" atualizada com sucesso!')
            return redirect('financeiro:listar_contas_financeiras')
    else:
        form = ContaFinanceiraForm(instance=conta)
    
    return render(request, 'financeiro/form_conta_financeira.html', {
        'form': form,
        'titulo': 'Editar Conta Financeira',
        'conta': conta
    })


@login_required
def excluir_conta_financeira(request, pk):
    """Excluir conta financeira"""
    conta = get_object_or_404(ContaFinanceira, pk=pk, empresa=request.empresa)
    
    # Verificar se tem movimentações
    tem_movimentacoes = conta.movimentacoes.exists()
    
    if request.method == 'POST':
        if not tem_movimentacoes:
            nome = conta.nome
            conta.delete()
            messages.success(request, f'Conta "{nome}" excluída com sucesso!')
        else:
            messages.error(request, 'Não é possível excluir conta com movimentações! Desative-a em vez de excluir.')
        return redirect('financeiro:listar_contas_financeiras')
    
    return render(request, 'financeiro/confirmar_exclusao_conta_financeira.html', {
        'conta': conta,
        'tem_movimentacoes': tem_movimentacoes
    })


@login_required
def extrato_conta(request, conta_id):
    """Extrato de movimentações de uma conta"""
    conta = get_object_or_404(ContaFinanceira, pk=conta_id)
    
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo', '')
    
    movimentacoes = conta.movimentacoes.filter(estornado=False)
    
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_movimentacao__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_movimentacao__lte=data_fim)
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    
    # Calcular totais
    total_entradas = movimentacoes.filter(tipo='ENTRADA').aggregate(total=Sum('valor'))['total'] or Decimal('0')
    total_saidas = movimentacoes.filter(tipo='SAIDA').aggregate(total=Sum('valor'))['total'] or Decimal('0')
    saldo_final = total_entradas - total_saidas
    
    context = {
        'conta': conta,
        'movimentacoes': movimentacoes.order_by('data_movimentacao', 'id'),
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_final': saldo_final,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo': tipo,
    }
    
    return render(request, 'financeiro/extrato_conta.html', context)


@login_required
def extrato_conta_pdf(request, conta_id):
    """Gera PDF do extrato de uma conta financeira"""
    
    def formatar_real(valor):
        """Formata valor em formato brasileiro R$ 1.234,56"""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    conta = get_object_or_404(ContaFinanceira, pk=conta_id, empresa=request.empresa)
    
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo', '')
    
    movimentacoes = conta.movimentacoes.filter(estornado=False)
    
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_movimentacao__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_movimentacao__lte=data_fim)
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    
    movimentacoes = movimentacoes.order_by('data_movimentacao', 'id')
    
    # Calcular totais
    total_entradas = movimentacoes.filter(tipo='ENTRADA').aggregate(total=Sum('valor'))['total'] or Decimal('0')
    total_saidas = movimentacoes.filter(tipo='SAIDA').aggregate(total=Sum('valor'))['total'] or Decimal('0')
    saldo_periodo = total_entradas - total_saidas
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo customizado para título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=10,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_LEFT
    )
    
    # Cabeçalho com logo à direita
    empresa = request.empresa
    
    # Criar tabela para cabeçalho (texto à esquerda, logo à direita)
    cabecalho_data = []
    
    # Textos do lado esquerdo
    texto_esquerda = [
        Paragraph(f"<b>{empresa.nome_fantasia}</b>", titulo_style),
        Paragraph("EXTRATO BANCÁRIO", subtitulo_style)
    ]
    
    # Logo do lado direito (se existir)
    logo_direita = None
    if empresa and empresa.logo:
        try:
            import os
            if os.path.exists(empresa.logo.path):
                logo_direita = Image(empresa.logo.path, width=3*cm, height=3*cm)
        except Exception as e:
            pass
    
    if logo_direita:
        # Tabela com 2 colunas: texto | logo
        cabecalho_table = Table([[texto_esquerda, logo_direita]], colWidths=[13*cm, 5*cm])
        cabecalho_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(cabecalho_table)
    else:
        # Sem logo, apenas os textos
        for texto in texto_esquerda:
            elements.append(texto)
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Informações da conta
    info_conta = [
        [Paragraph('<b>Conta:</b>', styles['Normal']), conta.nome],
        [Paragraph('<b>Tipo:</b>', styles['Normal']), conta.get_tipo_display()],
    ]
    
    if conta.banco:
        info_conta.extend([
            [Paragraph('<b>Banco:</b>', styles['Normal']), f"{conta.banco.codigo_compe} - {conta.banco.nome}"],
            [Paragraph('<b>Agência:</b>', styles['Normal']), conta.agencia or '-'],
            [Paragraph('<b>Número:</b>', styles['Normal']), conta.conta or '-'],
        ])
    
    # Período do extrato
    if data_inicio or data_fim:
        # Converter datas para formato brasileiro DD-MM-YYYY
        data_inicio_br = data_inicio
        data_fim_br = data_fim
        
        if data_inicio:
            try:
                from datetime import datetime
                dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                data_inicio_br = dt.strftime('%d-%m-%Y')
            except:
                pass
        
        if data_fim:
            try:
                from datetime import datetime
                dt = datetime.strptime(data_fim, '%Y-%m-%d')
                data_fim_br = dt.strftime('%d-%m-%Y')
            except:
                pass
        
        periodo = f"{data_inicio_br or 'Início'} até {data_fim_br or 'Hoje'}"
        info_conta.append([Paragraph('<b>Período:</b>', styles['Normal']), periodo])
    
    # Saldo inicial
    info_conta.append([Paragraph('<b>Saldo Inicial:</b>', styles['Normal']), formatar_real(conta.saldo_inicial)])
    
    table_info = Table(info_conta, colWidths=[4*cm, 12*cm])
    table_info.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f4788')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(table_info)
    elements.append(Spacer(1, 0.7*cm))
    
    # Tabela de movimentações
    if movimentacoes.exists():
        data_movs = [['Data', 'Descrição', 'Entradas', 'Saídas', 'Saldo']]
        
        saldo_acumulado = conta.saldo_inicial
        
        for mov in movimentacoes:
            if mov.tipo == 'ENTRADA':
                entrada = formatar_real(mov.valor)
                saida = "-"
                saldo_acumulado += mov.valor
            else:
                entrada = "-"
                saida = formatar_real(mov.valor)
                saldo_acumulado -= mov.valor
            
            data_movs.append([
                mov.data_movimentacao.strftime('%d/%m/%Y'),
                Paragraph(mov.descricao[:60], styles['Normal']),
                entrada,
                saida,
                formatar_real(saldo_acumulado)
            ])
        
        table_movs = Table(data_movs, colWidths=[2.5*cm, 7.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        table_movs.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Data
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Valores
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Padding
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(table_movs)
    else:
        elements.append(Paragraph("<i>Nenhuma movimentação encontrada no período.</i>", styles['Normal']))
    
    elements.append(Spacer(1, 0.7*cm))
    
    # Totalizadores
    totais_data = [
        [Paragraph('<b>Total de Entradas:</b>', styles['Normal']), formatar_real(total_entradas)],
        [Paragraph('<b>Total de Saídas:</b>', styles['Normal']), formatar_real(total_saidas)],
        [Paragraph('<b>Saldo do Período:</b>', styles['Normal']), formatar_real(saldo_periodo)],
        [Paragraph('<b>Saldo Atual:</b>', styles['Normal']), formatar_real(conta.saldo_atual())],
    ]
    
    table_totais = Table(totais_data, colWidths=[12*cm, 6*cm])
    table_totais.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f4788')),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table_totais)
    
    # Rodapé
    elements.append(Spacer(1, 1*cm))
    rodape_style = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    from datetime import datetime
    agora = datetime.now()
    elements.append(Paragraph(f"Extrato gerado em {agora.strftime('%d/%m/%Y às %H:%M')}", rodape_style))
    
    # Gerar PDF
    doc.build(elements)
    
    # Retornar resposta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    # Nome de arquivo seguro (remove caracteres especiais)
    nome_arquivo = conta.nome.replace(' ', '_').replace('/', '_').replace('\\', '_')
    filename = f'extrato_{nome_arquivo}_{date.today().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


# =========================================
# CADASTROS AUXILIARES
# =========================================

@login_required
def listar_bancos(request):
    """Lista todos os bancos"""
    bancos = Banco.objects.all().order_by('nome')
    
    context = {
        'bancos': bancos,
    }
    
    return render(request, 'financeiro/listar_bancos.html', context)


@login_required
def criar_banco(request):
    """Cria um novo banco"""
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            banco = form.save(commit=False)
            banco.criado_por = request.user
            banco.save()
            messages.success(request, f'Banco "{banco.nome}" cadastrado com sucesso!')
            return redirect('financeiro:listar_bancos')
    else:
        form = BancoForm()
    
    context = {
        'form': form,
        'titulo': 'Novo Banco',
    }
    
    return render(request, 'financeiro/form_banco.html', context)


@login_required
def editar_banco(request, banco_id):
    """Edita um banco existente"""
    banco = get_object_or_404(Banco, pk=banco_id)
    
    if request.method == 'POST':
        form = BancoForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            messages.success(request, f'Banco "{banco.nome}" atualizado com sucesso!')
            return redirect('financeiro:listar_bancos')
    else:
        form = BancoForm(instance=banco)
    
    context = {
        'form': form,
        'banco': banco,
        'titulo': f'Editar Banco: {banco.nome}',
    }
    
    return render(request, 'financeiro/form_banco.html', context)


@login_required
def excluir_banco(request, banco_id):
    """Exclui um banco"""
    banco = get_object_or_404(Banco, pk=banco_id)
    
    if request.method == 'POST':
        nome = banco.nome
        banco.delete()
        messages.success(request, f'Banco "{nome}" excluído com sucesso!')
        return redirect('financeiro:listar_bancos')
    
    context = {
        'banco': banco,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_banco.html', context)


@login_required
def listar_centros_custo(request):
    """Lista todos os centros de custo"""
    centros = CentroCusto.objects.filter(empresa=request.empresa).select_related('projeto', 'responsavel').order_by('codigo')
    
    context = {
        'centros': centros,
    }
    
    return render(request, 'financeiro/listar_centros_custo.html', context)


@login_required
def criar_centro_custo(request):
    """Cria um novo centro de custo"""
    if request.method == 'POST':
        form = CentroCustoForm(request.POST)
        if form.is_valid():
            centro = form.save(commit=False)
            centro.empresa = request.empresa
            centro.criado_por = request.user
            centro.save()
            messages.success(request, f'Centro de Custo "{centro.nome}" cadastrado com sucesso!')
            return redirect('financeiro:listar_centros_custo')
    else:
        form = CentroCustoForm()
    
    context = {
        'form': form,
        'titulo': 'Novo Centro de Custo',
    }
    
    return render(request, 'financeiro/form_centro_custo.html', context)


@login_required
def editar_centro_custo(request, centro_id):
    """Edita um centro de custo existente"""
    centro = get_object_or_404(CentroCusto, pk=centro_id, empresa=request.empresa)
    
    if request.method == 'POST':
        form = CentroCustoForm(request.POST, instance=centro)
        if form.is_valid():
            form.save()
            messages.success(request, f'Centro de Custo "{centro.nome}" atualizado com sucesso!')
            return redirect('financeiro:listar_centros_custo')
    else:
        form = CentroCustoForm(instance=centro)
    
    context = {
        'form': form,
        'centro': centro,
        'titulo': f'Editar Centro de Custo: {centro.nome}',
    }
    
    return render(request, 'financeiro/form_centro_custo.html', context)


@login_required
def excluir_centro_custo(request, centro_id):
    """Exclui um centro de custo"""
    centro = get_object_or_404(CentroCusto, pk=centro_id, empresa=request.empresa)
    
    if request.method == 'POST':
        nome = centro.nome
        centro.delete()
        messages.success(request, f'Centro de Custo "{nome}" excluído com sucesso!')
        return redirect('financeiro:listar_centros_custo')
    
    context = {
        'centro': centro,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_centro_custo.html', context)


# =========================================
# FORMAS DE PAGAMENTO
# =========================================

@login_required
def listar_formas_pagamento(request):
    """Lista todas as formas de pagamento"""
    formas = FormaPagamento.objects.filter(empresa=request.empresa).order_by('descricao')
    
    context = {
        'formas': formas,
    }
    
    return render(request, 'financeiro/listar_formas_pagamento.html', context)


@login_required
def criar_forma_pagamento(request):
    """Cria nova forma de pagamento"""
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST)
        if form.is_valid():
            forma = form.save(commit=False)
            forma.empresa = request.empresa
            forma.criado_por = request.user
            forma.save()
            messages.success(request, 'Forma de pagamento cadastrada com sucesso!')
            return redirect('financeiro:listar_formas_pagamento')
    else:
        form = FormaPagamentoForm()
    
    context = {
        'form': form,
        'titulo': 'Nova Forma de Pagamento',
    }
    
    return render(request, 'financeiro/form_forma_pagamento.html', context)


@login_required
def editar_forma_pagamento(request, forma_id):
    """Edita forma de pagamento existente"""
    forma = get_object_or_404(FormaPagamento, pk=forma_id, empresa=request.empresa)
    
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST, instance=forma)
        if form.is_valid():
            form.save()
            messages.success(request, 'Forma de pagamento atualizada com sucesso!')
            return redirect('financeiro:listar_formas_pagamento')
    else:
        form = FormaPagamentoForm(instance=forma)
    
    context = {
        'form': form,
        'forma': forma,
        'titulo': f'Editar Forma de Pagamento: {forma.descricao}',
    }
    
    return render(request, 'financeiro/form_forma_pagamento.html', context)


@login_required
def excluir_forma_pagamento(request, forma_id):
    """Exclui uma forma de pagamento"""
    forma = get_object_or_404(FormaPagamento, pk=forma_id, empresa=request.empresa)
    
    if request.method == 'POST':
        descricao = forma.descricao
        forma.delete()
        messages.success(request, f'Forma de Pagamento "{descricao}" excluída com sucesso!')
        return redirect('financeiro:listar_formas_pagamento')
    
    context = {
        'forma': forma,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_forma_pagamento.html', context)


# =========================================
# PLANO DE CONTAS
# =========================================

@login_required
def listar_plano_contas(request):
    """Lista plano de contas hierarquicamente"""
    contas = PlanoConta.objects.filter(empresa=request.empresa).order_by('codigo')
    
    context = {
        'contas': contas,
    }
    
    return render(request, 'financeiro/listar_plano_contas.html', context)


@login_required
def criar_plano_conta(request):
    """Cria nova conta no plano de contas"""
    if request.method == 'POST':
        form = PlanoContaForm(request.POST)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.empresa = request.empresa
            conta.criado_por = request.user
            conta.save()
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('financeiro:listar_plano_contas')
    else:
        form = PlanoContaForm()
    
    context = {
        'form': form,
        'titulo': 'Nova Conta - Plano de Contas',
    }
    
    return render(request, 'financeiro/form_plano_conta.html', context)


@login_required
def editar_plano_conta(request, conta_id):
    """Edita conta existente"""
    conta = get_object_or_404(PlanoConta, pk=conta_id, empresa=request.empresa)
    
    if request.method == 'POST':
        form = PlanoContaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta atualizada com sucesso!')
            return redirect('financeiro:listar_plano_contas')
    else:
        form = PlanoContaForm(instance=conta)
    
    context = {
        'form': form,
        'conta': conta,
        'titulo': f'Editar: {conta.codigo} - {conta.nome}',
    }
    
    return render(request, 'financeiro/form_plano_conta.html', context)


@login_required
def excluir_plano_conta(request, conta_id):
    """Exclui uma conta"""
    conta = get_object_or_404(PlanoConta, pk=conta_id, empresa=request.empresa)
    
    if request.method == 'POST':
        nome = f"{conta.codigo} - {conta.nome}"
        conta.delete()
        messages.success(request, f'Conta "{nome}" excluída com sucesso!')
        return redirect('financeiro:listar_plano_contas')
    
    context = {
        'conta': conta,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_plano_conta.html', context)


# =========================================
# TRANSFERÊNCIAS ENTRE CONTAS
# =========================================

@login_required
def criar_transferencia(request):
    """Cria uma transferência entre contas"""
    from financeiro.models import TransferenciaEntreContas, MovimentacaoConta
    from django.db import transaction
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data_transferencia = request.POST.get('data_transferencia')
                conta_origem_id = request.POST.get('conta_origem')
                conta_destino_id = request.POST.get('conta_destino')
                valor = request.POST.get('valor')
                taxa = request.POST.get('taxa', '0')
                descricao = request.POST.get('descricao')
                
                # Validações
                if not all([data_transferencia, conta_origem_id, conta_destino_id, valor, descricao]):
                    messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                    return redirect('financeiro:criar_transferencia')
                
                if conta_origem_id == conta_destino_id:
                    messages.error(request, 'Conta origem e destino não podem ser iguais.')
                    return redirect('financeiro:criar_transferencia')
                
                # Buscar contas
                conta_origem = ContaFinanceira.objects.get(pk=conta_origem_id)
                conta_destino = ContaFinanceira.objects.get(pk=conta_destino_id)
                
                # Converter valores
                from decimal import Decimal
                valor_decimal = Decimal(valor.replace(',', '.'))
                taxa_decimal = Decimal(taxa.replace(',', '.')) if taxa else Decimal('0')
                
                # Criar transferência
                transferencia = TransferenciaEntreContas.objects.create(
                    data_transferencia=data_transferencia,
                    conta_origem=conta_origem,
                    conta_destino=conta_destino,
                    valor=valor_decimal,
                    taxa=taxa_decimal,
                    descricao=descricao,
                    criado_por=request.user
                )
                
                # Criar movimentação de saída
                mov_saida = MovimentacaoConta.objects.create(
                    conta_financeira=conta_origem,
                    data_movimentacao=data_transferencia,
                    tipo='DEBITO',
                    valor=valor_decimal + taxa_decimal,
                    descricao=f'Transferência para {conta_destino.nome} - {descricao}',
                    categoria='TRANSFERENCIA'
                )
                
                # Criar movimentação de entrada
                mov_entrada = MovimentacaoConta.objects.create(
                    conta_financeira=conta_destino,
                    data_movimentacao=data_transferencia,
                    tipo='CREDITO',
                    valor=valor_decimal,
                    descricao=f'Transferência de {conta_origem.nome} - {descricao}',
                    categoria='TRANSFERENCIA'
                )
                
                # Vincular movimentações à transferência
                transferencia.movimentacao_saida = mov_saida
                transferencia.movimentacao_entrada = mov_entrada
                transferencia.save()
                
                # Atualizar saldos
                conta_origem.saldo_atual -= (valor_decimal + taxa_decimal)
                conta_origem.save()
                
                conta_destino.saldo_atual += valor_decimal
                conta_destino.save()
                
                messages.success(request, f'Transferência de {valor_decimal:,.2f} realizada com sucesso!')
                return redirect('financeiro:listar_contas_financeiras')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar transferência: {str(e)}')
            return redirect('financeiro:criar_transferencia')
    
    # GET - Exibir formulário
    contas = ContaFinanceira.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'contas': contas,
        'hoje': date.today(),
    }
    
    return render(request, 'financeiro/criar_transferencia.html', context)


@login_required
def listar_transferencias(request):
    """Lista todas as transferências"""
    from financeiro.models import TransferenciaEntreContas
    
    transferencias = TransferenciaEntreContas.objects.select_related(
        'conta_origem', 'conta_destino', 'criado_por'
    ).order_by('-data_transferencia', '-id')
    
    context = {
        'transferencias': transferencias,
    }
    
    return render(request, 'financeiro/listar_transferencias.html', context)


@login_required
def estornar_transferencia(request, transferencia_id):
    """Estorna uma transferência"""
    from financeiro.models import TransferenciaEntreContas
    from django.db import transaction
    
    transferencia = get_object_or_404(TransferenciaEntreContas, pk=transferencia_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if transferencia.estornado:
                    messages.warning(request, 'Esta transferência já foi estornada.')
                    return redirect('financeiro:listar_transferencias')
                
                # Marcar como estornado
                transferencia.estornado = True
                transferencia.save()
                
                # Reverter saldos
                transferencia.conta_origem.saldo_atual += (transferencia.valor + transferencia.taxa)
                transferencia.conta_origem.save()
                
                transferencia.conta_destino.saldo_atual -= transferencia.valor
                transferencia.conta_destino.save()
                
                # Marcar movimentações como estornadas (se existirem)
                if transferencia.movimentacao_saida:
                    transferencia.movimentacao_saida.estornado = True
                    transferencia.movimentacao_saida.save()
                
                if transferencia.movimentacao_entrada:
                    transferencia.movimentacao_entrada.estornado = True
                    transferencia.movimentacao_entrada.save()
                
                messages.success(request, 'Transferência estornada com sucesso!')
                return redirect('financeiro:listar_transferencias')
                
        except Exception as e:
            messages.error(request, f'Erro ao estornar transferência: {str(e)}')
            return redirect('financeiro:listar_transferencias')
    
    context = {
        'transferencia': transferencia,
    }
    
    return render(request, 'financeiro/confirmar_estorno_transferencia.html', context)


# ============================================================================
# VIEWS - REGIME TRIBUTÁRIO
# ============================================================================

@login_required
@require_empresa
def listar_regimes_tributarios(request):
    """Lista todos os regimes tributários"""
    from .models import RegimeTributario
    
    regimes = RegimeTributario.objects.all().order_by('nome')
    
    context = {
        'current_module': 'financeiro',
        'regimes': regimes,
    }
    
    return render(request, 'financeiro/listar_regimes_tributarios.html', context)


@login_required
@require_empresa
def criar_regime_tributario(request):
    """Cria um novo regime tributário"""
    from .models import RegimeTributario
    from .forms import RegimeTributarioForm
    
    if request.method == 'POST':
        form = RegimeTributarioForm(request.POST)
        if form.is_valid():
            regime = form.save()
            messages.success(request, f'Regime Tributário "{regime.get_nome_display()}" cadastrado com sucesso!')
            return redirect('financeiro:listar_regimes_tributarios')
    else:
        form = RegimeTributarioForm()
    
    context = {
        'current_module': 'financeiro',
        'form': form,
        'titulo': 'Novo Regime Tributário',
    }
    
    return render(request, 'financeiro/form_regime_tributario.html', context)


@login_required
@require_empresa
def editar_regime_tributario(request, regime_id):
    """Edita um regime tributário existente"""
    from .models import RegimeTributario
    from .forms import RegimeTributarioForm
    
    regime = get_object_or_404(RegimeTributario, pk=regime_id)
    
    if request.method == 'POST':
        form = RegimeTributarioForm(request.POST, instance=regime)
        if form.is_valid():
            form.save()
            messages.success(request, f'Regime Tributário "{regime.get_nome_display()}" atualizado com sucesso!')
            return redirect('financeiro:listar_regimes_tributarios')
    else:
        form = RegimeTributarioForm(instance=regime)
    
    context = {
        'current_module': 'financeiro',
        'form': form,
        'titulo': 'Editar Regime Tributário',
        'regime': regime,
    }
    
    return render(request, 'financeiro/form_regime_tributario.html', context)


@login_required
@require_empresa
def excluir_regime_tributario(request, regime_id):
    """Exclui um regime tributário"""
    from .models import RegimeTributario
    
    regime = get_object_or_404(RegimeTributario, pk=regime_id)
    
    if request.method == 'POST':
        nome = regime.get_nome_display()
        regime.delete()
        messages.success(request, f'Regime Tributário "{nome}" excluído com sucesso!')
        return redirect('financeiro:listar_regimes_tributarios')
    
    context = {
        'current_module': 'financeiro',
        'regime': regime,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_regime.html', context)


# ============================================================================
# VIEWS - CATEGORIAS DE CUSTO
# ============================================================================

@login_required
@require_empresa
def listar_categorias_custo(request):
    """Lista todas as categorias de custo"""
    from .models import CategoriaCustoVariabilidade
    
    categorias = CategoriaCustoVariabilidade.objects.filter(
        empresa=request.empresa
    ).order_by('tipo', 'nome')
    
    context = {
        'current_module': 'financeiro',
        'categorias': categorias,
    }
    
    return render(request, 'financeiro/listar_categorias_custo.html', context)


@login_required
@require_empresa
def criar_categoria_custo(request):
    """Cria uma nova categoria de custo"""
    from .models import CategoriaCustoVariabilidade
    from .forms import CategoriaCustoForm
    
    if request.method == 'POST':
        form = CategoriaCustoForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" cadastrada com sucesso!')
            return redirect('financeiro:listar_categorias_custo')
    else:
        form = CategoriaCustoForm(empresa=request.empresa)
    
    context = {
        'current_module': 'financeiro',
        'form': form,
        'titulo': 'Nova Categoria de Custo',
    }
    
    return render(request, 'financeiro/form_categoria_custo.html', context)


@login_required
@require_empresa
def editar_categoria_custo(request, categoria_id):
    """Edita uma categoria de custo existente"""
    from .models import CategoriaCustoVariabilidade
    from .forms import CategoriaCustoForm
    
    categoria = get_object_or_404(CategoriaCustoVariabilidade, pk=categoria_id, empresa=request.empresa)
    
    if request.method == 'POST':
        form = CategoriaCustoForm(request.POST, instance=categoria, empresa=request.empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect('financeiro:listar_categorias_custo')
    else:
        form = CategoriaCustoForm(instance=categoria, empresa=request.empresa)
    
    context = {
        'current_module': 'financeiro',
        'form': form,
        'titulo': 'Editar Categoria de Custo',
        'categoria': categoria,
    }
    
    return render(request, 'financeiro/form_categoria_custo.html', context)


@login_required
@require_empresa
def excluir_categoria_custo(request, categoria_id):
    """Exclui uma categoria de custo"""
    from .models import CategoriaCustoVariabilidade
    
    categoria = get_object_or_404(CategoriaCustoVariabilidade, pk=categoria_id, empresa=request.empresa)
    
    if request.method == 'POST':
        nome = categoria.nome
        categoria.delete()
        messages.success(request, f'Categoria "{nome}" excluída com sucesso!')
        return redirect('financeiro:listar_categorias_custo')
    
    context = {
        'current_module': 'financeiro',
        'categoria': categoria,
    }
    
    return render(request, 'financeiro/confirmar_exclusao_categoria.html', context)
