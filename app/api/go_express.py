""" GO Express API """

import requests, json
from datetime import datetime, timedelta
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from ..models import MainSettings, Orders, Logger, PackagePickupTimes

def go_express_create_label(order_id):
    """ Create go express label """

    response = None

    main_settings = MainSettings.objects.first()

    username = main_settings.go_express_username
    password = main_settings.go_express_password

    base_url = main_settings.go_express_base_url_test if main_settings.test_mode else main_settings.go_express_base_url_prod
    pickup_url = base_url + "/external/ci/order/api/v1/createOrder"

    order = Orders.objects.get(id=order_id)

    # Define pickup date
    # If current time is after 17:00, pickup date is tomorrow """
    if timezone.now().time() > timezone.make_aware(datetime.strptime('17:00', '%H:%M')).time():
        pickup_date = timezone.now().date() + timedelta(days=1)
    else:
        pickup_date = timezone.now().date()

    # If order value is under 250 and current day is friday, pickup date is monday
    if order.subtotal_brutto < 250 and pickup_date.weekday() == 4:
        pickup_date = pickup_date + timedelta(days=3)

    # If current day is saturday, pickup date is monday
    if pickup_date.weekday() == 5:
        pickup_date = pickup_date + timedelta(days=2)

    # Create pickupTimes
    weekday = pickup_date.weekday()
    pickup_times = PackagePickupTimes.objects.filter(day=str(weekday), pharmacy=order.pharmacy).first()

    payload = {
        "responsibleStation": main_settings.go_express_responsible_station,
        "customerId": main_settings.go_express_customer_id,
        "shipment": {
            "hwbNumber": "",
            "orderStatus": "Released",
            "validation": "",
            "service": "ON",
            "weight": "0.5",
            "content": "",
            "customerReference": f"{ order.number }",
            "selfPickup": "",
            "selfDelivery": "",
            "dimensions": "",
            "packageCount": "1",
            "identCheck": "Yes",
            "freightCollect": "",
            "receiptNotice": "",
            "isNeutralPickup": "",
            "pickup": {
                "date": f"{ pickup_date.strftime('%d.%m.%Y') }",
                "timeFrom": "17:00" if not pickup_times else pickup_times.from_time.strftime('%H:%M'),
                "timeTill": "19:00" if not pickup_times else pickup_times.to_time.strftime('%H:%M')
            },
            "delivery": {
                "date": "",
                "avisFrom": "",
                "avisTill": "",
                "timeFrom": "",
                "timeTill": "",
                "weekendOrHolidayIndicator": ""
            },
            "insurance": {
                "amount": "",
                "currency": ""
            },
            "valueOfGoods": {
                "amount": "",
                "currency": ""
            },
            "cashOnDelivery": {
                "amount": "",
                "currency": ""
            }
        },
        "consignorAddress": {
            "name1": f"{ order.pharmacy.name}",
            "name2": "",
            "name3": "",
            "street": f"{ order.pharmacy.street }",
            "houseNumber": f"{ order.pharmacy.street_number }",
            "zipCode": f"{ order.pharmacy.postalcode }",
            "city": f"{ order.pharmacy.city }",
            "country": "DE",
            "phoneNumber": f"{ order.pharmacy.phonenumber }",
		    "remarks": "",
            "email": f"{ order.pharmacy.email }"
        },
        "neutralAddress": {
            "name1": "",
            "name2": "",
            "name3": "",
            "street": "",
            "houseNumber": "",
            "zipCode": "",
            "city": "",
            "country": ""
        },
        "consigneeAddress": {
            "name1": f"{ order.del_first_name } { order.del_last_name }",
            "name2": "",
            "name3": "",
            "street": f"{ order.del_street }",
            "houseNumber": f"{ order.del_street_number }",
            "zipCode": f"{ order.del_postalcode }",
            "city": f"{ order.del_city }",
            "country": "DE",
            "phoneNumber": "",
            "remarks": "",
            "email": ""
        },
        "label": "2",
        "packages": [
            {
                "length": "",
                "width": "",
                "height": ""
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "higreen-apotheke.de/1.0"
    }

    response = requests.post(pickup_url, auth=HTTPBasicAuth(username=username, password=password), json=payload, headers=headers)
    
    if response.status_code == 200:

        Logger.objects.create(
            category='info',
            reference='GO! Express (Creation)',
            message=str(response.text),
        )

        parsed_data = json.loads(response.text)

        order.shipment_shipment_no = parsed_data['hwbNumber']
        order.shipment_ref_no = parsed_data['hwbNumber']
        order.shipment_label_b64_string = parsed_data['hwbOrPackageLabel']
        order.shipment_label_type = order.delivery_type

        if order.status not in ['shipped', 'delivered', 'cancelled']:
            order.status = 'ready_to_ship'

        order.save()

        response = {
            'success': True,
            'code': str(response.status_code),
            'shipment_label_type': order.shipment_label_type,
            'shipment_label_type_display': order.get_shipment_label_type_display(),
            'shipment_no': order.shipment_shipment_no,
        }

    else:

        Logger.objects.create(
            category='warning',
            reference='GO! Express (Creation)',
            message=str(response.text),
        )

        response = {
            'success': False,
            'code': str(response.status_code),
        }

    return response

def go_express_update_label(order_id):
    """ Update go express label """

    response = None

    main_settings = MainSettings.objects.first()

    username = main_settings.go_express_username
    password = main_settings.go_express_password

    base_url = main_settings.go_express_base_url_test if main_settings.test_mode else main_settings.go_express_base_url_prod
    pickup_url = base_url + "/external/ci/order/api/v1/createOrder"

    order = Orders.objects.get(id=order_id)

    # Define pickup date
    # If current time is after 17:00, pickup date is tomorrow """
    if timezone.now().time() > timezone.make_aware(datetime.strptime('17:00', '%H:%M')).time():
        pickup_date = timezone.now().date() + timedelta(days=1)
    else:
        pickup_date = timezone.now().date()

    # If order value is under 250 and current day is friday, pickup date is monday
    if order.subtotal_brutto < 250 and pickup_date.weekday() == 4:
        pickup_date = pickup_date + timedelta(days=3)

    # If current day is saturday, pickup date is monday
    if pickup_date.weekday() == 5:
        pickup_date = pickup_date + timedelta(days=2)

    if order.shipment_label_type != 'go_express' or order.shipment_shipment_no == '':
        return False

    payload = {
        "responsibleStation": main_settings.go_express_responsible_station,
        "customerId": main_settings.go_express_customer_id,
        "shipment": {
            "hwbNumber": f"{ order.shipment_shipment_no }",
            "orderStatus": "Released",
            "validation": "",
            "service": "ON",
            "weight": "0.5",
            "content": "",
            "customerReference": f"{ order.number }",
            "selfPickup": "",
            "selfDelivery": "",
            "dimensions": "",
            "packageCount": "1",
            "identCheck": "Yes",
            "freightCollect": "",
            "receiptNotice": "",
            "isNeutralPickup": "",
            "pickup": {
                "date": f"{ pickup_date.strftime('%d.%m.%Y') }",
                "timeFrom": "17:00",
                "timeTill": "19:00"
            },
            "delivery": {
                "date": "",
                "avisFrom": "",
                "avisTill": "",
                "timeFrom": "",
                "timeTill": "",
                "weekendOrHolidayIndicator": ""
            },
            "insurance": {
                "amount": "",
                "currency": ""
            },
            "valueOfGoods": {
                "amount": "",
                "currency": ""
            },
            "cashOnDelivery": {
                "amount": "",
                "currency": ""
            }
        },
        "consignorAddress": {
            "name1": f"{ order.pharmacy.name}",
            "name2": "",
            "name3": "",
            "street": f"{ order.pharmacy.street }",
            "houseNumber": f"{ order.pharmacy.street_number }",
            "zipCode": f"{ order.pharmacy.postalcode }",
            "city": f"{ order.pharmacy.city }",
            "country": "DE",
            "phoneNumber": f"{ order.pharmacy.phonenumber }",
            "remarks": "",
            "email": f"{ order.pharmacy.email }"
        },
        "neutralAddress": {
            "name1": "",
            "name2": "",
            "name3": "",
            "street": "",
            "houseNumber": "",
            "zipCode": "",
            "city": "",
            "country": ""
        },
        "consigneeAddress": {
            "name1": f"{ order.del_first_name } { order.del_last_name }",
            "name2": "",
            "name3": "",
            "street": f"{ order.del_street }",
            "houseNumber": f"{ order.del_street_number }",
            "zipCode": f"{ order.del_postalcode }",
            "city": f"{ order.del_city }",
            "country": "DE",
            "phoneNumber": "",
            "remarks": "",
            "email": f"{ order.email_address }"
        },
        "label": "2",
        "packages": [
            {
                "length": "",
                "width": "",
                "height": ""
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "higreen-apotheke.de/1.0"
    }

    response = requests.post(pickup_url, auth=HTTPBasicAuth(username=username, password=password), json=payload, headers=headers)

    if response.status_code == 200:

        Logger.objects.create(
            category='info',
            reference=f'GO! Express (Update) - Order: { order.number }',
            message=str(response.text),
        )

        parsed_data = json.loads(response.text)

        order.shipment_label_b64_string = parsed_data['hwbOrPackageLabel']

        order.save()

        response = {
            'success': True,
            'code': str(response.status_code),
            'shipment_label_type': order.shipment_label_type,
            'shipment_label_type_display': order.get_shipment_label_type_display(),
            'shipment_no': order.shipment_shipment_no,
        }

    else:

        Logger.objects.create(
            category='warning',
            reference=f'GO! Express (Update) - Order: { order.number }',
            message=str(response.text),
        )

        response = {
            'success': False,
            'code': str(response.status_code),
        }

    return response

def go_express_update_status(order_id):
    """ Update go express label status to Released """

    response = None

    main_settings = MainSettings.objects.first()

    username = main_settings.go_express_username
    password = main_settings.go_express_password

    base_url = main_settings.go_express_base_url_test if main_settings.test_mode else main_settings.go_express_base_url_prod
    pickup_url = base_url + "/external/ci/order/api/v1/updateOrderStatus"

    order = Orders.objects.get(id=order_id)

    payload = {
        "responsibleStation": main_settings.go_express_responsible_station,
        "customerId": main_settings.go_express_customer_id,
        "orderStatus": "Released",
        "hwbNumber": f"{ order.shipment_shipment_no }",
        "label": "2",
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "higreen-apotheke.de/1.0"
    }

    response = requests.post(pickup_url, auth=HTTPBasicAuth(username=username, password=password), json=payload, headers=headers)

    if response.status_code == 200:

        Logger.objects.create(
            category='info',
            reference=f'GO! Express (Status Update) - Order: { order.number }',
            message=str(response.text),
        )

        parsed_data = json.loads(response.text)

        order.shipment_label_b64_string = parsed_data['hwbOrPackageLabel']
        order.save()

        response = {
            'success': True,
            'code': str(response.status_code),
            'shipment_label_type': order.shipment_label_type,
            'shipment_label_type_display': order.get_shipment_label_type_display(),
            'shipment_no': order.shipment_shipment_no,
        }

    else:

        Logger.objects.create(
            category='warning',
            reference=f'GO! Express (Status Update) - Order: { order.number }',
            message=str(response.text),
        )

        response = {
            'success': False,
            'code': str(response.status_code),
        }

    return response

def go_express_cancel_label(order_id):
    """ Cancel go express label """

    response = None

    main_settings = MainSettings.objects.first()

    username = main_settings.go_express_username
    password = main_settings.go_express_password

    base_url = main_settings.go_express_base_url_test if main_settings.test_mode else main_settings.go_express_base_url_prod
    pickup_url = base_url + "/external/ci/order/api/v1/updateOrderStatus"

    order = Orders.objects.get(id=order_id)

    payload = {
        "responsibleStation": main_settings.go_express_responsible_station,
        "customerId": main_settings.go_express_customer_id,
        "orderStatus": "Cancelled",
        "hwbNumber": order.shipment_shipment_no,
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "higreen-apotheke.de/1.0"
    }

    response = requests.post(pickup_url, auth=HTTPBasicAuth(username=username, password=password), json=payload, headers=headers)

    if response.status_code == 200:

        parsed_data = json.loads(response.text)

        order.shipment_label_b64_string = ''
        order.shipment_label_type = ''
        order.shipment_shipment_no = ''
        order.shipment_ref_no = ''
        order.status = 'process'
        order.save()

        response = {
            'success': True,
            'code': str(response.status_code),
        }

    else:

        response = {
            'success': False,
            'code': str(response.status_code),
        }

    return response

def go_express_check_status(order_id):
    """ Check go express label status """

    response = None

    main_settings = MainSettings.objects.first()

    username = main_settings.go_express_track_username
    password = main_settings.go_express_track_password

    base_url = main_settings.go_express_base_url_test if main_settings.test_mode else main_settings.go_express_base_url_prod
    pickup_url = base_url + "/external/api/v1/status"

    order = Orders.objects.get(id=order_id)

    # Check if order has go express label
    if order.shipment_label_type != 'go_express' or order.shipment_shipment_no == '':
        return False

    # Define get parameters
    params = {
        "hwbNumber": order.shipment_shipment_no,
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "higreen-apotheke.de/1.0"
    }
    
    # Create get request
    response = requests.get(pickup_url, auth=HTTPBasicAuth(username=username, password=password), params=params, headers=headers)

    if response.status_code == 200:

        parsed_data = json.loads(response.text)

        current_status = parsed_data['trackingItems']['trackingTable'][0]["statusCode"]

        intern_shipping_status = {
            "GO10": "shipped",
            "GO20": "shipped",
            "GO30": "shipped",
            "GO40": "shipped",
            "GO42": "shipped",
            "GO50": "shipped",
            "GO52": "shipped",
            "GOY011": "delivered",
            "GO90": "delivered",
            "GOY005": "delivery_not_possible",
            "GOY008": "delivery_not_possible",
        }

        send_mail = False

        if current_status in intern_shipping_status:

            send_mail = order.status not in ['shipped', 'delivered']

            order.status = intern_shipping_status[current_status]
            order.save()

        response = {
            'success': True,
            'code': str(response.status_code),
            'current_status': current_status,
            'current_status_display': parsed_data['trackingItems']['trackingTable'][0]["status"],
            'shipment_no': order.shipment_shipment_no,
            'status': order.status,
            'status_display': order.get_status_display(),
            'send_email': send_mail,
        }
        
    else:

        response = {
            'success': False,
            'code': str(response.status_code),
        }

    return response
