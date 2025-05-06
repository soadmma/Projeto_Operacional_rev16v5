from django.urls import path
from . import views

app_name = 'fornecedores'

urlpatterns = [
    path('', views.listar_fornecedores, name='listar_fornecedores'),
    path('criar/', views.criar_fornecedor, name='criar_fornecedor'),
    path('editar/<int:id>/', views.editar_fornecedor, name='editar_fornecedor'),
    path('excluir/<int:id>/', views.excluir_fornecedor, name='excluir_fornecedor'),
] 