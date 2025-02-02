from datetime import datetime
from decimal import Decimal, InvalidOperation
import unicodedata

from datetime import datetime

def validate_date(date_str, format="%d-%m-%Y"):
    """
    Validate if the date string is in the specified format.
    
    Args:
        date_str (str): The date string to validate.
        format (str): The format to validate against. Default is "%d-%m-%Y".
    
    Returns:
        bool: True if the date string is valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_amount(amount_str: str) -> bool:
    try:
        amount = Decimal(amount_str)
        return amount > 0
    except InvalidOperation:
        return False

def validate_account_type(normal_balance: str) -> bool:
    return normal_balance.lower() in ['debito', 'credito']

def normalizar_nome(texto):
    """
    Normaliza o nome: remove acentos e converte para minúsculas.
    Exemplo: "Coração" -> "coracao"
    """
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    texto_sem_acentos = ''.join(c for c in texto_normalizado if not unicodedata.combining(c))
    return texto_sem_acentos.lower()