"""
Signals para sincronizar usuários com cadastro de Pessoas (vendedores)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario


@receiver(post_save, sender=PerfilUsuario)
def sync_vendedor_pessoa(sender, instance, created, **kwargs):
    """
    Quando PerfilUsuario.vendedor=True, cria/atualiza automaticamente
    o registro de Pessoa vinculado ao usuário
    """
    # Evitar importação circular
    from cadastros.models import Pessoa
    from usuarios.models import Empresa
    
    usuario = instance.usuario
    
    # Se marcou como vendedor
    if instance.vendedor:
        # Buscar empresa padrão (primeira empresa ou empresa ativa do usuário)
        empresa = None
        
        # Tentar pegar empresa do usuário via UsuarioEmpresa
        try:
            from usuarios.models import UsuarioEmpresa
            usuario_empresa = UsuarioEmpresa.objects.filter(
                usuario=usuario,
                ativo=True
            ).order_by('-empresa__matriz', 'data_inicio').first()
            
            if usuario_empresa:
                empresa = usuario_empresa.empresa
        except:
            pass
        
        # Se não encontrou, pegar primeira empresa ativa
        if not empresa:
            empresa = Empresa.objects.filter(ativa=True).first()
        
        if not empresa:
            print(f"⚠️ Nenhuma empresa ativa encontrada para vincular vendedor {usuario.username}")
            return
        
        # Buscar ou criar registro de Pessoa vinculado ao usuário
        pessoa, pessoa_created = Pessoa.objects.get_or_create(
            usuario=usuario,
            defaults={
                'empresa': empresa,
                'tipo': 'F',  # Pessoa Física (ajustar conforme necessário)
                'nome': usuario.get_full_name() or usuario.username,
                'vendedor': True,
                'email': usuario.email or '',
                'cpf_cnpj': '',  # Deve ser preenchido manualmente depois
            }
        )
        
        if pessoa_created:
            print(f"✓ Pessoa vendedor criada automaticamente: {pessoa.nome} (ID: {pessoa.id})")
        else:
            # Atualizar campos se já existe
            pessoa.vendedor = True
            pessoa.nome = usuario.get_full_name() or usuario.username
            if usuario.email and not pessoa.email:
                pessoa.email = usuario.email
            pessoa.save()
            print(f"✓ Pessoa vendedor atualizada: {pessoa.nome} (ID: {pessoa.id})")
    
    else:
        # Se desmarcou vendedor, atualizar Pessoa se existir
        try:
            from cadastros.models import Pessoa
            pessoa = Pessoa.objects.filter(usuario=usuario).first()
            if pessoa and pessoa.vendedor:
                pessoa.vendedor = False
                pessoa.save()
                print(f"✓ Flag vendedor removida de: {pessoa.nome}")
        except:
            pass


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria automaticamente PerfilUsuario quando um User é criado
    """
    if created:
        PerfilUsuario.objects.create(usuario=instance)
