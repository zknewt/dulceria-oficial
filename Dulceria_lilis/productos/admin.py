from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("sku", "nombre", "categoria", "precio_venta", "stock_actual")
    search_fields = ("sku", "nombre", "categoria")  # 🔥 Necesario
