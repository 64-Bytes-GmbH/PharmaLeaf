import requests
import json
from datetime import datetime

from app.models import Orders, MainSettings, EmailTemplates, Invoices, OrderProducts, Pharmacies
from db_logger.utils import create_log

######### Functions #########
def custom_currency_format(amount):
    """ Format float to euro """
    formatted_amount = f"{amount:,.2f}".replace(",", ";").replace(".", ",").replace(";", ".")
    return f"{formatted_amount} €"

def brevo_send_activate_staff_user(user, reset_url):
    """ Send email to customer when order is shipped """

    main_settings = MainSettings.objects.first()
    pharmacy = Pharmacies.objects.first()

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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                'name': f'{user.first_name} {user.last_name}',
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
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

######### User Mails #########
def brevo_send_activate_user(user, reset_url):
    """ Send email to activate user """

    main_settings = MainSettings.objects.first()
    pharmacy = Pharmacies.objects.first()

    try:
        email_template = EmailTemplates.objects.get(email_type='activate_user')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_activate_user',
            f'Error sending email to customer {user.email} for activation',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                'name': f'{user.first_name} {user.last_name}',
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            },
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                
            create_log(
                'brevo_send_activate_user',
                f'Error sending email to customer {user.email} for activation',
                'error',
                'System',
                response.text
            )

def brevo_send_reset_password(user, reset_url):
    """ Send email to reset password """

    main_settings = MainSettings.objects.first()

    try:
        email_template = EmailTemplates.objects.get(email_type='reset_password')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_reset_password',
            f'Error sending email to customer {user.email} to reset password',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                'brevo_send_reset_password',
                f'Error sending email to customer {user.email} to reset password',
                'error',
                'System',
                response.text
            )

######### Order Mails #########
def brevo_send_new_order_created(order_id, confirm_url):
    """ Send email to customer when order is shipped """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    try:
        email_template = EmailTemplates.objects.get(email_type='new_order_created')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_new_order_created',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                'confirm_url': confirm_url,
                'order': {
                    'name': f'{order.first_name} {order.last_name}',
                    'order_date': order.order_time.strftime('%d.%m.%Y'),
                    'order_time': order.order_time.strftime('%H:%M'),
                },
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                
            create_log(
                'brevo_send_new_order_created',
                f'Error sending email to customer {order.email_address} for order {order.number}',
                'error',
                'System',
                response.text
            )


def brevo_send_order_confirmation(order_id):
    """ Send email to customer when order is shipped """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    try:
        email_template = EmailTemplates.objects.get(email_type='order_confirmation')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_order_confirmation',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                    'order_date': order.order_time.strftime('%d.%m.%Y'),
                    'order_time': order.order_time.strftime('%H:%M'),
                    'delivery_type': order.delivery_type,
                    'delivery_type_display': order.get_delivery_type_display(),
                    'payment_type': order.payment_type,
                    'subtotal': custom_currency_format(order.subtotal),
                    'tax_amount': custom_currency_format(order.tax_amount),
                    'total': custom_currency_format(order.total),
                    'delivery_costs': custom_currency_format(order.delivery_costs),
                    'delivery_costs_exist': order.delivery_costs > 0,
                },
                'order_products': [
                    {
                        'name': order_product.product.name,
                        'amount': order_product.amount,
                        'price': custom_currency_format(order_product.price),
                        'total': custom_currency_format(order_product.total),
                    } for order_product in OrderProducts.objects.filter(order=order)
                ],
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                
            create_log(
                'brevo_send_order_confirmation',
                f'Error sending email to customer {order.email_address} for order {order.number}',
                'error',
                'System',
                response.text
            )

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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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

        if response.status_code not in [200, 201]:

            create_log(
                'brevo_send_order_shipped',
                f'Error sending email to customer {order.email_address} for order {order.number}',
                'error',
                'System',
                response.text
            )

def brevo_send_order_cancelled(order_id):
    """ Send email to customer when order is cancelled """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    try:
        email_template = EmailTemplates.objects.get(email_type='order_cancelled')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_order_cancelled',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
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
                    'cancellation_reason': order.cancellation_reason,
                },
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            },
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                
            create_log(
                'brevo_send_order_cancelled',
                f'Error sending email to customer {order.email_address} for order {order.number}',
                'error',
                'System',
                response.text
            )

######### Invoice Mails #########
def brevo_send_pre_invoice(invoice_id, invoice_file):
    """ Send pre invoice to customer """

    main_settings = MainSettings.objects.first()
    invoice = Invoices.objects.get(id=invoice_id)
    pharmacy = invoice.order.pharmacy

    try:
        email_template = EmailTemplates.objects.get(email_type='pre_invoice')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_pre_invoice',
            f'Error sending email to customer {invoice.order.email_address} for invoice {invoice.number}',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'subject': email_template.subject,
            'templateId': email_template.template_id,
            'to':[  
                {
                    'email': invoice.order.email_address,
                    'name': f'{invoice.first_name} {invoice.last_name}'
                }
            ],
            'params': {
                'now': datetime.now().date().year,
                'invoice': {
                    'name': f'{invoice.first_name} {invoice.last_name}',
                    'number': invoice.invoice_number,
                    'invoice_date': invoice.date_time.strftime('%d.%m.%Y'),
                    'invoice_time': invoice.date_time.strftime('%H:%M'),
                    'total': custom_currency_format(invoice.amount_payable),
                },
                'order': {
                    'number': invoice.order.number,
                    'order_date': invoice.order.order_time.strftime('%d.%m.%Y'),
                    'order_time': invoice.order.order_time.strftime('%H:%M'),
                    'delivery_type': invoice.order.get_delivery_type_display(),
                    'payment_type': invoice.order.payment_type,
                },
                'pharmacy': {
                    'paypal_active': pharmacy.paypal_active,
                    'paypal_email': pharmacy.paypal_email,
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            },
            'attachment': [
                {
                    'content': invoice_file,
                    'name': f'{invoice.invoice_number}.pdf',
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                    
            create_log(
                'brevo_send_pre_invoice',
                f'Error sending email to customer {invoice.order.email_address} for invoice {invoice.number}',
                'error',
                'System',
                response.text
            )

        else:

            invoice = Invoices.objects.get(id=invoice_id)
            invoice.send_to_customer = True
            invoice.save()

def brevo_send_invoice(invoice_id, invoice_file):
    """ Send invoice to customer """

    main_settings = MainSettings.objects.first()
    invoice = Invoices.objects.get(id=invoice_id)
    pharmacy = invoice.order.pharmacy

    try:
        email_template = EmailTemplates.objects.get(email_type='payment_received')
    except EmailTemplates.DoesNotExist:
        create_log(
            'brevo_send_invoice',
            f'Error sending email to customer {invoice.order.email_address} for invoice {invoice.number}',
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
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'replyTo': {
                'email': main_settings.brevo_sender_email,
                'name': main_settings.brevo_sender_name
            },
            'subject': email_template.subject,
            'templateId': email_template.template_id,
            'to':[  
                {
                    'email': invoice.order.email_address,
                    'name': f'{invoice.first_name} {invoice.last_name}'
                }
            ],
            'params': {
                'now': datetime.now().date().year,
                'invoice': {
                    'name': f'{invoice.first_name} {invoice.last_name}',
                    'number': invoice.invoice_number,
                    'invoice_date': invoice.date_time.strftime('%d.%m.%Y'),
                    'invoice_time': invoice.date_time.strftime('%H:%M'),
                    'total': custom_currency_format(invoice.amount_payable),
                },
                'order': {
                    'number': invoice.order.number,
                    'order_date': invoice.order.order_time.strftime('%d.%m.%Y'),
                    'order_time': invoice.order.order_time.strftime('%H:%M'),
                    'delivery_type': invoice.order.get_delivery_type_display(),
                    'payment_type': invoice.order.payment_type,
                },
                'pharmacy': {
                    'name': pharmacy.name,
                    'street': pharmacy.street,
                    'street_number': pharmacy.street_number,
                    'postalcode': pharmacy.postalcode,
                    'city': pharmacy.city,
                    'phonenumber': pharmacy.phonenumber,
                    'responsible_pharmacist': pharmacy.responsible_pharmacist,
                    'responsible_for_content': pharmacy.responsible_for_content,
                    'register_court': pharmacy.register_court,
                    'register_number': pharmacy.register_number,
                    'responsible_supervicory_authority': pharmacy.responsible_supervicory_authority,
                    'responsible_chamber': pharmacy.responsible_chamber,
                    'tax_idenfitication': pharmacy.tax_idenfitication,
                }
            },
            'attachment': [
                {
                    'content': invoice_file,
                    'name': f'{invoice.invoice_number}.pdf',
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in [200, 201]:
                    
            create_log(
                'brevo_send_invoice',
                f'Error sending email to customer {invoice.order.email_address} for invoice {invoice.number}',
                'error',
                'System',
                response.text
            )
