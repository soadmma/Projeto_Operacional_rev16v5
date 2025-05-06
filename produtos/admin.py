from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Produto, Fornecedor
import xml.etree.ElementTree as ET

class ProdutoResource(resources.ModelResource):
    class Meta:
        model = Produto
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'nome', 'descricao', 'valor_unitario', 'unidade_medida', 'codigo', 'ativo')

@admin.register(Produto)
class ProdutoAdmin(ImportExportModelAdmin):
    resource_class = ProdutoResource
    list_display = ('nome', 'codigo', 'valor_unitario', 'unidade_medida', 'ativo')
    list_filter = ('ativo', 'unidade_medida')
    search_fields = ('nome', 'codigo', 'descricao')
    list_editable = ('valor_unitario', 'ativo')
    list_per_page = 20

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'telefone', 'email', 'tipo_fornecedor', 'ativo')
    search_fields = ('nome', 'cnpj', 'email')
    list_filter = ('ativo', 'tipo_fornecedor')
    ordering = ('nome',)

def processar_xml_nfe_massa(request):
    print("[IMPORTAÇÃO XML MASSA] INÍCIO DA VIEW")
    # ... resto do código ...
