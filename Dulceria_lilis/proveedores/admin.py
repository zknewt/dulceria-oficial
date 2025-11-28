from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "email", "telefono", "ciudad", "estado")
    search_fields = ("razon_social", "email", "telefono", "ciudad")  # 🔥 Necesario
