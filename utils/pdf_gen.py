import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFGenerator:
    def __init__(self):
        self.font_path = "assets/fonts/Cairo-Regular.ttf"
        self.bold_font_path = "assets/fonts/Cairo-Bold.ttf"
        self.font_name = 'Cairo'

        try:
            if os.path.exists(self.font_path):
                pdfmetrics.registerFont(TTFont('Cairo', self.font_path))
                pdfmetrics.registerFont(TTFont('Cairo-Bold', self.bold_font_path))
                pdfmetrics.registerFontFamily('Cairo', normal='Cairo', bold='Cairo-Bold')
            else:
                self.font_name = 'Helvetica'
        except Exception as e:
            print(f"Font registration error: {e}")
            self.font_name = 'Helvetica'

        # Initialize reshaper once
        try:
            from arabic_reshaper import ArabicReshaper
            self.reshaper = ArabicReshaper(
                configuration={
                    'delete_harakat': False,
                    'support_zwj': True,
                    'unreshape_quotes': True,
                    'use_expanded_forms': True,
                    'reshape_digits': True,
                    'use_unshaped_instead_of_isolated': True
                }
            )
        except ImportError:
            self.reshaper = None

    def _prepare_arabic(self, text, is_english=False):
        if text is None: return ""
        text = str(text)
        if not text.strip(): return ""

        if is_english or self.reshaper is None:
            return text

        try:
            from bidi.algorithm import get_display
            # First reshape the text to handle character joining (ligatures)
            reshaped_text = self.reshaper.reshape(text)
            # Then apply bidi for RTL layout reordering
            return get_display(reshaped_text)
        except Exception as e:
            print(f"Arabic preparing error: {e}")
            return text

    def generate_invoice(self, filename, data, items, company_info):
        from reportlab.lib.units import inch
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        styles = getSampleStyleSheet()
        # Custom Styles
        style_title = ParagraphStyle(
            'TitleStyle', parent=styles['Normal'], fontName='Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold',
            fontSize=22, alignment=1, textColor=colors.HexColor("#1a2a6c"), spaceAfter=10
        )
        style_company = ParagraphStyle(
            'CompanyStyle', parent=styles['Normal'], fontName='Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold',
            fontSize=16, alignment=1, textColor=colors.HexColor("#d4af37")
        )
        style_contact = ParagraphStyle(
            'ContactStyle', parent=styles['Normal'], fontName=self.font_name,
            fontSize=10, alignment=1, textColor=colors.grey
        )
        style_arabic_right = ParagraphStyle(
            'ArabicRight', parent=styles['Normal'], fontName=self.font_name,
            fontSize=12, alignment=2, leading=15
        )
        style_label = ParagraphStyle(
            'LabelStyle', parent=styles['Normal'], fontName='Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold',
            fontSize=12, alignment=2, textColor=colors.HexColor("#1a2a6c")
        )

        # 1. Header
        logo_path = "logo/logo.png"
        if not os.path.exists(logo_path) and company_info and company_info.get('logo_path'):
            logo_path = company_info['logo_path']

        logo_img = ""
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=1.2*inch, height=1.2*inch)
            except: pass

        company_name = company_info.get('company_name', 'American Marine Services Free-Zone')
        company_addr = company_info.get('address', '')
        phone = company_info.get('phone', '')
        email = company_info.get('email', '')
        company_contact = f"هاتف: {phone} | بريد: {email}" if phone or email else ""

        header_content = [
            [logo_img],
            [Paragraph(self._prepare_arabic(company_name, is_english=True), style_company)],
            [Paragraph(self._prepare_arabic(company_addr), style_contact)],
            [Paragraph(self._prepare_arabic(company_contact), style_contact)],
        ]

        header_table = Table(header_content, colWidths=[doc.width])
        header_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))

        elements.append(Table([[""]], colWidths=[doc.width], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#1a2a6c"))]))
        elements.append(Spacer(1, 0.2*inch))

        # 2. Title
        title_text = data.get('report_title')
        if not title_text:
            title_text = "فاتورة توريد مخزني" if data['type'] == 'IN' else "سند صرف مخزني"
        elements.append(Paragraph(self._prepare_arabic(title_text), style_title))
        elements.append(Spacer(1, 0.2*inch))

        # 3. Details
        party_label = "المورد:" if data['type'] == 'IN' else "المستلم:"
        party_name = data.get('supplier_name') if data['type'] == 'IN' else data.get('receiver_name', '')

        details_data = [
            [self._prepare_arabic(data['reference_no']), Paragraph(self._prepare_arabic("رقم العملية:"), style_label),
             self._prepare_arabic(data['date']), Paragraph(self._prepare_arabic("التاريخ:"), style_label)],
            ["", "", self._prepare_arabic(party_name), Paragraph(self._prepare_arabic(party_label), style_label)]
        ]

        details_table = Table(details_data, colWidths=[1.5*inch, 1.2*inch, 2.5*inch, 1.2*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), self.font_name),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 0.3*inch))

        # 4. Table
        table_headers = [
            self._prepare_arabic("الإجمالي"),
            self._prepare_arabic("السعر"),
            self._prepare_arabic("الكمية"),
            self._prepare_arabic("الوحدة"),
            self._prepare_arabic("كود الصنف"),
            self._prepare_arabic("اسم الصنف")
        ]

        table_rows = [table_headers]
        for item in items:
            price = item.get('price', 0)
            qty = item.get('quantity', 0)
            total = price * qty
            table_rows.append([
                f"{total:,.2f}",
                f"{price:,.2f}",
                str(qty),
                self._prepare_arabic(item.get('unit', '')),
                self._prepare_arabic(item.get('item_code', '')),
                self._prepare_arabic(item.get('item_name', ''))
            ])

        col_widths = [1.0*inch, 1.0*inch, 0.8*inch, 0.8*inch, 1.2*inch, 2.5*inch]
        items_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a6c")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTNAME', (0, 0), (-1, 0), 'Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))

        # 5. Summary
        if 'subtotal' in data:
            summary_data = [
                [f"{data['subtotal']:,.2f}", Paragraph(self._prepare_arabic("المجموع الفرعي:"), style_arabic_right)],
                [f"{data['discount_amount']:,.2f} ({data['discount_percent']}%)", Paragraph(self._prepare_arabic("إجمالي الخصم:"), style_arabic_right)],
                [f"{data['final_total']:,.2f}", Paragraph(self._prepare_arabic("الإجمالي النهائي:"), style_label)],
            ]
            summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('LINEABOVE', (0, 2), (0, 2), 1, colors.HexColor("#1a2a6c")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))

            outer_summary = Table([[summary_table]], colWidths=[doc.width])
            outer_summary.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
            elements.append(outer_summary)

        # 6. Notes
        if data.get('notes'):
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(self._prepare_arabic("ملاحظات:"), style_label))
            elements.append(Paragraph(self._prepare_arabic(data['notes']), style_arabic_right))

        # 7. Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_data = [
            [self._prepare_arabic("توقيع المستلم"), "", self._prepare_arabic("توقيع أمين المخزن"), "", self._prepare_arabic("ختم الشركة")],
            ["\n\n....................", "", "\n\n....................", "", ""]
        ]
        footer_table = Table(footer_data, colWidths=[1.5*inch, 0.5*inch, 1.5*inch, 0.5*inch, 2.0*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('BOX', (4, 0), (4, 1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ]))
        elements.append(footer_table)

        doc.build(elements)

    def generate_report(self, filename, title, headers, data, company_info):
        from reportlab.lib.units import inch
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            'TitleStyle', parent=styles['Normal'], fontName='Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold',
            fontSize=20, alignment=1, textColor=colors.HexColor("#1a2a6c"), spaceAfter=15
        )
        style_company = ParagraphStyle(
            'CompanyStyle', parent=styles['Normal'], fontName='Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold',
            fontSize=14, alignment=1, textColor=colors.HexColor("#d4af37")
        )
        style_contact = ParagraphStyle(
            'ContactStyle', parent=styles['Normal'], fontName=self.font_name,
            fontSize=9, alignment=1, textColor=colors.grey
        )

        # 1. Header (Consistent with Invoice)
        logo_path = "logo/logo.png"
        if not os.path.exists(logo_path) and company_info and company_info.get('logo_path'):
            logo_path = company_info['logo_path']

        logo_img = ""
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=0.8*inch, height=0.8*inch)
            except: pass

        company_name = company_info.get('company_name', 'American Marine Services Free-Zone')
        company_addr = company_info.get('address', '')
        phone = company_info.get('phone', '')
        email = company_info.get('email', '')
        company_contact = f"هاتف: {phone} | بريد: {email}" if phone or email else ""

        header_content = [
            [logo_img],
            [Paragraph(self._prepare_arabic(company_name, is_english=True), style_company)],
            [Paragraph(self._prepare_arabic(company_addr), style_contact)],
            [Paragraph(self._prepare_arabic(company_contact), style_contact)],
        ]

        header_table = Table(header_content, colWidths=[doc.width])
        header_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Table([[""]], colWidths=[doc.width], style=[('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#1a2a6c"))]))
        elements.append(Spacer(1, 0.2*inch))

        # 2. Title
        elements.append(Paragraph(self._prepare_arabic(title), style_title))
        elements.append(Spacer(1, 0.2*inch))

        # 3. Table
        table_data = []
        # Prepare headers with Arabic reshaping
        header_row = [self._prepare_arabic(h) for h in headers]
        header_row.reverse() # RTL handling for table columns
        table_data.append(header_row)

        for row in data:
            data_row = [self._prepare_arabic(str(item)) for item in row]
            data_row.reverse()
            table_data.append(data_row)

        # Calculate column widths
        num_cols = len(headers)
        avail_width = doc.width
        col_width = avail_width / num_cols

        table = Table(table_data, colWidths=[col_width] * num_cols, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a6c")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTNAME', (0, 0), (-1, 0), 'Cairo-Bold' if self.font_name == 'Cairo' else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(table)

        # 4. Footer
        elements.append(Spacer(1, 0.4*inch))
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        footer_text = f"تم استخراج التقرير في: {ts}"
        elements.append(Paragraph(self._prepare_arabic(footer_text), style_contact))

        doc.build(elements)
