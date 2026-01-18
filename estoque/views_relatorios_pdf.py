from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
from .models import MovimentoEstoque
from projetos.models import Projeto
from django.db.models import Sum, Count


@login_required
def relatorio_consolidado_pdf(request):
    """Gera PDF do relatório consolidado de custos por obra"""
    projeto_id = request.GET.get('projeto')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Converter 'None' string para None real
    if projeto_id == 'None' or not projeto_id:
        projeto_id = None
    if data_inicio == 'None' or not data_inicio:
        data_inicio = None
    if data_fim == 'None' or not data_fim:
        data_fim = None
    
    # Busca movimentações filtradas
    movimentacoes = MovimentoEstoque.objects.select_related('item', 'projeto').filter(
        tipo_movimento='SAIDA',
        projeto__isnull=False
    )
    
    projeto_selecionado = None
    if projeto_id:
        movimentacoes = movimentacoes.filter(projeto_id=projeto_id)
        projeto_selecionado = Projeto.objects.get(id=projeto_id)
    
    if data_inicio:
        from datetime import datetime as dt
        data_inicio_dt = dt.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__gte=data_inicio_dt)
    
    if data_fim:
        from datetime import datetime as dt
        data_fim_dt = dt.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__lte=data_fim_dt)
    
    # Agrupa por projeto e item
    relatorio = movimentacoes.values(
        'projeto__id',
        'projeto__codigo',
        'projeto__descricao',
        'projeto__cliente__nome',
        'item__codigo',
        'item__descricao',
        'item__unidade_medida'
    ).annotate(
        total_movimentacoes=Count('id'),
        quantidade_total=Sum('quantidade'),
        custo_total=Sum('custo_total')
    ).order_by('projeto__codigo', 'item__descricao')
    
    # Total geral
    totais = {
        'quantidade_total': sum(r['quantidade_total'] for r in relatorio),
        'custo_total': sum(r['custo_total'] for r in relatorio),
    }
    
    # Cria a resposta HTTP com tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_custos_obra_{datetime.now().strftime("%d%m%Y_%H%M")}.pdf"'
    
    # Cria o documento PDF em orientação horizontal
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                           topMargin=1*cm, bottomMargin=1*cm,
                           leftMargin=0*cm, rightMargin=0*cm)
    
    # Container para elementos do PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulo
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#555555'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Logo e cabeçalho da empresa
    empresa_id = request.session.get('empresa_id')
    
    # Tentar buscar logo da empresa
    logo_path = None
    if empresa_id:
        from usuarios.models import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            if empresa.logo:
                import os
                from django.conf import settings
                logo_path = os.path.join(settings.MEDIA_ROOT, str(empresa.logo))
                if not os.path.exists(logo_path):
                    logo_path = None
        except Empresa.DoesNotExist:
            pass
    
    # Cabeçalho com logo centralizado
    if logo_path:
        from reportlab.platypus import Image as RLImage
        try:
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            logo_table = Table([[logo]], colWidths=[28*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.3*cm))
        except:
            pass
    
    # Título do relatório centralizado
    elements.append(Paragraph("<b>RELATÓRIO CONSOLIDADO DE CUSTOS POR OBRA</b>", title_style))
    
    # Informações do filtro
    filtro_info = []
    if projeto_selecionado:
        filtro_info.append(f"Projeto: {projeto_selecionado.codigo} - {projeto_selecionado.descricao}")
    if data_inicio:
        filtro_info.append(f"Período: {data_inicio_dt.strftime('%d/%m/%Y')}")
    if data_fim:
        filtro_info.append(f" até {data_fim_dt.strftime('%d/%m/%Y')}")
    
    if filtro_info:
        elements.append(Paragraph(" | ".join(filtro_info), subtitle_style))
    
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Resumo em cards
    resumo_data = [
        ['Total de Itens', 'Quantidade Total', 'Custo Total'],
        [str(len(relatorio)), f"{totais['quantidade_total']:.2f}", f"R$ {totais['custo_total']:,.2f}"]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[5.67*cm, 5.67*cm, 5.67*cm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#95a5a6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#7f8c8d')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ecf0f1')),
    ]))
    
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # Tabela de dados
    if relatorio:
        # Cabeçalho da tabela
        data = [['Cód. Obra', 'Obra/Projeto', 'Cliente', 'Cód. Material', 'Material', 'Un.', 'Qtd.', 'Custo Total']]
        
        # Dados
        for item in relatorio:
            data.append([
                item['projeto__codigo'],
                item['projeto__descricao'][:25] + '...' if len(item['projeto__descricao']) > 25 else item['projeto__descricao'],
                item.get('projeto__cliente__nome', '')[:20],
                item.get('item__codigo', '')[:15],
                item['item__descricao'][:25] + '...' if len(item['item__descricao']) > 25 else item['item__descricao'],
                item['item__unidade_medida'],
                f"{item['quantidade_total']:.2f}",
                f"R$ {item['custo_total']:,.2f}"
            ])
        
        # Linha de total
        data.append([
            '', '', '', '', 'TOTAL GERAL', '',
            f"{totais['quantidade_total']:.2f}",
            f"R$ {totais['custo_total']:,.2f}"
        ])
        
        # Cria tabela com larguras otimizadas para landscape (8 colunas)
        table = Table(data, colWidths=[3.5*cm, 5.5*cm, 3*cm, 2.5*cm, 4.5*cm, 1.5*cm, 2*cm, 3.5*cm])
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Dados - linhas menores
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),
            ('ALIGN', (1, 1), (4, -2), 'LEFT'),
            ('ALIGN', (5, 1), (5, -2), 'CENTER'),
            ('ALIGN', (6, 1), (7, -2), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -2), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 4),
            ('LEFTPADDING', (0, 1), (-1, -2), 5),
            ('RIGHTPADDING', (0, 1), (-1, -2), 5),
            
            # Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#cbd5e0')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('ALIGN', (0, -1), (4, -1), 'CENTER'),
            ('ALIGN', (6, -1), (7, -1), 'RIGHT'),
            ('TOPPADDING', (0, -1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            
            # Grade e Zebrado
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(table)
    else:
        elements.append(Paragraph("Nenhum dado encontrado para os filtros selecionados.", subtitle_style))
    
    # Rodapé
    elements.append(Spacer(1, 1*cm))
    rodape_style = ParagraphStyle(
        'RodapeStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    elements.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {request.user.get_full_name() or request.user.username}",
        rodape_style
    ))
    
    # Gera o PDF
    doc.build(elements)
    
    return response


@login_required
def relatorio_analitico_pdf(request):
    """Gera PDF do relatório analítico de materiais por obra"""
    projeto_id = request.GET.get('projeto')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Converter 'None' string para None real
    if projeto_id == 'None' or not projeto_id:
        projeto_id = None
    if data_inicio == 'None' or not data_inicio:
        data_inicio = None
    if data_fim == 'None' or not data_fim:
        data_fim = None
    
    projeto_selecionado = None
    
    # Busca movimentações filtradas
    movimentacoes = MovimentoEstoque.objects.select_related(
        'item', 'projeto', 'criado_por', 'solicitante_material', 'liberado_por'
    ).filter(
        tipo_movimento='SAIDA',
        projeto__isnull=False
    ).order_by('projeto__codigo', '-data_movimento')
    
    if projeto_id:
        movimentacoes = movimentacoes.filter(projeto_id=projeto_id)
        projeto_selecionado = Projeto.objects.get(id=projeto_id)
    
    if data_inicio:
        from datetime import datetime as dt
        data_inicio_dt = dt.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__gte=data_inicio_dt)
    
    if data_fim:
        from datetime import datetime as dt
        data_fim_dt = dt.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__lte=data_fim_dt)
    
    # Agrupa movimentações por projeto
    from collections import defaultdict
    movimentacoes_por_projeto = defaultdict(list)
    totais_por_projeto = defaultdict(lambda: {'quantidade': 0, 'custo': 0, 'itens': 0})
    projeto_clientes = {}  # Armazena cliente por projeto
    
    for mov in movimentacoes:
        projeto_key = f"{mov.projeto.codigo} - {mov.projeto.descricao}"
        movimentacoes_por_projeto[projeto_key].append(mov)
        totais_por_projeto[projeto_key]['quantidade'] += mov.quantidade
        totais_por_projeto[projeto_key]['custo'] += mov.custo_total
        totais_por_projeto[projeto_key]['itens'] += 1
        if mov.projeto and mov.projeto.cliente:
            projeto_clientes[projeto_key] = mov.projeto.cliente.nome
    
    # Total geral
    total_geral = {
        'itens': sum(t['itens'] for t in totais_por_projeto.values()),
        'quantidade': sum(t['quantidade'] for t in totais_por_projeto.values()),
        'custo': sum(t['custo'] for t in totais_por_projeto.values()),
    }
    
    # Cria a resposta HTTP com tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_analitico_obra_{datetime.now().strftime("%d%m%Y_%H%M")}.pdf"'
    
    # Cria o documento PDF em orientação horizontal
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                           topMargin=1*cm, bottomMargin=1*cm,
                           leftMargin=0*cm, rightMargin=0*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    empresa_id = request.session.get('empresa_id')
    
    # Tentar buscar logo da empresa
    logo_path = None
    if empresa_id:
        from usuarios.models import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            if empresa.logo:
                import os
                from django.conf import settings
                logo_path = os.path.join(settings.MEDIA_ROOT, str(empresa.logo))
                if not os.path.exists(logo_path):
                    logo_path = None
        except Empresa.DoesNotExist:
            pass
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1a1a1a'), spaceAfter=8,
                                 alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.HexColor('#555555'), spaceAfter=15,
                                   alignment=TA_CENTER, fontName='Helvetica')
    
    # Cabeçalho com logo centralizado
    if logo_path:
        from reportlab.platypus import Image as RLImage
        try:
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            logo_table = Table([[logo]], colWidths=[28*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.3*cm))
        except:
            pass
    
    # Título do relatório centralizado
    elements.append(Paragraph("<b>RELATÓRIO ANALÍTICO - MATERIAIS POR OBRA</b>", title_style))
    
    # Informações do filtro
    filtro_info = []
    if projeto_selecionado:
        filtro_info.append(f"Projeto: {projeto_selecionado.codigo} - {projeto_selecionado.descricao}")
    if data_inicio:
        filtro_info.append(f"Período: {data_inicio_dt.strftime('%d/%m/%Y')}")
    if data_fim:
        filtro_info.append(f" até {data_fim_dt.strftime('%d/%m/%Y')}")
    
    if filtro_info:
        elements.append(Paragraph(" | ".join(filtro_info), subtitle_style))
    
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Detalhamento por projeto
    for projeto_nome, movs in movimentacoes_por_projeto.items():
        # Título do projeto com cliente
        projeto_title_style = ParagraphStyle('ProjetoTitle', parent=styles['Heading2'],
                                            fontSize=12, textColor=colors.HexColor('#7f8c8d'),
                                            spaceAfter=8, fontName='Helvetica-Bold')
        cliente_info = f" - Cliente: {projeto_clientes.get(projeto_nome, '')}" if projeto_clientes.get(projeto_nome) else ""
        elements.append(Paragraph(f"{projeto_nome}{cliente_info}", projeto_title_style))
        
        # Tabela de movimentações com larguras otimizadas para landscape
        data = [['Data', 'Doc.', 'Item', 'Qtd.', 'Vlr. Unit.', 'Total']]
        
        for mov in movs:
            data.append([
                mov.data_movimento.strftime('%d/%m/%y'),
                mov.documento[:12],
                mov.item.descricao[:50] + '...' if len(mov.item.descricao) > 50 else mov.item.descricao,
                f"{mov.quantidade:.2f}",
                f"R$ {mov.custo_unitario:.2f}",
                f"R$ {mov.custo_total:.2f}"
            ])
        
        # Subtotal
        totais = totais_por_projeto[projeto_nome]
        data.append([
            '', '', 'SUBTOTAL', 
            f"{totais['quantidade']:.2f}", 
            '', 
            f"R$ {totais['custo']:.2f}"
        ])
        
        table = Table(data, colWidths=[2.5*cm, 3*cm, 10*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            
            # Dados - linhas menores
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (0, 1), (2, -2), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -2), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 3),
            ('LEFTPADDING', (0, 1), (-1, -2), 4),
            ('RIGHTPADDING', (0, 1), (-1, -2), 4),
            
            # Subtotal
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('TOPPADDING', (0, -1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 5),
            
            # Grade e Zebrado
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Total Geral
    elements.append(Spacer(1, 0.5*cm))
    total_data = [
        ['TOTAL GERAL', '', '', ''],
        ['Movimentações', 'Quantidade Total', 'Obras', 'Custo Total'],
        [str(total_geral['itens']), f"{total_geral['quantidade']:.2f}", 
         str(len(movimentacoes_por_projeto)), f"R$ {total_geral['custo']:,.2f}"]
    ]
    
    total_table = Table(total_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#95a5a6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#bdc3c7')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#7f8c8d')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(total_table)
    
    # Rodapé
    elements.append(Spacer(1, 0.8*cm))
    rodape_style = ParagraphStyle('RodapeStyle', parent=styles['Normal'], fontSize=7,
                                  textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    elements.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {request.user.get_full_name() or request.user.username}",
        rodape_style
    ))
    
    doc.build(elements)
    return response


@login_required
def relatorio_estoque_atual_pdf(request):
    """Gera PDF do relatório de estoque atual"""
    # Filtros
    tipo_item = request.GET.get('tipo_item')
    estoque_baixo = request.GET.get('estoque_baixo')
    
    # Converter 'None' string para None real
    if tipo_item == 'None' or not tipo_item:
        tipo_item = None
    if estoque_baixo == 'None' or not estoque_baixo:
        estoque_baixo = None
    
    # Aplicar filtros
    from .models import Item
    itens = Item.objects.filter(ativo=True).order_by('descricao')
    
    if tipo_item:
        itens = itens.filter(tipo_item=tipo_item)
    
    # Filtro de estoque baixo
    if estoque_baixo == 'sim':
        itens_filtrados = []
        for item in itens:
            if item.get_saldo_total() <= item.estoque_minimo:
                itens_filtrados.append(item)
        itens = itens_filtrados
    else:
        itens = list(itens)
    
    # Cria a resposta HTTP com tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="estoque_atual_{datetime.now().strftime("%d%m%Y_%H%M")}.pdf"'
    
    # Cria o documento PDF em orientação horizontal
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                           topMargin=1*cm, bottomMargin=1*cm,
                           leftMargin=0*cm, rightMargin=0*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    empresa_id = request.session.get('empresa_id')
    
    # Tentar buscar logo da empresa
    logo_path = None
    if empresa_id:
        from usuarios.models import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            if empresa.logo:
                import os
                from django.conf import settings
                logo_path = os.path.join(settings.MEDIA_ROOT, str(empresa.logo))
                if not os.path.exists(logo_path):
                    logo_path = None
        except Empresa.DoesNotExist:
            pass
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1a1a1a'), spaceAfter=8,
                                 alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.HexColor('#555555'), spaceAfter=15,
                                   alignment=TA_CENTER, fontName='Helvetica')
    
    # Cabeçalho com logo centralizado
    if logo_path:
        from reportlab.platypus import Image as RLImage
        try:
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            logo_table = Table([[logo]], colWidths=[28*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.3*cm))
        except:
            pass
    
    # Título do relatório
    titulo = "RELATÓRIO DE ESTOQUE ATUAL"
    if estoque_baixo == 'sim':
        titulo = "RELATÓRIO DE ESTOQUE ATUAL - ITENS COM ESTOQUE BAIXO"
    elements.append(Paragraph(f"<b>{titulo}</b>", title_style))
    
    # Informações do filtro
    filtro_info = []
    if tipo_item:
        tipo_nome = "Matéria Prima" if tipo_item == 'MP' else "Produto Acabado"
        filtro_info.append(f"Tipo: {tipo_nome}")
    
    if filtro_info:
        elements.append(Paragraph(" | ".join(filtro_info), subtitle_style))
    
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabela de dados
    if itens:
        # Cabeçalho da tabela
        data = [['Descrição', 'Tipo', 'Un.', 'Estoque Atual', 'Est. Mín.', 'Status', 'Custo Médio', 'Valor Total']]
        
        # Dados
        total_valor = 0
        for item in itens:
            estoque_atual = item.get_saldo_total()
            custo_medio = item.get_custo_medio_ponderado()
            valor_total_item = estoque_atual * custo_medio
            total_valor += valor_total_item
            
            tipo_display = "Matéria Prima" if item.tipo_item == 'MP' else "Produto Acabado"
            
            # Status
            if estoque_atual <= item.estoque_minimo:
                status_display = "Estoque Baixo"
            elif estoque_atual == 0:
                status_display = "Esgotado"
            else:
                status_display = "Normal"
            
            data.append([
                item.descricao[:35] + '...' if len(item.descricao) > 35 else item.descricao,
                tipo_display[:12],
                item.unidade_medida or "-",
                f"{estoque_atual:.3f}",
                f"{item.estoque_minimo:.3f}",
                status_display,
                f"R$ {custo_medio:.4f}",
                f"R$ {valor_total_item:,.2f}"
            ])
        
        # Linha de total
        data.append([
            '', '', '', '', '', '', 'TOTAL',
            f"R$ {total_valor:,.2f}"
        ])
        
        # Cria tabela
        table = Table(data, colWidths=[7*cm, 3*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            ('ALIGN', (1, 1), (2, -2), 'CENTER'),
            ('ALIGN', (3, 1), (7, -2), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -2), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 3),
            ('LEFTPADDING', (0, 1), (-1, -2), 4),
            ('RIGHTPADDING', (0, 1), (-1, -2), 4),
            
            # Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#cbd5e0')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('ALIGN', (0, -1), (6, -1), 'CENTER'),
            ('ALIGN', (7, -1), (7, -1), 'RIGHT'),
            ('TOPPADDING', (0, -1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            
            # Grade e Zebrado
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(table)
        
        # Resumo
        elements.append(Spacer(1, 0.5*cm))
        resumo_data = [
            ['Total de Itens', 'Valor Total do Estoque'],
            [str(len(itens)), f"R$ {total_valor:,.2f}"]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[8*cm, 8*cm])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f7fafc')),
        ]))
        
        elements.append(resumo_table)
    else:
        elements.append(Paragraph("Nenhum item encontrado para os filtros selecionados.", subtitle_style))
    
    # Rodapé
    elements.append(Spacer(1, 0.5*cm))
    rodape_style = ParagraphStyle(
        'RodapeStyle2',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    elements.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {request.user.get_full_name() or request.user.username}",
        rodape_style
    ))
    
    # Gera o PDF
    doc.build(elements)
    
    return response


@login_required
def listar_itens_pdf(request):
    """Gera PDF da listagem de itens do estoque"""
    # Filtros
    tipo_item = request.GET.get('tipo_item')
    material = request.GET.get('material')
    status = request.GET.get('status')
    estoque_baixo = request.GET.get('estoque_baixo')
    busca = request.GET.get('busca')
    
    # Converter 'None' string para None real
    if tipo_item == 'None' or not tipo_item:
        tipo_item = None
    if material == 'None' or not material:
        material = None
    if status == 'None' or not status:
        status = None
    if estoque_baixo == 'None' or not estoque_baixo:
        estoque_baixo = None
    if busca == 'None' or not busca:
        busca = None
    
    # Aplicar filtros
    from .models import Item
    itens = Item.objects.all().order_by('descricao')
    
    if tipo_item:
        itens = itens.filter(tipo_item=tipo_item)
    
    if material:
        itens = itens.filter(material=material)
    
    if status == 'ativo':
        itens = itens.filter(ativo=True)
    elif status == 'inativo':
        itens = itens.filter(ativo=False)
    
    if busca:
        itens = itens.filter(descricao__icontains=busca)
    
    # Filtro de estoque baixo
    if estoque_baixo == 'sim':
        itens_filtrados = []
        for item in itens:
            if item.get_saldo_total() <= item.estoque_minimo:
                itens_filtrados.append(item)
        itens = itens_filtrados
    else:
        itens = list(itens)
    
    # Cria a resposta HTTP com tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_itens_{datetime.now().strftime("%d%m%Y_%H%M")}.pdf"'
    
    # Cria o documento PDF em orientação horizontal
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                           topMargin=1*cm, bottomMargin=1*cm,
                           leftMargin=0*cm, rightMargin=0*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    empresa_id = request.session.get('empresa_id')
    
    # Tentar buscar logo da empresa
    logo_path = None
    if empresa_id:
        from usuarios.models import Empresa
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            if empresa.logo:
                import os
                from django.conf import settings
                logo_path = os.path.join(settings.MEDIA_ROOT, str(empresa.logo))
                if not os.path.exists(logo_path):
                    logo_path = None
        except Empresa.DoesNotExist:
            pass
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1a1a1a'), spaceAfter=8,
                                 alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.HexColor('#555555'), spaceAfter=15,
                                   alignment=TA_CENTER, fontName='Helvetica')
    
    # Cabeçalho com logo centralizado
    if logo_path:
        from reportlab.platypus import Image as RLImage
        try:
            logo = RLImage(logo_path, width=3*cm, height=3*cm, kind='proportional')
            logo_table = Table([[logo]], colWidths=[28*cm])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ]))
            elements.append(logo_table)
            elements.append(Spacer(1, 0.3*cm))
        except:
            pass
    
    # Título do relatório
    titulo = "RELATÓRIO DE ITENS DO ESTOQUE"
    if estoque_baixo == 'sim':
        titulo = "RELATÓRIO DE ITENS COM ESTOQUE BAIXO"
    elements.append(Paragraph(f"<b>{titulo}</b>", title_style))
    
    # Informações do filtro
    filtro_info = []
    if tipo_item:
        tipo_nome = "Matéria Prima" if tipo_item == 'MP' else "Produto Acabado"
        filtro_info.append(f"Tipo: {tipo_nome}")
    if material:
        filtro_info.append(f"Material: {material}")
    if status:
        filtro_info.append(f"Status: {status.capitalize()}")
    if busca:
        filtro_info.append(f"Busca: {busca}")
    
    if filtro_info:
        elements.append(Paragraph(" | ".join(filtro_info), subtitle_style))
    
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabela de dados
    if itens:
        # Cabeçalho da tabela
        data = [['Foto', 'Cód.', 'Descrição', 'Material', 'Tipo', 'Un.', 'Estoque Atual', 'Est. Mín.', 'Custo Médio', 'Valor Total', 'Status']]
        
        # Dados
        total_valor = 0
        for item in itens:
            estoque_atual = item.get_saldo_total()
            custo_medio = item.get_custo_medio_ponderado()
            valor_total_item = estoque_atual * custo_medio
            total_valor += valor_total_item
            
            tipo_display = "MP" if item.tipo_item == 'MP' else "PA"
            material_display = item.get_material_display() if item.material else "-"
            status_display = "Ativo" if item.ativo else "Inativo"
            
            # Tentar carregar a foto do item
            foto_cell = ""
            if item.foto:
                import os
                from django.conf import settings
                foto_path = os.path.join(settings.MEDIA_ROOT, str(item.foto))
                if os.path.exists(foto_path):
                    try:
                        from reportlab.platypus import Image as RLImage
                        foto_img = RLImage(foto_path, width=1.2*cm, height=1.2*cm, kind='proportional')
                        foto_cell = foto_img
                    except:
                        foto_cell = "-"
                else:
                    foto_cell = "-"
            else:
                foto_cell = "-"
            
            data.append([
                foto_cell,
                item.codigo[:8] if item.codigo else "-",
                item.descricao[:25] + '...' if len(item.descricao) > 25 else item.descricao,
                material_display[:8],
                tipo_display,
                item.unidade_medida or "-",
                f"{estoque_atual:.2f}",
                f"{item.estoque_minimo:.2f}",
                f"R$ {custo_medio:.2f}",
                f"R$ {valor_total_item:,.2f}",
                status_display
            ])
        
        # Linha de total
        data.append([
            '', '', '', '', '', '', '', 'TOTAL GERAL', '',
            f"R$ {total_valor:,.2f}",
            ''
        ])
        
        # Cria tabela
        table = Table(data, colWidths=[1.5*cm, 1.5*cm, 4.5*cm, 1.5*cm, 1*cm, 1*cm, 2*cm, 2*cm, 2.5*cm, 2.8*cm, 1.5*cm])
        table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Dados - linhas menores
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),
            ('ALIGN', (1, 1), (1, -2), 'CENTER'),
            ('ALIGN', (2, 1), (4, -2), 'LEFT'),
            ('ALIGN', (5, 1), (5, -2), 'CENTER'),
            ('ALIGN', (6, 1), (9, -2), 'RIGHT'),
            ('ALIGN', (10, 1), (10, -2), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, -2), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 3),
            ('LEFTPADDING', (0, 1), (-1, -2), 4),
            ('RIGHTPADDING', (0, 1), (-1, -2), 4),
            ('VALIGN', (0, 1), (-1, -2), 'MIDDLE'),
            
            # Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#cbd5e0')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            ('ALIGN', (0, -1), (7, -1), 'CENTER'),
            ('ALIGN', (9, -1), (9, -1), 'RIGHT'),
            ('TOPPADDING', (0, -1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            
            # Grade e Zebrado
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(table)
        
        # Resumo
        elements.append(Spacer(1, 0.5*cm))
        resumo_data = [
            ['Total de Itens', 'Valor Total do Estoque'],
            [str(len(itens)), f"R$ {total_valor:,.2f}"]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[8*cm, 8*cm])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f7fafc')),
        ]))
        
        elements.append(resumo_table)
    else:
        elements.append(Paragraph("Nenhum item encontrado para os filtros selecionados.", subtitle_style))
    
    # Rodapé
    elements.append(Spacer(1, 0.5*cm))
    rodape_style = ParagraphStyle(
        'RodapeStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    elements.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {request.user.get_full_name() or request.user.username}",
        rodape_style
    ))
    
    # Gera o PDF
    doc.build(elements)
    
    return response
