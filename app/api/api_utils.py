""" Set api general functions """

import base64
from ..models import MainSettings, EmailRecipients
from django.core.files.storage import default_storage

def get_mailchimp_api():
    """ Get Mailchimp api key """

    if MainSettings.objects.first().test_mode:
        return MainSettings.objects.first().mailchimp_api_key_test
    else:
        return MainSettings.objects.first().mailchimp_api_key_prod
    
def get_main_settings():
    """ Get main settings """

    return MainSettings.objects.first()
    
def check_live_status():
    """ Check if settings on test """
    return bool(not MainSettings.objects.first().test_mode)

def currency_format(amount):
    """ Format float to euro """
    formatted_amount = f"{amount:,.2f}".replace(",", ";").replace(".", ",").replace(";", ".")
    return f"{formatted_amount} €"

def get_email_recipients(category, pharmacy=None):
    """ Get all email recipients by category """

    if pharmacy:
        return EmailRecipients.objects.filter(category=category, pharmacy=pharmacy)

    return EmailRecipients.objects.filter(category=category)

def get_file_as_base64(file_path):
    """Konvertiert eine Datei in einen Base64-kodierten String."""
    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as file:
            file_content = file.read()
        return base64.b64encode(file_content).decode('utf-8')
    
    return None

def chunks(lst, n):
    """ Yield successive n-sized chunks from lst. """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
