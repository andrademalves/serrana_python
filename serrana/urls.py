"""
URL configuration for serrana project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', usuarios_views.logout_view, name='logout'),
    
    # Apps principais
    path('', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),
    path('cadastros/', include(('cadastros.urls', 'cadastros'), namespace='cadastros')),
    path('estoque/', include(('estoque.urls', 'estoque'), namespace='estoque')),
    path('projetos/', include(('projetos.urls', 'projetos'), namespace='projetos')),
    path('financeiro/', include(('financeiro.urls', 'financeiro'), namespace='financeiro')),
    
    # Budget e Controle de Lucratividade
    path('financeiro/budget/', include('financeiro.urls_budget')),
    
    # Atalhos para contas a pagar/receber
    path('contas-receber/', RedirectView.as_view(pattern_name='financeiro:contas_receber', permanent=False)),
    path('contas-pagar/', RedirectView.as_view(pattern_name='financeiro:contas_pagar', permanent=False)),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
