from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from api.models import Order, Item, OrderItem, Customer, User

admin.site.register(User, UserAdmin)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "ship", "supervisor", "contact")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("customer", "state", "comment", "created_on")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "item", "quantity", "price", "unit")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "default_price")
