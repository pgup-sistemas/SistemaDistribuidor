# Configuração do Sistema de Pagamentos

## Visão Geral
O sistema suporta múltiplos gateways de pagamento através de uma interface unificada. Atualmente implementados:
- MercadoPago (completo)
- Stripe (stub preparado para implementação)

## Configuração Rápida

### 1. Configure o ambiente
```powershell
# Execute o script de configuração
.\setup_env.ps1
```

### 2. Ou configure manualmente
Copie `.env.example` para `.env` e configure:

```ini
# Gateway (mercadopago ou stripe)
PAYMENT_PROVIDER=mercadopago

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=seu-token-aqui
MERCADOPAGO_PUBLIC_KEY=sua-chave-publica
MERCADOPAGO_WEBHOOK_SECRET=seu-segredo-webhook
MERCADOPAGO_SANDBOX=true  # true para testes, false para produção

# Stripe (quando implementado)
STRIPE_SECRET_KEY=seu-token-aqui
STRIPE_PUBLIC_KEY=sua-chave-publica
STRIPE_WEBHOOK_SECRET=seu-segredo-webhook

# URL Base (para callbacks)
BASE_URL=http://localhost:5000
```

## Modo Sandbox/Testes

### MercadoPago
1. Use `MERCADOPAGO_SANDBOX=true`
2. Acesse `/payments/info` para ver cartões de teste
3. Cartões disponíveis:
   - 4509 9535 6623 3704 (aprovado)
   - 5031 7557 3453 0604 (aprovado)
   - 4774 0614 7401 7001 (rejeitado)

### Stripe (quando implementado)
1. Use chaves de teste do painel Stripe
2. Cartões de teste:
   - 4242 4242 4242 4242 (aprovado)
   - 4000 0000 0000 9995 (rejeitado)

## Webhooks

### Configuração Local
Para testar webhooks localmente:
1. Instale ngrok: `choco install ngrok`
2. Execute: `ngrok http 5000`
3. Use a URL fornecida para configurar no painel do gateway

### URLs de Webhook
- MercadoPago: `https://seu-dominio/payments/webhook`
- Stripe: `https://seu-dominio/payments/webhook` (mesmo endpoint)

## Desenvolvimento

### Estrutura
- `services/payment_factory.py` - Fábrica de gateways
- `services/mercadopago_service.py` - Implementação MercadoPago
- `services/stripe_service.py` - Stub do Stripe
- `routes/payments.py` - Rotas de pagamento
- `templates/payments/` - Templates relacionados

### Adicionando novo gateway
1. Implemente a interface `PaymentGateway`
2. Adicione o provider na fábrica
3. Configure as variáveis de ambiente
4. Atualize a documentação

## Troubleshooting

### Erros comuns
- **BuildError em templates**: Verifique se as rotas existem em `routes/payments.py`
- **Webhook 404**: Verifique se a URL base está configurada corretamente
- **Erro de autenticação**: Verifique as chaves de API no .env

### Logs
- Todos os erros são registrados via `logging`
- Procure por "MercadoPago Service" ou "Stripe Service" nos logs

## Segurança

### Boas Práticas
- Nunca comite o `.env` (está no .gitignore)
- Use HTTPS em produção
- Valide as assinaturas dos webhooks
- Use as chaves de sandbox para testes

### Produção
1. Configure HTTPS
2. Defina `BASE_URL` para seu domínio
3. Use chaves de produção
4. Configure os webhooks com SSL
5. Desative o modo sandbox

## Configuração de Email (segurança)

- Para envio de emails recomendamos utilizar senhas de app (App Password) quando disponível (ex.: Gmail com 2FA). Isso evita expor a senha principal da conta.
- Sempre roteie as credenciais em um cofre de segredos em produção (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault) em vez de arquivos em texto plano.
- Após testes, rotacione (invalide) a senha de app utilizada para evitar uso indevido.