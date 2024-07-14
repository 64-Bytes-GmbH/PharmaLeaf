import json
import os
import re
import base64

from datetime import datetime
from jsonschema import validate, ValidationError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile

from app.models import Pharmacies, Customers, Orders, OrderProducts, Products, OrderRecipes
from db_logger.utils import create_log

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def recipe_endpoint_v1(request):
    """ Recipe endpoint """

    create_log(
        reference='recipe_endpoint_v1',
        message=str(request.data),
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
        pharmacy = Pharmacies.objects.filter(pharmacy_id=pharmacy_id).first()

        if not pharmacy:
            return Response({'status': 'Error', 'message': 'Pharmacy not found'}, status=404)

        # Customer data
        customer_data = data.get('customer')

        # Validate if customer.email is email via regex
        if not re.match(r"[^@]+@[^@]+\.[^@]+", customer_data.get('email')):
            return Response({'status': 'Error', 'message': 'Email is not valid'}, status=400)
        
        # Validate if birthDate is valid date
        try:
            datetime.strptime(customer_data.get('birthDate'), '%d.%m.%Y')
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
                    'birth_date': datetime.strptime(customer_data.get('birthDate'), '%d.%m.%Y').date() if customer_data.get('birthDate') else None,
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
            customer        =   customer,
            pharmacy        =   pharmacy,
            ansay_order_id  =   data.get('internalOrderId'),
            delivery_type   =   'dhl_standard',
            payment_type    =   'prepayment',
            status          =   'in_review',
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
                hg_product = Products.objects.get(number=product_number)
            except Products.DoesNotExist:
                return Response({'status': 'Error', 'message': f'Product with Number { product_number } not found'}, status=404)

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
            return Response({'status': 'Error', 'message': 'Prescription file not valid'}, status=400)
        
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

        order.ordered = False
        order.save()

        try:
            # TO-Do: E-Mail sending
            return True
        except Exception as e:
            create_log(
                reference='recipe_endpoint_v1 - send_mailgun_new_recipe_order',
                message=str(e),
                user=request.user,
                category='error',
            )
            pass

        return Response({'status': 'Success', 'message': f'Order with id { order.id } successfully created.'}, status=200)
    
    except Exception as e:

        create_log(
            reference='recipe_endpoint_v1',
            message=str(e),
            user=request.user,
            category='error',
        )

        return Response({'status': 'Error', 'message': 'Internal Server Error'}, status=500)
    
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
                'price': round(product.self_payer_selling_price_brutto * 100),
                'form': product.form,
                'status': {
                    'value': product.status,
                    'label': product.get_status_display(),
                },
                'active': product.active,
            })

        data['status']  = 'Success'
        data['products'] = products_array

        return Response(data, status=200)

    except:

        return Response({'status': 'Error', 'message': 'Internal Server Error'}, status=500)
