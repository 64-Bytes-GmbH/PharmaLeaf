""" Views """

import json
import csv
from weasyprint import HTML

from datetime import datetime, timedelta, date
from io import StringIO
from decimal import Decimal
from collections import defaultdict
from xhtml2pdf import pisa

from django.core.paginator import Paginator
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.utils.functional import wraps
from django.db.models import F, Q, Count, Sum, Avg, Min, Max
from django.db.models.functions import ExtractWeek, ExtractMonth, ExtractYear, TruncDate

from .models import *
from .utils import *
from db_logger.utils import create_log
from .tasks import task_update_delivery_status
from .api.api_utils import chunks
from .api.dhl import order_shipment_pick_up, dhl_create_label, dhl_cancel_label, dhl_check_status
from .api.go_express import go_express_create_label, go_express_cancel_label, go_express_update_label, go_express_update_status, go_express_check_status
from .api.brevo import brevo_send_test_mail, brevo_send_order_shipped

from app.templatetags.extra_tags import fill_week_gaps, fill_month_gaps
from django.shortcuts import redirect


def set_cookie(response, key, value, days_expire=7):
    """ Cookies einstellen """

    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60

    expires = datetime.strftime(
        datetime.utcnow() + timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )

    response.set_cookie(
        key,
        value,
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
    )


#################################### Decorators ###########################################
def user_is_authenticated(function):
    """ Decorator, to check if user is authenticated """

    def _function(request, *args, **kwargs):

        if request.user.is_authenticated:

            try:
                Customers.objects.get(user=request.user)
            except ObjectDoesNotExist:
                return redirect(home)

            return function(request, *args, **kwargs)
        
        return redirect(home)
    
    return _function

def check_staff_user(function):
    """ Decorator, to check if user is authenticated and has premission """
    
    def _function(request, *args, **kwargs):

        if request.user.is_authenticated and not request.user.is_staff:
            return redirect(home)
        
        if request.user.is_staff:
            
            view_name = request.resolver_match.url_name

            if view_name == 'dashboard_users':
                premissions = list(UserPremissions.objects.filter(user=request.user, read_premission=True).values_list('view', flat=True))
            else:
                staff_user = StaffUser.objects.get(user=request.user)
                premissions = list(UserPremissions.objects.filter(user=request.user, read_premission=True, pharmacy=staff_user.selected_pharmacy).values_list('view', flat=True))

            if view_name in premissions or request.user.is_superuser:
                print(view_name)
                return function(request, *args, **kwargs)
            
            if len(premissions) != 0:
                return redirect(premissions[0])
            
            return redirect(home)
    
        return redirect(dashboard_login)

    return _function

####################### General Pages #######################
def home(request): #!
    """ Startseite """

    context = {}

    context['faqs'] = FAQs.objects.filter(group__name='Häufig gestellte Fragen')
    context['indications'] = CannabisIndications.objects.exclude(teaser='').exclude(teaser_source='').exclude(image__exact='')
    context['genetics'] = Genetics.objects.all()
    context['effects_content'] = CannabisEffects.objects.filter(main_page=True).order_by('position')
    context['is_staff'] = request.user.is_staff

    response = render(request, 'dashboard/index.html', context)

    ###### Cookies #######
    if request.method == 'POST':

        if 'acceptCookies' in request.POST:

            data = {}

            cookies_type = request.POST.get('cookiesType')

            if cookies_type == 'full':
                set_cookie(response, 'full_cookies', 'Cookie to save if the cookies where already accepted in the past 30 days.', 30)
                
                data['cookies'] = 'full'

            else:
                set_cookie(response, 'mandatory_cookies', 'Cookie to save if the cookies where already accepted in the past 30 days.', 30)

                data['cookies'] = 'mandatory'

        if 'globalSearch' in request.POST:

            data = {}

            search_word = request.POST.get('search')

            items = []

            if search_word:

                values = search_word.split(' ')
                values = [value for value in values if value]

                q_objects = Q()

                for value in values:

                    q_objects &= (
                        Q(name__icontains=value) |
                        Q(cultivar__name__icontains=value) |
                        Q(genetics__name__icontains=value) |
                        Q(manufacturer__name__icontains=value) |
                        Q(main_terpene__name__icontains=value) |
                        Q(main_terpene__terpene_effect__name__icontains=value)
                    )

                products = Products.objects.filter(active=True).filter(q_objects).distinct().order_by('-priority', '-status')

                for item in products:

                    product_image = ProductImages.objects.filter(product=item, main_image=True).first()

                    items.append({
                        'id': item.id,
                        'name': item.name,
                        'img': product_image.img.url if product_image else '',
                        'cultivar': item.cultivar.name if item.cultivar else '',
                        'genetics': item.genetics.name if item.genetics else '',
                        'thc_value': round(item.thc_value * 100),
                        'cbd_value': round(item.max_cbd_value * 100),
                        'status': item.status,
                        'url': reverse('product', kwargs={'url_name': item.url_name}),
                    })

            data['items'] = items

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'disableSpecialOfferModal' in request.POST:
            set_cookie(response, 'special_offer_shown', 'Cookie for the special offer.', 1)

    return response

def imprint(request): #!
    """ Impressum """

    context = {}

    order = None

    if 'order_id' in request.session:

        try:
            order = Orders.objects.get(id=request.session['order_id'])
        except ObjectDoesNotExist:
            order = None

    context['order'] = order

    return render(request, 'app/imprint.html', context)

def policy(request): #!
    """ Datenschutz """

    context = {}

    order = None

    if 'order_id' in request.session:

        try:
            order = Orders.objects.get(id=request.session['order_id'])
        except ObjectDoesNotExist:
            order = None

    context['order'] = order

    return render(request, 'app/policy.html', context)

def agb(request): #!
    """ AGBs """

    context = {}


    return render(request, 'app/agb.html', context)

def cookie_info(request): #!
    """ Cookie-Informationen """

    context = {}


    return render(request, 'app/cookie_info.html', context)

def shipping_and_retoures(request): #!
    """ Versand und Retouren """

    context = {}

    return render(request, 'app/shipping_and_retoures.html', context)

def payment(request): #!
    """ Zahlungsmethoden """

    context = {}

    return render(request, 'app/payment.html', context)


####################### Dashboard #######################
def dashboard_login(request):
    """ Dashboard login """

    context = {}

    if request.method == 'POST':

        data = {}
        
        if 'loginUser' in request.POST:

            wrong_username = False
            wrong_password = False
            no_premission = False

            username = request.POST.get('username')
            password = request.POST.get('password')

            # Check if user with unsername exists
            try:
                user = User.objects.get(username=username)

                if not user.is_staff:
                    wrong_username = True

            except ObjectDoesNotExist:
                wrong_username = True

            url = None

            # Check password
            if not wrong_username:

                user = authenticate(username=username, password=password)

                if user and user.is_superuser:
                    login(request, user)
                    url = reverse(dashboard)

                elif user:
                    premissions = list(UserPremissions.objects.filter(user=user, read_premission=True).values_list('view', flat=True))

                    if len(premissions) != 0:
                        login(request, user)
                        url = reverse(premissions[0])
                    
                    else:
                        no_premission = True

                else:
                    wrong_password = True

            data['wrong_username'] = wrong_username
            data['wrong_password'] = wrong_password
            data['no_premission'] = no_premission
            data['url'] = url

        if 'setNewPassword' in request.POST:

            new_password = request.POST.get('newPassword')

            user = request.user

            url = None

            user.set_password(new_password)
            user.save()

            if user and user.is_superuser:
                    login(request, user)
                    url = reverse(dashboard)

            elif user:
                premissions = list(UserPremissions.objects.filter(user=user, read_premission=True).values_list('view', flat=True))

                if len(premissions) != 0:
                    login(request, user)
                    url = reverse(premissions[0])
                
                else:
                    no_premission = True

            data['url'] = url

        if 'selectPharmacy' in request.POST:

            pharmacy_id = request.POST.get('pharmacyId')

            pharmacy = Pharmacies.objects.get(id=pharmacy_id)

            staff_user = StaffUser.objects.get(user=request.user)
            staff_user.selected_pharmacy = pharmacy
            staff_user.save()

        return HttpResponse(json.dumps(data), content_type='application/json')

    return render(request, 'dashboard/login.html', context)

def dashboard_activate_user(request, uidb64, token):
    """ Dashboard activate user """

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):

        user.is_active = True
        user.save()

        login(request, user)

        request.session['reset_password_confirmed'] = True

        return redirect(dashboard_login)

    else:
        request.session['reset_password_confirmed'] = False

    return redirect(home)

@check_staff_user
def dashboard(request):
    """ Dashboard """
    
    context = {}

    if request.method == 'GET':

        amount_completed_orders = Orders.objects.filter(status__in=['delivered'])
        total_revenue = amount_completed_orders.aggregate(total_revenue=Sum('subtotal'))['total_revenue']

        if amount_completed_orders.count():
            average_revenue = total_revenue / amount_completed_orders.count()
            average_revenue_per_order = "{:,.2f}".format(average_revenue).replace('.', ',') + " EUR"
        else:
            average_revenue_per_order = "0 EUR"

        # Top 10 Produkte
        top_products = OrderProducts.objects \
            .filter(order__status='delivered') \
            .select_related('product').values(
                'product__name', 
                'product__cultivar__name', 
                # 'product__pirce_per_unit', 
                'product__manufacturer__name'
        ).annotate(
            top_total_revenue=Sum(0),
            # top_total_revenue=Sum(F('product__pirce_per_unit') * F('amount')),
            top_total_amount=Sum('amount')
        ).order_by('-top_total_revenue')[:10]

        # Runde die `top_total_revenue` in jedem Top Produkt
        for product in top_products:
            # product['pirc_per_unit'] = "{:,.2f}".format(product['product__pirce_per_unit']).replace('.', ',') + " EUR"
            product['pirc_per_unit'] = "0,00 EUR"
            product['top_total_revenue'] = Decimal(product['top_total_revenue']).quantize(Decimal("1.00"))

        total_amount_sold = OrderProducts.objects.filter(order__status='delivered').aggregate(total_amount_sold=Sum('amount'))['total_amount_sold']

        # Get stats for revenue table
        today = date.today()
        yesterday = today - timedelta(days=1)
        this_month = today.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        this_year = today.replace(month=1, day=1)

        subtotal_table = {}

        subtotal_table['today'] = Orders.objects.filter(status='delivered', order_time__date=today).aggregate(total_subtotal=Sum('subtotal'))['total_subtotal'] or 0
        subtotal_table['yesterday'] = Orders.objects.filter(status='delivered', order_time__date=yesterday).aggregate(total_subtotal=Sum('subtotal'))['total_subtotal'] or 0
        subtotal_table['this_month'] = Orders.objects.filter(status='delivered', order_time__date__gte=this_month).aggregate(total_subtotal=Sum('subtotal'))['total_subtotal'] or 0
        subtotal_table['last_month'] = Orders.objects.filter(status='delivered', order_time__date__range=(last_month, this_month - timedelta(days=1))).aggregate(total_subtotal=Sum('subtotal'))['total_subtotal'] or 0
        subtotal_table['year'] = Orders.objects.filter(status='delivered', order_time__date__gte=this_year).aggregate(total_subtotal=Sum('subtotal'))['total_subtotal'] or 0

        amount_table = {}

        amount_table['today'] = OrderProducts.objects.filter(order__status='delivered', order__order_time__date=today).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        amount_table['yesterday'] = OrderProducts.objects.filter(order__status='delivered', order__order_time__date=yesterday).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        amount_table['this_month'] = OrderProducts.objects.filter(order__status='delivered', order__order_time__date__gte=this_month).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        amount_table['last_month'] = OrderProducts.objects.filter(order__status='delivered', order__order_time__date__range=(last_month, this_month - timedelta(days=1))).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        amount_table['year'] = OrderProducts.objects.filter(order__status='delivered', order__order_time__date__gte=this_year).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        context['completed_orders'] = amount_completed_orders.count()
        context['total_revenue'] = total_revenue
        context['top_products'] = top_products
        context['total_amount_sold'] = total_amount_sold / 1000 if total_amount_sold else 0
        context['average_revenue_per_order'] = average_revenue_per_order
        context['subtotal_table'] = subtotal_table
        context['amount_table'] = amount_table

    return render(request, 'dashboard/index.html', context)

@check_staff_user
def dashboard_orders(request):
    """ Dashboard Bestellungen """
    
    context = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    orders = Orders.objects.all()

    active_pharmacy = staff_user.selected_pharmacy
    pharmacy_employees = PharmacyEmployees.objects.filter(pharmacy=active_pharmacy).values('id', 'short_name', 'is_default')
    context['pharmacy_employees'] = list(pharmacy_employees)

    if request.method == 'GET':
        
        # Seite
        page_number = request.GET.get('page', 1)
        
        # fastFilter Button
        filter_button = request.GET.get('filterButton', '')

        # Suche
        search_value = request.GET.get('search', '')

        orders = dashboard_filter_orders(request.GET, staff_user.selected_pharmacy)

        orders = orders.exclude(status='in_review')

        cancellation_reasons = CancellationReasons.objects.all()
        
        paginator = Paginator(orders, 20)
        page_orders = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['filterButton'] = filter_button
        context['search'] = search_value
        context['orders'] = page_orders
        context['orders_dic'] = [order.id for order in page_orders]
        context['cancellation_reasons'] = cancellation_reasons

    context['selected_pharmacy_id'] = staff_user.selected_pharmacy.id
    context['baseUrl'] = request.build_absolute_uri(request.path)

    return render(request, 'dashboard/orders.html', context)

@check_staff_user
def dashboard_order_products(request):
    """ List of order products """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_order_products',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    context = {}

    if request.method == 'GET':
        
        # Seite
        page_number = request.GET.get('page', 1)

        # Suche
        search_value = request.GET.get('search', '')

        order_products = dashboard_filter_order_products(request.GET, staff_user.selected_pharmacy)
        
        paginator = Paginator(order_products, 20)
        page_products = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['search'] = search_value
        context['order_products'] = page_products

    context['selected_pharmacy_id'] = staff_user.selected_pharmacy.id
    context['manufacturers'] = Manufacturer.objects.all()
    context['suppliers'] = Supplier.objects.all()

    return render(request, 'dashboard/order_products.html', context)

@check_staff_user
def dashboard_review_orders(request):
    """ Dashboard Rezeptbestellungen """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_review_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    context = {}

    prescription_orders = Orders.objects.filter(status='in_review').order_by('-id')

    if request.method == 'GET':

        # Seite
        page_number = request.GET.get('page', 1)

        # Suche
        search_value = request.GET.get('search', '')

        prescription_orders = dashboard_filter_prescription_orders(request.GET, staff_user.selected_pharmacy)

        prescription_orders.filter(status='in_review')
        
        paginator = Paginator(prescription_orders, 20)
        page_orders = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['search'] = search_value
        context['orders'] = page_orders
        context['orders_dic'] = [order.id for order in page_orders]

    context['selected_pharmacy_id'] = staff_user.selected_pharmacy.id
    context['prescription_orders'] = prescription_orders

    return render(request, 'dashboard/review_orders.html', context)

@check_staff_user
def dashboard_products_stock(request):
    """ Lagerbestand (Produkte) """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    context = {}

    active_pharmacy = staff_user.selected_pharmacy

    if request.method == 'GET':
        
        # Seite
        page_number = request.GET.get('page', 1)

        # Suche
        search_value = request.GET.get('search', '')

        products = dashboard_filter_stock_products(request.GET, staff_user.selected_pharmacy)
        
        paginator = Paginator(products, 20)
        page_products = paginator.get_page(page_number)

        
        context['page'] = page_number
        context['search'] = search_value
        context['products'] = page_products
        context['suppliers'] = Supplier.objects.all().order_by('name')
        context['manufacturer'] = Manufacturer.objects.all().order_by('name')
        context['active_pharmacy'] = active_pharmacy

    return render(request, 'dashboard/products_stock.html', context)

@check_staff_user
def dashboard_packages_stock(request):
    """ Lagerbestand (Verpackungen) """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    context = {}

    manufacturers = PackageManufacturers.objects.all()
    
    context['manufacturers'] = manufacturers

    if request.method == 'GET':
        
        # Seite
        page_number = request.GET.get('page', 1)

        # Suche
        search_value = request.GET.get('search', '')

        packages = dashboard_filter_stock_packages(request.GET, staff_user.selected_pharmacy)
        
        paginator = Paginator(packages, 20)
        page_packages = paginator.get_page(page_number)

        
        context['page'] = page_number
        context['search'] = search_value
        context['packages'] = page_packages
        context['manufacturer'] = PackageManufacturers.objects.all().order_by('name')
        context['active_pharmacy'] = staff_user.selected_pharmacy

    return render(request, 'dashboard/packages_stock.html', context)

@check_staff_user
def dashboard_imports(request):
    """ Dashboard Bestellungen """
    
    context = {}

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:
        create_log(
            reference='dashboard_imports',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    return render(request, 'dashboard/products/imports.html', context)

@check_staff_user
def dashboard_products_all(request):
    """ Dashboard Produkte """
    
    context = {}

    products = Products.objects.filter()

    if request.method == 'GET':
        

        # Seite
        page_number = request.GET.get('page', 1)

        # Suche
        search_value = request.GET.get('search', '')

        products = dashboard_filter_products(request.GET)

        cancellation_reasons = CancellationReasons.objects.all()
        
        paginator = Paginator(products, 20)
        page_products = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['search'] = search_value
        context['products'] = page_products

    return render(request, 'dashboard/products/index.html', context)

@check_staff_user
def dashboard_product_requests(request):
    """ Dashboard Produktanfragen """

    context = {}

    product_requests = ProductRequest.objects.all().order_by('-id')

    if request.method == 'POST':

        data = {}

        if 'changeStatus' in request. POST:

            product_request_id = request.POST.get('productRequestId')
            status_name = request.POST.get('statusName')
            new_status = request.POST.get('newStatus')
            closingReason = request.POST.get('cancellationReasonValue')

            # Get order by id
            product_request = ProductRequest.objects.get(id=product_request_id)

            # Old status for comparison
            old_status = getattr(product_request, status_name)

            # Set status by status name
            if old_status not in ['approved', 'rejected']:
                
                setattr(product_request, status_name, new_status)
                product_request.save()
                
                # Create log entry
                log_entry = {
                    'reference': f'Produktanfrage ID: { product_request_id }',
                    'message': f'Produktanfrage aktualisiert. {old_status}: {new_status}',
                    'user': f'({ request.user.id }) { request.user.username }'
                }
                create_log(**log_entry)
            
            data['newStatusDisplay'] = getattr(product_request, f'get_{status_name}_display')()
            data['newStatus'] = getattr(product_request, status_name)

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'approveProductRequest' in request.POST:

            product_request_id = request.POST.get('productRequestId')
            available_until_date = request.POST.get('availableUntilDate')
            available_until_date = datetime.strptime(available_until_date, '%d.%m.%Y')

            # Get order by id
            product_request = ProductRequest.objects.get(id=product_request_id)

            # Set new status
            product_request.status = 'approved'
            product_request.available_until = available_until_date
            product_request.save()

            # Send mail
            send_product_request_approval(request, product_request)

            # Create log entry
            log_entry = {
                'reference': f'Produktanfrage ID: { product_request_id }',
                'message': 'Produktanfrage bestätigt.',
                'user': f'({ request.user.id }) { request.user.username }'
            }
            create_log(**log_entry)

            data['statusDisplay'] = product_request.get_status_display()
            data['status'] = product_request.status
            data['availableUntil'] = available_until_date.strftime('%d.%m.%Y')

            return HttpResponse(json.dumps(data), content_type='application/json')

        if 'rejectProductRequest' in request.POST:

            product_request_id = request.POST.get('productRequestId')
            reject_reason = request.POST.get('rejectReason')

            # Get order by id
            product_request = ProductRequest.objects.get(id=product_request_id)

            # Set new status
            product_request.status = 'rejected'
            product_request.reject_reason = reject_reason
            product_request.save()

            # Send mail
            send_product_request_rejection(product_request)

            # Create log entry
            log_entry = {
                'reference': f'Produktanfrage ID: { product_request_id }',
                'message': 'Produktanfrage abgelehnt.',
                'user': f'({ request.user.id }) { request.user.username }'
            }
            create_log(**log_entry)

            data['statusDisplay'] = product_request.get_status_display()
            data['status'] = product_request.status
            data['rejectReasonDisplay'] = product_request.get_reject_reason_display()

            return HttpResponse(json.dumps(data), content_type='application/json')

    context['product_requests'] = product_requests
    context['product_requests_dic'] = [product_request.id for product_request in product_requests]

    return render(request, 'dashboard/product_requests.html', context)

@check_staff_user
def dashboard_get_data(request):
    """ Dashboard Analytics Data """

    context = {}

    # Ausgeführte Bestellungen
    completed_orders = Orders.objects.filter(status='delivered')

    # Bezahlte Bestellungen (ausgeführt, bezahlt)
    payed_orders = completed_orders.filter(payment_status='received')

    # Offene Bestellungen (ausgeführt, unbezahlt)
    open_orders = completed_orders.filter(~Q(payment_status='received'))

    # Stornierte Bestellungen
    cancelled_orders = Orders.objects.filter(status='cancelled')


    # Datenextraktion für Bestellungen
    orders_per_week = completed_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time')
    ).values('year', 'week').annotate(total=Count('id')).order_by('year', 'week')

    if orders_per_week:
        orders_per_week = fill_week_gaps(orders_per_week)

    orders_per_month = completed_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

    if orders_per_month:
        orders_per_month = fill_month_gaps(orders_per_month)


    # Datenextraktion für offene Bestellungen
    open_orders_per_week = open_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time')
    ).values('year', 'week').annotate(total=Count('id')).order_by('year', 'week')

    if open_orders_per_week:
        open_orders_per_week = fill_week_gaps(open_orders_per_week)

    open_orders_per_month = open_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

    if open_orders_per_month:
        open_orders_per_month = fill_month_gaps(open_orders_per_month)



    # Datenextraktion für bezahlte Bestellungen
    payed_orders_per_week = payed_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time')
    ).values('year', 'week').annotate(total=Count('id')).order_by('year', 'week')

    if payed_orders_per_week:
        payed_orders_per_week = fill_week_gaps(payed_orders_per_week)

    payed_orders_per_month = payed_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

    if payed_orders_per_month:
        payed_orders_per_month = fill_month_gaps(payed_orders_per_month)



    # Datenextraktion für stornierte Bestellungen
    cancelled_orders_per_week = cancelled_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time')
    ).values('year', 'week').annotate(total=Count('id')).order_by('year', 'week')

    if cancelled_orders_per_week:
        cancelled_orders_per_week = fill_week_gaps(cancelled_orders_per_week)

    cancelled_orders_per_month = cancelled_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Count('id')).order_by('year', 'month')

    if cancelled_orders_per_month:
        cancelled_orders_per_month = fill_month_gaps(cancelled_orders_per_month)



    # Datenextraktion für Gesamtumsatz (netto)
    total_revenue_per_week = completed_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time'),
    ).values('year', 'week').annotate(total=Sum('subtotal')).order_by('year', 'week')

    if total_revenue_per_week:
        total_revenue_per_week = fill_week_gaps(total_revenue_per_week)

    total_revenue_per_month = completed_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Sum('subtotal')).order_by('year', 'month')

    if total_revenue_per_month:
        total_revenue_per_month = fill_month_gaps(total_revenue_per_month)



    # Datenextraktion für Gesamtumsatz (bezahlt, netto)
    payed_revenue_per_week = payed_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time'),
    ).values('year', 'week').annotate(total=Sum('subtotal')).order_by('year', 'week')

    if payed_revenue_per_week:
        payed_revenue_per_week = fill_week_gaps(payed_revenue_per_week)

    payed_revenue_per_month = payed_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Sum('subtotal')).order_by('year', 'month')

    if payed_revenue_per_month:
        payed_revenue_per_month = fill_month_gaps(payed_revenue_per_month)



    # Datenextraktion für Gesamtumsatz (offen, netto)
    open_revenue_per_week = open_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time'),
    ).values('year', 'week').annotate(total=Sum('subtotal')).order_by('year', 'week')

    if open_revenue_per_week:
        open_revenue_per_week = fill_week_gaps(open_revenue_per_week)

    open_revenue_per_month = open_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Sum('subtotal')).order_by('year', 'month')

    if open_revenue_per_month:
        open_revenue_per_month = fill_month_gaps(open_revenue_per_month)



    # Datenextraktion für Gesamtumsatz (storniert, netto)
    cancelled_revenue_per_week = cancelled_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time'),
    ).values('year', 'week').annotate(total=Sum('subtotal')).order_by('year', 'week')

    if cancelled_revenue_per_week:
        cancelled_revenue_per_week = fill_week_gaps(cancelled_revenue_per_week)

    cancelled_revenue_per_month = cancelled_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Sum('subtotal')).order_by('year', 'month')

    if cancelled_revenue_per_month:
        cancelled_revenue_per_month = fill_month_gaps(cancelled_revenue_per_month)

    
    
    fourteen_days_ago = timezone.now() - timedelta(days=14)

    # Datenextraktion für Gesamtumsatz (gefordert, netto)
    demanded_revenue_per_week = Orders.objects.filter(
        status='ordered', 
        order_time__lt=fourteen_days_ago
    ).exclude(
        Q(payment_status='received') | Q(payment_status='pending')
    ).annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time'),
    ).values('year', 'week').annotate(total=Sum('subtotal')).order_by('year', 'week')

    if demanded_revenue_per_week:
        demanded_revenue_per_week = fill_week_gaps(demanded_revenue_per_week)

    demanded_revenue_per_month = Orders.objects.filter(
        status='ordered', 
        order_time__lt=fourteen_days_ago
    ).exclude(
        Q(payment_status='received') | Q(payment_status='pending')
    ).annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time'),
    ).values('year', 'month').annotate(total=Sum('subtotal')).order_by('year', 'month')

    if demanded_revenue_per_month:
        demanded_revenue_per_month = fill_month_gaps(demanded_revenue_per_month)


    # Datenextraktio für die durchschnittliche Gesamthöhe einer Bestellung (netto, bestellt)
    average_revenue_per_week = completed_orders.annotate(
        year=ExtractYear('order_time'),
        week=ExtractWeek('order_time')
    ).values('year', 'week').annotate(total=Avg('subtotal')).order_by('year', 'week')

    if average_revenue_per_week:
        average_revenue_per_week = fill_week_gaps(average_revenue_per_week)

    average_revenue_per_month = completed_orders.annotate(
        year=ExtractYear('order_time'),
        month=ExtractMonth('order_time')
    ).values('year', 'month').annotate(total=Avg('subtotal')).order_by('year', 'month')

    if average_revenue_per_month:
        average_revenue_per_month = fill_month_gaps(average_revenue_per_month)



    # Datenextraktio für die gesamte verkaufte Menge in g
    amount_gramm_per_week = OrderProducts.objects.filter(order__status='delivered').annotate(
        year=ExtractYear('order__order_time'),
        week=ExtractWeek('order__order_time')
    ).values('year', 'week').annotate(total=Sum('amount')).order_by('year', 'week')

    if amount_gramm_per_week:
        amount_gramm_per_week = fill_week_gaps(amount_gramm_per_week)

    amount_gramm_per_month = OrderProducts.objects.filter(order__status='delivered').annotate(
        year=ExtractYear('order__order_time'),
        month=ExtractMonth('order__order_time')
    ).values('year', 'month').annotate(total=Sum('amount')).order_by('year', 'month')

    if amount_gramm_per_month:
        amount_gramm_per_month = fill_month_gaps(amount_gramm_per_month)



    # Datenextraktion für den Durchschnittspreis pro Gramm
    average_price_per_gramm_per_week = OrderProducts.objects.filter(order__status='delivered').annotate(
        year=ExtractYear('order__order_time'),
        week=ExtractWeek('order__order_time')
    ).values('product__name', 'year', 'week').annotate(total=Avg('product__pirce_per_unit')).order_by('product__name', 'year', 'week')

    if average_price_per_gramm_per_week:
        average_price_per_gramm_per_week = fill_week_gaps(average_price_per_gramm_per_week)

    average_price_per_gramm_per_month = OrderProducts.objects.filter(order__status='delivered').annotate(
        year=ExtractYear('order__order_time'),
        month=ExtractMonth('order__order_time')
    ).values('product__name', 'year', 'month').annotate(total=Avg('product__pirce_per_unit')).order_by('product__name', 'year', 'month')

    if average_price_per_gramm_per_month:
        average_price_per_gramm_per_month = fill_month_gaps(average_price_per_gramm_per_month)

    # KPI 1
    def get_orders_by_status(status_list):
        return Orders.objects.filter(
            order_time__week=timezone.now().isocalendar()[1],
            order_time__year=timezone.now().year,
            status__in=status_list
        ).count()

    # Define the status lists for each category
    status_open = ['started', 'ordered']
    status_processing = ['process', 'queries', 'clarified']
    status_delivered = ['ready_to_ship', 'ready_for_pickup', 'shipped', 'delivered']
    status_cancelled = ['cancelled']

    # Retrieve orders for the current week based on status
    current_week_orders = [
        get_orders_by_status(status_open),           # Open orders
        get_orders_by_status(status_processing),     # Orders i nprocess
        get_orders_by_status(status_delivered),      # Delivered orders
        get_orders_by_status(status_cancelled)       # Cancelled orders
    ]    

    # KPI 2
    # Group completed orders by date and calculate the total revenue for each date
    
    today = timezone.now().date()


    daily_revenues = completed_orders.annotate(
        date=TruncDate('order_time')
    ).values('order_time').annotate(
        total_revenue=Sum('subtotal')
    ).order_by('order_time')

    # Aggregate to find min, max, and average of the total revenues
    revenue_stats = daily_revenues.aggregate(
        MinRevenue=Min('total_revenue'),
        MaxRevenue=Max('total_revenue'),
        AvgRevenue=Avg('total_revenue')
    )

    # Calculate today's revenue by filtering the daily_revenues query
    todays_revenue = daily_revenues.filter(date=today).aggregate(
        TodayRevenue=Sum('total_revenue')
    )['TodayRevenue'] or 0

    # Check if there is any revenue today, if none, set to 0
    revenue_stats['TodayRevenue'] = todays_revenue or 0



    # Group completed orders by date and calculate the total amount for each date
    daily_amounts = completed_orders.annotate(
        data=TruncDate('order_time')
    ).values('order_time').annotate(
        total_amount=Sum('order_products__amount')
    ).order_by('order_time')

    amount_stats = daily_amounts.aggregate(
        MinAmount=Min('total_amount'),
        MaxAmount=Max('total_amount'),
        AvgAmount=Avg('total_amount')
    )

    # Filter daily_amounts for today and aggregate today's total amount
    todays_amount_data = daily_amounts.filter(order_time=today).aggregate(
        TodayAmount=Sum('total_amount')
    )

    # Since the aggregate might return None if there are no records, handle this case
    amount_stats['TodayAmount'] = todays_amount_data['TodayAmount'] or 0
    # todays_amount = todays_amount_data['TodayAmount'] or 0


    # Group amount of orders by data and calculate the total amount of orders for each date
    daily_orders = completed_orders.annotate(
        date=TruncDate('order_time')
    ).values('order_time').annotate(
        total_orders=Count('id')
    ).order_by('order_time')

    # Aggregate to find min, max, and average of the total orders
    order_stats = daily_orders.aggregate(
        MinOrders=Min('total_orders'),
        MaxOrders=Max('total_orders'),
        AvgOrders=Avg('total_orders')
    )

    # Filter daily_orders for today and aggregate today's total orders
    todays_order_data = daily_orders.filter(order_time=today).aggregate(
        TodayOrders=Count('id')
    )

    order_stats['TodayOrders'] = todays_order_data['TodayOrders'] or 0


    # Kombinieren der Daten in einem Dictionary
    data = {
        'orders_per_week': list(orders_per_week),
        'orders_per_month': list(orders_per_month),
        'payed_orders_per_week': list(payed_orders_per_week),
        'payed_orders_per_month': list(payed_orders_per_month),
        'open_orders_per_week': list(open_orders_per_week),
        'open_orders_per_month': list(open_orders_per_month),
        'cancelled_orders_per_week': list(cancelled_orders_per_week),
        'cancelled_orders_per_month': list(cancelled_orders_per_month),
        'total_revenue_per_week': list(total_revenue_per_week),
        'total_revenue_per_month': list(total_revenue_per_month),
        'payed_revenue_per_week': list(payed_revenue_per_week),
        'payed_revenue_per_month': list(payed_revenue_per_month),
        'open_revenue_per_week': list(open_revenue_per_week),
        'open_revenue_per_month': list(open_revenue_per_month),
        'cancelled_revenue_per_week': list(cancelled_revenue_per_week),
        'cancelled_revenue_per_month': list(cancelled_revenue_per_month),
        'demanded_revenue_per_week': list(demanded_revenue_per_week),
        'demanded_revenue_per_month': list(demanded_revenue_per_month),
        'average_revenue_per_week': list(average_revenue_per_week),
        'average_revenue_per_month': list(average_revenue_per_month),
        'average_price_per_gramm_per_week': list(average_price_per_gramm_per_week),
        'average_price_per_gramm_per_month': list(average_price_per_gramm_per_month),
        'amount_gramm_per_month': list(amount_gramm_per_month),
        'amount_gramm_per_week': list(amount_gramm_per_week),
        'current_week_orders': list(current_week_orders),
        'revenue_stats': revenue_stats,
        'amount_stats': amount_stats,
        'order_stats': order_stats,
    }

    return JsonResponse(data)

@check_staff_user
def dashboard_customers(request):
    """ Kunden """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_review_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)
    
    context = {}

    customers = Customers.objects.all()

    if request.method == 'GET':
        
        # Seite
        page_number = request.GET.get('page', 1)

        customers = dashboard_filter_customers(request.GET, staff_user.selected_pharmacy)
        
        paginator = Paginator(customers, 20)
        page_customers = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['customers'] = page_customers

    context['selected_pharmacy_id'] = staff_user.selected_pharmacy.id

    return render(request, 'dashboard/customers.html', context)

@check_staff_user
def dashboard_users(request):
    """ Benutzer """

    if request.method == 'GET':

        # Get pharmacy premissons if not superuser
        if not request.user.is_superuser:
            pharmacy_premissions = UserPremissions.objects.filter(user=request.user, view='dashboard_users').values_list('pharmacy', flat=True).distinct()
            pharmacy_users = UserPremissions.objects.filter(pharmacy__in=pharmacy_premissions, user__is_superuser=False).values_list('user', flat=True).distinct()
        else:
            pharmacy_users = UserPremissions.objects.all().values_list('user', flat=True).distinct()

        context = {}

        users = User.objects.filter(id__in=pharmacy_users, is_staff=True).order_by('-date_joined')
        
        # Seite
        page_number = request.GET.get('page', 1)

        # users = dashboard_filter_users(request.GET)
        
        paginator = Paginator(users, 20)
        page_users = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['users'] = page_users

    return render(request, 'dashboard/users.html', context)

@check_staff_user
def dashboard_email_recipients(request):
    """ E-Mail Empfänger """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:

        create_log(
            reference='dashboard_orders',
            message='StaffUser not found',
            user=f'({ request.user.id }) { request.user.username }',
            category='error',
        )

        return redirect(home)

    context = {}

    recipients = EmailRecipients.objects.all()
    pharmacies = Pharmacies.objects.all()

    if request.method == 'GET':
            
        # Seite
        page_number = request.GET.get('page', 1)

        recipients = dashboard_filter_email_recipients(request.GET, staff_user.selected_pharmacy)
        
        paginator = Paginator(recipients, 20)
        page_recipients = paginator.get_page(page_number)
        
        context['page'] = page_number
        context['recipients'] = page_recipients
        context['pharmacies'] = pharmacies

    return render(request, 'dashboard/email_recipients.html', context)
