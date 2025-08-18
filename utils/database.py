import pandas as pd
from sqlalchemy import create_engine,Float,String,DateTime,Column,Integer,MetaData,ForeignKey
from sqlalchemy.orm import declarative_base,sessionmaker,relationship

DataBase_URL = 'sqlite:///finance_tracker.db'

engine = create_engine(DataBase_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):

    __tablename__ = 'users'
    id = Column(Integer,primary_key = True,autoincrement=True)
    username = Column(String,unique=True,index=True,nullable=False)

    accounts = relationship('Accounts',back_populates='owner')

class Accounts(Base):

    __tablename__ = 'accounts'
    id = Column(Integer,primary_key=True,autoincrement=True)
    account_number = Column(String, nullable=False) # masked account number
    bank_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User',back_populates='accounts')

    transactions = relationship('Transactions',back_populates='account')

class Transactions(Base):

    __tablename__ = 'transactions'
    id = Column(Integer,primary_key=True,autoincrement=True)
    account_id = Column(Integer,ForeignKey('accounts.id'))
    date = Column(DateTime,nullable=False)
    details = Column(String,nullable=False)
    amount = Column(Float,nullable=False)
    type = Column(String,nullable=False)
    category = Column(String,default='Uncategorized')

    account = relationship('Accounts',back_populates='transactions')


def create_database_and_table():
    print('creating Database and table if they dont exist')
    Base.metadata.create_all(bind=engine)
    print('Database setup completed')

def save_transactions_to_db(df: pd.DataFrame, user_id : int, account_number : str, bank_name : str):

    if df.empty:
        print('Dataframe is empty, no transactions to save')
        return
    db = SessionLocal()

    try:
        account = db.query(Accounts).filter_by(
            user_id = user_id,
            account_number = account_number,
            bank_name = bank_name
        ).first()

        if not account:
            print(f"Creating a new account {account_number} for user {user_id}")
            account = Accounts(user_id=user_id, account_number=account_number, bank_name=bank_name)
            db.add(account)
            db.commit()
            db.refresh(account)

        transaction_add = []
        for _, row in df.iterrows():
            exists = db.query(Transactions).filter_by(
                account_id = account.id,
                date = row['date'].to_pydatetime(),
                details = row['details'],
                amount = row['amount'],
                type = row['type'],
            ).first()

            if not exists:
                transaction_add.append(Transactions(**row,account_id = account.id))

        if transaction_add:
            db.add_all(transaction_add)
            db.commit()
            print(f'successfully saved {len(transaction_add)} new transaction for account {account_number}.')
        else:
            print('No transactions to save')
    except Exception as e:
        print(f"An error occurred while saving the transactions: {e}")
        db.rollback()
    finally:
        db.close()