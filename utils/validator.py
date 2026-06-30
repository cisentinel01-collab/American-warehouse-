import re

class Validator:
    @staticmethod
    def is_not_empty(text):
        return bool(text and text.strip())

    @staticmethod
    def is_valid_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def is_valid_phone(phone):
        pattern = r'^\+?[0-9\s-]{8,}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def setup_strict_validation(line_edit, type="text"):
        """
        Setup QValidator for QLineEdit based on type
        """
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression

        if type == "name":
            # Arabic and English letters, no numbers
            regex = QRegularExpression(r"^[^\d]*$")
            validator = QRegularExpressionValidator(regex)
            line_edit.setValidator(validator)
        elif type == "phone":
            regex = QRegularExpression(r"^[0-9\+\-\s]*$")
            validator = QRegularExpressionValidator(regex)
            line_edit.setValidator(validator)
