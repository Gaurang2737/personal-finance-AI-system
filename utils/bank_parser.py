import pdfplumber
import pikepdf
from io import BytesIO
from fuzzywuzzy import process
import pytesseract
import re
from PIL import Image

# Use a relative import to bring in our expert parsers
from .parsers import UnionBankParser, SbiParser

# IMPORTANT: This line is specific to your local machine's Tesseract installation.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class BankStatementParser:
    """
    The main controller for parsing bank statements.
    """

    def __init__(self, file_stream, password=None):
        self.file_stream = file_stream
        self.password = password
        self.bank_parsers = {
            "Union Bank of India": UnionBankParser(),
            "State Bank of India": SbiParser(),
        }
        self.known_banks = [bank for bank, parser in self.bank_parsers.items() if parser is not None]

    def identify_bank(self, pdf):
        """
        Identifies the bank using robust text-based "fingerprints".
        """
        print("Attempting to identify bank via text extraction...")
        page_text = ""
        # Read text from the first two pages to ensure we find the fingerprint
        for page in pdf.pages[:2]:
            page_text += page.extract_text(x_tolerance=1, y_tolerance=3) or ""

        # --- THE FIX: Simplified and more robust logic ---
        # We check for unique text fingerprints for each bank in a clear sequence.
        if "sbi.co.in" in page_text or "State Bank of India" in page_text:
            print("Bank identified as: State Bank of India (via text fingerprint)")
            return "State Bank of India"
        if "Union Bank of India" in page_text and "Particulars" in page_text:
            print("Bank identified as: Union Bank of India (via text fingerprint)")
            return "Union Bank of India"

        # The OCR fallback is now a true last resort.
        print("Text-based identification failed. Falling back to OCR...")
        try:
            page_image = pdf.pages[0].to_image(resolution=200)
            pil_image = page_image.original
            width, height = pil_image.size
            header_image = pil_image.crop((0, 0, width, height * 0.3))
            grayscale_image = header_image.convert("L")
            ocr_text = pytesseract.image_to_string(grayscale_image)

            print(ocr_text)

            if "SBI" in ocr_text:
                print("Bank identified as: State Bank of India (via OCR)")
                return "State Bank of India"

            if "UBIN" in ocr_text:
                print("Bank identified as: State Bank of India (via OCR)")
                return "Union Bank of India"


            match, score = process.extractOne(ocr_text, self.known_banks)
            if score > 80:
                print(f"Bank identified as '{match}' via OCR with score {score}%.")
                return match
        except Exception as e:
            print(f"An error occurred during OCR processing: {e}")
            return None

        return None

    def get_transactions(self):
        """
        Opens the PDF, identifies the bank, and runs the correct parser.
        """
        try:
            pdf_file = pikepdf.open(self.file_stream, password=self.password)
            pdf_bytes = BytesIO()
            pdf_file.save(pdf_bytes)
            pdf_bytes.seek(0)

            with pdfplumber.open(pdf_bytes) as pdf:
                bank_name = self.identify_bank(pdf)
                if not bank_name:
                    raise ValueError(
                        "Could not identify the bank from the provided PDF. The format may not be supported.")

                parser_instance = self.bank_parsers.get(bank_name)
                if not parser_instance:
                    raise NotImplementedError(f"A parser for '{bank_name}' has not been implemented yet.")

                print(f"Delegating parsing task to {parser_instance.__class__.__name__}...")
                parsed_data = parser_instance.parse(pdf)

                return bank_name, parsed_data

        except pikepdf.PasswordError:
            raise ValueError("Incorrect password provided for the PDF.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
