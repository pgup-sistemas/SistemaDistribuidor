import re
import requests
import json
from typing import Dict, Optional, Tuple

class ValidationService:
    """Serviço para validação de documentos brasileiros e consulta de CEP"""
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida um CPF brasileiro
        Args:
            cpf: String com o CPF (com ou sem formatação)
        Returns:
            True se o CPF for válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula o primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0
        
        # Verifica o primeiro dígito
        if int(cpf[9]) != digit1:
            return False
        
        # Calcula o segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0
        
        # Verifica o segundo dígito
        return int(cpf[10]) == digit2
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Valida um CNPJ brasileiro
        Args:
            cnpj: String com o CNPJ (com ou sem formatação)
        Returns:
            True se o CNPJ for válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cnpj = re.sub(r'\D', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Pesos para o cálculo dos dígitos verificadores
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # Calcula o primeiro dígito verificador
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        remainder1 = sum1 % 11
        digit1 = 0 if remainder1 < 2 else 11 - remainder1
        
        # Verifica o primeiro dígito
        if int(cnpj[12]) != digit1:
            return False
        
        # Calcula o segundo dígito verificador
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        remainder2 = sum2 % 11
        digit2 = 0 if remainder2 < 2 else 11 - remainder2
        
        # Verifica o segundo dígito
        return int(cnpj[13]) == digit2
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """
        Formata um CPF com pontos e hífen
        Args:
            cpf: String com números do CPF
        Returns:
            CPF formatado (000.000.000-00)
        """
        cpf = re.sub(r'\D', '', cpf)
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf
    
    @staticmethod
    def format_cnpj(cnpj: str) -> str:
        """
        Formata um CNPJ com pontos, barra e hífen
        Args:
            cnpj: String com números do CNPJ
        Returns:
            CNPJ formatado (00.000.000/0000-00)
        """
        cnpj = re.sub(r'\D', '', cnpj)
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
    
    @staticmethod
    def format_cep(cep: str) -> str:
        """
        Formata um CEP com hífen
        Args:
            cep: String com números do CEP
        Returns:
            CEP formatado (00000-000)
        """
        cep = re.sub(r'\D', '', cep)
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep
    
    @staticmethod
    def get_address_by_cep(cep: str) -> Optional[Dict]:
        """
        Consulta endereço pelo CEP usando a API ViaCEP
        Args:
            cep: String com o CEP (com ou sem formatação)
        Returns:
            Dicionário com os dados do endereço ou None se não encontrado
        """
        # Remove caracteres não numéricos
        cep = re.sub(r'\D', '', cep)
        
        # Verifica se o CEP tem 8 dígitos
        if len(cep) != 8:
            return None
        
        try:
            # Faz a consulta na API ViaCEP
            url = f"https://viacep.com.br/ws/{cep}/json/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica se o CEP foi encontrado
                if 'erro' not in data:
                    return {
                        'cep': data.get('cep', ''),
                        'logradouro': data.get('logradouro', ''),
                        'complemento': data.get('complemento', ''),
                        'bairro': data.get('bairro', ''),
                        'localidade': data.get('localidade', ''),  # cidade
                        'uf': data.get('uf', ''),
                        'ibge': data.get('ibge', ''),
                        'gia': data.get('gia', ''),
                        'ddd': data.get('ddd', ''),
                        'siafi': data.get('siafi', '')
                    }
            
            return None
            
        except (requests.RequestException, json.JSONDecodeError, KeyError):
            return None
    
    @staticmethod
    def validate_cep(cep: str) -> bool:
        """
        Valida se um CEP tem formato correto
        Args:
            cep: String com o CEP
        Returns:
            True se o formato for válido, False caso contrário
        """
        cep = re.sub(r'\D', '', cep)
        return len(cep) == 8 and cep.isdigit()
    
    @staticmethod
    def clean_document(document: str) -> str:
        """
        Remove formatação de documentos (CPF/CNPJ)
        Args:
            document: String com o documento
        Returns:
            String apenas com números
        """
        return re.sub(r'\D', '', document)
    
    @staticmethod
    def identify_document_type(document: str) -> str:
        """
        Identifica o tipo de documento baseado no tamanho
        Args:
            document: String com o documento
        Returns:
            'cpf', 'cnpj' ou 'unknown'
        """
        clean_doc = ValidationService.clean_document(document)
        if len(clean_doc) == 11:
            return 'cpf'
        elif len(clean_doc) == 14:
            return 'cnpj'
        else:
            return 'unknown'
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Formata um telefone brasileiro
        Args:
            phone: String com números do telefone
        Returns:
            Telefone formatado
        """
        phone = re.sub(r'\D', '', phone)
        if len(phone) == 11:  # Celular
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        elif len(phone) == 10:  # Fixo
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        return phone
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida formato de email
        Args:
            email: String com o email
        Returns:
            True se o formato for válido, False caso contrário
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))