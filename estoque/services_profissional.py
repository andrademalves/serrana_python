"""
SERVICES - REGRAS DE NEGÓCIO DO ESTOQUE PROFISSIONAL
====================================================

Camada de serviços com regras de negócio complexas:
- Cálculo de estoque mínimo e consumo médio
- Sugestões de reposição
- Relatórios e consultas especializadas
- Validações avançadas

Autor: Sistema Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from django.db import models, transaction
from django.db.models import Sum, Avg, Q, F, Count, Max, Min
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ValidationError

from cadastros.models import Pessoa, Produto
from .models_profissional import (
    LocalEstoque,
    DestinoEstoque,
    MovimentoEstoque,
    SaldoEstoque,
    CustoObra,
    ProdutoFornecedor
)


# ==============================================================================
# 1. CÁLCULO DE ESTOQUE MÍNIMO E CONSUMO
# ==============================================================================

class EstoqueMinimoService:
    """
    Serviço para cálculo de estoque mínimo baseado em consumo real.
    """
    
    @staticmethod
    def calcular_consumo_medio_diario(
        produto: Produto,
        dias: int = 90,
        local: Optional[LocalEstoque] = None
    ) -> Decimal:
        """
        Calcula consumo médio diário de um produto baseado em histórico.
        
        Args:
            produto: Produto para análise
            dias: Período de análise (padrão 90 dias)
            local: Local específico (opcional)
        
        Returns:
            Consumo médio diário (Decimal)
        """
        data_inicio = timezone.now() - timedelta(days=dias)
        
        # Filtrar saídas do período
        query = MovimentoEstoque.objects.filter(
            produto=produto,
            tipo_movimento='SAIDA',
            data_operacao__gte=data_inicio,
            estornado=False
        )
        
        if local:
            query = query.filter(local_origem=local)
        
        # Somar total de saídas
        total_saidas = query.aggregate(
            total=Coalesce(Sum('quantidade'), Decimal('0'))
        )['total']
        
        # Calcular média diária
        if dias > 0:
            consumo_medio = total_saidas / Decimal(str(dias))
        else:
            consumo_medio = Decimal('0')
        
        return consumo_medio.quantize(Decimal('0.001'))
    
    @staticmethod
    def calcular_ponto_ressuprimento(
        produto: Produto,
        consumo_medio_diario: Optional[Decimal] = None,
        dias_analise: int = 90
    ) -> Decimal:
        """
        Calcula ponto de ressuprimento baseado em:
        - Consumo médio diário
        - Lead time do fornecedor
        - Estoque de segurança
        
        Fórmula: Ponto = (Consumo Médio × Lead Time) + Estoque Segurança
        
        Args:
            produto: Produto para cálculo
            consumo_medio_diario: Consumo médio (calcula automaticamente se None)
            dias_analise: Período para cálculo de consumo
        
        Returns:
            Ponto de ressuprimento (Decimal)
        """
        # Se não informado, calcular consumo médio
        if consumo_medio_diario is None:
            consumo_medio_diario = EstoqueMinimoService.calcular_consumo_medio_diario(
                produto, dias=dias_analise
            )
        
        # Usar lead_time e estoque_seguranca do produto
        lead_time = getattr(produto, 'lead_time_dias', 0) or 0
        estoque_seguranca = getattr(produto, 'estoque_seguranca', Decimal('0')) or Decimal('0')
        
        # Calcular ponto de ressuprimento
        ponto = (consumo_medio_diario * Decimal(str(lead_time))) + estoque_seguranca
        
        return ponto.quantize(Decimal('0.001'))
    
    @staticmethod
    def calcular_quantidade_sugerida_compra(
        produto: Produto,
        saldo_atual: Decimal,
        ponto_ressuprimento: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calcula quantidade sugerida para compra.
        
        Args:
            produto: Produto
            saldo_atual: Saldo atual total
            ponto_ressuprimento: Ponto de ressuprimento (calcula se None)
        
        Returns:
            Quantidade sugerida para compra
        """
        if ponto_ressuprimento is None:
            ponto_ressuprimento = EstoqueMinimoService.calcular_ponto_ressuprimento(produto)
        
        if saldo_atual < ponto_ressuprimento:
            quantidade_sugerida = ponto_ressuprimento - saldo_atual
        else:
            quantidade_sugerida = Decimal('0')
        
        return quantidade_sugerida.quantize(Decimal('0.001'))
    
    @staticmethod
    @transaction.atomic
    def atualizar_consumo_medio_produtos(dias_analise: int = 90) -> Dict:
        """
        Atualiza consumo_medio_diario de todos os produtos ativos.
        Deve ser executado periodicamente (job noturno/semanal).
        
        Args:
            dias_analise: Período de análise
        
        Returns:
            Dict com estatísticas da atualização
        """
        produtos_atualizados = 0
        produtos_sem_consumo = 0
        
        # Buscar produtos ativos que têm o campo consumo_medio_diario
        produtos = Produto.objects.filter(ativo=True)
        
        for produto in produtos:
            # Calcular consumo médio
            consumo_medio = EstoqueMinimoService.calcular_consumo_medio_diario(
                produto, dias=dias_analise
            )
            
            # Atualizar produto se campo existir
            if hasattr(produto, 'consumo_medio_diario'):
                produto.consumo_medio_diario = consumo_medio
                
                # Recalcular estoque_minimo com base no consumo
                if hasattr(produto, 'estoque_minimo'):
                    ponto = EstoqueMinimoService.calcular_ponto_ressuprimento(
                        produto, consumo_medio_diario=consumo_medio
                    )
                    produto.estoque_minimo = ponto
                
                produto.save(update_fields=['consumo_medio_diario', 'estoque_minimo'])
                produtos_atualizados += 1
                
                if consumo_medio == 0:
                    produtos_sem_consumo += 1
        
        return {
            'produtos_atualizados': produtos_atualizados,
            'produtos_sem_consumo': produtos_sem_consumo,
            'dias_analise': dias_analise,
            'data_atualizacao': timezone.now()
        }


# ==============================================================================
# 2. RELATÓRIOS E CONSULTAS
# ==============================================================================

class RelatorioEstoqueService:
    """
    Serviço para geração de relatórios de estoque.
    """
    
    @staticmethod
    def posicao_estoque(
        produto: Optional[Produto] = None,
        local: Optional[LocalEstoque] = None,
        apenas_com_saldo: bool = False
    ) -> models.QuerySet:
        """
        Relatório de posição de estoque (saldos atuais).
        
        Args:
            produto: Filtrar por produto específico
            local: Filtrar por local específico
            apenas_com_saldo: Mostrar apenas itens com saldo > 0
        
        Returns:
            QuerySet de SaldoEstoque
        """
        query = SaldoEstoque.objects.select_related(
            'produto', 'local'
        ).all()
        
        if produto:
            query = query.filter(produto=produto)
        
        if local:
            query = query.filter(local=local)
        
        if apenas_com_saldo:
            query = query.filter(saldo_quantidade__gt=0)
        
        return query.order_by('produto__codigo', 'local__codigo')
    
    @staticmethod
    def extrato_movimentos(
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        produto: Optional[Produto] = None,
        local_origem: Optional[LocalEstoque] = None,
        local_destino: Optional[LocalEstoque] = None,
        obra: Optional[str] = None,
        tipo_movimento: Optional[str] = None,
        solicitante: Optional[Pessoa] = None,
        entregador: Optional[Pessoa] = None
    ) -> models.QuerySet:
        """
        Extrato de movimentos com filtros diversos.
        
        Returns:
            QuerySet de MovimentoEstoque
        """
        query = MovimentoEstoque.objects.select_related(
            'produto', 'local_origem', 'local_destino', 'destino',
            'fornecedor', 'solicitante', 'entregador', 'criado_por'
        ).all()
        
        if data_inicio:
            query = query.filter(data_operacao__gte=data_inicio)
        
        if data_fim:
            # Incluir todo o dia final
            data_fim_completa = datetime.combine(data_fim, datetime.max.time())
            query = query.filter(data_operacao__lte=data_fim_completa)
        
        if produto:
            query = query.filter(produto=produto)
        
        if local_origem:
            query = query.filter(local_origem=local_origem)
        
        if local_destino:
            query = query.filter(local_destino=local_destino)
        
        if obra:
            query = query.filter(obra=obra)
        
        if tipo_movimento:
            query = query.filter(tipo_movimento=tipo_movimento)
        
        if solicitante:
            query = query.filter(solicitante=solicitante)
        
        if entregador:
            query = query.filter(entregador=entregador)
        
        return query.order_by('-data_operacao', '-criado_em')
    
    @staticmethod
    def produtos_abaixo_minimo() -> List[Dict]:
        """
        Relatório de produtos abaixo do estoque mínimo.
        Inclui sugestão de quantidade para compra.
        
        Returns:
            Lista de dicionários com informações dos produtos
        """
        produtos_criticos = []
        
        # Buscar produtos ativos com estoque_minimo definido
        produtos = Produto.objects.filter(
            ativo=True
        ).exclude(
            Q(estoque_minimo__isnull=True) | Q(estoque_minimo=0)
        )
        
        for produto in produtos:
            # Calcular saldo total
            saldo_total = SaldoEstoque.objects.filter(
                produto=produto
            ).aggregate(
                total=Coalesce(Sum('saldo_quantidade'), Decimal('0'))
            )['total']
            
            # Verificar se está abaixo do mínimo
            if hasattr(produto, 'estoque_minimo') and saldo_total < produto.estoque_minimo:
                # Calcular diferença e sugestão
                diferenca = produto.estoque_minimo - saldo_total
                
                # Se tem consumo médio e lead time, calcular quantidade ideal
                if hasattr(produto, 'consumo_medio_diario') and hasattr(produto, 'lead_time_dias'):
                    ponto_ideal = EstoqueMinimoService.calcular_ponto_ressuprimento(produto)
                    qtd_sugerida = max(diferenca, ponto_ideal - saldo_total)
                else:
                    qtd_sugerida = diferenca
                
                # Fornecedor principal
                fornecedor_nome = produto.fornecedor.nome_razao_social if hasattr(produto, 'fornecedor') and produto.fornecedor else 'Não definido'
                
                produtos_criticos.append({
                    'produto': produto,
                    'codigo': produto.codigo,
                    'descricao': produto.descricao,
                    'unidade': produto.unidade,
                    'saldo_atual': saldo_total,
                    'estoque_minimo': produto.estoque_minimo,
                    'diferenca': diferenca,
                    'quantidade_sugerida': qtd_sugerida,
                    'fornecedor': fornecedor_nome,
                    'criticidade': (diferenca / produto.estoque_minimo * 100) if produto.estoque_minimo > 0 else 0
                })
        
        # Ordenar por criticidade (maior = mais crítico)
        produtos_criticos.sort(key=lambda x: x['criticidade'], reverse=True)
        
        return produtos_criticos
    
    @staticmethod
    def consumo_por_produto(
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        produto: Optional[Produto] = None
    ) -> List[Dict]:
        """
        Relatório de consumo médio por produto.
        
        Returns:
            Lista com dados de consumo
        """
        # Período padrão: últimos 90 dias
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=90)
        
        dias_periodo = (data_fim - data_inicio).days + 1
        
        # Query de produtos
        query_produtos = Produto.objects.filter(ativo=True)
        if produto:
            query_produtos = query_produtos.filter(pk=produto.pk)
        
        resultados = []
        
        for prod in query_produtos:
            # Total de saídas no período
            total_saidas = MovimentoEstoque.objects.filter(
                produto=prod,
                tipo_movimento='SAIDA',
                data_operacao__date__gte=data_inicio,
                data_operacao__date__lte=data_fim,
                estornado=False
            ).aggregate(
                total=Coalesce(Sum('quantidade'), Decimal('0'))
            )['total']
            
            # Consumo médio diário
            consumo_medio = total_saidas / Decimal(str(dias_periodo)) if dias_periodo > 0 else Decimal('0')
            
            # Saldo atual
            saldo_atual = SaldoEstoque.objects.filter(
                produto=prod
            ).aggregate(
                total=Coalesce(Sum('saldo_quantidade'), Decimal('0'))
            )['total']
            
            # Lead time e ponto de ressuprimento
            lead_time = getattr(prod, 'lead_time_dias', 0) or 0
            estoque_seguranca = getattr(prod, 'estoque_seguranca', Decimal('0')) or Decimal('0')
            ponto_ressuprimento = (consumo_medio * Decimal(str(lead_time))) + estoque_seguranca
            
            # Status
            if saldo_atual < ponto_ressuprimento:
                status = 'CRÍTICO'
            elif saldo_atual < (ponto_ressuprimento * Decimal('1.5')):
                status = 'ATENÇÃO'
            else:
                status = 'OK'
            
            resultados.append({
                'produto': prod,
                'codigo': prod.codigo,
                'descricao': prod.descricao,
                'consumo_total': total_saidas,
                'consumo_medio_diario': consumo_medio,
                'lead_time_dias': lead_time,
                'ponto_ressuprimento': ponto_ressuprimento,
                'saldo_atual': saldo_atual,
                'status': status,
                'dias_estoque': (saldo_atual / consumo_medio) if consumo_medio > 0 else Decimal('999')
            })
        
        return resultados
    
    @staticmethod
    def custos_por_obra(
        obra: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        categoria: Optional[str] = None
    ) -> Dict:
        """
        Relatório de custos por obra.
        Separa custos do estoque de outros custos.
        
        Returns:
            Dict com custos detalhados e totalizadores
        """
        query = CustoObra.objects.all()
        
        if obra:
            query = query.filter(obra=obra)
        
        if data_inicio:
            query = query.filter(data__gte=data_inicio)
        
        if data_fim:
            query = query.filter(data__lte=data_fim)
        
        if categoria:
            query = query.filter(categoria=categoria)
        
        # Totalizar por categoria
        totais_categoria = query.values('categoria').annotate(
            total=Sum('valor')
        ).order_by('categoria')
        
        # Totalizar por origem
        totais_origem = query.values('origem').annotate(
            total=Sum('valor')
        ).order_by('origem')
        
        # Total geral
        total_geral = query.aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        # Custos do estoque especificamente
        custos_estoque = query.filter(origem='ESTOQUE').aggregate(
            total=Coalesce(Sum('valor'), Decimal('0'))
        )['total']
        
        return {
            'custos': query.select_related('fornecedor', 'movimento_estoque', 'criado_por'),
            'totais_categoria': list(totais_categoria),
            'totais_origem': list(totais_origem),
            'total_geral': total_geral,
            'custos_estoque': custos_estoque,
            'custos_outros': total_geral - custos_estoque,
            'percentual_estoque': (custos_estoque / total_geral * 100) if total_geral > 0 else 0
        }


# ==============================================================================
# 3. OPERAÇÕES DE ESTOQUE (Helpers)
# ==============================================================================

class OperacaoEstoqueService:
    """
    Serviço para facilitar operações de estoque.
    """
    
    @staticmethod
    @transaction.atomic
    def criar_entrada(
        documento: str,
        data_operacao: datetime,
        fornecedor: Pessoa,
        local_destino: LocalEstoque,
        itens: List[Dict],
        usuario: User,
        observacao: str = ''
    ) -> List[MovimentoEstoque]:
        """
        Cria entrada de estoque (NF).
        
        Args:
            documento: Número do documento (NF)
            data_operacao: Data da entrada
            fornecedor: Fornecedor
            local_destino: Local de destino
            itens: Lista de dicts com {produto, quantidade, custo_unitario}
            usuario: Usuário que está registrando
            observacao: Observações
        
        Returns:
            Lista de MovimentoEstoque criados
        """
        if not fornecedor.fornecedor:
            raise ValidationError('Pessoa informada não é fornecedor.')
        
        movimentos = []
        
        for item in itens:
            movimento = MovimentoEstoque.objects.create(
                tipo_movimento='ENTRADA',
                documento=documento,
                documento_tipo='NF_ENTRADA',
                data_operacao=data_operacao,
                produto=item['produto'],
                local_destino=local_destino,
                quantidade=item['quantidade'],
                custo_unitario_aplicado=item['custo_unitario'],
                fornecedor=fornecedor,
                observacao=observacao,
                criado_por=usuario
            )
            movimentos.append(movimento)
        
        return movimentos
    
    @staticmethod
    @transaction.atomic
    def criar_saida(
        documento: str,
        data_operacao: datetime,
        local_origem: LocalEstoque,
        destino: DestinoEstoque,
        itens: List[Dict],
        usuario: User,
        obra: Optional[str] = None,
        solicitante: Optional[Pessoa] = None,
        entregador: Optional[Pessoa] = None,
        observacao: str = ''
    ) -> List[MovimentoEstoque]:
        """
        Cria saída de estoque (requisição).
        
        Args:
            documento: Número da requisição
            data_operacao: Data da saída
            local_origem: Local de origem
            destino: Destino/finalidade
            itens: Lista de dicts com {produto, quantidade}
            usuario: Usuário que está registrando
            obra: Obra (se destino exigir)
            solicitante: Funcionário que solicitou
            entregador: Funcionário que entregou (almoxarife)
            observacao: Observações
        
        Returns:
            Lista de MovimentoEstoque criados
        """
        # Validar obra se destino exigir
        if destino.exige_obra and not obra:
            raise ValidationError(f'Destino "{destino.nome}" exige que uma obra seja informada.')
        
        # Validar funcionários
        if solicitante and not solicitante.funcionario:
            raise ValidationError('Solicitante deve ser um funcionário.')
        
        if entregador and not entregador.funcionario:
            raise ValidationError('Entregador deve ser um funcionário.')
        
        movimentos = []
        
        for item in itens:
            # Verificar saldo antes de criar
            try:
                saldo = SaldoEstoque.objects.get(
                    produto=item['produto'],
                    local=local_origem
                )
                if saldo.saldo_quantidade < item['quantidade']:
                    if not local_origem.permite_saldo_negativo:
                        raise ValidationError(
                            f"Saldo insuficiente de {item['produto'].descricao}. "
                            f"Disponível: {saldo.saldo_quantidade} {item['produto'].unidade}"
                        )
            except SaldoEstoque.DoesNotExist:
                raise ValidationError(
                    f"Produto {item['produto'].descricao} não possui saldo no local {local_origem.nome}"
                )
            
            movimento = MovimentoEstoque.objects.create(
                tipo_movimento='SAIDA',
                documento=documento,
                documento_tipo='REQ_SAIDA',
                data_operacao=data_operacao,
                produto=item['produto'],
                local_origem=local_origem,
                destino=destino,
                obra=obra,
                quantidade=item['quantidade'],
                custo_unitario_aplicado=saldo.custo_medio,  # Será sobrescrito pelo save()
                solicitante=solicitante,
                entregador=entregador,
                observacao=observacao,
                criado_por=usuario
            )
            movimentos.append(movimento)
        
        return movimentos
    
    @staticmethod
    @transaction.atomic
    def criar_transferencia(
        documento: str,
        data_operacao: datetime,
        local_origem: LocalEstoque,
        local_destino: LocalEstoque,
        itens: List[Dict],
        usuario: User,
        observacao: str = ''
    ) -> List[MovimentoEstoque]:
        """
        Cria transferência entre locais.
        
        Args:
            documento: Número da transferência
            data_operacao: Data da transferência
            local_origem: Local de origem
            local_destino: Local de destino
            itens: Lista de dicts com {produto, quantidade}
            usuario: Usuário que está registrando
            observacao: Observações
        
        Returns:
            Lista de MovimentoEstoque criados
        """
        if local_origem == local_destino:
            raise ValidationError('Local de origem e destino não podem ser iguais.')
        
        movimentos = []
        
        for item in itens:
            movimento = MovimentoEstoque.objects.create(
                tipo_movimento='TRANSFERENCIA',
                documento=documento,
                documento_tipo='TRANS',
                data_operacao=data_operacao,
                produto=item['produto'],
                local_origem=local_origem,
                local_destino=local_destino,
                quantidade=item['quantidade'],
                custo_unitario_aplicado=Decimal('0'),  # Será calculado pelo save()
                observacao=observacao,
                criado_por=usuario
            )
            movimentos.append(movimento)
        
        return movimentos
    
    @staticmethod
    def validar_saldo_disponivel(
        produto: Produto,
        local: LocalEstoque,
        quantidade: Decimal
    ) -> Tuple[bool, str, Decimal]:
        """
        Valida se há saldo disponível.
        
        Returns:
            Tupla (tem_saldo: bool, mensagem: str, saldo_disponivel: Decimal)
        """
        try:
            saldo = SaldoEstoque.objects.get(produto=produto, local=local)
            saldo_disponivel = saldo.saldo_quantidade
            
            if saldo_disponivel >= quantidade:
                return (True, 'Saldo disponível', saldo_disponivel)
            else:
                if local.permite_saldo_negativo:
                    return (True, f'Saldo insuficiente, mas local permite negativo. Disponível: {saldo_disponivel}', saldo_disponivel)
                else:
                    return (False, f'Saldo insuficiente. Disponível: {saldo_disponivel} {produto.unidade}', saldo_disponivel)
        
        except SaldoEstoque.DoesNotExist:
            if local.permite_saldo_negativo:
                return (True, 'Produto sem saldo, mas local permite negativo', Decimal('0'))
            else:
                return (False, f'Produto {produto.descricao} não possui saldo no local {local.nome}', Decimal('0'))


# ==============================================================================
# 4. UTILITÁRIOS
# ==============================================================================

class EstoqueUtilsService:
    """
    Funções utilitárias para estoque.
    """
    
    @staticmethod
    def obter_saldo_total_produto(produto: Produto) -> Decimal:
        """
        Retorna saldo total de um produto (soma de todos os locais).
        """
        return SaldoEstoque.objects.filter(
            produto=produto
        ).aggregate(
            total=Coalesce(Sum('saldo_quantidade'), Decimal('0'))
        )['total']
    
    @staticmethod
    def obter_valor_total_estoque(local: Optional[LocalEstoque] = None) -> Decimal:
        """
        Retorna valor total do estoque.
        """
        query = SaldoEstoque.objects.all()
        
        if local:
            query = query.filter(local=local)
        
        # Calcular soma de (quantidade * custo_medio)
        total = query.aggregate(
            total=Coalesce(
                Sum(F('saldo_quantidade') * F('custo_medio'), output_field=DecimalField()),
                Decimal('0')
            )
        )['total']
        
        return total
    
    @staticmethod
    def obter_fornecedor_preferencial(produto: Produto) -> Optional[Pessoa]:
        """
        Retorna fornecedor preferencial de um produto.
        Prioridade: ProdutoFornecedor.preferencial > Produto.fornecedor
        """
        # Tentar ProdutoFornecedor preferencial
        try:
            pf = ProdutoFornecedor.objects.filter(
                produto=produto,
                preferencial=True,
                ativo=True
            ).first()
            
            if pf:
                return pf.fornecedor
        except:
            pass
        
        # Fallback: fornecedor padrão do produto
        if hasattr(produto, 'fornecedor'):
            return produto.fornecedor
        
        return None
    
    @staticmethod
    def gerar_proximo_numero_documento(tipo_documento: str, prefixo: str = '') -> str:
        """
        Gera próximo número de documento sequencial.
        
        Args:
            tipo_documento: Tipo de documento (NF_ENTRADA, REQ_SAIDA, etc)
            prefixo: Prefixo opcional (ex: '2025-')
        
        Returns:
            Número do documento
        """
        # Buscar último documento do tipo
        ultimo = MovimentoEstoque.objects.filter(
            documento_tipo=tipo_documento,
            documento__startswith=prefixo
        ).order_by('-documento').first()
        
        if ultimo:
            # Tentar extrair número
            try:
                numero_str = ultimo.documento.replace(prefixo, '')
                numero = int(numero_str) + 1
            except:
                numero = 1
        else:
            numero = 1
        
        return f"{prefixo}{numero:06d}"
