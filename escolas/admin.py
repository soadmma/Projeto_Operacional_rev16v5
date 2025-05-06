from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Escola, Supervisor, HistoricoBudget

class SupervisorResource(resources.ModelResource):
    class Meta:
        model = Supervisor
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'nome', 'email', 'telefone', 'ativo')

@admin.register(Supervisor)
class SupervisorAdmin(ImportExportModelAdmin):
    resource_class = SupervisorResource
    list_display = ('nome', 'email', 'telefone', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'email', 'telefone')
    list_editable = ('ativo',)

class EscolaResource(resources.ModelResource):
    class Meta:
        model = Escola
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'nome', 'codigo', 'lote', 'empresa', 'endereco', 'cep', 'cidade', 'estado', 
                  'telefone', 'email', 'supervisor', 'ativo')

@admin.register(Escola)
class EscolaAdmin(ImportExportModelAdmin):
    resource_class = EscolaResource
    list_display = ('nome', 'codigo', 'lote', 'empresa', 'budget', 'cidade', 'estado', 'supervisor', 'ativo')
    list_filter = ('ativo', 'estado', 'supervisor')
    search_fields = ('nome', 'codigo', 'endereco', 'cidade')
    list_editable = ('ativo',)
    autocomplete_fields = ['supervisor']
    
    def save_model(self, request, obj, form, change):
        # Passa o usuário para o método save do modelo
        obj.save(user=request.user)
    
    def save_related(self, request, form, formsets, change):
        # Implementação padrão
        super().save_related(request, form, formsets, change)

@admin.register(HistoricoBudget)
class HistoricoBudgetAdmin(admin.ModelAdmin):
    list_display = ('escola', 'valor_anterior', 'valor_novo', 'data_alteracao', 'usuario')
    list_filter = ('data_alteracao',)
    search_fields = ('escola__nome', 'usuario')
    date_hierarchy = 'data_alteracao'
    readonly_fields = ('escola', 'valor_anterior', 'valor_novo', 'data_alteracao', 'usuario')
