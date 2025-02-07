import sqlite3
from sqlite3 import Error
from config.settings import DATABASE_PATH

class Database:
    def __init__(self):
        self.conn = None
        self.db_file = DATABASE_PATH
        
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.create_tables()
            self.prepopulate_account_types()  # Add this line
            return self.conn
        except Error as e:
            print(e)
    
    def create_tables(self):
        sql_account_categories = """
        CREATE TABLE IF NOT EXISTS account_categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,  -- Nome original (com acentos e maiúsculas/minúsculas)
            normalized_name TEXT NOT NULL UNIQUE,  -- Nome normalizado (sem acentos e minúsculas)
            description TEXT
        );"""

        sql_accounts = """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,  -- Nome original (com acentos e maiúsculas/minúsculas)
            normalized_name TEXT NOT NULL UNIQUE,  -- Nome normalizado (sem acentos e minúsculas)
            type TEXT CHECK(type IN ('debito', 'credito')),
            specific_type TEXT,
            specific_subtype TEXT,
            category_id INTEGER,
            balance REAL DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES account_categories(id)
        );"""
        
        sql_account_types = """
        CREATE TABLE IF NOT EXISTS account_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            normal_balance TEXT CHECK(normal_balance IN ('debito', 'credito'))
        );"""
        
        sql_transactions = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT,
            debit_account INTEGER,
            credit_account INTEGER,
            amount REAL NOT NULL,
            FOREIGN KEY (debit_account) REFERENCES accounts(id),
            FOREIGN KEY (credit_account) REFERENCES accounts(id)
        );"""
        
        sql_templates = """
        CREATE TABLE IF NOT EXISTS transaction_templates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            details TEXT
        );"""

        sql_fiscal_periods = """
        CREATE TABLE IF NOT EXISTS fiscal_periods (
            id INTEGER PRIMARY KEY,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            interval_days INTEGER NOT NULL
        );"""

        sql_depreciation_methods = """
    CREATE TABLE IF NOT EXISTS depreciation_methods (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        annual_rate REAL
    );"""

        sql_assets = """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            acquisition_date TEXT NOT NULL,
            acquisition_value REAL NOT NULL,
            depreciation_method_id INTEGER,
            useful_life_years INTEGER,
            salvage_value REAL,
            start_depreciation_date TEXT NOT NULL,
            account_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );"""
        
        self.execute(sql_account_categories)
        self.execute(sql_account_types)
        self.execute(sql_accounts)
        self.execute(sql_transactions)
        self.execute(sql_templates)
        self.execute(sql_fiscal_periods)
        self.execute(sql_depreciation_methods)
        self.execute(sql_assets)
    
    def prepopulate_account_types(self):
        predefined_types = [
            ("despesas", "debito"),
            ("ativos", "debito"),
            ("compras", "debito"),
            ("passivos", "credito"),
            ("entradas", "credito"),
            ("vendas", "credito"),
            ("patrimonio", "credito"),
        ]

        sql_select = "SELECT COUNT(*) FROM account_types WHERE name = ? AND normal_balance = ?"
        sql_insert = "INSERT OR IGNORE INTO account_types (name, normal_balance) VALUES (?, ?)"

        for name, normal_balance in predefined_types:
            c = self.execute(sql_select, (name, normal_balance))
            count = c.fetchone()[0]

            if count == 0:
                self.execute(sql_insert, (name, normal_balance))

    def execute(self, sql, params=()):
        try:
            c = self.conn.cursor()
            c.execute(sql, params)
            self.conn.commit()
            return c
        except Error as e:
            print(f"SQL Error: {e}")