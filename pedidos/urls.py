from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('novo/', views.novo, name='novo'),
    path('editar/<int:pk>/', views.editar, name='editar'),
    path('<int:pk>/', views.detalhes, name='detalhes'),
    path('<int:pk>/atualizar-status/', views.atualizar_status, name='atualizar_status'),
    path('<int:pk>/excluir/', views.excluir, name='excluir'),
    path('<int:pk>/duplicar/', views.duplicar, name='duplicar'),
    path('<int:pk>/imprimir/', views.imprimir_pedido, name='imprimir_pedido'),
    path('<int:pk>/cancelar-recorrencia/', views.cancelar_recorrencia, name='cancelar_recorrencia'),
    path('exportar/', views.exportar, name='exportar'),
    path('relatorio/', views.relatorio, name='relatorio'),
    path('dashboard/', views.dashboard_relatorios, name='dashboard_relatorios'),
    path('central-relatorios/', views.central_relatorios, name='central_relatorios'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('buscar-recentes/', views.buscar_pedidos_recentes, name='buscar_pedidos_recentes'),
    path('gerar-recorrentes/', views.gerar_pedidos_recorrentes_manual, name='gerar_pedidos_recorrentes_manual'),
    # URLs para importação de XML
    path('importar-xml-nfe/', views.importar_xml_nfe, name='importar_xml_nfe'),
    path('<int:pedido_id>/importar-xml-nfe/', views.importar_xml_nfe, name='importar_xml_nfe'),
    path('selecionar-pedido-nfe/<str:chave_nfe>/', views.selecionar_pedido_nfe, name='selecionar_pedido_nfe'),
    # URL para visualizar detalhes de nota fiscal em página separada
    path('nota-fiscal/<int:nf_id>/', views.nota_fiscal_detalhes, name='nota_fiscal_detalhes'),
    # URL para reprocessar XML de nota fiscal
    path('nota-fiscal/<int:nf_id>/reprocessar/', views.reprocessar_itens_nota_fiscal, name='reprocessar_xml_nf'),
    # URL para excluir nota fiscal
    path('nota-fiscal/<int:nf_id>/excluir/', views.excluir_nota_fiscal, name='excluir_nota_fiscal'),
] 