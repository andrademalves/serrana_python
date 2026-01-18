from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'cadastros'

urlpatterns = [
    # Redireciona /cadastros/ para /cadastros/dashboard/
    path('', RedirectView.as_view(pattern_name='cadastros:dashboard_cadastros', permanent=False), name='cadastros_index'),
    
    # Dashboard
    path('dashboard/', views.dashboard_cadastros, name='dashboard_cadastros'),
    
    # Pessoas
    path('pessoas/', views.listar_pessoas, name='listar_pessoas'),
    path('pessoas/criar/', views.criar_pessoa, name='criar_pessoa'),
    path('pessoas/<int:pessoa_id>/editar/', views.editar_pessoa, name='editar_pessoa'),
    path('pessoas/<int:pessoa_id>/excluir/', views.excluir_pessoa, name='excluir_pessoa'),
    
    # API
    path('api/pessoa/<int:pessoa_id>/', views.get_pessoa_json, name='get_pessoa_json'),
    
    # Produtos
    path('produtos/', views.listar_produtos, name='listar_produtos'),
    path('produtos/criar/', views.criar_produto, name='criar_produto'),
    path('produtos/<int:produto_id>/editar/', views.editar_produto, name='editar_produto'),
    path('produtos/<int:produto_id>/excluir/', views.excluir_produto, name='excluir_produto'),
]
