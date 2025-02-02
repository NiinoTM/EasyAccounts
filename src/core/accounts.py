from decimal import Decimal
from src.database.models import Account, AccountType
from src.database.models import AccountCategory
from typing import Optional, List


class AccountManager:
    def __init__(self, db):
        self.db = db

    def create_account(self, name: str, type_id: int, specific_subtype: Optional[str] = None) -> Account:
        sql = "INSERT INTO accounts (name, type_id, specific_subtype) VALUES (?, ?, ?)"
        cursor = self.db.execute(sql, (name, type_id, specific_subtype))
        return Account(cursor.lastrowid, name, type_id, specific_subtype)

    def update_balance(self, account_id: int, amount: Decimal):
        sql = "UPDATE accounts SET balance = balance + ? WHERE id = ?"
        self.db.execute(sql, (amount, account_id))

    def get_account(self, account_id: int) -> Account:
        sql = """
        SELECT id, name, type_id, balance 
        FROM accounts 
        WHERE id = ?
        """
        result = self.db.execute(sql, (account_id,)).fetchone()
        if result:
            return Account(*result)
        return None

    def get_accounts_by_name_or_id(self, search_term: str) -> List[Account]:
        """
        Retrieves accounts that match the search term (ID or name).
        If search_term is empty, returns all accounts.
        """
        sql = """
        SELECT id, name, type, specific_type, specific_subtype, category_id 
        FROM accounts 
        WHERE id = ? OR name LIKE ?
        """
        try:
            # Try to convert the search term to an integer (for ID search)
            account_id = int(search_term)
            results = self.db.execute(sql, (account_id, f"%{search_term}%")).fetchall()
        except ValueError:
            # If search term is not a number, search only by name
            if search_term.strip():  # If search_term is not empty
                results = self.db.execute(sql, (-1, f"%{search_term}%")).fetchall()
            else:
                # If search_term is empty, return all accounts
                sql_all = "SELECT id, name, type, specific_type, specific_subtype, category_id FROM accounts"
                results = self.db.execute(sql_all).fetchall()

        return [Account(*result) for result in results]

    def update_account(self, account_id: int, new_name: str, new_type_id: int, new_subtype: Optional[str] = None) -> bool:
        """
        Atualiza os dados de uma conta existente.
        Retorna True se a conta foi atualizada com sucesso.
        """
        sql = """
        UPDATE accounts 
        SET name = ?, type_id = ?, specific_subtype = ?
        WHERE id = ?
        """
        try:
            self.db.execute(sql, (new_name, new_type_id, new_subtype, account_id))
            return True
        except Exception as e:
            print(f"Erro ao atualizar conta: {e}")
            return False

    def delete_account(self, account_id: int) -> bool:
        """
        Exclui uma conta existente.
        Retorna True se a conta foi excluída com sucesso.
        """
        sql = "DELETE FROM accounts WHERE id = ?"
        try:
            self.db.execute(sql, (account_id,))
            return True
        except Exception as e:
            print(f"Erro ao excluir conta: {e}")
            return False
        
    def get_categories_by_name_or_id(self, search_term: str) -> List[AccountCategory]:
        """
        Retrieves categories that match the search term (ID or name).
        If search_term is empty, returns all categories.
        """
        sql = """
        SELECT id, name, description 
        FROM account_categories 
        WHERE id = ? OR name LIKE ?
        """
        try:
            # Try to convert the search term to an integer (for ID search)
            category_id = int(search_term)
            results = self.db.execute(sql, (category_id, f"%{search_term}%")).fetchall()
        except ValueError:
            # If search term is not a number, search only by name
            if search_term.strip():  # If search_term is not empty
                results = self.db.execute(sql, (-1, f"%{search_term}%")).fetchall()
            else:
                # If search_term is empty, return all categories
                sql_all = "SELECT id, name, description FROM account_categories"
                results = self.db.execute(sql_all).fetchall()

        return [AccountCategory(*result) for result in results]