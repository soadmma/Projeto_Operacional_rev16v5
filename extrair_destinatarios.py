import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pedidos.models import NotaFiscal
import xml.etree.ElementTree as ET

def extrair_dados_notas_fiscais():
    """Extrai os dados dos destinatários, série e natureza da operação das notas fiscais existentes"""
    print("Iniciando extração de dados das notas fiscais...")
    
    notas_fiscais = NotaFiscal.objects.all().order_by('id')
    total_notas = notas_fiscais.count()
    
    print(f"Total de notas fiscais a processar: {total_notas}")
    
    for i, nota_fiscal in enumerate(notas_fiscais, 1):
        print(f"Processando nota fiscal #{nota_fiscal.id} ({i}/{total_notas}) - NFe: {nota_fiscal.numero_nfe}")
        print(f"  Destinatário antes: {nota_fiscal.destinatario_nome or 'Não informado'}")
        print(f"  Natureza da Operação antes: {nota_fiscal.natureza_operacao or 'Não informado'}")
        print(f"  Série antes: {nota_fiscal.serie or 'Não informado'}")
        
        try:
            if nota_fiscal.xml_completo:
                root = ET.fromstring(nota_fiscal.xml_completo)
                
                # Tentativa com diferentes namespaces e caminhos para encontrar informações
                nat_op = None
                serie = None
                namespaces = [
                    'http://www.portalfiscal.inf.br/nfe',
                    None  # Sem namespace
                ]
                
                # Tenta encontrar a natureza da operação
                for ns in namespaces:
                    if nat_op is not None:
                        break
                        
                    ns_prefix = '{' + ns + '}' if ns else ''
                    
                    # Busca o elemento natOp
                    nat_op_paths = [
                        f'.//{ns_prefix}natOp',
                        f'./{ns_prefix}NFe/{ns_prefix}infNFe/{ns_prefix}ide/{ns_prefix}natOp',
                        f'./{ns_prefix}infNFe/{ns_prefix}ide/{ns_prefix}natOp',
                        './natOp'
                    ]
                    
                    for path in nat_op_paths:
                        try:
                            elem = root.find(path)
                            if elem is not None and elem.text:
                                nat_op = elem.text
                                print(f"  Natureza da operação encontrada no caminho: {path}")
                                break
                        except:
                            continue
                
                # Tenta encontrar a série
                for ns in namespaces:
                    if serie is not None:
                        break
                        
                    ns_prefix = '{' + ns + '}' if ns else ''
                    
                    # Busca o elemento serie
                    serie_paths = [
                        f'.//{ns_prefix}serie',
                        f'./{ns_prefix}NFe/{ns_prefix}infNFe/{ns_prefix}ide/{ns_prefix}serie',
                        f'./{ns_prefix}infNFe/{ns_prefix}ide/{ns_prefix}serie',
                        './serie'
                    ]
                    
                    for path in serie_paths:
                        try:
                            elem = root.find(path)
                            if elem is not None and elem.text:
                                serie = elem.text
                                print(f"  Série encontrada no caminho: {path}")
                                break
                        except:
                            continue
                
                # Tenta encontrar as informações complementares (infCpl)
                inf_cpl = None
                for ns in namespaces:
                    if inf_cpl is not None:
                        break
                        
                    ns_prefix = '{' + ns + '}' if ns else ''
                    
                    # Busca o elemento infCpl
                    inf_cpl_paths = [
                        f'.//{ns_prefix}infCpl',
                        f'./{ns_prefix}NFe/{ns_prefix}infNFe/{ns_prefix}infAdic/{ns_prefix}infCpl',
                        f'./{ns_prefix}infNFe/{ns_prefix}infAdic/{ns_prefix}infCpl',
                        './infCpl'
                    ]
                    
                    for path in inf_cpl_paths:
                        try:
                            elem = root.find(path)
                            if elem is not None and elem.text:
                                inf_cpl = elem.text
                                print(f"  Informações complementares encontradas no caminho: {path}")
                                break
                        except:
                            continue
                
                # Tentativa com diferentes namespaces e caminhos para encontrar o destinatário
                destinatario = None
                dest_nome = None
                dest_cnpj = None
                
                for ns in namespaces:
                    if dest_nome is not None:
                        break
                        
                    ns_prefix = '{' + ns + '}' if ns else ''
                    
                    # Busca o elemento dest
                    dest_paths = [
                        f'.//{ns_prefix}dest',
                        f'./{ns_prefix}NFe/{ns_prefix}infNFe/{ns_prefix}dest',
                        f'./{ns_prefix}infNFe/{ns_prefix}dest',
                        './dest'
                    ]
                    
                    for path in dest_paths:
                        try:
                            destinatario = root.find(path)
                            if destinatario is not None:
                                print(f"  Encontrado elemento destinatário no caminho: {path}")
                                
                                # Busca nome dentro do elemento dest
                                nome_paths = [
                                    f'.//{ns_prefix}xNome',
                                    f'./{ns_prefix}xNome',
                                    './xNome'
                                ]
                                
                                for nome_path in nome_paths:
                                    try:
                                        elem = destinatario.find(nome_path)
                                        if elem is not None and elem.text:
                                            dest_nome = elem.text
                                            print(f"  Nome encontrado no caminho: {nome_path}")
                                            break
                                    except:
                                        continue
                                
                                # Busca CNPJ dentro do elemento dest
                                cnpj_paths = [
                                    f'.//{ns_prefix}CNPJ',
                                    f'./{ns_prefix}CNPJ',
                                    './CNPJ'
                                ]
                                
                                for cnpj_path in cnpj_paths:
                                    try:
                                        elem = destinatario.find(cnpj_path)
                                        if elem is not None and elem.text:
                                            dest_cnpj = elem.text
                                            print(f"  CNPJ encontrado no caminho: {cnpj_path}")
                                            break
                                    except:
                                        continue
                                        
                                if dest_nome or dest_cnpj:
                                    break
                        except:
                            continue
                
                # Atualiza os dados se encontrou algo
                atualizado = False
                if dest_nome:
                    nota_fiscal.destinatario_nome = dest_nome
                    atualizado = True
                
                if dest_cnpj:
                    nota_fiscal.destinatario_cnpj = dest_cnpj
                    atualizado = True
                
                if nat_op:
                    nota_fiscal.natureza_operacao = nat_op
                    atualizado = True
                    
                if serie:
                    nota_fiscal.serie = serie
                    atualizado = True
                
                if inf_cpl:
                    nota_fiscal.informacoes_complementares = inf_cpl
                    atualizado = True
                
                if atualizado:
                    nota_fiscal.save(update_fields=['destinatario_nome', 'destinatario_cnpj', 'natureza_operacao', 'serie', 'informacoes_complementares'])
                    print(f"  Dados atualizados:")
                    print(f"    - Destinatário: {nota_fiscal.destinatario_nome or 'Não informado'}")
                    print(f"    - CNPJ: {nota_fiscal.destinatario_cnpj or 'Não informado'}")
                    print(f"    - Série: {nota_fiscal.serie or 'Não informado'}")
                    print(f"    - Natureza da Operação: {nota_fiscal.natureza_operacao or 'Não informado'}")
                    if inf_cpl:
                        print(f"    - Informações Complementares: {inf_cpl[:100]}..." if len(inf_cpl) > 100 else f"    - Informações Complementares: {inf_cpl}")
                else:
                    print("  Não foi possível encontrar os dados no XML")
            else:
                print("  XML não disponível para esta nota fiscal")
                
        except Exception as e:
            print(f"  ERRO: {str(e)}")
        
        print("-" * 50)
    
    print("Extração concluída!")

if __name__ == "__main__":
    extrair_dados_notas_fiscais() 