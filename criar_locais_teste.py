from estoque.models import LocalEstoque
from django.contrib.auth.models import User

user = User.objects.first()

locais = [
    {'codigo': 'DEP01', 'descricao': 'Depósito Principal', 'endereco': 'Rua Principal, 100'},
    {'codigo': 'ALM01', 'descricao': 'Almoxarifado Geral', 'endereco': 'Área Industrial'},
    {'codigo': 'LOJ01', 'descricao': 'Loja - Showroom', 'endereco': 'Av. Comercial, 500'},
]

for dados in locais:
    local, created = LocalEstoque.objects.get_or_create(
        codigo=dados['codigo'],
        defaults={
            'descricao': dados['descricao'],
            'endereco': dados['endereco'],
            'ativo': True,
            'permite_saldo_negativo': False,
            'criado_por': user
        }
    )
    print(f"{'Criado' if created else 'Já existe'}: {local.codigo} - {local.descricao}")

print(f"\nTotal de locais: {LocalEstoque.objects.count()}")
