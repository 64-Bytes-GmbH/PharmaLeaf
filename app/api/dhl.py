import requests
import json
import logging
import xmltodict
import xml.etree.ElementTree as ET
from django.db.models import Q
from xml.dom.minidom import parseString
from urllib.parse import urlencode
from datetime import datetime
from ..models import MainSettings, Orders, Logger, OpeningHours
from base64 import b64decode, b64encode
from .api_utils import chunks
from db_logger.utils import create_log

logger = logging.getLogger(__name__)

# AUTHENTICATION
DHL_API_KEY = "XWtMA11twO3hbFv18TGq43zOWei20b2k"
TEST_AUTH_KEY = "MjIyMjIyMjIyMl9hYnJfMDgwMTpTOFBqbUxCIXMydnJ6V1Yzbw=="
ACCOUNT_NUMBER = ""
BILLING_NUMBER = ""

# URLs
LABEL_URL = "https://api-sandbox.dhl.com/parcel/de/shipping/v2/orders"
TRACKING_URL = "https://api-eu.dhl.com/track/shipments"
PICKUP_URL = "https://api-sandbox.dhl.com/parcel/de/transportation/pickup/v1/orders"


def dhl_create_label(order_id):
    """
    Parameters
    ----------
    order_id : int
        id of the order
    get_file : bool
        true if pdf should be returned
    """

    response = {
        'success': False,
    }

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    username = pharmacy.dhl_username
    password = pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    pickup_url = base_url + "/parcel/de/shipping/v2/orders"

    # Create payload
    payload = {
        "profile": "STANDARD_GRUPPENPROFIL",
        "shipments": [
            {
                "product": "V01PAK" if main_settings.test_mode else pharmacy.dhl_shipping_product,
                "billingNumber": "33333333330102" if main_settings.test_mode else pharmacy.dhl_billing_number,
                "refNo": order.number,
                "shipper": {
                    "name1": pharmacy.name,
                    "name2": "Haupteingang",
                    "addressStreet": pharmacy.street,
                    "addressHouse": pharmacy.street_number,
                    "postalCode": pharmacy.postalcode,
                    "city": pharmacy.city,
                    "email": pharmacy.email,
                    "phone": pharmacy.phonenumber,
                    "country": "DEU",
                },
                "consignee": {
                    "name1": f"{order.del_first_name} {order.del_last_name}",
                    "addressStreet": "Packstation" if order.delivery_at_postoffice else order.del_street,
                    "addressHouse": order.locker_id if order.delivery_at_postoffice else order.del_street_number,
                    # "additionalAddressInformation1": order.comment,
                    "postalCode": order.del_postalcode,
                    "city": order.del_city,
                    "country": "DEU",
                    "email": order.email_address,
                },
                "details": {
                    "dim": {"uom": "mm", "height": 100, "length": 200, "width": 150},
                    "weight": {"uom": "g", "value": 500},
                },
                "services": {
                    "visualCheckOfAge": "A18",
                },
            }
        ],
    }
    
    # Add name2 to consignee if delivery at postoffice
    if order.delivery_at_postoffice:
        payload['shipments'][0]['consignee']['name2'] = order.postnumber

    auth_key = 'c2FuZHlfc2FuZGJveDpwYXNz' if main_settings.test_mode else b64encode(str(username + ':' + password).encode('ascii')).decode('utf-8')

    headers = {
        "content-type": "application/json",
        "Accept-Language": "de-DE",
        "Authorization": f"Basic {auth_key}",
        "dhl-api-key": api_key,
    }

    dhl_response = requests.request("POST", pickup_url, json=payload, headers=headers, timeout=180)
    parsed_data = json.loads(dhl_response.text)

    if 'status' in parsed_data:
    
        if isinstance(parsed_data['status'], dict) and 'statusCode' in parsed_data['status']:

            if parsed_data['status']['statusCode'] in [200]:
            
                order.shipment_shipment_no = parsed_data['items'][0]['shipmentNo']
                order.shipment_ref_no = parsed_data['items'][0]['shipmentRefNo']
                order.shipment_label_b64_string = parsed_data['items'][0]['label']['b64']
                order.shipment_label_type = order.delivery_type
                
                if order.status not in ['shipped', 'delivered', 'cancelled']:
                    order.status = 'ready_to_ship'
                order.save()

                response = {
                    'success': True,
                    'code': parsed_data['status']['statusCode'],
                    'shipment_label_type': order.shipment_label_type,
                    'shipment_label_type_display': order.get_shipment_label_type_display(),
                    'shipment_no': order.shipment_shipment_no,
                }

            else:

                create_log(
                    reference='DHL Label (Creation) - Header',
                    message=f'DHL Label could not be created for order {order.number} (Pharmacy: {pharmacy.name})',
                    stack_trace=str(payload),
                    category='warning',
                    user='System'
                )

                response = {
                    'success': False,
                    'code': parsed_data['status']['statusCode'],
                    'title': parsed_data['status']['title'],
                    'detail': parsed_data['status']['detail'],
                }

        else:

            create_log(
                reference='DHL Label (Creation) - Header',
                message=str(headers),
                category='info',
                user='System'
            )

            create_log(
                reference='DHL Label (Creation) - Payload',
                message=str(payload),
                category='info',
                user='System'
            )

            create_log(
                reference='DHL Label (Creation) - Payload',
                message=str(parsed_data),
                category='warning',
                user='System'
            )

            response = {
                'success': False,
                'code': parsed_data['status'],
                'title': parsed_data['title'],
                'detail': parsed_data['detail'],
            }

    if 'success' in response and response['success'] == True:
        return response

    create_log(
        reference='DHL Label (Creation)',
        message=response,
        category='error',
        stack_trace=str(parsed_data),
        user='System'
    )

    response['success'] = False

    return response

def b64_to_pdf(b64_string):
    """
    Creates a pdf file from b64 string used by DHL for label creation
    Needs to be adjusted so file is opened in new tab (?)
    """

    bytes = b64decode(b64_string, validate=True)

    if bytes[0:4] != b"%PDF":
        raise ValueError("Missing the PDF file signature")

    f = open("file.pdf", "wb")
    f.write(bytes)
    f.close()

def order_shipment_pick_up(order_id, date=0):
    """
    Parameters
    ----------
    order_id : int
        id of the order
    date : str
        date format: yyyy-mm--dd. If not set, parcel will be picked up asap
    """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    username = pharmacy.dhl_username
    password = pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    pickup_url = base_url + "/parcel/de/transportation/pickup/v1/orders"

    # Get todays weekday as integer
    today = datetime.today()
    weekday = today.weekday()

    # Create businessHours
    opening_hours = OpeningHours.objects.filter(day=str(weekday), pharmacy=pharmacy).first()

    # Create payload
    payload = {
        "customerDetails": {
            "accountNumber": "2222222222" if main_settings.test_mode else pharmacy.dhl_account_number,
            "billingNumber": "22222222220801" if main_settings.test_mode else pharmacy.dhl_billing_number,
        },
        "pickupLocation": {
            "pickupAddress": {
                "name1": pharmacy.name,
                "name2": "Haupteingang",
                "addressStreet": pharmacy.street,
                "addressHouse": pharmacy.street_number,
                "postalCode": pharmacy.postalcode,
                "city": pharmacy.city,
                "country": "DE",
            },
            "businessHours": [
                {
                    "timeFrom": "08:00" if not opening_hours else opening_hours.from_time.strftime('%H:%M'),
                    "timeUntil": "19:00" if not opening_hours else opening_hours.to_time.strftime('%H:%M'),
                }
            ],
        },
        "contactPerson": {
            "name": pharmacy.contact_name,
            "phone": pharmacy.phonenumber,
            "email": pharmacy.email,
        },
        "pickupDetails": {
            "pickupDate": {
                "type": "ASAP" if date == 0 else date,
                # "value": None if date == 0 else date,
            },
            "emailNotification": pharmacy.email,
            "totalWeight": {
                "uom": "kg", "value": 1
            },
            # "comment": "string",
        },
        "shipmentDetails": {
            "shipments": [
                {
                    "transportationType": "PAKET",
                    "size": "S",
                }
            ]
        },
    }

    auth_key = 'MjIyMjIyMjIyMl9hYnJfMDgwMTpTOFBqbUxCIXMydnJ6V1Yzbw==' if main_settings.test_mode else b64encode(str(username + ':' + password).encode('ascii')).decode('utf-8')

    headers = {
        "content-type": "application/json",
        "Accept-Language": "de-DE",
        "Authorization": f"Basic {auth_key}",
        "dhl-api-key": api_key,
    }

    response = requests.request("POST", pickup_url, json=payload, headers=headers, timeout=180)

    parsed_data = json.loads(response.text)

    if 'confirmation' in parsed_data:
            
        order.shipment_pickup_order_uuid = parsed_data['confirmation']['value']['orderID']
        order.shipment_pickup_date = datetime.strptime(parsed_data['confirmation']['value']['pickupDate'], '%Y-%m-%d')
        order.save()

        response = {
            'success': True,
            'code': 201,
            'pickUpDate': order.shipment_pickup_date.strftime('%d.%m.%Y')
        }


    else:

        if 'status' in parsed_data:

            response = {
                'success': False,
                'code': parsed_data['status'],
                'title': parsed_data['title'],
                'detail': parsed_data['detail'],
            }

        else:

            response = {
                'success': False,
                'code': parsed_data[0]['errorCode'],
                'title': parsed_data[0]['title'],
                'detail': '',
            }

    return response

def dhl_cancel_label(order_id):
    """ Cancel shipment label """
    
    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    username = pharmacy.dhl_username
    password = pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    url = base_url + "/parcel/de/shipping/v2/orders"

    query = {"shipmentNumber": order.shipment_shipment_no}

    query = {
        "profile": "STANDARD_GRUPPENPROFIL",
        "shipment": order.shipment_shipment_no
    }
    
    auth_key = 'c2FuZHlfc2FuZGJveDpwYXNz' if main_settings.test_mode else b64encode(str(username + ':' + password).encode('ascii')).decode('utf-8')

    headers = {
        "content-type": "application/json",
        "Accept-Language": "de-DE",
        "Authorization": f"Basic {auth_key}",
        "dhl-api-key": api_key,
    }

    response = requests.request("DELETE", url, headers=headers, params=query, timeout=180)
    parsed_data = json.loads(response.text)

    if 'status' in parsed_data:
    
        if isinstance(parsed_data['status'], dict) and 'statusCode' in parsed_data['status']:

            if parsed_data['status']['statusCode'] in [200]:

                order.shipment_label_b64_string = ''
                order.shipment_label_type = ''
                order.shipment_shipment_no = ''
                order.shipment_ref_no = ''
                order.status = 'process'
                order.save()

                response = {
                    'success': True,
                    'code': parsed_data['status']['statusCode'],
                }

            else:

                order.shipment_label_b64_string = ''
                order.shipment_label_type = ''
                order.shipment_shipment_no = ''
                order.shipment_ref_no = ''
                order.save()
                
                create_log(
                    reference='DHL Label (Cancellation)',
                    message=str(parsed_data),
                    category='error',
                    user='System'
                )

                response = {
                    'success': False,
                    'code': parsed_data['status']['statusCode'],
                    'title': parsed_data['items'][0]['sstatus']['title'],
                    'detail': parsed_data['items'][0]['sstatus']['detail'],
                }
    
    return response

def delete_shipment_pick_up(order_id):
    """ Delete shipment pick up """

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    username = pharmacy.dhl_username
    password = pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    url = base_url + "/parcel/de/transportation/pickup/v3/orders"

    query = {"orderID": order.shipment_pickup_order_uuid}

    headers = {
        "content-type": "application/json",
        "Accept-Language": "de-DE",
        "dhl-api-key": api_key,
    }

    response = requests.request("DELETE", url, headers=headers, params=query, timeout=180)
    parsed_data = json.loads(response.text)

    if (
        parsed_data["confirmedCancellations"][0]["orderID"]
        == order.shipment_pickup_order_uuid
    ):
        return "Abholung storniert"
    else:
        return "Stornierung nicht möglich. Fehler aufgetreten."

def dhl_check_status(order_id):
    """ DHL check status of shipment """
    
    response = None

    main_settings = MainSettings.objects.first()
    order = Orders.objects.get(id=order_id)
    pharmacy = order.pharmacy

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    secret_key = pharmacy.dhl_secret_key
    username = 'zt12345' if main_settings.test_mode else pharmacy.dhl_z_username
    password = 'geheim' if main_settings.test_mode else pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    tracking_url = base_url + "/parcel/de/tracking/v0/shipments"

    auth_key = 'WFd0TUExMXR3TzNoYkZ2MThUR3E0M3pPV2VpMjBiMms6WDNTbmhLZGhKeUFjcGFtZQ==' if main_settings.test_mode else b64encode(str(api_key + ':' + secret_key).encode('ascii')).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_key}",
        # TODO: User-Agent anpassen
        # "User-Agent": "apotheke.de/1.0"
    }

    parameters = {
        "appname": username,
        "language-code": "de",
        "password": password,
        "piece-code": order.shipment_shipment_no,
        "request": "d-get-piece-detail",
    }

    # XML manuell erstellen
    root = ET.Element("data", attrib=parameters)
    xml_str = ET.tostring(root, encoding="ISO-8859-1", method="xml").decode("ISO-8859-1")

    params = {'xml': xml_str}
    url_encoded_params = urlencode(params)

    response = requests.get(tracking_url, headers=headers, params=url_encoded_params)

    if response.status_code == 200:
        dict_response = xmltodict.parse(response.text)

        if not '@error' in dict_response['data']:

            send_mail = False

            delivery_event_flag = dict_response['data']['data']['@delivery-event-flag']

            if delivery_event_flag == '1':
                order.status = 'delivered'
                order.save()

            else:

                ice = dict_response['data']['data']['@ice']

                if ice in ['DLVRD', 'HLDCC']:
                    order.status = 'delivered'

                if ice in ['DLVRF']:
                    order.status = 'acceptance_refused'

                if ice in ['NTDEL']:
                    order.status = 'delivery_not_possible'

                if ice in ['LDTMV', 'SRTED', 'ULFMV', 'PARCV', 'ADVIS', 'INFCL', 'CNRFC', 'HNDDE', 'SHRCU', 'PCKDU']:
                    send_mail = order.status not in ['shipped', 'delivered']
                    order.status = 'shipped'

                order.save()

            response = {
                'success': True,
                'code': response.status_code,
                'status': order.status,
                'send_email': send_mail,
            }

        else:

            error_message = dict_response['data']['@error']

            create_log(
                reference='DHL Label (Check status)',
                message=f'{response.status_code} - {error_message}',
                stack_trace=str(dict_response),
                category='error',
                user='System'
            )

            response = {
                'success': False,
                'code': response.status_code,
                'message': response.text,
            }

    else:

        create_log(
            reference='DHL Label (Check status)',
            message=f'{response.status_code}',
            stack_trace=str(response.text),
            category='error',
            user='System'
        )

        response = {
            'success': False,
            'code': response.status_code,
            'message': response.text,
        }

    return response

def dhl_check_bulk_status(orders, pharmacy):
    """ DHL check status of shipment - NICHT IM TEST MODUS """

    response = None

    main_settings = MainSettings.objects.first()

    # DHL credentials
    api_key = pharmacy.dhl_api_key
    secret_key = pharmacy.dhl_secret_key
    username = 'zt12345' if main_settings.test_mode else pharmacy.dhl_z_username
    password = 'geheim' if main_settings.test_mode else pharmacy.dhl_password

    # DHL base url
    base_url = pharmacy.dhl_base_url_test if main_settings.test_mode else pharmacy.dhl_baser_url_prod
    tracking_url = base_url + "/parcel/de/tracking/v0/shipments"

    auth_key = b64encode(str(api_key + ':' + secret_key).encode('ascii')).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_key}",
        # TODO: User-Agent anpassen
        "User-Agent": "apotheke.de/1.0"
    }

    orders = orders.filter(shipment_label_type='dhl_standard').exclude(shipment_shipment_no='')

    send_mail_order_ids = []

    for chunk_order_ids in chunks(orders.values_list('id', flat=True), 20):

        chunk_orders = Orders.objects.filter(id__in=chunk_order_ids)

        parameters = {
            "appname": username,
            "language-code": "de",
            "password": password,
            "piece-code": ";".join([str(order.shipment_shipment_no) for order in chunk_orders]),
            "request": "d-get-piece-detail",
        }

        # XML manuell erstellen
        root = ET.Element("data", attrib=parameters)
        xml_str = ET.tostring(root, encoding="ISO-8859-1", method="xml").decode("ISO-8859-1")

        params = {'xml': xml_str}
        url_encoded_params = urlencode(params)

        response = requests.get(tracking_url, headers=headers, params=url_encoded_params)

        if response.status_code == 200:

            dict_response = xmltodict.parse(response.text)

            if not '@error' in dict_response['data']:

                if isinstance(dict_response['data']['data'], list):

                    for data in dict_response['data']['data']:

                        order = Orders.objects.get(shipment_shipment_no=data['@piece-code'])

                        delivery_event_flag = data['@delivery-event-flag']

                        if delivery_event_flag == '1':
                            order.status = 'delivered'
                            order.save()

                        else:

                            ice = data['@ice']

                            if ice in ['DLVRD', 'HLDCC']:
                                order.status = 'delivered'

                            if ice in ['DLVRF']:
                                order.status = 'acceptance_refused'

                            if ice in ['NTDEL']:
                                order.status = 'delivery_not_possible'

                            if ice in ['LDTMV', 'SRTED', 'ULFMV', 'PARCV', 'ADVIS', 'INFCL', 'CNRFC', 'HNDDE', 'PCKDU']:

                                if order.status not in ['shipped', 'delivered']:
                                    send_mail_order_ids.append(order.id)

                                order.status = 'shipped'

                            order.save()

                else:

                    order = Orders.objects.get(shipment_shipment_no=dict_response['data']['data']['@piece-code'])

                    delivery_event_flag = dict_response['data']['data']['@delivery-event-flag']

                    if delivery_event_flag == '1':
                        order.status = 'delivered'
                        order.save()

                    else:

                        ice = dict_response['data']['data']['@ice']
                        
                        if ice in ['DLVRD', 'HLDCC']:
                            order.status = 'delivered'

                        if ice in ['NTDEL']:
                            order.status = 'delivery_not_possible'

                        if ice in ['LDTMV', 'SRTED', 'ULFMV', 'PARCV', 'ADVIS', 'INFCL', 'CNRFC', 'HNDDE', 'PCKDU']:

                            if order.status not in ['shipped', 'delivered']:
                                send_mail_order_ids.append(order.id)
                            order.status = 'shipped'

                        order.save()

    response = {
        'send_mail_order_ids': send_mail_order_ids,
    }

    return response
