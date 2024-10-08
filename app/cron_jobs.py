""" Cerate cronjobs and adjust in settings.py """

from django.utils import timezone
from datetime import timedelta
from db_logger.utils import create_log
from .models import Orders, Customers
from .utils import send_payment_reminder, send_last_payment_reminder, send_overdue_mail
from .tasks import task_update_delivery_status

def cj_send_payment_reminder():
    """ Zahlungserinnerung """

    # Date before 15 days
    _days_ago = timezone.now().date() - timedelta(days=15)

    orders = Orders.objects.filter(
        status              =   'delivered',
        payment_status      =   'pending',
        payment_type        =   'payment_by_invoice',
        delivered_on__date  =   _days_ago
    )

    for order in orders:
        send_payment_reminder(order)

        log_data = {
            'reference': 'Cronjob',
            'message': f'Send payment reminder - Order-Nr. { order.number }',
            'user': 'System',
        }

        create_log(**log_data)

def cj_send_last_payment_reminder():
    """ Mahnung """

    # Date before 21 days
    _days_ago = timezone.now().date() - timedelta(days=6)

    orders = Orders.objects.filter(
        status              =   'delivered',
        payment_status      =   'invoice_reminder',
        payment_type        =   'payment_by_invoice',
        invoice_reminder_send_on__date  =   _days_ago
    )

    for order in orders:

        send_last_payment_reminder(order)

        log_data = {
            'reference': 'Cronjob',
            'message': f'Send last payment reminder - Order-Nr. { order.number }',
            'user': 'System',
        }

        create_log(**log_data)

def cj_check_overdue():
    """ Überfälligkeit überprüfen """

    # Date before 6 days
    _days_ago = timezone.now().date() - timedelta(days=6)

    orders = Orders.objects.filter(
        status              =   'delivered',
        payment_status      =   'last_reminder',
        payment_type        =   'payment_by_invoice',
        last_reminder_send_on__date  =   _days_ago
    )

    for order in orders:

        send_overdue_mail(order)

        customer = Customers.objects.get(id=order.customer.id)
        customer.blocked = True
        customer.save()

        log_data = {
            'reference': 'Cronjob',
            'message': f'Payment is overdue - Order-Nr. { order.number }',
            'user': 'System',
        }

        create_log(**log_data)

def cj_check_delivery_status():
    """ Lieferstatus überprüfen """
    task_update_delivery_status.delay()
