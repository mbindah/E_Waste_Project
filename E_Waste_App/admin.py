# admin.py

from django.contrib import admin
from .models import Administrator, Vendor, Client, Product, Purchase

admin.site.register(Administrator)
admin.site.register(Vendor)
admin.site.register(Client)
admin.site.register(Product)
admin.site.register(Purchase)
