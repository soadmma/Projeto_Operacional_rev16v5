import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pedidos.models import NotaFiscal, ItemNotaFiscal
from decimal import Decimal
import xml.etree.ElementTree as ET
from django.db import transaction

# Carrega a nota fiscal
nf = NotaFiscal.objects.get(id=1)
print(f"Processando nota fiscal #{nf.id} - {nf.numero_nfe}")

# Define o namespace
ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
namespace = 'http://www.portalfiscal.inf.br/nfe'

# Limpa os itens existentes
with transaction.atomic():
    ItemNotaFiscal.objects.filter(nota_fiscal=nf).delete()
    
    # Processa o XML
    root = ET.fromstring(nf.xml_completo)
    
    # Encontra os itens da nota fiscal
    itens = root.findall('.//{' + namespace + '}det')
    print(f"Encontrados {len(itens)} itens no XML")
    
    # Processa cada item
    for item in itens:
        try:
            numero_item = int(item.attrib.get('nItem', '0'))
            prod = item.find('.//{' + namespace + '}prod')
            
            if prod is None:
                print(f"Produto não encontrado no item {numero_item}")
                continue
            
            # Extrai dados do produto
            codigo_produto = prod.find('.//{' + namespace + '}cProd')
            codigo_produto = codigo_produto.text if codigo_produto is not None else ''
            
            descricao = prod.find('.//{' + namespace + '}xProd')
            descricao = descricao.text if descricao is not None else ''
            
            ncm = prod.find('.//{' + namespace + '}NCM')
            ncm = ncm.text if ncm is not None else ''
            
            cfop = prod.find('.//{' + namespace + '}CFOP')
            cfop = cfop.text if cfop is not None else ''
            
            unidade = prod.find('.//{' + namespace + '}uCom')
            unidade = unidade.text if unidade is not None else ''
            
            quantidade = prod.find('.//{' + namespace + '}qCom')
            quantidade = quantidade.text.replace(',', '.') if quantidade is not None else '0'
            
            valor_unitario = prod.find('.//{' + namespace + '}vUnCom')
            valor_unitario = valor_unitario.text.replace(',', '.') if valor_unitario is not None else '0'
            
            valor_total = prod.find('.//{' + namespace + '}vProd')
            valor_total = valor_total.text.replace(',', '.') if valor_total is not None else '0'
            
            # Encontra informações de impostos
            icms_value = None
            
            # Procura em diferentes tipos de ICMS
            icms_tags = [
                'ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 
                'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90'
            ]
            
            for icms_tag in icms_tags:
                icms_node = item.find('.//{' + namespace + '}' + icms_tag)
                if icms_node is not None:
                    p_icms = icms_node.find('.//{' + namespace + '}pICMS')
                    if p_icms is not None:
                        icms_value = p_icms.text.replace(',', '.')
                        break
            
            # Procura informação de IPI
            ipi_value = None
            ipi_node = item.find('.//{' + namespace + '}IPI')
            if ipi_node is not None:
                p_ipi = ipi_node.find('.//{' + namespace + '}pIPI')
                if p_ipi is not None:
                    ipi_value = p_ipi.text.replace(',', '.')
            
            # Cria o item no banco de dados
            new_item = ItemNotaFiscal.objects.create(
                nota_fiscal=nf,
                numero_item=numero_item,
                codigo_produto=codigo_produto,
                descricao=descricao,
                ncm=ncm,
                cfop=cfop,
                unidade=unidade,
                quantidade=Decimal(quantidade),
                valor_unitario=Decimal(valor_unitario),
                valor_total=Decimal(valor_total),
                valor_desconto=Decimal('0'),
                icms=Decimal(icms_value) if icms_value else None,
                ipi=Decimal(ipi_value) if ipi_value else None
            )
            
            print(f"Item {numero_item} criado: {codigo_produto} - {descricao}")
            
        except Exception as e:
            print(f"Erro ao processar item {numero_item}: {str(e)}")
    
    total_items = ItemNotaFiscal.objects.filter(nota_fiscal=nf).count()
    print(f"Processamento concluído. Total de itens criados: {total_items}") 