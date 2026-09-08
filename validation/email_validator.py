import re

# Standard RFC 5322 regex for email syntax validation
EMAIL_SYNTAX_REGEX = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"

IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']

def is_valid_email(email):
    """
    Validates email format:
    1. Basic syntax check using regex
    2. Ends with an image extension check (discard)
    3. Domain part length check (discard if > 50 characters)
    """
    if not email:
        return False
        
    email = email.strip(" \t\n\r.,;:!?()[]{}'\"")
    
    # 1. Regex syntax match
    if not re.match(EMAIL_SYNTAX_REGEX, email):
        return False
        
    # 2. Check for image extension endings
    email_lower = email.lower()
    if any(email_lower.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return False
        
    # 3. Check domain length limit (domain part length > 50 characters)
    try:
        parts = email.split('@')
        if len(parts) != 2:
            return False
        domain = parts[1]
        if len(domain) > 50:
            return False
    except Exception:
        return False
        
    return True
