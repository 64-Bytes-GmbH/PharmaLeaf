""" Set functions """

from django.core.mail import send_mail, get_connection
from .models import MainSettings, EmailRecipients, Logger


def create_log(reference, message, category='info', user='Unknown', stack_trace=''):
    """ create custom log entry """

    log_item = Logger.objects.create(user=user, category=category, reference=reference, message=message, stack_trace=stack_trace)

    if log_item.category in ['error', 'fatal']:
        send_error_mail(log_item)

    return True

######### System Mails #########
def send_error_mail(log_item):
    """ Send error mail """

    main_settings = MainSettings.objects.first()

    subject = f'{ log_item.get_category_display().upper() } - { main_settings.mail_subject }'

    connection = get_connection(
                    host = main_settings.error_mail_host,
                    port = main_settings.error_mail_port,
                    username = main_settings.error_mail,
                    password = main_settings.error_mail_password,
                    use_ssl = True,
                )

    connection_settings = {
        'host': main_settings.error_mail_host,
        'port': main_settings.error_mail_port,
        'username': main_settings.error_mail,
        'password': main_settings.error_mail_password,
        'use_ssl': True,
    }

    message = f'Message:\n{ log_item.message }\n\nTrace Log:\n{ log_item.stack_trace }'

    to_mail_list = []

    for recipient in EmailRecipients.objects.all():
        to_mail_list.append(recipient.email)

    try:
        send_mail(subject, message, main_settings.error_mail, to_mail_list, connection=connection)
    except Exception as e:

        # Create log entry
        log_entry = {
            'reference': 'Mail Connection error',
            'message': 'E-Mail could not be send',
            'stack_trace': f'Conneciton settings: { connection_settings }: { e }',
            'category': 'error'
        }
        create_log(**log_entry)
