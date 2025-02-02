from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional  # Add this import

@dataclass
class AccountType:
    id: Optional[int]
    name: str
    normal_balance: str  # 'debito' or 'credito'

@dataclass
class Account:
    id: Optional[int]
    name: str
    type_id: int          # This will receive the value from the "type" column in your query.
    specific_type: Optional[str] = None    # New field added to capture the "specific_type" from the query.
    specific_subtype: Optional[str] = None
    category_id: Optional[int] = None      # New field added to capture the "category_id" from the query.
    balance: Decimal = Decimal('0')        # This field will remain with its default value.

@dataclass
class Transaction:
    id: Optional[int]
    date: date
    description: str
    debit_account: int
    credit_account: int
    amount: Decimal

@dataclass
class TemplateTransaction:  # Add this class
    description: str
    debit_account: int
    credit_account: int
    amount: float

@dataclass
class TransactionTemplate:
    id: Optional[int] = None
    name: str = ""
    transactions: List[TemplateTransaction] = None  # Use List and TemplateTransaction

@dataclass
class AccountCategory:
    id: Optional[int]
    name: str
    description: Optional[str] = None