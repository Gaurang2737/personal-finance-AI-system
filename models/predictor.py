import pandas as pd
from sqlalchemy import create_engine
from utils.database import DataBase_URL
from sklearn.ensemble import RandomForestRegressor
import joblib
from pathlib import Path

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

class spending_predictor:
    def __init__(self,user_id: int):
        self.user_id = user_id
        self.model_path = Path(f"trained_models/spending_predictor_user_{self.user_id}.joblib")
        self.model = RandomForestRegressor(n_estimators=100,random_state=34,n_jobs=-1)
        self.model_path.parent.mkdir(exist_ok=True)

    def train(self,X: pd.DataFrame, y: pd.Series):
        print(f"Training the spending prediction model for user {self.user_id}...")
        self.model.fit(X,y)
        self.save_model()
        print("Model training complete.")

    def save_model(self):
        joblib.dump(self.model, self.model_path)
        print(f"model saved to {self.model_path}")

    def load_model(self)-> bool:
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            print(f"Model loaded from {self.model_path}.")
            return True
        print("No pre-trained model Found.")
        return False

    def predict(self,X:pd.DataFrame)-> list[float]:
        return self.model.predict(X)



