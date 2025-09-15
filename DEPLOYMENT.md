# 🚀 Guia de Deploy em Produção - Sistema Distribuidor

## 📋 Pré-requisitos

### 1. Servidor
- **OS:** Ubuntu 20.04+ ou CentOS 8+
- **RAM:** Mínimo 2GB (Recomendado: 4GB+)
- **CPU:** 2 cores (Recomendado: 4 cores+)
- **Disco:** 20GB+ de espaço livre

### 2. Software Necessário
- Python 3.11+
- PostgreSQL 12+
- Nginx
- Redis (opcional, para cache e rate limiting)

## 🔧 Instalação

### 1. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependências
```bash
# Python e pip
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Nginx
sudo apt install nginx -y

# Redis (opcional)
sudo apt install redis-server -y

# Outras dependências
sudo apt install build-essential libpq-dev -y
```

### 3. Configurar PostgreSQL
```bash
# Acessar PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE distributor_system;
CREATE USER distributor_user WITH PASSWORD 'sua_senha_segura';
GRANT ALL PRIVILEGES ON DATABASE distributor_system TO distributor_user;
\q
```

### 4. Configurar Usuário do Sistema
```bash
# Criar usuário para a aplicação
sudo adduser --system --group --home /opt/distributor distributor

# Dar permissões
sudo chown -R distributor:distributor /opt/distributor
```

## 📁 Deploy da Aplicação

### 1. Clonar/Transferir Código
```bash
# Como usuário distributor
sudo -u distributor -i
cd /opt/distributor

# Clonar repositório ou transferir arquivos
git clone https://github.com/seu-usuario/sistema-distribuidor.git .
# ou
# scp -r /caminho/local/* user@server:/opt/distributor/
```

### 2. Configurar Ambiente Virtual
```bash
cd /opt/distributor
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env
sudo nano /opt/distributor/.env
```

**Conteúdo do .env:**
```env
# Configurações do Sistema
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_muito_segura_aqui
DATABASE_URL=postgresql://distributor_user:sua_senha_segura@localhost:5432/distributor_system

# Configurações de Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com

# Configurações do MercadoPago
MERCADOPAGO_ACCESS_TOKEN=APP-sua_access_token_real
MERCADOPAGO_PUBLIC_KEY=APP-sua_public_key_real
MERCADOPAGO_WEBHOOK_SECRET=seu_webhook_secret
MERCADOPAGO_SANDBOX=false

# Configurações de Produção
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=sua_sentry_dsn_se_tiver
```

### 4. Executar Migrações
```bash
cd /opt/distributor
source venv/bin/activate
python migration.py
```

### 5. Configurar Gunicorn
```bash
# Criar diretório de logs
sudo mkdir -p /opt/distributor/logs
sudo chown -R distributor:distributor /opt/distributor/logs

# Testar Gunicorn
cd /opt/distributor
source venv/bin/activate
gunicorn --config gunicorn.conf.py wsgi:application
```

## 🔧 Configuração do Nginx

### 1. Criar Configuração do Site
```bash
sudo nano /etc/nginx/sites-available/distributor
```

**Conteúdo:**
```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Certificados SSL (usar Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de segurança
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logs
    access_log /var/log/nginx/distributor_access.log;
    error_log /var/log/nginx/distributor_error.log;
    
    # Configurações do proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Arquivos estáticos
    location /static {
        alias /opt/distributor/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Uploads
    location /uploads {
        alias /opt/distributor/uploads;
        expires 1d;
    }
    
    # Logs (apenas para admin)
    location /logs {
        deny all;
    }
}
```

### 2. Ativar Site
```bash
sudo ln -s /etc/nginx/sites-available/distributor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Configurar SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configurar renovação automática
sudo crontab -e
# Adicionar linha:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚀 Configurar Systemd Service

### 1. Criar Service
```bash
sudo nano /etc/systemd/system/distributor.service
```

**Conteúdo:**
```ini
[Unit]
Description=Sistema Distribuidor
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=distributor
Group=distributor
WorkingDirectory=/opt/distributor
Environment=PATH=/opt/distributor/venv/bin
ExecStart=/opt/distributor/venv/bin/gunicorn --config gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Ativar Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable distributor
sudo systemctl start distributor
sudo systemctl status distributor
```

## 📊 Monitoramento

### 1. Logs
```bash
# Logs da aplicação
sudo journalctl -u distributor -f

# Logs do Nginx
sudo tail -f /var/log/nginx/distributor_access.log
sudo tail -f /var/log/nginx/distributor_error.log

# Logs da aplicação
tail -f /opt/distributor/logs/app.log
tail -f /opt/distributor/logs/security.log
tail -f /opt/distributor/logs/payments.log
```

### 2. Backup Automático
```bash
# Criar script de backup
sudo nano /opt/distributor/backup.sh
```

**Conteúdo:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
DB_NAME="distributor_system"
DB_USER="distributor_user"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco
pg_dump -h localhost -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /opt/distributor

# Remover backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

```bash
# Tornar executável
sudo chmod +x /opt/distributor/backup.sh

# Configurar cron (executar diariamente às 2h)
sudo crontab -e
# Adicionar linha:
# 0 2 * * * /opt/distributor/backup.sh
```

## 🔧 Comandos Úteis

### Gerenciamento do Serviço
```bash
# Iniciar/Parar/Reiniciar
sudo systemctl start distributor
sudo systemctl stop distributor
sudo systemctl restart distributor

# Status
sudo systemctl status distributor

# Logs em tempo real
sudo journalctl -u distributor -f
```

### Gerenciamento do Banco
```bash
# Backup manual
pg_dump -h localhost -U distributor_user distributor_system > backup.sql

# Restaurar backup
psql -h localhost -U distributor_user distributor_system < backup.sql
```

### Atualizações
```bash
# Atualizar código
cd /opt/distributor
sudo -u distributor git pull

# Atualizar dependências
sudo -u distributor -i
cd /opt/distributor
source venv/bin/activate
pip install -r requirements.txt

# Executar migrações
python migration.py

# Reiniciar serviço
sudo systemctl restart distributor
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de permissão:**
   ```bash
   sudo chown -R distributor:distributor /opt/distributor
   ```

2. **Banco não conecta:**
   ```bash
   # Verificar se PostgreSQL está rodando
   sudo systemctl status postgresql
   
   # Verificar configuração
   sudo -u postgres psql -c "SELECT * FROM pg_user;"
   ```

3. **Nginx não carrega:**
   ```bash
   # Testar configuração
   sudo nginx -t
   
   # Verificar logs
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Aplicação não inicia:**
   ```bash
   # Verificar logs
   sudo journalctl -u distributor -n 50
   
   # Testar manualmente
   cd /opt/distributor
   source venv/bin/activate
   python wsgi.py
   ```

## 📈 Otimizações

### 1. Configurações do PostgreSQL
```bash
sudo nano /etc/postgresql/12/main/postgresql.conf
```

Adicionar/alterar:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### 2. Configurações do Nginx
```bash
sudo nano /etc/nginx/nginx.conf
```

Adicionar no bloco `http`:
```
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

## ✅ Checklist de Deploy

- [ ] Servidor configurado com todas as dependências
- [ ] PostgreSQL instalado e configurado
- [ ] Aplicação clonada e configurada
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados migrado
- [ ] Nginx configurado e funcionando
- [ ] SSL configurado
- [ ] Systemd service configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Testes de funcionamento realizados

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verificar logs da aplicação
2. Verificar logs do Nginx
3. Verificar status dos serviços
4. Consultar documentação do Flask/Gunicorn
5. Verificar configurações de firewall

---

**🎉 Parabéns! Seu Sistema Distribuidor está rodando em produção!**
