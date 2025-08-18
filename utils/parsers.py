import pandas as pd
import re
import pytesseract
from PIL import Image
from datetime import datetime


class UnionBankParser:
    """An expert parser for Union Bank of India statements."""

    def _extract_account_number(self, page_text: str) -> str | None:
        match = re.search(r"Account Number\s*:\s*(\S+)", page_text)
        if match:
            return match.group(1)
        return None

    def parse(self, pdf):
        first_page_text = pdf.pages[0].extract_text()
        account_number = self._extract_account_number(first_page_text)
        if not account_number:
            raise ValueError('Unable to extract account number from the PDF')

        all_transactions = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                header_index = -1
                for i, row in enumerate(table):
                    row_string = "".join(filter(None, row))
                    if "Date" in row_string and "Particulars" in row_string and "Balance" in row_string:
                        header_index = i
                        break
                if header_index != -1:
                    all_transactions.extend(table[header_index + 1:])

        if not all_transactions:
            raise ValueError("No transaction rows could be found in the PDF.")

        df = pd.DataFrame(all_transactions,
                          columns=['SI', 'Date', 'Particulars', 'Chq Num', 'Withdrawal', 'Deposit', 'Balance'])
        df.dropna(subset=['Date'], inplace=True)
        df = df[df['Date'].str.contains(r'\d{2}-\d{2}-\d{4}', na=False)].copy()
        df['Particulars'] = df['Particulars'].str.replace('\n', ' ', regex=False)
        df.rename(columns={'Date': 'date', 'Particulars': 'details', 'Withdrawal': 'debit', 'Deposit': 'credit'},
                  inplace=True)
        df['debit'] = pd.to_numeric(df['debit'].str.replace(',', '', regex=False), errors='coerce')
        df['credit'] = pd.to_numeric(df['credit'].str.replace(',', '', regex=False), errors='coerce')
        df.fillna({'debit': 0, 'credit': 0}, inplace=True)
        df['amount'] = df.apply(lambda row: row['credit'] if row['credit'] > 0 else row['debit'], axis=1)
        df['type'] = df.apply(lambda row: 'Credit' if row['credit'] > 0 else 'Debit', axis=1)
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
        standardized_df = df[['date', 'details', 'amount', 'type']].copy()
        return {'account_number': account_number, 'transactions_df': standardized_df}


class SbiParser:
    """An expert parser for handling multiple State Bank of India (SBI) statement formats."""

    def _identify_format(self, pdf) -> str:
        page_text = pdf.pages[0].extract_text(x_tolerance=1, y_tolerance=3) or ""
        if "sbi.co.in" in page_text:
            return "yono"
        if "Ref No./Cheque No" in page_text:
            return "standard"
        try:
            page_image = pdf.pages[0].to_image(resolution=200).original
            width, height = page_image.size
            header_image = page_image.crop((0, 0, width, height * 0.4))
            ocr_text = pytesseract.image_to_string(header_image)
            if "Relationship Summary" in ocr_text:
                return "yono"
        except Exception as e:
            print(f"OCR for SBI format identification failed: {e}")
        return "standard"

    def _parse_standard_format(self, pdf):
        page_text = pdf.pages[0].extract_text()
        match = re.search(r"Account Number\s*.*?(\d{11})", page_text)
        account_number = match.group(1) if match else None
        if not account_number:
            raise ValueError("Could not extract account number from standard SBI statement.")

        all_transactions = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                header_found = False
                for row in table:
                    if header_found:
                        all_transactions.append(row)
                        continue
                    # A more robust check for the header row
                    row_str = "".join(map(str, filter(None, row)))
                    if "Date" in row_str and "Details" in row_str and "Balance" in row_str:
                        header_found = True

        if not all_transactions:
            raise ValueError("Failed to extract any transaction rows from the standard SBI statement.")

        # Create DataFrame without specifying columns first
        df = pd.DataFrame(all_transactions)

        # Dynamically assign column names based on the actual number of columns found
        if df.shape[1] == 6:
            df.columns = ["Date", "Details", "Ref No./Cheque No", "Debit", "Credit", "Balance"]
        else:
            raise ValueError(f"Unexpected number of columns ({df.shape[1]}) in SBI standard statement table.")

        df.dropna(subset=['Date'], inplace=True)
        df['Date'] = df['Date'].str.replace('\n', ' ', regex=False).str.strip()
        df['date'] = pd.to_datetime(df['Date'], format='%d %b %Y', errors='coerce')
        df.dropna(subset=['date'], inplace=True)

        df.rename(columns={'Details': 'details', 'Debit': 'debit', 'Credit': 'credit'}, inplace=True)
        df['debit'] = pd.to_numeric(df['debit'].str.replace(',', '', regex=False), errors='coerce')
        df['credit'] = pd.to_numeric(df['credit'].str.replace(',', '', regex=False), errors='coerce')
        df.fillna({'debit': 0, 'credit': 0}, inplace=True)

        df['amount'] = df.apply(lambda r: r['credit'] if r['credit'] > 0 else r['debit'], axis=1)
        df['type'] = df.apply(lambda r: 'Credit' if r['credit'] > 0 else 'Debit', axis=1)

        return {"account_number": account_number, "transactions_df": df[['date', 'details', 'amount', 'type']]}

    def _parse_yono_format(self, pdf):
        account_number = None
        for page in pdf.pages[1:3]:
            page_text = page.extract_text()
            if page_text:
                match = re.search(r"XXXXXXX(\d{4})", page_text)
                if match:
                    account_number = "XXXXXXX" + match.group(1)
                    break
        if not account_number:
            raise ValueError("Could not extract account number from Yono statement.")

        all_transactions = []
        for page in pdf.pages:
            if page.page_number < 3: continue
            # --- FIX: Call the method with () ---
            table = page.extract_table()
            if table:
                for row in table:
                    if row and row[0] and (
                            re.search(r'\d{2}-\d{2}-\d{2}', str(row[0])) or "Opening Balance" in str(row[0])):
                        all_transactions.append(row)

        start_index = 0
        for i, row in enumerate(all_transactions):
            if row and "Opening Balance" in str(row[0]):
                start_index = i + 1
                break

        df = pd.DataFrame(all_transactions[start_index:],
                          columns=["Date","Transaction Reference","None_col", "Ref.No./Chq.No.", "Credit", "Debit", "Balance"])
        df = df.iloc[:-1]
        df.dropna(subset=['Date'], inplace=True)
        # --- FIX: Correct date format for Yono (yy not Y) ---
        df['date'] = pd.to_datetime(df['Date'], format='%d-%m-%y')
        # --- FIX: Add inplace=True to the rename operation ---
        df.rename(columns={'Credit': 'credit', 'Debit': 'debit','Transaction Reference':"details"}, inplace=True)

        df['credit'] = pd.to_numeric(df['credit'].astype(str).str.replace(',', '', regex=False), errors='coerce')
        df['debit'] = pd.to_numeric(df['debit'].astype(str).str.replace(',', '', regex=False), errors='coerce')
        df.fillna({'credit': 0, 'debit': 0}, inplace=True)

        df['amount'] = df.apply(lambda x: x['credit'] if x['credit'] > 0 else x['debit'], axis=1)
        df['type'] = df.apply(lambda x: 'Credit' if x['credit'] > 0 else 'Debit', axis=1)
        return {'account_number': account_number, "transactions_df": df[['date', 'details', 'amount', 'type']]}

    def parse(self, pdf):
        statement_format = self._identify_format(pdf)
        if statement_format == 'yono':
            return self._parse_yono_format(pdf)
        else:
            return self._parse_standard_format(pdf)


class BarodaBankParser:
    """
    The definitive, expert parser for Bank of Baroda statements. This version
    uses a robust, stateful parser on layout-preserved text to ensure
    complete data integrity.
    """

    def _extract_account_number(self, page_text: str) -> str | None:
        """Extracts the account number from the page text."""
        match = re.search(r"Savings Account\s*-?\s*(\d{14,})", page_text)
        if match:
            return match.group(1)
        return None

    def _parse_balance(self, balance_str: str) -> float:
        """Converts a balance string like '1,234.56 Cr' to a float for state tracking."""
        if not isinstance(balance_str, str): return 0.0
        balance_val = float(re.sub(r'[^\d.]', '', balance_str))
        return -balance_val if "Dr" in balance_str else balance_val

    def parse(self, pdf):
        """
        The main parsing method that orchestrates the definitive extraction strategy.
        """
        first_page_text = pdf.pages[0].extract_text()
        account_number = self._extract_account_number(first_page_text)
        if not account_number:
            raise ValueError("Unable to extract Account number from the PDF.")
        print(f"Extracted Account Number: {account_number}")

        # --- Initialize the running balance from the Opening Balance ---
        opening_balance_match = re.search(r"Opening Balance\s+([\d,.]+\s(?:Cr|Dr))", first_page_text)
        if not opening_balance_match:
            raise ValueError("Could not find Opening Balance on the first page.")
        last_balance = self._parse_balance(opening_balance_match.group(1))

        # --- A robust, stateful, line-by-line parser ---
        all_transactions = []
        current_transaction = {}

        # A simple, robust regex to identify the START of a transaction line.
        # It only checks for a date at the start and a balance at the end.
        tx_start_regex = re.compile(r"^(\d{2}-\d{2}-\d{4}).*?([\d,.]+\s(?:Cr|Dr))$")

        # Extract text with layout preservation
        all_lines = []
        for page in pdf.pages:
            all_lines.extend(page.extract_text(x_tolerance=1).split('\n'))

        for line in all_lines:
            # Skip irrelevant lines
            if not line.strip() or "Opening Balance" in line or "DATE NARRATION" in line:
                continue

            match = tx_start_regex.match(line)
            if match:
                # This line is the start of a new transaction.
                # First, commit the previously completed transaction.
                if current_transaction:
                    all_transactions.append(current_transaction)

                # --- Start a new transaction record ---
                date_str, balance_str_with_cr_dr = match.groups()

                # Find all numbers on the line to determine amount vs. balance
                numbers = re.findall(r'[\d,]+\.\d{2}', line)

                amount = 0.0
                debit, credit = 0.0, 0.0

                # The narration is everything between the date and the numbers at the end
                narration = re.sub(r'(\s*[\d,]+\.\d{2}\s*)+(Cr|Dr)$', '', line.replace(date_str, '', 1)).strip()

                if len(numbers) > 1:
                    amount = float(numbers[-2].replace(",", ""))

                current_balance = self._parse_balance(balance_str_with_cr_dr)

                # Determine debit/credit by comparing balance change
                if amount > 0:
                    if abs(current_balance - (last_balance - amount)) < 0.01:
                        debit = amount
                    else:
                        credit = amount

                last_balance = current_balance

                current_transaction = {
                    "date": datetime.strptime(date_str, "%d-%m-%Y").date(),
                    "details": narration,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance_str_with_cr_dr.split()[0].replace(",", "")
                }
            elif current_transaction:
                # This is a continuation line for the narration.
                current_transaction["details"] += " " + line.strip()

        # Append the very last transaction
        if current_transaction:
            all_transactions.append(current_transaction)

        if not all_transactions:
            raise ValueError("No transaction rows could be parsed from the PDF.")

        # --- Convert to DataFrame and Finalize ---
        df = pd.DataFrame(all_transactions)
        df['details'] = df['details'].str.replace(r'\s+', ' ', regex=True).str.strip()

        print(df)

