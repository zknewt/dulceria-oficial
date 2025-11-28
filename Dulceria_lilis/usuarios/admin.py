from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario

class UsuarioAdmin(BaseUserAdmin):
    model = Usuario
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('nombres', 'apellidos', 'telefono', 'rol', 'estado', 'mfa_habilitado', 'ultimo_acceso', 'area', 'observaciones')
        }),
    )
    list_display = ('username', 'email', 'nombres', 'apellidos', 'rol', 'is_staff', 'estado')
    search_fields = ('username', 'email', 'nombres', 'apellidos', 'rol')

admin.site.register(Usuario, UsuarioAdmin)
