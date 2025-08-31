import streamlit as st
import pandas as pd
from io import BytesIO
from utils.bank_parser import BankStatementParser
from utils.database import SessionLocal, User, save_transactions_to_db

if "user_id" not in st.session_state:
    st.warning("Please log in to upload and process a bank statement.")
    st.stop()

st.title("Upload New Bank Statement")
st.write(
    "Please upload your password-protected bank statement PDF to add new transactions. "
    "Your data will be saved to your profile."
)

file_uploaded = st.file_uploader(
    "Upload you bank statement",
    type = ['pdf'],
    help="Only password-protected PDF statements are supported."
)

file_password = st.text_input(
    "Enter your PDF password",
    type= "password",
    help="Your password is required to unlock and read the statement."
)

if st.button("Process Statement",type="primary"):
    if file_uploaded and file_password:
        with st.spinner("Processing your bank statement... This may take a moment."):
            try:
                user_id = st.session_state["user_id"]
                file_bytes = BytesIO(file_uploaded.getvalue())
                parser = BankStatementParser(file_bytes,file_password)

                bank_name , parsed_data = parser.get_transactions()
                account_number = parsed_data["account_number"]
                transactions_df = parsed_data['transactions_df']

                save_transactions_to_db(
                    df=transactions_df,
                    user_id= user_id,
                    account_number= account_number,
                    bank_name= bank_name
                )
                st.success('✅ Statement processed and saved successfully!')
                st.info("Navigate to the 'Dashboard' or 'Transactions' page to view your updated data.")
            except (ValueError, NotImplementedError) as e:
                st.error(f"❌ An error occurred: {e}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {e}")
    else:
        st.warning("Please upload a file and enter the password.")

