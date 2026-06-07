import urllib.parse
import re

def clean_phone_number(phone, country_code='964'):
    """
    Clean the phone number to ensure it can be used with WhatsApp.
    Strips leading zeros and adds the country code if it's not present.
    """
    if not phone:
        return ""
    
    # Remove all non-numeric characters
    cleaned = re.sub(r'\D', '', str(phone))
    
    # If the number starts with 0, remove it and add country code
    # e.g., 07701234567 -> 9647701234567
    if cleaned.startswith('0'):
        cleaned = country_code + cleaned[1:]
    # If it doesn't start with the country code, add it
    elif not cleaned.startswith(country_code):
        cleaned = country_code + cleaned
        
    return cleaned

def generate_whatsapp_link(phone, message):
    """
    Generate a wa.me link with pre-filled message.
    """
    cleaned_phone = clean_phone_number(phone)
    if not cleaned_phone:
        return None
        
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{cleaned_phone}?text={encoded_message}"
