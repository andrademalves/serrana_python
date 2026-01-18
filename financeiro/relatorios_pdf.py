"""
Geração de PDFs dos Relatórios Financeiros
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date, datetime
from decimal import Decimal
import io
import calendar

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

from .models import ParcelaFinanceira, BaixaFinanceira, CentroCusto
from .services.calculadora import CalculadoraSaldos, ProjecaoFluxoCaixa
from .services.ponto_equilibrio import AnalisePontoEquilibrio

# Nomes dos meses em português
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}


def formatar_real(valor):
    """Formata valor em formato brasileiro R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def criar_cabecalho_pdf(elements, styles, empresa, titulo_relatorio):
    """Cria cabeçalho padrão para todos os PDFs"""
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
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # Textos do lado esquerdo
    texto_esquerda = [
        Paragraph(f"<b>{empresa.nome_fantasia}</b>", titulo_style),
        Paragraph(titulo_relatorio, subtitulo_style)
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
        cabecalho_table = Table([[texto_esquerda, logo_direita]], colWidths=[13*cm, 5*cm])
        cabecalho_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(cabecalho_table)
    else:
        for texto in texto_esquerda:
            elements.append(texto)
    
    elements.append(Spacer(1, 0.5*cm))


@login_required
def relatorio_dre_pdf(request):
    """Gera PDF do DRE (Demonstração do Resultado do Exercício)"""
    from .services.calculadora import CalculadoraSaldos
    
    ano = int(request.GET.get('ano', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))
    
    # Calcular DRE
    primeiro_dia = date(ano, mes, 1)
    import calendar
    ultimo_dia = date(ano, mes, calendar.monthday[mes])
    
    # Receitas
    receitas = BaixaFinanceira.objects.filter(
        parcela__titulo__tipo='RECEBER',
        parcela__titulo__empresa=request.empresa,
        data_pagamento__gte=primeiro_dia,
        data_pagamento__lte=ultimo_dia,
        estornado=False
    ).aggregate(total=Sum('valor_liquido'))['total'] or Decimal('0')
    
    # Despesas
    despesas = BaixaFinanceira.objects.filter(
        parcela__titulo__tipo='PAGAR',
        parcela__titulo__empresa=request.empresa,
        data_pagamento__gte=primeiro_dia,
        data_pagamento__lte=ultimo_dia,
        estornado=False
    ).aggregate(total=Sum('valor_liquido'))['total'] or Decimal('0')
    
    resultado = receitas - despesas
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, 
                          topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    from .models import TituloFinanceiro
    MESES_PT = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    titulo = f"DRE - {MESES_PT[mes]}/{ano}"
    criar_cabecalho_pdf(elements, styles, request.empresa, titulo)
    
    # Tabela DRE
    dre_data = [
        ['<b>Descrição</b>', '<b>Valor</b>'],
        ['<b>RECEITAS</b>', formatar_real(receitas)],
        ['(-) <b>DESPESAS</b>', formatar_real(despesas)],
        ['', ''],
        ['<b>RESULTADO DO PERÍODO</b>', formatar_real(resultado)],
    ]
    
    table = Table(dre_data, colWidths=[12*cm, 6*cm])
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Dados
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1f4788')),
        
        # Destaque resultado
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Gráfico de Pizza
    elements.append(Spacer(1, 1*cm))
    
    if receitas > 0 or despesas > 0:
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = [float(receitas), float(despesas)]
        pie.labels = ['Receitas', 'Despesas']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor('#28a745')
        pie.slices[1].fillColor = colors.HexColor('#dc3545')
        
        drawing.add(pie)
        elements.append(drawing)
    
    # Rodapé
    elements.append(Spacer(1, 1*cm))
    rodape_style = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    agora = datetime.now()
    elements.append(Paragraph(f"Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')}", rodape_style))
    
    # Gerar PDF
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f'dre_{mes}_{ano}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


@login_required
def relatorio_fluxo_caixa_pdf(request):
    """Gera PDF do Fluxo de Caixa"""
    ano = int(request.GET.get('ano', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))
    
    # Calcular fluxo
    from .services.calculadora import ProjecaoFluxoCaixa
    dados = ProjecaoFluxoCaixa.fluxo_mensal(ano, mes, request.empresa)
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    MESES_PT = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    titulo = f"FLUXO DE CAIXA - {MESES_PT[mes]}/{ano}"
    criar_cabecalho_pdf(elements, styles, request.empresa, titulo)
    
    # Tabela comparativa
    fluxo_data = [
        ['Item', 'Previsto', 'Realizado', 'Diferença'],
        ['Recebimentos', 
         formatar_real(dados['previsto']['receber']),
         formatar_real(dados['realizado']['receber']),
         formatar_real(dados['diferenca']['receber'])],
        ['Pagamentos', 
         formatar_real(dados['previsto']['pagar']),
         formatar_real(dados['realizado']['pagar']),
         formatar_real(dados['diferenca']['pagar'])],
        ['Saldo', 
         formatar_real(dados['previsto']['saldo']),
         formatar_real(dados['realizado']['saldo']),
         formatar_real(dados['diferenca']['saldo'])],
    ]
    
    table = Table(fluxo_data, colWidths=[6*cm, 4*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),  # Linha "Saldo" em negrito
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1f4788')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Gráfico de Barras
    elements.append(Spacer(1, 1*cm))
    
    drawing = Drawing(400, 200)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 300
    bc.data = [
        [float(dados['previsto']['receber']), float(dados['previsto']['pagar'])],
        [float(dados['realizado']['receber']), float(dados['realizado']['pagar'])]
    ]
    bc.categoryAxis.categoryNames = ['Recebimentos', 'Pagamentos']
    bc.valueAxis.valueMin = 0
    bc.bars[0].fillColor = colors.HexColor('#007bff')
    bc.bars[1].fillColor = colors.HexColor('#28a745')
    
    drawing.add(bc)
    elements.append(drawing)
    
    # Rodapé
    elements.append(Spacer(1, 0.5*cm))
    rodape_style = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.grey, alignment=TA_CENTER)
    agora = datetime.now()
    elements.append(Paragraph(f"Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')}", rodape_style))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f'fluxo_caixa_{mes}_{ano}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


@login_required
def relatorio_ponto_equilibrio_pdf(request):
    """Gera PDF do Ponto de Equilíbrio"""
    periodo_meses = int(request.GET.get('periodo', 12))
    
    # Calcular ponto de equilíbrio
    resultado = AnalisePontoEquilibrio.calcular_break_even(periodo_meses, request.empresa)
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    titulo = f"ANÁLISE DE PONTO DE EQUILÍBRIO - {periodo_meses} meses"
    criar_cabecalho_pdf(elements, styles, request.empresa, titulo)
    
    # Tabela de resultados
    pe_data = [
        ['<b>Indicador</b>', '<b>Valor</b>'],
        ['Custos Fixos Mensais', formatar_real(resultado['custos_fixos'])],
        ['Custos Variáveis Mensais', formatar_real(resultado['custos_variaveis'])],
        ['Margem de Contribuição (%)', f"{resultado['margem_contribuicao']:.2f}%"],
        ['<b>Ponto de Equilíbrio</b>', formatar_real(resultado['ponto_equilibrio'])],
    ]
    
    table = Table(pe_data, colWidths=[12*cm, 6*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1f4788')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(table)
    
    # Rodapé
    elements.append(Spacer(1, 2*cm))
    rodape_style = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.grey, alignment=TA_CENTER)
    agora = datetime.now()
    elements.append(Paragraph(f"Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')}", rodape_style))
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def calendario_financeiro_pdf(request):
    """
    Gera PDF do calendário financeiro do mês
    """
    empresa = request.empresa
    
    # Pega mês/ano dos parâmetros ou usa atual
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    
    # Valida mês/ano
    if mes < 1:
        mes = 12
        ano -= 1
    elif mes > 12:
        mes = 1
        ano += 1
    
    # Primeiro e último dia do mês
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia_num = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_num)
    
    # Busca parcelas do mês
    parcelas_mes = ParcelaFinanceira.objects.filter(
        titulo__empresa=empresa,
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
        status__in=['ABERTO', 'PARCIAL', 'QUITADO']
    ).select_related('titulo', 'titulo__pessoa').order_by('data_vencimento')
    
    # Organiza por dia
    eventos_por_dia = {}
    for dia in range(1, ultimo_dia_num + 1):
        eventos_por_dia[dia] = {
            'a_pagar': [],
            'a_receber': [],
            'total_pagar': Decimal('0.00'),
            'total_receber': Decimal('0.00'),
        }
    
    for parcela in parcelas_mes:
        dia = parcela.data_vencimento.day
        
        evento = {
            'parcela': parcela,
            'titulo': parcela.titulo,
            'pessoa': parcela.titulo.pessoa,
            'valor': parcela.saldo_aberto if parcela.status != 'QUITADO' else parcela.valor_original,
            'status': parcela.status,
            'vencida': parcela.esta_vencida()
        }
        
        if parcela.titulo.tipo == 'PAGAR':
            eventos_por_dia[dia]['a_pagar'].append(evento)
            if parcela.status != 'QUITADO':
                eventos_por_dia[dia]['total_pagar'] += parcela.saldo_aberto
        else:
            eventos_por_dia[dia]['a_receber'].append(evento)
            if parcela.status != 'QUITADO':
                eventos_por_dia[dia]['total_receber'] += parcela.saldo_aberto
    
    # Configuração do PDF (paisagem para melhor visualização do calendário)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="calendario_financeiro_{mes:02d}_{ano}.pdf"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                          leftMargin=1.5*cm, rightMargin=1.5*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Cabeçalho
    criar_cabecalho_pdf(elements, styles, empresa, f"Calendário Financeiro - {MESES_PT[mes]}/{ano}")
    
    # Monta calendário
    cal = calendar.monthcalendar(ano, mes)
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    
    # Dados da tabela do calendário
    calendario_data = []
    
    # Cabeçalho dos dias da semana
    calendario_data.append(dias_semana)
    
    # Estilo para células
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)
    titulo_dia_style = ParagraphStyle('TituloDia', parent=styles['Normal'], 
                                     fontSize=10, fontName='Helvetica-Bold')
    
    # Adiciona as semanas
    for semana in cal:
        linha_semana = []
        for dia in semana:
            if dia == 0:
                linha_semana.append('')
            else:
                # Monta conteúdo da célula
                eventos_dia = eventos_por_dia[dia]
                cell_content = [Paragraph(f"<b>{dia}</b>", titulo_dia_style)]
                
                # A Pagar
                if eventos_dia['a_pagar']:
                    qtd_pagar = len(eventos_dia['a_pagar'])
                    total_pagar = eventos_dia['total_pagar']
                    cell_content.append(Spacer(1, 0.1*cm))
                    cell_content.append(Paragraph(
                        f"<font color='red'>▼ Pagar ({qtd_pagar}): {formatar_real(total_pagar)}</font>",
                        cell_style
                    ))
                
                # A Receber
                if eventos_dia['a_receber']:
                    qtd_receber = len(eventos_dia['a_receber'])
                    total_receber = eventos_dia['total_receber']
                    cell_content.append(Spacer(1, 0.1*cm))
                    cell_content.append(Paragraph(
                        f"<font color='green'>▲ Receber ({qtd_receber}): {formatar_real(total_receber)}</font>",
                        cell_style
                    ))
                
                linha_semana.append(cell_content)
        
        calendario_data.append(linha_semana)
    
    # Cria tabela do calendário
    col_width = (landscape(A4)[0] - 3*cm) / 7  # Divide largura disponível por 7 dias
    table = Table(calendario_data, colWidths=[col_width]*7, rowHeights=None)
    
    # Estilo da tabela
    table_style = [
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]
    
    # Alterna cores de fundo nas linhas (semanas)
    for i in range(1, len(calendario_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
    
    table.setStyle(TableStyle(table_style))
    elements.append(table)
    
    # Legenda
    elements.append(Spacer(1, 1*cm))
    legenda_data = [
        [
            Paragraph("<font color='red'><b>▼ Contas a Pagar</b></font>", cell_style),
            Paragraph("<font color='green'><b>▲ Contas a Receber</b></font>", cell_style)
        ]
    ]
    legenda_table = Table(legenda_data, colWidths=[10*cm, 10*cm])
    legenda_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(legenda_table)
    
    # Rodapé
    elements.append(Spacer(1, 1*cm))
    rodape_style = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.grey, alignment=TA_CENTER)
    agora = datetime.now()
    elements.append(Paragraph(f"Relatório gerado em {agora.strftime('%d/%m/%Y às %H:%M')}", rodape_style))
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response
