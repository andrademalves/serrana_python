from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os
from .models import MovimentoEstoque


@login_required
def gerar_documento_retirada_pdf(request, pk):
    """
    Gera PDF do documento de retirada de material para assinatura
    """
    movimentacao = get_object_or_404(MovimentoEstoque, pk=pk)
    
    # Cria a resposta HTTP com tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="retirada_material_{movimentacao.id}.pdf"'
    
    # Cria o documento PDF
    doc = SimpleDocTemplate(response, pagesize=A4, 
                           topMargin=1.5*cm, bottomMargin=2*cm,
                           leftMargin=2*cm, rightMargin=2*cm)
    
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
        spaceAfter=30,
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
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica'
    )
    
    # Título do documento
    elements.append(Paragraph("DOCUMENTO DE RETIRADA DE MATERIAL", title_style))
    elements.append(Paragraph(f"Documento Nº {movimentacao.id:06d}", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informações do documento
    data_formatada = movimentacao.data_movimento.strftime('%d/%m/%Y %H:%M')
    
    info_data = [
        ['Data/Hora:', data_formatada],
        ['Tipo de Movimento:', movimentacao.get_tipo_movimento_display()],
        ['Documento Ref.:', movimentacao.documento or '-'],
    ]
    
    if movimentacao.projeto:
        info_data.append(['Projeto:', f"{movimentacao.projeto.codigo} - {movimentacao.projeto.descricao}"])
    
    info_table = Table(info_data, colWidths=[4*cm, 13*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # Detalhes do Material
    elements.append(Paragraph("<b>MATERIAL RETIRADO</b>", normal_style))
    elements.append(Spacer(1, 0.3*cm))
    
    material_data = [
        ['Código', 'Descrição', 'Quantidade', 'Unidade', 'Valor Unit.', 'Valor Total'],
        [
            movimentacao.item.codigo or '-',
            movimentacao.item.descricao,
            f"{movimentacao.quantidade:.2f}",
            movimentacao.item.unidade_medida,
            f"R$ {movimentacao.custo_unitario:.2f}",
            f"R$ {movimentacao.custo_total:.2f}"
        ]
    ]
    
    material_table = Table(material_data, colWidths=[2.5*cm, 6*cm, 2*cm, 2*cm, 2.5*cm, 2*cm])
    material_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    elements.append(material_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Local de origem/destino
    if movimentacao.local_origem:
        elements.append(Paragraph(f"<b>Local de Origem:</b> {movimentacao.local_origem.descricao}", normal_style))
    
    if movimentacao.local_destino:
        elements.append(Paragraph(f"<b>Local de Destino:</b> {movimentacao.local_destino.descricao}", normal_style))
    
    if movimentacao.destino:
        elements.append(Paragraph(f"<b>Destino:</b> {movimentacao.destino.descricao}", normal_style))
    
    if movimentacao.observacao:
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"<b>Observações:</b> {movimentacao.observacao}", normal_style))
    
    elements.append(Spacer(1, 1*cm))
    
    # Seção de Autorização e Assinaturas
    elements.append(Paragraph("<b>AUTORIZAÇÃO E RESPONSABILIDADE</b>", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informações de quem solicitou e liberou
    autorizacao_data = []
    
    if movimentacao.solicitante_material:
        autorizacao_data.append(['Solicitado por:', movimentacao.solicitante_material.nome])
    
    if movimentacao.liberado_por:
        nome_liberador = movimentacao.liberado_por.get_full_name() or movimentacao.liberado_por.username
        autorizacao_data.append(['Liberado por:', nome_liberador])
    
    if autorizacao_data:
        autorizacao_table = Table(autorizacao_data, colWidths=[4*cm, 13*cm])
        autorizacao_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(autorizacao_table)
        elements.append(Spacer(1, 1*cm))
    
    # Seção de assinaturas
    assinatura_style = ParagraphStyle(
        'AssinaturaStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    elements.append(Spacer(1, 1.5*cm))
    
    # Tabela de assinaturas
    assinatura_data = [
        ['_'*40, '_'*40],
        ['QUEM RETIROU', 'QUEM AUTORIZOU'],
        ['', ''],
        [f"Nome: {movimentacao.solicitante_material.nome if movimentacao.solicitante_material else '_'*30}", 
         f"Nome: {movimentacao.liberado_por.get_full_name() if movimentacao.liberado_por else '_'*30}"],
        [f"Data: {datetime.now().strftime('%d/%m/%Y')}", f"Data: {datetime.now().strftime('%d/%m/%Y')}"]
    ]
    
    assinatura_table = Table(assinatura_data, colWidths=[8.5*cm, 8.5*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('FONTSIZE', (0, 2), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(assinatura_table)
    
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
        f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} por {request.user.get_full_name() or request.user.username}", 
        rodape_style
    ))
    
    # Gera o PDF
    doc.build(elements)
    
    return response
