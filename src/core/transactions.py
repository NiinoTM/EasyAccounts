from decimal import Decimal
from datetime import datetime
from src.database.models import Transaction
from src.core.accounts import AccountManager

class TransactionManager:
    def __init__(self, db):
        self.db = db
        self.account_manager = AccountManager(db)

    def create_transaction(self, transaction: Transaction) -> bool:
        # Begin transaction
        try:
            # Insert transaction record
            sql = """
            INSERT INTO transactions 
            (date, description, debit_account, credit_account, amount)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute(sql, (
                transaction.date.strftime('%Y-%m-%d'),
                transaction.description,
                transaction.debit_account,
                transaction.credit_account,
                float(transaction.amount)
            ))

            # Update account balances
            self.account_manager.update_balance(transaction.debit_account, -transaction.amount)
            self.account_manager.update_balance(transaction.credit_account, transaction.amount)

            return True
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return False