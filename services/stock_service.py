from sqlalchemy.orm import Session
from models.inventory import Item, StockLot, StockQuant, Bin, Warehouse, Zone
from repositories.movement_repo import MovementRepository
from app_logging.app_logger import app_logger
from datetime import datetime
from utils.signals import signal_manager

class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.movement_repo = MovementRepository(db)

    def record_movement(self, movement_data: dict, items_list: list) -> bool:
        """
        Record movement and update quants.
        """
        from models.inventory import Movement, MovementItem
        try:
            # 1. Create the Movement Record (Persistence)
            # Ensure data mapping is correct for the model
            m_obj = Movement(
                type=movement_data['type'],
                reference_no=movement_data['reference_no'],
                date=datetime.now(),
                supplier_id=movement_data.get('supplier_id'),
                received_by=movement_data.get('received_by'),
                issuing_entity=movement_data.get('issuing_entity'),
                receiver_name=movement_data.get('receiver_name'),
                notes=movement_data.get('notes', ''),
                discount_percent=float(movement_data.get('discount_percent', 0)),
                subtotal=0.0,
                final_total=0.0
            )
            self.db.add(m_obj)
            self.db.flush()

            total_value = 0.0
            # Ensure at least one bin exists to satisfy FK constraint
            default_bin = self.db.query(Bin).first()
            if not default_bin:
                # Emergency recovery if seeding failed
                wh = Warehouse(code="DEF", name="Default")
                self.db.add(wh); self.db.flush()
                zone = Zone(warehouse_id=wh.id, code="D1", name="Default")
                self.db.add(zone); self.db.flush()
                default_bin = Bin(zone_id=zone.id, code="B1", name="Default")
                self.db.add(default_bin); self.db.flush()

            for it in items_list:
                item = self.db.query(Item).filter(Item.id == it['item_id']).first()
                if not item: continue

                qty = float(it['qty'])
                price = float(it['price'])
                line_total = qty * price
                total_value += line_total

                # Robust Bin/Lot Identification
                bin_id = it.get('bin_id')
                if not bin_id or bin_id == 0: bin_id = default_bin.id

                # Persistence: Line Items
                m_item = MovementItem(
                    movement_id=m_obj.id,
                    item_id=item.id,
                    quantity=qty,
                    price=price
                )
                self.db.add(m_item)

                if movement_data['type'] == 'IN':
                    lot_num = it.get('lot_number', 'DEFAULT')
                    if not lot_num: lot_num = 'DEFAULT'

                    # Force dates if available or required
                    p_date = it.get('production_date')
                    e_date = it.get('expiry') or it.get('expiry_date')

                    lot = self.db.query(StockLot).filter(
                        StockLot.item_id == item.id,
                        StockLot.lot_number == lot_num
                    ).first()
                    if not lot:
                        lot = StockLot(item_id=item.id, lot_number=lot_num, expiry_date=e_date)
                        self.db.add(lot)
                        self.db.flush()

                    lot.quantity += qty
                    item.current_stock += qty

                    quant = self.db.query(StockQuant).filter(
                        StockQuant.item_id == item.id, StockQuant.bin_id == bin_id, StockQuant.lot_id == lot.id
                    ).first()
                    if not quant:
                        quant = StockQuant(item_id=item.id, bin_id=bin_id, lot_id=lot.id, quantity=0)
                        self.db.add(quant)
                    quant.quantity += qty
                    m_item.batch_id = lot.id

                else: # OUT
                    item.current_stock -= qty
                    quant = self.db.query(StockQuant).filter(
                        StockQuant.item_id == item.id, StockQuant.bin_id == bin_id
                    ).first()
                    if quant:
                        quant.quantity -= qty

            # Finalize Totals
            m_obj.subtotal = total_value
            disc_amt = (total_value * m_obj.discount_percent) / 100
            m_obj.discount_amount = disc_amt
            m_obj.final_total = total_value - disc_amt

            self.db.commit()
            signal_manager.movement_added.emit()
            signal_manager.item_changed.emit()
            return True
        except Exception as e:
            self.db.rollback()
            app_logger.error(f"Movement failed: {e}")
            raise e

    def get_history(self, **kwargs):
        return self.movement_repo.get_history(**kwargs)

    def generate_invoice_pdf(self, movement_id):
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from models.inventory import Movement, MovementItem, Settings
        from utils.translation_manager import tr, tr_manager
        import os

        m = self.db.query(Movement).filter(Movement.id == movement_id).first()
        if not m: return ""

        settings = self.db.query(Settings).first() or Settings()
        filename = f"reports/invoice_{m.reference_no}.pdf"
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
            return get_display(arabic_reshaper.reshape(str(txt)))

        # Premium Header with Logo and Company Info
        logo_path = "logo/logo.png"
        header_data = []
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=150, height=75)
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
        elements.append(Paragraph(fmt(f"{tr('invoice').upper()}: {m.reference_no}"), styles['Heading2']))
        elements.append(Paragraph(fmt(f"{tr('date')}: {m.date.strftime('%Y-%m-%d %H:%M')}"), styles['Normal']))

        # Party info
        party_label = tr("supplier") if m.type == "IN" else tr("issuing_entity")
        party_name = m.supplier.name if m.type == "IN" and m.supplier else (m.issuing_entity or "N/A")
        elements.append(Paragraph(fmt(f"{party_label}: {party_name}"), styles['Normal']))

        elements.append(Spacer(1, 20))

        # Pro Max Summary Bar
        m_type_txt = tr("inbound") if m.type == 'IN' else tr("outbound")
        top_sum = [[fmt(f"{tr('type')}: {m_type_txt}"), fmt(f"{tr('receiver_name')}: {m.received_by or m.receiver_name or '-'}")]]
        if is_ar: top_sum[0].reverse()
        ts_table = Table(top_sum, colWidths=[250, 250])
        ts_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f2f3f4')), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        elements.append(ts_table)
        elements.append(Spacer(1, 15))

        # Premium Line Items Table
        m_items = self.db.query(MovementItem).filter(MovementItem.movement_id == movement_id).all()
        headers = [tr("item_code"), tr("item_name"), tr("quantity"), tr("unit_price"), tr("total")]
        if is_ar: headers.reverse()

        data = [[fmt(h) for h in headers]]
        for mi in m_items:
            line_total = mi.quantity * mi.price
            row = [mi.item.code, mi.item.name, str(mi.quantity), f"{mi.price:,.2f}", f"{line_total:,.2f}"]
            if is_ar: row.reverse()
            data.append([fmt(cell) for cell in row])

        t = Table(data, repeatRows=1, colWidths=[90, 200, 80, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f9f9f9')])
        ]))
        elements.append(t)

        # Summary Section
        elements.append(Spacer(1, 30))
        summary_data = [
            [fmt(tr("subtotal") + ":"), f"{m.subtotal:,.2f}"],
            [fmt(tr("discount_percent") + f" ({m.discount_percent}%):"), f"{m.discount_amount:,.2f}"],
            [fmt(tr("total_value").upper() + ":"), Paragraph(f"<b>{m.final_total:,.2f}</b>", styles['Heading3'])]
        ]
        if is_ar:
            for row in summary_data: row.reverse()

        sum_table = Table(summary_data, colWidths=[350, 150] if not is_ar else [150, 350])
        sum_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT' if not is_ar else 'LEFT'),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
        ]))
        elements.append(sum_table)

        doc.build(elements)
        return filename
