import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pedidos.models import NotaFiscal, ItemNotaFiscal
from pedidos.views import reprocessar_itens_nota_fiscal
from django.db import transaction

def reprocessar_todas_notas():
    """Reprocessa todas as notas fiscais do sistema para extrair corretamente os dados de destinatário e itens"""
    print("Iniciando reprocessamento de todas as notas fiscais...")
    
    notas_fiscais = NotaFiscal.objects.all().order_by('id')
    total_notas = notas_fiscais.count()
    
    print(f"Total de notas fiscais a processar: {total_notas}")
    
    with transaction.atomic():
        for i, nota_fiscal in enumerate(notas_fiscais, 1):
            print(f"Processando nota fiscal #{nota_fiscal.id} ({i}/{total_notas}) - NFe: {nota_fiscal.numero_nfe}")
            print(f"  Destinatário antes: {nota_fiscal.destinatario_nome or 'Não informado'}")
            
            try:
                # Verificar e salvar destinatário
                if not nota_fiscal.destinatario_nome or nota_fiscal.destinatario_nome == "Não informado":
                    try:
                        import xml.etree.ElementTree as ET
                        
                        if nota_fiscal.xml_completo:
                            root = ET.fromstring(nota_fiscal.xml_completo)
                            namespace = 'http://www.portalfiscal.inf.br/nfe'
                            
                            # Extrai dados do destinatário - mais abordagens de busca
                            destinatario = root.find('.//{' + namespace + '}dest')
                            if destinatario is not None:
                                # Múltiplas tentativas de localização
                                dest_nome = None
                                for path in ['.//{' + namespace + '}xNome', 'xNome', './/xNome']:
                                    if dest_nome is None:
                                        dest_nome = destinatario.find(path)
                                
                                if dest_nome is not None:
                                    nota_fiscal.destinatario_nome = dest_nome.text
                                
                                dest_cnpj = None
                                for path in ['.//{' + namespace + '}CNPJ', 'CNPJ', './/CNPJ']:
                                    if dest_cnpj is None:
                                        dest_cnpj = destinatario.find(path)
                                
                                if dest_cnpj is not None:
                                    nota_fiscal.destinatario_cnpj = dest_cnpj.text
                                
                                # Salvar apenas os campos de destinatário
                                nota_fiscal.save(update_fields=['destinatario_nome', 'destinatario_cnpj'])
                                print(f"  Destinatário extraído: {nota_fiscal.destinatario_nome}, CNPJ: {nota_fiscal.destinatario_cnpj}")
                    except Exception as e:
                        print(f"  Erro ao extrair destinatário: {str(e)}")
                
                # Processamento completo via função existente
                itens_processados = reprocessar_itens_nota_fiscal(nota_fiscal)
                
                print(f"  Destinatário depois: {nota_fiscal.destinatario_nome or 'Não informado'}")
                print(f"  Itens processados: {itens_processados}")
                print("  Status: Sucesso!")
            except Exception as e:
                print(f"  ERRO: {str(e)}")
            
            print("-" * 50)
    
    print("Reprocessamento concluído!")

if __name__ == "__main__":
    reprocessar_todas_notas() 