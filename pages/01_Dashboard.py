import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import SessionLocal, Transactions, Accounts
from models.categorizer import SmartCategorizer

@st.cache_resource
def load_categorizer():
    return SmartCategorizer()


def clean_transaction_detail(detail : str) -> str:
    parts = detail.split('/')
    try:
        if 'DR' in parts:
            index = parts.index('DR')
            return parts[index + 1].strip()
        elif 'CR' in parts:
            index = parts.index('CR')
            return parts[index + 1].strip()
    except (ValueError, IndexError):
        return detail[:40]
    return detail[:40]

def get_all_transactions_for_user(user_id : int) -> pd.DataFrame:
    db = SessionLocal()

    try:
        query = db.query(Transactions).join(Accounts).filter(Accounts.user_id == user_id)
        df = pd.read_sql(query.statement,db.bind)
        return df
    finally:
        db.close()

def update_transaction_category(df: pd.DataFrame):
    db = SessionLocal()
    try:
        db.bulk_update_mappings(Transactions,df.to_dict(orient='records'))
        db.commit()
    except Exception as e:
        print(f"error updating categories: {e}")
        db.rollback()
    finally:
        db.close()

st.set_page_config(page_title='Dashboard Page', page_icon="📊", layout='wide')
st.title('Personal Finance Dashboard 📊')

if "user_id" not in st.session_state:
    st.warning('Please log in by entering a username on the Home page first.')
    st.stop()

user_id = st.session_state['user_id']
transactions_df = get_all_transactions_for_user(user_id)
categorizer = load_categorizer()

if transactions_df.empty:
    st.info('You have no transactions yet. Please upload a statement on the Home page.')
    st.stop()

categorized_df = transactions_df[transactions_df['category']!= 'Uncategorized']
uncategorized_df = transactions_df[transactions_df['category'] == 'Uncategorized']

if not categorized_df.empty and not uncategorized_df.empty:
    st.toast('🤖 Running AI Smart Categorizer...')
    categorizer.fit(categorized_df)
    uncategorized_details = uncategorized_df['details'].tolist()
    predict_categories=categorizer.predict(uncategorized_details)
    uncategorized_df['category'] = predict_categories
    display_df = pd.concat([categorized_df,uncategorized_df]).sort_values(by='date')
else:
    display_df = transactions_df.copy()

debits_df = display_df[display_df['type'] == 'Debit'].copy()
debits_df['summary'] = debits_df['details'].apply(clean_transaction_detail)

st.header('Categorize Your Expenses.')
st.write('Our AI has suggested categories for new transactions. Review and save the changes.')

with st.form('category_form'):
    edited_df = st.data_editor(
        debits_df,
        column_config={
            'id': None,
            'account_id' : None,
            'date' : st.column_config.DateColumn('Date',format= 'DD MMM YYYY'),
            'details' : st.column_config.TextColumn('Details', width='large'),
            'amount' : st.column_config.NumberColumn('Amount (₹)', format = '%.2f'),
            'type' : None,
            'category' : st.column_config.SelectboxColumn(
                'Category',
                options=["Uncategorized", "Food & Dining", "Shopping", "Travel", "Bills & Utilities", "Transfers", "Entertainment", "Health"],
                required=True
            )
        },
        hide_index = True,
        use_container_width=True,
        key=f"editor_{user_id}"
    )

    submitted = st.form_submit_button('Apply Changes',type='primary')
    if submitted:
        original_debits = debits_df.set_index('id')
        edited_debits = edited_df.set_index('id')
        changed_rows = original_debits[original_debits['category'] != edited_debits['category']]
        if not changed_rows.empty:
            updated_df = edited_debits.loc[changed_rows.index][['category']].reset_index()
            update_transaction_category(updated_df)
            st.success("Your changes have been saved to the database!")
            st.rerun()
        else:
            st.info('No changes were made.')

st.header('Expense Analysis')
col1,col2 = st.columns(2)
with col1:
    st.header('Summary by Category')
    category_totals = edited_df.groupby('category')['amount'].sum().reset_index()
    category_totals = category_totals.sort_values('amount',ascending=False)
    st.dataframe(
        category_totals,
        column_config={
            'category':'category',
            'amount' : st.column_config.NumberColumn('Date',format='%.2f')
        },
        hide_index=True,
        use_container_width=True
    )

with col2:
    st.header('Spending BreakDown')
    fig = px.pie(
        category_totals,
        values='amount',
        names='category',
        title='Expense by Category',
        hole=0.3
    )
    fig.update_traces(textposition = 'inside', textinfo= 'percent+label')
    st.plotly_chart(fig,use_container_width=True)


