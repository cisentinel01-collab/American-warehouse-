import barcode
from barcode.writer import ImageWriter
import os

class BarcodeGenerator:
    @staticmethod
    def generate(code_text, filename):
        os.makedirs("images/barcodes", exist_ok=True)
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(code_text, writer=ImageWriter())
        path = os.path.join("images/barcodes", filename)
        ean.save(path)
        return path + ".png"
