# internal_requests/urls.py

from django.urls import path
from . import requests

urlpatterns = [
    path('v1/products/', requests.product_datas_v1, name='request_product_datas'),
    path('v1/orders/', requests.order_functions_v1, name='request_order_functions'),
    path('v1/products/stock/', requests.products_stock_v1, name='request_products_stock'),
    path('v1/packages/stock/', requests.packages_stock_v1, name='request_packages_stock'),
    path('v1/import/', requests.import_functions_v1, name='request_import_functions'),
]
