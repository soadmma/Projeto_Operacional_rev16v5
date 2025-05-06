from django.db.models import Count, Q
from escolas.models import Supervisor
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from pedidos.models import Pedido, ItemPedido
from escolas.models import Escola
from core.models import DadosVisaoGerencialCache
import json
import traceback

@login_required
def visao_gerencial_dados(request):
    """API para fornecer dados para o dashboard de visão gerencial"""
    try:
        # Obter parâmetros de filtro
        empresa_id = request.GET.get('empresa', 'all')
        contrato_id = request.GET.get('contrato', 'all')
        periodo = request.GET.get('periodo', 'all')
        
        # Dados para o gráfico de top supervisores
        top_supervisores = []
        for supervisor in Supervisor.objects.filter(ativo=True).annotate(
            num_escolas=Count('escolas', filter=Q(escolas__ativo=True))
        ).order_by('-num_escolas')[:5]:
            top_supervisores.append({
                'nome': supervisor.nome,
                'total_pedidos': supervisor.num_escolas
            })
        
        # Preparar resposta
        response_data = {
            'top_supervisores': top_supervisores,
            # ... outros dados ...
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ ERRO CRÍTICO na visão gerencial: {str(e)}")
        print(error_trace)
        
        return JsonResponse({
            'error': True,
            'message': str(e),
            'trace': error_trace,
            'error_type': type(e).__name__
        }, status=500) 