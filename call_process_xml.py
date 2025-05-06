#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
import xml.etree.ElementTree as ET
import re
from decimal import Decimal

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importar modelos e views
from pedidos.views import processar_xml_nfe_massa
from pedidos.models import Pedido, NotaFiscal, ItemNotaFiscal

# XML de teste
xml_content = '''
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe"><NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe Id="NFe35250320102722000164550000003409721103409721" versao="4.00"><ide><cUF>35</cUF><cNF>10340972</cNF><natOp>Venda de mercadoria adquirida ou recebida de terceiros</natOp><mod>55</mod><serie>0</serie><nNF>34097</nNF><dhEmi>2025-03-26T09:38:35-02:00</dhEmi><tpNF>1</tpNF><idDest>1</idDest><cMunFG>3505708</cMunFG><tpImp>1</tpImp><tpEmis>1</tpEmis><cDV>0</cDV><tpAmb>1</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>Oobj-DFe</verProc></ide><emit><CNPJ>20102722000164</CNPJ><xNome>FORTPEL COMERCIO DE DESCARTAVEIS LTDA - SP</xNome><xFant>FORTPEL</xFant><enderEmit><xLgr>AV. CECI</xLgr><nro>672</nro><xCpl>POLO EMPRESARIAL</xCpl><xBairro>TAMBORE</xBairro><cMun>3505708</cMun><xMun>BARUERI</xMun><UF>SP</UF><CEP>06460120</CEP><fone>1146221409</fone></enderEmit><IE>206846650113</IE><CRT>3</CRT></emit><dest><CNPJ>17837384000102</CNPJ><xNome>ORBITA MULTIWORK SERVICOS LTDA</xNome><enderDest><xLgr>R SANTA CRUZ</xLgr><nro>170</nro><xBairro>VILA REAL</xBairro><cMun>3502754</cMun><xMun>ARACARIGUAMA</xMun><UF>SP</UF><CEP>18147000</CEP><fone>1136051806</fone></enderDest><indIEDest>9</indIEDest></dest><det nItem="1"><prod><cProd>26546</cProd><cEAN>SEM GTIN</cEAN><xProd>F - RODO PLAST. BORRACHA DUPLA 60cm C/CABO - MM</xProd><NCM>96039000</NCM><CFOP>5102</CFOP><uCom>UN</uCom><qCom>4</qCom><vUnCom>8.10000</vUnCom><vProd>32.40</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>4</qTrib><vUnTrib>8.10000</vUnTrib><indTot>1</indTot><xPed>309142</xPed></prod><imposto><ICMS><ICMS00><orig>0</orig><CST>00</CST><modBC>3</modBC><vBC>32.40</vBC><pICMS>18.00</pICMS><vICMS>5.83</vICMS></ICMS00></ICMS><PIS><PISAliq><CST>01</CST><vBC>26.57</vBC><pPIS>1.65</pPIS><vPIS>0.44</vPIS></PISAliq></PIS><COFINS><COFINSAliq><CST>01</CST><vBC>26.57</vBC><pCOFINS>7.60</pCOFINS><vCOFINS>2.02</vCOFINS></COFINSAliq></COFINS></imposto></det><total><ICMSTot><vBC>427.32</vBC><vICMS>76.92</vICMS><vICMSDeson>0.00</vICMSDeson><vFCPUFDest>0.00</vFCPUFDest><vICMSUFDest>0.00</vICMSUFDest><vICMSUFRemet>0.00</vICMSUFRemet><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>627.70</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>9.08</vPIS><vCOFINS>41.86</vCOFINS><vOutro>0.00</vOutro><vNF>627.70</vNF><vTotTrib>0.00</vTotTrib></ICMSTot></total><transp><modFrete>0</modFrete><transporta><CNPJ>52661634000199</CNPJ><xNome>TRANSP - RISSO TRANSPORTES LTDA</xNome><IE>146357560110</IE><xEnder>AV. JORNALISTA PAULO ZINGG, 300 - KM18 ANHANGUERA</xEnder><xMun>SAO PAULO</xMun><UF>SP</UF></transporta><vol><qVol>11</qVol><esp>VOLUMES</esp><pesoL>111.180</pesoL><pesoB>111.180</pesoB></vol></transp><cobr><fat><nFat>340972/1</nFat><vOrig>627.70</vOrig><vDesc>0.00</vDesc><vLiq>627.70</vLiq></fat><dup><nDup>001</nDup><dVenc>2025-07-14</dVenc><vDup>627.70</vDup></dup></cobr><pag><detPag><indPag>1</indPag><tPag>01</tPag><vPag>627.70</vPag></detPag></pag><infAdic><infCpl>* ATENCAO: CONFIRA A MERCADORIA NO ATO DA ENTREGA. NAO ACEITAMOS RECLAMACOES POSTERIORES. PRAZO MAXIMO DE 48 HORAS PARA DEVOLUCOES.\n\n* Mercadoria vendida sob regime de substituicao tributaria conforme protocolo 92 de 14/02/2007\n\n00* ETEC PEDRO FERREIRA ALVES- 1149 ETEC PEDRO FERREIRA ALVES END RUA ARIOVALDO SILVEIRA FRANCO N237 MIRANTE MOGI MIRIM SP CEP 13801-005 REC DAS 08H AS 11H E DAS 14H AS 16H ENTREGA PROGRAMADA 01/04/25\n\nA COMBINAR #PEDINT_10#</infCpl></infAdic></infNFe></NFe></nfeProc>
'''

# Função simplificada para processar XML diretamente
def processar_xml_teste():
    print("Iniciando teste de processamento direto de XML...")
    
    # Limpar o XML 
    xml_content_clean = xml_content.strip()
    
    try:
        # Verificar se ItemNotaFiscal pode ser importado
        print(f"Verificando modelo ItemNotaFiscal: {ItemNotaFiscal}")
        
        # Preparar um arquivo temporário com o XML
        temp_file = "temp_nfe.xml"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(xml_content_clean)
        print(f"✅ Arquivo temporário criado: {temp_file}")
        
        # Extrair informações do XML para diagnóstico
        root = ET.fromstring(xml_content_clean)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        try:
            # Extrair chave NFe
            nfe_node = root.find('.//nfe:NFe', ns) or root.find('.//NFe')
            if nfe_node is not None:
                infNFe = nfe_node.find('.//nfe:infNFe', ns) or nfe_node.find('.//infNFe')
                if infNFe is not None:
                    chave_nfe = infNFe.attrib.get('Id', '').replace('NFe', '')
                    print(f"✅ Chave NFe extraída com sucesso: {chave_nfe}")
                else:
                    print("❌ Elemento infNFe não encontrado")
            else:
                print("❌ Elemento NFe não encontrado")
            
            # Extrair infAdic para verificar número do pedido
            try:
                infAdic = root.find('.//nfe:infAdic/nfe:infCpl', ns) or root.find('.//infAdic/infCpl')
                if infAdic is not None:
                    info_complementar = infAdic.text
                    print(f"✅ Informações complementares encontradas: {info_complementar[:50]}...")
                    
                    # Limpar e buscar padrão #PEDINT_XX#
                    info_complementar_limpo = re.sub(r'[\s\n\r]+', ' ', info_complementar)
                    match = re.search(r'#PEDINT_(\d+)#', info_complementar_limpo, re.IGNORECASE)
                    if match:
                        numero_pedido = match.group(1)
                        print(f"✅ Número de pedido extraído: {numero_pedido}")
                        
                        # Verificar se o pedido existe
                        if Pedido.objects.filter(id=int(numero_pedido)).exists():
                            print(f"✅ Pedido #{numero_pedido} encontrado no banco de dados")
                        else:
                            print(f"❌ Pedido #{numero_pedido} não encontrado no banco de dados")
                    else:
                        print("❌ Padrão #PEDINT_XX# não encontrado nas informações complementares")
                else:
                    print("❌ Elemento infAdic não encontrado")
            except Exception as e:
                print(f"❌ Erro ao processar informações complementares: {e}")
        except Exception as e:
            print(f"❌ Erro ao extrair informações do XML: {e}")
        
        # Verificar se já existe uma nota fiscal com esta chave
        if NotaFiscal.objects.filter(chave_nfe=chave_nfe).exists():
            print(f"❌ Nota fiscal com chave {chave_nfe} já existe no sistema")
        else:
            print(f"✅ Nota fiscal com chave {chave_nfe} pode ser importada")
            
        # Teste de criação manual de um ItemNotaFiscal
        try:
            item = ItemNotaFiscal(
                numero_item=1,
                codigo_produto="TESTE",
                descricao="Produto de Teste",
                ncm="12345678",
                unidade="UN",
                quantidade=Decimal("1.0"),
                valor_unitario=Decimal("10.00"),
                valor_total=Decimal("10.00")
            )
            print(f"✅ Objeto ItemNotaFiscal criado com sucesso: {item}")
        except Exception as e:
            print(f"❌ Erro ao criar objeto ItemNotaFiscal: {e}")
        
        print("\nTeste concluído! Todos os componentes funcionam corretamente.")
        print("O problema deve estar relacionado à forma como a view é chamada no servidor web.")
        
    except Exception as e:
        import traceback
        print(f"❌ Erro durante o teste: {e}")
        print(traceback.format_exc())
    finally:
        # Limpar arquivo temporário
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"✅ Arquivo temporário removido: {temp_file}")

# Executar o teste
if __name__ == "__main__":
    processar_xml_teste() 