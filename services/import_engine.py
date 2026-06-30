import re
import pandas as pd
import pdfplumber
import os
from typing import List, Dict, Any, Optional
from thefuzz import fuzz, process

class ImportEngine:
    """Industrial Grade Deterministic Invoice Parser."""

    def __init__(self):
        self.target_fields = {
            'code': ['ERP Item Code', 'Supplier Item Code', 'Part No', 'SKU', 'Item Code', 'Ref', 'Code'],
            'name': ['Product Name', 'Description', 'Item Name', 'Nomenclature', 'Article'],
            'brand': ['Brand', 'Make', 'Manufacturer'],
            'origin': ['Country of Origin', 'Origin', 'COO'],
            'packing': ['Packing Description', 'Packaging', 'Pack'],
            'hscode': ['HS Code', 'H.S. Code', 'Tariff Code'],
            'net_weight': ['Net Weight', 'N.W.', 'NW'],
            'gross_weight': ['Gross Weight', 'G.W.', 'GW'],
            'colli': ['Colli', 'Cartons', 'CTNS', 'Pallets'],
            'quantity': ['Quantity', 'Qty', 'Amount', 'Volume', 'QNT'],
            'uom': ['UOM', 'Unit', 'Measure'],
            'price': ['Unit Price', 'Price', 'Rate', 'Value'],
            'total': ['Total Price', 'Total', 'Subtotal', 'Extension'],
            'tax': ['Tax Code', 'VAT', 'Tax'],
            'ref_code': ['Reference Code', 'Lot', 'Batch']
        }

        self.header_fields = {
            'supplier': ['Supplier Name', 'Vendor', 'From'],
            'address': ['Supplier Address', 'Address'],
            'country': ['Supplier Country', 'Country'],
            'invoice_no': ['Invoice Number', 'Invoice #', 'Inv No'],
            'invoice_date': ['Invoice Date', 'Bill Date', 'Date'],
            'customer': ['Customer Name', 'Ship To', 'Bill To'],
            'shipment_no': ['Shipment Number', 'Shipment #'],
            'container_no': ['Container Number', 'Container #'],
            'seal_no': ['Seal Number', 'Seal #'],
            'currency': ['Currency', 'CCY'],
            'incoterms': ['Incoterms', 'Delivery Terms'],
            'payment_terms': ['Payment Terms'],
            'port': ['Port', 'Port of Loading', 'POL'],
            'destination': ['Destination', 'Port of Discharge', 'POD'],
            'vat': ['VAT Number', 'VAT #', 'Tax ID'],
            'reg_no': ['Company Registration', 'Reg #'],
            'iban': ['IBAN'],
            'bic': ['BIC', 'SWIFT']
        }

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return self.parse_pdf(file_path)
        elif ext in ['.xlsx', '.xls', '.csv']:
            return self.parse_tabular(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff']:
            return self.parse_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def parse_tabular(self, file_path: str) -> Dict[str, Any]:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Header Detection
        header_data = self._extract_headers_from_df(df)

        # Table Detection
        rows = self._extract_rows_from_df(df)

        return {
            'headers': header_data,
            'items': rows
        }

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        all_rows = []
        headers = {}

        with pdfplumber.open(file_path) as pdf:
            # 1. Extract Headers from first page
            first_page_text = pdf.pages[0].extract_text()
            headers = self._extract_headers_from_text(first_page_text)

            # 2. Extract Tables across all pages
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Clean and Merge Rows
                    cleaned_table = self._clean_table(table)
                    all_rows.extend(cleaned_table)

        # 3. Process Multi-line Descriptions and Merge
        merged_items = self._merge_multiline_rows(all_rows)

        # 4. Map Columns
        final_items = self._map_columns(merged_items)

        # 5. Validate
        validated_items = self._validate_data(final_items)

        return {
            'headers': headers,
            'items': validated_items
        }

    def parse_image(self, file_path: str) -> Dict[str, Any]:
        # Use Tesseract for OCR
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(file_path))
        headers = self._extract_headers_from_text(text)

        # For images, we rely more on OCR + Layout Analysis
        # This is a simplified version for now
        return {
            'headers': headers,
            'items': self._extract_via_heuristics(text)
        }

    def _extract_headers_from_df(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Look at first few rows for header info
        header_data = {}
        top_rows = df.head(10).astype(str)
        text_blob = " ".join(top_rows.values.flatten())
        return self._extract_headers_from_text(text_blob)

    def _extract_headers_from_text(self, text: str) -> Dict[str, Any]:
        header_results = {}
        for field, patterns in self.header_fields.items():
            for p in patterns:
                # Look for Pattern: [Value]
                match = re.search(fr'{re.escape(p)}[:\s]+([^\n\r,]+)', text, re.IGNORECASE)
                if match:
                    header_results[field] = match.group(1).strip()
                    break
        return header_results

    def _clean_table(self, table: List[List[str]]) -> List[List[str]]:
        cleaned = []
        for row in table:
            if not row or all(not cell for cell in row): continue
            # Remove repeated headers
            if any('Item' in str(cell) for cell in row) and any('Qty' in str(cell) for cell in row):
                continue
            cleaned.append([str(cell).strip() if cell else "" for cell in row])
        return cleaned

    def _merge_multiline_rows(self, rows: List[List[str]]) -> List[List[str]]:
        if not rows: return []
        merged = []
        current_row = None

        for row in rows:
            # Check if this row is a continuation (most cells empty, one long string)
            is_continuation = sum(1 for c in row if c) <= 2 and len(" ".join(row)) > 10

            if current_row and is_continuation:
                # Merge into the most likely description column (usually the widest)
                # For now, append to the longest cell in current_row
                desc_idx = max(range(len(current_row)), key=lambda i: len(current_row[i]))
                row_desc = " ".join(c for c in row if c)
                current_row[desc_idx] += " " + row_desc
            else:
                if current_row: merged.append(current_row)
                current_row = row

        if current_row: merged.append(current_row)
        return merged

    def _map_columns(self, rows: List[List[str]]) -> List[Dict[str, Any]]:
        if not rows: return []

        # Try to find header row to build map
        col_map = {}
        header_row = rows[0]

        for field, choices in self.target_fields.items():
            match, score = process.extractOne(field, header_row, scorer=fuzz.token_set_ratio)
            if score > 60:
                col_map[field] = header_row.index(match)

        # If no clear header row, use heuristics (simplified)
        if not col_map:
            col_map = {'name': 1, 'quantity': 2, 'price': 3} # Default fallback

        data = []
        for row in rows[1:]:
            item = {}
            for field, idx in col_map.items():
                if idx < len(row):
                    item[field] = row[idx]
            data.append(item)
        return data

    def _validate_data(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for it in items:
            try:
                qty = self._parse_num(it.get('quantity'))
                price = self._parse_num(it.get('price'))
                total = self._parse_num(it.get('total'))

                it['quantity'] = qty
                it['price'] = price
                it['total'] = total

                if abs((qty * price) - total) > 0.1:
                    it['warning'] = "Price Mismatch"
            except:
                pass
        return items

    def _parse_num(self, val: Any) -> float:
        if not val: return 0.0
        s = re.sub(r'[^\d.]', '', str(val))
        try: return float(s) if s else 0.0
        except: return 0.0

    def _extract_via_heuristics(self, text: str) -> List[Dict[str, Any]]:
        # Fallback for poorly structured text
        results = []
        lines = text.split('\n')
        for line in lines:
            parts = re.findall(r'(\d+)\s+([\w\s\.-]{10,})\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)', line)
            for p in parts:
                results.append({
                    'code': p[0],
                    'name': p[1].strip(),
                    'quantity': float(p[2]),
                    'price': float(p[3]),
                    'total': float(p[2]) * float(p[3])
                })
        return results
