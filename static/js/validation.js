/**
 * Biblioteca de validação e formatação para documentos brasileiros
 */

class DocumentValidator {
    static formatCPF(cpf) {
        // Remove caracteres não numéricos
        cpf = cpf.replace(/\D/g, '');
        
        // Aplica a máscara conforme o usuário digita
        if (cpf.length <= 3) {
            return cpf;
        } else if (cpf.length <= 6) {
            return cpf.replace(/(\d{3})(\d+)/, '$1.$2');
        } else if (cpf.length <= 9) {
            return cpf.replace(/(\d{3})(\d{3})(\d+)/, '$1.$2.$3');
        } else {
            return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d+)/, '$1.$2.$3-$4');
        }
    }

    static formatCNPJ(cnpj) {
        // Remove caracteres não numéricos
        cnpj = cnpj.replace(/\D/g, '');
        
        // Aplica a máscara conforme o usuário digita
        if (cnpj.length <= 2) {
            return cnpj;
        } else if (cnpj.length <= 5) {
            return cnpj.replace(/(\d{2})(\d+)/, '$1.$2');
        } else if (cnpj.length <= 8) {
            return cnpj.replace(/(\d{2})(\d{3})(\d+)/, '$1.$2.$3');
        } else if (cnpj.length <= 12) {
            return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d+)/, '$1.$2.$3/$4');
        } else {
            return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d+)/, '$1.$2.$3/$4-$5');
        }
    }

    static formatCEP(cep) {
        // Remove caracteres não numéricos
        cep = cep.replace(/\D/g, '');
        
        // Aplica a máscara conforme o usuário digita
        if (cep.length <= 5) {
            return cep;
        } else {
            return cep.replace(/(\d{5})(\d+)/, '$1-$2');
        }
    }

    static formatPhone(phone) {
        // Remove caracteres não numéricos
        phone = phone.replace(/\D/g, '');
        
        // Aplica a máscara conforme o usuário digita
        if (phone.length <= 2) {
            return phone;
        } else if (phone.length <= 6) {
            return phone.replace(/(\d{2})(\d+)/, '($1) $2');
        } else if (phone.length <= 10) {
            return phone.replace(/(\d{2})(\d{4})(\d+)/, '($1) $2-$3');
        } else {
            return phone.replace(/(\d{2})(\d{5})(\d+)/, '($1) $2-$3');
        }
    }

    static async validateDocument(document, fieldElement = null) {
        try {
            const response = await fetch('/api/validation/document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ document: document })
            });

            const result = await response.json();
            
            if (fieldElement) {
                this.updateFieldValidation(fieldElement, result.valid, result.message);
            }
            
            return result;
        } catch (error) {
            console.error('Erro ao validar documento:', error);
            return { valid: false, message: 'Erro na validação' };
        }
    }

    static async validateCEP(cep, onSuccess = null) {
        try {
            const response = await fetch('/api/validation/cep', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cep: cep })
            });

            const result = await response.json();
            
            if (result.success && onSuccess) {
                onSuccess(result.data);
            }
            
            return result;
        } catch (error) {
            console.error('Erro ao consultar CEP:', error);
            return { success: false, message: 'Erro na consulta do CEP' };
        }
    }

    static updateFieldValidation(fieldElement, isValid, message) {
        // Remove classes anteriores
        fieldElement.classList.remove('is-valid', 'is-invalid');
        
        // Remove feedback anterior
        const feedback = fieldElement.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            feedback.remove();
        }
        
        // Adiciona nova classe e feedback
        if (isValid) {
            fieldElement.classList.add('is-valid');
            const validFeedback = document.createElement('div');
            validFeedback.className = 'valid-feedback';
            validFeedback.textContent = message;
            fieldElement.parentNode.appendChild(validFeedback);
        } else {
            fieldElement.classList.add('is-invalid');
            const invalidFeedback = document.createElement('div');
            invalidFeedback.className = 'invalid-feedback';
            invalidFeedback.textContent = message;
            fieldElement.parentNode.appendChild(invalidFeedback);
        }
    }

    static setupDocumentField(fieldId, validationDelay = 1000) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        let validationTimeout;

        field.addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            
            // Auto-formatação baseada no tamanho
            if (value.length <= 11) {
                // Formatar como CPF
                e.target.value = DocumentValidator.formatCPF(value);
            } else {
                // Formatar como CNPJ
                e.target.value = DocumentValidator.formatCNPJ(value);
            }
            
            // Limpar timeout anterior
            clearTimeout(validationTimeout);
            
            // Validar após delay
            if (value.length >= 11) {
                validationTimeout = setTimeout(() => {
                    DocumentValidator.validateDocument(value, field);
                }, validationDelay);
            } else {
                // Limpar validação se muito pouco texto
                field.classList.remove('is-valid', 'is-invalid');
                const feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
                if (feedback) feedback.remove();
            }
        });
    }

    static setupCEPField(cepFieldId, options = {}) {
        const cepField = document.getElementById(cepFieldId);
        if (!cepField) return;

        let validationTimeout;

        cepField.addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            
            // Auto-formatação
            e.target.value = DocumentValidator.formatCEP(value);
            
            // Limpar timeout anterior
            clearTimeout(validationTimeout);
            
            // Consultar CEP quando completo
            if (value.length === 8) {
                validationTimeout = setTimeout(async () => {
                    const result = await DocumentValidator.validateCEP(value, (data) => {
                        // Preencher campos de endereço automaticamente
                        if (options.addressField) {
                            const addressField = document.getElementById(options.addressField);
                            if (addressField && data.logradouro) {
                                addressField.value = data.logradouro;
                            }
                        }
                        
                        if (options.neighborhoodField) {
                            const neighborhoodField = document.getElementById(options.neighborhoodField);
                            if (neighborhoodField && data.bairro) {
                                neighborhoodField.value = data.bairro;
                            }
                        }
                        
                        if (options.cityField) {
                            const cityField = document.getElementById(options.cityField);
                            if (cityField && data.localidade) {
                                cityField.value = data.localidade;
                            }
                        }
                        
                        if (options.stateField) {
                            const stateField = document.getElementById(options.stateField);
                            if (stateField && data.uf) {
                                stateField.value = data.uf;
                            }
                        }
                        
                        // Focar no próximo campo
                        if (options.nextField) {
                            const nextField = document.getElementById(options.nextField);
                            if (nextField) {
                                nextField.focus();
                            }
                        }
                    });
                    
                    DocumentValidator.updateFieldValidation(
                        cepField, 
                        result.success, 
                        result.message
                    );
                }, 500);
            }
        });
    }

    static setupPhoneField(phoneFieldId) {
        const phoneField = document.getElementById(phoneFieldId);
        if (!phoneField) return;

        phoneField.addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            e.target.value = DocumentValidator.formatPhone(value);
        });
    }

    static setupEmailField(emailFieldId, validationDelay = 1000) {
        const emailField = document.getElementById(emailFieldId);
        if (!emailField) return;

        let validationTimeout;

        emailField.addEventListener('input', function(e) {
            const value = e.target.value;
            
            // Limpar timeout anterior
            clearTimeout(validationTimeout);
            
            // Validar após delay
            if (value.length > 0) {
                validationTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch('/api/validation/email', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ email: value })
                        });

                        const result = await response.json();
                        DocumentValidator.updateFieldValidation(emailField, result.valid, result.message);
                    } catch (error) {
                        console.error('Erro ao validar email:', error);
                    }
                }, validationDelay);
            } else {
                // Limpar validação se campo vazio
                emailField.classList.remove('is-valid', 'is-invalid');
                const feedback = emailField.parentNode.querySelector('.invalid-feedback, .valid-feedback');
                if (feedback) feedback.remove();
            }
        });
    }

    // Função utilitária para inicializar todos os campos de um formulário
    static initializeForm(config = {}) {
        // Configurar campos de documento
        if (config.documentFields) {
            config.documentFields.forEach(fieldId => {
                this.setupDocumentField(fieldId);
            });
        }
        
        // Configurar campos de CEP
        if (config.cepFields) {
            config.cepFields.forEach(cepConfig => {
                this.setupCEPField(cepConfig.fieldId, cepConfig.options || {});
            });
        }
        
        // Configurar campos de telefone
        if (config.phoneFields) {
            config.phoneFields.forEach(fieldId => {
                this.setupPhoneField(fieldId);
            });
        }
        
        // Configurar campos de email
        if (config.emailFields) {
            config.emailFields.forEach(fieldId => {
                this.setupEmailField(fieldId);
            });
        }
    }
}

// Disponibilizar globalmente
window.DocumentValidator = DocumentValidator;