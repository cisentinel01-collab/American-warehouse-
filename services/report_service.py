from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from sqlalchemy.orm import Session
from models.inventory import Item, Settings, StockLot
from datetime import datetime, timedelta
import os

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_inventory_report(self, is_low_stock=False):
        from utils.translation_manager import tr, tr_manager
        try:
            settings = self.db.query(Settings).first() or Settings()
            filename = f"reports/inventory_{os.getpid()}.pdf"
            if not os.path.exists("reports"): os.makedirs("reports")

            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            is_ar = tr_manager.current_language == 'ar'

            def fmt(txt):
                if not txt: return ""
                if not is_ar: return str(txt)
                import arabic_reshaper
                from bidi.algorithm import get_display
                reshaped = arabic_reshaper.reshape(str(txt))
                return get_display(reshaped)

            # Modern Header Table
            logo_path = "logo/logo.png"
            header_data = []
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=120, height=60)
                company_info = [
                    [Paragraph(f"<b>{fmt(settings.company_name)}</b>", styles['Title'])],
                    [Paragraph(fmt(settings.address or ""), styles['Normal'])],
                    [Paragraph(fmt(f"{tr('phone')}: {settings.phone or ''}"), styles['Normal'])]
                ]
                comp_table = Table(company_info)
                if is_ar:
                    header_data = [[comp_table, logo]]
                else:
                    header_data = [[logo, comp_table]]

            if header_data:
                h_table = Table(header_data, colWidths=[350, 150] if not is_ar else [150, 350])
                h_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LINEBELOW', (0,0), (-1,-1), 3, colors.HexColor('#d4af37'))
                ]))
                elements.append(h_table)

            elements.append(Spacer(1, 25))
            elements.append(Paragraph(fmt(tr("inventory_report").upper()), styles['Heading2']))
            elements.append(Paragraph(fmt(f"{tr('date')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), styles['Normal']))
            elements.append(Spacer(1, 20))

            # Pro-Level Data Fetching (Move up for Summary calculation)
            items = self.db.query(Item).filter(Item.active == True).all()

            # Summary Analytics Top Bar (Pro Max)
            total_items = len(items)
            total_qty = sum(i.current_stock for i in items)
            summary_top = [[fmt(f"{tr('total_items')}: {total_items}"), fmt(f"Total On-Hand: {total_qty}")]]
            if is_ar: summary_top[0].reverse()
            st_table = Table(summary_top, colWidths=[250, 250])
            st_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ecf0f1')),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,0), (-1,-1), 10)
            ]))
            elements.append(st_table)
            elements.append(Spacer(1, 15))

            # Pro-Level Data Table
            query = self.db.query(Item).filter(Item.active == True)
            if is_low_stock:
                query = query.filter(Item.current_stock <= Item.min_stock)
            items = query.all()

            headers = [tr("item_code"), tr("item_name"), tr("category"), tr("current_stock"), tr("unit")]
            if is_ar: headers.reverse()

            data = [[fmt(h) for h in headers]]
            for i in items:
                row = [i.code, i.name, i.category or "-", str(i.current_stock), i.unit or "-"]
                if is_ar: row.reverse()
                data.append([fmt(cell) for cell in row])

            if len(data) > 1:
                t = Table(data, repeatRows=1, colWidths=[100, 180, 100, 80, 70])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f2f3f4')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#ecf0f1')])
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph(fmt("No items found."), styles['Normal']))

            doc.build(elements)
            return filename
        except Exception as e:
            from app_logging.app_logger import app_logger
            app_logger.error(f"Report generation error: {e}")
            raise

    def generate_inventory_excel(self, is_low_stock=False):
        import pandas as pd
        from utils.translation_manager import tr
        query = self.db.query(Item).filter(Item.active == True)
        if is_low_stock:
            query = query.filter(Item.current_stock <= Item.min_stock)
        items = query.all()
        filename = f"reports/inventory_{os.getpid()}.xlsx"

        data = [{
            tr('item_code'): i.code,
            tr('item_name'): i.name,
            tr('category'): i.category,
            tr('unit'): i.unit,
            tr('current_stock'): i.current_stock,
            tr('min_stock'): i.min_stock
        } for i in items]

        df = pd.DataFrame(data)

        # Professional Excel Design with XlsxWriter
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Inventory')

        workbook  = writer.book
        worksheet = writer.sheets['Inventory']

        # Corporate Formatting (Pro Max)
        header_fmt = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'middle', 'align': 'center',
            'fg_color': '#2c3e50', 'font_color': 'white', 'border': 1
        })

        cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'middle'})
        alt_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'middle', 'fg_color': '#f2f3f4'})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 22)

        for row in range(1, len(df) + 1):
            worksheet.set_row(row, 22)
            fmt = alt_fmt if row % 2 == 0 else cell_fmt
            for col in range(len(df.columns)):
                worksheet.write(row, col, df.iloc[row-1, col], fmt)

        writer.close()
        return filename

    def generate_audit_report(self):
        from models.audit import AuditLog
        from utils.translation_manager import tr
        logs = self.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500).all()
        filename = f"reports/audit_{os.getpid()}.xlsx"

        data = [{
            tr('date'): l.timestamp.strftime("%Y-%m-%d %H:%M"),
            tr('username'): l.username,
            tr('action'): l.action,
            tr('details'): l.details
        } for l in logs]

        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        return filename

    def generate_expiry_report(self):
        from models.inventory import StockLot
        from utils.translation_manager import tr
        lots = self.db.query(StockLot).filter(StockLot.quantity > 0).order_by(StockLot.expiry_date).all()
        filename = f"reports/expiry_{os.getpid()}.xlsx"

        data = [{
            tr('item_name'): l.item.name,
            tr('batch_no'): l.lot_number,
            tr('expiry_date'): l.expiry_date.strftime("%Y-%m-%d"),
            tr('quantity'): l.quantity
        } for l in lots]

        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        return filename

    def generate_movements_report(self, m_type, format="pdf"):
        from models.inventory import Movement, MovementItem, Settings
        from utils.translation_manager import tr, tr_manager
        from sqlalchemy import func

        movements = self.db.query(Movement).filter(Movement.type == m_type).all()
        total_val = self.db.query(func.sum(Movement.final_total)).filter(Movement.type == m_type).scalar() or 0

        if format == "excel":
            return self._gen_movements_excel(movements, m_type)

        # PDF Generation
        try:
            settings = self.db.query(Settings).first() or Settings()
            filename = f"reports/movements_{m_type}_{os.getpid()}.pdf"

            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            is_ar = tr_manager.current_language == 'ar'

            def fmt(txt):
                if not txt: return ""
                if not is_ar: return str(txt)
                import arabic_reshaper
                from bidi.algorithm import get_display
                return get_display(arabic_reshaper.reshape(str(txt)))

            title = tr("stock_in") if m_type == "IN" else tr("stock_out")
            elements.append(Paragraph(f"<b>{fmt(settings.company_name)}</b>", styles['Title']))
            elements.append(Paragraph(fmt(title), styles['Heading2']))

            # Profit Analytics in Reports (Pro Max)
            total_in = self.db.query(func.sum(Movement.final_total)).filter(Movement.type == 'IN').scalar() or 0
            total_out = self.db.query(func.sum(Movement.final_total)).filter(Movement.type == 'OUT').scalar() or 0
            profit = total_out - total_in
            margin = (profit / total_out * 100) if total_out > 0 else 0

            summary_txt = f"{tr('total_value')}: {total_val:,.2f}"
            if m_type == "OUT":
                summary_txt += f" | Est. Profit: {profit:,.2f} ({margin:.1f}%)"

            elements.append(Paragraph(fmt(summary_txt), styles['Heading3']))
            elements.append(Spacer(1, 20))

            headers = [tr("date"), tr("invoice_no"), tr("supplier" if m_type=="IN" else "issuing_entity"), tr("total")]
            if is_ar: headers.reverse()
            data = [[fmt(h) for h in headers]]

            for m in movements:
                party = m.supplier.name if m.type=="IN" and m.supplier else (m.issuing_entity or "-")
                row = [m.date.strftime("%Y-%m-%d"), m.reference_no, party, f"{m.final_total:,.2f}"]
                if is_ar: row.reverse()
                data.append([fmt(cell) for cell in row])

            if len(data) > 1:
                t = Table(data, repeatRows=1, colWidths=[100, 120, 180, 100])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f2f3f4')])
                ]))
                elements.append(t)

            doc.build(elements)
            return filename
        except Exception as e:
            from app_logging.app_logger import app_logger
            app_logger.error(f"Movements report error: {e}")
            return ""

    def _gen_movements_excel(self, movements, m_type):
        import pandas as pd
        from utils.translation_manager import tr
        filename = f"reports/movements_{m_type}_{os.getpid()}.xlsx"

        data = []
        for m in movements:
            party = m.supplier.name if m.type=="IN" and m.supplier else (m.issuing_entity or "-")
            data.append({
                tr('date'): m.date.strftime("%Y-%m-%d"),
                tr('invoice_no'): m.reference_no,
                tr('party'): party,
                tr('subtotal'): m.subtotal,
                tr('total'): m.final_total
            })

        df = pd.DataFrame(data)
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Movements')

        workbook  = writer.book
        worksheet = writer.sheets['Movements']

        # Pro Design Excel
        header_fmt = workbook.add_format({'bold': True, 'fg_color': '#2c3e50', 'font_color': 'white', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        money_fmt = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'align': 'center'})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 20)

        for row_num in range(1, len(df) + 1):
            worksheet.set_row(row_num, 20)
            for col_num in range(len(df.columns)):
                val = df.iloc[row_num-1, col_num]
                fmt = money_fmt if isinstance(val, (int, float)) else cell_fmt
                worksheet.write(row_num, col_num, val, fmt)

        writer.close()
        return filename

    def get_movements(self, start_date, end_date):
        from models.inventory import Movement
        query = self.db.query(Movement)
        if start_date: query = query.filter(Movement.date >= start_date)
        if end_date: query = query.filter(Movement.date <= end_date)
        return query.all()
