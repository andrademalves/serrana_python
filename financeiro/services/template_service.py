"""
Serviço de Renderização de Templates de Mensagens
Substitui variáveis dinâmicas nos templates
"""
from datetime import date


class TemplateService:
    """Renderiza templates de e-mail com variáveis dinâmicas"""
    
    @staticmethod
    def renderizar(template, parcela):
        """
        Renderiza template substituindo variáveis
        
        Variáveis disponíveis:
        - {cliente_nome}
        - {parcela_numero}
        - {parcela_valor}
        - {parcela_vencimento}
        - {dias_atraso}
        - {empresa_nome}
        - {titulo_numero}
        """
        if not template:
            return ""
        
        # Preparar dados
        dias_atraso = parcela.dias_atraso()
        empresa_nome = parcela.titulo.empresa.razao_social if parcela.titulo.empresa else "Empresa"
        
        # Dicionário de substituições
        variaveis = {
            '{cliente_nome}': parcela.titulo.pessoa.nome if parcela.titulo.pessoa else "Cliente",
            '{parcela_numero}': str(parcela.numero_parcela),
            '{parcela_valor}': f"R$ {parcela.valor_original:,.2f}",
            '{parcela_vencimento}': parcela.data_vencimento.strftime('%d/%m/%Y'),
            '{data_vencimento}': parcela.data_vencimento.strftime('%d/%m/%Y'),  # Alias
            '{dias_atraso}': str(dias_atraso) if dias_atraso > 0 else "0",
            '{empresa_nome}': empresa_nome,
            '{titulo_numero}': parcela.titulo.numero_documento,
            '{saldo_aberto}': f"R$ {parcela.saldo_aberto:,.2f}",
        }
        
        # Substituir todas as variáveis
        mensagem = template
        for variavel, valor in variaveis.items():
            mensagem = mensagem.replace(variavel, valor)
        
        return mensagem
    
    @staticmethod
    def obter_template_padrao_email(tipo='LEMBRETE'):
        """
        Retorna templates padrões de e-mail
        """
        templates = {
            'LEMBRETE': {
                'assunto': 'Lembrete: Parcela {parcela_numero} vence em breve',
                'corpo': """
Olá {cliente_nome},

Este é um lembrete amigável sobre a parcela nº {parcela_numero} do título {titulo_numero}.

Valor: {parcela_valor}
Vencimento: {parcela_vencimento}

Por favor, organize-se para efetuar o pagamento na data correta.

Atenciosamente,
{empresa_nome}
"""
            },
            'VENCIMENTO': {
                'assunto': 'Parcela {parcela_numero} vence hoje',
                'corpo': """
Olá {cliente_nome},

Sua parcela nº {parcela_numero} vence HOJE.

Valor: {parcela_valor}
Vencimento: {parcela_vencimento}

Por favor, efetue o pagamento para evitar juros e multa.

Atenciosamente,
{empresa_nome}
"""
            },
            'ATRASO_LEVE': {
                'assunto': 'Parcela {parcela_numero} está em atraso',
                'corpo': """
Olá {cliente_nome},

Identificamos que a parcela nº {parcela_numero} está em atraso há {dias_atraso} dia(s).

Valor: {parcela_valor}
Vencimento: {parcela_vencimento}
Saldo em aberto: {saldo_aberto}

Pedimos que regularize o quanto antes para evitar a cobrança de juros adicionais.

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
{empresa_nome}
"""
            },
            'COBRANCA': {
                'assunto': 'URGENTE: Parcela {parcela_numero} vencida - Regularize agora',
                'corpo': """
{cliente_nome},

Sua parcela nº {parcela_numero} está vencida há {dias_atraso} dias.

Valor original: {parcela_valor}
Saldo em aberto: {saldo_aberto}
Vencimento: {parcela_vencimento}

É URGENTE que você regularize este débito o mais breve possível.

Caso já tenha efetuado o pagamento, por favor desconsidere este aviso e nos envie o comprovante.

Se precisar negociar, entre em contato conosco imediatamente.

{empresa_nome}
"""
            },
            'FINAL': {
                'assunto': 'AVISO FINAL: Parcela {parcela_numero} - Últimas providências',
                'corpo': """
{cliente_nome},

Este é nosso ÚLTIMO AVISO sobre a parcela nº {parcela_numero}.

Dias de atraso: {dias_atraso}
Valor em aberto: {saldo_aberto}
Vencimento original: {parcela_vencimento}

Caso não haja regularização imediata, seremos forçados a tomar medidas cabíveis.

Entre em contato URGENTE para negociação.

{empresa_nome}
"""
            }
        }
        
        return templates.get(tipo, templates['LEMBRETE'])
