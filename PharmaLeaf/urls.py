"""PharmaLeaf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.conf import settings
from app import views
from app.endpoints import recipe_endpoint_v1, get_all_products_v1
import object_tools
from  django.conf.urls import url
from django.views.generic.base import RedirectView

urlpatterns = [
    # Admin
    path('object-tools/', object_tools.tools.urls),

    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('hg-admin-page/', admin.site.urls),

    # General Pages
    path('', views.home, name='home'),
    path('Impressum/', views.imprint, name='imprint'),
    path('Datenschutz/', views.policy, name='policy'),
    path('AGB/', views.agb, name='agb'),
    path('Cookie-Informationen/', views.cookie_info, name='cookie_info'),
    path('Versand-Retouren/', views.shipping_and_retoures, name='shipping_and_retoures'),
    path('Zahlungsmethoden/', views.payment, name='payment'),
    path('Bestellübersicht/<int:order_id>', views.order_overview, name='order_overview'),
    re_path(r'^Bestellung/Bestätigen/(?P<order_id>\d+)/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z_\-]+)/$', views.confirm_order, name='confirm_order'),
    re_path(r'^Account/Passwort/(?P<order_id>\d+)/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z_\-]+)/$', RedirectView.as_view(pattern_name='confirm_order', permanent=True)),

    # Dashboard
    re_path(r'^Dashboard/Account/Aktivieren/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z_\-]+)/$', views.dashboard_activate_user, name='dashboard_activate_user'),
    path('dashboard/login', views.dashboard_login, name='dashboard_login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('dashboard/orders', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/orders/review', views.dashboard_review_orders, name='dashboard_review_orders'),
    path('dashboard/orders/products', views.dashboard_order_products, name='dashboard_order_products'),
    path('dashboard/products', views.dashboard_products_all, name='dashboard_products_all'),
    path('dashboard/product_requests', views.dashboard_product_requests, name='dashboard_product_requests'),
    path('dashboard/stock/products', views.dashboard_products_stock, name='dashboard_products_stock'),
    path('dashboard/stock/packages', views.dashboard_packages_stock, name='dashboard_packages_stock'),
    path('dashboard/imports', views.dashboard_imports, name='dashboard_imports'),
    path('dashboard/data', views.dashboard_get_data, name='dashboard_get_data'),
    path('dashboard/customers', views.dashboard_customers, name='dashboard_customers'),
    path('dashboard/settings/users', views.dashboard_users, name='dashboard_users'),
    path('dashboard/settings/email_recipients', views.dashboard_email_recipients, name='dashboard_email_recipients'),

    # API Endpioints
    path('orders/create/v1/prescription', recipe_endpoint_v1, name='recipe_endpint_v1'),
    path('retrieve/products/v1', get_all_products_v1, name='get_all_products_v1'),

    # Request Methods
    path('api/', include('app.internal_requests.urls')),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
