"""
URL configuration for E_Waste_Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings
from django.urls import path
from E_Waste_App.views import *
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('update-details/', update_user_details, name='update_user_details'),
    path('update-details1/', update_user_details1, name='update_user_details1'),

    # Vendor URLs
    path('vendor/dashboard/', vendor_dashboard, name='vendor_dashboard'),
    path('vendor/signup/', vendor_signup, name='vendor_signup'),
    path('vendor/login/', vendor_login, name='vendor_login'),
    path('vendor/post_product/', post_product, name='post_product'),
    path('vendor/delete_product/<int:product_id>/', delete_product, name='delete_product'),    
    path('vendor/view_products/', view_products, name='view_products'),
    path('vendor/view_messages/', view_messages1, name='view_messages1'),
    path('vendor/delete_message/<int:message_id>/', delete_message, name='delete_message'),
    path('vendor/logout/', vendor_logout, name='vendor_logout'),
    path('vendor/check_new_messages/', check_new_messages1, name='check_new_messages1'),
    path('vendor/view_ratings/', view_ratings, name='view_ratings'),

    # Client URLs
    path('client/dashboard/', client_dashboard, name='client_dashboard'),
    path('client/signup/', client_signup, name='client_signup'),
    path('client/login/', client_login, name='client_login'),
    path('client/view_products/', view_products_for_clients, name='view_products_for_clients'),
    path('client/purchase_product/<int:product_id>/', purchase_product, name='purchase_product'),
    path('client/rate_vendor/<int:vendor_id>/', rate_vendor, name='rate_vendor'),
    path('client/logout/', client_logout, name='client_logout'),
    path('client/check_new_messages/', check_new_messages, name='check_new_messages'),
    
    # Communication between Clients and Vendors
    path('client/send_message/<int:vendor_id>/', send_message, name='send_message'),
    path('client/view_messages/', view_messages, name='view_messages'),
    path('client/delete_message/<int:message_id>/', delete_message, name='delete_message'),

    # Order Management URLs
    path('vendor/view_orders/', view_orders, name='view_orders'),
    path('client/view_orders/', view_orders_for_client, name='view_orders_for_client'),    
    path('client/cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('vendor/complete_order/<int:order_id>/', complete_order, name='complete_order'),
    path('vendor/accept_order/<int:order_id>/', accept_order, name='accept_order'),
    path('vendor/reject_order/<int:order_id>/', reject_order, name='reject_order'),

    # Dashboards
    path('vendor/dashboard/', vendor_dashboard, name='vendor_dashboard'),  # Duplicate: Consider renaming or combining
    path('client/dashboard/', client_dashboard, name='client_dashboard'),  # Duplicate: Consider renaming or combining
]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)