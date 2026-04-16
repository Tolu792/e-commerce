from django.contrib import admin
from .models import User, Product, Category, CartItem, Order, OrderItem

admin.site.site_header = "E-commerce Admin"
admin.site.site_title = "E-commerce Admin Portal"
admin.site.index_title = "Welcome to the E-commerce Admin Portal"

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'phone_number', 'profile_picture')
    search_fields = ('email', 'username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'price', 'stock', 'category', 'image', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ['name']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity')
    search_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at', 'updated_at')
    search_fields = ['user__email']
    list_filter = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ['product__name']
