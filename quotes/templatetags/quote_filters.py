from django import template

register = template.Library()

@register.filter
def clean_cleaning_type(value):
    """
    Extract just the cleaning type name from the stored value.
    
    Examples:
    - "1000-1500 (Regular)" -> "Regular"
    - "1500-2000 (Deep)" -> "Deep"
    - "1000-1500 (Move)" -> "Move In/Out"
    - "1000-1500 (Post)" -> "Post Renovation"
    """
    if not value:
        return value
    
    # Handle different cleaning type formats
    if "(" in value and ")" in value:
        # Extract text between parentheses
        start = value.find("(") + 1
        end = value.find(")")
        cleaning_type = value[start:end].strip()
        
        # Map common variations
        cleaning_type_mapping = {
            "Regular": "Regular Cleaning",
            "Deep": "Deep Cleaning", 
            "Move": "Move In/Out Cleaning",
            "Post": "Post Renovation Cleaning"
        }
        
        return cleaning_type_mapping.get(cleaning_type, cleaning_type)
    
    # If no parentheses, return as is
    return value

@register.filter
def get_cleaning_type_name(value):
    """
    Get a clean, user-friendly cleaning type name.
    """
    return clean_cleaning_type(value)

@register.filter
def sub(value, arg):
    """
    Subtract arg from value.
    Usage: {{ value|sub:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiply value by arg.
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
