# app/tasks.py
from celery import shared_task
from .models import Orders, Pharmacies
from .utils import go_express_check_status, dhl_check_bulk_status, send_order_status_shipped
from db_logger.utils import create_log

@shared_task
def task_update_delivery_status():
    """ Update all delivery status """

    create_log(
        reference='TASK - update_delivery_status',
        message='Delivery status update started',
        category='task',
        user='System'
    )

    for pharmacy in Pharmacies.objects.all():

        # Get all orders for the pharmacy with status ready_to_ship, shipped, delivery_not_possible
        orders = Orders.objects.filter(
            ordered=True,
            pharmacy=pharmacy,
            status__in=['ready_to_ship', 'shipped', 'delivery_not_possible']
        )

        create_log(
            reference='update_delivery_status',
            message=f'Update delivery status for {orders.count()} orders',
            category='task',
            user='System'
        )

        # DHL
        dhl_orders = orders.filter(shipment_label_type='dhl_standard')

        if dhl_orders.count() > 0:
            create_log(
                reference='update_delivery_status',
                message=f'Check delivery status for DHL for {dhl_orders.count()} orders',
                category='task',
                user='System'
            )
            dhl_response = dhl_check_bulk_status(dhl_orders, pharmacy)

            if dhl_response and 'send_mail_order_ids' in dhl_response:
                for order_id in dhl_response['send_mail_order_ids']:
                    order = Orders.objects.get(id=order_id)
                    send_order_status_shipped(order)

    create_log(
        reference='TASK - update_delivery_status',
        message='Delivery status update finished',
        category='task',
        user='System'
    )
