# internal_requests/urls.py

from django.urls import path
from . import requests

urlpatterns = [
    path('v1/products/', requests.product_datas_v1, name='request_product_datas'),
    path('v1/orders/', requests.order_functions_v1, name='request_order_functions'),
    path('v1/products/stock/', requests.products_stock_v1, name='request_products_stock'),
    path('v1/packages/stock/', requests.packages_stock_v1, name='request_packages_stock'),
    path('v1/import/', requests.import_functions_v1, name='request_import_functions'),
    path('v1/customer/', requests.customer_functions_v1, name='request_customer_functions'),
    path('v1/staff_user/', requests.staff_user_functions_v1, name='request_staff_user_functions'),
    path('v1/email_recipients/', requests.email_recipient_functions_v1, name='request_email_recipient_functions'),

    path('v1/user/order', requests.user_order_functions_v1, name='request_user_order_functions'),
    
    # Downloads
    path('invoice/<int:invoice_id>/<str:invoice_type>/<str:datetime_now>', requests.download_invoice_v1, name='download_invoice'),
    path('export/orders/products/<str:datetime_now>', requests.download_order_products_v1, name='download_order_products'),
    path('invoice/<int:order_id>/<str:datetime_now>', requests.create_shipping_label_v1, name='create_shipping_label'),

]
