from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Oportunidade, HistoricoEtapa, EtapaFunil


@receiver(pre_save, sender=Oportunidade)
def registrar_mudanca_etapa(sender, instance, **kwargs):
    """Registra histórico quando a etapa muda"""
    if instance.pk:  # Se já existe (update)
        try:
            oportunidade_anterior = Oportunidade.objects.get(pk=instance.pk)
            if oportunidade_anterior.etapa != instance.etapa:
                # Criar histórico
                HistoricoEtapa.objects.create(
                    oportunidade=instance,
                    etapa_de=oportunidade_anterior.etapa,
                    etapa_para=instance.etapa,
                    usuario=instance.criado_por,  # Idealmente pegar do request
                )
        except Oportunidade.DoesNotExist:
            pass
    else:  # Novo registro
        # Será criado após o save no post_save
        pass


@receiver(post_save, sender=Oportunidade)
def criar_historico_inicial(sender, instance, created, **kwargs):
    """Cria histórico inicial quando oportunidade é criada"""
    if created:
        HistoricoEtapa.objects.create(
            oportunidade=instance,
            etapa_de=None,
            etapa_para=instance.etapa,
            usuario=instance.criado_por,
            observacao='Oportunidade criada'
        )


# Signal para quando orçamento for aprovado (integração reversa)
# Este será chamado do módulo projetos
def vincular_oportunidade_ao_projeto(oportunidade, projeto):
    """
    Chamado quando um orçamento vinculado a oportunidade é aprovado e vira projeto
    """
    if oportunidade and projeto:
        # Buscar etapa final tipo 'ganho'
        etapa_ganho = EtapaFunil.objects.filter(
            pipeline=oportunidade.pipeline,
            is_final=True,
            tipo_final='ganho',
            ativo=True
        ).first()
        
        if etapa_ganho:
            oportunidade.etapa = etapa_ganho
            oportunidade.projeto = projeto
            oportunidade.status = 'ganho'
            oportunidade.data_fechamento = timezone.now()
            oportunidade.save()
