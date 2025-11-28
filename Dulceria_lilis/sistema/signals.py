# sistema/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from sistema.middleware import get_current_user
from sistema.models import RegistroActividad

# Modelos que quieres auditar
from usuarios.models import Usuario
from productos.models import Producto
from proveedores.models import Proveedor
from inventario.models import MovimientoInventario


# ===== SOLUCIÓN AL RECURSIÓN: bandera para evitar bucle infinito =====
@receiver(post_save)
def auditar_creacion_modificacion(sender, instance, created, **kwargs):
    # IGNORAMOS completamente el modelo RegistroActividad
    if sender == RegistroActividad:
        return

    # Evitamos registrar si no hay usuario autenticado
    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    # Evitamos registrar acciones del propio sistema o admin interno
    if getattr(user, 'is_staff', False) and user.username == 'admin':
        return

    # Construimos el mensaje según el modelo
    if sender == Usuario:
        texto = f"usuario '{instance.username}' (Rol: {instance.get_rol_display()})"
    elif sender == Producto:
        texto = f"producto '{instance.sku}' - {instance.nombre}"
    elif sender == Proveedor:
        texto = f"proveedor '{instance.rut_nif}' - {instance.razon_social}"
    elif sender == MovimientoInventario:
        texto = f"movimiento {instance.get_tipo_display()} de {instance.cantidad} unidades del producto {instance.producto.nombre}"
    else:
        texto = str(instance)

    accion = "creado" if created else "modificado"

    # CREAMOS EL REGISTRO SIN DISPARAR MÁS SIGNALS
    RegistroActividad.objects.bulk_create([
        RegistroActividad(
            usuario=user,
            descripcion=f"{sender.__name__} {accion}: {texto}",
            modelo=sender.__name__,
            objeto_id=instance.pk
        )
    ], ignore_conflicts=True)


@receiver(post_delete)
def auditar_eliminacion(sender, instance, **kwargs):
    if sender == RegistroActividad:
        return

    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    if sender == Usuario:
        texto = f"usuario '{instance.username}'"
    elif sender == Producto:
        texto = f"producto '{instance.sku}' - {instance.nombre}"
    elif sender == Proveedor:
        texto = f"proveedor '{instance.rut_nif}'"
    else:
        texto = str(instance)

    RegistroActividad.objects.bulk_create([
        RegistroActividad(
            usuario=user,
            descripcion=f"{sender.__name__} eliminado: {texto}",
            modelo=sender.__name__,
        )
    ], ignore_conflicts=True)