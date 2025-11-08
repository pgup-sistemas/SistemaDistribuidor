try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
    print("[PRINT_SERVICE] WeasyPrint successfully imported, PDF generation enabled")
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"[PRINT_SERVICE] WeasyPrint not available, will use ReportLab fallback. Error: {e}")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
    print("[PRINT_SERVICE] ReportLab successfully imported, PDF fallback enabled")
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    print(f"[PRINT_SERVICE] ReportLab not available. Error: {e}")

from flask import render_template
from config import Config
import io

class PrintService:
    def __init__(self):
        self.professional_css = """
        @page {
            size: A4;
            margin: 20mm;
        }

        body {
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
            background: #fff;
        }

        .receipt-container {
            max-width: 800px;
            margin: 0 auto;
            border: 3px double #333;
            border-radius: 10px;
            padding: 25px;
            background: #fff;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            position: relative;
        }

        .receipt-container::before {
            content: '';
            position: absolute;
            top: -3px;
            left: -3px;
            right: -3px;
            bottom: -3px;
            border: 1px solid #666;
            border-radius: 13px;
            pointer-events: none;
        }

        .receipt-header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 15px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
            border-radius: 8px 8px 0 0;
        }

        .company-name {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }

        .company-details {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }

        .receipt-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-top: 10px;
        }

        .order-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 8px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }

        .info-section {
            flex: 1;
        }

        .info-section h4 {
            margin: 0 0 8px 0;
            color: #007bff;
            font-size: 14px;
        }

        .info-section p {
            margin: 2px 0;
            font-size: 12px;
        }

        .items-section {
            margin-bottom: 20px;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            border: 2px solid #333;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            border-radius: 8px;
            overflow: hidden;
        }

        .items-table thead {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border-bottom: 2px solid #0056b3;
        }

        .items-table th {
            padding: 15px 12px;
            text-align: left;
            font-weight: bold;
            font-size: 13px;
            border-right: 1px solid #0056b3;
        }

        .items-table th:last-child {
            border-right: none;
        }

        .items-table td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            font-size: 12px;
            border-right: 1px solid #eee;
        }

        .items-table td:last-child {
            border-right: none;
        }

        .items-table tbody tr:last-child td {
            border-bottom: none;
        }

        .items-table tbody tr:hover {
            background: #f8f9fa;
        }

        .item-name {
            font-weight: 500;
        }

        .quantity {
            text-align: center;
        }

        .price, .total {
            text-align: right;
            font-weight: 500;
        }

        .discount-row {
            background: #fff3cd;
        }

        .discount-row td {
            color: #856404;
            font-size: 11px;
        }

        .totals-section {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 20px;
        }

        .totals-table {
            width: 350px;
            border-collapse: collapse;
            border: 3px double #333;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .totals-table td {
            padding: 12px 15px;
            font-size: 13px;
            border-bottom: 1px solid #ddd;
            border-right: 1px solid #ddd;
        }

        .totals-table td:last-child {
            border-right: none;
        }

        .totals-table tr:last-child td {
            border-bottom: none;
        }

        .totals-table .label {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-weight: bold;
            width: 50%;
            border-right: 2px solid #007bff !important;
        }

        .totals-table .amount {
            text-align: right;
            font-weight: bold;
        }

        .total-row {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border-bottom: none !important;
        }

        .total-row .label,
        .total-row .amount {
            border-right: 2px solid #0056b3 !important;
        }

        .total-row .amount {
            border-right: none !important;
        }

        .payment-info {
            margin-bottom: 20px;
            padding: 18px;
            background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%);
            border: 2px solid #007bff;
            border-left: 6px solid #007bff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,123,255,0.1);
        }

        .payment-info h4 {
            margin: 0 0 10px 0;
            color: #0056b3;
            font-size: 16px;
            font-weight: bold;
        }

        .notes-section {
            margin-bottom: 20px;
            padding: 18px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #6c757d;
            border-left: 6px solid #6c757d;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(108,117,125,0.1);
        }

        .notes-section h4 {
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 16px;
            font-weight: bold;
        }

        .receipt-footer {
            text-align: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px solid #ddd;
            color: #666;
            font-size: 11px;
        }

        .footer-text {
            margin: 5px 0;
        }

        @media print {
            .receipt-container {
                border: 1px solid #000 !important;
                box-shadow: none !important;
                margin: 0 !important;
                padding: 15px !important;
            }

            .receipt-header {
                background: white !important;
                border-bottom: 2px solid #000 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }

            .items-table {
                border: 1px solid #000 !important;
                box-shadow: none !important;
            }

            .items-table th {
                background: #000 !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                border-right: 1px solid #000 !important;
            }

            .totals-table {
                border: 2px solid #000 !important;
                box-shadow: none !important;
            }

            .total-row {
                background: #000 !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }

            .payment-info, .notes-section {
                border: 1px solid #000 !important;
                background: white !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }

            .receipt-footer {
                border-top: 1px solid #000 !important;
            }
        }
        """
    
    def generate_receipt(self, order):
        """Generate thermal receipt PDF for an order"""
        print(f"[PRINT_SERVICE] Generating receipt for order ID: {order.id}")

        try:
            receipt_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recibo - Pedido #{order.id}</title>
        </head>
        <body>
            <div class="receipt-container">
                <div class="receipt-header">
                    <div class="company-name">{Config.COMPANY_NAME}</div>
                    <div class="company-details">{Config.COMPANY_PHONE}</div>
                    <div class="company-details">{Config.COMPANY_ADDRESS}</div>
                    <div class="receipt-title">RECIBO DE VENDA</div>
                </div>

                <div class="order-info">
                    <div class="info-section">
                        <h4>Informações do Pedido</h4>
                        <p><strong>Número:</strong> #{order.id}</p>
                        <p><strong>Data/Hora:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                        <p><strong>Atendente:</strong> {order.user.name}</p>
                    </div>
                    <div class="info-section">
                        <h4>Informações do Cliente</h4>
                        <p><strong>Nome:</strong> {order.customer.name}</p>
                        {f'<p><strong>Telefone:</strong> {order.customer.phone}</p>' if order.customer.phone else ''}
                    </div>
                </div>

                <div class="items-section">
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>Produto</th>
                                <th class="quantity">Qtd</th>
                                <th class="price">Valor Unit.</th>
                                <th class="total">Total</th>
                            </tr>
                        </thead>
                        <tbody>
        """

            # Add items
            for item in order.order_items:
                item_subtotal = item.unit_price * item.quantity
                item_total = item_subtotal - item.discount
                receipt_html += f"""
                            <tr>
                                <td class="item-name">{item.product.name}</td>
                                <td class="quantity">{item.quantity}</td>
                                <td class="price">R$ {item.unit_price:.2f}</td>
                                <td class="total">R$ {item_subtotal:.2f}</td>
                            </tr>
                """

                if item.discount > 0:
                    receipt_html += f"""
                            <tr class="discount-row">
                                <td colspan="3" style="text-align: right;">Desconto:</td>
                                <td class="total">-R$ {item.discount:.2f}</td>
                            </tr>
                            <tr class="discount-row">
                                <td colspan="3" style="text-align: right; font-weight: bold;">Total do Item:</td>
                                <td class="total">R$ {item_total:.2f}</td>
                            </tr>
                """

            receipt_html += f"""
                        </tbody>
                    </table>
                </div>

                <div class="totals-section">
                    <table class="totals-table">
                        <tr>
                            <td class="label">Subtotal:</td>
                            <td class="amount">R$ {sum(item.unit_price * item.quantity for item in order.order_items):.2f}</td>
                        </tr>
                        <tr>
                            <td class="label">Descontos:</td>
                            <td class="amount">-R$ {sum(item.discount for item in order.order_items):.2f}</td>
                        </tr>
                        <tr class="total-row">
                            <td class="label">TOTAL:</td>
                            <td class="amount">R$ {order.total:.2f}</td>
                        </tr>
                    </table>
                </div>

                <div class="payment-info">
                    <h4>Forma de Pagamento</h4>
                    <p>{self._format_payment_method(order.payment_method)}</p>
                </div>
        """

            if order.notes:
                receipt_html += f"""
                <div class="notes-section">
                    <h4>Observações</h4>
                    <p>{order.notes}</p>
                </div>
        """

            receipt_html += f"""
                <div class="receipt-footer">
                    <div class="footer-text">Obrigado pela preferência!</div>
                    <div class="footer-text">Sistema de Atendimento para Distribuidoras v1.0</div>
                    <div class="footer-text">Emitido em {order.created_at.strftime('%d/%m/%Y às %H:%M')}</div>
                </div>
            </div>
        </body>
        </html>
        """

            # Try WeasyPrint first, then ReportLab fallback
            if WEASYPRINT_AVAILABLE:
                try:
                    print(f"[PRINT_SERVICE] Attempting PDF generation with WeasyPrint for order {order.id}")
                    html_doc = HTML(string=receipt_html)
                    css_doc = CSS(string=self.professional_css)

                    pdf_buffer = io.BytesIO()
                    html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc])
                    pdf_buffer.seek(0)

                    print(f"[PRINT_SERVICE] PDF generated successfully with WeasyPrint for order {order.id}")
                    return pdf_buffer.getvalue(), 'application/pdf'
                except Exception as e:
                    print(f"[PRINT_SERVICE] WeasyPrint failed for order {order.id}, trying ReportLab fallback. Error: {e}")
                    if REPORTLAB_AVAILABLE:
                        try:
                            return self.generate_pdf_with_reportlab(order), 'application/pdf'
                        except Exception as e2:
                            print(f"[PRINT_SERVICE] ReportLab also failed for order {order.id}. Error: {e2}")
                            return self._generate_styled_html_fallback(order, error=f"WeasyPrint: {e}; ReportLab: {e2}"), 'text/html'
                    else:
                        print(f"[PRINT_SERVICE] ReportLab not available for order {order.id}, returning HTML fallback")
                        return self._generate_styled_html_fallback(order, error=f"WeasyPrint: {e}"), 'text/html'
            elif REPORTLAB_AVAILABLE:
                try:
                    print(f"[PRINT_SERVICE] WeasyPrint not available, using ReportLab for order {order.id}")
                    return self.generate_pdf_with_reportlab(order), 'application/pdf'
                except Exception as e:
                    print(f"[PRINT_SERVICE] ReportLab failed for order {order.id}. Error: {e}")
                    return self._generate_styled_html_fallback(order, error=str(e)), 'text/html'
            else:
                print(f"[PRINT_SERVICE] Neither WeasyPrint nor ReportLab available for order {order.id}, returning HTML fallback")
                return self._generate_styled_html_fallback(order, error="PDF libraries not available"), 'text/html'

        except Exception as e:
            print(f"[PRINT_SERVICE] Error generating receipt for order {order.id}: {e}")
            # Return styled HTML fallback with print functionality
            error_html = self._generate_styled_html_fallback(order, error=str(e))
            return error_html, 'text/html'
    
    def _format_payment_method(self, method):
        methods = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }
        return methods.get(method, method)

    def _generate_styled_html_fallback(self, order, error=None):
        """Generate styled HTML fallback with thermal receipt appearance and print buttons"""
        print(f"[PRINT_SERVICE] Generating styled HTML fallback for order {order.id}")

        # Build items HTML
        items_html = ""
        for item in order.order_items:
            item_subtotal = item.unit_price * item.quantity
            item_total = item_subtotal - item.discount

            items_html += f"""
            <div class="item">
                <div class="item-name">{item.product.name}</div>
                <div class="item-details">
                    <div class="item-qty-price">
                        {item.quantity} x R$ {item.unit_price:.2f}
                        {"<span class='item-discount'>- R$ " + f"{item.discount:.2f}</span>" if item.discount > 0 else ""}
                    </div>
                    <div class="item-total">R$ {item_total:.2f}</div>
                </div>
            </div>
            """

        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in order.order_items)
        total_discount = sum(item.discount for item in order.order_items)

        # Build totals HTML
        totals_html = ""
        if total_discount > 0:
            totals_html += f"""
            <div class="total-line">
                <span>Subtotal:</span>
                <span>R$ {subtotal:.2f}</span>
            </div>
            <div class="total-line">
                <span>Desconto:</span>
                <span>- R$ {total_discount:.2f}</span>
            </div>
            """

        totals_html += f"""
        <div class="total-line total-final">
            <span>TOTAL:</span>
            <span>R$ {order.total:.2f}</span>
        </div>
        """

        # Error message if any
        error_html = f"<div style='color: red; text-align: center; margin: 10px 0;'><strong>Erro na geração do PDF: {error}</strong></div>" if error else ""

        # Build complete HTML with thermal styling
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recibo - Pedido #{order.id}</title>
            <style>
                @page {{
                    size: 80mm auto;
                    margin: 5mm;
                }}

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    line-height: 1.2;
                    margin: 0;
                    padding: 0;
                    color: #000;
                    background: #fff;
                }}

                .receipt-container {{
                    width: 70mm;
                    margin: 0 auto;
                    padding: 5mm;
                    background: white;
                }}

                .receipt-header {{
                    text-align: center;
                    border-bottom: 1px dashed #000;
                    padding-bottom: 8px;
                    margin-bottom: 12px;
                }}

                .company-name {{
                    font-weight: bold;
                    font-size: 14px;
                    text-transform: uppercase;
                    margin-bottom: 2px;
                }}

                .company-info {{
                    font-size: 10px;
                    line-height: 1.3;
                    margin: 2px 0;
                }}

                .order-info {{
                    margin-bottom: 12px;
                    font-size: 11px;
                }}

                .order-info strong {{
                    font-weight: bold;
                }}

                .items-section {{
                    margin-bottom: 12px;
                }}

                .items-header {{
                    font-weight: bold;
                    border-bottom: 1px solid #000;
                    padding-bottom: 2px;
                    margin-bottom: 8px;
                    font-size: 11px;
                }}

                .item {{
                    margin-bottom: 6px;
                    font-size: 11px;
                }}

                .item-name {{
                    font-weight: bold;
                    margin-bottom: 1px;
                }}

                .item-details {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 10px;
                }}

                .item-qty-price {{
                    flex: 1;
                }}

                .item-total {{
                    font-weight: bold;
                    text-align: right;
                    min-width: 20mm;
                }}

                .item-discount {{
                    color: #666;
                    font-size: 9px;
                    margin-left: 10px;
                }}

                .totals-section {{
                    border-top: 1px dashed #000;
                    padding-top: 8px;
                    margin-top: 12px;
                }}

                .total-line {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 3px;
                    font-size: 11px;
                }}

                .total-final {{
                    font-weight: bold;
                    font-size: 14px;
                    border-top: 1px solid #000;
                    border-bottom: 1px solid #000;
                    padding: 4px 0;
                    margin: 6px 0;
                }}

                .payment-info {{
                    text-align: center;
                    margin: 8px 0;
                    font-size: 11px;
                }}

                .payment-method {{
                    font-weight: bold;
                    text-transform: uppercase;
                }}

                .receipt-footer {{
                    text-align: center;
                    margin-top: 12px;
                    padding-top: 8px;
                    border-top: 1px dashed #000;
                    font-size: 10px;
                    line-height: 1.4;
                }}

                .notes-section {{
                    margin: 8px 0;
                    padding: 6px;
                    border: 1px dashed #666;
                    font-size: 10px;
                }}

                .notes-title {{
                    font-weight: bold;
                    margin-bottom: 3px;
                }}

                @media print {{
                    body {{
                        width: 80mm;
                        margin: 0;
                        padding: 0;
                    }}

                    .receipt-container {{
                        width: 100%;
                        padding: 0;
                        margin: 0;
                    }}

                    .no-print {{
                        display: none !important;
                    }}
                }}

                .print-actions {{
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 5px;
                }}

                .print-actions button {{
                    margin: 0 5px;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 14px;
                }}

                .btn-print {{
                    background: #007bff;
                    color: white;
                }}

                .btn-print:hover {{
                    background: #0056b3;
                }}

                .btn-close {{
                    background: #6c757d;
                    color: white;
                }}

                .btn-close:hover {{
                    background: #545b62;
                }}
            </style>
        </head>
        <body>
            <div class="print-actions no-print">
                <button class="btn-print" onclick="window.print()">
                    🖨️ Imprimir Recibo
                </button>
                <button class="btn-close" onclick="window.close()">
                    ✕ Fechar
                </button>
            </div>

            {error_html}

            <div class="receipt-container">
                <!-- Header -->
                <div class="receipt-header">
                    <div class="company-name">{Config.COMPANY_NAME}</div>
                    <div class="company-info">{Config.COMPANY_PHONE}</div>
                    <div class="company-info">{Config.COMPANY_ADDRESS}</div>
                </div>

                <!-- Order Information -->
                <div class="order-info">
                    <div><strong>CUPOM FISCAL</strong></div>
                    <div><strong>Pedido:</strong> #{order.id}</div>
                    <div><strong>Data:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</div>
                    <div><strong>Cliente:</strong> {order.customer.name}</div>
                    {"<div><strong>Telefone:</strong> " + order.customer.phone + "</div>" if order.customer.phone else ""}
                    <div><strong>Atendente:</strong> {order.user.name}</div>
                </div>

                <!-- Items -->
                <div class="items-section">
                    <div class="items-header">ITENS DO PEDIDO</div>
                    {items_html}
                </div>

                <!-- Totals -->
                <div class="totals-section">
                    {totals_html}
                </div>

                <!-- Payment Method -->
                <div class="payment-info">
                    <div>FORMA DE PAGAMENTO</div>
                    <div class="payment-method">{self._format_payment_method(order.payment_method)}</div>
                </div>

                <!-- Notes -->
                {"<div class='notes-section'><div class='notes-title'>OBSERVAÇÕES:</div><div>" + order.notes + "</div></div>" if order.notes else ""}

                <!-- Footer -->
                <div class="receipt-footer">
                    <div><strong>OBRIGADO PELA PREFERÊNCIA!</strong></div>
                    <div>Sistema de Atendimento para Distribuidoras v1.0</div>
                    <div style="margin-top: 6px; font-size: 8px; color: #666;">
                        Emitido em {order.created_at.strftime('%d/%m/%Y às %H:%M')}
                    </div>
                </div>
            </div>

            <script>
                // Auto-print when loaded (for thermal printers)
                window.addEventListener('load', function() {{
                    // Small delay to ensure page is fully rendered
                    setTimeout(function() {{
                        // Check if this is being opened for printing
                        const urlParams = new URLSearchParams(window.location.search);
                        if (urlParams.get('auto_print') === 'true') {{
                            window.print();
                        }}
                    }}, 500);
                }});

                // Handle print completion
                window.addEventListener('afterprint', function() {{
                    // Option to close window after printing
                    const urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.get('auto_close') === 'true') {{
                        setTimeout(function() {{
                            window.close();
                        }}, 1000);
                    }}
                }});
            </script>
        </body>
        </html>
        """

        return html

    def generate_pdf_with_reportlab(self, order):
        """Generate PDF receipt using ReportLab as fallback"""
        print(f"[PRINT_SERVICE] Generating PDF with ReportLab for order {order.id}")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=30, leftMargin=30,
                               topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()

        # Custom styles for thermal receipt look
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center
            fontName='Helvetica-Bold',
            textColor=colors.darkblue
        )

        company_style = ParagraphStyle(
            'Company',
            parent=styles['Normal'],
            fontSize=14,
            alignment=1,
            fontName='Helvetica-Bold',
            spaceAfter=15,
            textColor=colors.darkblue
        )

        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=5
        )

        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            spaceAfter=5
        )

        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            spaceAfter=3
        )

        # Build the PDF content
        story = []

        # Company header with border effect
        story.append(Paragraph("=" * 50, small_style))
        story.append(Paragraph(Config.COMPANY_NAME, company_style))
        story.append(Paragraph(Config.COMPANY_PHONE, normal_style))
        story.append(Paragraph(Config.COMPANY_ADDRESS, normal_style))
        story.append(Paragraph("=" * 50, small_style))
        story.append(Spacer(1, 15))

        # Title
        story.append(Paragraph("RECIBO DE VENDA", title_style))
        story.append(Paragraph("-" * 30, small_style))
        story.append(Spacer(1, 15))

        # Order info in a more receipt-like format
        story.append(Paragraph("<b>Informações do Pedido</b>", bold_style))
        story.append(Paragraph(f"Número: #{order.id}", normal_style))
        story.append(Paragraph(f"Data/Hora: {order.created_at.strftime('%d/%m/%Y %H:%M')}", normal_style))
        story.append(Paragraph(f"Atendente: {order.user.name}", normal_style))
        story.append(Paragraph(f"Cliente: {order.customer.name}", normal_style))
        if order.customer.phone:
            story.append(Paragraph(f"Telefone: {order.customer.phone}", normal_style))
        story.append(Paragraph("-" * 40, small_style))
        story.append(Spacer(1, 10))

        # Items section - thermal receipt style
        story.append(Paragraph("<b>Itens do Pedido</b>", bold_style))
        story.append(Paragraph("-" * 40, small_style))

        for item in order.order_items:
            item_subtotal = item.unit_price * item.quantity
            story.append(Paragraph(f"{item.product.name}", normal_style))
            story.append(Paragraph(f"  {item.quantity} x R$ {item.unit_price:.2f} = R$ {item_subtotal:.2f}", small_style))
            if item.discount > 0:
                story.append(Paragraph(f"  Desconto: -R$ {item.discount:.2f}", small_style))

        story.append(Paragraph("-" * 40, small_style))
        story.append(Spacer(1, 10))

        # Totals section - thermal receipt style
        story.append(Paragraph("<b>Totais</b>", bold_style))
        subtotal = sum(item.unit_price * item.quantity for item in order.order_items)
        discounts = sum(item.discount for item in order.order_items)

        story.append(Paragraph(f"Subtotal: R$ {subtotal:.2f}", normal_style))
        if discounts > 0:
            story.append(Paragraph(f"Descontos: -R$ {discounts:.2f}", normal_style))
        story.append(Paragraph("=" * 40, small_style))
        story.append(Paragraph(f"<b>TOTAL: R$ {order.total:.2f}</b>", bold_style))
        story.append(Paragraph("=" * 40, small_style))
        story.append(Spacer(1, 10))

        # Payment method
        story.append(Paragraph(f"Pagamento: {self._format_payment_method(order.payment_method)}", normal_style))
        story.append(Spacer(1, 5))

        # Notes
        if order.notes:
            story.append(Paragraph(f"Obs: {order.notes}", normal_style))
            story.append(Spacer(1, 5))

        # Footer
        story.append(Spacer(1, 20))
        story.append(Paragraph("=" * 50, small_style))
        story.append(Paragraph("Obrigado pela preferência!", normal_style))
        story.append(Paragraph("Sistema de Atendimento para Distribuidoras v1.0", small_style))
        story.append(Paragraph(f"Emitido em {order.created_at.strftime('%d/%m/%Y às %H:%M')}", small_style))
        story.append(Paragraph("=" * 50, small_style))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        print(f"[PRINT_SERVICE] PDF generated successfully with ReportLab for order {order.id}")
        return buffer.getvalue()
