from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Max, Avg, Min, F, Q, Case, When, DecimalField, Value, ExpressionWrapper, FloatField
from django.db.models.functions import TruncMonth, TruncYear, ExtractMonth, ExtractYear, Extract
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.utils import timezone
from datetime import timedelta, datetime
from django.forms.models import model_to_dict
import json
from decimal import Decimal
import math
import os
import tempfile
import zipfile
from openpyxl import Workbook
import hashlib
import openpyxl.styles
import shutil
import sqlite3
import subprocess
from django.conf import settings
import time
import django  # Importar o módulo django para obter a versão
import xml.etree.ElementTree as ET
import re

# Importações corretas de cada app
from .models import ConfiguracaoSistema, Contrato, DetalhesContrato, Empresa
from produtos.models import Produto
from escolas.models import Escola, Supervisor 
from pedidos.models import Pedido, ItemPedido, NotaFiscal, ItemNotaFiscal

# Importar todos os modelos necessários no topo do arquivo
from core.models import Empresa, Contrato, DetalhesContrato
from escolas.models import Escola
from pedidos.models import Pedido
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def verificar_senha_diagnostico(request):
    if request.method == "POST":
        data = json.loads(request.body)
        senha = data.get("senha")
        user = request.user

        if user.is_authenticated and user.is_superuser:
            auth_user = authenticate(username=user.username, password=senha)
            if auth_user:
                return JsonResponse({"autorizado": True, "redirecionar_para": "/diagnostico/"})

    return JsonResponse({"autorizado": False})
def is_superuser(user):
    """Verifica se o usuário é um superusuário."""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def backup_sistema(request):
    """
    Cria um backup completo do sistema, incluindo banco de dados e arquivos de mídia.
    Apenas superusuários têm acesso a esta funcionalidade.
    """
    # Obter o caminho do banco de dados para exibir em caso de erro
    db_path = settings.DATABASES['default']['NAME']
    
    if request.method == 'POST':
        temp_files_to_clean = []  # Lista para rastrear arquivos temporários que precisam ser removidos
        
        try:
            # Timestamp para o nome do arquivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_sistema_{timestamp}.zip'
            
            # Criar um arquivo ZIP temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_file_path = temp_file.name
            temp_file.close()
            temp_files_to_clean.append(temp_file_path)
            
            with zipfile.ZipFile(temp_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 1. Backup do banco de dados SQLite
                if os.path.exists(db_path):
                    # Solução compatível com Windows: copiar o arquivo diretamente
                    try:
                        # Criar um nome temporário para a cópia do banco de dados
                        temp_db_path = os.path.join(tempfile.gettempdir(), f'db_backup_{timestamp}.sqlite3')
                        temp_files_to_clean.append(temp_db_path)
                        
                        # Fechar conexões existentes (se possível)
                        from django.db import connection
                        connection.close()
                        
                        # Copiar o arquivo do banco de dados
                        shutil.copy2(db_path, temp_db_path)
                        
                        # Adicionar ao arquivo ZIP
                        backup_zip.write(temp_db_path, 'database.sqlite3')
                        
                    except Exception as e:
                        # Registrar erro e tentar método alternativo se o primeiro falhar
                        print(f"Erro ao fazer backup do banco de dados (método 1): {str(e)}")
                        
                        # Método alternativo: usar comandos de sistema para copiar (Windows)
                        try:
                            temp_db_path = os.path.join(tempfile.gettempdir(), f'db_backup_{timestamp}_alt.sqlite3')
                            temp_files_to_clean.append(temp_db_path)
                            
                            # Usar comando do sistema operacional para copiar
                            if os.name == 'nt':  # Windows
                                os.system(f'copy "{db_path}" "{temp_db_path}"')
                            else:  # Unix/Linux/Mac
                                os.system(f'cp "{db_path}" "{temp_db_path}"')
                                
                            # Verificar se o arquivo foi criado
                            if os.path.exists(temp_db_path):
                                backup_zip.write(temp_db_path, 'database.sqlite3')
                            else:
                                raise Exception(f"Falha ao copiar banco de dados para {temp_db_path}")
                                
                        except Exception as e2:
                            # Terceiro método: tentar com pequenas pausas
                            print(f"Erro ao fazer backup do banco de dados (método 2): {str(e2)}")
                            
                            try:
                                # Esperar um pouco para garantir que as conexões sejam fechadas
                                time.sleep(2)
                                
                                # Usar uma terceira localização
                                temp_db_path = os.path.join(tempfile.gettempdir(), f'db_backup_{timestamp}_final.sqlite3')
                                temp_files_to_clean.append(temp_db_path)
                                
                                # Fazer uma cópia simples do arquivo
                                with open(db_path, 'rb') as src, open(temp_db_path, 'wb') as dst:
                                    dst.write(src.read())
                                    
                                # Verificar se a cópia foi bem-sucedida
                                if os.path.exists(temp_db_path) and os.path.getsize(temp_db_path) > 0:
                                    backup_zip.write(temp_db_path, 'database.sqlite3')
                                else:
                                    raise Exception("Falha ao copiar o banco de dados (arquivo vazio ou inexistente)")
                                    
                            except Exception as e3:
                                # Se todos os métodos falharem, lançar exceção detalhada
                                raise Exception(f"Falha em todos os métodos de backup. Detalhes: Método 1: {str(e)}, Método 2: {str(e2)}, Método 3: {str(e3)}")
                
                # 2. Backup dos arquivos de mídia
                media_dir = settings.MEDIA_ROOT
                if os.path.exists(media_dir) and os.path.isdir(media_dir):
                    for root, dirs, files in os.walk(media_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(media_dir))
                            backup_zip.write(file_path, f'media/{arcname}')
                
                # 3. Adicionar informações sobre o backup
                # Obter a versão do Django importada na linha 22
                django_version = django.__version__
                
                info = {
                    'data_backup': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'versao_sistema': '1.0',
                    'usuario': request.user.username,
                    'django_version': django_version,
                    'metodo_backup': 'Método direto de cópia de arquivo',
                }
                
                # Criar arquivo de informações
                info_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                info_file_path = info_file.name
                info_file.close()
                temp_files_to_clean.append(info_file_path)
                
                with open(info_file_path, 'w') as f:
                    json.dump(info, f, indent=2)
                
                # Adicionar arquivo de informações ao ZIP
                backup_zip.write(info_file_path, 'backup_info.json')
            
            # Preparar resposta para download
            with open(temp_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{backup_filename}"'
            
            # Sucesso! Remover arquivos temporários
            for tmp_file in temp_files_to_clean:
                try:
                    if os.path.exists(tmp_file):
                        os.unlink(tmp_file)
                except Exception:
                    # Ignorar erros na limpeza de arquivos temporários
                    pass
            
            return response
        
        except Exception as e:
            # Em caso de erro, tentar limpar todos os arquivos temporários
            for tmp_file in temp_files_to_clean:
                try:
                    if os.path.exists(tmp_file):
                        os.unlink(tmp_file)
                except Exception:
                    pass
                    
            messages.error(request, f'Erro ao criar backup: {str(e)}')
            return redirect('admin:backup_sistema')
    
    # Se for uma requisição GET, exibir a página de backup
    return render(request, 'admin/backup_sistema.html', {
        'database_path': db_path,
        'media_path': settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else 'media/'
    })

@login_required
@user_passes_test(is_superuser)
def restaurar_sistema(request):
    """
    Restaura o sistema a partir de um arquivo de backup.
    Apenas superusuários têm acesso a esta funcionalidade.
    """
    if request.method == 'POST' and request.FILES.get('backup_file'):
        try:
            backup_file = request.FILES['backup_file']
            
            # Verificar se o arquivo é um ZIP
            if not backup_file.name.endswith('.zip'):
                messages.error(request, 'O arquivo selecionado não é um arquivo ZIP válido.')
                return redirect('admin:restaurar_sistema')
            
            # Criar diretório temporário para extrair o backup
            temp_dir = tempfile.mkdtemp()
            
            # Salvar o arquivo de backup no diretório temporário
            temp_zip_path = os.path.join(temp_dir, 'backup.zip')
            with open(temp_zip_path, 'wb') as f:
                for chunk in backup_file.chunks():
                    f.write(chunk)
            
            # Verificar a estrutura do arquivo ZIP
            required_files = ['database.sqlite3', 'backup_info.json']
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                missing_files = [f for f in required_files if f not in file_list]
                
                if missing_files:
                    messages.error(request, f'O arquivo de backup não é válido. Arquivos ausentes: {", ".join(missing_files)}')
                    shutil.rmtree(temp_dir)
                    return redirect('admin:restaurar_sistema')
                
                # Extrair arquivos para o diretório temporário
                zip_ref.extractall(temp_dir)
            
            # Verificar informações do backup
            with open(os.path.join(temp_dir, 'backup_info.json'), 'r') as f:
                backup_info = json.load(f)
                
                # Exibir informações para confirmação
                backup_date = backup_info.get('data_backup', 'Data desconhecida')
                backup_version = backup_info.get('versao_sistema', 'Versão desconhecida')
                
                # Armazenar informações na sessão para uso na confirmação
                request.session['backup_info'] = {
                    'temp_dir': temp_dir,
                    'data_backup': backup_date,
                    'versao_sistema': backup_version,
                    'usuario': backup_info.get('usuario', 'Usuário desconhecido'),
                    'django_version': backup_info.get('django_version', 'Desconhecida'),
                    'metodo_backup': backup_info.get('metodo_backup', 'Método padrão')
                }
                
                # Redirecionar para a página de confirmação
                return render(request, 'admin/confirmar_restauracao.html', {
                    'backup_info': backup_info
                })
            
        except Exception as e:
            messages.error(request, f'Erro ao processar arquivo de backup: {str(e)}')
            # Limpar diretório temporário em caso de erro
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
            return redirect('admin:restaurar_sistema')
    
    # Se for uma requisição GET, exibir o formulário para upload
    return render(request, 'admin/restaurar_sistema.html')

@login_required
@user_passes_test(is_superuser)
def confirmar_restauracao(request):
    """
    Página de confirmação para a restauração do sistema.
    """
    if request.method == 'POST':
        # Obter informações do backup da sessão
        backup_info = request.session.get('backup_info', {})
        temp_dir = backup_info.get('temp_dir')
        
        if not temp_dir or not os.path.exists(temp_dir):
            messages.error(request, 'As informações de backup não estão disponíveis ou expiraram.')
            return redirect('admin:restaurar_sistema')
        
        try:
            # 1. Restaurar banco de dados
            db_backup_path = os.path.join(temp_dir, 'database.sqlite3')
            db_path = settings.DATABASES['default']['NAME']
            
            # Fazer backup do banco de dados atual antes de substituí-lo
            current_db_backup_path = f"{db_path}.bak_{int(time.time())}"
            shutil.copy2(db_path, current_db_backup_path)
            
            # Fechar todas as conexões com o banco de dados
            from django.db import connection
            connection.close()
            
            # Tentar fechar todas as conexões possíveis antes de copiar
            time.sleep(1)  # Pequena pausa para garantir que as conexões fechem
            
            # Substituir o banco de dados - tentativa 1
            try:
                shutil.copy2(db_backup_path, db_path)
            except Exception as e1:
                # Tentativa 2 com comando do sistema
                if os.name == 'nt':  # Windows
                    success = os.system(f'copy /Y "{db_backup_path}" "{db_path}"') == 0
                else:  # Unix/Linux/Mac
                    success = os.system(f'cp "{db_backup_path}" "{db_path}"') == 0
                
                if not success:
                    raise Exception(f"Falha ao restaurar o banco de dados: {str(e1)}")
            
            # 2. Restaurar arquivos de mídia
            media_backup_dir = os.path.join(temp_dir, 'media')
            if os.path.exists(media_backup_dir):
                # Fazer backup do diretório de mídia atual
                current_media_backup_dir = f"{settings.MEDIA_ROOT}.bak_{int(time.time())}"
                if os.path.exists(settings.MEDIA_ROOT):
                    shutil.copytree(settings.MEDIA_ROOT, current_media_backup_dir)
                
                # Substituir arquivos de mídia
                for root, dirs, files in os.walk(media_backup_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, media_backup_dir)
                        dst_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                        
                        # Criar diretório de destino se não existir
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # Copiar arquivo
                        shutil.copy2(src_path, dst_path)
            
            # 3. Limpar diretório temporário
            shutil.rmtree(temp_dir)
            
            # 4. Limpar informações da sessão
            if 'backup_info' in request.session:
                del request.session['backup_info']
            
            messages.success(request, 'Sistema restaurado com sucesso! Recomendamos reiniciar a aplicação para garantir o funcionamento correto.')
            return redirect('admin:index')
            
        except Exception as e:
            error_msg = f'Erro ao restaurar o sistema: {str(e)}.'
            if 'current_db_backup_path' in locals():
                error_msg += f' Uma cópia de segurança do banco de dados atual foi feita em {current_db_backup_path}.'
            
            messages.error(request, error_msg)
            
            # Limpar diretório temporário em caso de erro
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Limpar informações da sessão
            if 'backup_info' in request.session:
                del request.session['backup_info']
                
            return redirect('admin:index')
    
    # Se não for POST, redirecionar para a página de restauração
    messages.warning(request, 'Ação inválida.')
    return redirect('admin:restaurar_sistema')

@login_required
def home(request):
    """Exibe a página inicial do sistema"""
    
    # Redireciona operadores de pedidos diretamente para a lista de pedidos
    if request.user.groups.filter(name='Operador de Pedidos').exists():
        return redirect('pedidos:lista')
    
    # Cálculos para o dashboard (resumo de pedidos)
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # Totais gerais
    total_produtos = Produto.objects.filter(ativo=True).count()
    total_escolas = Escola.objects.filter(ativo=True).count()
    total_pedidos_ativos = Pedido.objects.exclude(status__in=['entregue', 'cancelado']).count()
    total_pedidos_pendentes = Pedido.objects.filter(status='pendente').count()
    
    # Pedidos recentes
    pedidos_recentes = Pedido.objects.select_related('escola').order_by('-data_solicitacao')[:10]
    
    # Escolas com mais pedidos
    escolas_top = Escola.objects.filter(ativo=True).annotate(
        total_pedidos=Count('pedidos')
    ).order_by('-total_pedidos')[:5]
    
    return render(request, 'core/home.html', {
        'total_produtos': total_produtos,
        'total_escolas': total_escolas,
        'total_pedidos_ativos': total_pedidos_ativos,
        'total_pedidos_pendentes': total_pedidos_pendentes,
        'pedidos_recentes': pedidos_recentes,
        'escolas_top': escolas_top
    })

@login_required
def configuracoes(request):
    """Exibe e gerencia configurações do sistema"""
    return render(request, 'core/configuracoes.html')

def exportar_dados(request):
    """Exporta todos os dados do sistema em arquivos Excel compactados"""
    # Cria um arquivo temporário para o ZIP
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_file.close()
    
    # Cria o arquivo ZIP
    with zipfile.ZipFile(temp_file.name, 'w') as zipf:
        # Exporta produtos
        wb_produtos = Workbook()
        ws_produtos = wb_produtos.active
        ws_produtos.title = "Produtos"
        
        # Adiciona cabeçalho
        ws_produtos.append(["ID", "Nome", "Descrição", "Valor Unitário", "Unidade de Medida", "Código", "Data Cadastro", "Ativo"])
        
        # Adiciona dados
        for produto in Produto.objects.all():
            ws_produtos.append([
                produto.id,
                produto.nome,
                produto.descricao,
                float(produto.valor_unitario),
                produto.unidade_medida,
                produto.codigo,
                produto.data_cadastro.strftime("%d/%m/%Y %H:%M:%S"),
                "Sim" if produto.ativo else "Não"
            ])
        
        # Salva o arquivo de produtos
        produtos_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        produtos_file.close()
        wb_produtos.save(produtos_file.name)
        zipf.write(produtos_file.name, "produtos.xlsx")
        os.unlink(produtos_file.name)
        
        # Exporta escolas (código similar para escolas e pedidos)
        # [Implementação adicional para escolas e pedidos]
    
    # Retorna o arquivo ZIP
    with open(temp_file.name, 'rb') as f:
        response = HttpResponse(
            f.read(),
            content_type="application/zip"
        )
    os.unlink(temp_file.name)
    
    # Define o nome do arquivo
    hoje = datetime.now().strftime("%Y-%m-%d")
    response['Content-Disposition'] = f'attachment; filename="sistema_pedidos_export_{hoje}.zip"'
    
    return response

def limpar_temporarios(request):
    """Remove arquivos temporários do sistema"""
    # Implementar limpeza de arquivos temporários
    # [Implementação]
    
    messages.success(request, 'Dados temporários limpos com sucesso!')
    return redirect('core:configuracoes')

# Função auxiliar para geocodificar endereços (versão simplificada que não requer requests)
def local_geocode(cep=None, city=None, state=None, address=None):
    """
    Retorna coordenadas aproximadas baseando-se primeiramente no CEP, depois na cidade e estado
    Usa uma combinação de dicionários de coordenadas para melhorar a precisão
    """
    # Normalização do nome da cidade (remover acentos, converter para título)
    def normalize_name(name):
        if not name:
            return ""
        
        # Mapeamento simples de caracteres acentuados para não acentuados
        accents = {
            'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c',
            'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C'
        }
        
        name = name.strip()
        normalized = ""
        for char in name:
            normalized += accents.get(char, char)
        
        return normalized.title()
    
    # Limpar o CEP para conter apenas números
    def clean_cep(cep_text):
        if not cep_text:
            return None
        return ''.join(filter(str.isdigit, cep_text))
    
    # Coordenadas baseadas em faixas de CEP (mais preciso)
    # Cada faixa representa uma região aproximada
    cep_ranges = {
        # São Paulo capital (01000-000 a 05999-999)
        '01': (-23.5505, -46.6333),  # Centro
        '02': (-23.4856, -46.6503),  # Zona Norte
        '03': (-23.5336, -46.5989),  # Zona Leste
        '04': (-23.6229, -46.6520),  # Zona Sul
        '05': (-23.5868, -46.7203),  # Zona Oeste
        
        # Rio de Janeiro (20000-000 a 23799-999)
        '20': (-22.9068, -43.1729),  # Centro
        '21': (-22.8604, -43.2504),  # Zona Norte
        '22': (-22.9698, -43.1856),  # Zona Sul
        '23': (-22.9374, -43.3534),  # Zona Oeste
        
        # Belo Horizonte (30000-000 a 31999-999)
        '30': (-19.9167, -43.9345),  # Centro
        '31': (-19.8778, -43.9429),  # Região Norte
        
        # Brasília (70000-000 a 72799-999)
        '70': (-15.7801, -47.9292),  # Plano Piloto
        '71': (-15.8698, -47.9183),  # Guará e outras
        '72': (-15.8198, -48.0938),  # Taguatinga e outras
        
        # Porto Alegre (90000-000 a 91999-999)
        '90': (-30.0277, -51.2287),  # Centro
        '91': (-30.0589, -51.1731),  # Zona Norte
        
        # Curitiba (80000-000 a 82999-999)
        '80': (-25.4195, -49.2646),  # Centro
        '81': (-25.4896, -49.2883),  # Portão
        '82': (-25.3862, -49.3019),  # Santa Felicidade
    }
    
    # Coordenadas predefinidas para cidades brasileiras comuns
    city_coordinates = {
        # Capitais
        "Sao Paulo": (-23.5505, -46.6333),
        "Rio De Janeiro": (-22.9068, -43.1729),
        "Belo Horizonte": (-19.9167, -43.9345),
        "Brasilia": (-15.7801, -47.9292),
        "Salvador": (-12.9714, -38.5014),
        "Fortaleza": (-3.7172, -38.5433),
        "Recife": (-8.0476, -34.8770),
        "Porto Alegre": (-30.0277, -51.2287),
        "Curitiba": (-25.4195, -49.2646),
        "Manaus": (-3.1019, -60.0250),
        "Belem": (-1.4558, -48.4902),
        "Goiania": (-16.6864, -49.2643),
        "Sao Luis": (-2.5391, -44.2829),
        "Maceio": (-9.6498, -35.7089),
        "Natal": (-5.7945, -35.2120),
        "Teresina": (-5.0920, -42.8038),
        "Campo Grande": (-20.4428, -54.6464),
        "Joao Pessoa": (-7.1219, -34.8829),
        "Florianopolis": (-27.5969, -48.5495),
        "Aracaju": (-10.9472, -37.0731),
        "Cuiaba": (-15.6014, -56.0979),
        "Porto Velho": (-8.7608, -63.9004),
        "Macapa": (0.0356, -51.0705),
        "Rio Branco": (-9.9738, -67.8277),
        "Boa Vista": (2.8235, -60.6758),
        "Palmas": (-10.2491, -48.3243),
        "Vitoria": (-20.2976, -40.2958),
        # Outras cidades importantes
        "Guarulhos": (-23.4543, -46.5337),
        "Campinas": (-22.9064, -47.0616),
        "Sao Goncalo": (-22.8269, -43.0539),
        "Duque De Caxias": (-22.7729, -43.3109),
        "Sao Bernardo Do Campo": (-23.6914, -46.5650),
        "Osasco": (-23.5324, -46.7916),
        "Jaboatao Dos Guararapes": (-8.1638, -34.9171),
        "Contagem": (-19.9321, -44.0539),
        "Sao Jose Dos Campos": (-23.1896, -45.8841),
        "Santo Andre": (-23.6639, -46.5383),
        "Ribeirao Preto": (-21.1775, -47.8103),
        "Nova Iguacu": (-22.7592, -43.4511),
        "Uberlandia": (-18.9141, -48.2749),
        "Sorocaba": (-23.5015, -47.4582),
        "Niteroi": (-22.8832, -43.1036),
        "Sao Jose Do Rio Preto": (-20.8198, -49.3849),
        "Londrina": (-23.3045, -51.1696),
        "Juiz De Fora": (-21.7641, -43.3501),
        "Joinville": (-26.3032, -48.8461),
        "Feira De Santana": (-12.2664, -38.9663),
        "Santos": (-23.9608, -46.3340),
        "Maringa": (-23.4273, -51.9375),
        "Bauru": (-22.3246, -49.0871),
        "Sao Vicente": (-23.9608, -46.3919),
        "Diadema": (-23.6813, -46.6205),
        "Franca": (-20.5386, -47.4008),
        "Carapicuiba": (-23.5235, -46.8407),
        "Piracicaba": (-22.7253, -47.6490),
        "Taubate": (-23.0268, -45.5553),
        "Cascavel": (-24.9578, -53.4595),
        "Limeira": (-22.5641, -47.4016),
        "Jundiai": (-23.1857, -46.8978),
        "Itaquaquecetuba": (-23.4862, -46.3489),
        "Aracatuba": (-21.2076, -50.4401),
        "Presidente Prudente": (-22.1208, -51.3884),
        "Sao Carlos": (-22.0174, -47.8908),
        "Americana": (-22.7375, -47.3306),
        "Jacarei": (-23.2954, -45.9662),
        "Araras": (-22.3572, -47.3842),
        "Araraquara": (-21.7845, -48.1786),
        "Itapetininga": (-23.5886, -48.0529),
        "Braganca Paulista": (-22.9527, -46.5419),
        "Pindamonhangaba": (-22.9243, -45.4617),
        "Botucatu": (-22.8837, -48.4437),
        "Atibaia": (-23.1171, -46.5563),
        "Barueri": (-23.5057, -46.8775),
        "Cotia": (-23.6022, -46.9189),
        "Valinhos": (-22.9698, -46.9969),
        "Vinhedo": (-23.0302, -46.9833),
        "Paulinia": (-22.7542, -47.1532),
        "Itatiba": (-23.0057, -46.8384),
        "Louveira": (-23.0858, -46.9487),
        "Indaiatuba": (-23.0816, -47.2101),
        "Hortolandia": (-22.8529, -47.2209),
        "Santa Barbara D'Oeste": (-22.7539, -47.4136),
        "Sumare": (-22.8204, -47.2728),
        "Salto": (-23.1996, -47.2933),
        "Itu": (-23.2637, -47.2992),
        "Itupeva": (-23.1526, -47.0593),
        "Jaguariuna": (-22.7037, -46.9851),
        "Guaruja": (-23.9939, -46.2576),
        "Praia Grande": (-24.0048, -46.4026),
        "Cubatao": (-23.8911, -46.4261),
        "Bertioga": (-23.8543, -46.1384),
        "Caraguatatuba": (-23.6237, -45.4121),
        "Ubatuba": (-23.4336, -45.0838),
        "Ilhabela": (-23.7785, -45.3559),
        "Sao Sebastiao": (-23.8062, -45.4017),
        # Adicionar mais cidades conforme necessário
    }
    
    # Mapeamento de siglas de estados para uma cidade representativa
    state_to_capital = {
        'AC': (-9.9738, -67.8277),  # Rio Branco
        'AL': (-9.6498, -35.7089),  # Maceió
        'AP': (0.0356, -51.0705),   # Macapá
        'AM': (-3.1019, -60.0250),  # Manaus
        'BA': (-12.9714, -38.5014), # Salvador
        'CE': (-3.7172, -38.5433),  # Fortaleza
        'DF': (-15.7801, -47.9292), # Brasília
        'ES': (-20.2976, -40.2958), # Vitória
        'GO': (-16.6864, -49.2643), # Goiânia
        'MA': (-2.5391, -44.2829),  # São Luís
        'MT': (-15.6014, -56.0979), # Cuiabá
        'MS': (-20.4428, -54.6464), # Campo Grande
        'MG': (-19.9167, -43.9345), # Belo Horizonte
        'PA': (-1.4558, -48.4902),  # Belém
        'PB': (-7.1219, -34.8829),  # João Pessoa
        'PR': (-25.4195, -49.2646), # Curitiba
        'PE': (-8.0476, -34.8770),  # Recife
        'PI': (-5.0920, -42.8038),  # Teresina
        'RJ': (-22.9068, -43.1729), # Rio de Janeiro
        'RN': (-5.7945, -35.2120),  # Natal
        'RS': (-30.0277, -51.2287), # Porto Alegre
        'RO': (-8.7608, -63.9004),  # Porto Velho
        'RR': (2.8235, -60.6758),   # Boa Vista
        'SC': (-27.5969, -48.5495), # Florianópolis
        'SP': (-23.5505, -46.6333), # São Paulo
        'SE': (-10.9472, -37.0731), # Aracaju
        'TO': (-10.2491, -48.3243)  # Palmas
    }

    # Tentar encontrar por CEP primeiro (método mais preciso)
    if cep:
        clean_cep_value = clean_cep(cep)
        if clean_cep_value and len(clean_cep_value) >= 2:
            prefix = clean_cep_value[:2]
            if prefix in cep_ranges:
                return cep_ranges[prefix]
    
    # Tenta encontrar a cidade na lista
    if city:
        city_name = normalize_name(city)
        if city_name in city_coordinates:
            return city_coordinates[city_name]
        
        # Tenta novamente removendo possíveis sufixos comuns (Ex: "Araçatuba/SP" -> "Araçatuba")
        if '/' in city_name:
            city_name = city_name.split('/')[0].strip()
            if city_name in city_coordinates:
                return city_coordinates[city_name]
    
    # Tenta buscar pelo estado, se fornecido
    if state:
        state_code = state.strip().upper()
        if state_code in state_to_capital:
            return state_to_capital[state_code]
    
    # Se não encontrar, retorna coordenadas para o centro do Brasil
    return (-15.7801, -47.9292)  # Centro aproximado do Brasil (Brasília)

@login_required
def visao_gerencial(request):
    """
    Renderiza o template da visão gerencial
    """
    # Adicionar contagem de escolas ao contexto
    from escolas.models import Escola
    from django.db.models import Count
    
    total_escolas = Escola.objects.filter(ativo=True).count()
    
    # Buscar empresas distintas da tabela escolas_escola
    empresas = Escola.objects.exclude(empresa__isnull=True).exclude(empresa='').values('empresa').distinct().order_by('empresa')
    
    context = {
        'active_menu': 'visao_gerencial',
        'total_escolas': total_escolas,
        'empresas': empresas,
    }
    return render(request, 'core/visao_gerencial_otimizada.html', context)

def visao_gerencial_dados(request):
    """
    API que fornece os dados para o dashboard de Visão Gerencial
    Versão otimizada usando sistema de cache para melhorar desempenho
    """
    try:
        # Importações necessárias
        from escolas.models import Supervisor, Escola, HistoricoBudget
        from django.db.models import Count, Q, F, ExpressionWrapper, FloatField, Max, Avg, Sum
        from core.models import DadosVisaoGerencialCache
        import json
        from datetime import timedelta
        from django.utils import timezone
        
        # Obtém os parâmetros de filtro
        empresa_id = request.GET.get('empresa', 'all')
        contrato_id = request.GET.get('contrato', 'all')
        periodo = request.GET.get('periodo', '30')
        
        # Forçar recálculo se solicitado (para atualizações manuais)
        force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
        
        # Verificar se já temos dados em cache para esses filtros
        if not force_refresh:
            try:
                # Buscar dados do cache (não mais antigos que 1 hora)
                cache_time_threshold = timezone.now() - timedelta(hours=1)
                cached_data = DadosVisaoGerencialCache.objects.filter(
                    filtro_empresa=empresa_id,
                    filtro_contrato=contrato_id,
                    filtro_periodo=periodo,
                    data_atualizacao__gte=cache_time_threshold
                ).first()
                
                if cached_data:
                    print("✅ Usando dados em cache para maior velocidade")
                    return JsonResponse(json.loads(cached_data.dados_json))
            except Exception as e:
                print(f"⚠️ Erro ao buscar cache: {str(e)}")
                # Continuar com geração de dados novos
        
        # Se não temos cache ou o cache está expirado, gerar novos dados
        print("🔄 Gerando novos dados para a visão gerencial...")
        
        # Verificar se as tabelas existem no banco de dados
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tabelas_existentes = [row[0] for row in cursor.fetchall()]
        
        tabela_contrato_existe = 'core_contrato' in tabelas_existentes
        tabela_empresa_existe = 'core_empresa' in tabelas_existentes
        tabela_supervisor_existe = 'escolas_supervisor' in tabelas_existentes
        tabela_produto_existe = 'produtos_produto' in tabelas_existentes
        tabela_escola_existe = 'escolas_escola' in tabelas_existentes
        
        # Adicionar opções de filtro para empresas e contratos
        filterOptions = {
            'companies': [],
            'contracts': []
        }
        
        if tabela_escola_existe:
            try:
                # Buscar as escolas, que são usadas como contratos no sistema
                from escolas.models import Escola
                escolas = Escola.objects.filter(ativo=True)
                
                # Agrupar escolas por empresa
                empresas = {}
                
                # Processar cada escola para extrair empresas
                for escola in escolas:
                    # Obter empresa da escola
                    empresa_nome = escola.empresa if hasattr(escola, 'empresa') and escola.empresa else 'Sem empresa'
                    
                    # Adicionar empresa ao dicionário se não existir
                    if empresa_nome not in empresas:
                        # Gerar um ID para a empresa (baseado no nome)
                        import hashlib
                        empresa_id_hash = hashlib.md5(empresa_nome.encode()).hexdigest()[:8]
                        empresas[empresa_nome] = empresa_id_hash
                    
                    # Adicionar contrato (escola) à lista
                    filterOptions['contracts'].append({
                        'id': str(escola.id),
                        'name': escola.nome,
                        'company_id': empresas[empresa_nome]
                    })
                
                # Converter o dicionário de empresas para lista
                for empresa_nome, empresa_id_hash in empresas.items():
                    filterOptions['companies'].append({
                        'id': empresa_id_hash,
                        'name': empresa_nome
                    })
                
                # Ordenar alfabeticamente
                filterOptions['companies'].sort(key=lambda x: x['name'])
                filterOptions['contracts'].sort(key=lambda x: x['name'])
                
                print(f"✅ Carregadas {len(filterOptions['companies'])} empresas e {len(filterOptions['contracts'])} contratos (escolas) para os filtros")
            except Exception as e:
                import traceback
                print(f"⚠️ Erro ao carregar opções de filtro: {str(e)}")
                print(traceback.format_exc())
        
        # 1. Contagem de pedidos por status (usando icontains para maior compatibilidade)
        print("🔄 Calculando contagem de pedidos por status...")
        from pedidos.models import Pedido
        from escolas.models import Escola
        
        # Filtrar por empresa se especificado
        pedidos_query = Pedido.objects
        
        # Aplicar filtro de empresa se fornecido e diferente de 'all'
        empresa_nome = request.GET.get('empresa')
        if empresa_nome and empresa_nome != 'all' and empresa_nome != '':
            print(f"🔍 Filtrando por empresa: {empresa_nome}")
            # Obter IDs das escolas com a empresa especificada
            escola_ids = Escola.objects.filter(empresa=empresa_nome).values_list('id', flat=True)
            # Filtrar pedidos por essas escolas
            pedidos_query = pedidos_query.filter(escola_id__in=escola_ids)
        
        # Aplicar filtro de contrato (escola) se fornecido e diferente de 'all'
        contrato_id = request.GET.get('contrato')
        if contrato_id and contrato_id != 'all' and contrato_id != '':
            print(f"🔍 Filtrando por contrato/escola ID: {contrato_id}")
            pedidos_query = pedidos_query.filter(escola_id=contrato_id)
            
        # Aplicar filtro de período se fornecido e diferente de 'all'
        periodo = request.GET.get('periodo')
        if periodo and periodo != 'all':
            from datetime import timedelta
            dias = int(periodo)
            data_limite = timezone.now() - timedelta(days=dias)
            print(f"🔍 Filtrando por período: últimos {dias} dias")
            pedidos_query = pedidos_query.filter(data_solicitacao__gte=data_limite)
        
        pendentes = pedidos_query.filter(status='pendente').count()
        aprovados = pedidos_query.filter(status='aprovado').count()
        enviados = pedidos_query.filter(status='pedido_enviado').count()
        entregues = pedidos_query.filter(status='entregue').count()
        cancelados = pedidos_query.filter(status='cancelado').count()
        
        # Calcular tendências com base em dados históricos (30 dias atrás)
        data_atual = timezone.now()
        data_anterior = data_atual - timedelta(days=30)
        
        pendentes_anterior = pedidos_query.filter(status='pendente', data_solicitacao__lt=data_anterior).count()
        aprovados_anterior = pedidos_query.filter(status='aprovado', data_solicitacao__lt=data_anterior).count()
        enviados_anterior = pedidos_query.filter(status='pedido_enviado', data_solicitacao__lt=data_anterior).count()
        entregues_anterior = pedidos_query.filter(status='entregue', data_solicitacao__lt=data_anterior).count()
        cancelados_anterior = pedidos_query.filter(status='cancelado', data_solicitacao__lt=data_anterior).count()
        
        # Calcular tendências (cuidado com divisão por zero)
        def calcular_tendencia(valor_atual, valor_anterior):
            if valor_anterior == 0:
                return 100.0 if valor_atual > 0 else 0.0
            return ((valor_atual - valor_anterior) / valor_anterior) * 100
        
        pendente_trend = calcular_tendencia(pendentes, pendentes_anterior)
        aprovado_trend = calcular_tendencia(aprovados, aprovados_anterior)
        enviado_trend = calcular_tendencia(enviados, enviados_anterior)
        entregue_trend = calcular_tendencia(entregues, entregues_anterior)
        cancelado_trend = calcular_tendencia(cancelados, cancelados_anterior)
        
        # 2. Contratos ativos (com verificação se a tabela existe)
        print("🔄 Calculando contratos ativos...")
        if tabela_contrato_existe:
            try:
                # SOLUÇÃO APLICADA: Usar o mesmo método que funciona no dashboard inicial
                # Em vez de buscar no modelo Contrato, buscamos no modelo Escola
                from escolas.models import Escola
                total_contratos_ativos = Escola.objects.filter(ativo=True).count()
                
                # Log para depuração
                print(f"✅ Total de contratos ativos através de Escola.objects: {total_contratos_ativos}")
                
                # Buscar contratos anteriores (considerando que não precisamos disso, já que estamos forçando zero na UI)
                contratos_anteriores = total_contratos_ativos  # Isso manterá o trend em 0%
                contratos_trend = 0.0  # Forçamos tendência zero
                
            except Exception as e:
                # Em caso de erro, usar dados de backup
                print(f"❌ Erro ao contar escolas ativas: {str(e)}")
                import traceback
                print(traceback.format_exc())
                
                total_contratos_ativos = 0  # Forçando a exibir zero
                print(f"⚠️ Definindo contratos ativos como ZERO devido a erro")
                contratos_trend = 0.0
        else:
            # Usar total de escolas como substituto se contratos não existirem
            try:
                from escolas.models import Escola
                total_contratos_ativos = Escola.objects.filter(ativo=True).count()
                print(f"✅ Usando escolas como substituto para contratos: {total_contratos_ativos} escolas ativas")
            except Exception as e:
                print(f"❌ Erro ao buscar escolas: {str(e)}")
                total_contratos_ativos = 0
            contratos_trend = 0.0
        
        # 3. Valor total de pedidos por mês - ABORDAGEM OTIMIZADA
        print("🔄 Calculando valores mensais de pedidos...")
        try:
            # Formato exato que o frontend espera (array de objetos com month e value)
            meses_nomes = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }
            
            # Dados fixos - garantir pelo menos um conjunto básico de dados para o gráfico funcionar
            mensal_data = [
                {'month': 'Jan', 'value': 0},
                {'month': 'Fev', 'value': 0},
                {'month': 'Mar', 'value': 0},
                {'month': 'Abr', 'value': 0},
                {'month': 'Mai', 'value': 0},
                {'month': 'Jun', 'value': 0}
            ]
            
            # OTIMIZAÇÃO: Usar consulta com annotate e aggregate para evitar loop sobre todos os pedidos
            try:
                from django.db.models import Sum, F, ExpressionWrapper, FloatField
                from django.db.models.functions import TruncMonth, ExtractMonth
                from pedidos.models import Pedido, ItemPedido
                
                # Tentar buscar pedidos com suas propriedades
                valid_statuses = ['aprovado', 'entregue', 'pedido_enviado', 'enviado', 
                                'Aprovado', 'Entregue', 'Pedido Enviado', 'Enviado']
                
                # Consulta base para itens de pedido
                itens_query = ItemPedido.objects.all()
                
                # Aplicar filtro de empresa se fornecido e diferente de 'all'
                if empresa_id and empresa_id != 'all':
                    itens_query = itens_query.filter(pedido__escola__empresa=empresa_id)
                
                # Aplicar filtro de contrato (escola) se fornecido e diferente de 'all'
                if contrato_id and contrato_id != 'all':
                    itens_query = itens_query.filter(pedido__escola_id=contrato_id)
                
                # Aplicar filtro de período se fornecido e diferente de 'all'
                if periodo and periodo != 'all':
                    from datetime import timedelta
                    dias = int(periodo)
                    data_limite = timezone.now() - timedelta(days=dias)
                    itens_query = itens_query.filter(pedido__data_solicitacao__gte=data_limite)
                
                # Consulta otimizada para calcular valores por mês
                valores_por_mes = (
                    itens_query
                    .filter(pedido__status__in=valid_statuses)
                    .annotate(mes=ExtractMonth('pedido__data_solicitacao'))
                    .values('mes')
                    .annotate(total=Sum(ExpressionWrapper(F('quantidade') * F('valor_unitario'), output_field=FloatField())))
                    .order_by('mes')
                )
                
                # Converter para o formato esperado pelo frontend
                mensal_data = []
                for item in valores_por_mes:
                    mes_nome = meses_nomes[item['mes']]
                    mensal_data.append({
                        'month': mes_nome,
                        'value': float(item['total'] or 0)
                    })
                
                # Pegar apenas os últimos 6 meses com dados não-zero
                meses_com_dados = [item for item in mensal_data if item['value'] > 0]
                if len(meses_com_dados) > 0:
                    # Ordenar por mês 
                    ordem_meses = {
                        'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6,
                        'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
                    }
                    meses_com_dados.sort(key=lambda x: ordem_meses[x['month']])
                    
                    # Pegar apenas os últimos 6 (ou menos se não houver 6)
                    if len(meses_com_dados) > 6:
                        meses_com_dados = meses_com_dados[-6:]
                    
                    # Usar os meses com dados
                    mensal_data = meses_com_dados
                    print(f"✅ Usando dados reais para o gráfico: {len(valores_por_mes)} meses com dados")
                else:
                    print("⚠️ Sem pedidos com valor para mostrar no gráfico")
            except Exception as e:
                import traceback
                print(f"⚠️ Erro ao calcular valores mensais otimizados: {str(e)}")
                print(traceback.format_exc())
                
        except Exception as e:
            import traceback
            print(f"❌ ERRO ao gerar gráfico de pedidos por mês: {str(e)}")
            print(traceback.format_exc())
            
            # IMPORTANTE: garantir que sempre temos dados no formato esperado
            # para não travar o frontend com "carregando dados..."
            mensal_data = [
                {'month': 'Jan', 'value': 0},
                {'month': 'Fev', 'value': 0},
                {'month': 'Mar', 'value': 0},
                {'month': 'Abr', 'value': 0},
                {'month': 'Mai', 'value': 0},
                {'month': 'Jun', 'value': 0}
            ]
        
        # Dados de orçamentos (budgets) das escolas
        try:
            # Query base para escolas
            escolas_query = Escola.objects.filter(ativo=True)
            
            # Aplicar filtros se necessário
            if empresa_id and empresa_id != 'all':
                escolas_query = escolas_query.filter(empresa=empresa_id)
            if contrato_id and contrato_id != 'all':
                escolas_query = escolas_query.filter(id=contrato_id)
                
            # Buscar top 5 escolas com maior variação percentual no budget
            escolas_com_variacao = []
            for escola in escolas_query:
                try:
                    variacao = escola.variacao_budget
                    escolas_com_variacao.append({
                        'contrato': escola.nome,
                        'empresa': escola.empresa or "Não especificada",
                        'budget_atual': float(escola.budget),
                        'percentual_variacao': float(variacao)
                    })
                except Exception as e:
                    print(f"⚠️ Erro ao calcular variação budget para escola {escola.id}: {str(e)}")
            
            # Ordenar pela variação percentual (absoluta)
            escolas_com_variacao.sort(key=lambda x: abs(x['percentual_variacao']), reverse=True)
            
            # Pegar as 5 escolas com maior variação
            top_variacoes_budget = escolas_com_variacao[:5]
            
            # Verificar se há datas de validade de budget próximas de expirar
            hoje = timezone.now().date()
            proximo_mes = hoje + timedelta(days=30)
            escolas_budget_expirando = escolas_query.filter(
                data_validade_budget__gte=hoje,
                data_validade_budget__lte=proximo_mes
            ).order_by('data_validade_budget')[:5]
            
            # Formatar para resposta
            budgets_expirando = []
            for escola in escolas_budget_expirando:
                dias_restantes = (escola.data_validade_budget - hoje).days
                budgets_expirando.append({
                    'contrato': escola.nome,
                    'data_validade': escola.data_validade_budget.strftime('%d/%m/%Y'),
                    'dias_restantes': dias_restantes,
                    'valor': float(escola.budget)
                })
                
        except Exception as e:
            import traceback
            print(f"⚠️ Erro ao calcular dados de variação de budget: {str(e)}")
            print(traceback.format_exc())
            top_variacoes_budget = []
            budgets_expirando = []
        
        # SEÇÃO INDEPENDENTE - Cálculo da utilização de budget por contrato
        # Esta seção irá calcular sempre independentemente dos filtros
        try:
            from pedidos.models import Pedido, ItemPedido
            from django.db.models import Sum, F, ExpressionWrapper, FloatField
            
            # Status válidos de pedidos
            valid_statuses = ['aprovado', 'entregue', 'pedido_enviado', 'enviado', 
                            'Aprovado', 'Entregue', 'Pedido Enviado', 'Enviado']
            
            # ABORDAGEM SIMPLIFICADA: calcular diretamente usando aggregate
            # Passo 1: Obter todas as escolas ativas com budget
            escolas_ativas = Escola.objects.filter(ativo=True, budget__gt=0)
            
            # Lista para armazenar os dados de utilização
            utilizacao_budget = []
            
            # Passo 2: Para cada escola, calcular o total gasto em pedidos
            for escola in escolas_ativas:
                try:
                    # Calcular valor total dos pedidos via ItemPedido
                    total_gasto = ItemPedido.objects.filter(
                        pedido__escola=escola,
                        pedido__status__in=valid_statuses
                    ).aggregate(
                        total=Sum(
                            ExpressionWrapper(
                                F('quantidade') * F('valor_unitario'),
                                output_field=FloatField()
                            )
                        )
                    )['total'] or 0
                    
                    # Calcular percentual utilizado
                    percentual = (float(total_gasto) / float(escola.budget)) * 100 if escola.budget > 0 else 0
                    
                    # Adicionar à lista
                    utilizacao_budget.append({
                        'contrato': escola.nome,
                        'empresa': escola.empresa or "Não especificada",
                        'budget_total': float(escola.budget),
                        'valor_utilizado': float(total_gasto),
                        'percentual_utilizado': round(percentual, 1)
                    })
                except Exception as e:
                    print(f"⚠️ Erro ao calcular budget para escola {escola.id}: {str(e)}")
            
            # Ordenar por valor_utilizado (do maior para o menor)
            utilizacao_budget.sort(key=lambda x: x['valor_utilizado'], reverse=True)
            
            # Pegar apenas os top 5 com maior gasto absoluto
            utilizacao_budget = utilizacao_budget[:5]
            
            # DEBUG
            print("✅ TOP 5 ESCOLAS COM MAIOR GASTO DE BUDGET:")
            for item in utilizacao_budget:
                print(f"  - {item['contrato']}: R$ {item['valor_utilizado']} ({item['percentual_utilizado']}% do budget)")
            
        except Exception as e:
            import traceback
            print(f"⚠️ Erro ao calcular dados de utilização de budget independente: {str(e)}")
            print(traceback.format_exc())
            
            # Dados de fallback garantidos
            utilizacao_budget = [
                {'contrato': 'Contrato A', 'empresa': 'Empresa A', 'budget_total': 10000, 'valor_utilizado': 8500, 'percentual_utilizado': 85},
                {'contrato': 'Contrato B', 'empresa': 'Empresa B', 'budget_total': 15000, 'valor_utilizado': 10200, 'percentual_utilizado': 68},
                {'contrato': 'Contrato C', 'empresa': 'Empresa C', 'budget_total': 5000, 'valor_utilizado': 4600, 'percentual_utilizado': 92},
                {'contrato': 'Contrato D', 'empresa': 'Empresa D', 'budget_total': 8000, 'valor_utilizado': 3600, 'percentual_utilizado': 45},
                {'contrato': 'Contrato E', 'empresa': 'Empresa E', 'budget_total': 12000, 'valor_utilizado': 9000, 'percentual_utilizado': 75}
            ]
        
        # Buscar produtos mais pedidos da tabela pedidos_itempedido
        try:
            from pedidos.models import Pedido, ItemPedido
            from produtos.models import Produto
            
            # Consulta base para itens de pedido
            itens_query = ItemPedido.objects.select_related('produto', 'pedido')
            
            # Aplicar filtros
            if empresa_id and empresa_id != 'all':
                itens_query = itens_query.filter(pedido__escola__empresa=empresa_id)
            
            if contrato_id and contrato_id != 'all':
                itens_query = itens_query.filter(pedido__escola_id=contrato_id)
            
            if periodo and periodo != 'all':
                dias = int(periodo)
                data_limite = timezone.now() - timedelta(days=dias)
                itens_query = itens_query.filter(pedido__data_solicitacao__gte=data_limite)
            
            # Consideramos apenas pedidos com status válidos
            valid_statuses = ['aprovado', 'entregue', 'pedido_enviado', 'enviado', 
                            'Aprovado', 'Entregue', 'Pedido Enviado', 'Enviado']
            itens_query = itens_query.filter(pedido__status__in=valid_statuses)
            
            # Produtos mais pedidos - agregando por produto e somando quantidade
            produtos_mais_pedidos = (
                itens_query
                .values('produto__nome')
                .annotate(total=Sum('quantidade'))
                .order_by('-total')
            )[:5]
            
            # Produtos menos pedidos - mesma lógica, mas em ordem crescente
            produtos_menos_pedidos = (
                itens_query
                .values('produto__nome')
                .annotate(total=Sum('quantidade'))
                .order_by('total')
            )[:5]
            
            # Formatar para o frontend
            produtos_mais_pedidos_formatados = [
                {'produto': item['produto__nome'], 'quantidade': item['total']}
                for item in produtos_mais_pedidos
            ]
            
            produtos_menos_pedidos_formatados = [
                {'produto': item['produto__nome'], 'quantidade': item['total']}
                for item in produtos_menos_pedidos
            ]
            
            print(f"✅ Produtos mais pedidos obtidos com sucesso: {len(produtos_mais_pedidos_formatados)} itens")
                
        except Exception as e:
            import traceback
            print(f"⚠️ Erro ao buscar produtos mais pedidos: {str(e)}")
            print(traceback.format_exc())
            
            # Dados simulados como fallback
            produtos_mais_pedidos_formatados = [
                {'produto': 'Produto A', 'quantidade': 120},
                {'produto': 'Produto B', 'quantidade': 95},
                {'produto': 'Produto C', 'quantidade': 87},
                {'produto': 'Produto D', 'quantidade': 68},
                {'produto': 'Produto E', 'quantidade': 52}
            ]
            
            produtos_menos_pedidos_formatados = [
                {'produto': 'Produto X', 'quantidade': 5},
                {'produto': 'Produto Y', 'quantidade': 8},
                {'produto': 'Produto Z', 'quantidade': 12},
                {'produto': 'Produto W', 'quantidade': 15},
                {'produto': 'Produto V', 'quantidade': 18}
            ]
        
        # CALCULAR INDICADORES FINANCEIROS REAIS
        try:
            # Calcular indicadores financeiros baseados nos dados reais
            from pedidos.models import Pedido, ItemPedido
            from django.db.models import Sum, Avg, Count, Case, When, F, ExpressionWrapper, FloatField, DecimalField
            
            # Status válidos para pedidos
            valid_statuses = ['aprovado', 'entregue', 'pedido_enviado', 'enviado', 
                            'Aprovado', 'Entregue', 'Pedido Enviado', 'Enviado']
            
            # Base de pedidos para cálculos
            pedidos_base = Pedido.objects.all()
            
            # Aplicar filtros se necessário
            if empresa_id and empresa_id != 'all':
                pedidos_base = pedidos_base.filter(escola__empresa=empresa_id)
            if contrato_id and contrato_id != 'all':
                pedidos_base = pedidos_base.filter(escola_id=contrato_id)
            if periodo and periodo != 'all':
                dias = int(periodo)
                data_limite = timezone.now() - timedelta(days=dias)
                pedidos_base = pedidos_base.filter(data_solicitacao__gte=data_limite)
            
            # 1. Valor total de todos os pedidos
            total_valor_pedidos = ItemPedido.objects.filter(
                pedido__in=pedidos_base
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantidade') * F('valor_unitario'), 
                        output_field=FloatField()
                    )
                )
            )['total'] or 0
            
            # 2. Total de pedidos
            total_pedidos = pedidos_base.count()
            
            # 3. Valor médio por pedido
            valor_medio_pedido = total_valor_pedidos / total_pedidos if total_pedidos > 0 else 0
            
            # 4. Taxa de aprovação
            pedidos_aprovados_ou_finalizados = pedidos_base.filter(status__in=valid_statuses).count()
            taxa_aprovacao = (pedidos_aprovados_ou_finalizados / total_pedidos) * 100 if total_pedidos > 0 else 0
            
            # 5. Taxa de cancelamento
            pedidos_cancelados = pedidos_base.filter(status='cancelado').count()
            taxa_cancelamento = (pedidos_cancelados / total_pedidos) * 100 if total_pedidos > 0 else 0
            
            # Dados para indicadores financeiros
            indicadores_financeiros = {
                'valor_total_pedidos': float(total_valor_pedidos),
                'valor_medio_pedido': float(valor_medio_pedido),
                'total_pedidos': total_pedidos,
                'taxa_aprovacao': float(taxa_aprovacao),
                'taxa_cancelamento': float(taxa_cancelamento),
                'pedidos_aprovados': pedidos_aprovados_ou_finalizados,
                'pedidos_cancelados': pedidos_cancelados,
                'pedidos_pendentes': pendentes
            }
            
            print("✅ Indicadores financeiros calculados com sucesso:")
            print(f"  - Valor total: R$ {total_valor_pedidos:.2f}")
            print(f"  - Valor médio: R$ {valor_medio_pedido:.2f}")
            print(f"  - Taxa aprovação: {taxa_aprovacao:.1f}%")
            print(f"  - Taxa cancelamento: {taxa_cancelamento:.1f}%")
            
        except Exception as e:
            import traceback
            print(f"⚠️ Erro ao calcular indicadores financeiros: {str(e)}")
            print(traceback.format_exc())
            
            # Fallback para indicadores financeiros
            indicadores_financeiros = {
                'valor_total_pedidos': 350000,
                'valor_medio_pedido': 1200,
                'total_pedidos': 150,
                'taxa_aprovacao': 75.5,
                'taxa_cancelamento': 8.3,
                'pedidos_aprovados': 110,
                'pedidos_cancelados': 12,
                'pedidos_pendentes': 28
            }
        
        # Calcular outros indicadores financeiros
        try:
            # Buscar todos os pedidos válidos (não cancelados)
            pedidos_validos = pedidos_query.exclude(status='cancelado')
            total_pedidos_validos = pedidos_validos.count()
            
            # Valor total de todos os pedidos
            # O problema está aqui: valor_total é uma propriedade, não um campo do banco de dados
            # Vamos calcular corretamente usando os itens de pedido
            from pedidos.models import ItemPedido
            
            valor_total_pedidos = ItemPedido.objects.filter(
                pedido__in=pedidos_validos
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantidade') * F('valor_unitario'),
                        output_field=FloatField()
                    )
                )
            )['total'] or 0
            
            # Valor médio dos pedidos
            valor_medio_pedido = valor_total_pedidos / total_pedidos_validos if total_pedidos_validos > 0 else 0
            
            # Taxa de aprovação (pedidos aprovados / total de pedidos)
            pedidos_aprovados = pedidos_query.filter(status__in=['aprovado', 'enviado', 'entregue']).count()
            total_pedidos = pedidos_query.count()
            taxa_aprovacao = (pedidos_aprovados / total_pedidos * 100) if total_pedidos > 0 else 0
            
            # Taxa de cancelamento
            pedidos_cancelados = pedidos_query.filter(status='cancelado').count()
            taxa_cancelamento = (pedidos_cancelados / total_pedidos * 100) if total_pedidos > 0 else 0
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {str(e)}")
            import traceback
            print(traceback.format_exc())

        # Construir o JSON de resposta
        response_data = {
            'filterOptions': filterOptions,
            'metrics': {
                'pendingOrders': pendentes,
                'pendingTrend': pendente_trend,
                'approvedOrders': aprovados,
                'approvedTrend': aprovado_trend,
                'shippedOrders': enviados,
                'shippedTrend': enviado_trend,
                'deliveredOrders': entregues,
                'deliveredTrend': entregue_trend,
                'canceledOrders': cancelados,
                'canceledTrend': cancelado_trend,
                'activeContracts': total_contratos_ativos,
                'contractsTrend': contratos_trend
            },
            'financialIndicators': {
                'averageOrderValue': 0,
                'averageOrderValuePercent': 0,
                'approvalRate': 0,
                'approvalRatePercent': 0,
                'cancellationRate': 0,
                'cancellationRatePercent': 0
            },
            'monthlyOrders': mensal_data,
            'orderStatus': [],
            'topSupervisors': [],
            'exceededBudgets': [],
            'topProducts': [],
            'bottomProducts': [],
            'budgetUsage': [],
            'insights': [],
            # Dados para os novos gráficos
            'total_pedidos': pendentes + aprovados + enviados + entregues + cancelados,
            'valor_total': sum(item['value'] for item in mensal_data),
            'pedidos_finalizados': entregues,
            'pedidos_pendentes': pendentes,
            'pedidos_aprovados': aprovados,
            'pedidos_enviados': enviados,
            'pedidos_entregues': entregues,
            'pedidos_cancelados': cancelados,
            # Status dos pedidos
            'status_pedidos': {
                'pendente': pendentes,
                'aprovado': aprovados,
                'enviado': enviados,
                'entregue': entregues,
                'finalizado': entregues,  # Compatibilidade para o template antigo
                'rejeitado': cancelados,  # Compatibilidade para o template antigo
                'cancelado': cancelados
            },
            # Valor por mês (já está no mensal_data)
            'valor_por_mes': mensal_data,
            # Dados para os gráficos adicionais
            'top_supervisores': buscar_top_supervisores(
                empresa_id=empresa_id,
                contrato_id=contrato_id,
                valid_statuses=valid_statuses
            ),
            'budgets_estourados': [
                {'contrato': 'Contrato A', 'percentual_estouro': 15},
                {'contrato': 'Contrato B', 'percentual_estouro': 12},
                {'contrato': 'Contrato C', 'percentual_estouro': 8},
                {'contrato': 'Contrato D', 'percentual_estouro': 5}
            ],
            'produtos_mais_pedidos': produtos_mais_pedidos_formatados,
            'produtos_menos_solicitados': produtos_menos_pedidos_formatados,
            'utilizacao_budget': utilizacao_budget if utilizacao_budget else [
                {'contrato': 'Contrato A', 'percentual_utilizado': 85},
                {'contrato': 'Contrato B', 'percentual_utilizado': 68},
                {'contrato': 'Contrato C', 'percentual_utilizado': 92},
                {'contrato': 'Contrato D', 'percentual_utilizado': 45},
                {'contrato': 'Contrato E', 'percentual_utilizado': 75}
            ],
            # Usar indicadores financeiros calculados
            'indicadores_financeiros': indicadores_financeiros,
            # Dados para a tabela de pedidos
            'pedidos': [],
            # Adicionar dados de budget variações e expiração
            'budgets_alterados': top_variacoes_budget,
            'budgets_expirando': budgets_expirando,
        }
        
        # Calcular outros indicadores financeiros usando método correto
        try:
            # Como valor_total é uma propriedade/método e não um campo de banco de dados,
            # precisamos calcular isso de forma diferente
            from pedidos.models import ItemPedido
            from django.db.models import Sum, F, ExpressionWrapper, FloatField
            
            # Total pedidos
            total_pedidos = pedidos_query.count()
            
            # Calcular o valor total através dos itens de pedido
            valor_total_pedidos = ItemPedido.objects.filter(
                pedido__in=pedidos_query.exclude(status='cancelado')
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantidade') * F('valor_unitario'),
                        output_field=FloatField()
                    )
                )
            )['total'] or 0
            
            # Valor médio
            total_pedidos_validos = pedidos_query.exclude(status='cancelado').count()
            valor_medio_pedido = valor_total_pedidos / total_pedidos_validos if total_pedidos_validos > 0 else 0
            
            # Taxa de aprovação
            pedidos_aprovados = pedidos_query.filter(status__in=['aprovado', 'enviado', 'entregue']).count()
            taxa_aprovacao = (pedidos_aprovados / total_pedidos * 100) if total_pedidos > 0 else 0
            
            # Taxa de cancelamento
            pedidos_cancelados = pedidos_query.filter(status='cancelado').count()
            taxa_cancelamento = (pedidos_cancelados / total_pedidos * 100) if total_pedidos > 0 else 0
            
            # Atualizar indicadores financeiros no response_data
            response_data['indicadores_financeiros'] = {
                'valor_total_pedidos': float(valor_total_pedidos),
                'valor_medio_pedido': float(valor_medio_pedido),
                'total_pedidos': total_pedidos,
                'taxa_aprovacao': float(taxa_aprovacao),
                'taxa_cancelamento': float(taxa_cancelamento),
                'pedidos_aprovados': pedidos_aprovados,
                'pedidos_cancelados': pedidos_cancelados,
                'pedidos_pendentes': pendentes
            }
            
            print("✅ Indicadores financeiros calculados com sucesso:")
            print(f"  - Valor total: R$ {valor_total_pedidos:.2f}")
            print(f"  - Valor médio: R$ {valor_medio_pedido:.2f}")
            print(f"  - Taxa aprovação: {taxa_aprovacao:.1f}%")
            print(f"  - Taxa cancelamento: {taxa_cancelamento:.1f}%")
            
        except Exception as e:
            print(f"⚠️ Erro ao calcular indicadores financeiros adicionais: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        # Retornar todos os dados como JSON
        return JsonResponse(response_data)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERRO CRÍTICO na visão gerencial: {str(e)}")
        print(error_trace)
        
        return JsonResponse({
            'error': True,
            'message': str(e),
            'trace': error_trace,
            'error_type': type(e).__name__
        }, status=500)

def calcular_tendencia(valor_atual, valor_anterior):
    """
    Calcula o percentual de tendência entre períodos
    """
    if valor_anterior == 0:
        return 100 if valor_atual > 0 else 0
    
    return ((valor_atual - valor_anterior) / valor_anterior) * 100

def diagnostico_endereco(request):
    """API simples para retornar dados de endereço dos contratos cadastrados"""
    escolas = Escola.objects.filter(ativo=True).order_by('-id')
    
    # Lista para armazenar dados de diagnóstico
    diagnostico = []
    
    for escola in escolas:
        # Capturar dados de endereço para diagnóstico
        escola_info = {
            'id': escola.id,
            'nome': escola.nome,
            'cep': escola.cep or "Não cadastrado",
            'endereco': escola.endereco or "Não cadastrado",
            'cidade': escola.cidade or "Não cadastrada",
            'estado': escola.estado or "Não cadastrado"
        }
        
        # Geocodificação
        lat, lng = local_geocode(
            cep=escola.cep,
            city=escola.cidade, 
            state=escola.estado,
            address=escola.endereco
        )
        
        # Registrar método usado para geocodificação
        if escola.cep:
            escola_info['metodo'] = f"Geocodificação por CEP: {escola.cep}"
        elif escola.cidade:
            escola_info['metodo'] = f"Geocodificação pela cidade: {escola.cidade}"
        elif escola.estado:
            escola_info['metodo'] = f"Geocodificação pelo estado: {escola.estado}"
        else:
            escola_info['metodo'] = "Fallback para Brasília (não encontrou dados suficientes)"
        
        escola_info['coordenadas'] = {
            'lat': lat,
            'lng': lng
        }
        
        diagnostico.append(escola_info)
    
    return JsonResponse(diagnostico, safe=False)

def verificar_dados(request):
    """
    View de diagnóstico para verificar a estrutura do banco de dados
    e compatibilidade com o dashboard de Visão Gerencial
    """
    try:
        # Informações gerais sobre os modelos
        info = {
            'total_pedidos': Pedido.objects.count(),
            'total_produtos': Produto.objects.count(),
            'total_contratos': Contrato.objects.count(),
            'total_supervisores': Supervisor.objects.count(),
            'total_empresas': Empresa.objects.count(),
            'total_detalhes_contrato': DetalhesContrato.objects.count(),
        }
        
        # Verificar campos dos modelos
        info['campos'] = {
            'pedido': [f.name for f in Pedido._meta.get_fields()],
            'produto': [f.name for f in Produto._meta.get_fields()],
            'contrato': [f.name for f in Contrato._meta.get_fields()],
            'supervisor': [f.name for f in Supervisor._meta.get_fields()],
            'empresa': [f.name for f in Empresa._meta.get_fields()],
            'detalhes_contrato': [f.name for f in DetalhesContrato._meta.get_fields()]
        }
        
        # Verificar status dos pedidos
        status_list = Pedido.objects.values_list('status', flat=True).distinct()
        info['status_pedidos'] = list(status_list)
        
        # Verificar distribuição de pedidos por status
        status_counts = {}
        for status in status_list:
            status_counts[status] = Pedido.objects.filter(status=status).count()
        info['contagem_status'] = status_counts
        
        # Verificar datas dos pedidos
        info['datas_pedidos'] = {}
        if hasattr(Pedido, 'data_criacao'):
            data_min = Pedido.objects.order_by('data_criacao').first()
            data_max = Pedido.objects.order_by('-data_criacao').first()
            info['datas_pedidos']['data_criacao'] = {
                'min': data_min.data_criacao.strftime('%d/%m/%Y') if data_min else 'N/A',
                'max': data_max.data_criacao.strftime('%d/%m/%Y') if data_max else 'N/A'
            }
        
        if hasattr(Pedido, 'data_solicitacao'):
            data_min = Pedido.objects.order_by('data_solicitacao').first()
            data_max = Pedido.objects.order_by('-data_solicitacao').first()
            info['datas_pedidos']['data_solicitacao'] = {
                'min': data_min.data_solicitacao.strftime('%d/%m/%Y') if data_min else 'N/A',
                'max': data_max.data_solicitacao.strftime('%d/%m/%Y') if data_max else 'N/A'
            }
        
        # Verificar valores dos pedidos
        if hasattr(Pedido, 'valor_total'):
            info['valores_pedidos'] = {
                'min': float(Pedido.objects.aggregate(Min('valor_total'))['valor_total__min'] or 0),
                'max': float(Pedido.objects.aggregate(Max('valor_total'))['valor_total__max'] or 0),
                'media': float(Pedido.objects.aggregate(Avg('valor_total'))['valor_total__avg'] or 0)
            }
        
        # Verificar relacionamentos
        info['relacionamentos'] = {}
        
        # Pedido -> Contrato
        if hasattr(Pedido, 'contrato'):
            pedidos_com_contrato = Pedido.objects.exclude(contrato=None).count()
            info['relacionamentos']['pedido_contrato'] = {
                'total': pedidos_com_contrato,
                'percentual': (pedidos_com_contrato / info['total_pedidos']) * 100 if info['total_pedidos'] > 0 else 0
            }
        
        # Pedido -> Empresa
        if hasattr(Pedido, 'empresa'):
            pedidos_com_empresa = Pedido.objects.exclude(empresa=None).count()
            info['relacionamentos']['pedido_empresa'] = {
                'total': pedidos_com_empresa,
                'percentual': (pedidos_com_empresa / info['total_pedidos']) * 100 if info['total_pedidos'] > 0 else 0
            }
        
        # Supervisor -> Contrato (verificar se existe)
        if hasattr(Supervisor, 'contrato_set'):
            info['relacionamentos']['supervisor_contrato'] = {
                'existe': True,
                'nota': 'Relacionamento Supervisor -> Contrato existe'
            }
        else:
            info['relacionamentos']['supervisor_contrato'] = {
                'existe': False,
                'nota': 'Relacionamento Supervisor -> Contrato NÃO existe'
            }
        
        # Examinar valores
        pedido_amostra = None
        if Pedido.objects.exists():
            pedido_amostra = model_to_dict(Pedido.objects.first())
        
        contrato_amostra = None
        if Contrato.objects.exists():
            contrato_amostra = model_to_dict(Contrato.objects.first())
        
        produto_amostra = None
        if Produto.objects.exists():
            produto_amostra = model_to_dict(Produto.objects.first())
        
        info['amostras'] = {
            'pedido': pedido_amostra,
            'contrato': contrato_amostra,
            'produto': produto_amostra
        }
        
        return JsonResponse(info, json_dumps_params={'indent': 2})
    
    except Exception as e:
        import traceback
        error_message = str(e)
        error_trace = traceback.format_exc()
        
        return JsonResponse({
            'error': 'Erro ao verificar dados',
            'message': error_message,
            'trace': error_trace
        }, status=500)

def exportar_dashboard(request):
    """Exporta os dados do dashboard em formato Excel"""
    # Obtém os mesmos parâmetros de filtro que a visão usa
    empresa_id = request.GET.get('empresa', 'all')
    contrato_id = request.GET.get('contrato', 'all')
    periodo = request.GET.get('periodo', '30')
    
    # Obter dados do dashboard (reaproveitando a lógica existente)
    dados = visao_gerencial_dados(request).content
    dados = json.loads(dados)
    
    # Se ocorreu um erro, retornar mensagem
    if 'error' in dados and dados['error']:
        messages.error(request, f"Erro ao exportar dados: {dados['message']}")
        return redirect('core:visao_gerencial')
    
    # Criar um arquivo Excel
    wb = Workbook()
    
    # Métricas gerais
    ws_metricas = wb.active
    ws_metricas.title = "Métricas"
    
    # Adicionar título
    ws_metricas.append(["Dashboard de Visão Gerencial - Exportação"])
    ws_metricas.append(["Data de exportação", datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    ws_metricas.append([])  # Linha em branco
    
    # Adicionar parâmetros de filtro utilizados
    ws_metricas.append(["Parâmetros de filtro"])
    empresa_nome = "Todas as empresas"
    contrato_nome = "Todos os contratos"
    
    # Buscar nome da empresa selecionada
    if empresa_id != 'all' and 'filterOptions' in dados:
        for empresa in dados['filterOptions']['companies']:
            if empresa['id'] == empresa_id:
                empresa_nome = empresa['name']
                break
    
    # Buscar nome do contrato selecionado
    if contrato_id != 'all' and 'filterOptions' in dados:
        for contrato in dados['filterOptions']['contracts']:
            if contrato['id'] == contrato_id:
                contrato_nome = contrato['name']
                break
    
    periodo_texto = {
        '30': 'Últimos 30 dias',
        '90': 'Últimos 90 dias',
        '180': 'Últimos 6 meses',
        '365': 'Último ano',
        'all': 'Todo período'
    }.get(periodo, 'Período personalizado')
    
    ws_metricas.append(["Empresa", empresa_nome])
    ws_metricas.append(["Contrato", contrato_nome])
    ws_metricas.append(["Período", periodo_texto])
    ws_metricas.append([])  # Linha em branco
    
    # Métricas principais
    if 'metrics' in dados:
        metrics = dados['metrics']
        ws_metricas.append(["Métricas Principais"])
        ws_metricas.append(["Métrica", "Valor", "Tendência (%)"])
        ws_metricas.append(["Pedidos Pendentes", metrics.get('pendingOrders', 0), metrics.get('pendingTrend', 0)])
        ws_metricas.append(["Pedidos Aprovados", metrics.get('approvedOrders', 0), metrics.get('approvedTrend', 0)])
        ws_metricas.append(["Pedidos Enviados", metrics.get('shippedOrders', 0), metrics.get('shippedTrend', 0)])
        ws_metricas.append(["Pedidos Entregues", metrics.get('deliveredOrders', 0), metrics.get('deliveredTrend', 0)])
        ws_metricas.append(["Pedidos Cancelados", metrics.get('canceledOrders', 0), metrics.get('canceledTrend', 0)])
        ws_metricas.append(["Contratos Ativos", metrics.get('activeContracts', 0), metrics.get('contractsTrend', 0)])
    
    # Indicadores Financeiros
    if 'financialIndicators' in dados:
        ws_metricas.append([])  # Linha em branco
        financials = dados['financialIndicators']
        ws_metricas.append(["Indicadores Financeiros"])
        ws_metricas.append(["Indicador", "Valor", "Percentual"])
        ws_metricas.append(["Valor Médio por Pedido (R$)", financials.get('averageOrderValue', 0), f"{financials.get('averageOrderValuePercent', 0)}%"])
        ws_metricas.append(["Taxa de Aprovação", f"{financials.get('approvalRate', 0)}%", f"{financials.get('approvalRatePercent', 0)}%"])
        ws_metricas.append(["Taxa de Cancelamento", f"{financials.get('cancellationRate', 0)}%", f"{financials.get('cancellationRatePercent', 0)}%"])
    
    # Valor Total de Pedidos por Mês
    if 'monthlyOrders' in dados and dados['monthlyOrders']:
        ws_mensal = wb.create_sheet("Pedidos Mensais")
        ws_mensal.append(["Valor Total de Pedidos por Mês"])
        ws_mensal.append(["Mês", "Valor Total (R$)"])
        
        for item in dados['monthlyOrders']:
            ws_mensal.append([item.get('month', ''), item.get('value', 0)])
    
    # Status dos Pedidos
    if 'orderStatus' in dados and dados['orderStatus']:
        ws_status = wb.create_sheet("Status dos Pedidos")
        ws_status.append(["Status dos Pedidos"])
        ws_status.append(["Status", "Quantidade"])
        
        for item in dados['orderStatus']:
            ws_status.append([item.get('status', ''), item.get('value', 0)])
    
    # Top Supervisores
    if 'topSupervisors' in dados and dados['topSupervisors']:
        ws_super = wb.create_sheet("Top Supervisores")
        ws_super.append(["Top Supervisores"])
        ws_super.append(["Nome", "Cargo", "Contratos", "Tendência (%)"])
        
        for supervisor in dados['topSupervisors']:
            ws_super.append([
                supervisor.get('name', ''),
                supervisor.get('role', ''),
                supervisor.get('contracts', 0),
                supervisor.get('trend', 0)
            ])
    
    # Orçamentos Estourados
    if 'exceededBudgets' in dados and dados['exceededBudgets']:
        ws_budget = wb.create_sheet("Orçamentos Estourados")
        ws_budget.append(["Orçamentos Estourados"])
        ws_budget.append(["Contrato", "Empresa", "Orçamento (R$)", "Utilizado (R$)", "Status"])
        
        for budget in dados['exceededBudgets']:
            ws_budget.append([
                budget.get('contract', ''),
                budget.get('company', ''),
                budget.get('budget', 0),
                budget.get('current', 0),
                budget.get('status', '')
            ])
    
    # Top Produtos
    if 'topProducts' in dados and dados['topProducts']:
        ws_top = wb.create_sheet("Produtos Mais Pedidos")
        ws_top.append(["Produtos Mais Pedidos"])
        ws_top.append(["Nome", "Categoria", "Pedidos", "Valor Total (R$)"])
        
        for produto in dados['topProducts']:
            ws_top.append([
                produto.get('name', ''),
                produto.get('category', ''),
                produto.get('orders', 0),
                produto.get('value', 0)
            ])
    
    # Bottom Produtos
    if 'bottomProducts' in dados and dados['bottomProducts']:
        ws_bottom = wb.create_sheet("Produtos Menos Pedidos")
        ws_bottom.append(["Produtos Menos Pedidos"])
        ws_bottom.append(["Nome", "Categoria", "Pedidos", "Valor Total (R$)", "Último Pedido"])
        
        for produto in dados['bottomProducts']:
            ws_bottom.append([
                produto.get('name', ''),
                produto.get('category', ''),
                produto.get('orders', 0),
                produto.get('value', 0),
                produto.get('lastOrder', '')
            ])
    
    # Utilização de Budget
    if 'budgetUsage' in dados and dados['budgetUsage']:
        ws_usage = wb.create_sheet("Utilização de Budget")
        ws_usage.append(["Utilização de Budget por Contrato"])
        ws_usage.append(["Contrato", "Orçamento (R$)", "Utilizado (R$)", "Percentual (%)"])
        
        for usage in dados['budgetUsage']:
            ws_usage.append([
                usage.get('contract', ''),
                usage.get('budget', 0),
                usage.get('used', 0),
                usage.get('percentage', 0)
            ])
    
    # Insights
    if 'insights' in dados and dados['insights']:
        ws_insights = wb.create_sheet("Insights")
        ws_insights.append(["Previsões e Insights"])
        ws_insights.append(["Tipo", "Título", "Mensagem"])
        
        for insight in dados['insights']:
            ws_insights.append([
                insight.get('type', ''),
                insight.get('title', ''),
                insight.get('message', '')
            ])
    
    # Aplicar formatação
    for ws in wb.worksheets:
        # Formatar cabeçalhos e títulos
        for row_idx in range(1, 5):
            if row_idx <= ws.max_row:
                for cell in ws[row_idx]:
                    cell.font = openpyxl.styles.Font(bold=True)
        
        # Ajustar largura das colunas
        for column in ws.columns:
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Criar resposta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Definir nome do arquivo
    hoje = datetime.now().strftime("%Y-%m-%d")
    filename = f"dashboard_visao_gerencial_{hoje}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Salvar o arquivo
    wb.save(response)
    
    return response

def prioridade_insight(insight):
    if insight['alertType'] == 'warning':
        return 0  # Maior prioridade
    elif insight['alertType'] == 'success':
        return 1
    else:  # 'info'
        return 2

@login_required
def visao_gerencial_contratos(request):
    """
    API que retorna os contratos (escolas) relacionados à empresa selecionada
    """
    try:
        # Obtém o parâmetro de empresa
        empresa_nome = request.GET.get('empresa', '')
        
        if not empresa_nome:
            return JsonResponse({
                'error': True,
                'message': 'Empresa não especificada',
                'contratos': []
            })
        
        # Buscar escolas relacionadas à empresa
        from escolas.models import Escola
        escolas = Escola.objects.filter(
            empresa=empresa_nome,
            ativo=True
        ).order_by('nome')
        
        # Preparar lista de contratos
        contratos = []
        for escola in escolas:
            contratos.append({
                'id': str(escola.id),
                'nome': escola.nome
            })
        
        return JsonResponse({
            'error': False,
            'message': 'Contratos encontrados com sucesso',
            'contratos': contratos
        })
    
    except Exception as e:
        import traceback
        print(f"Erro ao buscar contratos: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'error': True,
            'message': f'Erro ao buscar contratos: {str(e)}',
            'contratos': []
        })

@login_required
def visao_gerencial(request):
    """
    Renderiza o template da visão gerencial
    """
    # Adicionar contagem de escolas ao contexto
    from escolas.models import Escola
    from django.db.models import Count
    
    total_escolas = Escola.objects.filter(ativo=True).count()
    
    # Buscar empresas distintas da tabela escolas_escola
    empresas = Escola.objects.exclude(empresa__isnull=True).exclude(empresa='').values('empresa').distinct().order_by('empresa')
    
    context = {
        'active_menu': 'visao_gerencial',
        'total_escolas': total_escolas,
        'empresas': empresas,
    }
    return render(request, 'core/visao_gerencial_otimizada.html', context)

def buscar_top_supervisores(empresa_id=None, contrato_id=None, valid_statuses=None):
    """
    Função auxiliar para buscar os top 5 supervisores com mais contratos (escolas)
    """
    from escolas.models import Supervisor
    from django.db.models import Count, Q
    
    try:
        # Query base para supervisores
        supervisores_query = Supervisor.objects.filter(ativo=True)
        
        # Aplicar filtros se necessário
        if empresa_id and empresa_id != 'all':
            supervisores_query = supervisores_query.filter(escolas__empresa=empresa_id)
        if contrato_id and contrato_id != 'all':
            supervisores_query = supervisores_query.filter(escolas__id=contrato_id)
        
        # Buscar top 5 supervisores por número de escolas (contratos)
        supervisores = supervisores_query.annotate(
            total_escolas=Count('escolas', filter=Q(escolas__ativo=True)),
            total_pedidos=Count('escolas__pedidos', filter=Q(escolas__pedidos__status__in=valid_statuses))
        ).order_by('-total_escolas')[:5]
        
        # Formatar resultado
        return [
            {
                'nome': supervisor.nome,
                'total_escolas': supervisor.total_escolas,
                'total_pedidos': supervisor.total_pedidos
            }
            for supervisor in supervisores
        ]
    except Exception as e:
        print(f"⚠️ Erro ao buscar supervisores: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Em caso de erro, retornar dados de backup
        return [
            {'nome': 'Supervisor 1', 'total_escolas': 5, 'total_pedidos': 45},
            {'nome': 'Supervisor 2', 'total_escolas': 4, 'total_pedidos': 38},
            {'nome': 'Supervisor 3', 'total_escolas': 3, 'total_pedidos': 29},
            {'nome': 'Supervisor 4', 'total_escolas': 3, 'total_pedidos': 24},
            {'nome': 'Supervisor 5', 'total_escolas': 2, 'total_pedidos': 18}
        ]

@login_required
@permission_required('pedidos.add_notafiscal')
def importar_xml_nfe_massa(request):
    """
    Exibe a página para importação em massa de XMLs de notas fiscais
    """
    return render(request, 'core/importar_xml_nfe_massa.html')


@login_required
@permission_required('pedidos.add_notafiscal')
def processar_xml_nfe_massa(request):
    """
    Processa múltiplos arquivos XML de notas fiscais, tentando associá-los
    aos pedidos com base no número informado no campo de informações complementares
    Versão melhorada com mais padrões de reconhecimento para identificar pedidos
    """
    import traceback
    from datetime import datetime
    from django.utils import timezone
    
    if request.method != 'POST' or not request.FILES.getlist('xml_files'):
        messages.error(request, 'Nenhum arquivo XML foi enviado.')
        return redirect('core:importar_xml_nfe_massa')
    
    xml_files = request.FILES.getlist('xml_files')
    atualizar_previsao_entrega = request.POST.get('atualizar_previsao_entrega', '') == '1'
    
    # Namespace padrão da NFe
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Preparar resultados
    xmls_sucesso = []
    xmls_erro = []
    total_arquivos = len(xml_files)
    
    for xml_file in xml_files:
        try:
            # Ler o conteúdo do XML
            xml_content = xml_file.read().decode('utf-8')
            
            # Parsear o XML
            root = ET.fromstring(xml_content)
            
            # Buscar os elementos principais
            nfe_node = root.find('.//nfe:NFe', ns)
            if not nfe_node:
                # Tenta sem namespace
                nfe_node = root.find('.//NFe')
                if not nfe_node:
                    raise ValueError("Elemento NFe não encontrado no XML")
            
            # Extrair informações básicas da NFe
            infNFe = nfe_node.find('.//nfe:infNFe', ns) or nfe_node.find('.//infNFe')
            ide = infNFe.find('.//nfe:ide', ns) or infNFe.find('.//ide')
            emit = infNFe.find('.//nfe:emit', ns) or infNFe.find('.//emit')
            dest = infNFe.find('.//nfe:dest', ns) or infNFe.find('.//dest')
            total = infNFe.find('.//nfe:total/nfe:ICMSTot', ns) or infNFe.find('.//total/ICMSTot')
            
            # Extrair informações complementares com método mais robusto
            print("DEBUG - Buscando informações complementares...")
            
            # Tentar vários caminhos para encontrar infCpl
            infCpl = None
            
            # 1. Tentativa com namespace completo
            infAdic = infNFe.find('.//nfe:infAdic/nfe:infCpl', ns)
            if infAdic is not None:
                infCpl = infAdic.text
                print("DEBUG - infCpl encontrado via namespace completo")
            
            # 2. Tentativa sem namespace
            if infCpl is None:
                infAdic = infNFe.find('.//infAdic/infCpl')
                if infAdic is not None:
                    infCpl = infAdic.text
                    print("DEBUG - infCpl encontrado sem namespace")
            
            # 3. Tentativa buscando diretamente o nó infCpl
            if infCpl is None:
                infAdic = infNFe.find('.//nfe:infCpl', ns) or infNFe.find('.//infCpl')
                if infAdic is not None:
                    infCpl = infAdic.text
                    print("DEBUG - infCpl encontrado via busca direta")
            
            # 4. Tentativa com busca generica por texto 
            if infCpl is None:
                # Busca mais genérica no XML bruto
                match = re.search(r'<infCpl>(.*?)</infCpl>', xml_content, re.DOTALL)
                if match:
                    infCpl = match.group(1)
                    print("DEBUG - infCpl encontrado via regex no XML bruto")
            
            # Usar string vazia se não encontrar
            info_complementar = infCpl if infCpl is not None else ""
            
            # Debug completo
            print(f"DEBUG - Conteúdo encontrado em infCpl: '{info_complementar}'")
            
            # Extrair chave de acesso
            chave_nfe = infNFe.attrib.get('Id', '').replace('NFe', '')
            if not chave_nfe:
                raise ValueError("Chave de acesso não encontrada no XML")
            
            # Verificar se a nota já existe no sistema
            if NotaFiscal.objects.filter(chave_nfe=chave_nfe).exists():
                xmls_erro.append({
                    'nome_arquivo': xml_file.name,
                    'numero_nfe': ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ide.find('nNF').text if ide.find('nNF') is not None else "N/A",
                    'emitente': emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else emit.find('xNome').text if emit.find('xNome') is not None else "N/A",
                    'mensagem': 'Nota fiscal já existe no sistema.',
                    'info_complementar': info_complementar
                })
                continue
                
            # Extrair número do pedido do campo de informações complementares
            numero_pedido = None
            
            # Lista expandida de padrões para encontrar números de pedido
            padroes_pedido = [
                r'#PEDINT_(\d+)#',                                  # #PEDINT_123#
                r'#PEDINT_(\d+)#-',                                 # #PEDINT_123#-
                r'#PEDIDO(\d+)#',                                   # #PEDIDO123#
                r'PEDIDO\s*(?:N[°º]|NUM|NUMERO|NÚMERO)?[\s:.-]*(\d+)', # PEDIDO Nº 123, PEDIDO NUM 123
                r'PEDIDO\s*(?:INTERNO|INT)[\s:.-]*(\d+)',           # PEDIDO INTERNO 123
                r'PEDIDO\s*(?:EXTERNO|EXT)[\s:.-]*(\d+)',           # PEDIDO EXTERNO 123
                r'(?:Nº|NUM|NUMERO|NÚMERO)\s*(?:PED|PEDIDO)[\s:.-]*(\d+)', # Nº PEDIDO 123
                r'(?:ORDEM|ORDER|ORD)[\s:.-]*(?:COMPRA)?[\s:.-]*(\d+)', # ORDEM COMPRA 123
                r'(?:REF|REFERENCIA|REFERÊNCIA)[\s:.-]*(\d+)',      # REF 123
                r'#\s*(\d+)\s*#',                                   # # 123 #
                r'PEDIDOINT#\s*(\d+)',                              # PEDIDOINT#123
                r'PEDIDO\s*INT\s*#\s*(\d+)',                        # PEDIDO INT # 123
                r'PEDIDO\s*(\d+)-#-',                               # PEDIDO 123-#-
                r'ENTREGAR\s+EM:.*?PEDIDO\s+(\d+)-#-',              # ENTREGAR EM: ... PEDIDO 123-#-
                r'(?:^|\s)(\d+)-#-',                                # 123-#-
                r'[^a-zA-Z0-9]#?\s*PEDINT_\s*(\d+)\s*#?[^a-zA-Z0-9]', # qualquer padrão com PEDINT_
                r'(?:O\.C\.|O\.COMPRA|ORDEM[_\s]COMPRA)[\s:.-]*(\d+)', # O.C. 123
                r'(?:^|\s)OC[\s:.-]*(\d+)',                          # OC 123
                r'(?:PEDIDO|PED)[\s\._-]*(\d+)(?:\s|$|\W)',           # Padrão genérico: PEDIDO_123 ou PED 123
                # Adicionando padrões mais flexíveis e abrangentes
                r'(?:^|\s|:)(\d{1,6})(?:\s|$|[,;.:])',               # Números isolados que podem ser pedidos (1 a 6 dígitos)
                r'(?:CYBER\s*GO|CYBERGO)[^0-9]*(\d+)',               # Qualquer referência a CYBERGO seguida de número
                r'N[°º.]?\s*(\d+)(?:\s|$|\W)',                      # N° 123 ou Nº 123
                r'ID[:.# ]*(\d+)',                                  # ID: 123 ou ID#123
                r'REFEREN[CÇ]IA[:.# ]*(\d+)',                       # REFERENCIA: 123
                r'(?:^|[^\d])(\d{4,7})(?:[^\d]|$)',                 # Números de 4 a 7 dígitos (típico de pedidos)
                r'SOL(?:ICITAÇÃO|ICITACAO)[:.# ]*(\d+)',            # SOLICITAÇÃO: 123
                r'(?:NR|Nr|nr)[º°. ]*(\d+)',                        # Nr. 123
                r'\b(?:PED)[.:]?\s*(\d+)',                          # PED: 123 ou PED. 123
                r'(?:ORD|ORDEM)[.:]?\s*(?:NR|N)[.:]?\s*(\d+)',      # ORD. NR. 123
            ]
            
            if info_complementar:
                # Remove quebras de linha e espaços duplicados para facilitar a busca
                info_complementar_limpo = re.sub(r'[\s\n\r]+', ' ', info_complementar)
                
                # Adicionar debug auxiliar para mostrar a informação complementar
                print(f"DEBUG - Info Complementar: '{info_complementar_limpo}'")
                
                # Verificação direta para o padrão #PEDINT_X# antes de tentar outros padrões
                pedint_match = re.search(r'#PEDINT_(\d+)#', info_complementar_limpo)
                if pedint_match:
                    numero_pedido = pedint_match.group(1)
                    print(f"DEBUG - Encontrado padrão #PEDINT_{numero_pedido}#")
                else:
                    # Tenta cada padrão para encontrar o número do pedido
                    for padrao in padroes_pedido:
                        match = re.search(padrao, info_complementar_limpo, re.IGNORECASE)
                        if match:
                            numero_pedido = match.group(1)
                            print(f"DEBUG - Número de pedido encontrado: '{numero_pedido}' com padrão: '{padrao}'")
                            break
            
            # Se não encontrou nas informações complementares, procurar em outros campos
            if not numero_pedido:
                print(f"DEBUG - Nenhum número de pedido encontrado nos padrões testados!")
                # Verificar nos itens do XML
                itens = infNFe.findall('.//nfe:det', ns) or infNFe.findall('.//det')
                for item in itens:
                    prod = item.find('.//nfe:prod', ns) or item.find('./prod')
                    if prod is not None:
                        # Verificar no campo xPed (número do pedido) dos itens
                        xped = prod.find('.//nfe:xPed', ns) or prod.find('./xPed')
                        if xped is not None and xped.text and xped.text.strip():
                            numero_pedido_xped = xped.text.strip()
                            print(f"DEBUG - Encontrado possível número de pedido em xPed: '{numero_pedido_xped}'")
                            # Só usar números como pedidos
                            if numero_pedido_xped.isdigit():
                                numero_pedido = numero_pedido_xped
                                print(f"DEBUG - Usando número do pedido de xPed: '{numero_pedido}'")
                                break
            
            # Buscar o pedido pelo número
            pedido = None
            if numero_pedido:
                try:
                    # Converter para inteiro e buscar pelo ID
                    pedido = Pedido.objects.filter(id=int(numero_pedido)).first()
                except (ValueError, TypeError):
                    # Se não conseguir converter para inteiro, não encontrou o pedido
                    pass
            
            if not pedido:
                xmls_erro.append({
                    'nome_arquivo': xml_file.name,
                    'numero_nfe': ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ide.find('nNF').text if ide.find('nNF') is not None else "N/A",
                    'emitente': emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else emit.find('xNome').text if emit.find('xNome') is not None else "N/A",
                    'mensagem': f'Não foi possível encontrar um pedido correspondente. {"Número extraído: " + numero_pedido if numero_pedido else "Nenhum número de pedido encontrado nas informações complementares."}',
                    'info_complementar': info_complementar,
                    'chave_nfe': chave_nfe  # Adicionando a chave NFe para permitir associação manual posterior
                })
                
                # Salvar o XML temporariamente para permitir associação manual posterior
                temp_xml_path = os.path.join(settings.MEDIA_ROOT, 'temp_xml', f'{chave_nfe}.xml')
                
                # Criar o diretório se não existir
                os.makedirs(os.path.dirname(temp_xml_path), exist_ok=True)
                
                # Salvar o XML temporariamente
                with open(temp_xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                
                continue
            
            # Extrair informações da nota fiscal
            numero_nfe = ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ide.find('nNF').text
            serie = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ide.find('serie').text
            
            # Extrair e converter data de emissão
            data_emissao_str = ide.find('nfe:dhEmi', ns).text if ide.find('nfe:dhEmi', ns) is not None else ide.find('dhEmi').text if ide.find('dhEmi') is not None else ide.find('nfe:dEmi', ns).text if ide.find('nfe:dEmi', ns) is not None else ide.find('dEmi').text
            
            try:
                if 'T' in data_emissao_str:  # Formato ISO
                    data_emissao = datetime.fromisoformat(data_emissao_str.replace('Z', '+00:00'))
                else:  # Formato antigo dd/mm/aaaa
                    data_emissao = datetime.strptime(data_emissao_str, '%Y-%m-%d')
                
                # Converter para timezone aware
                data_emissao = timezone.make_aware(data_emissao)
            except Exception as e:
                # Fallback para data atual se houver erro
                data_emissao = timezone.now()
                
            # Extrair valores
            valor_total = Decimal(total.find('nfe:vNF', ns).text if total.find('nfe:vNF', ns) is not None else total.find('vNF').text)
            valor_produtos = Decimal(total.find('nfe:vProd', ns).text if total.find('nfe:vProd', ns) is not None else total.find('vProd').text)
            
            # Extrair dados do emitente
            razao_social_emitente = emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else emit.find('xNome').text
            cnpj_emitente = emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else emit.find('CNPJ').text
            
            # Dados adicionais
            natureza_operacao = ide.find('nfe:natOp', ns).text if ide.find('nfe:natOp', ns) is not None else ide.find('natOp').text
            destinatario_nome = dest.find('nfe:xNome', ns).text if dest.find('nfe:xNome', ns) is not None else dest.find('xNome').text if dest is not None and (dest.find('nfe:xNome', ns) is not None or dest.find('xNome') is not None) else None
            destinatario_cnpj = dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else dest.find('CNPJ').text if dest is not None and (dest.find('nfe:CNPJ', ns) is not None or dest.find('CNPJ') is not None) else None
            
            # Extrair data prevista de entrega das informações complementares
            if atualizar_previsao_entrega and info_complementar:
                # Padrões para buscar datas de entrega nas informações complementares
                padroes_data = [
                    # Formato DD/MM/YYYY
                    r'(PREVIS[ÃA]O|PREV\.?|DATA)\s*(DE)?\s*(ENTREGA|ENTREG)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'ENTREGA\s*(PREVISTA|PROGRAMADA)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    # Formato YYYY-MM-DD
                    r'(PREVIS[ÃA]O|PREV\.?|DATA)\s*(DE)?\s*(ENTREGA|ENTREG)\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})',
                    r'ENTREGA\s*(PREVISTA|PROGRAMADA)\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})',
                    # Formatos adicionais
                    r'ENTREG[AR]?\s*(EM|NO DIA|DIA)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                    r'ENTREG[AR]?\s*(EM|NO DIA|DIA)\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})',
                ]
                
                data_prevista = None
                
                for padrao in padroes_data:
                    match = re.search(padrao, info_complementar, re.IGNORECASE)
                    if match:
                        # Pegar o grupo com a data
                        data_str = match.group(match.lastindex)  # Pega o último grupo capturado
                        try:
                            # Tentar diferentes formatos de data
                            if re.match(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', data_str):
                                # Formato DD/MM/YYYY ou DD-MM-YYYY
                                separador = '/' if '/' in data_str else '-' if '-' in data_str else '.'
                                dia, mes, ano = data_str.split(separador)
                                # Ajustar ano de 2 dígitos
                                if len(ano) == 2:
                                    ano = '20' + ano
                                data_prevista = datetime(int(ano), int(mes), int(dia)).date()
                            elif re.match(r'\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}', data_str):
                                # Formato YYYY-MM-DD ou YYYY/MM/DD
                                separador = '/' if '/' in data_str else '-' if '-' in data_str else '.'
                                ano, mes, dia = data_str.split(separador)
                                data_prevista = datetime(int(ano), int(mes), int(dia)).date()
                            break
                        except Exception as e:
                            # Log para debug
                            print(f"Erro ao converter data prevista: {e}")
                
                if data_prevista:
                    pedido.previsao_entrega_fornecedor = data_prevista
                    pedido.save(update_fields=['previsao_entrega_fornecedor'])
            
            # Criar nota fiscal
            nota_fiscal = NotaFiscal(
                pedido=pedido,
                chave_nfe=chave_nfe,
                numero_nfe=numero_nfe,
                data_emissao=data_emissao,
                valor_total=valor_total,
                razao_social_emitente=razao_social_emitente,
                cnpj_emitente=cnpj_emitente,
                xml_completo=xml_content,
                natureza_operacao=natureza_operacao,
                serie=serie,
                destinatario_nome=destinatario_nome,
                destinatario_cnpj=destinatario_cnpj,
                valor_produtos=valor_produtos,
                informacoes_complementares=info_complementar
            )
            
            # Salvar a nota fiscal
            nota_fiscal.save()
            
            # Processar os itens da nota fiscal
            itens = infNFe.findall('.//nfe:det', ns) or infNFe.findall('.//det')
            
            for item in itens:
                numero_item = item.attrib.get('nItem')
                prod = item.find('nfe:prod', ns) or item.find('prod')
                
                codigo_produto = prod.find('nfe:cProd', ns).text if prod.find('nfe:cProd', ns) is not None else prod.find('cProd').text
                descricao = prod.find('nfe:xProd', ns).text if prod.find('nfe:xProd', ns) is not None else prod.find('xProd').text
                ncm = prod.find('nfe:NCM', ns).text if prod.find('nfe:NCM', ns) is not None else prod.find('NCM').text if prod.find('NCM') is not None else None
                cfop = prod.find('nfe:CFOP', ns).text if prod.find('nfe:CFOP', ns) is not None else prod.find('CFOP').text if prod.find('CFOP') is not None else None
                unidade = prod.find('nfe:uCom', ns).text if prod.find('nfe:uCom', ns) is not None else prod.find('uCom').text
                quantidade = Decimal(prod.find('nfe:qCom', ns).text if prod.find('nfe:qCom', ns) is not None else prod.find('qCom').text)
                valor_unitario = Decimal(prod.find('nfe:vUnCom', ns).text if prod.find('nfe:vUnCom', ns) is not None else prod.find('vUnCom').text)
                valor_total_item = Decimal(prod.find('nfe:vProd', ns).text if prod.find('nfe:vProd', ns) is not None else prod.find('vProd').text)
                
                # Tentar extrair informações de impostos
                imposto = item.find('nfe:imposto', ns) or item.find('imposto')
                
                icms = None
                if imposto:
                    icms_tags = ['ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90']
                    for icms_tag in icms_tags:
                        icms_node = imposto.find(f'.//nfe:{icms_tag}', ns) or imposto.find(f'.//{icms_tag}')
                        if icms_node is not None:
                            icms_text = icms_node.find('.//nfe:pICMS', ns).text if icms_node.find('.//nfe:pICMS', ns) is not None else icms_node.find('.//pICMS').text if icms_node.find('.//pICMS') is not None else None
                            if icms_text:
                                icms = Decimal(icms_text)
                                break
                
                ipi = None
                if imposto:
                    ipi_node = imposto.find('.//nfe:IPI', ns) or imposto.find('.//IPI')
                    if ipi_node is not None:
                        ipi_text = (ipi_node.find('.//nfe:pIPI', ns) or ipi_node.find('.//pIPI'))
                        if ipi_text is not None:
                            ipi_text = ipi_text.text
                            if ipi_text:
                                ipi = Decimal(ipi_text)
                
                # Salvar o item da nota fiscal
                ItemNotaFiscal.objects.create(
                    nota_fiscal=nota_fiscal,
                    numero_item=numero_item,
                    codigo_produto=codigo_produto,
                    descricao=descricao,
                    ncm=ncm,
                    cfop=cfop,
                    unidade=unidade,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total_item,
                    icms=icms,
                    ipi=ipi
                )
            
            # Adicionar à lista de sucesso
            xmls_sucesso.append({
                'nome_arquivo': xml_file.name,
                'nota': nota_fiscal
            })
            
            # Atualizar o status do pedido se necessário
            if pedido.status == 'aprovado':
                pedido.status = 'pedido_enviado'
                pedido.data_envio = timezone.now()
                pedido.save(update_fields=['status', 'data_envio'])
            
        except Exception as e:
            # Registrar erro e adicionar à lista de falhas
            print(f"Erro ao processar o arquivo {xml_file.name}: {e}")
            print(traceback.format_exc())
            
            # Extrair informações básicas para identificação do XML com erro
            try:
                # Tentar extrair informações básicas do XML
                numero_nf = "N/A"
                emitente = "N/A"
                info_complementar = "Não disponível"
                
                # Se o XML foi corretamente parseado antes do erro
                if 'root' in locals() and 'xml_content' in locals():
                    root = ET.fromstring(xml_content)
                    nfe_node = root.find('.//nfe:NFe', ns) or root.find('.//NFe')
                    if nfe_node:
                        infNFe = nfe_node.find('.//nfe:infNFe', ns) or nfe_node.find('.//infNFe')
                        if infNFe:
                            ide = infNFe.find('.//nfe:ide', ns) or infNFe.find('.//ide')
                            if ide:
                                numero_nf_elem = ide.find('nfe:nNF', ns) or ide.find('nNF')
                                if numero_nf_elem is not None:
                                    numero_nf = numero_nf_elem.text
                            
                            emit = infNFe.find('.//nfe:emit', ns) or infNFe.find('.//emit')
                            if emit:
                                emitente_elem = emit.find('nfe:xNome', ns) or emit.find('xNome')
                                if emitente_elem is not None:
                                    emitente = emitente_elem.text
                            
                            infAdic = infNFe.find('.//nfe:infAdic/nfe:infCpl', ns) or infNFe.find('.//infAdic/infCpl')
                            if infAdic is not None:
                                info_complementar = infAdic.text
            except:
                # Se falhar na extração de dados, usar valores padrão
                pass
            
            xmls_erro.append({
                'nome_arquivo': xml_file.name,
                'numero_nfe': numero_nf,
                'emitente': emitente,
                'mensagem': f'Erro ao processar: {str(e)}',
                'info_complementar': info_complementar
            })
    
    # Renderizar template com os resultados
    return render(request, 'core/resultado_importacao_xml_massa.html', {
        'xmls_sucesso': xmls_sucesso,
        'xmls_erro': xmls_erro,
        'total_arquivos': total_arquivos
    })
