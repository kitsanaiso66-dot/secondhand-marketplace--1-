from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Order, Product, User


@admin.register(User)
class ShopUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("ข้อมูลเพิ่มเติม", {"fields": ("phone",)}),)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "seller", "category", "condition", "price", "status", "created_at")
    list_filter = ("status", "category", "condition")
    search_fields = ("name", "seller__username")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "product", "price", "status", "created_at")
    list_filter = ("status",)
