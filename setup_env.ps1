# Script para configurar variáveis de ambiente do Sistema Distribuidor
# Autor: Oézios normando
# Data: 08/11/2025

# Função para validar se uma string não está vazia
function Test-NotEmpty {
    param([string]$value, [string]$name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "Erro: $name não pode estar vazio!" -ForegroundColor Red
        return $false
    }
    return $true
}

Write-Host "Configurando variáveis de ambiente para o Sistema Distribuidor..." -ForegroundColor Green
Write-Host "IMPORTANTE: Este script irá configurar as variáveis apenas para o usuário atual." -ForegroundColor Yellow
Write-Host "As variáveis serão persistidas entre sessões do PowerShell." -ForegroundColor Yellow
Write-Host ""

# Gateway de Pagamento
$provider = Read-Host "Gateway de Pagamento (mercadopago/stripe) [padrão: mercadopago]"
if ([string]::IsNullOrWhiteSpace($provider)) { $provider = "mercadopago" }

if ($provider -eq "mercadopago") {
    $accessToken = Read-Host "MercadoPago Access Token"
    $publicKey = Read-Host "MercadoPago Public Key"
    $webhookSecret = Read-Host "MercadoPago Webhook Secret"
    $sandbox = Read-Host "Usar Sandbox? (true/false) [padrão: true]"
    
    if ([string]::IsNullOrWhiteSpace($sandbox)) { $sandbox = "true" }
    
    if ((Test-NotEmpty $accessToken "Access Token") -and (Test-NotEmpty $publicKey "Public Key")) {
        setx PAYMENT_PROVIDER "mercadopago"
        setx MERCADOPAGO_ACCESS_TOKEN $accessToken
        setx MERCADOPAGO_PUBLIC_KEY $publicKey
        setx MERCADOPAGO_WEBHOOK_SECRET $webhookSecret
        setx MERCADOPAGO_SANDBOX $sandbox
        
        Write-Host "Configurações do MercadoPago salvas com sucesso!" -ForegroundColor Green
    }
}
elseif ($provider -eq "stripe") {
    $secretKey = Read-Host "Stripe Secret Key"
    $publicKey = Read-Host "Stripe Public Key"
    $webhookSecret = Read-Host "Stripe Webhook Secret"
    
    if ((Test-NotEmpty $secretKey "Secret Key") -and (Test-NotEmpty $publicKey "Public Key")) {
        setx PAYMENT_PROVIDER "stripe"
        setx STRIPE_SECRET_KEY $secretKey
        setx STRIPE_PUBLIC_KEY $publicKey
        setx STRIPE_WEBHOOK_SECRET $webhookSecret
        
        Write-Host "Configurações do Stripe salvas com sucesso!" -ForegroundColor Green
    }
}

# URL Base
$baseUrl = Read-Host "URL Base do Sistema (ex: http://localhost:5000) [padrão: http://localhost:5000]"
if ([string]::IsNullOrWhiteSpace($baseUrl)) { $baseUrl = "http://localhost:5000" }
setx BASE_URL $baseUrl

# --- Configuração de Email (opcional) ---
Write-Host ""
Write-Host "Configuração de e-mail (opcional):" -ForegroundColor Cyan
$configureMail = Read-Host "Deseja configurar SMTP agora? (s/n) [padrão: n]"
if ([string]::IsNullOrWhiteSpace($configureMail)) { $configureMail = "n" }
if ($configureMail -eq 's' -or $configureMail -eq 'S') {
    $mailServer = Read-Host "Servidor SMTP (ex: smtp.gmail.com) [padrão: smtp.gmail.com]"
    if ([string]::IsNullOrWhiteSpace($mailServer)) { $mailServer = "smtp.gmail.com" }
    $mailPort = Read-Host "Porta SMTP [padrão: 587]"
    if ([string]::IsNullOrWhiteSpace($mailPort)) { $mailPort = "587" }
    $mailUseTls = Read-Host "Usar TLS? (true/false) [padrão: true]"
    if ([string]::IsNullOrWhiteSpace($mailUseTls)) { $mailUseTls = "true" }
    $mailUseSsl = Read-Host "Usar SSL? (true/false) [padrão: false]"
    if ([string]::IsNullOrWhiteSpace($mailUseSsl)) { $mailUseSsl = "false" }
    $mailUsername = Read-Host "Email de envio (MAIL_USERNAME)"
    $mailPassword = Read-Host "Senha de app / senha SMTP (será armazenada conforme opção abaixo)"
    $mailDefaultSender = Read-Host "MAIL_DEFAULT_SENDER (opcional) [padrão: $mailUsername]"
    if ([string]::IsNullOrWhiteSpace($mailDefaultSender)) { $mailDefaultSender = $mailUsername }

    Write-Host "Escolha como persistir as variáveis de email:" -ForegroundColor Yellow
    Write-Host "  1) Persistir nas variáveis de usuário do Windows (setx)"
    Write-Host "  2) Gravar em arquivo .env no diretório do projeto (arquivo será criado e adicionado ao .gitignore)"
    Write-Host "  3) Não persistir (apenas sessão atual)"
    $choice = Read-Host "Escolha 1, 2 ou 3 [padrão: 3]"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "3" }

    if ($choice -eq "1") {
        setx MAIL_SERVER $mailServer
        setx MAIL_PORT $mailPort
        setx MAIL_USE_TLS $mailUseTls
        setx MAIL_USE_SSL $mailUseSsl
        setx MAIL_USERNAME $mailUsername
        setx MAIL_PASSWORD $mailPassword
        setx MAIL_DEFAULT_SENDER $mailDefaultSender
        Write-Host "Variáveis de email salvas nas variáveis de usuário (setx). Abra um novo terminal para que tenham efeito." -ForegroundColor Green
    }
    elseif ($choice -eq "2") {
        $envFilePath = Join-Path -Path (Get-Location) -ChildPath ".env"
        $lines = @()
        $lines += "MAIL_SERVER=$mailServer"
        $lines += "MAIL_PORT=$mailPort"
        $lines += "MAIL_USE_TLS=$mailUseTls"
        $lines += "MAIL_USE_SSL=$mailUseSsl"
        $lines += "MAIL_USERNAME=$mailUsername"
        $lines += "MAIL_PASSWORD=$mailPassword"
        $lines += "MAIL_DEFAULT_SENDER=$mailDefaultSender"
        $lines | Out-File -FilePath $envFilePath -Encoding UTF8 -Force

        # Adicionar .env ao .gitignore se não estiver presente
        $gitignorePath = Join-Path -Path (Get-Location) -ChildPath ".gitignore"
        if (Test-Path $gitignorePath) {
            $gitignoreContent = Get-Content $gitignorePath -Raw
            if ($gitignoreContent -notmatch "(?m)^\.env$") {
                Add-Content -Path $gitignorePath -Value "`n.env`n"
                Write-Host ".env adicionado ao .gitignore" -ForegroundColor Green
            }
        } else {
            # Criar .gitignore com entry for .env
            ".env`nvenv/`n__pycache__/`n*.pyc`n" | Out-File -FilePath $gitignorePath -Encoding UTF8 -Force
            Write-Host ".gitignore criado e .env adicionado" -ForegroundColor Green
        }

        Write-Host ".env criado em $envFilePath" -ForegroundColor Green
        Write-Host "AVISO: O arquivo .env contém segredos em texto plano. Proteja este arquivo e nunca o comite em repositórios públicos." -ForegroundColor Yellow
    }
    else {
        # Apenas variável de sessão
        $env:MAIL_SERVER = $mailServer
        $env:MAIL_PORT = $mailPort
        $env:MAIL_USE_TLS = $mailUseTls
        $env:MAIL_USE_SSL = $mailUseSsl
        $env:MAIL_USERNAME = $mailUsername
        $env:MAIL_PASSWORD = $mailPassword
        $env:MAIL_DEFAULT_SENDER = $mailDefaultSender
        Write-Host "Variáveis de email definidas apenas para a sessão atual." -ForegroundColor Cyan
    }
}
Write-Host ""
Write-Host "Configuração concluída!" -ForegroundColor Green
Write-Host "IMPORTANTE: Abra um novo terminal do PowerShell para que as alterações tenham efeito." -ForegroundColor Yellow
Write-Host "Para verificar as configurações, use: Get-ChildItem Env: | Select-String 'MERCADOPAGO|STRIPE|BASE_URL'" -ForegroundColor Cyan