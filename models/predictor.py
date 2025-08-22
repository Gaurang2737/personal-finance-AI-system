import pandas as pd
from sqlalchemy import create_engine
from utils.database import DataBase_URL

def get_daily_spending_history(user_id: int) -> pd.DataFrame:
    engine = create_engine(DataBase_URL)
    query=f'''
     SELECT date,amount
     FROM transactions
     JOIN accounts ON transactions.account_id = accounts.id
     WHERE accounts.user_id = {user_id} AND transactions.type = 'Debit' 
     '''
    df = pd.read_sql(query,engine,parse_dates=['date'])
    if df.empty:
        return pd.DataFrame({'total_spending':[]})
    df.set_index('date',inplace=True)
    daily_spending = df['amount'].resample('D').sum().fillna(0)
    return daily_spending.to_frame(name="total_spending")

def create_feature(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['dayofweek'] = df.index.dayofweek
    df['dayofmonth'] = df.index.day
    df['month'] = df.index.month
    df['year'] = df.index.year

    df['lag_7'] = df['total_spending'].shift(7).fillna(0)
    df['rolling_7_day_avg'] = df['total_spending'].rolling(window=7).mean().fillna(0)
    return df

if __name__ == "__main__":
    test_user_id = 1
    daily_data = get_daily_spending_history(test_user_id)
    feature_data = create_feature(daily_data)
    print(feature_data.head())
    print('\n \n \n')
    print(feature_data.tail())

