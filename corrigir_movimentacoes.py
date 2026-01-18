"""
Script para corrigir movimentações de conta faltantes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import BaixaFinanceira, MovimentacaoConta

def corrigir_movimentacoes():
    """Cria movimentações faltantes para baixas existentes"""
    
    # Busca todas as baixas não estornadas
    baixas = BaixaFinanceira.objects.filter(estornado=False).select_related('parcela__titulo', 'conta_financeira')
    
    total_baixas = baixas.count()
    corrigidas = 0
    
    print(f"Total de baixas não estornadas: {total_baixas}")
    
    for baixa in baixas:
        # Verifica se existe movimentação não estornada para esta baixa
        tem_movimentacao = MovimentacaoConta.objects.filter(
            baixa_financeira=baixa,
            estornado=False
        ).exists()
        
        if not tem_movimentacao:
            print(f"Criando movimentação para baixa #{baixa.id} - {baixa.parcela.titulo.numero_documento}")
            
            tipo = 'ENTRADA' if baixa.parcela.titulo.tipo == 'RECEBER' else 'SAIDA'
            
            MovimentacaoConta.objects.create(
                conta_financeira=baixa.conta_financeira,
                tipo=tipo,
                data_movimentacao=baixa.data_pagamento,
                valor=baixa.valor_liquido,
                descricao=f"{baixa.parcela.titulo.get_tipo_display()} - {baixa.parcela.titulo.numero_documento} - Parc {baixa.parcela.numero_parcela}",
                baixa_financeira=baixa,
                estornado=False
            )
            
            corrigidas += 1
    
    print(f"\n✅ Correção concluída!")
    print(f"Total de baixas analisadas: {total_baixas}")
    print(f"Movimentações criadas: {corrigidas}")

if __name__ == '__main__':
    corrigir_movimentacoes()
