# Sistema Serrana - Gestão Empresarial

Sistema de gestão empresarial desenvolvido em Django para a Serrana.

## Requisitos

- Python 3.8+
- MySQL 5.7+
- Django 6.0+

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install django mysqlclient pillow
```

4. Configure o banco de dados MySQL:
   - Crie o banco: `serrana_empresarial`
   - Usuário: `root`
   - Senha: `MBRHELP2023DEV@`

5. Execute as migrações:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Popule os dados iniciais:
```bash
python manage.py popular_dados
python manage.py popular_localizacao
```

7. Inicie o servidor:
```bash
python manage.py runserver
```

8. Acesse: http://localhost:8000
   - Usuário: admin
   - Senha: admin123

## Módulos

### Sistema (Usuários)
- Gerenciamento de usuários
- Controle de permissões por menu
- Perfis de usuário
- Sistema de módulos e menus hierárquicos

### Cadastros
- Pessoas (Clientes, Fornecedores, Funcionários)
- Produtos e Serviços
- Estados e Cidades

## Estrutura do Projeto

```
serrana/
├── manage.py
├── serrana/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── usuarios/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── management/
│       └── commands/
│           └── popular_dados.py
├── cadastros/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── management/
│       └── commands/
│           └── popular_localizacao.py
└── templates/
    ├── base.html
    └── registration/
        └── login.html
```

## Funcionalidades

- ✅ Sistema de login e autenticação
- ✅ Controle de permissões granular (visualizar, criar, editar, excluir)
- ✅ Gestão de usuários e perfis
- ✅ Cadastro de pessoas (CPF/CNPJ)
- ✅ Cadastro de produtos com controle de estoque
- ✅ Interface responsiva com Bootstrap 5
- ✅ Sistema de mensagens (alerts)

## Próximos Passos

- Implementar templates HTML para todas as views
- Adicionar validação de CPF/CNPJ
- Criar relatórios
- Implementar sistema de backup
- Adicionar logs de auditoria
