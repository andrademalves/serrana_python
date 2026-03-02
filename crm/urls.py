from django.urls import path
from . import views
from . import views_dashboard

app_name = 'crm'

urlpatterns = [
    # Dashboard BI
    path('dashboard/', views_dashboard.dashboard_crm, name='dashboard'),
    
    # Kanban principal
    path('kanban/', views.kanban_view, name='kanban'),
    
    # Oportunidades
    path('oportunidades/<int:pk>/', views.oportunidade_detail, name='oportunidade_detail'),
    path('oportunidades/criar-rapida/', views.criar_oportunidade_rapida, name='criar_oportunidade_rapida'),
    path('oportunidades/<int:oportunidade_id>/criar-orcamento/', views.criar_orcamento_de_oportunidade, name='criar_orcamento'),
    path('oportunidades/<int:oportunidade_id>/desvincular-orcamento/', views.desvincular_orcamento, name='desvincular_orcamento'),
    path('oportunidades/<int:oportunidade_id>/trocar-responsavel/', views.trocar_responsavel, name='trocar_responsavel'),
    
    # AJAX: Drag & Drop
    path('api/atualizar-etapa/', views.atualizar_etapa_oportunidade, name='atualizar_etapa'),
    
    # AJAX: Atividades
    path('api/oportunidades/<int:oportunidade_id>/atividades/', views.criar_atividade, name='criar_atividade'),
    
    # AJAX: Alertas
    path('api/oportunidades/<int:oportunidade_id>/alertas/', views.criar_alerta, name='criar_alerta'),
    path('api/alertas/<int:alerta_id>/concluir/', views.concluir_alerta, name='concluir_alerta'),
    
    # Admin: Gerenciar Etapas
    path('admin/pipeline/<int:pipeline_id>/etapas/', views.gerenciar_etapas, name='gerenciar_etapas'),
    path('admin/pipeline/<int:pipeline_id>/etapas/criar/', views.criar_etapa, name='criar_etapa'),
    path('admin/etapas/<int:etapa_id>/deletar/', views.deletar_etapa, name='deletar_etapa'),
]
