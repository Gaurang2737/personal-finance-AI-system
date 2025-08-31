import streamlit as st
import pandas as pd

from utils.database import SessionLocal, Transactions, Accounts

if 'user_id' not in st.session_state:
    st.warning("Please log in to view this page.")
    st.stop()

def get_transactions_for_user(user_id: int) -> pd.DataFrame:
    db = SessionLocal()
    try:
        query = db.query(Transactions).join(Accounts).filter(Accounts.user_id == user_id)
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

st.set_page_config(page_title='All Transactions',page_icon="💰",layout='wide')
st.title('All Transactions 💰')

if 'user_id' not in st.session_state:
    st.warning('Please log in by entering a username on the Home page first.')
    st.stop()

user_id = st.session_state['user_id']
transaction_df = get_transactions_for_user(user_id)

if transaction_df.empty:
    st.warning('ou have no transactions yet. Please upload a statement on the Home page.')
    st.stop()

st.header('Incoming Payments(Credits)')
credit_df = transaction_df[transaction_df['type']== 'Credit']
total_credit = credit_df['amount'].sum()
st.metric("Total Payments Received",f"₹{total_credit:,.2f}")
st.dataframe(
    credit_df,
    column_config={
        'id':None,
        'account_id':None,
        'date': st.column_config.DateColumn('Date', format="DD MMM YYYY"),
        'details': st.column_config.TextColumn('Details', width='large'),
        'amount': st.column_config.NumberColumn('Amount', format='%.2f'),
        'type':None,
        'category': None
    },
    column_order=['date','details','amount'],
    use_container_width=True,
    hide_index=True
)

st.header('Outgoing Expenses(Debits)')
debit_df = transaction_df[transaction_df['type']=='Debit']
total_debit = debit_df['amount'].sum()
st.metric("Total Expenses",f"₹{total_debit:,.2f}")
st.dataframe(
    debit_df,
    column_config={
        'id':None,
        'account_id':None,
        'date': st.column_config.DateColumn('Date', format="DD MMM YYYY"),
        'details': st.column_config.TextColumn('Details', width='large'),
        'amount': st.column_config.NumberColumn('Amount (₹)', format='%.2f'),
        'type':None,
        'category': 'category'

    },
    column_order=['date','details','amount','category'],
    use_container_width=True,
    hide_index=True
)