# usuarios/signals.py
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import Group


@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    """
    Se ejecuta cada vez que un usuario inicia sesión correctamente.
    Actualiza la fecha de último acceso y cuenta las veces que ha iniciado sesión.
    """
    user.ultimo_acceso = timezone.now()
    
    if user.sesiones is None:
        user.sesiones = 1
    else:
        user.sesiones += 1
    
    user.save(update_fields=['ultimo_acceso', 'sesiones'])


@receiver(post_save, sender='usuarios.Usuario')
def asignar_grupo_por_rol(sender, instance, created, **kwargs):
    """
    Asigna automáticamente el grupo de permisos según el rol del usuario.
    Se ejecuta al crear o actualizar un usuario.
    """
    # Mapping de roles a grupos
    rol_a_grupo = {
        'ADMIN': None,  # Los ADMIN usan is_staff o is_superuser
        'BODEGA': 'BODEGA',
        'CONSULTA': 'CONSULTA',
        'PROVEEDOR': 'PROVEEDOR',
        'OPERADOR': 'OPERADOR',
    }
    
    # Limpiar grupos anteriores si cambió de rol
    instance.groups.clear()
    
    # Asignar nuevo grupo según rol
    nombre_grupo = rol_a_grupo.get(instance.rol)
    
    if nombre_grupo:
        try:
            grupo = Group.objects.get(name=nombre_grupo)
            instance.groups.add(grupo)
            print(f"✅ Usuario {instance.username} asignado al grupo {nombre_grupo}")
        except Group.DoesNotExist:
            print(f"⚠️  Grupo {nombre_grupo} no existe. Ejecuta las migraciones.")
    
    # Si es ADMIN, asegurar permisos de staff
    if instance.rol == 'ADMIN':
        if not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=['is_staff'])