import pandas as pd
import pdfplumber
import re
import os
from typing import List, Dict, Callable, Optional
from thefuzz import fuzz, process

class ImportService:
    def __init__(self):
        pass

    def extract_from_excel(self, file_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> List[Dict]:
        """Enterprise Excel/CSV Extraction with structural intelligence and header discovery."""
        try:
            if progress_callback: progress_callback(10)
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            if progress_callback: progress_callback(20)

            # Strategy 1: Data Cleaning (Drop empty perimeter)
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)

            # 1. Beast Structural Analysis: Discover main table body
            # We look for the row with the most contentful cells
            max_cols = 0
            header_row_idx = 0
            for i in range(min(20, len(df))):
                non_empty = df.iloc[i].count()
                if non_empty > max_cols:
                    max_cols = non_empty
                    header_row_idx = i

            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx+1:]
            df = df.dropna(how='all', axis=0)

            # 2. Hyper-Fuzzy Header Detection (50+ variants)
            target_fields = {
                'name': ['اسم الصنف', 'Item Name', 'Description', 'Details', 'الصنف', 'البيان', 'Product', 'Model', 'النوع', 'اسم المنتج', 'اسم المادة', 'Nomenclature', 'Service', 'Task', 'Subject', 'Article', 'Items'],
                'quantity': ['الكمية', 'Quantity', 'Qty', 'Amount', 'العدد', 'الوحدات', 'Vol', 'Stock', 'Count', 'عدد الوحدات', 'QNT', 'Weight', 'Size', 'UOM', 'Units'],
                'price': ['السعر', 'Unit Price', 'Price', 'Rate', 'سعر الوحدة', 'القيمة', 'Cost', 'Unit Cost', 'المبلغ', 'سعر المفرد', 'Price Each', 'Total Price', 'Net Price', 'Total Amt', 'Value'],
                'code': ['الكود', 'Item Code', 'Part No', 'SKU', 'رقم الصنف', 'الباركود', 'Barcode', 'Ref', 'Reference', 'Serial', 'رقم المادة', 'ID', 'Part #', 'Index', 'Code', 'No.'],
                'production_date': ['تاريخ الانتاج', 'Production Date', 'MFG Date', 'MFG'],
                'expiry_date': ['تاريخ الانتهاء', 'Expiry Date', 'Exp', 'Valid Until'],
                'supplier': ['المورد', 'Supplier', 'Vendor', 'Seller', 'From'],
                'invoice_no': ['رقم الفاتورة', 'Invoice No', 'Invoice #', 'Inv No', 'Bill No'],
                'invoice_date': ['تاريخ الفاتورة', 'Invoice Date', 'Bill Date', 'Date'],
                'total': ['الإجمالي', 'Total', 'Grand Total', 'Amount Due'],
                'taxes': ['الضريبة', 'Tax', 'VAT', 'GST'],
                'notes': ['ملاحظات', 'Notes', 'Remarks', 'Comments']
            }

            col_map = {}
            total_fields = len(target_fields)
            for idx, (field, choices) in enumerate(target_fields.items()):
                if progress_callback: progress_callback(30 + int((idx / total_fields) * 20))
                best_match = None
                highest_score = 0
                for col in df.columns:
                    col_str = str(col).strip()
                    if not col_str or col_str.lower() == 'nan': continue
                    match, score = process.extractOne(col_str, choices, scorer=fuzz.token_set_ratio)
                    if score > 70 and score > highest_score:
                        highest_score = score
                        best_match = col
                if best_match:
                    col_map[field] = best_match

            # 3. Beast Pattern Fallback: If col_map is missing fields, scan row-by-row
            results = []
            total_rows = len(df)
            for idx, (row_idx, row) in enumerate(df.iterrows()):
                if progress_callback and idx % 10 == 0:
                    progress_callback(50 + int((idx / total_rows) * 45))
                name_val = row.get(col_map.get('name')) if col_map.get('name') is not None else None

                # If fuzzy matching failed, try brute force pattern matching on the row
                if name_val is None or pd.isna(name_val):
                    # Look for first string that looks like a name and adjacent numbers
                    candidates = [x for x in row.values if not pd.isna(x)]
                    if len(candidates) >= 2:
                        # Simple heuristic: Item name usually long string, Qty/Price are floats
                        str_candidates = [str(x) for x in candidates if isinstance(x, str) and len(str(x)) > 3]
                        num_candidates = [float(re.sub(r'[^\d.]', '', str(x))) for x in candidates if str(x).replace('.','').isdigit()]
                        if str_candidates and num_candidates:
                            name_val = str_candidates[0]
                            # Assume first num is qty, second is price
                            qty_val = num_candidates[0]
                            price_val = num_candidates[1] if len(num_candidates) > 1 else 0.0
                            code_val = ""
                        else: continue
                    else: continue
                else:
                    def clean_num(val):
                        if pd.isna(val) or val == "": return 0.0
                        try:
                            s = re.sub(r'[^\d.]', '', str(val))
                            return float(s) if s else 0.0
                        except: return 0.0
                    qty_val = clean_num(row.get(col_map.get('quantity')))
                    price_val = clean_num(row.get(col_map.get('price')))
                    code_val = str(row.get(col_map.get('code'), '')).split('.')[0] if not pd.isna(row.get(col_map.get('code'))) else ''

                if not name_val or any(x in str(name_val).lower() for x in ['total', 'sum', 'إجمالي', 'مجموع']): continue

                def clean_date(val):
                    if pd.isna(val) or val == "" or str(val).lower() == "none": return None
                    try:
                        # Advanced date parsing with format detection
                        return pd.to_datetime(val, errors='coerce').strftime("%Y-%m-%d")
                    except: return None

                results.append({
                    'code': code_val,
                    'name': str(name_val).strip(),
                    'quantity': qty_val,
                    'price': price_val,
                    'production_date': clean_date(row.get(col_map.get('production_date'))),
                    'expiry_date': clean_date(row.get(col_map.get('expiry_date'))),
                    'supplier': str(row.get(col_map.get('supplier'), '')).strip(),
                    'invoice_no': str(row.get(col_map.get('invoice_no'), '')).strip(),
                    'invoice_date': clean_date(row.get(col_map.get('invoice_date'))),
                    'total': clean_num(row.get(col_map.get('total'))),
                    'taxes': clean_num(row.get(col_map.get('taxes'))),
                    'notes': str(row.get(col_map.get('notes'), '')).strip()
                })
            if progress_callback: progress_callback(100)
            return results
        except Exception as e:
            print(f"v6 Hyper-Smart Excel Extraction Error: {e}")
            return []

    def extract_from_pdf(self, file_path: str) -> List[Dict]:
        """Enterprise PDF Extraction: Structural + Multi-page + OCR Fallback."""
        results = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # 1. Structural Digital Table Extraction
                    tables = page.extract_tables()

                    if tables:
                        for table in tables:
                            if not table or len(table) < 2: continue
                            results.extend(self._process_table_rows(table))

                    # 2. Heuristic Line-by-Line (if tables failed or incomplete)
                    if len(results) < 2:
                        text = page.extract_text()
                        if text:
                            results.extend(self._extract_via_heuristics(text))

                # 3. Final OCR Fallback (if still no good data)
                if not results:
                    import pypdfium2 as pdfium
                    pdf_doc = pdfium.PdfDocument(file_path)
                    for i in range(len(pdf_doc)):
                        page = pdf_doc[i]
                        bitmap = page.render(scale=2)
                        pil_image = bitmap.to_pil()
                        # Save to temp and extract
                        temp_path = f"temp_page_{i}.png"
                        pil_image.save(temp_path)
                        results.extend(self.extract_from_image(temp_path))
                        os.remove(temp_path)

            return results
        except Exception as e:
            print(f"PDF Extraction Error: {e}")
            return []

    def _extract_via_heuristics(self, text: str) -> List[Dict]:
        """Advanced Regex & Keyword matching for non-tabular digital text."""
        heuristic_results = []
        # Look for patterns: [Name/Desc] ... [Qty] ... [Price]
        lines = text.split('\n')
        for line in lines:
            # Skip totals
            if any(x in line.lower() for x in ['total', 'sum', 'إجمالي', 'مجموع']): continue

            # Pattern: Long string followed by 1 or 2 numbers
            # Matches many standard invoice formats
            parts = re.findall(r'(\w[\w\s\.-]{5,})\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)?', line)
            for p in parts:
                heuristic_results.append({
                    'name': p[0].strip(),
                    'quantity': float(p[1]),
                    'price': float(p[2]) if p[2] else 0.0,
                    'code': ""
                })
        return heuristic_results

    def extract_from_image(self, file_path: str) -> List[Dict]:
        """OCR Extraction for images using Tesseract + Barcode detection."""
        try:
            import pytesseract
            from PIL import Image
            import cv2
            from pyzbar.pyzbar import decode

            # 1. Barcode/QR Detection
            image_cv = cv2.imread(file_path)
            barcodes = decode(image_cv)
            barcode_data = {}
            if barcodes:
                for bc in barcodes:
                    barcode_data[bc.rect.top] = bc.data.decode('utf-8')

            # 2. Use Tesseract to get data with bounding boxes
            # config='--psm 6' assumes a single uniform block of text.
            # '--psm 11' for sparse text
            data = pytesseract.image_to_data(Image.open(file_path), output_type=pytesseract.Output.DICT)

            rows = {}
            for i in range(len(data['text'])):
                if int(data['conf'][i]) < 40: continue # Skip low confidence
                text = data['text'][i].strip()
                if not text: continue

                y_center = data['top'][i] + data['height'][i] / 2
                row_key = round(y_center / 15) * 15
                if row_key not in rows: rows[row_key] = []
                rows[row_key].append({'text': text, 'x': data['left'][i]})

            structured_rows = []
            for r_key in sorted(rows.keys()):
                cells = sorted(rows[r_key], key=lambda x: x['x'])
                texts = [c['text'] for c in cells]
                if len(texts) < 2: continue

                row_data = {'name': '', 'quantity': 1.0, 'price': 0.0, 'code': ''}

                # Assign nearest barcode if exists
                for b_y, b_val in barcode_data.items():
                    if abs(b_y - r_key) < 30:
                        row_data['code'] = b_val
                        break

                found_num = False
                for t in texts:
                    t_clean = re.sub(r'[^\d.]', '', t)
                    if t_clean and t_clean.replace('.','').isdigit() and len(t_clean) < 10:
                        try:
                            val = float(t_clean)
                            if not found_num:
                                row_data['quantity'] = val; found_num = True
                            else:
                                row_data['price'] = val
                        except: pass
                    elif len(t) > 3 and not row_data['name']:
                        row_data['name'] = t

                if row_data['name']:
                    structured_rows.append(row_data)

            return structured_rows
        except Exception as e:
            print(f"OCR Extraction Error: {e}")
            return []

    def _process_table_rows(self, table):
        rows_data = []
        for row in table[1:]:
            extracted = {'name': '', 'quantity': 0, 'price': 0, 'code': ''}
            for cell in row:
                if not cell: continue
                cell_str = str(cell).strip()
                if re.match(r'^\d+(\.\d+)?$', cell_str):
                    num = float(cell_str)
                    if extracted['quantity'] == 0: extracted['quantity'] = num
                    elif extracted['price'] == 0: extracted['price'] = num
                elif len(cell_str) > 3:
                    if not extracted['name']: extracted['name'] = cell_str
                    elif not extracted['code']: extracted['code'] = cell_str
            if extracted['name'] and extracted['quantity'] > 0:
                rows_data.append(extracted)
        return rows_data
