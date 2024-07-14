import locale
import os
import codecs

from django import template
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Min, Max, F, Value, CharField
from django.db.models.functions import Concat

from app import choices
from app.models import MainSettings, Orders, OrderProducts, ProductImages,\
                    UserPremissions, OrderRecipes, CannabisIndications,\
                    CannabisEffects, Products, Terpene,PagesMetaDatas, CannabisBlog,\
                    ProductRequest, StockProducts, ProductOrders, Invoices, Pharmacies, \
                    StaffUser
from app.utils import count_notifications, count_product_request_notifications, check_min_order_amount, sum_product_stock_ordered_amount, sum_product_ordered_amount


locale.setlocale(locale.LC_ALL, '')

register = template.Library()

@register.filter
def tround(value, digits):
    """ Round value by digits """

    if digits == 0:
        value = round(value)
    else:
        value = round(value, digits)

    return value

@register.filter
def tsplit(string, key):
    """ Split String by key """

    return list(filter(None, string.split(key)))

@register.filter
def trange(value):
    """ Create range """

    return range(value)

@register.filter
def tarray_element(array, key):
    """ Get Arrayelement by key """

    if len(array) != 0:
        return array[key - 1]
    
    return None

@register.filter
def to_euro_decimal(number):
    """ Get Arrayelent by key """

    number = locale.format_string('%.2f', number, True) if number or number == 0 else '--'

    return number

@register.filter
def to_percentage(value):
    """ Format value to percentage """
    return '{:.2%}'.format(round(value, 2)).replace('.', ',')

@register.filter
def to_percentage_value(value):
    """ Format value to percentage """

    value = value if value else 0

    return '{:.0%}'.format(round(value, 2)).replace('.', ',')

@register.filter
def calculate_percentage_value(value):
    """ Format value to percentage """

    value = round(value * 1, 2) if value else 0

    return '{:.0%}'.format(value).replace('.', ',')

@register.filter
def to_string(value):
    """ Convert to string """
    return str(value)

@register.filter
def read_html_file(html_field):
    """ Rad html file """
    html_path = html_field.path
    if os.path.exists(html_path):
        html_string = codecs.open(html_path, 'r').read()
        return mark_safe(html_string)
    return None

@register.simple_tag
def get_choices(name):
    """ Get schoices by name """

    return getattr(choices, name, [])

@register.simple_tag
def get_order(order_id):
    """ Get order by order id """

    if order_id:

        try:
            order = Orders.objects.get(id=order_id)
        except ObjectDoesNotExist:
            order = None

    return order

@register.filter
def get_min_order_amount(order):
    """ Get order min amount status """

    if order:
        return check_min_order_amount(order)
    
    return False

@register.filter
def get_order_products(order):
    """ Get order products form order """

    if order:
        return OrderProducts.objects.filter(order=order)
    
    return []

@register.filter
def get_invoices_by_order(order):
    """ Get invoices by order """

    return Invoices.objects.filter(order=order, cancellation_invoice=False).order_by('-id')

@register.filter
def get_main_image(product):
    """ Get Main image url """
    return \
        ProductImages.objects.filter(product=product, main_image=True).first().img.url \
        if ProductImages.objects.filter(product=product, main_image=True) \
        else ''

@register.filter
def get_product_images(product):
    """ Get Main image url """
    return  ProductImages.objects.filter(product=product)

@register.filter
def list_all_values(array, value):
    """ List all by value """
    return ', '.join(list(array.values_list(value, flat=True)))

@register.filter
def premission_check(user, view_names):
    """ Check user premission for dashboard """

    # Superuser has always the premission
    if user.is_superuser:
        return True

    # Get user premissions
    if 'dashboard_users' in view_names:
        premissions = list(UserPremissions.objects.filter(user=user, read_premission=True).values_list('view', flat=True))
    else:
        staff_user = StaffUser.objects.get(user=user)
        premissions = list(UserPremissions.objects.filter(user=user, read_premission=True, pharmacy=staff_user.selected_pharmacy).values_list('view', flat=True))

    # Check premission based on view_name
    for view_name in view_names.split(';'):
        if view_name in premissions:
            return True

    return False

@register.filter
def get_recipes(order):
    """ Get recipes by order """

    return OrderRecipes.objects.filter(order=order)

@register.simple_tag
def get_orders_amount(request_user):
    """ Get amount of Orders """

    staff_user = StaffUser.objects.get(user=request_user)

    return Orders.objects.filter(ordered=True, pharmacy=staff_user.selected_pharmacy).exclude(status='in_review').count()

@register.simple_tag
def get_orders_in_review():
    """ Get amount of Orders in status in_review """

    return Orders.objects.filter(status='in_review').count()

@register.simple_tag
def get_order_products_amount(request_user):
    """ Get amount of ordered producgts """

    staff_user = StaffUser.objects.get(user=request_user)

    return OrderProducts.objects.filter(order__ordered=True, order__pharmacy=staff_user.selected_pharmacy).count()

@register.simple_tag
def get_total_product_stock_amount(request_user):
    """ Get amount of total product stock """

    staff_user = StaffUser.objects.get(user=request_user)

    return StockProducts.objects.filter(pharmacy=staff_user.selected_pharmacy).aggregate(total=Sum('amount'))['total']

@register.filter
def get_product_stock_ordered_amount(stock_product, pharmacy):
    """ Get amount of ordered product """
    return sum_product_stock_ordered_amount(stock_product, pharmacy)

@register.filter
def get_product_ordered_amount(product, pharmacy):
    """ Get amount of ordered product """
    return sum_product_ordered_amount(product, pharmacy)

@register.filter
def get_customers_orders_amount(customer):
    """ Get amount of orders by customer """
    return Orders.objects.filter(customer=customer, ordered=True).count()

@register.simple_tag
def get_open_product_requests_amount():
    """ Get amount of Product Requests """

    return ProductRequest.objects.exclude(status='closed').count()

@register.simple_tag
def get_prepaid_envelope():
    """ Get prepaid envelope url """

    if MainSettings.objects.first() and MainSettings.objects.first().prepaid_envelope:
        return MainSettings.objects.first().prepaid_envelope.url
    
    return None

@register.simple_tag
def get_allindications():
    """ Get all indications """
    return CannabisIndications.objects.filter(active=True)

@register.simple_tag
def get_sidebar_indications():
    """ Get sidebar indications """
    return CannabisIndications.objects.exclude(teaser='').exclude(image='').filter(active=True).order_by('?')[:4]

@register.simple_tag
def get_sidebar_effects():
    """ Get sidebar effects """
    return CannabisEffects.objects.exclude(teaser='').exclude(image='').filter(active=True).order_by('?')[:4]

@register.simple_tag
def get_cannabis_blocks():
    """ Get cannabis blocks """
    return CannabisBlog.objects.exclude(teaser='').exclude(block_image='').order_by('?')

@register.simple_tag
def get_alleffects():
    """ Get all effects """
    return CannabisEffects.objects.all()

@register.filter
def get_main_product_img(product):
    """ Get main product image """

    try:
        img = ProductImages.objects.get(product=product, main_image=True).img.url
    except Exception:
        img = '../../../static/app/img/ExampleProduct.png'

    return img

@register.filter
def get_matching_products(cannabis_indication):
    """ Get matching products """

    if cannabis_indication.indication:
    
        terpene_ids = Terpene.objects.filter(indications__id=cannabis_indication.indication.id).values_list('id', flat=True)

        similar_products = Products.objects.filter(main_terpene__id__in=terpene_ids).order_by('-status')[:15]

    else:
        similar_products = []

    return similar_products

@register.filter
def get_effect_content_name(item):
    """ Get effect content name """

    try:
        return CannabisEffects.objects.get(terpene_effects=item).name
    except ObjectDoesNotExist:
        return None
    
@register.filter
def get_effect_url_name(item):
    """ Get effect url name """

    try:
        return CannabisEffects.objects.get(terpene_effects=item).url_name
    except ObjectDoesNotExist:
        return None

@register.filter
def get_indication_content_name(item):
    """ Get effect content name """

    try:
        return CannabisIndications.objects.get(indication=item).name
    except ObjectDoesNotExist:
        return None

@register.filter
def get_indication_url_name(item):
    """ Get indication url name """

    try:
        return CannabisIndications.objects.get(indication=item).url_name
    except ObjectDoesNotExist:
        return None

@register.simple_tag
def get_meta_datas(url_name):
    """ Get meta datas from backend by url name """

    try:
        meta_datas = PagesMetaDatas.objects.get(page=url_name)
    except ObjectDoesNotExist:
        meta_datas = PagesMetaDatas.objects.get(page='for_all')

    return meta_datas

@register.filter
def add_get_parameter(query_string, arguments):
    """ Add argument to get parameters """

    q = QueryDict('', mutable=True)
    q.update(query_string.dict())

    for argument in arguments.split(';'):

        key, value = argument.split(':')

        q[key] = value

    return q.urlencode()

@register.filter
def concat_string(string1, string2):
    """ Concat to strings """
    return str(string1) + str(string2)

@register.filter
def get_page_range(page_range, current_page):
    """ Get range from current page """

    return page_range[max(0, page_range.index(current_page) - 2) : min(len(page_range), page_range.index(current_page) + 3)]

@register.filter
def set_opacity_color(hex_color, opacity):
    """ Set hey color with opcity to rgba """

    # Hex to rgba
    hex_color = hex_color.lstrip('#')
    hex_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Rgb with opacity
    r, g, b = hex_color

    return (r, g, b, opacity)

@register.simple_tag
def get_approved_product_requests(user):
    """ Get approved product requests """

    product_reqeusts = ProductRequest.objects.filter(customer__user=user, status='approved', ordered=False, declined=False)

    requests = []

    for product_reqeust in product_reqeusts:

        requests.append({
            'id': product_reqeust.id,
            'name': product_reqeust.product.name,
            'amount': f'{ product_reqeust.amount } { "g" if product_reqeust.product.form == "flower" else "ml" }',
        })

    return requests

@register.filter
def request_in_cart(product_request, order_id):
    """ Check if prodcut_request is in current cart """

    if order_id:
        order = Orders.objects.get(id=order_id)

        try:
            order_product = OrderProducts.objects.get(order=order, requested_product=product_request)
        except:
            return False
        
        return True
    
    return False

@register.simple_tag
def get_total_notificatinos_amount(user):
    """ Get amount of total notifications """
    return count_notifications(user)

@register.simple_tag
def get_approved_product_requests(user):
    """ Get amount of total notifications """
    return count_product_request_notifications(user)

@register.simple_tag
def get_best_price_products():
    """ Get best price products for modal """

    products = Products.objects.filter(active=True).order_by('-special_offer', '-status', 'self_payer_selling_price_brutto')[:3]

    return products

@register.simple_tag
def get_high_thc_products():
    """ Get best price products for modal """

    products = Products.objects.filter(active=True).order_by('-status', '-thc_value')[:3]

    return products

@register.simple_tag
# Bestimmung des frühesten und spätesten Jahres und der jeweiligen Wochen
def fill_week_gaps(orders_query_set):
        
        # if not orders_query_set:
        #     return {}
        
        date_range = orders_query_set.aggregate(
            earliest_year=Min('year'),
            latest_year=Max('year')
        )

        earliest_year = date_range['earliest_year']
        latest_year = date_range['latest_year']
        earliest_week = orders_query_set.filter(year=earliest_year).aggregate(earliest_week=Min('week'))['earliest_week']
        latest_week_in_latest_year = orders_query_set.filter(year=latest_year).aggregate(latest_week=Max('week'))['latest_week']

        filled_orders = []
        week_data = {(order['year'], order['week']): order for order in orders_query_set}

        for year in range(earliest_year, latest_year + 1):
            start_week = earliest_week if year == earliest_year else 1
            end_week = latest_week_in_latest_year if year == latest_year else 52

            for week in range(start_week, end_week + 1):
                if (year, week) in week_data:
                    filled_orders.append(week_data[(year, week)])
                else:
                    filled_orders.append({'year': year, 'week': week, 'total': 0})

                # Stoppe die Schleife am Ende des vorhandenen Datensatzes
                if year == latest_year and week == latest_week_in_latest_year:
                    break


        filled_orders = [
            {'x': f'KW{revenue["week"]}', 'y': f'{revenue["total"]}'} 
            for revenue in filled_orders
        ]

        return filled_orders

@register.simple_tag
# Ermitteln des frühesten und spätesten Jahres und Monats
def fill_month_gaps(orders_query_set):
        date_range = orders_query_set.aggregate(
            earliest_year=Min('year'),
            latest_year=Max('year')
        )

        earliest_year = date_range['earliest_year']
        latest_year = date_range['latest_year']

        # Ermitteln des frühesten Monats im frühesten Jahr
        earliest_month = orders_query_set.filter(
            year=earliest_year
        ).aggregate(earliest_month=Min('month'))['earliest_month']

        # Ermitteln des spätesten Monats im spätesten Jahr
        latest_month_in_latest_year = orders_query_set.filter(
            year=latest_year
        ).aggregate(latest_month=Max('month'))['latest_month']

        # Füllen der fehlenden Monate
        filled_orders = []
        month_data = {(order['year'], order['month']): order for order in orders_query_set}

        for year in range(earliest_year, latest_year + 1):
            start_month = earliest_month if year == earliest_year else 1
            end_month = latest_month_in_latest_year if year == latest_year else 12

            for month in range(start_month, end_month + 1):
                if (year, month) in month_data:
                    filled_orders.append(month_data[(year, month)])
                else:
                    filled_orders.append({'year': year, 'month': month, 'total': 0})

                # Stoppe die Schleife am Ende des vorhandenen Datensatzes
                if year == latest_year and month == latest_month_in_latest_year:
                    break

        filled_orders = [
            {'x': f'{order["month"]}', 'y': order['total']} 
            for order in filled_orders
        ]

        return filled_orders

@register.simple_tag
# Bestimmung des frühesten und spätesten Jahres und der jeweiligen Wochen
def fill_week_gaps(orders_query_set):
        
        # if not orders_query_set:
        #     return {}
        
        date_range = orders_query_set.aggregate(
            earliest_year=Min('year'),
            latest_year=Max('year')
        )

        earliest_year = date_range['earliest_year']
        latest_year = date_range['latest_year']
        earliest_week = orders_query_set.filter(year=earliest_year).aggregate(earliest_week=Min('week'))['earliest_week']
        latest_week_in_latest_year = orders_query_set.filter(year=latest_year).aggregate(latest_week=Max('week'))['latest_week']

        filled_orders = []
        week_data = {(order['year'], order['week']): order for order in orders_query_set}

        for year in range(earliest_year, latest_year + 1):
            start_week = earliest_week if year == earliest_year else 1
            end_week = latest_week_in_latest_year if year == latest_year else 52

            for week in range(start_week, end_week + 1):
                if (year, week) in week_data:
                    filled_orders.append(week_data[(year, week)])
                else:
                    filled_orders.append({'year': year, 'week': week, 'total': 0})

                # Stoppe die Schleife am Ende des vorhandenen Datensatzes
                if year == latest_year and week == latest_week_in_latest_year:
                    break


        filled_orders = [
            {'x': f'KW{revenue["week"]}', 'y': f'{revenue["total"]}'} 
            for revenue in filled_orders
        ]

        return filled_orders

@register.simple_tag
# Ermitteln des frühesten und spätesten Jahres und Monats
def fill_month_gaps(orders_query_set):
        date_range = orders_query_set.aggregate(
            earliest_year=Min('year'),
            latest_year=Max('year')
        )

        earliest_year = date_range['earliest_year']
        latest_year = date_range['latest_year']

        # Ermitteln des frühesten Monats im frühesten Jahr
        earliest_month = orders_query_set.filter(
            year=earliest_year
        ).aggregate(earliest_month=Min('month'))['earliest_month']

        # Ermitteln des spätesten Monats im spätesten Jahr
        latest_month_in_latest_year = orders_query_set.filter(
            year=latest_year
        ).aggregate(latest_month=Max('month'))['latest_month']

        # Füllen der fehlenden Monate
        filled_orders = []
        month_data = {(order['year'], order['month']): order for order in orders_query_set}

        for year in range(earliest_year, latest_year + 1):
            start_month = earliest_month if year == earliest_year else 1
            end_month = latest_month_in_latest_year if year == latest_year else 12

            for month in range(start_month, end_month + 1):
                if (year, month) in month_data:
                    filled_orders.append(month_data[(year, month)])
                else:
                    filled_orders.append({'year': year, 'month': month, 'total': 0})

                # Stoppe die Schleife am Ende des vorhandenen Datensatzes
                if year == latest_year and month == latest_month_in_latest_year:
                    break

        filled_orders = [
            {'x': f'{order["month"]}', 'y': order['total']} 
            for order in filled_orders
        ]

        return filled_orders

@register.filter
def get_parameter(request, key):
    """ Get parameter from request """
    
    return request.GET.get(key, '')

@register.filter
def check_get_parameters_exist(request, keys):
    """ Check if get parameters exist """

    for key in keys.split(';'):
        if request.GET.get(key, ''):
            return True
    
    return False

@register.simple_tag
def check_get_parameter(request, key, value):
    """ Check if key with value esists in get parameters """
    
    return 'checked' if value in request.GET.get(key, '').split(',') else ''

@register.filter
def get_userrights(user):
    """ Get user rights """

    # view_order = {view[0]: index for index, view in enumerate(choices.DashboardViewsChoices)}

    # Get all userpremissions group by view without read premission and write premission and pharmacy
    user_rights = UserPremissions.objects.filter(user=user).annotate(
        view_display=Value('', output_field=CharField())
    ).values('view', 'view_display').distinct()

    for permission in user_rights:
        permission['view_display'] = dict(choices.DashboardViewsChoices).get(permission['view'], permission['view'])

    return user_rights

@register.filter
def get_all_livestock_entries(livestock_product, request):
    """ Get all entries of livestock product """

    try:
        staff_user = StaffUser.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return []

    if livestock_product:
        return StockProducts.objects.filter(product=livestock_product, pharmacy=staff_user.selected_pharmacy)
    
    return []    

@register.filter
def get_pharmacyrights(user, request_user):
    """ Get pharmacy rights """

    if request_user.is_superuser:
        return Pharmacies.objects.all()

    pharmacy_premissions = UserPremissions.objects.filter(user=request_user, view='dashboard_users').values_list('pharmacy', flat=True).distinct()
    user_premissions = UserPremissions.objects.filter(user=user, pharmacy__in=pharmacy_premissions).values_list('pharmacy', flat=True)

    pharmacies = Pharmacies.objects.filter(id__in=user_premissions)

    return pharmacies

@register.simple_tag
def get_read_premission(user, view, pharmacy):
    """ Get read premission """

    try:
        return UserPremissions.objects.get(user=user, view=view, pharmacy=pharmacy).read_premission
    except ObjectDoesNotExist:
        pass

    return False

@register.simple_tag
def get_write_premission(user, view, pharmacy):
    """ Get read premission """

    try:
        return UserPremissions.objects.get(user=user, view=view, pharmacy=pharmacy).write_premission
    except ObjectDoesNotExist:
        pass

    return False

@register.simple_tag
def get_premission_pharmacies(user):
    """ Get premission pharmacies """

    if user.is_superuser:
        return Pharmacies.objects.all()

    pharmacies_ids = list(UserPremissions.objects.filter(user=user).values_list('pharmacy', flat=True))

    return Pharmacies.objects.filter(id__in=pharmacies_ids)

@register.filter
def get_selected_pharmacy(user):
    """ Get last selected pharmacy """

    try:
        pharamcy = StaffUser.objects.get(user=user).selected_pharmacy
        return f'{pharamcy.name} - {pharamcy.city}'
    except ObjectDoesNotExist:
        return None

@register.filter
def delivery_type_check_activated(delivery_type, pharmacy):
    """ Check if delivery type is activated """

    if delivery_type == 'dhl_standard':
        return pharmacy.dhl_active
    elif delivery_type == 'go_express':
        return pharmacy.go_express_active
    
    return True
