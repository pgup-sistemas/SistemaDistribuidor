# Solução: Instalar ReportLab no Servidor

## Problema Identificado

O erro `ReportLab not available. Error: No module named 'reportlab'` indica que o ReportLab não está instalado no servidor onde você está executando o sistema.

## Solução

Execute no servidor onde o sistema está rodando:

```bash
# Navegue até a pasta do projeto
cd /caminho/para/sistema-distribuidor

# Instale as dependências
pip install -r requirements.txt

# Ou instale apenas o ReportLab
pip install reportlab==4.2.5
```

## Verificação

Após a instalação, execute o arquivo de diagnóstico:

```bash
python check_pdf_server.py
```

Deve mostrar:
```
REPORTLAB_AVAILABLE: True
✓ ReportLab OK - Versão: 4.2.5
```

## Resultado Esperado

Com o ReportLab instalado:

1. **WeasyPrint** tentará primeiro (falhará no Windows, mas é normal)
2. **ReportLab** será usado como fallback
3. **PDF térmico** será gerado automaticamente
4. **HTML fallback** só será usado se ambas as bibliotecas falharem

## Verificação no Navegador

Acesse: `http://192.168.1.94:5000/orders/102/print`

- Deve baixar um PDF automaticamente
- Não deve mostrar o HTML fallback
- O recibo terá layout térmico profissional

## Se o Problema Persistir

Se ainda não funcionar após instalar o ReportLab:

1. **Reinicie o servidor** Flask
2. **Verifique os logs** para confirmar que o ReportLab foi detectado
3. **Teste em ambiente limpo** com:
   ```bash
   pip install reportlab==4.2.5
   python -c "import reportlab; print('OK')"
   ```

## Status Atual

✅ **HTML Fallback Funcionando**: Botões de imprimir e fechar estão funcionando
✅ **Layout Térmico**: Aparência profissional do recibo
⚠️ **PDF Indisível**: ReportLab precisa ser instalado no servidor

O sistema está funcionando corretamente, apenas falta a biblioteca PDF no servidor!