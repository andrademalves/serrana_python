"""
Serviço de Régua de Cobrança
Cálculo de etapas e gerenciamento de disparos
"""
from datetime import date, timedelta
from django.db.models import Q
from financeiro.models import ParcelaFinanceira, ReguaEtapa, LogCobranca


class ReguaService:
    """Serviço para processar réguas de cobrança"""
    
    @staticmethod
    def calcular_etapas_disponiveis(parcela):
        """
        Calcula quais etapas devem ser enviadas para uma parcela
        baseado no offset de dias em relação ao vencimento
        """
        if not parcela.regua or not parcela.regua_ativa:
            return []
        
        # Calcula dias desde vencimento (negativo = antes, positivo = depois)
        offset_atual = (date.today() - parcela.data_vencimento).days
        
        # Busca etapas que devem disparar hoje
        etapas = ReguaEtapa.objects.filter(
            regua=parcela.regua,
            ativo=True,
            offset_dias=offset_atual
        ).order_by('ordem')
        
        # Filtra etapas já enviadas
        etapas_enviadas = LogCobranca.objects.filter(
            parcela=parcela,
            etapa__in=etapas,
            status='ENVIADO'
        ).values_list('etapa_id', flat=True)
        
        # Retorna apenas não enviadas
        return etapas.exclude(id__in=etapas_enviadas)
    
    @staticmethod
    def buscar_parcelas_para_processar(empresa=None):
        """
        Busca parcelas que devem ser processadas hoje
        """
        parcelas = ParcelaFinanceira.objects.filter(
            regua_ativa=True,
            regua__isnull=False,
            regua__ativa=True,
        ).exclude(
            status__in=['QUITADO', 'CANCELADO']
        ).exclude(
            status_cobranca='BLOQUEADA'
        ).select_related('regua', 'titulo', 'titulo__pessoa')
        
        # Filtra pausadas
        parcelas = parcelas.filter(
            Q(pausar_regua_ate__isnull=True) | Q(pausar_regua_ate__lt=date.today())
        )
        
        if empresa:
            parcelas = parcelas.filter(titulo__empresa=empresa)
        
        return parcelas
    
    @staticmethod
    def deve_disparar_etapa(parcela, etapa):
        """
        Verifica se uma etapa específica deve ser disparada
        """
        # Calcula offset atual
        offset_atual = (date.today() - parcela.data_vencimento).days
        
        # Verifica se é o dia certo
        if etapa.offset_dias != offset_atual:
            return False
        
        # Verifica se já foi enviada
        ja_enviada = LogCobranca.objects.filter(
            parcela=parcela,
            etapa=etapa,
            status='ENVIADO'
        ).exists()
        
        return not ja_enviada
    
    @staticmethod
    def criar_log_cobranca(parcela, etapa, canal='EMAIL'):
        """
        Cria um log de cobrança para rastreamento
        """
        # Determina destinatário
        if canal == 'EMAIL':
            destinatario = parcela.contato_email_override or parcela.titulo.pessoa.email
            
            if not destinatario:
                raise ValueError(f"Parcela {parcela.id} não possui e-mail configurado")
        
        # Cria log
        log = LogCobranca.objects.create(
            parcela=parcela,
            etapa=etapa,
            canal=canal,
            destinatario=destinatario,
            status='ENFILEIRADO'
        )
        
        return log
    
    @staticmethod
    def atualizar_status_cobranca(parcela):
        """
        Atualiza status de cobrança baseado em dias de atraso
        """
        dias_atraso = parcela.dias_atraso()
        
        # Se tem promessa de pagamento
        if parcela.data_promessa_pagamento and parcela.data_promessa_pagamento >= date.today():
            parcela.status_cobranca = 'PROMESSA'
        
        # Cobrança intensa após 15 dias
        elif dias_atraso >= 15:
            parcela.status_cobranca = 'INTENSA'
        
        # Normal
        elif dias_atraso < 15:
            if parcela.status_cobranca == 'INTENSA':
                parcela.status_cobranca = 'NORMAL'
        
        parcela.save(update_fields=['status_cobranca'])
    
    @staticmethod
    def pausar_regua(parcela, ate_data=None, motivo=None):
        """
        Pausa régua temporariamente
        """
        if not ate_data:
            ate_data = date.today() + timedelta(days=7)
        
        parcela.pausar_regua_ate = ate_data
        parcela.save(update_fields=['pausar_regua_ate'])
        
        return True
    
    @staticmethod
    def retomar_regua(parcela):
        """
        Retoma régua pausada
        """
        parcela.pausar_regua_ate = None
        parcela.save(update_fields=['pausar_regua_ate'])
        
        return True
    
    @staticmethod
    def marcar_promessa_pagamento(parcela, data_promessa, observacao=None):
        """
        Marca promessa de pagamento
        """
        parcela.data_promessa_pagamento = data_promessa
        parcela.observacao_promessa = observacao
        parcela.status_cobranca = 'PROMESSA'
        parcela.save(update_fields=['data_promessa_pagamento', 'observacao_promessa', 'status_cobranca'])
        
        return True
