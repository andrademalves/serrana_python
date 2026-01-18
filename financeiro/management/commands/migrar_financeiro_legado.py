"""
Migração do Sistema Legado de Financeiro
Converte dados da tabela antiga para o novo modelo
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth.models import User
from datetime import datetime, date
from decimal import Decimal

from financeiro.models import (
    TituloFinanceiro, ParcelaFinanceira, BaixaFinanceira,
    ContaFinanceira, Banco, FormaPagamento
)
from cadastros.models import Pessoa, PlanoConta


class Command(BaseCommand):
    help = 'Migra dados do financeiro legado para o novo sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar (teste)',
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Limita número de registros (para teste)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limite = options['limite']
        
        self.stdout.write(self.style.WARNING('Iniciando migração do financeiro legado...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhum dado será salvo'))
        
        # Busca dados da tabela legado
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    IDLANCAMENTO, IDCREDOR, DOCUMENTO, REFERENTE,
                    CONTA, SUBCONTA, EMISSAO, VENCIMENTO,
                    PARCELA, INTERVALO, VALORPARCELA, VALORTOTAL, VALORECEBER,
                    TIPOCONTA, IDPROJETO,
                    JUROS, DESCONTO, MULTA,
                    VALORPAGO, VALORRECEBIDO,
                    DATAPAGTO, DATABAIXA, BAIXADO, IDBANCO
                FROM financeiro
                ORDER BY IDLANCAMENTO
            """
            
            if limite:
                query += f" LIMIT {limite}"
            
            cursor.execute(query)
            registros = cursor.fetchall()
        
        self.stdout.write(f'Encontrados {len(registros)} registros no legado')
        
        # Obtém usuário padrão para auditoria
        try:
            usuario_sistema = User.objects.get(username='admin')
        except User.DoesNotExist:
            usuario_sistema = User.objects.first()
        
        # Mapeia banco padrão
        conta_padrao = self.obter_conta_padrao()
        forma_padrao = self.obter_forma_padrao()
        
        contador = {
            'titulos': 0,
            'parcelas': 0,
            'baixas': 0,
            'erros': 0
        }
        
        for reg in registros:
            try:
                with transaction.atomic():
                    # Desempacota registro
                    (id_lanc, id_credor, documento, referente,
                     conta, subconta, emissao_str, vencimento_str,
                     num_parcela, intervalo, valor_parcela, valor_total, valor_receber,
                     tipo_conta, id_projeto,
                     juros, desconto, multa,
                     valor_pago, valor_recebido,
                     data_pagto_str, data_baixa_str, baixado, id_banco) = reg
                    
                    # Converte tipo (TIPOCONTA define se é pagar ou receber)
                    if tipo_conta in ['PAGAR', 'A PAGAR']:
                        tipo = 'PAGAR'
                    elif tipo_conta in ['RECEBER', 'A RECEBER']:
                        tipo = 'RECEBER'
                    else:
                        self.stdout.write(self.style.WARNING(f'Tipo desconhecido: {tipo_conta} no ID {id_lanc}'))
                        continue
                    
                    # Converte datas (de varchar para date)
                    data_emissao = self.converter_data(emissao_str)
                    data_vencimento = self.converter_data(vencimento_str)
                    
                    if not data_emissao:
                        data_emissao = date.today()
                    if not data_vencimento:
                        data_vencimento = data_emissao
                    
                    # Mapeia pessoa (cliente/fornecedor)
                    pessoa = self.mapear_pessoa(id_credor)
                    if not pessoa:
                        self.stdout.write(self.style.WARNING(f'Pessoa não encontrada: {id_credor} no ID {id_lanc}'))
                        continue
                    
                    # Mapeia plano de contas
                    plano_conta = self.mapear_plano_conta(conta, subconta)
                    
                    # Mapeia centro de custo (projeto/obra)
                    centro_custo = self.mapear_centro_custo(id_projeto)
                    
                    # Valores
                    valor_total_dec = self.converter_decimal(valor_total or valor_parcela or 0)
                    valor_parcela_dec = self.converter_decimal(valor_parcela or valor_total or 0)
                    
                    if not documento:
                        documento = f'LEG-{id_lanc}'
                    
                    # Verifica se já existe título com este documento
                    titulo_existente = TituloFinanceiro.objects.filter(
                        numero_documento=documento,
                        tipo=tipo
                    ).first()
                    
                    if not titulo_existente:
                        # Cria título
                        if not dry_run:
                            titulo = TituloFinanceiro.objects.create(
                                tipo=tipo,
                                numero_documento=documento,
                                descricao=referente or f'Migração legado {id_lanc}',
                                pessoa=pessoa,
                                plano_conta=plano_conta,
                                centro_custo=centro_custo,
                                data_emissao=data_emissao,
                                valor_total=valor_total_dec,
                                num_parcelas=1,  # Legado tem 1 parcela por linha
                                intervalo_dias=intervalo or 30,
                                status='ABERTO',
                                criado_por=usuario_sistema
                            )
                            
                            # Remove parcelas auto-geradas
                            titulo.parcelas.all().delete()
                            
                            contador['titulos'] += 1
                        else:
                            titulo = None
                    else:
                        titulo = titulo_existente
                    
                    # Cria parcela
                    if not dry_run and titulo:
                        parcela = ParcelaFinanceira.objects.create(
                            titulo=titulo,
                            numero_parcela=num_parcela or 1,
                            data_vencimento=data_vencimento,
                            valor_original=valor_parcela_dec,
                            saldo_aberto=valor_parcela_dec,
                            status='ABERTO'
                        )
                        contador['parcelas'] += 1
                    else:
                        parcela = None
                    
                    # Se tinha pagamento/recebimento, cria baixa
                    if baixado and (valor_pago or valor_recebido):
                        data_pagamento = self.converter_data(data_pagto_str or data_baixa_str)
                        if not data_pagamento:
                            data_pagamento = date.today()
                        
                        valor_baixa = self.converter_decimal(valor_pago if tipo == 'PAGAR' else valor_recebido or 0)
                        
                        if valor_baixa > 0 and not dry_run and parcela:
                            # Mapeia conta financeira
                            conta_financeira = self.mapear_conta_financeira(id_banco) or conta_padrao
                            
                            baixa = BaixaFinanceira.objects.create(
                                parcela=parcela,
                                data_pagamento=data_pagamento,
                                conta_financeira=conta_financeira,
                                forma_pagamento=forma_padrao,
                                valor_principal=valor_baixa,
                                juros=self.converter_decimal(juros or 0),
                                multa=self.converter_decimal(multa or 0),
                                desconto=self.converter_decimal(desconto or 0),
                                taxas=Decimal('0.00'),
                                observacao=f'Migrado do legado ID {id_lanc}',
                                criado_por=usuario_sistema
                            )
                            contador['baixas'] += 1
                            
                            # Atualiza status da parcela
                            parcela.atualizar_status()
                    
                    # Atualiza status do título
                    if not dry_run and titulo:
                        titulo.atualizar_status()
                
            except Exception as e:
                contador['erros'] += 1
                self.stdout.write(self.style.ERROR(f'Erro no registro {id_lanc}: {str(e)}'))
                if not dry_run:
                    # Em modo real, continua mesmo com erros
                    continue
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n========== RESUMO DA MIGRAÇÃO =========='))
        self.stdout.write(f'Títulos criados: {contador["titulos"]}')
        self.stdout.write(f'Parcelas criadas: {contador["parcelas"]}')
        self.stdout.write(f'Baixas criadas: {contador["baixas"]}')
        self.stdout.write(f'Erros: {contador["erros"]}')
        self.stdout.write(self.style.SUCCESS('========================================\n'))
    
    def converter_data(self, data_str):
        """Converte string de data para date"""
        if not data_str:
            return None
        
        # Remove espaços
        data_str = str(data_str).strip()
        
        # Tenta vários formatos
        formatos = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
        ]
        
        for formato in formatos:
            try:
                return datetime.strptime(data_str, formato).date()
            except:
                continue
        
        return None
    
    def converter_decimal(self, valor):
        """Converte valor para Decimal"""
        try:
            return Decimal(str(valor))
        except:
            return Decimal('0.00')
    
    def mapear_pessoa(self, id_credor):
        """Mapeia ID do credor para Pessoa"""
        if not id_credor:
            return None
        
        try:
            return Pessoa.objects.get(pk=id_credor)
        except Pessoa.DoesNotExist:
            return None
    
    def mapear_plano_conta(self, conta, subconta):
        """Mapeia conta/subconta para PlanoConta"""
        # Tenta buscar por código
        codigo = f"{conta}.{subconta}" if subconta else conta
        
        if codigo:
            plano = PlanoConta.objects.filter(codigo=codigo).first()
            if plano:
                return plano
        
        # Busca primeiro ativo como fallback
        return PlanoConta.objects.filter(ativo=True).first()
    
    def mapear_centro_custo(self, id_projeto):
        """Mapeia projeto para CentroCusto"""
        if not id_projeto:
            return None
        
        from financeiro.models import CentroCusto
        
        # Tenta buscar centro de custo relacionado ao projeto
        try:
            return CentroCusto.objects.filter(projeto_id=id_projeto).first()
        except:
            return None
    
    def mapear_conta_financeira(self, id_banco):
        """Mapeia ID do banco para ContaFinanceira"""
        if not id_banco:
            return None
        
        try:
            return ContaFinanceira.objects.filter(pk=id_banco).first()
        except:
            return None
    
    def obter_conta_padrao(self):
        """Obtém conta financeira padrão (ou cria)"""
        conta = ContaFinanceira.objects.first()
        if not conta:
            # Cria conta padrão
            conta = ContaFinanceira.objects.create(
                nome='Caixa Geral',
                tipo='CAIXA',
                saldo_inicial=Decimal('0.00'),
                ativo=True
            )
        return conta
    
    def obter_forma_padrao(self):
        """Obtém forma de pagamento padrão (ou cria)"""
        forma = FormaPagamento.objects.first()
        if not forma:
            # Cria forma padrão
            forma = FormaPagamento.objects.create(
                codigo='DINHEIRO',
                descricao='Dinheiro',
                tipo='DINHEIRO',
                ativo=True
            )
        return forma
