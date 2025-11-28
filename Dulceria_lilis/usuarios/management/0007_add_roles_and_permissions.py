# usuarios/migrations/0007_add_roles_and_permissions.py
from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def crear_grupos_y_permisos(apps, schema_editor):
    """
    Crea los grupos BODEGA y CONSULTA con sus permisos correspondientes
    """
    Usuario = apps.get_model('usuarios', 'Usuario')
    
    # Obtener ContentTypes
    try:
        producto_ct = ContentType.objects.get(app_label='productos', model='producto')
        proveedor_ct = ContentType.objects.get(app_label='proveedores', model='proveedor')
        inventario_ct = ContentType.objects.get(app_label='inventario', model='movimientoinventario')
        bodega_ct = ContentType.objects.get(app_label='inventario', model='bodega')
        sistema_ct = ContentType.objects.get(app_label='sistema', model='sistemanopermisos')
    except ContentType.DoesNotExist:
        # Si no existen los modelos, salir
        return

    # =============================
    # GRUPO BODEGA
    # =============================
    grupo_bodega, created = Group.objects.get_or_create(name='BODEGA')
    
    # Permisos de Productos (ver, agregar, editar)
    permisos_bodega = [
        Permission.objects.get(codename='view_producto', content_type=producto_ct),
        Permission.objects.get(codename='add_producto', content_type=producto_ct),
        Permission.objects.get(codename='change_producto', content_type=producto_ct),
        # NO delete_producto
    ]
    
    # Permisos de Inventario (ver, agregar, editar)
    try:
        permisos_bodega.extend([
            Permission.objects.get(codename='view_movimientoinventario', content_type=inventario_ct),
            Permission.objects.get(codename='add_movimientoinventario', content_type=inventario_ct),
            Permission.objects.get(codename='change_movimientoinventario', content_type=inventario_ct),
            Permission.objects.get(codename='view_bodega', content_type=bodega_ct),
        ])
    except Permission.DoesNotExist:
        pass
    
    # Permisos de Dashboard (solo gráfica)
    try:
        permisos_bodega.append(
            Permission.objects.get(codename='ver_grafica', content_type=sistema_ct)
        )
    except Permission.DoesNotExist:
        pass
    
    # Asignar permisos al grupo
    grupo_bodega.permissions.set(permisos_bodega)
    
    # =============================
    # GRUPO CONSULTA
    # =============================
    grupo_consulta, created = Group.objects.get_or_create(name='CONSULTA')
    
    # Solo permisos de lectura
    permisos_consulta = [
        Permission.objects.get(codename='view_producto', content_type=producto_ct),
        Permission.objects.get(codename='view_proveedor', content_type=proveedor_ct),
    ]
    
    try:
        permisos_consulta.extend([
            Permission.objects.get(codename='view_movimientoinventario', content_type=inventario_ct),
            Permission.objects.get(codename='view_bodega', content_type=bodega_ct),
            Permission.objects.get(codename='ver_grafica', content_type=sistema_ct),
            Permission.objects.get(codename='ver_actividad', content_type=sistema_ct),
        ])
    except Permission.DoesNotExist:
        pass
    
    # Asignar permisos al grupo
    grupo_consulta.permissions.set(permisos_consulta)
    
    print("✅ Grupos BODEGA y CONSULTA creados con sus permisos")


def asignar_grupos_usuarios_existentes(apps, schema_editor):
    """
    Asigna grupos a usuarios existentes según su rol
    """
    Usuario = apps.get_model('usuarios', 'Usuario')
    
    for usuario in Usuario.objects.all():
        if usuario.rol == 'BODEGA':
            grupo = Group.objects.get(name='BODEGA')
            usuario.groups.add(grupo)
            print(f"✅ Usuario {usuario.username} asignado al grupo BODEGA")
        elif usuario.rol == 'CONSULTA':
            grupo = Group.objects.get(name='CONSULTA')
            usuario.groups.add(grupo)
            print(f"✅ Usuario {usuario.username} asignado al grupo CONSULTA")


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_alter_usuario_email'),
        ('productos', '__latest__'),
        ('proveedores', '__latest__'),
        ('inventario', '__latest__'),
        ('sistema', '__latest__'),
    ]

    operations = [
        migrations.RunPython(crear_grupos_y_permisos),
        migrations.RunPython(asignar_grupos_usuarios_existentes),
    ]