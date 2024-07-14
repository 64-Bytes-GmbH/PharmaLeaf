import requests
import json
from datetime import datetime

from app.models import Orders, MainSettings, EmailTemplates
from db_logger.utils import create_log

def brevo_send_test_mail(email):
    """ Send email to staff user when account is activated """

    main_settings = MainSettings.objects.first()

    if main_settings.brevo_api_key and main_settings.brevo_base_url:

        api_key = main_settings.brevo_api_key
            
        url = f'{main_settings.brevo_base_url}/v3/smtp/email'

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api-key': api_key,
        }

        payload = {
            'sender': {
                'email': 'no-reply@higreen-apotheke.de',
                'name': 'higreen! Apotheke'
            },
            'subject': 'Test E-Mail',
            'templateId': 1,
            'messageVersions': [
                {
                    'to': [
                        {
                            'email': email,
                            'name': 'Bob Anderson'
                        },
                    ],
                    'subject':'We are happy to be working with you'
                },
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(response.status_code)

def brevo_send_order_shipped(order_id):
    """ Send email to customer when order is shipped """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)

    try:
        email_template = EmailTemplates.objects.get(email_type='order_shipped')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_order_shipped',
            f'Error sending email to customer {order.email_address} for order {order.number}',
            'error',
            'System',
            'Email template not found'
        )
        return


    if main_settings.brevo_api_key and main_settings.brevo_base_url:

        api_key = main_settings.brevo_api_key
            
        url = f'{main_settings.brevo_base_url}/v3/smtp/email'

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api-key': api_key,
        }

        payload = {
            'sender': {
                'email': 'no-reply@higreen-apotheke.de',
                'name': 'higreen! Apotheke'
            },
            'subject': email_template.subject,
            'templateId': email_template.template_id,
            'to':[  
                {
                    'email': order.email_address,
                    'name': f'{order.first_name} {order.last_name}'
                }
            ],
            'params': {
                'now': datetime.now().date().year,
                'order': {
                    'name': f'{order.first_name} {order.last_name}',
                    'number': order.number,
                    'delivery_type': order.get_delivery_type_display(),
                    'shipment_no': order.shipment_shipment_no,
                },
            },
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response.text)

        if response.status_code not in [200, 201]:

            create_log(
                'brevo_send_order_shipped',
                f'Error sending email to customer {order.email_address} for order {order.number}',
                'error',
                'System',
                response.text
            )

def brevo_send_activate_staff_user(user, reset_url):
    """ Send email to customer when order is shipped """

    main_settings = MainSettings.objects.first()

    try:
        email_template = EmailTemplates.objects.get(email_type='activate_staff_user')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_activate_staff_user',
            f'Error sending email to staff user {user.email} for activation',
            'error',
            'System',
            'Email template not found'
        )
        return


    if main_settings.brevo_api_key and main_settings.brevo_base_url:

        api_key = main_settings.brevo_api_key
            
        url = f'{main_settings.brevo_base_url}/v3/smtp/email'

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api-key': api_key,
        }

        payload = {
            'sender': {
                'email': 'no-reply@higreen-apotheke.de',
                'name': 'higreen! Apotheke'
            },
            'subject': email_template.subject,
            'templateId': email_template.template_id,
            'to':[  
                {
                    'email': user.email,
                    'name': f'{user.first_name} {user.last_name}'
                }
            ],
            'params': {
                'now': datetime.now().date().year,
                'reset_url': reset_url,
                'name': f'{user.first_name} {user.last_name}'
            },
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:

            create_log(
                'brevo_send_order_shipped',
                f'Error sending email to staff user {user.email} for activation',
                'error',
                'System',
                response.text
            )
