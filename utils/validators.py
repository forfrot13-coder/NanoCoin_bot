import re

def validate_item_code(code: str):
    return bool(re.match(r"^[A-Z0-9_]{3,20}$", code))

def validate_price(price: int):
    return price > 0

def validate_quantity(quantity: int):
    return quantity > 0
