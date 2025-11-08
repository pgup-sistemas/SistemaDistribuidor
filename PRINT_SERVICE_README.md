# Print Service - Sistema Distribuidor

## Visão Geral

O Print Service é responsável por gerar recibos de venda em formato PDF para pedidos do sistema. Ele suporta múltiplas bibliotecas de geração de PDF com fallbacks robustos.

## Funcionalidades

### Geração de Recibos
- Gera recibos térmicos em formato PDF
- Layout otimizado para impressão térmica (80mm)
- Suporte a múltiplas bibliotecas (WeasyPrint e ReportLab)
- Fallback automático para HTML estilizado quando PDF falha
- HTML fallback inclui botões de impressão e aparência térmica

### Bibliotecas Suportadas

#### WeasyPrint (Primária)
- Gera PDFs de alta qualidade com CSS completo
- Suporte a layouts complexos
- **Nota**: Requer bibliotecas GTK+ no Windows (não disponível por padrão)

#### ReportLab (Fallback)
- Geração de PDF pura em Python
- Layout térmico estilo recibo
- Sempre disponível como fallback

## Estrutura do Recibo

### Layout Térmico
```
========================================
        SISTEMA DISTRIBUIDOR
      (11) 99999-9999
Rua das Distribuidoras, 123 - São Paulo/SP
========================================

           RECIBO DE VENDA
           ---------------

Informações do Pedido
Número: #102
Data/Hora: 06/11/2025 18:30
Atendente: Maria Atendente
Cliente: João Silva
Telefone: (11) 99999-9999
----------------------------------------

Itens do Pedido
----------------------------------------
Produto A
  2 x R$ 10.50 = R$ 21.00
  Desconto: -R$ 1.00
Produto B
  1 x R$ 25.00 = R$ 25.00
----------------------------------------

Totais
Subtotal: R$ 46.00
Descontos: -R$ 1.00
========================================
TOTAL: R$ 45.00
========================================

Pagamento: Dinheiro

Obs: Cliente pediu entrega rápida

========================================
Obrigado pela preferência!
Sistema de Atendimento para Distribuidoras v1.0
Emitido em 06/11/2025 às 18:30
========================================
```

## Tratamento de Erros

### Estratégia de Fallback
1. **Tentativa WeasyPrint**: Tenta gerar PDF com WeasyPrint
2. **Fallback ReportLab**: Se WeasyPrint falhar, usa ReportLab
3. **Fallback HTML Estilizado**: Se ambas falharem, retorna HTML com:
   - Aparência térmica completa (fonte monospace, layout 80mm)
   - Botões de impressão e fechar
   - Estilos otimizados para impressão
   - Auto-impressão opcional via parâmetros URL

### Logs de Debug
- `[PRINT_SERVICE]` prefixo para todos os logs
- Logs detalhados de sucesso/falha
- Identificação clara do método usado

## API

### `PrintService.generate_receipt(order)`

Gera um recibo para o pedido especificado.

**Parâmetros:**
- `order`: Objeto Order com todos os relacionamentos carregados

**Retorno:**
- Tupla `(content, content_type)`
- `content`: bytes para PDF, str para HTML
- `content_type`: 'application/pdf' ou 'text/html'

**Exemplo:**
```python
print_service = PrintService()
content, content_type = print_service.generate_receipt(order)

if content_type == 'application/pdf':
    # Salvar como PDF
    with open('recibo.pdf', 'wb') as f:
        f.write(content)
else:
    # Salvar como HTML
    with open('recibo.html', 'w') as f:
        f.write(content)
```

## Rota Web

### `/orders/<id>/print`

Endpoint para download/impressão de recibos.

**Método:** GET
**Autenticação:** Necessária
**Parâmetros:** `id` (ID do pedido)

**Resposta:**
- PDF: `application/pdf` com filename `recibo_pedido_{id}.pdf`
- HTML: `text/html` com filename `recibo_pedido_{id}.html`

### Recursos do HTML Fallback

Quando o PDF não pode ser gerado, o sistema retorna HTML estilizado com:

- **Layout Térmico Completo**: Aparência idêntica a impressoras térmicas
- **Botões de Ação**:
  - 🖨️ Imprimir Recibo: Aciona impressão do navegador
  - ✕ Fechar: Fecha a janela
- **Auto-impressão**: Suporte a parâmetros `?auto_print=true&auto_close=true`
- **Estilos Responsivos**: Otimizado para impressão em 80mm
- **Fonte Monospace**: Aparência autêntica de recibo

## Configuração

### Dependências
```txt
WeasyPrint==66.0
reportlab==4.2.5
```

### Configurações da Empresa
Usa as configurações do `Config`:
- `COMPANY_NAME`
- `COMPANY_PHONE`
- `COMPANY_ADDRESS`

## Testes

Para testar a funcionalidade:

```bash
# Testar bibliotecas disponíveis
python -c "
from services.print_service import WEASYPRINT_AVAILABLE, REPORTLAB_AVAILABLE
print(f'WeasyPrint: {WEASYPRINT_AVAILABLE}')
print(f'ReportLab: {REPORTLAB_AVAILABLE}')
"

# Testar geração com dados mock
python test_print_service.py
```

## Problemas Conhecidos

### WeasyPrint no Windows
- WeasyPrint requer GTK+ libraries
- Não funciona por padrão no Windows
- ReportLab é usado como fallback confiável

### Codificação de Caracteres
- Garante UTF-8 para textos em português
- Suporte a caracteres especiais

## Melhorias Implementadas

### v1.1 - HTML Fallback Aprimorado
- ✅ HTML fallback com aparência térmica completa
- ✅ Botões de impressão e fechar no HTML
- ✅ Estilos otimizados para impressão térmica
- ✅ Auto-impressão e fechamento automático
- ✅ Tratamento de erros aprimorado

## Melhorias Futuras

- Suporte a logotipos da empresa
- Templates personalizáveis
- Múltiplas impressoras
- Impressão direta via API
- Suporte a códigos QR
- Integração com impressoras Bluetooth