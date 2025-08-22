import re
import pandas as pd
from datetime import datetime
# You will need a PDF library, pdfplumber is recommended
import pdfplumber


class BarodaBankParser:
    """
    A robust parser for Bank of Baroda statements that is resilient to
    common PDF text extraction issues.
    """

    def _extract_account_number(self, text: str) -> str | None:
        """Extracts the 14-digit account number."""
        # This regex is more specific to avoid false positives.
        match = re.search(r'Savings Account\s+([0-9]{14})', text)
        if match:
            return match.group(1)
        return None

    def _parse_amount(self, amount_str: str) -> float:
        """Converts a string amount to a float."""
        return float(amount_str.replace(",", ""))

    def parse(self, file_path: str):
        """
        Main parsing method to extract transactions from the PDF file.

        Args:
            file_path: The path to the PDF statement file.
        """
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text(x_tolerance=2) + "\n"

        account_number = self._extract_account_number(full_text)
        if not account_number:
            raise ValueError("Unable to find account number.")
        print(f"Extracted Account Number: {account_number}")

        transactions = []
        # This regex is the key. It finds all the columns in one go.
        # It looks for Date, Narration, Withdrawal, Deposit, and Balance.
        # The narration is captured non-greedily to handle multi-line entries.
        transaction_pattern = re.compile(
            r'(\d{2}-\d{2}-\d{4})\s+(.*?)\s+([\d,.]*)\s+([\d,.]*)\s+([\d,.]+\s+Cr)',
            re.DOTALL  # Allows '.' to match newlines in the narration
        )

        # Find all matches in the entire text
        matches = transaction_pattern.finditer(full_text)

        for match in matches:
            date_str, narration, debit_str, credit_str, balance_str = match.groups()

            # Clean up the narration by removing extra whitespace and newlines
            details = re.sub(r'\s+', ' ', narration).strip()

            # Skip header rows that might get accidentally matched
            if "NARRATION" in details:
                continue

            transactions.append({
                'date': datetime.strptime(date_str, '%d-%m-%Y').date(),
                'details': details,
                'debit': self._parse_amount(debit_str) if debit_str.strip() else 0.0,
                'credit': self._parse_amount(credit_str) if credit_str.strip() else 0.0,
                'balance': self._parse_amount(balance_str.replace(" Cr", ""))
            })

        if not transactions:
            # If you get here, it means the regex failed.
            # You can uncomment the line below to debug the raw text.
            # print(full_text)
            raise ValueError("No transactions were extracted. The PDF layout may have changed.")

        df = pd.DataFrame(transactions)
        return df

# Create an instance of the parser
parser = BarodaBankParser()

# Call the parse method with the path to your PDF
try:
    df_transactions = parser.parse('data\pawan_statement_unlocked.pdf')
    print(df_transactions)
except (ValueError, FileNotFoundError) as e:
    print(f"Error: {e}")