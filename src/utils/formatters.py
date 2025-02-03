from decimal import Decimal
from datetime import datetime
from dateutil import parser
import unicodedata

def format_currency(amount: Decimal) -> str:
    return f"R$ {amount:,.2f}"

def convert_comma_to_float(number_str):
    """
    Converts a string number with a comma as a decimal separator to a float.

    Args:
        number_str (str): The input number as a string (e.g., "5,6").

    Returns:
        float: The converted float (e.g., 5.6), or None if the input is invalid.
    """
    try:
        # Replace the comma with a dot and convert to float
        return float(number_str.replace(",", "."))
    except (ValueError, AttributeError):
        # Handle invalid input (e.g., non-numeric strings or None)
        return None

def format_date(date_obj: datetime) -> str:
    return date_obj.strftime('%Y-%m-%d')

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, '%Y-%m-%d')
