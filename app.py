import streamlit as st
import pandas as pd
from io import BytesIO
from utils.bank_parser import BankStatementParser
from utils.database import create_database_and_table,save_transactions_to_db,User, SessionLocal

create_database_and_table()

st.set_page_config(
    page_title="Personal Finance AI",
    page_icon="🤖💰",
    layout="centered"
)

st.title('Personal Finance AI System')
st.write(
    "Welcome! Please upload your password-protected bank statement PDF to begin. "
    "Your data is processed locally and is not saved anywhere."
)
st.header('Step1: Enter your Username')
username = st.text_input('Enter you username',help='This can be any name you choose')

st.header('Step2: Please upload your statement')
col1,col2 = st.columns(2)

with col1:
    file_uploaded = st.file_uploader(
        'Upload your bank statement',
        type = ['pdf'],
        help= 'Only password-protected PDF statements are supported.'
    )

with col2:
    file_password = st.text_input(
        'Enter your pdf password',
        type = 'password',
        help="Your password is required to unlock and read the statement."
    )

if st.button('Process Statement',type='primary'):
    if username and file_uploaded and file_password:
        st.spinner('Processing your bank statement..... This may take a moment')
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(username=username).first()
            if not user:
                print(f"Creating new user: {username}")
                user = User(username=username)
                db.add(user)
                db.commit()
                db.refresh(user)
            st.session_state['user_id'] = user.id
            print(f"Current username: {user.username} (ID: {user.id})")

            file_bytes = BytesIO(file_uploaded.getvalue())
            parser = BankStatementParser(file_bytes, file_password)

            bank_name, parsed_data = parser.get_transactions()
            account_number = parsed_data['account_number']
            transactions_df = parsed_data['transactions_df']

            save_transactions_to_db(
                df=transactions_df,
                bank_name=bank_name,
                user_id= user.id,
                account_number= account_number
            )
            st.session_state['transactions-df'] = transactions_df

            st.success('✅ Statement processed and saved successfully!')
            st.info("Navigate to the 'Dashboard' or 'Transactions' page from the sidebar to view your latest upload.")
        except (ValueError,NotImplementedError) as e:
            print(f"❌ error occurred: {e}")
        except Exception as e:
            print(f"❌ An Unexpected error occurred: {e}")
        finally:
            db.close()
    else:
        st.warning('Please provide a username, upload a file, and enter the password.')



st.sidebar.header('Navigation')
st.sidebar.info(
    "This is a multi-page app. After processing your file, "
    "use the navigation above to switch between pages."
)
