"""
Managers customizados para filtro automático por empresa
Facilita queries seguras com isolamento de dados
"""
from django.db import models


class EmpresaQuerySet(models.QuerySet):
    """
    QuerySet customizado que adiciona métodos de filtro por empresa.
    
    Uso:
        # Filtrar por empresa específica
        Item.objects.for_empresa(request.empresa)
        
        # Ver todos (apenas admin)
        Item.objects.all_empresas()
    """
    
    def for_empresa(self, empresa):
        """
        Filtra registros da empresa especificada.
        
        Args:
            empresa: Instância de Empresa ou empresa_id
        
        Returns:
            QuerySet filtrado pela empresa
        """
        if isinstance(empresa, models.Model):
            return self.filter(empresa=empresa)
        else:
            # Assume que é um ID
            return self.filter(empresa_id=empresa)
    
    def all_empresas(self):
        """
        Retorna todos os registros sem filtro de empresa.
        
        ⚠️ ATENÇÃO: Use apenas em contextos administrativos!
        Para uso geral, SEMPRE use .for_empresa()
        
        Returns:
            QuerySet com todos os registros
        """
        return self.all()
    
    def ativas(self):
        """
        Filtra apenas registros ativos (se o model tiver campo 'ativo').
        
        Returns:
            QuerySet apenas com registros ativos
        """
        if hasattr(self.model, 'ativo'):
            return self.filter(ativo=True)
        return self
    
    def com_detalhes(self):
        """
        Otimiza query com select_related/prefetch_related comuns.
        Sobrescrever em managers específicos se necessário.
        
        Returns:
            QuerySet otimizado
        """
        return self.select_related('empresa')


class EmpresaManager(models.Manager):
    """
    Manager customizado que adiciona métodos de filtro por empresa.
    
    Uso no model:
        class MeuModel(models.Model):
            empresa = models.ForeignKey(Empresa, ...)
            
            objects = EmpresaManager()
            
        # Nas views:
        MeuModel.objects.for_empresa(request.empresa)
    """
    
    def get_queryset(self):
        """Retorna o QuerySet customizado"""
        return EmpresaQuerySet(self.model, using=self._db)
    
    def for_empresa(self, empresa):
        """
        Atalho para filtrar por empresa.
        
        Args:
            empresa: Instância de Empresa ou empresa_id
        
        Returns:
            QuerySet filtrado pela empresa
        """
        return self.get_queryset().for_empresa(empresa)
    
    def all_empresas(self):
        """
        Retorna tudo sem filtro - admin only.
        
        ⚠️ ATENÇÃO: Use com extremo cuidado!
        
        Returns:
            QuerySet com todos os registros
        """
        return self.get_queryset().all_empresas()
    
    def ativas(self):
        """
        Filtra apenas registros ativos.
        
        Returns:
            QuerySet apenas com registros ativos
        """
        return self.get_queryset().ativas()
    
    def com_detalhes(self):
        """
        Query otimizada com relacionamentos.
        
        Returns:
            QuerySet otimizado
        """
        return self.get_queryset().com_detalhes()


# ============================================
# MANAGERS ESPECIALIZADOS (EXEMPLOS)
# ============================================

class PessoaQuerySet(EmpresaQuerySet):
    """QuerySet especializado para Pessoa"""
    
    def clientes(self):
        """Retorna apenas clientes"""
        return self.filter(cliente=True)
    
    def fornecedores(self):
        """Retorna apenas fornecedores"""
        return self.filter(fornecedor=True)
    
    def funcionarios(self):
        """Retorna apenas funcionários"""
        return self.filter(funcionario=True)
    
    def com_detalhes(self):
        """Otimiza queries de Pessoa"""
        return self.select_related('empresa')


class PessoaManager(EmpresaManager):
    """Manager especializado para Pessoa"""
    
    def get_queryset(self):
        return PessoaQuerySet(self.model, using=self._db)
    
    def clientes(self):
        return self.get_queryset().clientes()
    
    def fornecedores(self):
        return self.get_queryset().fornecedores()
    
    def funcionarios(self):
        return self.get_queryset().funcionarios()


class ItemQuerySet(EmpresaQuerySet):
    """QuerySet especializado para Item de Estoque"""
    
    def produtos(self):
        """Retorna apenas produtos"""
        return self.filter(tipo_item='PRODUTO')
    
    def servicos(self):
        """Retorna apenas serviços"""
        return self.filter(tipo_item='SERVICO')
    
    def materiais(self):
        """Retorna apenas materiais"""
        return self.filter(tipo_item='MATERIAL')
    
    def com_estoque(self):
        """Retorna apenas itens que controlam estoque"""
        return self.filter(controla_estoque=True)
    
    def com_detalhes(self):
        """Otimiza queries de Item"""
        return self.select_related('empresa', 'unidade')


class ItemManager(EmpresaManager):
    """Manager especializado para Item"""
    
    def get_queryset(self):
        return ItemQuerySet(self.model, using=self._db)
    
    def produtos(self):
        return self.get_queryset().produtos()
    
    def servicos(self):
        return self.get_queryset().servicos()
    
    def materiais(self):
        return self.get_queryset().materiais()
    
    def com_estoque(self):
        return self.get_queryset().com_estoque()


class OrcamentoQuerySet(EmpresaQuerySet):
    """QuerySet especializado para Orçamento"""
    
    def pendentes(self):
        """Retorna orçamentos pendentes"""
        return self.filter(status='PENDENTE')
    
    def aprovados(self):
        """Retorna orçamentos aprovados"""
        return self.filter(status='APROVADO')
    
    def rejeitados(self):
        """Retorna orçamentos rejeitados"""
        return self.filter(status='REJEITADO')
    
    def com_detalhes(self):
        """Otimiza queries de Orçamento"""
        return self.select_related(
            'empresa',
            'cliente',
            'vendedor',
            'criado_por'
        ).prefetch_related('itens', 'parcelas')


class OrcamentoManager(EmpresaManager):
    """Manager especializado para Orçamento"""
    
    def get_queryset(self):
        return OrcamentoQuerySet(self.model, using=self._db)
    
    def pendentes(self):
        return self.get_queryset().pendentes()
    
    def aprovados(self):
        return self.get_queryset().aprovados()
    
    def rejeitados(self):
        return self.get_queryset().rejeitados()


# ============================================
# EXEMPLO DE USO
# ============================================

"""
# No model:
from usuarios.managers_empresa import EmpresaManager

class Pessoa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    nome = models.CharField(max_length=200)
    
    objects = EmpresaManager()

# Na view:
from usuarios.decorators import require_empresa

@login_required
@require_empresa
def listar_pessoas(request):
    # Automático: apenas pessoas da empresa ativa
    pessoas = Pessoa.objects.for_empresa(request.empresa)
    
    # Com filtros adicionais
    clientes_ativos = Pessoa.objects.for_empresa(request.empresa).filter(
        cliente=True,
        ativo=True
    )
    
    return render(request, 'pessoas/listar.html', {
        'pessoas': pessoas
    })
"""
