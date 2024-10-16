import json
import os
import re
import base64

from datetime import datetime
from jsonschema import validate, ValidationError
from functools import wraps
from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile

from app.models import Pharmacies, Customers, Orders, OrderProducts, Products, OrderRecipes, APIKey, PZNAmounts
from db_logger.utils import create_log

def api_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        key = request.headers.get('Api-key')

        if not key:
            return JsonResponse({'error': 'API key required'}, status=401)

        try:
            api_key = APIKey.objects.get(key=key)
            request.user = api_key.user
        except APIKey.DoesNotExist:
            return JsonResponse({'error': 'Invalid API key'}, status=401)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

@api_view(['POST'])
@api_key_required
def recipe_endpoint_v1(request):
    """ Recipe endpoint with api key authentification """

    create_log(
        reference='recipe_endpoint_v1',
        message='Get request data',
        stack_trace=str(request.data),
        user=request.user,
    )

    try:

        # Check user premission for endpoint
        if not request.user.groups.filter(name='recipe_endpoint_v1').exists():
            return Response({'status': 'Error', 'message': 'Permission denied'}, status=403)

        data = request.data

        # Validate data via schema
        path = os.path.join(settings.SCHMEA_DIR, 'recipe_endpoint_v1.json')
        with open(path) as schema_file:
            schema = json.load(schema_file)

        try:
            validate(data, schema)
        except ValidationError as e:
            return Response({'status': 'Error', 'message': e.message}, status=400)

        # Check pharmacy_id
        pharmacy_id = data.get('pharmacy_id')

        # Check if pharmacy_id in pharmacies and get pharmacy
        pharmacy = Pharmacies.objects.filter(ansay_id=pharmacy_id).first()

        if not pharmacy:
            return Response({'status': 'Error', 'message': 'Pharmacy not found'}, status=404)

        # Customer data
        customer_data = data.get('customer')

        # Validate if customer.email is email via regex
        if not re.match(r"[^@]+@[^@]+\.[^@]+", customer_data.get('email')):
            return Response({'status': 'Error', 'message': 'Email is not valid'}, status=400)
        
        # Validate if birthDate is valid date
        birth_date = None
        try:
            # Check if birthdate in customre_data
            if 'birthDate' in customer_data and customer_data.get('birthDate'):
                birth_date = datetime.strptime(customer_data.get('birthDate'), '%d.%m.%Y')
        except:
            return Response({'status': 'Error', 'message': 'Birthdate is not valid'}, status=400)

        # Check customer exists via email
        user, created = User.objects.update_or_create(
            username=customer_data.get('email'),
            defaults={
                'email': customer_data.get('email'),
                'first_name': customer_data.get('firstname'),
                'last_name': customer_data.get('lastname'),
            }
        )

        # Address data
        adress_data = customer_data.get('homeAddress')

        # Create or update customer
        if user:
            customer, created = Customers.objects.update_or_create(
                user=user,
                defaults={
                    'birth_date': birth_date,
                    'street': adress_data.get('streetName'),
                    'street_number': adress_data.get('houseNr'),
                    'postcode': adress_data.get('postalCode'),
                    'city': adress_data.get('city'),
                    'country': 'DE',
                    'customer_type': 'self_payer',
                    'payment_type': 'prepayment',
                    'delivery_type': 'dhl_standard',
                    'phone': customer_data.get('phone'),
                    'can_trigger_order': True,
                }
            )
        
        # Get delivery address for order
        delivery_address = customer_data.get('deliveryAddress')

        # Create order
        order = Orders.objects.create(
            external_id     =   data.get('internalOrderId'),
            customer        =   customer,
            pharmacy        =   pharmacy,
            ansay_order_id  =   data.get('internalOrderId'),
            delivery_type   =   'dhl_standard',
            payment_type    =   'prepayment',
            status          =   'open',
            created_by      =   request.user,
        )

        if delivery_address:
            order.delivery_address_as_invoice = False
            order.del_street = delivery_address.get('streetName')
            order.del_street_number = delivery_address.get('houseNr')
            order.del_postal_code = delivery_address.get('postcode')
            order.del_city = delivery_address.get('city')

        order.save()

        # Create order products
        for product in data.get('products'):

            # Get product from product_id
            product_id = product.get('id')
            product_number = product.get('number')

            try:
                pzn_amount = PZNAmounts.objects.get(number=product_id)
                hg_product = pzn_amount.product
            except PZNAmounts.DoesNotExist:

                create_log(
                    reference='recipe_endpoint_v1',
                    message=f'Product with ID { product_id } not found',
                    user=request.user,
                    category='warning',
                )

                return Response({'status': 'Error', 'message': f'Product with ID { product_id } could not be found'}, status=404)

            OrderProducts.objects.create(
                order           =   order,
                product         =   hg_product,
                amount          =   product.get('quantity'),
                prepared        =   product.get('crushed'),
            )

        # Create recipe file from data base64
        prescription_url = data.get('prescriptionURL')

        # Decode base64
        try:

            # Ceck if prescription_url starts with data:application/pdf;base64,
            if prescription_url.startswith('data:application/pdf;base64,'):
                prescription_url = prescription_url.replace('data:application/pdf;base64,', '')

            pdf_data = base64.b64decode(prescription_url)
        except:
            return Response({'status': 'Error', 'message': 'Recipe not correct'}, status=400)
        
        pdf_file = ContentFile(pdf_data, name='recipe.pdf')

        # Create order recipe
        order_recipe = OrderRecipes.objects.create(
                            order = order,
                            file = pdf_file,
                            e_recipe = True,
                        )
        
        if data.get('doctor'):
            order_recipe.doctor_first_name = data.get('doctor').get('firstname')
            order_recipe.doctor_last_name = data.get('doctor').get('name')
            order_recipe.doctor_phone = data.get('doctor').get('phone')
            order_recipe.city_of_signature = data.get('doctor').get('cityOfSignature')
            try:
                order_recipe.signature_date = datetime.strptime(data.get('doctor').get('dateOfSignature'), '%Y-%m-%d').date()
            except:
                pass
            order_recipe.save()

        # Check if external_id already exists
        if order.external_id and Orders.objects.filter(external_id=order.external_id).exclude(status='open').exists():

            existing_order = Orders.objects.filter(external_id=order.external_id).exclude(status='open').first()

            order_recipe.order = existing_order
            order_recipe.save()

            return Response({'status': 'Error', 'message': f'Error. Order already exists'}, status=400)

        order.status = 'in_review'
        order.ordered = False
        order.save()

        return Response({'status': 'Success', 'message': f'Order has been successfully created.'}, status=200)
    
    except Exception as e:

        create_log(
            reference='recipe_endpoint_v1',
            message='Error while creating order via API',
            stack_trace=str(e),
            user=request.user,
            category='error',
        )

        return Response({'status': 'Error', 'message': 'Internal Server Error'}, status=500)
    
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def recipe_endpoint_v2(request):
    """ Recipe endpoint """

    create_log(
        reference='recipe_endpoint_v2',
        message=str(request.data),
        user=request.user,
    )

    try:

        # Check user premission for endpoint
        if not request.user.groups.filter(name='recipe_endpoint_v2').exists():
            return Response({'status': 'Error', 'message': 'Permission denied'}, status=403)

        data = request.data

        # Validate data via schema
        path = os.path.join(settings.SCHMEA_DIR, 'recipe_endpoint_v2.json')
        with open(path) as schema_file:
            schema = json.load(schema_file)

        try:
            validate(data, schema)
        except ValidationError as e:
            return Response({'status': 'Error', 'message': e.message}, status=400)

        # Check pharmacy_id 
        pharmacy_id = data.get('pharmacy_id')

        # Check if pharmacy_id in pharmacies and get pharmacy
        pharmacy = Pharmacies.objects.filter(pharmacy_id=pharmacy_id).first()

        if not pharmacy:
            return Response({'status': 'Error', 'message': 'Pharmacy not found'}, status=404)

        # Customer data
        customer_data = data.get('customer')

        # Validate if customer.email is email via regex
        if not re.match(r"[^@]+@[^@]+\.[^@]+", customer_data.get('email')):
            return Response({'status': 'Error', 'message': 'Email is not valid'}, status=400)
        
        # Validate if birth_date is valid date
        try:
            datetime.strptime(customer_data.get('birth_date'), '%d.%m.%Y')
        except:
            return Response({'status': 'Error', 'message': 'birth_date is not valid'}, status=400)

        # Check customer exists via email
        user, created = User.objects.update_or_create(
            username=customer_data.get('email'),
            defaults={
                'email': customer_data.get('email'),
                'first_name': customer_data.get('first_name'),
                'last_name': customer_data.get('last_name'),
            }
        )

        # Address data
        adress_data = customer_data.get('billing_address')

        # Create or update customer
        if user:
            customer, created = Customers.objects.update_or_create(
                user=user,
                defaults={
                    'birth_date': datetime.strptime(customer_data.get('birth_date'), '%d.%m.%Y').date() if customer_data.get('birth_date') else None,
                    'street': adress_data.get('street_name'),
                    'street_number': adress_data.get('house_number'),
                    'postcode': adress_data.get('postal_code'),
                    'city': adress_data.get('city'),
                    'country': 'DE',
                    'customer_type': 'self_payer',
                    'payment_type': 'prepayment',
                    'delivery_type': 'dhl_standard',
                    'phone': customer_data.get('phone_number'),
                    'can_trigger_order': True,
                }
            )
        
        # Get delivery address for order
        delivery_address = customer_data.get('delivery_address')

        # Create order
        order = Orders.objects.create(
            customer        =   customer,
            pharmacy        =   pharmacy,
            ansay_order_id  =   data.get('order_id'),
            delivery_type   =   'dhl_standard',
            payment_type    =   'prepayment',
            status          =   'in_review',
            created_by      =   request.user,
        )

        if delivery_address:
            order.delivery_address_as_invoice = False
            order.del_street = delivery_address.get('street_name')
            order.del_street_number = delivery_address.get('house_number')
            order.del_postal_code = delivery_address.get('postal_code')
            order.del_city = delivery_address.get('city')

        order.save()

        # Create order products
        for product in data.get('products'):

            # Get product from product_id
            product_id = product.get('id')
            product_number = product.get('number')

            try:
                hg_product = Products.objects.get(number=product_number)
            except Products.DoesNotExist:
                return Response({'status': 'Error', 'message': f'Product with number { product_number } could not be found'}, status=404)

            OrderProducts.objects.create(
                order           =   order,
                product         =   hg_product,
                amount          =   product.get('amount'),
                prepared        =   product.get('squashed'),
            )

        # Create recipe file from data base64
        prescription_url = data.get('recipe_url')

        # Decode base64
        try:

            # Ceck if prescription_url starts with data:application/pdf;base64,
            if prescription_url.startswith('data:application/pdf;base64,'):
                prescription_url = prescription_url.replace('data:application/pdf;base64,', '')

            pdf_data = base64.b64decode(prescription_url)
        except:
            return Response({'status': 'Error', 'message': 'Prescription file not valid'}, status=400)
        
        pdf_file = ContentFile(pdf_data, name='recipe.pdf')

        # Create order recipe
        order_recipe = OrderRecipes.objects.create(
                            order = order,
                            file = pdf_file,
                            e_recipe = True,
                        )
        
        if data.get('doctor'):
            order_recipe.doctor_first_name = data.get('doctor').get('first_name')
            order_recipe.doctor_last_name = data.get('doctor').get('last_name')
            order_recipe.doctor_phone = data.get('doctor').get('phone_number')
            order_recipe.city_of_signature = data.get('doctor').get('city')
            try:
                order_recipe.signature_date = datetime.strptime(data.get('doctor').get('date'), '%Y-%m-%d').date()
            except:
                pass
            order_recipe.save()

        order.ordered = False
        order.save()

        try:
            # TO-Do: E-Mail sending
            return True
        except Exception as e:
            create_log(
                reference='recipe_endpoint_v - send_mailgun_new_recipe_order',
                message=str(e),
                user=request.user,
                category='error',
            )
            pass

        return Response({'status': 'Success', 'message': f'Order created.'}, status=200)
    
    except Exception as e:

        create_log(
            reference='recipe_endpoint_v',
            message=str(e),
            user=request.user,
            category='error',
        )

        return Response({'status': 'Error', 'message': 'Server Error [HTTP500]'}, status=500)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_all_products_v1(request):
    """ Api endpoint to get all products """

    try:

        # Check user premission for endpoint
        if not request.user.groups.filter(name='get_all_products_v1').exists():
            return Response({'status': 'Error', 'message': 'Permission denied'}, status=403)

        products = Products.objects.all()

        data = {}

        products_array = []

        for product in products:
            products_array.append({
                'id': product.id,
                'number': product.number,
                'name': product.name,
                'description': product.description,
                'cultiviar': product.cultivar.name,
                'country': product.country_of_origin.name,
                'thc_value': product.thc_value,
                'cbd_value': product.max_cbd_value,
                'genetic': product.genetics.name,
                'manufacturer': product.manufacturer.name,
                'supplier': product.supplier.name,
                'price': round(product.self_payer_selling_price_brutto * 100),
                'form': product.form,
                'terpene': [terpene.name for terpene in product.main_terpene.all()],
                'status': {
                    'value': product.status,
                    'label': product.get_status_display(),
                },
                'avaliable_amount': 0,
                'active': product.active,
            })

        data['status']  = 'Success'
        data['products'] = products_array

        return Response(data, status=200)

    except:

        return Response({'status': 'Error', 'message': 'Internal Server Error'}, status=500)
