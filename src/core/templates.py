# src/core/templates.py
from dataclasses import dataclass
from typing import List
import json
from decimal import Decimal
from datetime import datetime

@dataclass
class TemplateTransaction:
    description: str
    debit_account: int
    credit_account: int
    amount: float

@dataclass
class TransactionTemplate:
    id: int = None
    name: str = ""
    transactions: List[TemplateTransaction] = None

    def to_json(self):
        return json.dumps([{
            'description': t.description,
            'debit_account': t.debit_account,
            'credit_account': t.credit_account,
            'amount': t.amount
        } for t in self.transactions])

    @staticmethod
    def from_json(template_id: int, name: str, json_str: str):
        data = json.loads(json_str)
        transactions = [
            TemplateTransaction(
                description=t['description'],
                debit_account=t['debit_account'],
                credit_account=t['credit_account'],
                amount=t['amount']
            ) for t in data
        ]
        template = TransactionTemplate(template_id, name)
        template.transactions = transactions
        return template

# src/services/template_service.py
