from django.urls import path
from . import views

app_name = 'orcamentos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('novo/', views.novo, name='novo'),
    path('importar/', views.importar, name='importar'),
    path('download-modelo/', views.download_modelo, name='download_modelo'),
    path('<int:orcamento_id>/', views.detalhe, name='detalhe'),
    path('<int:orcamento_id>/aprovar/', views.aprovar_orcamento, name='aprovar'),
    path('<int:orcamento_id>/rejeitar/', views.rejeitar, name='rejeitar'),
    path('<int:orcamento_id>/editar/', views.editar, name='editar'),
    path('<int:orcamento_id>/excluir/', views.excluir, name='excluir'),
    path('<int:orcamento_id>/exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('<int:orcamento_id>/exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('comparar/', views.comparar, name='comparar'),
    path('definir-melhor/', views.definir_melhor, name='definir_melhor'),
    path('agrupar-orcamentos/', views.agrupar_orcamentos, name='agrupar_orcamentos'),
    path('<int:orcamento_id>/gerar-pedido/', views.gerar_pedido, name='gerar_pedido'),
    # Outras urls serão adicionadas depois
] 