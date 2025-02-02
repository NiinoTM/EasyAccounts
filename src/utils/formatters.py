from decimal import Decimal
from datetime import datetime
import unicodedata

def format_currency(amount: Decimal) -> str:
    return f"R$ {amount:,.2f}"

def format_date(date_obj: datetime) -> str:
    return date_obj.strftime('%Y-%m-%d')

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, '%Y-%m-%d')


