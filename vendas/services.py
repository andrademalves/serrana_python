"""
SERVICES - MÓDULO ORÇAMENTOS E VENDAS
======================================

Regras de negócio:
- Validações de orçamentos
- Aprovação e geração automática de Obra + Títulos
- Cálculos comerciais
- Geração de propostas PDF

Autor: Sistema Comercial Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
import datetime
from typing import List, Dict, Tuple

# Imports dos modelos
from .models import (
    Orcamento, OrcamentoItem, OrcamentoHistorico,
    CondicaoPagamento, OrcamentoAnexo
)
from cadastros.models import Pessoa, Produto
from projetos.models import Obra
from financeiro.models import Titulo, CentroCusto, PlanoContas

User = get_user_model()


# ==============================================================================
# SERVIÇO PRINCIPAL DE ORÇAMENTOS
# ==============================================================================

class OrcamentoService:
    """
    Service com regras de negócio de orçamentos.
    """
    
    @staticmethod
    def validar_cliente_orcamento(cliente: Pessoa) -> Tuple[bool, List[str]]:
        """
        Valida se cliente tem dados mínimos para orçamento.
        
        Returns:
            (is_valid, erros)
        """
        erros = []
        
        if not cliente.cliente:
            erros.append("Pessoa não está marcada como Cliente")
        
        if not cliente.telefone and not cliente.celular:
            erros.append("Cliente sem telefone de contato")
        
        if not cliente.email:
            erros.append("Cliente sem email")
        
        if not cliente.endereco_logradouro:
            erros.append("Cliente sem endereço cadastrado")
        
        if cliente.tipo_pessoa == 'JURIDICA' and not cliente.cnpj:
            erros.append("Pessoa jurídica sem CNPJ")
        
        if cliente.tipo_pessoa == 'FISICA' and not cliente.cpf:
            erros.append("Pessoa física sem CPF")
        
        return (len(erros) == 0, erros)
    
    @staticmethod
    def criar_orcamento(
        cliente: Pessoa,
        vendedor: User,
        condicao_pagamento: CondicaoPagamento,
        criado_por: User,
        data_orcamento: datetime.date = None,
        validade_dias: int = 15,
        prazo_execucao_dias: int = 30,
        observacoes: str = ""
    ) -> Orcamento:
        """
        Cria novo orçamento validando dados.
        """
        # Validar cliente
        is_valid, erros = OrcamentoService.validar_cliente_orcamento(cliente)
        if not is_valid:
            raise ValidationError({
                'cliente': erros
            })
        
        # Criar orçamento
        data_orc = data_orcamento or datetime.date.today()
        validade = data_orc + datetime.timedelta(days=validade_dias)
        
        orcamento = Orcamento.objects.create(
            cliente=cliente,
            vendedor=vendedor,
            condicao_pagamento=condicao_pagamento,
            criado_por=criado_por,
            data_orcamento=data_orc,
            validade_ate=validade,
            prazo_execucao_dias=prazo_execucao_dias,
            observacoes=observacoes
        )
        
        # Registrar histórico
        OrcamentoHistorico.objects.create(
            orcamento=orcamento,
            status_novo='RASCUNHO',
            observacao='Orçamento criado',
            criado_por=criado_por
        )
        
        return orcamento
    
    @staticmethod
    def adicionar_item(
        orcamento: Orcamento,
        produto: Produto = None,
        descricao: str = "",
        quantidade: Decimal = Decimal('1.0'),
        unidade: str = "UN",
        preco_unitario: Decimal = Decimal('0.00'),
        custo_unitario_estimado: Decimal = Decimal('0.00'),
        largura: Decimal = None,
        altura: Decimal = None,
        cor: str = "",
        linha: str = "",
        vidro: str = "",
        acabamento: str = "",
        observacao_tecnica: str = ""
    ) -> OrcamentoItem:
        """
        Adiciona item ao orçamento.
        """
        if not orcamento.pode_editar:
            raise ValidationError(
                f"Orçamento {orcamento.numero} não pode ser editado (status: {orcamento.status})"
            )
        
        # Ordem
        ultimo = orcamento.itens.order_by('-ordem').first()
        ordem = (ultimo.ordem + 1) if ultimo else 1
        
        item = OrcamentoItem.objects.create(
            orcamento=orcamento,
            ordem=ordem,
            produto=produto,
            descricao=descricao or (produto.descricao if produto else ""),
            quantidade=quantidade,
            unidade=unidade,
            preco_unitario=preco_unitario,
            custo_unitario_estimado=custo_unitario_estimado,
            largura=largura,
            altura=altura,
            cor=cor,
            linha=linha,
            vidro=vidro,
            acabamento=acabamento,
            observacao_tecnica=observacao_tecnica
        )
        
        return item
    
    @staticmethod
    def mudar_status(
        orcamento: Orcamento,
        novo_status: str,
        usuario: User,
        observacao: str = ""
    ):
        """
        Muda status do orçamento com validações.
        """
        status_anterior = orcamento.status
        
        # Validar transição
        transicoes_permitidas = {
            'RASCUNHO': ['ENVIADO', 'CANCELADO'],
            'ENVIADO': ['NEGOCIACAO', 'APROVADO', 'REPROVADO', 'CANCELADO'],
            'NEGOCIACAO': ['ENVIADO', 'APROVADO', 'REPROVADO', 'CANCELADO'],
            'APROVADO': [],  # Final
            'REPROVADO': [],  # Final
            'CANCELADO': [],  # Final
        }
        
        if novo_status not in transicoes_permitidas.get(status_anterior, []):
            raise ValidationError(
                f"Transição inválida: {status_anterior} → {novo_status}"
            )
        
        # Atualizar
        orcamento.status = novo_status
        orcamento.save()
        
        # Registrar histórico
        OrcamentoHistorico.objects.create(
            orcamento=orcamento,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=observacao,
            criado_por=usuario
        )
    
    @staticmethod
    @transaction.atomic
    def aprovar_orcamento(
        orcamento: Orcamento,
        usuario: User,
        observacao: str = ""
    ) -> Obra:
        """
        Aprova orçamento e gera automaticamente:
        1. Obra (módulo projetos)
        2. Centro de Custo
        3. Títulos a Receber (módulo financeiro)
        
        TRANSAÇÃO ATÔMICA: Tudo ou nada!
        """
        # Validações
        if not orcamento.pode_aprovar:
            raise ValidationError(
                f"Orçamento {orcamento.numero} não pode ser aprovado. " +
                f"Status atual: {orcamento.status}, Vencido: {orcamento.esta_vencido}"
            )
        
        if orcamento.total <= 0:
            raise ValidationError("Orçamento sem valor total")
        
        if not orcamento.itens.exists():
            raise ValidationError("Orçamento sem itens")
        
        # 1. Criar OBRA
        obra = OrcamentoService.criar_obra_de_orcamento(orcamento, usuario)
        
        # 2. Criar CENTRO DE CUSTO para a obra
        centro_custo = CentroCusto.objects.create(
            nome=f"CC-{obra.codigo} - {obra.nome}",
            tipo='OBRA',
            ativo=True,
            observacoes=f"Centro de custo da obra {obra.codigo} (Orçamento {orcamento.numero})"
        )
        obra.centro_custo = centro_custo
        obra.save()
        
        # 3. Criar TÍTULOS A RECEBER
        titulos = OrcamentoService.gerar_titulos_receber(
            orcamento, obra, centro_custo, usuario
        )
        
        # 4. Atualizar orçamento
        orcamento.status = 'APROVADO'
        orcamento.obra_gerada = obra
        orcamento.data_aprovacao = timezone.now()
        orcamento.aprovado_por = usuario
        orcamento.save()
        
        # 5. Registrar histórico
        OrcamentoHistorico.objects.create(
            orcamento=orcamento,
            status_anterior=orcamento.status,
            status_novo='APROVADO',
            observacao=(
                f"{observacao}\n\n" +
                f"Obra criada: {obra.codigo}\n" +
                f"Centro de Custo: {centro_custo.nome}\n" +
                f"Títulos criados: {len(titulos)}"
            ),
            criado_por=usuario
        )
        
        return obra
    
    @staticmethod
    def criar_obra_de_orcamento(orcamento: Orcamento, usuario: User) -> Obra:
        """
        Cria Obra a partir do orçamento.
        """
        # Data de início (hoje) e fim (prazo de execução)
        data_inicio = datetime.date.today()
        data_fim = data_inicio + datetime.timedelta(days=orcamento.prazo_execucao_dias)
        
        # Criar obra
        obra = Obra.objects.create(
            nome=f"{orcamento.cliente.nome_razao} - {orcamento.numero}",
            cliente=orcamento.cliente,
            
            # Endereço (copiado do orçamento)
            endereco_logradouro=orcamento.endereco_execucao_logradouro,
            endereco_numero=orcamento.endereco_execucao_numero,
            endereco_complemento=orcamento.endereco_execucao_complemento,
            endereco_bairro=orcamento.endereco_execucao_bairro,
            endereco_cidade=orcamento.endereco_execucao_cidade,
            endereco_estado=orcamento.endereco_execucao_estado,
            endereco_cep=orcamento.endereco_execucao_cep,
            
            # Datas
            data_inicio=data_inicio,
            data_previsao_termino=data_fim,
            
            # Valores
            valor_orcado=orcamento.total,
            
            # Status
            status='PLANEJAMENTO',
            
            # Observações
            observacoes=(
                f"Obra gerada automaticamente do Orçamento {orcamento.numero}\n" +
                f"Cliente: {orcamento.cliente.nome_razao}\n" +
                f"Vendedor: {orcamento.vendedor.get_full_name()}\n" +
                f"Valor: R$ {orcamento.total:,.2f}\n" +
                f"Condição de Pagamento: {orcamento.condicao_pagamento.descricao}"
            ),
        )
        
        return obra
    
    @staticmethod
    def gerar_titulos_receber(
        orcamento: Orcamento,
        obra: Obra,
        centro_custo: CentroCusto,
        usuario: User
    ) -> List[Titulo]:
        """
        Gera títulos a receber com base na condição de pagamento.
        
        Suporta 4 tipos:
        1. À Vista: 1 título
        2. Parcelado: N parcelas iguais
        3. Entrada + Parcelas: 1 entrada + N parcelas
        4. Medição: Títulos com % configurados
        """
        titulos = []
        condicao = orcamento.condicao_pagamento
        
        # Plano de contas (receita)
        try:
            plano_contas = PlanoContas.objects.get(
                codigo='3.1.01',  # Receita de Vendas
            )
        except PlanoContas.DoesNotExist:
            # Criar se não existir
            plano_contas = PlanoContas.objects.create(
                codigo='3.1.01',
                nome='Receita de Vendas',
                tipo='RECEITA'
            )
        
        # À VISTA
        if condicao.tipo == 'A_VISTA':
            vencimento = datetime.date.today() + datetime.timedelta(
                days=condicao.primeira_parcela_dias
            )
            
            titulo = Titulo.objects.create(
                tipo='RECEBER',
                numero=f"{orcamento.numero}-1/1",
                pessoa=orcamento.cliente,
                plano_contas=plano_contas,
                centro_custo=centro_custo,
                valor_original=orcamento.total,
                data_emissao=datetime.date.today(),
                data_vencimento=vencimento,
                descricao=f"Orçamento {orcamento.numero} - À Vista",
                observacoes=f"Obra: {obra.codigo}",
            )
            titulos.append(titulo)
        
        # PARCELADO
        elif condicao.tipo == 'PARCELADO':
            valor_parcela = orcamento.total / condicao.numero_parcelas
            
            for i in range(1, condicao.numero_parcelas + 1):
                dias = condicao.primeira_parcela_dias + (
                    (i - 1) * condicao.intervalo_dias
                )
                vencimento = datetime.date.today() + datetime.timedelta(days=dias)
                
                # Última parcela ajusta diferença de arredondamento
                if i == condicao.numero_parcelas:
                    valor_parcela = orcamento.total - sum(t.valor_original for t in titulos)
                
                titulo = Titulo.objects.create(
                    tipo='RECEBER',
                    numero=f"{orcamento.numero}-{i}/{condicao.numero_parcelas}",
                    pessoa=orcamento.cliente,
                    plano_contas=plano_contas,
                    centro_custo=centro_custo,
                    valor_original=valor_parcela,
                    data_emissao=datetime.date.today(),
                    data_vencimento=vencimento,
                    descricao=f"Orçamento {orcamento.numero} - Parcela {i}/{condicao.numero_parcelas}",
                    observacoes=f"Obra: {obra.codigo}",
                )
                titulos.append(titulo)
        
        # ENTRADA + PARCELAS
        elif condicao.tipo == 'ENTRADA_PARCELAS':
            # Entrada
            valor_entrada = orcamento.total * (condicao.percentual_entrada / 100)
            vencimento_entrada = datetime.date.today() + datetime.timedelta(
                days=condicao.primeira_parcela_dias
            )
            
            titulo_entrada = Titulo.objects.create(
                tipo='RECEBER',
                numero=f"{orcamento.numero}-ENTRADA",
                pessoa=orcamento.cliente,
                plano_contas=plano_contas,
                centro_custo=centro_custo,
                valor_original=valor_entrada,
                data_emissao=datetime.date.today(),
                data_vencimento=vencimento_entrada,
                descricao=f"Orçamento {orcamento.numero} - Entrada ({condicao.percentual_entrada}%)",
                observacoes=f"Obra: {obra.codigo}",
            )
            titulos.append(titulo_entrada)
            
            # Parcelas do restante
            valor_restante = orcamento.total - valor_entrada
            valor_parcela = valor_restante / condicao.numero_parcelas
            
            for i in range(1, condicao.numero_parcelas + 1):
                dias = condicao.primeira_parcela_dias + (i * condicao.intervalo_dias)
                vencimento = datetime.date.today() + datetime.timedelta(days=dias)
                
                # Última parcela ajusta arredondamento
                if i == condicao.numero_parcelas:
                    valor_parcela = orcamento.total - sum(t.valor_original for t in titulos)
                
                titulo = Titulo.objects.create(
                    tipo='RECEBER',
                    numero=f"{orcamento.numero}-{i}/{condicao.numero_parcelas}",
                    pessoa=orcamento.cliente,
                    plano_contas=plano_contas,
                    centro_custo=centro_custo,
                    valor_original=valor_parcela,
                    data_emissao=datetime.date.today(),
                    data_vencimento=vencimento,
                    descricao=f"Orçamento {orcamento.numero} - Parcela {i}/{condicao.numero_parcelas}",
                    observacoes=f"Obra: {obra.codigo}",
                )
                titulos.append(titulo)
        
        # MEDIÇÃO
        elif condicao.tipo == 'MEDICAO':
            if not condicao.medicoes_percentuais:
                raise ValidationError("Condição de medição sem percentuais configurados")
            
            for i, percentual in enumerate(condicao.medicoes_percentuais, start=1):
                valor_medicao = orcamento.total * (Decimal(str(percentual)) / 100)
                
                dias = condicao.primeira_parcela_dias + (
                    (i - 1) * condicao.intervalo_dias
                )
                vencimento = datetime.date.today() + datetime.timedelta(days=dias)
                
                titulo = Titulo.objects.create(
                    tipo='RECEBER',
                    numero=f"{orcamento.numero}-MED{i}",
                    pessoa=orcamento.cliente,
                    plano_contas=plano_contas,
                    centro_custo=centro_custo,
                    valor_original=valor_medicao,
                    data_emissao=datetime.date.today(),
                    data_vencimento=vencimento,
                    descricao=f"Orçamento {orcamento.numero} - Medição {i} ({percentual}%)",
                    observacoes=f"Obra: {obra.codigo}",
                )
                titulos.append(titulo)
        
        return titulos
    
    @staticmethod
    def reprovar_orcamento(
        orcamento: Orcamento,
        usuario: User,
        motivo: str
    ):
        """
        Reprova orçamento.
        """
        if not orcamento.pode_reprovar:
            raise ValidationError(f"Orçamento {orcamento.numero} não pode ser reprovado")
        
        status_anterior = orcamento.status
        orcamento.status = 'REPROVADO'
        orcamento.motivo_reprovacao = motivo
        orcamento.save()
        
        # Registrar histórico
        OrcamentoHistorico.objects.create(
            orcamento=orcamento,
            status_anterior=status_anterior,
            status_novo='REPROVADO',
            observacao=f"Reprovado: {motivo}",
            criado_por=usuario
        )
    
    @staticmethod
    def calcular_margem_orcamento(orcamento: Orcamento) -> Dict:
        """
        Calcula margem detalhada do orçamento.
        """
        custo_total = sum(
            item.custo_unitario_estimado * item.quantidade
            for item in orcamento.itens.all()
            if item.custo_unitario_estimado
        ) or Decimal('0.00')
        
        lucro = orcamento.total - custo_total
        margem_percentual = (lucro / orcamento.total * 100) if orcamento.total > 0 else Decimal('0.00')
        
        return {
            'total_venda': orcamento.total,
            'custo_total': custo_total,
            'lucro': lucro,
            'margem_percentual': margem_percentual,
        }


# ==============================================================================
# SERVIÇO DE RELATÓRIOS COMERCIAIS
# ==============================================================================

class RelatorioComercialService:
    """
    Relatórios e análises comerciais.
    """
    
    @staticmethod
    def funil_vendas(data_inicio: datetime.date, data_fim: datetime.date) -> List[Dict]:
        """
        Funil de vendas: quantidade e valor por status.
        """
        from django.db.models import Count, Sum
        
        funil = Orcamento.objects.filter(
            data_orcamento__range=[data_inicio, data_fim]
        ).values('status').annotate(
            quantidade=Count('id'),
            valor_total=Sum('total')
        ).order_by('status')
        
        return list(funil)
    
    @staticmethod
    def taxa_conversao_vendedor(data_inicio: datetime.date, data_fim: datetime.date) -> List[Dict]:
        """
        Taxa de conversão por vendedor.
        """
        from django.db.models import Count, Q, Sum
        
        vendedores = User.objects.filter(
            orcamentos_vendidos__data_orcamento__range=[data_inicio, data_fim]
        ).annotate(
            total_orcamentos=Count('orcamentos_vendidos'),
            total_aprovados=Count(
                'orcamentos_vendidos',
                filter=Q(orcamentos_vendidos__status='APROVADO')
            ),
            valor_aprovados=Sum(
                'orcamentos_vendidos__total',
                filter=Q(orcamentos_vendidos__status='APROVADO')
            )
        ).values(
            'id', 'username', 'first_name', 'last_name',
            'total_orcamentos', 'total_aprovados', 'valor_aprovados'
        )
        
        # Calcular taxa de conversão
        resultado = []
        for vendedor in vendedores:
            taxa = (
                (vendedor['total_aprovados'] / vendedor['total_orcamentos'] * 100)
                if vendedor['total_orcamentos'] > 0 else 0
            )
            vendedor['taxa_conversao'] = round(taxa, 2)
            resultado.append(vendedor)
        
        return resultado
    
    @staticmethod
    def backlog_obras(data_referencia: datetime.date = None) -> List[Dict]:
        """
        Backlog de obras: orçamentos aprovados ainda não faturados.
        """
        data_ref = data_referencia or datetime.date.today()
        
        orcamentos = Orcamento.objects.filter(
            status='APROVADO',
            data_aprovacao__lte=data_ref
        ).select_related('cliente', 'vendedor', 'obra_gerada').values(
            'numero', 'cliente__nome_razao', 'vendedor__username',
            'data_aprovacao', 'total', 'obra_gerada__codigo', 
            'obra_gerada__status'
        )
        
        return list(orcamentos)
