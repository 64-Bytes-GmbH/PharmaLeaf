""" Request methods """

import json
import re
import os
import base64

from io import BytesIO
from django.conf import settings
from weasyprint import HTML
from xhtml2pdf.files import pisaFileObject
from datetime import datetime, timezone, timedelta
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from app.models import MainSettings, Products, ProductImages, ProductPrices,\
                        Pharmacies, StockProducts, OrderProducts,\
                        Orders, OrderRecipes, OrderInsuranceConfirmation,\
                        IdentificationFiles, CancellationReasons, OrderProducts,\
                        OrderRecipes, OrderInsuranceConfirmation, IdentificationFiles,\
                        CancellationReasons, Invoices, Customers, User, StaffUser,\
                        PharmacyEmployees, PackedOrderedProducts, Packages, StandardFillingProtocolIds,\
                        FillProtocols, ProductThresholds, PackageManufacturers, UserPremissions,\
                        EmailRecipients
from db_logger.utils import create_log
from django.urls import reverse
from app.utils import sum_product_ordered_amount, custom_currency_format, check_status_for_mail,\
                        get_order_details, send_order_status_shipped, create_new_invoice,\
                        send_new_order_created, get_order_package_data, shorten_string,\
                        create_stock_product_log, create_package_log, import_products,\
                        import_terpene, import_product_prices, import_product_images, add_product_to_cart,\
                        send_activate_staff_user, generate_invoice_customer, generate_invoice_insurance,\
                        export_order_products
from app.api.dhl import dhl_create_label, dhl_cancel_label, dhl_check_status, order_shipment_pick_up
from app.api.go_express import go_express_create_label, go_express_cancel_label, go_express_check_status, go_express_update_label, go_express_update_status
from app.tasks import task_update_delivery_status

def product_datas_v1(request):
    """ Get product datas """

    data = {}
    
    if request.method == 'POST':

        if 'searchWord' in request.POST:

            search_word = request.POST.get('search')
            pharmacy_id = request.POST.get('pharmacyId')

            try:
                pharmacy = Pharmacies.objects.get(id=pharmacy_id)
            except Pharmacies.DoesNotExist:

                response = {
                    'error': True,
                    'message': f'Pharmacy not found with id: {pharmacy_id}',
                }

                create_log(
                    reference='product_datas',
                    message=f'Pharmacy not found with id: {pharmacy_id}',
                    category='error',
                )
                return JsonResponse(response, status=404)

            items = []

            if search_word:

                values = search_word.split(' ')
                values = [value for value in values if value]

                q_objects = Q()

                for value in values:

                    q_objects &= (
                        Q(product__name__icontains=value) |
                        Q(product__cultivar__name__icontains=value) |
                        Q(product__genetics__name__icontains=value) |
                        Q(product__manufacturer__name__icontains=value) |
                        Q(product__main_terpene__name__icontains=value) |
                        Q(product__main_terpene__terpene_effect__name__icontains=value)
                    )

                product_ids = ProductPrices.objects.filter(pharmacy=pharmacy, active=True).filter(q_objects).distinct().order_by('-status').values_list('product__id', flat=True).distinct()

                products = Products.objects.filter(id__in=product_ids)

                for item in products:

                    product_image = ProductImages.objects.filter(product=item, main_image=True).first()
                    product_price = ProductPrices.objects.get(product=item, pharmacy=pharmacy)

                    total_stock_amount = StockProducts.objects.filter(product=item, pharmacy=pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                    total_booked_amount = sum_product_ordered_amount(item, pharmacy)

                    status = 2 if total_stock_amount - total_booked_amount >= 0 and (total_stock_amount > 0) else '0'
                    status_display = 'Verfügbar' if status == 2 else 'Nicht verfügbar'

                    items.append({
                        'id': item.id,
                        'name': item.name,
                        'img': product_image.img.url if product_image else '',
                        'cultivar': item.cultivar.name if item.cultivar else '',
                        'genetics': item.genetics.name if item.genetics else '',
                        'thc_value': round(item.thc_value * 100),
                        'cbd_value': round(item.max_cbd_value * 100),
                        'status': str(status),
                        'status_display': status_display,
                        'available_amount': total_stock_amount - total_booked_amount,
                    })

                sorted_items = sorted(items, key=lambda x: x['status'], reverse=True)

            data['items'] = sorted_items

    return HttpResponse(json.dumps(data), content_type='application/json')

def order_functions_v1(request):
    """ Order functions """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:

        create_log(
            reference='order_functions',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':

        if 'changeDeliveryType' in request.POST:
            
            order_id = request.POST.get('orderId')
            delivery_type = request.POST.get('deliveryType')

            order = Orders.objects.get(id=order_id)
            order.delivery_type = delivery_type
            order.save()

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'checkDeliveryLabel' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            data['deliveryLabelExists'] = bool(order.shipment_shipment_no)
            data['status'] = order.status

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'changeStatus' in request.POST:

            order_id = request.POST.get('orderId')
            status_name = request.POST.get('statusName')
            new_status = request.POST.get('newStatus')
            comment = request.POST.get('comment')

            # Get order by id
            order = Orders.objects.get(id=order_id)

            # Check if delivery label is generated before update
            if status_name == 'status' and new_status == 'shipped' and not order.shipment_shipment_no:
                data['stateError'] = True
                data['message'] = 'Bitte erstellen Sie zuerst ein <strong>Versandlabel</strong> bevor Sie den Status auf "Versendet" setzen.'
                return HttpResponse(json.dumps(data), content_type='application/json')

            # Old status for comparison
            old_status = getattr(order, status_name)

            # Set status by status name
            setattr(order, status_name, new_status)

            if status_name == 'payment_status' and new_status == 'received':
                order.payed_on = timezone.now()

            if new_status == 'cancelled' and comment and comment != '':
                order.cancellation_reason = CancellationReasons.objects.get(id=comment)

                # Create log entry
                log_entry = {
                    'reference': f'Bestellung { order.number }',
                    'message': f'Bestellung storniert. Grund: {comment}',
                    'user': f'({ request.user.id }) { request.user.username }'
                }
                create_log(**log_entry)

            if new_status == 'queries' and comment and comment != '':
                order.queries_comment = comment

            if new_status == 'clarified' and comment and comment != '':
                order.clarified_comment = comment

            order.save()

            # Create log entry
            log_entry = {
                'reference': f'Bestellung { order.number }',
                'message': f'Bestellung aktualisiert. {status_name}: {new_status}',
                'user': f'({ request.user.id }) { request.user.username }'
            }
            create_log(**log_entry)

            # Check status change and send maiil
            check_status_for_mail(order, status_name, old_status, new_status, request)

            data['newStatusDisplay'] = getattr(order, f'get_{status_name}_display')()
            data['newStatus'] = getattr(order, status_name)
            data['orderStatus'] = order.status
            data['orderStatusDisplay'] = order.get_status_display()

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'completeIdentCheck' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            order.ident_check = True
            order.save()

            # Create log entry
            log_entry = {
                'reference': f'Bestellung { order.number }',
                'message': 'Ident-Check bestätigt (Kauf auf Rechnung).',
                'user': f'({ request.user.id }) { request.user.username }'
            }
            create_log(**log_entry)

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'getOrderDetails' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)
            order_products = OrderProducts.objects.filter(order=order)
            order_recipes = OrderRecipes.objects.filter(order=order)
            order_insurance_confirmations = OrderInsuranceConfirmation.objects.filter(order=order)

            identification_files = IdentificationFiles.objects.filter(order=order)

            ident_check_images = []
            for item in identification_files:
                ident_check_images.append(
                    {
                        'id': item.id,
                        'id_number': item.id_number,
                        'file': item.file.url if item.file else ''
                    }
                )

            order_products_array = []
            for order_product in order_products:

                total_stock_amount = StockProducts.objects.filter(product=order_product.product, pharmacy=order_product.order.pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                total_booked_amount = OrderProducts.objects.filter(
                    product=order_product.product,
                    calculated_in_stock=False,
                    order__ordered=True,
                    order__pharmacy=order_product.order.pharmacy,
                ).aggregate(total=Sum('amount'))['total'] or 0

                available_amount = 0 if total_stock_amount - total_booked_amount <= 0 else total_stock_amount - total_booked_amount

                amount_label = 'Menge (g)' if order_product.product.form == 'flower' else 'Anzahl'
                amount_label = amount_label + f' (Verfügbar: {available_amount})'

                order_products_array.append({
                    'id': order_product.id,
                    'productId': order_product.product.id,
                    'name': order_product.product.name,
                    'amount': order_product.amount,
                    'amountLabel': amount_label,
                    'prepared': order_product.prepared,
                    'supplier': order_product.product.supplier.name,
                    'form': order_product.product.get_form_display(),
                    'total': custom_currency_format(order_product.total),
                    'products': [{'id': item.product.id, 'name': item.product.name, 'thc': f'{round(item.product.thc_value * 100)} %', 'genetic': item.product.genetics.name if item.product.genetics else ''} for item in ProductPrices.objects.filter(active=True, pharmacy=order.pharmacy).order_by('product__name')],
                    'preparedChoices': [{'value': False, 'name': 'unverändert'}, {'value': True, 'name': 'Zerkleinert'}],
                    'thc': f"{round(order_product.product.thc_value * 100, 2)}%",
                    'genetic': order_product.product.genetics.name if order_product.product.genetics else '',
                    'isEnoughAvailable': True if available_amount >= order_product.amount else False,
                })

            delivery_button_status = False
            if order.is_packed:
                if order.payment_type == 'payment_by_invoice' and order.recipe_status == 'checked':
                    delivery_button_status = True
                elif order.payment_status == 'received' and order.recipe_status == 'checked':
                    delivery_button_status = True

            recipe_files = []
            for recipe_file in order_recipes:
                recipe_files.append({
                    'id': recipe_file.id,
                    'number': recipe_file.number,
                    'url': recipe_file.file.url,
                })

            order_details = {
                'id': order.id,
                'orderNumber': order.number,
                'orderDate': order.order_time.strftime('%d.%m.%Y | %H:%M Uhr'),
                'orderAmount': custom_currency_format(order.total),
                'recipeFiles': recipe_files,
                'insuranceConfirmation': order_insurance_confirmations.first().file.name if order_insurance_confirmations else False,
                'insuranceConfirmationURL': order_insurance_confirmations.first().file.url if order_insurance_confirmations else False,
                'paymentType': order.payment_type,
                'paymentStatus': order.payment_status,
                'recipeStatus': order.recipe_status,
                'orderStatus': order.status,
                'deliveryButtonStatus': delivery_button_status,
                'shipmentLabelType': order.get_shipment_label_type_display() if order.shipment_label_type else '',
                'shipmentShipmentNo': order.shipment_shipment_no,
                'pickUpButtonStatus': True if order.shipment_shipment_no and order.shipment_shipment_no != '' else False,
                'pickUpStatus': True if order.shipment_pickup_order_uuid and order.shipment_pickup_order_uuid != '' else False,
                'pickUpDate': order.shipment_pickup_date.strftime('%d.%m.%Y') if order.shipment_pickup_date else '',
                'delivery_type': order.delivery_type,
                'salutation': order.salutation,
                'firstName': order.first_name,
                'lastName': order.last_name,
                'birthDate': order.birth_date.strftime('%d.%m.%Y') if order.birth_date else '',
                'street': order.street,
                'streetNumber': order.street_number,
                'postalcode': order.postalcode,
                'city': order.city,
                'country': order.country,
                'phonenumber': order.phone_number,
                'email': order.email_address,
                'comment': order.comment,
                'delFirstName': order.del_first_name,
                'delLastName': order.del_last_name,
                'postofficeDelivery': order.delivery_at_postoffice,
                'delLockerId': order.locker_id,
                'delPostnumber': order.postnumber,
                'delStreet': order.del_street,
                'delStreetNumber': order.del_street_number,
                'delPostalcode': order.del_postalcode,
                'delCity': order.del_city,
                'delCountry': order.del_country,
                'delComment': order.del_comment,
                'orderProducts': order_products_array,
                'healthInsuranceCompany': order.health_insurance_company,
                'healthInsuranceContactPerson': order.health_insurance_contact_person,
                'customerType': order.customer_type,
                'ident_check_images': ident_check_images,
                'identNumber': identification_files.first().id_number if identification_files.first() else '',
                'isPacked': order.is_packed,
            }

            data['orderDetails'] = order_details

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'updateOrder' in request.POST:
            
            order_id = request.POST.get('orderId')
            invoice_data = json.loads(request.POST.get('invoiceData'))
            delivery_data = json.loads(request.POST.get('deliveryData'))
            products = json.loads(request.POST.get('productsData'))
            payment_status = request.POST.get('paymentStatus')
            recipe_status = request.POST.get('recipeStatus')
            order_status = request.POST.get('orderStatus')

            order = Orders.objects.get(id=order_id)

            old_payment_status = order.payment_status
            old_recipe_status = order.recipe_status
            old_status = order.status

            # Check for changes
            changes = []

            # Invoice data
            if order.salutation != invoice_data.get('salutation'):
                changes.append('salutation')
            order.salutation = invoice_data.get('salutation')

            if order.first_name != invoice_data.get('firstName'):
                changes.append('firstName')
            
            order.first_name = invoice_data.get('firstName')

            if order.last_name != invoice_data.get('lastName'):
                changes.append('lastName')
            order.last_name = invoice_data.get('lastName')

            if order.birth_date != datetime.strptime(invoice_data.get('birthDate'), '%d.%m.%Y'):
                changes.append('birthDate')
            order.birth_date = datetime.strptime(invoice_data.get('birthDate'), '%d.%m.%Y')

            if order.delivery_at_postoffice != delivery_data.get('postofficeDelivery'):
                changes.append('postofficeDelivery')
            order.delivery_at_postoffice = delivery_data.get('postofficeDelivery')

            if order.locker_id != delivery_data.get('delLockerId'):
                changes.append('delLockerId')
            order.locker_id = delivery_data.get('delLockerId')

            if order.postnumber != delivery_data.get('delPostnumber'):
                changes.append('delPostnumber')
            order.postnumber = delivery_data.get('delPostnumber')

            if order.street != invoice_data.get('street'):
                changes.append('street')
            order.street = invoice_data.get('street')

            if order.street_number != invoice_data.get('streetNumber'):
                changes.append('streetNumber')
            order.street_number = invoice_data.get('streetNumber')

            if order.postalcode != invoice_data.get('postalcode'):
                changes.append('postalcode')
            order.postalcode = invoice_data.get('postalcode')

            if order.city != invoice_data.get('city'):
                changes.append('city')
            order.city = invoice_data.get('city')

            if order.country != invoice_data.get('country'):
                changes.append('country')
            order.country = invoice_data.get('country')

            if order.phone_number != invoice_data.get('phonenumber'):
                changes.append('phonenumber')
            order.phone_number = invoice_data.get('phonenumber')

            if order.email_address != invoice_data.get('email'):
                changes.append('email')
            order.email_address = invoice_data.get('email')

            if order.comment != invoice_data.get('comment'):
                changes.append('comment')
            order.comment = invoice_data.get('comment')

            # Delivery data
            order.delivery_address_as_invoice = False
            
            if order.del_first_name != delivery_data.get('delFirstName'):
                changes.append('delFirstName')
            order.del_first_name = delivery_data.get('delFirstName')

            if order.del_last_name != delivery_data.get('delLastName'):
                changes.append('delLastName')
            order.del_last_name = delivery_data.get('delLastName')

            if order.del_street != delivery_data.get('delStreet'):
                changes.append('delStreet')
            order.del_street = delivery_data.get('delStreet')

            if order.del_street_number != delivery_data.get('delStreetNumber'):
                changes.append('delStreetNumber')
            order.del_street_number = delivery_data.get('delStreetNumber')

            if order.del_postalcode != delivery_data.get('delPostalcode'):
                changes.append('delPostalcode')
            order.del_postalcode = delivery_data.get('delPostalcode')

            if order.del_city != delivery_data.get('delCity'):
                changes.append('delCity')
            order.del_city = delivery_data.get('delCity')

            if order.del_country != delivery_data.get('delCountry'):
                changes.append('delCountry')
            order.del_country = delivery_data.get('delCountry')

            if order.del_comment != delivery_data.get('delComment'):
                changes.append('delComment')
            order.del_comment = delivery_data.get('delComment')

            # Order status
            if order.payment_status != payment_status:
                changes.append('payment_status')
            order.payment_status = payment_status

            if order.recipe_status != recipe_status:
                changes.append('recipe_status')
            order.recipe_status = recipe_status

            if order.status and order.status != order_status:
                changes.append('order_status')
            order.status = order_status if order_status != 'cancelled' else order.status

            order.save()

            changes_str = ', '.join(str(x) for x in changes)

            # Create log entry
            log_entry = {
                'reference': f'Bestellung { order.number }',
                'message': f'Bestellung aktualisiert. Änderungen: {changes_str}',
                'user': f'({ request.user.id }) { request.user.username }'
            }
            create_log(**log_entry)

            for item in products:

                order_product = OrderProducts.objects.get(id=item.get('orderProductId'))

                order_product.product = Products.objects.get(id=item.get('product'))
                order_product.amount = int(item.get('amount'))
                order_product.prepared = item.get('prepared') if order_product.product.form == 'flower' else False
                order_product.save()

            # Send Mail for status
            check_status_for_mail(order, 'payment_status', old_payment_status, payment_status, request)
            check_status_for_mail(order, 'recipe_status', old_recipe_status, recipe_status, request)
            check_status_for_mail(order, 'status', old_status, order_status, request)

            data['orderDetails'] = get_order_details(order.id)

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'downloadInvoice' in request.POST:

            order_id = request.POST.get('orderId')
            invoice_type = request.POST.get('invoiceType')

            invoice_exists = True

            try:
                invoice = Invoices.objects.get(order__id=order_id, cancellation_invoice=False, canceled=False)

                now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0] = datetime.now().timestamp()

                data['downloadLink'] = reverse('download_invoice', kwargs={'invoice_id':invoice.id, 'invoice_type': invoice_type, 'datetime_now': now})
            except Invoices.DoesNotExist:
                invoice_exists = False

            data['invoiceExists'] = invoice_exists

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'generateDeliveryLabel' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            label_response = {}
            label_response['success'] = False

            if not order.shipment_label_b64_string or order.shipment_label_b64_string == '':

                if order.delivery_type == 'dhl_standard':
                    label_response = dhl_create_label(order_id)

                if order.delivery_type == 'go_express':
                    label_response = go_express_create_label(order_id)

                shipment_label_type = label_response.get('shipment_label_type')
                shipment_label_type_display = label_response.get('shipment_label_type_display')
                shipment_shipment_no = label_response.get('shipment_no')

            else:
                label_response['success'] = True

                shipment_label_type = order.shipment_label_type
                shipment_label_type_display = order.get_shipment_label_type_display()
                shipment_shipment_no = order.shipment_shipment_no

            if label_response['success']:

                now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0] = datetime.now().timestamp()

                data['downloadLink'] = reverse('create_shipping_label', kwargs={'order_id':order_id, 'datetime_now': now})
                data['shipmentLabelType'] = shipment_label_type
                data['shipmentLabelTypeDisplay'] = shipment_label_type_display
                data['shipmentShipmentNo'] = shipment_shipment_no

            data['response'] = label_response

            return HttpResponse(json.dumps(data), content_type='application/json')
        
        # Update Order status
        if 'updateOrderStatus' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            data['order'] = {
                'id': order.id,
                'status': order.status,
                'statusDisplay': order.get_status_display(),
            }

            return HttpResponse(json.dumps(data), content_type='application/json')

        # Delivery labels
        if 'updateDeliveryLabel' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            label_response = {}
            label_response['success'] = False

            if order.shipment_label_type == 'go_express':
                label_response = go_express_update_label(order_id)

            if label_response and label_response['success']:

                now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0] = datetime.now().timestamp()

                data['downloadLink'] = reverse('create_shipping_label', kwargs={'order_id':order_id, 'datetime_now': now})
                data['shipmentShipmentNo'] = label_response.get('shipment_no')

            data['response'] = label_response

            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'updateGOExpressStatus' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            label_response = {}
            label_response['success'] = False

            if order.shipment_label_type == 'go_express':
                label_response = go_express_update_status(order_id)

            data['response'] = label_response

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'cancelDeliveryLabel' in request.POST:

            order_id  = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            if order.status in ['shipped', 'delivered']:
                data['stateError'] = True
                data['message'] = f'Label kann nicht storniert werden, da der Status auf "{ order.get_status_display() }" gesetzt ist.'

                return HttpResponse(json.dumps(data), content_type='application/json')

            label_response = {}
            label_response['success'] = False

            if order.shipment_label_type == 'dhl_standard':
                label_response = dhl_cancel_label(order_id)

            if order.shipment_label_type == 'go_express':
                label_response = go_express_cancel_label(order_id)

            data['response'] = label_response

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'orderPickUp' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            if order.shipment_pickup_order_uuid == '':
                pickup_response = order_shipment_pick_up(order_id)
            else:
                pickup_response = {
                    'success': True,
                    'pickUpDate': order.shipment_pickup_date.strftime('%d.%m.%Y')
                }

            data['response'] = pickup_response

            return HttpResponse(json.dumps(data), content_type='application/json')

        # Invoice
        if 'createNewInvoice' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            invoice = create_new_invoice(order)

            now = str(datetime.now().timestamp()).split('.', maxsplit=1)[0] = datetime.now().timestamp()

            data['downloadLink'] = reverse('download_invoice', kwargs={'invoice_id':invoice.id, 'invoice_type': 'customer', 'datetime_now': now})

            return HttpResponse(json.dumps(data), content_type='application/json')

        # Order Funktions
        if 'updateAllDeliveryStatus' in request.POST:
            
            task_update_delivery_status.delay()

            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'updateDeliveryStatus' in request.POST:

            order_ids = json.loads(request.POST.get('orderIds[]'))

            orders = Orders.objects.filter(id__in=order_ids)
            
            for order in orders:
                if order.shipment_shipment_no and order.shipment_shipment_no != '':

                    if order.shipment_label_type == 'dhl_standard':
                        response = dhl_check_status(order.id)

                    if order.shipment_label_type == 'go_express':
                        response = go_express_check_status(order.id)

                    if 'send_email' in response and response['send_email']:
                        send_order_status_shipped(order)

            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'deleteOrderProduct' in request.POST:
                
            order_product_id = request.POST.get('productId')

            order_product = OrderProducts.objects.get(id=order_product_id)
            order_product.delete()

            data['orderDetails'] = {
                'id': order_product.order.id,
                'orderNumber': order_product.order.number,
                'orderAmount': custom_currency_format(order_product.order.total),
            }

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'checkAvailability' in request.POST:

            data = {
                'errors': {
                    'productsNotFound': []
                },
                'productStatus': [],
                'products': [],
            }

            products = json.loads(request.POST.get('productsData'))

            for product in products:
                try:
                    product_obj = Products.objects.get(name=product['product'])

                    total_stock_amount = StockProducts.objects.filter(product=product_obj, pharmacy=active_pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                    total_booked_amount = OrderProducts.objects.filter(
                        product=product_obj,
                        calculated_in_stock=False,
                        order__ordered=True,
                        order__pharmacy=active_pharmacy,
                    ).aggregate(total=Sum('amount'))['total'] or 0

                    available_amount = 0 if total_stock_amount - total_booked_amount <= 0 else total_stock_amount - total_booked_amount

                    data['products'].append({
                        'name': product_obj.name,
                        'availableAmount': available_amount,
                    })

                except:
                    data['errors']['productsNotFound'].append(product['product'])
                    data['productStatus'].append({
                            'productName': product['product'],
                            'status': 'notFound',
                        })

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'importOrderData' in request.POST:

            data = {
                'errors': {
                    'productsNotFound': []
                },
                'message': '',
                'productStatus': [],
                'productAvailableAmounts': []
            }

            customerData = json.loads(request.POST.get('customerData'))
            products = json.loads(request.POST.get('productsData'))
            recipe_file = request.FILES.get('recipeData')
            external_order_id = customerData['external_order_id']
            online_recipe_status = request.POST.get('onlineRecipeStatus')

            # Check if order already exists
            if Orders.objects.filter(Q(external_id=external_order_id) & Q(status='started')).exists():
                data['message'] = "Bestellung bereits vorhanden."
                

            # Geburtsdatum formatieren
            parsed_birth_date = datetime.strptime(customerData['birth_date'], "%d.%m.%Y")
            formatted_birth_date = parsed_birth_date.strftime("%Y-%m-%d")

            # Versuche, den User zu aktualisieren oder erstelle ihn neu
            user, created = User.objects.update_or_create(
                username=customerData['email_address'],
                defaults={
                    'email': customerData['email_address'],
                    'first_name': customerData['first_name'],
                    'last_name': customerData['last_name'],
                }
            )

            # Versuche, den Customer zu aktualisieren oder erstelle ihn neu
            customer, customer_created = Customers.objects.update_or_create(
                user=user,
                defaults={
                    'can_trigger_order': True,
                    'salutation': customerData['salutation'],
                    'birth_date': parsed_birth_date,
                    'street': customerData['street'],
                    'street_number': customerData['street_number'],
                    'postcode': customerData['postalcode'],
                    'city': customerData['city'],
                    'country': 'DE',
                    'phone': customerData['phone_number'],
                    'customer_type': 'self_payer',
                    'payment_type': 'prepayment',
                    'delivery_type': 'dhl_standard',
                }
            )
            customer.pharmacies.add(staff_user.selected_pharmacy)
            customer.save()

            # Bestellung speichern
            order = Orders.objects.create(created_by=request.user, pharmacy=staff_user.selected_pharmacy)

            order.customer = customer
            order.external_id = external_order_id
            order.birth_date = customer.birth_date
            order.salutation = customer.salutation
            order.first_name = customer.user.first_name
            order.last_name = customer.user.last_name
            order.street = customer.street
            order.street_number = customer.street_number
            order.postalcode = customer.postcode
            order.city = customer.city
            order.state = customer.state
            order.country = customer.country
            order.phone_number = customer.phone

            order.customer_type = 'self_payer'
            order.payment_type = 'prepayment'
            order.delivery_type = 'dhl_standard'
            order.online_recipe_status = online_recipe_status

            # Hochladen des Rezepts
            if recipe_file:
                order_recipe = OrderRecipes.objects.create(order=order, file=recipe_file, e_recipe=True)

            # Produkte speichern
            for product in products:
                try:
                    product_obj = Products.objects.get(name=product['product'])
                    product_price = ProductPrices.objects.get(product=product_obj, pharmacy=staff_user.selected_pharmacy)

                    OrderProducts.objects.create(
                        order=order,
                        product=product_obj,
                        amount=int(product['amount']),
                        prepared=False,
                    )

                    if product_price.status == '0' or product_price.status == '1':
                        data['productStatus'].append({
                            'productName': product_obj.name,
                            'status': product_obj.status,
                        })
                    
                    total_stock_amount = StockProducts.objects.filter(product=product_obj, pharmacy=order.pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                    total_booked_amount = OrderProducts.objects.filter(
                        product=product_obj,
                        calculated_in_stock=False,
                        order__ordered=True,
                        order__pharmacy=order.pharmacy,
                    ).aggregate(total=Sum('amount'))['total'] or 0

                    available_amount = 0 if total_stock_amount - total_booked_amount <= 0 else total_stock_amount - total_booked_amount

                    data['productAvailableAmounts'].append({
                        'productName': product_obj.name,
                        'availableAmount': available_amount,
                    })

                except Products.DoesNotExist:
                    data['errors']['productsNotFound'].append(product['product'])
                    data['productStatus'].append({
                            'productName': product['product'],
                            'status': 'notFound',
                        })                    

            if not data['errors']['productsNotFound'] and not data['productStatus']:
                order.status = 'started'
                order.save()
                data['message'] = "Bestellung erfolgreich gespeichert."

                if not MainSettings.objects.first().test_mode:
                    send_new_order_created(order.id, request)

            else:
                data['message'] = "Bestellung nicht gespeichert. Einige Produkte wurden nicht gefunden."

            if not data['errors']['productsNotFound']:
                del data['errors']

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'saveInternComment' in request.POST:
                
            order_id = request.POST.get('orderId')
            intern_comment = request.POST.get('comment')

            order = Orders.objects.get(id=order_id)
            order.intern_comment = f"{request.user.get_full_name()}: {intern_comment}"
            order.save()

            data['comment'] = order.intern_comment
            
            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'uploadNewRecipe' in request.POST:

            order_id = request.POST.get('orderId')
            recipe_file = request.FILES.get('recipeFile')
            e_recipe = json.loads(request.POST.get('eRecipe'))
            recipe_number = request.POST.get('recipeNumber')

            order = Orders.objects.get(id=order_id)

            try:
                recipe = OrderRecipes.objects.get(order=order)
                recipe.file = recipe_file
                recipe.save()
            except:
                OrderRecipes.objects.create(order=order, number=recipe_number, file=recipe_file, e_recipe=e_recipe)

            old_online_recipe_status = order.online_recipe_status

            order.online_recipe_status == 'checked'
            order.save()

            # Check status change and send maiil
            check_status_for_mail(order, 'online_recipe_status', old_online_recipe_status, 'checked', request)

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'changeCustomerType' in request.POST:

            order_id = request.POST.get('orderId')
            customer_type = request.POST.get('customerType')

            order = Orders.objects.get(id=order_id)
            order.customer_type = customer_type
            order.save()

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'sendOrderCreatedToCustomer' in request.POST:

            order_ids = request.POST.getlist('orderIds[]')

            for order_id in order_ids:
                order = Orders.objects.get(id=order_id)
                send_new_order_created(order.id, request)

            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'getPackOrderData' in request.POST:

            order_id = request.POST.get('orderId')

            active_pharmacy = staff_user.selected_pharmacy
            pharmacy_employees = PharmacyEmployees.objects.filter(pharmacy=active_pharmacy).values('id', 'short_name')
            data['pharmacy_employees'] = list(pharmacy_employees)

            packed_products = get_order_package_data(order_id)

            if 'error' in packed_products:
                return JsonResponse(response, status=404)

            data['packedProducts'] = packed_products
                
            return HttpResponse(json.dumps(data), content_type='application/json')
        
        if 'sendOrderPackageData' in request.POST:

            try:
                
                data = json.loads(request.POST.get('data'))
                packer_id = data.get('packer_id')
                packer_id_2 = data.get('packer_id_2')
                products = data.get('products', [])

                order_id = OrderProducts.objects.get(id=products[0]['ordered_product_id']).order.id
                order = Orders.objects.get(id=order_id)

                # Remove all PackedProducts of order 
                PackedOrderedProducts.objects.filter(order_product__order__id=order_id).delete()
                
                # Process the received data as needed
                for product in products:

                    ordered_product_id = product.get('ordered_product_id')
                    packages = product.get('packages', [])
                    
                    for package in packages:
                        package_id = package.get('package_id')
                        stock_product_id = package.get('product_batch_id')
                        fill_amount_str = package.get('fill_amount')
                        fill_amount = re.search(r'\d+', fill_amount_str)
                        fill_amount = int(fill_amount.group()) if fill_amount else 0

                        order_product = OrderProducts.objects.get(id=ordered_product_id)
                        # package = Packages.objects.get(batch_number=package_id, pharmacy=order.pharmacy)
                        package = Packages.objects.get(id=package_id)
                        # product_batch = StockProducts.objects.get(batch_number=product_batch_id, product=order_product.product, pharmacy=order.pharmacy)
                        stock_product = StockProducts.objects.get(id=stock_product_id)
                        packer = PharmacyEmployees.objects.get(id=packer_id)
                        supervisor = PharmacyEmployees.objects.get(id=packer_id_2)

                        PackedOrderedProducts.objects.create(
                            order_product=order_product,
                            package=package,
                            stock_product=stock_product,
                            fill_amount=fill_amount,
                            packer_name=packer,
                            supervisor_name=supervisor,
                        )

                order.is_packed = True
                order.save()                
                
                # Return a successful response
                return JsonResponse({'status': 'success', 'message': 'Data received'})
            except json.JSONDecodeError:

                create_log(
                    reference='order_functions - sendOrderPackageData',
                    message=f'Invalid JSON - Ordernumber {order.number}',
                    user={ request.user.username },
                )

                return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        if 'downloadProtocol' in request.POST:

            error = []
            
            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            pharmacy = order.pharmacy

            today_str = datetime.now().strftime('%d.%m.%Y')
            in_six_months_str = (datetime.now() + timedelta(days=182)).strftime('%d.%m.%Y')

            # Abführprotokkoll erstellen
            # fill_protocol, created = FillProtocols.objects.get_or_create(order=order)

            # Standard-Herstellungsanweisung der Apotheke            
            standard_protocol_id = StandardFillingProtocolIds.objects.filter(pharmacy=order.pharmacy).order_by('-date').first()
            if standard_protocol_id == None:
                error.append('Keine Standard-Herstellungsanweisung für die Apotheke gefunden.')

            product_data = []
            packer1 = ''
            packer2 = ''

            for product in OrderProducts.objects.filter(order=order):

                fill_protocol, created = FillProtocols.objects.get_or_create(order_product=product, order=product.order)
                
                # Get product packaging data
                packed_products = PackedOrderedProducts.objects.filter(order_product=product)

                package_data = []
                used_packages = []

                for packed_product in packed_products:

                    # Add used packages to list
                    if not any(d['batch_number'] == packed_product.package.batch_number for d in used_packages):
                        used_packages.append({
                            'name': packed_product.package.name,
                            'batch_number': packed_product.package.batch_number,
                            'amount': 1
                        })
                    else:
                        for item in used_packages:
                            if item['batch_number'] == packed_product.package.batch_number:
                                item['amount'] += 1

                    # Get product packaging data
                    package_data.append({
                        'batch_number': packed_product.stock_product.batch_number,
                        'fill_amount': packed_product.fill_amount,
                        'packer': packed_product.packer_name.short_name,
                        'verification_number': packed_product.stock_product.verification_number,
                    })

                    packer1 = packed_product.packer_name.short_name
                    packer2 = packed_product.supervisor_name.short_name

                product_data.append({
                    'name': product.product.name,
                    'amount': product.amount,
                    'package_data': package_data,
                    'used_packages': used_packages,
                    'fill_protocol_id': fill_protocol.id,
                })

            # Liste für HTML-Seiten
            html_pages = []

            for product in product_data:
                context = {
                    'product': product,
                    'standard_filling_protocol': {
                        'id': standard_protocol_id.protocol_id if standard_protocol_id else '---',
                        'date': standard_protocol_id.date.strftime('%d.%m.%Y') if standard_protocol_id else '---',
                    },
                    'pharmacy': {
                        'name': pharmacy.name,
                        'street': pharmacy.street,
                        'street_number': pharmacy.street_number,
                        'postalcode': pharmacy.postalcode,
                        'city': pharmacy.city,
                        'responsible_pharmacist': pharmacy.responsible_pharmacist,
                        'packer1': packer1,
                        'packer2': packer2,
                    },
                    'customer_full_name': order.customer.user.get_full_name(),
                    'today_str': today_str,
                    'in_six_months_str': in_six_months_str,
                    'fill_protocol': product['fill_protocol_id'],
                }

                html_string = render_to_string('../templates/exports/protocol.html', context)
                html_pages.append(html_string)

            # Alle HTML-Seiten zu einem PDF-Dokument zusammenfügen
            full_html = ''
            for html_string in html_pages:
                # Konvertiere das gesamte HTML in PDF mit WeasyPrint
                full_html += html_string

            pdf = HTML(string=full_html).write_pdf()

             # PDF generation
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="Herstellungsprotokoll.pdf"'
            
            return response
        
        if 'downloadLabel' in request.POST:

            error = []
            
            order_id = request.POST.get('orderId')
            order = Orders.objects.get(id=order_id)

            today_str = datetime.now().strftime('%d.%m.%Y')
            in_six_months_str = (datetime.now() + timedelta(days=182)).strftime('%d.%m.%Y')
            pharmacy_data = f"{order.pharmacy.name} / {order.pharmacy.street} {order.pharmacy.street_number}, {order.pharmacy.postalcode} {order.pharmacy.city} / {order.pharmacy.phonenumber}"
            
            font_family_regular = os.path.join(settings.FONTS_DIR, 'Antonio-Bold' + '.ttf')

            standard_context = {
                'customer_name': order.customer.user.get_full_name(),
                'today_str': today_str,
                'in_six_months_str': in_six_months_str,
                'pharmacy': pharmacy_data,
                'font_family_regular': font_family_regular,
            }

            packed_order_products = PackedOrderedProducts.objects.filter(order_product__order=order)

            pisaFileObject.getNamedFile = lambda self: self.uri
            
            html_pages = []
            

            for product in packed_order_products:

                product_short_name = shorten_string(product.order_product.product.name, 35)

                context = {
                    'product': product_short_name,
                    'thc': product.order_product.product.thc_value*100,
                    'cbd': product.order_product.product.max_cbd_value*100,
                    'cultivar': product.order_product.product.cultivar,
                    'fill_amount': product.fill_amount,
                    'unit': 'g' if product.order_product.product.form == 'flower' else 'ml',
                }

                context.update(standard_context)

                html_string = render_to_string('../templates/exports/label_bk.html', context)
                html_pages.append(html_string)


            full_html_string = ''.join(html_pages)
            html = HTML(string=full_html_string)
            response = HttpResponse(content_type='application/pdf')
            # response['Content-Disposition'] = 'inline; filename="label_bk.pdf"'
            html.write_pdf(response)

            return response

        # Review Orders
        if 'deleteOrder' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)
            order.delete()

            data['orderDeleted'] = True

            return HttpResponse(json.dumps(data), content_type='application/json')

    return HttpResponse(json.dumps(data), content_type='application/json')

def products_stock_v1(request):
    """ Function for handling stock management """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:

        create_log(
            reference='products_stock',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':

        
        if 'saveBatchNumber' in request.POST:

            product_id = request.POST.get('productId')
            stock_id = request.POST.get('stockId')
            batch_number = request.POST.get('batchNumber')
            verification_number = request.POST.get('verificationNumber')
            amount = int(float(request.POST.get('amount').replace(',', '.')))
            amount = int(request.POST.get('amount'))
            stock_status = request.POST.get('stockStatus')

            product = Products.objects.get(id=product_id)

            if stock_id == 0 or stock_id == '0':
                stock_product = StockProducts.objects.create(
                    pharmacy=staff_user.selected_pharmacy,
                    product=product,
                    batch_number=batch_number,
                    verification_number=verification_number,
                    amount=amount,
                    status=stock_status,
                )

                data['status'] = 'created'

            else:
                stock_product = StockProducts.objects.get(id=stock_id)
                stock_product.batch_number = batch_number
                stock_product.verification_number = verification_number
                stock_product.amount = amount
                stock_product.status = stock_status
                stock_product.save()

                data['status'] = 'updated'

            create_stock_product_log(
                stock_product=stock_product,
                amount=amount,
                action=data['status'],
                reason=f'Pharmacy: { staff_user.selected_pharmacy } | Batch number: { batch_number } | Verification number: { verification_number } | Amount: { amount } | Status: { stock_status }',
                user=f'({ request.user.id }) { request.user.username }',
            )

        if 'saveThreshold' in request.POST:

            product_id = request.POST.get('productId')
            threshold = request.POST.get('threshold')

            threshold, created = ProductThresholds.objects.update_or_create(
                product_id=product_id,
                pharmacy=staff_user.selected_pharmacy,
                defaults={
                    'threshold': threshold
                }
            )

            stock_products = StockProducts.objects.filter(
                product__id=product_id
            ).values(
                'product__id', 'product__name'
            ).annotate(total_amount=Sum('amount'))

            if created:
                data['status'] = 'created'
            else:
                data['status'] = 'updated'

            data['livestock_amount'] = stock_products[0]['total_amount']

        if 'deleteThreshold' in request.POST:

            product_id = request.POST.get('productId')
            threshold = request.POST.get('threshold')

            if ProductThresholds.objects.filter(product_id=product_id, pharmacy=staff_user.selected_pharmacy).exists():
                ProductThresholds.objects.filter(product_id=product_id, pharmacy=staff_user.selected_pharmacy).delete()

                data['status'] = 'deleted'
            
            else:
                data['status'] = 'notFound'

        if 'getStock' in request.POST:

            product_id = request.POST.get('productId')

            stock_product = StockProducts.objects.get(id=product_id)

            data['productName'] = stock_product.product.name
            data['amount'] = stock_product.amount

        if 'saveStock' in request.POST:

            product_id = request.POST.get('productId')
            amount = request.POST.get('additionalAmount')
            
            stock_product = StockProducts.objects.get(id=product_id)

            if amount != '':

                # Check if amount starts with minus
                if amount[0] == '-':

                    amount = int(amount[1:])

                    if stock_product.amount - amount < 0:
                        stock_product.amount = 0
                    else:
                        stock_product.amount -= amount

                else:
                    amount = int(amount)
                    stock_product.amount += amount

                stock_product.save()

            data['amount_status'] = stock_product.amount_status
            data['status'] = stock_product.status
            data['statusDisplay'] = stock_product.get_status_display()
            data['amount'] = stock_product.amount
            data['enoughAmount'] = sum_product_ordered_amount(stock_product.product, stock_product.pharmacy) <= stock_product.amount

    return HttpResponse(json.dumps(data), content_type='application/json')

def packages_stock_v1(request):
    """ Function for handling stock management """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:

        create_log(
            reference='products_stock',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':

        if 'saveBatchNumber' in request.POST:

            name = request.POST.get('name')
            manufacturer_id = request.POST.get('manufacturerId')
            size = int(request.POST.get('size'))
            batch_number = request.POST.get('batchNumber')
            amount = request.POST.get('amount')

            manufacturer = PackageManufacturers.objects.get(id=manufacturer_id)

            package, created = Packages.objects.update_or_create(
                name=name,
                pharmacy=staff_user.selected_pharmacy,
                batch_number=batch_number,
                size=size,
                manufacturer=manufacturer,
                defaults={
                    'amount': amount,
                }
            )

            if created:
                data['status'] = 'created'
            else:
                data['status'] = 'updated'

            create_package_log(
                package=package,
                amount=amount,
                action=data['status'],
                reason=f'Pharmacy: { staff_user.selected_pharmacy } | Batch number: { batch_number } | Size: { size } | Amount: { amount }',
                user=f'({ request.user.id }) { request.user.username }',
            )

    return HttpResponse(json.dumps(data), content_type='application/json')

def import_functions_v1(request):
    """ Import functions """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:
        create_log(
            reference='import_functions',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':
        
        if 'saveImport' in request.POST:

            category = request.POST.get('category')
            import_file = request.FILES.get('importFile')

            if category == 'terpene':

                import_terpene(import_file, request)

            if category == 'products':

                import_products(import_file, request)

            if category == 'product_prices':

                import_product_prices(import_file, staff_user.selected_pharmacy, request)

        if 'updateProductImages' in request.POST:

            import_product_images()

    return HttpResponse(json.dumps(data), content_type='application/json')

def customer_functions_v1(request):
    """ Customer functions """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:
        create_log(
            reference='customer_functions',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':

        if 'getCustomerDetails' in request.POST:

            customer_id = request.POST.get('customerId')

            customer = Customers.objects.get(id=customer_id)

            data['customer'] = {
                'id': customer.id,
                'salutation': customer.salutation,
                'firstName': customer.user.first_name,
                'lastName': customer.user.last_name,
                'birthDate': customer.birth_date.strftime('%d.%m.%Y'),
                'email': customer.user.email,
                'phonenumber': customer.phone,
                'street': customer.street,
                'streetNumber': customer.street_number,
                'postalcode': customer.postcode,
                'city': customer.city,
                'country': customer.country,
                'customerType': customer.customer_type,
                'paymentType': customer.payment_type,
                'deliveryType': customer.delivery_type,
                'canTriggerOrder': customer.can_trigger_order,
            }

        if 'saveCustomer' in request.POST:

            customer_id = request.POST.get('customerId')
            order_settings = json.loads(request.POST.get('orderSettings'))
            invoice_data = json.loads(request.POST.get('invoiceData'))

            if customer_id:

                customer = Customers.objects.get(id=customer_id)

                user = customer.user
                user.first_name = invoice_data.get('firstName')
                user.last_name = invoice_data.get('lastName')
                user.email = invoice_data.get('email')
                user.username = invoice_data.get('email')
                user.save()
                
            else:

                try:
                    user = User.objects.get(username=invoice_data.get('email'))
                    customer = Customers.objects.get(user=user)

                    user = customer.user
                    user.first_name = invoice_data.get('firstName')
                    user.last_name = invoice_data.get('lastName')
                    user.save()

                except User.DoesNotExist:

                    user = User.objects.create_user(
                        username=invoice_data.get('email'),
                        email=invoice_data.get('email'),
                        first_name=invoice_data.get('firstName'),
                        last_name=invoice_data.get('lastName')
                    )

                    customer = Customers.objects.create(user=user)
                    
                    customer.can_trigger_order = True

            customer.pharmacies.add(staff_user.selected_pharmacy)
            customer.customer_type = order_settings.get('customerType')
            customer.payment_type = order_settings.get('paymentType')
            customer.delivery_type = order_settings.get('deliveryType')

            customer.salutation = invoice_data.get('salutation')
            customer.birth_date = datetime.strptime(invoice_data.get('birthDate'), '%d.%m.%Y')
            customer.phone = invoice_data.get('phonenumber')
            customer.street = invoice_data.get('street')
            customer.street_number = invoice_data.get('streetNumber')
            customer.postcode = invoice_data.get('postalcode')
            customer.city = invoice_data.get('city')
            customer.country = invoice_data.get('country')

            customer.save()

        if 'createOrder' in request.POST:

            customer = Customers.objects.get(id=request.POST.get('customerId'))
            
            data['premission'] = customer.can_trigger_order

            if customer.can_trigger_order:

                order = Orders.objects.create(customer=customer, created_by=request.user, pharmacy=staff_user.selected_pharmacy)
                
                data['orderId'] = order.id

                data['customer'] = {
                    'id': customer.id,
                    'salutation': customer.salutation,
                    'firstName': customer.user.first_name,
                    'lastName': customer.user.last_name,
                    'birthDate': customer.birth_date.strftime('%d.%m.%Y'),
                    'email': customer.user.email,
                    'phone': customer.phone,
                    'street': customer.street,
                    'streetNumber': customer.street_number,
                    'postcode': customer.postcode,
                    'city': customer.city,
                    'country': customer.country,
                    'customerType': customer.customer_type,
                    'paymentType': customer.payment_type,
                    'deliveryType': customer.delivery_type,
                }

        if 'uploadRecipeFile' in request.POST:

            order_id = request.POST.get('orderId')
            recipe_file = request.FILES.get('recipeFile')
            recipe_number = request.POST.get('recipeNumber')
            e_recipe = json.loads(request.POST.get('eRecipe'))

            # Hochladen des Rezepts
            if recipe_file:

                order = Orders.objects.get(id=order_id)
                order_recipe = OrderRecipes.objects.create(order=order, file=recipe_file, number=recipe_number, e_recipe=e_recipe)

                data['recipeId'] = order_recipe.id
                data['recipeNumber'] = order_recipe.number
                data['recipeName'] = os.path.basename(order_recipe.file.name)
                data['recipeUrl'] = order_recipe.file.url

        if 'addProduct' in request.POST:

            order_id = request.POST.get('orderId')
            order = Orders.objects.get(id=order_id)
            recipe_files = OrderRecipes.objects.filter(order=order)

            product_exist = True

            product = Products.objects.get(id=request.POST.get('productId'))

            #Verfügbare Menge berechnen
            total_stock_amount = StockProducts.objects.filter(product=product, pharmacy=order.pharmacy).aggregate(total=Sum('amount'))['total'] or 0
            total_booked_amount = sum_product_ordered_amount(product, order.pharmacy)

            available_amount = 0 if total_stock_amount - total_booked_amount < 0 else total_stock_amount - total_booked_amount

            add_product_response = add_product_to_cart(order, request.POST.get('productId'), 1, False, True)

            if not add_product_response['object_not_exist']:

                data['product'] = add_product_to_cart(order, request.POST.get('productId'), 1, False, True)
                data['recipeFiles'] = [{'id': recipe.id, 'number': recipe.number} for recipe in recipe_files]
                data['products'] = [{
                    'id': product.id,
                    'name': product.name,
                    'genetic': product.genetics.name if product.genetics else 'Unbekannt',
                    'thc': round(product.thc_value, 2),
                } for product in Products.objects.all().order_by('name')]
                data['preparedChoices'] = [{'value': False, 'name': 'unverändert'}, {'value': True, 'name': 'Zerkleinert'}]
                data['available_amount'] = available_amount

            else:
                product_exist = False

            data['productExist'] = product_exist
            data['total'] = custom_currency_format(order.total)

        if 'deleteOrderProduct' in request.POST:
                
            order_product_id = request.POST.get('productId')

            try:
                order_product = OrderProducts.objects.get(id=order_product_id)
                order_product.delete()

                data['total'] = custom_currency_format(order_product.order.total)

            except OrderProducts.DoesNotExist:
                pass

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'changeProductDetails' in request.POST:

            order_product_id = request.POST.get('orderProductId')
            amount = int(request.POST.get('amount'))
            prepared = request.POST.get('prepared')
            # recipe_id = request.POST.get('recipeId')

            try:
                order_product = OrderProducts.objects.get(id=order_product_id)

                # if recipe_id:
                #     order_recipe = OrderRecipes.objects.get(id=recipe_id)
                #     order_product.recipe_file = order_recipe

                order_product.amount = amount
                order_product.prepared = prepared == '1'
                order_product.save()

                #Verfügbare Menge berechnen
                total_stock_amount = StockProducts.objects.filter(product=order_product.product, pharmacy=order_product.order.pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                total_booked_amount = OrderProducts.objects.filter(
                    product=order_product.product,
                    calculated_in_stock=False,
                    order__ordered=True,
                    order__pharmacy=order_product.order.pharmacy,
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                available_amount = 0 if total_stock_amount - total_booked_amount < 0 else total_stock_amount - total_booked_amount

                data['available_amount'] = available_amount
                data['product_total'] = custom_currency_format(order_product.total)
                data['total'] = custom_currency_format(order_product.order.total)

            except OrderProducts.DoesNotExist:
                pass

        if 'saveOrder' in request.POST:

            order_id = request.POST.get('orderId')
            order_settings = json.loads(request.POST.get('orderSettings'))
            invoice_data = json.loads(request.POST.get('invoiceData'))
            deliver_data = json.loads(request.POST.get('deliverData'))

            order = Orders.objects.get(id=order_id)

            order.delivery_type = order_settings.get('deliveryType')
            order.payment_type = order_settings.get('paymentType')
            order.customer_type = order_settings.get('customerType')
            order.recipe_status = order_settings.get('recipeStatus')

            if order.recipe_status in ['received', 'checked']:
                order.online_recipe_status = 'checked'

            # Invoicedatas
            order.salutation = invoice_data.get('salutation')
            order.first_name = invoice_data.get('firstName')
            order.last_name = invoice_data.get('lastName')
            order.birth_date = datetime.strptime(invoice_data.get('birthDate'), '%d.%m.%Y')
            order.street = invoice_data.get('street')
            order.street_number = invoice_data.get('streetNumber')
            order.postalcode = invoice_data.get('postalcode')
            order.city = invoice_data.get('city')
            order.country = invoice_data.get('country')
            order.comment = invoice_data.get('comment') if invoice_data.get('comment') else ''
            order.phone_number = invoice_data.get('phonenumber')
            order.email_address = invoice_data.get('email')

            # Deliveryadress
            order.del_first_name = deliver_data.get('delFirstName')
            order.del_last_name = deliver_data.get('delLastName')
            order.del_street = deliver_data.get('delStreet')
            order.del_street_number = deliver_data.get('delStreetNumber')
            order.del_postalcode = deliver_data.get('delPostalcode')
            order.del_city = deliver_data.get('delCity')
            order.del_country = deliver_data.get('delCountry')
            order.del_comment = deliver_data.get('delComment') if deliver_data.get('delComment') else ''

            # Order created_by
            order.created_by = request.user

            # Order status
            order.status = 'started'
            order.save()

            send_new_order_created(order.id, request)

        if 'activateForOrder' in request.POST:

            customer_id = request.POST.get('customerId')
            customer = Customers.objects.get(id=customer_id)

            customer.can_trigger_order = True
            customer.save()

    return HttpResponse(json.dumps(data), content_type='application/json')

def staff_user_functions_v1(request):
    """ Staff user functions """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:
        create_log(
            reference='staff_user_functions',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':


        if 'createUser' in request.POST:

            email = request.POST.get('email')
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')

            try:
                user = User.objects.get(username=email)
                data['userExist'] = True

            except User.DoesNotExist:

                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,
                    is_active=False
                )
                data['userExist'] = False

                send_activate_staff_user(user, request)

        if 'getUserRights' in request.POST:

            user_id = request.POST.get('userId')

            user = User.objects.get(id=user_id)
            user_premissions = UserPremissions.objects.filter(user=user)
            
            user_rights = {}

            pharmacies = Pharmacies.objects.all()

            for pharmacy in pharmacies:

                if not pharmacy.id in user_rights:
                    user_rights[pharmacy.id] = {}

                    for user_premission in user_premissions.filter(pharmacy=pharmacy):

                        user_rights[pharmacy.id][user_premission.view] = {
                            'read': user_premission.read_premission,
                            'write': user_premission.write_premission,
                        }

            data['userRights'] = user_rights
        
        if 'saveUserRights' in request.POST:

            user_id = request.POST.get('userId')
            user_rights = json.loads(request.POST.get('userRights'))

            user = User.objects.get(id=user_id)

            # Delete all user rights
            for user_premission in UserPremissions.objects.filter(user=user):
                # Check if not user_premission pharmacy is in user_rights
                if not user_premission.pharmacy.id in user_rights:
                    user_premission.delete()

            # Create user rights
            for pharmacy_id, pharmacy_rights in user_rights.items():

                pharmacy = Pharmacies.objects.get(id=pharmacy_id)

                for view, rights in pharmacy_rights.items():

                    user_premission, created = UserPremissions.objects.get_or_create(user=user, pharmacy=pharmacy, view=view)

                    user_premission.read_premission = rights.get('read')
                    user_premission.write_premission = rights.get('write')

                    user_premission.save()

            user_rights_array = []

            data['userRights'] = user_rights_array

    return HttpResponse(json.dumps(data), content_type='application/json')

def email_recipient_functions_v1(request):
    """ E-Mail Emfänger Funktionen für das Dashboard """

    data = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except StaffUser.DoesNotExist:
        create_log(
            reference='staff_user_functions',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

    if request.method == 'POST':

        if 'createRecipient' in request.POST:

            pharmacy_id = request.POST.get('pharmacyId')
            category = request.POST.get('category')
            email = request.POST.get('email')
            name = request.POST.get('name')

            pharmacy = Pharmacies.objects.get(id=pharmacy_id)

            recipient, created = EmailRecipients.objects.get_or_create(pharmacy=pharmacy, category=category, email=email, defaults={'name': name})

            data['recipientExist'] = not created
            data['recipient'] = {
                'id': recipient.id,
                'pharmacy': recipient.pharmacy.name,
                'category': recipient.category,
                'email': recipient.email,
                'name': recipient.name,
            }

        if 'deleteRecipient' in request.POST:

            recipient_ids = json.loads(request.POST.get('recipientIds[]'))

            EmailRecipients.objects.filter(id__in=recipient_ids).delete()

    return HttpResponse(json.dumps(data), content_type='application/json')

def user_order_functions_v1(request):
    """ User order functions """

    data = {}

    if not request.user:
        return HttpResponse(json.dumps({'error': 'No user'}), content_type='application/json')
    
    if request.method == 'POST':

        if 'getOrderDetails' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)
            order_products = OrderProducts.objects.filter(order=order)
            order_recipes = OrderRecipes.objects.filter(order=order)
            order_insurance_confirmations = OrderInsuranceConfirmation.objects.filter(order=order)

            identification_files = IdentificationFiles.objects.filter(order=order)

            ident_check_images = []
            for item in identification_files:
                ident_check_images.append(
                    {
                        'id': item.id,
                        'id_number': item.id_number,
                        'file': item.file.url if item.file else ''
                    }
                )

            order_products_array = []
            for order_product in order_products:

                total_stock_amount = StockProducts.objects.filter(product=order_product.product, pharmacy=order_product.order.pharmacy).aggregate(total=Sum('amount'))['total'] or 0
                total_booked_amount = OrderProducts.objects.filter(
                    product=order_product.product,
                    calculated_in_stock=False,
                    order__ordered=True,
                    order__pharmacy=order_product.order.pharmacy,
                ).aggregate(total=Sum('amount'))['total'] or 0

                available_amount = 0 if total_stock_amount - total_booked_amount <= 0 else total_stock_amount - total_booked_amount

                amount_label = 'Menge (g)' if order_product.product.form == 'flower' else 'Anzahl'
                amount_label = amount_label + f' (Verfügbar: {available_amount})'

                order_products_array.append({
                    'id': order_product.id,
                    'productId': order_product.product.id,
                    'name': order_product.product.name,
                    'amount': order_product.amount,
                    'amountLabel': amount_label,
                    'prepared': order_product.prepared,
                    'supplier': order_product.product.supplier.name,
                    'form': order_product.product.get_form_display(),
                    'total': custom_currency_format(order_product.total),
                    'products': [{'id': item.product.id, 'name': item.product.name, 'thc': f'{round(item.product.thc_value * 100)} %', 'genetic': item.product.genetics.name if item.product.genetics else ''} for item in ProductPrices.objects.filter(active=True, pharmacy=order.pharmacy).order_by('product__name')],
                    'preparedChoices': [{'value': False, 'name': 'unverändert'}, {'value': True, 'name': 'Zerkleinert'}],
                    'thc': f"{round(order_product.product.thc_value * 100, 2)}%",
                    'genetic': order_product.product.genetics.name if order_product.product.genetics else '',
                    'isEnoughAvailable': True if available_amount >= order_product.amount else False,
                })

            delivery_button_status = False
            if order.is_packed:
                if order.payment_type == 'payment_by_invoice' and order.recipe_status == 'checked':
                    delivery_button_status = True
                elif order.payment_status == 'received' and order.recipe_status == 'checked':
                    delivery_button_status = True

            recipe_files = []
            for recipe_file in order_recipes:
                recipe_files.append({
                    'id': recipe_file.id,
                    'number': recipe_file.number,
                    'url': recipe_file.file.url,
                })

            order_details = {
                'id': order.id,
                'orderNumber': order.number,
                'orderDate': order.order_time.strftime('%d.%m.%Y | %H:%M Uhr'),
                'orderAmount': custom_currency_format(order.total),
                'recipeFiles': recipe_files,
                'insuranceConfirmation': order_insurance_confirmations.first().file.name if order_insurance_confirmations else False,
                'insuranceConfirmationURL': order_insurance_confirmations.first().file.url if order_insurance_confirmations else False,
                'paymentType': order.payment_type,
                'paymentStatus': order.payment_status,
                'recipeStatus': order.recipe_status,
                'orderStatus': order.status,
                'deliveryButtonStatus': delivery_button_status,
                'shipmentLabelType': order.get_shipment_label_type_display() if order.shipment_label_type else '',
                'shipmentShipmentNo': order.shipment_shipment_no,
                'pickUpButtonStatus': True if order.shipment_shipment_no and order.shipment_shipment_no != '' else False,
                'pickUpStatus': True if order.shipment_pickup_order_uuid and order.shipment_pickup_order_uuid != '' else False,
                'pickUpDate': order.shipment_pickup_date.strftime('%d.%m.%Y') if order.shipment_pickup_date else '',
                'deliveryType': order.delivery_type,
                'salutation': order.salutation,
                'firstName': order.first_name,
                'lastName': order.last_name,
                'birthDate': order.birth_date.strftime('%d.%m.%Y') if order.birth_date else '',
                'street': order.street,
                'streetNumber': order.street_number,
                'postalcode': order.postalcode,
                'city': order.city,
                'country': order.country,
                'phonenumber': order.phone_number,
                'email': order.email_address,
                'comment': order.comment,
                'delFirstName': order.del_first_name,
                'delLastName': order.del_last_name,
                'delStreet': order.del_street,
                'delStreetNumber': order.del_street_number,
                'delPostalcode': order.del_postalcode,
                'delCity': order.del_city,
                'delCountry': order.del_country,
                'delComment': order.del_comment,
                'orderProducts': order_products_array,
                'healthInsuranceCompany': order.health_insurance_company,
                'healthInsuranceContactPerson': order.health_insurance_contact_person,
                'customerType': order.customer_type,
                'ident_check_images': ident_check_images,
                'identNumber': identification_files.first().id_number if identification_files.first() else '',
                'isPacked': order.is_packed,
            }

            data['orderDetails'] = order_details

        if 'saveInvoiceDatas' in request.POST:

            order_id = request.POST.get('orderId')
            invoice_data = json.loads(request.POST.get('invoiceData'))

            order = Orders.objects.get(id=order_id)

            order.first_name = invoice_data.get('firstName')
            order.last_name = invoice_data.get('lastName')
            order.email_address = invoice_data.get('email')
            order.phone_number = invoice_data.get('phonenumber')
            order.street = invoice_data.get('street')
            order.street_number = invoice_data.get('streetNumber')
            order.postalcode = invoice_data.get('postalcode')
            order.city = invoice_data.get('city')
            order.country = invoice_data.get('country')
            order.comment = invoice_data.get('comment')

            order.save()

        if 'saveDeliveryDatas' in request.POST:

            order_id = request.POST.get('orderId')
            deliver_data = json.loads(request.POST.get('deliveryData'))

            order = Orders.objects.get(id=order_id)

            order.delivery_type = deliver_data.get('deliveryType')
            order.del_first_name = deliver_data.get('delFirstName')
            order.del_last_name = deliver_data.get('delLastName')
            order.del_street = deliver_data.get('delStreet')
            order.del_street_number = deliver_data.get('delStreetNumber')
            order.del_postalcode = deliver_data.get('delPostalcode')
            order.del_city = deliver_data.get('delCity')
            order.del_country = deliver_data.get('delCountry')
            order.del_comment = deliver_data.get('delComment')

            order.save()

            data['deliveryType'] = order.get_delivery_type_display()

        if 'savePaymentMethod' in request.POST:

            order_id = request.POST.get('orderId')
            payment_type = request.POST.get('paymentType')

            order = Orders.objects.get(id=order_id)

            order.payment_type = payment_type

            order.save()

            data['paymentType'] = order.get_payment_type_display()

        if 'saveOrder' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            create_log(
                reference='order',
                message=f'Order { order.id } confirmed',
                user=f'({ request.user.id }) { request.user.username }',
                category='info',
            )

            order.status = 'ordered'
            order.ordered = True
            order.save()

        if 'deleteOrder' in request.POST:

            order_id = request.POST.get('orderId')

            order = Orders.objects.get(id=order_id)

            order.status = 'acceptance_refused'
            order.save()

            data['orderDeleted'] = True

        return HttpResponse(json.dumps(data), content_type='application/json')

#pylint: disable=unused-argument
def download_invoice_v1(request, invoice_id, invoice_type, datetime_now):
    """ Download invoice """
    response = None

    if invoice_type == 'customer':

        invoice = Invoices.objects.get(id=invoice_id)

        is_staff = request.user.is_staff or request.user.is_superuser

        if request.user != invoice.order.customer and not is_staff:
            return redirect('home')

        response = generate_invoice_customer(invoice_id, 'http')

    if invoice_type == 'insurance':
        response = generate_invoice_insurance(invoice_id)

    return response

#pylint: disable=unused-argument
def download_order_products_v1(request, datetime_now):
    """ Download order products """

    ids = list(OrderProducts.objects.filter(order__ordered=True).values_list('id', flat=True))

    response = export_order_products(ids)

    return response

#pylint: disable=unused-argument
def create_shipping_label_v1(request, order_id, datetime_now):
    """ Create shipping label response """

    order = Orders.objects.get(id=order_id)

    # Dekodieren des base64-Strings
    pdf_bytes = base64.b64decode(order.shipment_label_b64_string)

    # Erstellen eines BytesIO-Objekts aus den dekodierten Daten
    pdf_io = BytesIO(pdf_bytes)

    # Erstellen einer FileResponse, um die PDF-Datei zurückzugeben
    response = FileResponse(pdf_io, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="DHL_Label_' + order.number + '.pdf"'

    return response

