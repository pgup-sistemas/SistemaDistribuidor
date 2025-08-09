from weasyprint import HTML, CSS
from flask import render_template
from config import Config
import io

class PrintService:
    def __init__(self):
        self.thermal_css = """
        @page {
            size: 80mm auto;
            margin: 5mm;
        }
        
        body {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.2;
            margin: 0;
            padding: 0;
        }
        
        .receipt-header {
            text-align: center;
            border-bottom: 1px dashed #000;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }
        
        .company-name {
            font-weight: bold;
            font-size: 14px;
        }
        
        .order-info {
            margin-bottom: 10px;
        }
        
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }
        
        .items-table td {
            padding: 2px 0;
            font-size: 11px;
        }
        
        .item-name {
            font-weight: bold;
        }
        
        .item-details {
            text-align: right;
        }
        
        .total-section {
            border-top: 1px dashed #000;
            padding-top: 5px;
            text-align: right;
            font-weight: bold;
            font-size: 14px;
        }
        
        .receipt-footer {
            text-align: center;
            margin-top: 10px;
            font-size: 10px;
            border-top: 1px dashed #000;
            padding-top: 5px;
        }
        """
    
    def generate_receipt(self, order):
        """Generate thermal receipt PDF for an order"""
        
        receipt_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Pedido #{order.id}</title>
        </head>
        <body>
            <div class="receipt-header">
                <div class="company-name">{Config.COMPANY_NAME}</div>
                <div>{Config.COMPANY_PHONE}</div>
                <div style="font-size: 10px;">{Config.COMPANY_ADDRESS}</div>
            </div>
            
            <div class="order-info">
                <strong>Pedido #{order.id}</strong><br>
                Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}<br>
                Cliente: {order.customer.name}<br>
                {f'Telefone: {order.customer.phone}<br>' if order.customer.phone else ''}
                Atendente: {order.user.name}
            </div>
            
            <table class="items-table">
        """
        
        # Add items
        for item in order.order_items:
            item_total = (item.unit_price * item.quantity) - item.discount
            receipt_html += f"""
                <tr>
                    <td class="item-name" colspan="2">{item.product.name}</td>
                </tr>
                <tr>
                    <td>{item.quantity} x R$ {item.unit_price:.2f}</td>
                    <td class="item-details">R$ {item_total:.2f}</td>
                </tr>
            """
            
            if item.discount > 0:
                receipt_html += f"""
                <tr>
                    <td style="font-size: 10px;">Desconto:</td>
                    <td class="item-details" style="font-size: 10px;">-R$ {item.discount:.2f}</td>
                </tr>
                """
        
        receipt_html += f"""
            </table>
            
            <div class="total-section">
                <div>TOTAL: R$ {order.total:.2f}</div>
                <div style="font-size: 12px; font-weight: normal;">
                    Pagamento: {self._format_payment_method(order.payment_method)}
                </div>
            </div>
        """
        
        if order.notes:
            receipt_html += f"""
            <div style="margin-top: 10px; font-size: 10px;">
                <strong>Observações:</strong><br>
                {order.notes}
            </div>
            """
        
        receipt_html += f"""
            <div class="receipt-footer">
                Obrigado pela preferência!<br>
                Sistema de Atendimento v1.0
            </div>
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = HTML(string=receipt_html)
        css_doc = CSS(string=self.thermal_css)
        
        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc])
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    
    def _format_payment_method(self, method):
        methods = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }
        return methods.get(method, method)
