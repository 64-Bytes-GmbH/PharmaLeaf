""" Admin page - register models """
import locale

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.base import ModelBase
from django.utils.html import format_html
from django.core.mail import send_mail, get_connection
from admin_extra_buttons.api import ExtraButtonsMixin, button
from rangefilter.filters import DateRangeFilterBuilder
from app import models
from .models import Terpene, Products, FAQs, CannabisIndications,\
                    CannabisEffects, Indications, Cultivar,\
                    Manufacturer, Customers, Orders, Flavors, \
                    OrderProducts, Invoices, Logger, ProductImages, EmailSettings,\
                    OrderRecipes, StockProducts, Pharmacies, OpeningHours, PackagePickupTimes, \
                    StaffUser, UserPremissions, OrderRecipes, StockProducts, Pharmacies, IdentificationFiles,\
                    PackedOrderedProducts, StockProductsLogger, PackagesLogger, ProductPrices, EmailLogger
from .utils import export_effect_content, export_indications_content,\
                    export_order_products, create_new_invoice,\
                    send_payment_reminder, send_last_payment_reminder, \
                    send_overdue_mail, update_order_prices, check_for_payment_reminder,\
                    send_order_confirmation, send_invoice_to_customer, send_new_order_created, \
                    create_product_stock_items, export_orders, confirm_created_order, send_order_ready_for_pickup

locale.setlocale(locale.LC_ALL, '')

for model_name in dir(models):
    if model_name not in [
        'User',
        'Terpene',
        'Products',
        'ProductPrices',
        'StockProducts',
        'FAQs',
        'CannabisIndications',
        'CannabisEffects',
        'Indications',
        'Cultivar',
        'Manufacturer',
        'Customers',
        'Orders',
        'OrderRecipes',
        'OrderProducts',
        'Flavors',
        'Invoices',
        'Logger',
        'ProductImages',
        'EmailSettings',
        'OpeningHours',
        'PackagePickupTimes',
        'Pharmacies',
        'StaffUser',
        'UserPremissions',
        'IdentificationFiles',
        'PackedOrderedProducts',
        'StockProductsLogger',
        'PackagesLogger',
        'EmailLogger'
        ]:
        model = getattr(models, model_name)
        if isinstance(model, ModelBase):
            admin.site.register(model)

######## Admin functions ########
#pylint: disable=unused-argument
def _create_new_invoice(modeladmin, request, queryset):
    """ Create new invoice """
    for item in queryset:
        create_new_invoice(item.order)
_create_new_invoice.short_description = 'Neue Rechnung erstellen'

#pylint: disable=unused-argument
def _send_invoice_to_customer(modeladmin, request, queryset):
    """ Create new invoice """
    for item in queryset:
        send_invoice_to_customer(item.id, request)
_send_invoice_to_customer.short_description = 'Rechnung an Kunden senden'

#pylint: disable=unused-argument
def update_product_priority_to_4(modeladmin, request, queryset):
    """ Update to priority 4 """
    queryset.update(priority=4)
update_product_priority_to_4.short_description = 'Auf Priorität 4 setzen'

#pylint: disable=unused-argument
def update_product_priority_to_3(modeladmin, request, queryset):
    """ Update to priority 3 """
    queryset.update(priority=3)
update_product_priority_to_3.short_description = 'Auf Priorität 3 setzen'

#pylint: disable=unused-argument
def update_product_priority_to_2(modeladmin, request, queryset):
    """ Update to priority 2 """
    queryset.update(priority=2)
update_product_priority_to_2.short_description = 'Auf Priorität 2 setzen'

#pylint: disable=unused-argument
def update_product_priority_to_1(modeladmin, request, queryset):
    """ Update to priority 1 """
    queryset.update(priority=1)
update_product_priority_to_1.short_description = 'Auf Priorität 1 setzen'

#pylint: disable=unused-argument
def update_product_priority_to_0(modeladmin, request, queryset):
    """ Update to priority 0 """
    queryset.update(priority=0)
update_product_priority_to_0.short_description = 'Auf Priorität 0 setzen'

#pylint: disable=unused-argument
def update_product_special_price(modeladmin, request, queryset):
    """ Update special price """
    for item in queryset:
        if item.special_offer:
            item.special_offer = False
            item.save()
        else:
            item.special_offer = True
            item.save()
update_product_special_price.short_description = 'Spezieller Preis'

#pylint: disable=unused-argument
def set_product_in_active(modeladmin, request, queryset):
    """ Update product active """
    for item in queryset:
        if item.active:
            item.active = False
            item.save()
        else:
            item.active = True
            item.save()
set_product_in_active.short_description = 'Auf Aktiv/Inaktiv setzen'

#pylint: disable=unused-argument
def save_orders(modeladmin, request, queryset):
    """ Save orders """
    for item in queryset:
        item.save()
save_orders.short_description = 'Speichern'

#pylint: disable=unused-argument
def _send_new_order_created(modeladmin, request, queryset):
    """ Update orders """
    for item in queryset:
        send_new_order_created(item.id, request)
_send_new_order_created.short_description = 'Neue Bestellung bestätigen senden'

#pylint: disable=unused-argument
def _send_order_confirmation(modeladmin, request, queryset):
    """ Update orders """
    for item in queryset:
        send_order_confirmation(item.id, request)
_send_order_confirmation.short_description = 'Bestellbestätigung senden'

#pylint: disable=unused-argument
def update_orders(modeladmin, request, queryset):
    """ Update orders """
    for item in queryset:
        update_order_prices(item)
update_orders.short_description = 'Bestellung und Rechnung updaten'

#pylint: disable=unused-argument
def check_order_payment_reminder(modeladmin, request, queryset):
    """ Check for payment reminder """
    for item in queryset:
        check_for_payment_reminder(item)
check_order_payment_reminder.short_description = 'Auf Zahlungserinnerung prüfen'

#pylint: disable=unused-argument
def _confirm_order(modeladmin, request, queryset):
    """ Confirm order """
    for item in queryset:
        confirm_created_order(item.id, request)
_confirm_order.short_description = 'Bestellung bestätigen'

#pylint: disable=unused-argument
def send_order_payment_reminder(modeladmin, request, queryset):
    """ Send payment reminder """
    for item in queryset:
        send_payment_reminder(item)
send_order_payment_reminder.short_description = 'Zahlungserinnerung senden'

#pylint: disable=unused-argument
def send_order_last_reminder(modeladmin, request, queryset):
    """ Send last reminder """
    for item in queryset:
        send_last_payment_reminder(item)
send_order_last_reminder.short_description = 'Mahnung senden'

#pylint: disable=unused-argument
def send_order_overdue_mail(modeladmin, request, queryset):
    """ Send overdue mail """
    for item in queryset:
        send_overdue_mail(item)
send_order_overdue_mail.short_description = 'Überfälligkeit senden'

#pylint: disable=unused-argument
def save_products(modeladmin, request, queryset):
    """ Update product active """
    for item in queryset:
        item.save()
save_products.short_description = 'Speichern'

#pylint: disable=unused-argument
def _export_order_products(modeladmin, request, queryset):
    """ Export order products """
    return export_order_products(list(queryset.values_list('id', flat=True)))
_export_order_products.short_description = 'Exportieren'

#pylint: disable=unused-argument
def _send_email_again(modeladmin, request, queryset):
    """ Send mail again """
    
    for item in queryset:

        ##### Bestellbestätigung senden #####
        subject = item.subject

        connection = get_connection(
            host = item.pharmacy.sending_mail_host,
            port = item.pharmacy.sending_mail_port,
            username = item.pharmacy.sending_mail,
            password = item.pharmacy.sending_mail_password,
            use_ssl = True,
        )

        to_mail_list = [item.to_email]

        num_sent = send_mail(subject, 'Bestellung versendet', item.pharmacy.sending_mail, to_mail_list, connection=connection, html_message=item.message)

        if num_sent > 0:
            item.sent_success = True
            item.save()
_send_email_again.short_description = 'E-Mail erneut senden'

#pylint: disable=unused-argument
def _send_order_ready_for_pickup(modeladmin, request, queryset):
    """ Send order ready for pickup """
    for item in queryset:
        send_order_ready_for_pickup(item)
_send_order_ready_for_pickup.short_description = 'Abholbereit E-Mail senden'

######## Admin ########
class TerpeneAdmin(admin.ModelAdmin):
    """ Admin Terpene """

    list_display = [
        'name',
        'all_indications',
        'img',
        'id',
    ]
    search_fields = (
        "name",
    )

    def all_indications(self, obj):
        """ Get all indications """
        return ', '.join([indication.name for indication in obj.indications.all()])

    all_indications.short_description = 'Indikationen'

class FAQsAdmin(admin.ModelAdmin):
    """ Admin Terpene """

    list_display = [
        'question',
        'position',
        'group',
        'id',
    ]
    list_filter = [
         "group",
    ]
    search_fields = (
        "name",
    )

class ProductsAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin Products """

    list_display = [
        'number',
        'name',
        'priority',
        'cultivar',
        'manufacturer',
        'supplier',
        'url_name',
        'id',
    ]
    list_filter = [
        'supplier',
        'manufacturer',
    ]
    search_fields = (
        "name",
        "manufacturer__name",
        "supplier__name",
    )
    ordering = [
        'name',
        'number',
    ]
    actions = (
        update_product_priority_to_4,
        update_product_priority_to_3,
        update_product_priority_to_2,
        update_product_priority_to_1,
        update_product_priority_to_0,
        update_product_special_price,
        set_product_in_active,
        save_products,
    )

    @button(html_attrs={'style': 'background-color:#F39B6D;color:black'}, change_list=True, label='Alles Updaten')
    # pylint: disable=unused-argument
    def update_all(self, request):
        """ Update all products """
        for product in Products.objects.all():
            product.url_name = ''
            product.save()

class CannabisIndicationsAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin Indication Templates """

    list_display = [
        'position',
        'name',
        'title',
        'indication',
        'banner_image',
        'image',
        'active',
        'id',
    ]
    list_filter = [
         "active",
    ]
    search_fields = (
        "name",
    )

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Alles exportieren')
    # pylint: disable=unused-argument
    def export_all(self, request):
        """ Export all questions """
        return export_indications_content(list(CannabisIndications.objects.all().values_list('id', flat=True)))

class CannabisEffectsAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin Effect Templates """

    list_display = [
        'id',
        'name',
        'title',
        'position',
        'terpene_effects',
        'banner_image',
        'active',
        'main_page',
    ]
    list_filter = [
        'active',
        'main_page',
    ]
    search_fields = [
        'name',
        'title',
        'terpene_effects',
    ]
    ordering = [
        'position',
        'name',
        'title',
    ]

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Alles exportieren')
    # pylint: disable=unused-argument
    def export_all(self, request):
        """ Export all questions """
        return export_effect_content(list(CannabisEffects.objects.all().values_list('id', flat=True)))

class IndicationsAdmin(admin.ModelAdmin):
    """ Admin indications """

    list_display = [
        'name',
        'id',
        'get_products_amount'
    ]
    search_fields = [
        'name'
    ]

    def get_products_amount(self, obj):
        """ Get products amount """
        return Products.objects.filter(main_terpene__indications=obj).distinct().count()

    get_products_amount.short_description = 'Anzahl Produkte'

class CultivarAdmin(admin.ModelAdmin):
    """ Admin Cultivar """

    list_display = [
        'name',
        'id',
        'get_products_amount'
    ]
    search_fields = [
        'name'
    ]

    def get_products_amount(self, obj):
        """ Get products amount """
        return Products.objects.filter(cultivar=obj).distinct().count()

    get_products_amount.short_description = 'Anzahl Produkte'

class ManufacturerAdmin(admin.ModelAdmin):
    """ Admin Manufacturer """

    list_display = [
        'name',
        'id',
        'get_products_amount'
    ]
    search_fields = [
        'name'
    ]

    def get_products_amount(self, obj):
        """ Get products amount """
        return Products.objects.filter(manufacturer=obj).distinct().count()

    get_products_amount.short_description = 'Anzahl Produkte'

class CustomersAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin customers """

    list_display = [
        'get_full_name',
        'get_user_email',
        'get_street_address',
        'postcode',
        'city',
        'get_state_display',
        'get_registration_date',
        'get_last_login',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'street',
        'postcode',
        'city',
    ]
    list_filter = [
        'customer_type',
        'newsletter',
        'blocked',
    ]
    ordering = [
        'user__first_name',
        'user__email',
        'postcode',
        'city',
        'state',
    ]

    def get_full_name(self, obj):
        """ Get user full name """
        return obj.user.get_full_name()
    get_full_name.short_description = 'Vor- und Nachname'
    get_full_name.admin_order_field  = 'user__first_name'

    def get_user_email(self, obj):
        """ Get user full name """
        return obj.user.email
    get_user_email.short_description = 'E-Mail'
    get_user_email.admin_order_field = 'user__email'

    def get_registration_date(self, obj):
        """ Get user full name """
        if obj.user.last_login:
            return obj.user.last_login.strftime('%d.%m.%Y')
        else:
            obj.user.date_joined.strftime('%d.%m.%Y')
    get_registration_date.short_description = 'Mitglied seit'

    def get_last_login(self, obj):
        """ Get user full name """
        return obj.user.date_joined.strftime('%d.%m.%Y')
    get_last_login.short_description = 'Letzter login'

    @button(html_attrs={'style': 'background-color:#f5c600;color:black'}, change_list=True, label='Benutzernamen updaten')
    # pylint: disable=unused-argument
    def update_all_usernames(self, request):
        """ Update all usernames """
        for customer in Customers.objects.all():

            user = customer.user

            user.username = user.username.lower()
            user.email = user.email.lower()
            user.save()

class OrdersAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin orders """

    raw_id_fields = ['customer']
    list_display = [
        'id',
        'number',
        'get_customer_name',
        'get_customer_email',
        'customer_type',
        'total',
        'get_order_date',
        'get_deliverd_date',
        'ordered',
        'status',
        'payment_status',
        'payment_type',
    ]
    search_fields = [
        'customer__user__email',
        'customer__user__first_name',
        'customer__user__last_name',
        'number',
    ]
    list_filter = (
        'ordered',
        'status',
        'payment_status',
        'payment_type',
        ('delivered_on', DateRangeFilterBuilder()),
        ('order_time', DateRangeFilterBuilder())
    )
    ordering = [
        '-order_time',
        'customer',
    ]
    actions = (
        save_orders,
        _send_order_confirmation,
        update_orders,
        send_order_payment_reminder,
        send_order_last_reminder,
        send_order_overdue_mail,
        check_order_payment_reminder,
        _send_new_order_created,
        _confirm_order,
        _send_order_ready_for_pickup,
    )

    def get_customer_name(self, obj):
        """ Get customer name """
        if obj.customer:
            return obj.customer.user.get_full_name()
        else:
            return ''
    get_customer_name.short_description = 'Name'
    get_customer_name.admin_order_field = 'customer'

    def get_customer_email(self, obj):
        """ Get customer email """
        if obj.customer:
            return obj.customer.user.email
        else:
            return ''
    get_customer_email.short_description = 'Kunde'
    get_customer_email.admin_order_field = 'customer'

    def get_order_date(self, obj):
        """ Get order date """
        return obj.order_time.strftime('%d.%m.%Y')
    get_order_date.short_description = 'Bestelldatum'
    get_order_date.admin_order_field = 'order_time'

    def get_deliverd_date(self, obj):
        """ Get deliver date """
        return obj.delivered_on.strftime('%d.%m.%Y') if obj.delivered_on else ''
    get_deliverd_date.short_description = 'Lieferdatum'
    get_deliverd_date.admin_order_field = 'delivered_on'

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Alles exportieren')
    # pylint: disable=unused-argument
    def export_all(self, request):
        """ Export all order products """
        return export_orders(list(Orders.objects.all().values_list('id', flat=True)))

class OrderRecipesAdmin(admin.ModelAdmin):
    """ Admin order receipts """

    raw_id_fields = ['order']
    list_display = [
        'get_order',
        'file',
        'number'
    ]
    search_fields = [
        'order__customer__user__first_name',
        'order__customer__user__last_name',
        'order__number',
        'order__id',
    ]

    def get_order(self, obj):
        """ Get order number """
        return f'{ obj.order.number if obj.order.number else "(Nicht vorhanden)"} - { obj.order }'

class OrderProductsAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin orderproducts """

    raw_id_fields = ['order', 'recipe_file',]
    list_display = [
        'get_order',
        'get_product_name',
        'amount',
        'get_total',
        'prepared',
    ]
    search_fields = [
        'order__customer__user__first_name',
        'order__customer__user__last_name',
        'order__number',
        'order__id',
        'product__name',
    ]
    list_filter = (
        'order__ordered',
        'order__status',
        'order__pharmacy',
        'order__payment_status',
        'order__payment_type',
        ('order__delivered_on', DateRangeFilterBuilder()),
        ('order__order_time', DateRangeFilterBuilder())
    )
    actions = (
        _export_order_products,
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "order":
            kwargs["queryset"] = Orders.objects.order_by('-id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_order(self, obj):
        """ Get order number """
        return f'{ obj.order.number if obj.order.number else "(Nicht vorhanden)"} - { obj.order }'
    get_order.short_description = 'Bestellung'

    def get_product_name(self, obj):
        """ Get product name """
        return f'{obj.product.number} - {obj.product.name}'
    get_product_name.short_description = 'Product'

    def get_total(self, obj):
        """ Get product name """
        # pylint: disable=deprecated-method
        return locale.format_string('%.2f', obj.total, True) + ' €' if obj.total or obj.total == 0 else '--'
    get_total.short_description = 'Verkausfpreis (Netto)'

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Alles exportieren')
    # pylint: disable=unused-argument
    def export_all(self, request):
        """ Export all order products """
        return export_order_products(list(OrderProducts.objects.all().values_list('id', flat=True)))

class IdentificationFilesAdmin(admin.ModelAdmin):

    raw_id_fields = ['order']
    list_display = [
        'get_order',
        'file',
        'id_number'
    ]
    search_fields = [
        'order__customer__user__first_name',
        'order__customer__user__last_name',
        'order__number',
        'order__id',
    ]

    def get_order(self, obj):
        """ Get order number """
        return f'{ obj.order.number if obj.order.number else "(Nicht vorhanden)"} - { obj.order }'

class FlavorsAdmin(admin.ModelAdmin):
    """ Admin aromen """

    list_display = [
        'id',
        'name',
        'get_terpene_amount',
        'get_terpene',
    ]
    search_fields = [
        'get_terpene',
    ]
    ordering = [
        'name'
    ]

    def get_terpene_amount(self, obj):
        """ Get amount terpene """
        return Terpene.objects.filter(flavors=obj).count()
    get_terpene_amount.short_description = 'Anzahl Terpene'

    def get_terpene(self, obj):
        """ Get amount terpene """
        return ', '.join(list(Terpene.objects.filter(flavors=obj).values_list('name', flat=True)))
    get_terpene.short_description = 'Terpene'

class InvoicesAdmin(admin.ModelAdmin):
    """ Admin invoices """

    raw_id_fields = ['order']
    list_display = [
        'invoice_number',
        'date_time',
        'total',
        'get_order_number',
        'status',
        'payment_type',
        'canceled',
        'send_to_customer',
        'pro_forma_invoice',
        'cancellation_invoice',
        'id'
    ]
    search_fields = [
        'customer__user__email',
        'order__number',
        'invoice_number',
    ]
    list_filter = [
        'status',
        'canceled',
        'cancellation_invoice',
        'payment_type',
        'send_to_customer',
        'pro_forma_invoice',
    ]
    ordering = [
        '-id',
        '-invoice_number',
        '-date_time',
    ]
    actions = (
        _create_new_invoice,
        _send_invoice_to_customer,
        )

    def get_order_number(self, obj):
        """ Get customer email """
        if obj.order:
            return obj.order.number
        return 'Nicht vorhanden'
    get_order_number.short_description = 'Bestellnummer'

class LoggerAdmin(admin.ModelAdmin):
    """ Admin logger """

    list_display = [
        'get_category_display',
        'get_date_time',
        'user',
        'reference',
        'message',
    ]
    search_fields = [
        'reference',
        'message',
        'stack_trace',
        'user',
    ]
    list_filter = [
        'category',
    ]

    def get_category_display(self, obj):
        """ Get categroy display name """

        if obj.category in ['info', 'notset']:
            color = '#4AC1D2'
        elif obj.category in ['error', 'fatal']:
            color = '#e33030'
        elif obj.category in ['warning', 'debug']:
            color = '#f0bb29'
        elif obj.category in ['task']:
            color = '#10B981'
        else:
            color = '#4AC1D2'

        return format_html('<span style="color: {color};">{msg}</span>', color=color, msg=obj.get_category_display() if obj.category else '')

    get_category_display.short_description = 'Kategorie'

    def get_date_time(self, obj):
        """ Get date_time as strptime """
        return obj.date_time.strftime('%d.%m.%Y - %H:%M:%S Uhr')

class ProductImagesAdmin(admin.ModelAdmin):
    """ Admin productimages """

    list_display = [
        'get_product_number',
        'get_product_name',
        'position',
        'img',
        'main_image',
    ]
    search_fields = [
        'product__number',
        'product__name',
    ]
    list_filter = [
        'main_image',
    ]
    ordering = [
        'product__name',
        'position'
    ]

    def get_product_number(self, obj):
        """ Get categroy display name """
        return obj.product.number
    get_product_number.short_description = 'Produktnummer'

    def get_product_name(self, obj):
        """ Get categroy display name """
        return obj.product.name
    get_product_name.short_description = 'Produktname'

class EmailSettingsAdmin(admin.ModelAdmin):
    """ Admin E-Mail Einstellungen """

    fieldsets = (
        ('Info E-Mail', {'fields':('info_email', 'info_email_host', 'info_email_password', 'info_email_port')}),
        ('No-Reply E-Mail', {'fields':('no_reply_email','no_reply_email_host', 'no_reply_email_password', 'no_reply_email_port')}),
        ('Kontakt E-Mail', {'fields':('contact_email', 'contact_email_host', 'contact_email_password', 'contact_email_port')}),
    )

class PharmaciesAdmin(admin.ModelAdmin):
    """ Admin Apotheken """

    list_display = [
        'name',
        'street',
        'street_number',
        'postalcode',
        'city',
        'contact_name',
        'pharmacy_overloaded',
    ]
    search_fields = [
        'name',
        'street',
        'postalcode',
        'city',
        'state',
    ]

    fieldsets = (
        ('Allgemein',
            {
                'fields':(
                    'name',
                    'street',
                    'street_number',
                    'postalcode',
                    'city',
                    'contact_name',
                    'phonenumber',
                    'email',
                    'pharmacy_overloaded',
                    'pharmacy_ext_id',
                    'active',
                )
            }
        ),
        ('Zahlungseinstellungen',
            {
                'fields':(
                    'paypal_active',
                    'paypal_email',
                    'bank_name',
                    'bank_iban',
                    'bank_bic',
                )
            }
        ),
        ('Rechnungsdaten', {
            'fields': (
                'invoice_name', 
                'invoice_street', 
                'invoice_street_number', 
                'invoice_postalcode', 
                'invoice_city'
                )
            }
        ),
        ('Rechtliche Daten',
            {
                'fields':(
                    'responsible_pharmacist',
                    'responsible_for_content',
                    'register_court',
                    'register_number',
                    'responsible_supervicory_authority',
                    'responsible_chamber',
                    'tax_idenfitication',
                )
            }
        ),
        ('DHL Einstellungen',
            {
                'fields':(
                    'dhl_active',
                    'dhl_api_key',
                    'dhl_secret_key',
                    'dhl_base_url_test',
                    'dhl_baser_url_prod',
                    'dhl_z_username',
                    'dhl_z_password',
                    'dhl_username',
                    'dhl_password',
                    'dhl_account_number',
                    'dhl_billing_number',
                    'dhl_shipping_product',
                )
            }
        ),
        ('GO!Express Einstellungen',
            {
                'fields':(
                    'go_express_active',
                    'go_express_base_url_test',
                    'go_express_base_url_prod',
                    'go_express_username',
                    'go_express_password',
                    'go_express_track_username',
                    'go_express_track_password',
                    'go_express_responsible_station',
                    'go_express_customer_id',
                )
            }
        ),
        ('E-Mail Einstellungen',
            {
                'fields':(
                    'sending_mail',
                    'sending_mail_host',
                    'sending_mail_password',
                    'sending_mail_port',
                )
            }
        )
    )

class ProductsStockAdmin(ExtraButtonsMixin, admin.ModelAdmin):

    list_display = [
        'get_pharmacy_name',
        'get_product_number',
        'get_product_name',
        'amount',
        'status',
    ]
    search_fields = [
        'product__number',
        'product__name',
    ]
    list_filter = [
        'status',
    ]

    def get_pharmacy_name(self, obj):
        """ Get pharmacy name """
        return obj.pharmacy.name
    get_pharmacy_name.short_description = 'Apotheke'

    def get_product_number(self, obj):
        """ Get product number """
        return obj.product.number
    get_product_number.short_description = 'Produktnummer'

    def get_product_name(self, obj):
        """ Get product name """
        return obj.product.name
    get_product_name.short_description = 'Produktname'

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Lagerbestannd updaten')
    # pylint: disable=unused-argument
    def update_all(self, request):
        """ Create stock products from proucts """
        create_product_stock_items()

    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Lagermengen updaten')
    # pylint: disable=unused-argument
    def update_all_amounts(self, request):
        """ Create stock products from proucts """
        for pharmacy in Pharmacies.objects.all():
            for order in Orders.objects.filter(pharmacy=pharmacy, status__in=['ready_to_ship', 'ready_for_pickup', 'shipped', 'delivered', 'picked_up']):
                for order_product in OrderProducts.objects.filter(order=order):
                    for packed_order_product in PackedOrderedProducts.objects.filter(order_product=order_product):

                        stock_product = packed_order_product.stock_product

                        if stock_product.amount > 0:
                            if packed_order_product.fill_amount > stock_product.amount:
                                stock_product.amount -= packed_order_product.fill_amount
                            else:
                                stock_product.amount = 0
                            stock_product.save()

                        OrderProducts.objects.filter(id=order_product.id).update(calculated_in_stock=True)

class ProductPricesAdmin(admin.ModelAdmin):

    list_display = [
        'get_product_number',
        'get_product_name',
        'get_pharmacy_name',
        'self_payer_selling_price',
        'status',
        'active',
    ]
    search_fields = [
        'product__number',
        'product__name',
    ]
    list_filter = [
        'pharmacy__name',
        'status',
        'active',
    ]

    def get_pharmacy_name(self, obj):
        """ Get pharmacy name """
        return obj.pharmacy.name

    def get_product_number(self, obj):
        """ Get product number """
        return obj.product.number
    get_product_number.short_description = 'Produktnummer'

    def get_product_name(self, obj):
        """ Get product name """
        return obj.product.name
    get_product_name.short_description = 'Produktname'

class OpeningHoursAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin opening hours """

    list_display = [
        'get_pharamcy_name',
        'day',
        'from_time',
        'to_time',
        'closed',
    ]
    search_fields = [
        'pharmacy__name',
    ]
    list_filter = [
        'day',
        'closed',
    ]
    ordering = [
        'pharmacy',
        'day'
    ]

    def get_pharamcy_name(self, obj):
        """ Get pharmacy name """
        return obj.pharmacy.name
    get_pharamcy_name.short_description = 'Apotheke'

    # Extrabutton to create opening hours for all pharmacies if not exist
    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Öffnungszeiten erstellen')
    # pylint: disable=unused-argument
    def create_all(self, request):
        """ Create opening hours for all pharmacies """
        for pharmacy in Pharmacies.objects.all():
            for day in range(0, 7):
                OpeningHours.objects.get_or_create(pharmacy=pharmacy, day=day, defaults={'from_time': '08:00', 'to_time': '18:00', 'closed': False})

class PackagePickupTimesAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    """ Admin opening hours """

    list_display = [
        'get_pharamcy_name',
        'day',
        'from_time',
        'to_time',
        'closed',
    ]
    search_fields = [
        'pharmacy__name',
    ]
    list_filter = [
        'day',
        'closed',
    ]
    ordering = [
        'pharmacy',
        'day'
    ]

    def get_pharamcy_name(self, obj):
        """ Get pharmacy name """
        return obj.pharmacy.name
    get_pharamcy_name.short_description = 'Apotheke'

    # Extrabutton to create opening hours for all pharmacies if not exist
    @button(html_attrs={'style': 'background-color:#88FF88;color:black'}, change_list=True, label='Abholzeiten erstellen')
    # pylint: disable=unused-argument
    def create_all(self, request):
        """ Create opening hours for all pharmacies """
        for pharmacy in Pharmacies.objects.all():
            for day in range(0, 7):
                PackagePickupTimes.objects.get_or_create(pharmacy=pharmacy, day=day, defaults={'from_time': '08:00', 'to_time': '18:00', 'closed': False})

class StaffUserAdmin(ExtraButtonsMixin, admin.ModelAdmin):

    raw_id_fields = ['user']
    list_display = [
        'get_full_name',
        'get_username',
        'get_email',
        'get_last_login',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__username',
    ]

    def get_full_name(self, obj):
        """ Get user full name """
        return obj.user.get_full_name()
    
    def get_username(self, obj):
        """ Get user full name """
        return obj.user.username
    
    def get_email(self, obj):
        """ Get user full name """
        return obj.user.email
    
    def get_last_login(self, obj):
        """ Get user full name """
        return obj.user.last_login.strftime('%d.%m.%Y') if obj.user.last_login else ''
    
    get_full_name.short_description = 'Vor- und Nachname'
    get_username.short_description = 'Benutzername'
    get_email.short_description = 'E-Mail'
    get_last_login.short_description = 'Letzter login'

    @button(html_attrs={'style': 'background-color:#f5c600;color:black'}, change_list=True, label='Mitarbeiter aktualisieren')
    # pylint: disable=unused-argument
    def create_staff_user_if_not_exist(self, request):
        """ Update all usernames """
        for user in User.objects.filter(is_staff=True):
            if not StaffUser.objects.filter(user=user).exists():
                StaffUser.objects.create(user=user)

class UserPremissionsAdmin(admin.ModelAdmin):

    raw_id_fields = ['user']
    list_display = [
        'get_pharmacy',
        'get_username',
        'get_user',
        'view',
        'read_premission',
        'write_premission',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'staff_user__user__first_name',
        'staff_user__user__last_name',
        'staff_user__user__email',
        'pharmacy__name',
    ]
    list_filter = [
        'pharmacy',
        'view',
        'read_premission',
        'write_premission',
    ]
    ordering = [
        'pharmacy',
    ]

    def get_username(self, obj):
        """ Get username """
        return obj.user.username
    
    def get_user(self, obj):
        """ Get user full name """
        return obj.user.get_full_name()
    
    def get_pharmacy(self, obj):
        """ Get user full name """
        return obj.pharmacy.name
    
    get_username.short_description = 'Benutzer'
    get_user.short_description = 'Name'
    get_pharmacy.short_description = 'Apotheke'

class PackedOrderedProductsAdmin(admin.ModelAdmin):

    raw_id_fields = ['order_product', 'package', 'stock_product']
    list_display = [
        'get_order_product',
        'get_package',
        'get_stock_product',
        'fill_amount',
        'get_order_number',
        'get_order_status_display',
    ]
    search_fields = [
        'order_product__order__number',
        'package__batch_number',
        'stock_product__product__name',
        'stock_product__pharmacy__name',
    ]

    list_filter = [
        'order_product__order__status',
    ]

    def get_order_product(self, obj):
        """ Get order product """
        return f'{obj.order_product.product.number} - {obj.order_product.product.name}'
    get_order_product.short_description = 'Bestelltes Produkt'

    def get_package(self, obj):
        """ Get package """
        return f'{obj.package.batch_number} - {obj.package.name}'
    get_package.short_description = 'Verpackung'

    def get_stock_product(self, obj):
        """ Get stock product """
        return f'{obj.stock_product.product.number} - {obj.stock_product.product.name} ({obj.stock_product.pharmacy.name})'
    get_stock_product.short_description = 'Lagerprodukt'

    def get_order_number(self, obj):
        """ Get order number """
        return obj.order_product.order.number if obj.order_product and obj.order_product.order else ''
    get_order_number.short_description = 'Bestellnummer'

    def get_order_status_display(self, obj):
        """ Get order status """
        return obj.order_product.order.get_status_display()
    get_order_status_display.short_description = 'Bestellstatus'

class StockProductsLoggerAdmin(admin.ModelAdmin):

    raw_id_fields = ['stock_product']
    list_display = [
        'get_stock_product',
        'amount',
        'action',
        'reason',
    ]
    search_fields = [
        'stock_product__product__number',
        'stock_product__product__name',
        'stock_product__pharmacy__name',
    ]

    def get_stock_product(self, obj):
        """ Get stock product """
        return f'{obj.stock_product.product.number} - {obj.stock_product.product.name} ({obj.stock_product.pharmacy.name})'
    get_stock_product.short_description = 'Lagerprodukt'

class PackagesLoggerAdmin(admin.ModelAdmin):

    raw_id_fields = ['package']
    list_display = [
        'get_package',
        'amount',
        'action',
        'reason',
    ]
    search_fields = [
        'package__batch_number',
        'package__name',
    ]

    def get_package(self, obj):
        """ Get stock product """
        return f'{obj.package.batch_number} - {obj.package.name}'
    get_package.short_description = 'Verpackung'

class EmailLoggerAdmin(admin.ModelAdmin):

    list_display = [
        'subject',
        'to_email',
        'from_email',
        'get_date_time',
        'sent_success',
    ]
    search_fields = [
        'subject',
        'from_email',
        'to_email',
    ]
    list_filter = [
        'sent_success',
        'pharmacy',
    ]
    actions = (
        _send_email_again,
    )

    def get_date_time(self, obj):
        """ Get date_time as strptime """
        return obj.date_time.strftime('%d.%m.%Y - %H:%M:%S Uhr')
    get_date_time.short_description = 'Datum und Uhrzeit'

# admin.site.register(User)
admin.site.register(EmailSettings, EmailSettingsAdmin)
admin.site.register(Terpene, TerpeneAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(ProductPrices, ProductPricesAdmin)
admin.site.register(StockProducts, ProductsStockAdmin)
admin.site.register(FAQs, FAQsAdmin)
admin.site.register(CannabisIndications, CannabisIndicationsAdmin)
admin.site.register(CannabisEffects, CannabisEffectsAdmin)
admin.site.register(Indications, IndicationsAdmin)
admin.site.register(Cultivar, CultivarAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Customers, CustomersAdmin)
admin.site.register(Orders, OrdersAdmin)
admin.site.register(OrderRecipes, OrderRecipesAdmin)
admin.site.register(OrderProducts, OrderProductsAdmin)
admin.site.register(Flavors, FlavorsAdmin)
admin.site.register(Invoices, InvoicesAdmin)
admin.site.register(Logger, LoggerAdmin)
admin.site.register(ProductImages, ProductImagesAdmin)
admin.site.register(OpeningHours, OpeningHoursAdmin)
admin.site.register(PackagePickupTimes, PackagePickupTimesAdmin)
admin.site.register(Pharmacies, PharmaciesAdmin)
admin.site.register(StaffUser, StaffUserAdmin)
admin.site.register(UserPremissions, UserPremissionsAdmin)
admin.site.register(IdentificationFiles, IdentificationFilesAdmin)
admin.site.register(PackedOrderedProducts, PackedOrderedProductsAdmin)
admin.site.register(StockProductsLogger, StockProductsLoggerAdmin)
admin.site.register(PackagesLogger, PackagesLoggerAdmin)
admin.site.register(EmailLogger, EmailLoggerAdmin)
