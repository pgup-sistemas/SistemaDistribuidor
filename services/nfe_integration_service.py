#!/usr/bin/env python3
"""
Serviço de Integração NF-e - Sistema Distribuidor
Infraestrutura preparada para integração com APIs de NF-e (gratuita inicialmente)
"""

import os
import re
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from models import db, Product, Supplier, Category, StockMovement

logger = logging.getLogger(__name__)

class NFeIntegrationService:
    """
    Serviço de integração com NF-e preparado para futuras implementações
    Atualmente simula integração - pronto para APIs reais
    """

    def __init__(self):
        # Configurações para futura integração
        self.environment = os.environ.get('NFE_ENVIRONMENT', 'homologation')  # production/homologation
        self.cert_path = os.environ.get('NFE_CERT_PATH')
        self.cert_password = os.environ.get('NFE_CERT_PASSWORD')
        self.api_provider = os.environ.get('NFE_API_PROVIDER', 'sefaz')  # sefaz, focusnfe, etc.

        # Configurações de negócio
        self.default_markup = Decimal(str(os.environ.get('NFE_DEFAULT_MARKUP', '1.3')))  # 30% markup
        self.default_min_stock = int(os.environ.get('NFE_DEFAULT_MIN_STOCK', '5'))

        # URLs das APIs (preparado para futuras implementações)
        self.api_urls = {
            'sefaz': {
                'production': 'https://nfe.fazenda.sp.gov.br/ws/',
                'homologation': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/'
            },
            'focusnfe': {
                'production': 'https://api.focusnfe.com.br/v2/',
                'homologation': 'https://homologacao.focusnfe.com.br/v2/'
            }
        }

    def consultar_nfe_simulada(self, chave_acesso: str) -> Dict:
        """
        Simulação de consulta NF-e
        Em produção, seria substituída por chamada real à API
        """
        logger.info(f"Simulando consulta NF-e: {chave_acesso}")

        # Simular dados de uma NF-e
        return {
            'chave_acesso': chave_acesso,
            'numero': '000012345',
            'serie': '001',
            'data_emissao': datetime.now().isoformat(),
            'fornecedor': {
                'cnpj': '12.345.678/0001-90',
                'nome': 'Fornecedor Exemplo Ltda',
                'endereco': 'Rua Exemplo, 123'
            },
            'itens': [
                {
                    'codigo': 'PROD001',
                    'descricao': 'Produto Exemplo 1',
                    'ncm': '12345678',
                    'cfop': '5101',
                    'unidade': 'UN',
                    'quantidade': 10,
                    'valor_unitario': 15.50,
                    'valor_total': 155.00
                },
                {
                    'codigo': 'PROD002',
                    'descricao': 'Produto Exemplo 2',
                    'ncm': '87654321',
                    'cfop': '5101',
                    'unidade': 'KG',
                    'quantidade': 5,
                    'valor_unitario': 25.00,
                    'valor_total': 125.00
                }
            ],
            'totais': {
                'valor_produtos': 280.00,
                'valor_icms': 33.60,
                'valor_ipi': 0.00,
                'valor_pis': 2.24,
                'valor_cofins': 10.36,
                'valor_total': 326.20
            }
        }

    def consultar_nfe_api(self, chave_acesso: str) -> Dict:
        """
        Método preparado para integração real com APIs
        Atualmente retorna simulação
        """
        try:
            if self.api_provider == 'focusnfe':
                return self._consultar_focusnfe(chave_acesso)
            elif self.api_provider == 'sefaz':
                return self._consultar_sefaz(chave_acesso)
            else:
                # Fallback para simulação
                return self.consultar_nfe_simulada(chave_acesso)

        except Exception as e:
            logger.error(f"Erro na consulta NF-e: {e}")
            raise

    def _consultar_focusnfe(self, chave_acesso: str) -> Dict:
        """
        Implementação preparada para Focus NFe
        Requer contratação do serviço
        """
        # TODO: Implementar chamada real para Focus NFe
        # import requests
        # url = f"{self.api_urls['focusnfe'][self.environment]}nfe/{chave_acesso}"
        # headers = {'Authorization': f'Bearer {os.environ.get("FOCUSNFE_TOKEN")}'}
        # response = requests.get(url, headers=headers)
        # return response.json()

        logger.warning("Focus NFe não implementado - usando simulação")
        return self.consultar_nfe_simulada(chave_acesso)

    def _consultar_sefaz(self, chave_acesso: str) -> Dict:
        """
        Implementação preparada para SEFAZ direto
        Requer certificado digital
        """
        # TODO: Implementar consulta SEFAZ
        # Requer certificado A1/A3 e bibliotecas específicas

        logger.warning("SEFAZ direto não implementado - usando simulação")
        return self.consultar_nfe_simulada(chave_acesso)

    def parse_xml_nfe(self, xml_content: str) -> Dict:
        """
        Parser XML de NF-e preparado para uso futuro
        """
        try:
            root = ET.fromstring(xml_content)

            # Namespaces da NF-e
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            # Extrair dados básicos
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                raise ValueError("XML NF-e inválido")

            chave_acesso = inf_nfe.get('Id')[3:]  # Remove 'NFe'

            # Dados do emitente (fornecedor)
            emit = root.find('.//nfe:emit', ns)
            fornecedor = {
                'cnpj': emit.find('nfe:CNPJ', ns).text,
                'nome': emit.find('nfe:xNome', ns).text,
            }

            # Itens da NF-e
            itens = []
            det_elements = root.findall('.//nfe:det', ns)

            for det in det_elements:
                prod = det.find('nfe:prod', ns)

                item = {
                    'codigo': prod.find('nfe:cProd', ns).text,
                    'descricao': prod.find('nfe:xProd', ns).text,
                    'ncm': prod.find('nfe:NCM', ns).text,
                    'cfop': prod.find('nfe:CFOP', ns).text,
                    'unidade': prod.find('nfe:uCom', ns).text,
                    'quantidade': float(prod.find('nfe:qCom', ns).text),
                    'valor_unitario': float(prod.find('nfe:vUnCom', ns).text),
                    'valor_total': float(prod.find('nfe:vProd', ns).text)
                }
                itens.append(item)

            return {
                'chave_acesso': chave_acesso,
                'fornecedor': fornecedor,
                'itens': itens,
                'fonte': 'xml'
            }

        except Exception as e:
            logger.error(f"Erro ao parsear XML NF-e: {e}")
            raise ValueError(f"XML NF-e inválido: {e}")

    def processar_itens_nfe(self, nfe_data: Dict, supplier_id: int) -> Dict:
        """
        Processa itens da NF-e e cria/atualiza produtos
        """
        itens = nfe_data.get('itens', [])
        supplier = Supplier.query.get(supplier_id)

        if not supplier:
            raise ValueError(f"Fornecedor ID {supplier_id} não encontrado")

        resultados = {
            'processados': 0,
            'criados': 0,
            'atualizados': 0,
            'erros': 0,
            'detalhes': []
        }

        for item in itens:
            try:
                # Verificar se produto já existe
                produto_existente = Product.query.filter_by(
                    sku=item['codigo'],
                    active=True
                ).first()

                if produto_existente:
                    # Atualizar produto existente
                    estoque_anterior = produto_existente.current_stock
                    produto_existente.current_stock += int(item['quantidade'])
                    produto_existente.cost_price = Decimal(str(item['valor_unitario']))

                    # Registrar movimentação
                    movimento = StockMovement(
                        product_id=produto_existente.id,
                        movement_type='entry',
                        quantity=int(item['quantidade']),
                        reason=f'Entrada NF-e: {nfe_data.get("chave_acesso", "N/A")}',
                        user_id=1  # TODO: Usar usuário atual
                    )
                    db.session.add(movimento)

                    resultados['atualizados'] += 1
                    resultados['detalhes'].append({
                        'sku': item['codigo'],
                        'acao': 'atualizado',
                        'estoque_anterior': estoque_anterior,
                        'estoque_novo': produto_existente.current_stock
                    })

                else:
                    # Criar novo produto
                    # Calcular preço de venda com markup
                    preco_venda = Decimal(str(item['valor_unitario'])) * self.default_markup

                    novo_produto = Product(
                        sku=item['codigo'],
                        name=item['descricao'][:100],  # Limitar tamanho
                        description=f'Produto importado NF-e: {nfe_data.get("chave_acesso", "N/A")}',
                        sale_price=preco_venda,
                        cost_price=Decimal(str(item['valor_unitario'])),
                        current_stock=int(item['quantidade']),
                        minimum_stock=self.default_min_stock,
                        unit=item.get('unidade', 'UN'),
                        supplier_id=supplier_id
                    )

                    # Verificar se categoria existe ou criar
                    categoria_nome = f"NF-e {supplier.name}"
                    categoria = Category.query.filter_by(
                        name=categoria_nome,
                        active=True
                    ).first()

                    if not categoria:
                        categoria = Category(
                            name=categoria_nome,
                            description=f'Categoria criada automaticamente para produtos NF-e do fornecedor {supplier.name}'
                        )
                        db.session.add(categoria)
                        db.session.flush()

                    novo_produto.category_id = categoria.id
                    db.session.add(novo_produto)
                    db.session.flush()

                    # Registrar movimentação inicial
                    movimento = StockMovement(
                        product_id=novo_produto.id,
                        movement_type='entry',
                        quantity=int(item['quantidade']),
                        reason=f'Entrada inicial NF-e: {nfe_data.get("chave_acesso", "N/A")}',
                        user_id=1  # TODO: Usar usuário atual
                    )
                    db.session.add(movimento)

                    resultados['criados'] += 1
                    resultados['detalhes'].append({
                        'sku': item['codigo'],
                        'acao': 'criado',
                        'estoque': int(item['quantidade'])
                    })

                resultados['processados'] += 1

            except Exception as e:
                logger.error(f"Erro ao processar item {item.get('codigo', 'N/A')}: {e}")
                resultados['erros'] += 1
                resultados['detalhes'].append({
                    'sku': item.get('codigo', 'N/A'),
                    'acao': 'erro',
                    'erro': str(e)
                })

        return resultados

    def importar_nfe_completa(self, chave_acesso: str, supplier_id: int, fonte: str = 'api') -> Dict:
        """
        Fluxo completo de importação NF-e
        """
        try:
            logger.info(f"Iniciando importação NF-e: {chave_acesso}")

            # 1. Consultar NF-e
            if fonte == 'api':
                nfe_data = self.consultar_nfe_api(chave_acesso)
            else:
                # Para simulação ou XML
                nfe_data = self.consultar_nfe_simulada(chave_acesso)

            # 2. Processar itens
            resultados = self.processar_itens_nfe(nfe_data, supplier_id)

            # 3. Commit das mudanças
            db.session.commit()

            logger.info(f"Importação NF-e concluída: {resultados['processados']} itens processados")

            return {
                'success': True,
                'nfe_data': nfe_data,
                'resultados': resultados,
                'fonte': fonte
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro na importação NF-e: {e}")
            return {
                'success': False,
                'error': str(e),
                'fonte': fonte
            }

    def validar_chave_acesso(self, chave_acesso: str) -> bool:
        """
        Valida formato da chave de acesso NF-e
        """
        # Chave NF-e tem 44 dígitos
        if not re.match(r'^\d{44}$', chave_acesso):
            return False

        # TODO: Validação mais rigorosa do dígito verificador
        return True

    def get_configuracao(self) -> Dict:
        """
        Retorna configuração atual do serviço
        """
        return {
            'environment': self.environment,
            'api_provider': self.api_provider,
            'default_markup': float(self.default_markup),
            'default_min_stock': self.default_min_stock,
            'cert_configured': bool(self.cert_path),
            'ready_for_production': self._check_production_readiness()
        }

    def _check_production_readiness(self) -> bool:
        """
        Verifica se está pronto para produção
        """
        checks = [
            self.cert_path and os.path.exists(self.cert_path),
            self.cert_password,
            self.api_provider in ['focusnfe', 'sefaz'],
            self.environment == 'production'
        ]
        return all(checks)

# Instância global do serviço
nfe_service = NFeIntegrationService()

def get_nfe_service():
    """Factory function para o serviço NF-e"""
    return nfe_service