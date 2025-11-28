# usuarios/management/commands/inicializar_permisos.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Inicializa grupos y permisos para BODEGA y CONSULTA'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Inicializando grupos y permisos...'))

        # =============================
        # GRUPO BODEGA
        # =============================
        self.stdout.write('\n📦 Configurando grupo BODEGA...')
        grupo_bodega, created = Group.objects.get_or_create(name='BODEGA')
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Grupo BODEGA creado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Grupo BODEGA ya existe, actualizando permisos'))

        # Permisos de Productos
        try:
            producto_ct = ContentType.objects.get(app_label='productos', model='producto')
            permisos_bodega = [
                Permission.objects.get(codename='view_producto', content_type=producto_ct),
                Permission.objects.get(codename='add_producto', content_type=producto_ct),
                Permission.objects.get(codename='change_producto', content_type=producto_ct),
            ]
            self.stdout.write('  ✅ Permisos de Productos agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error en permisos de Productos: {e}'))
            permisos_bodega = []

        # Permisos de Inventario
        try:
            inventario_ct = ContentType.objects.get(app_label='inventario', model='movimientoinventario')
            bodega_ct = ContentType.objects.get(app_label='inventario', model='bodega')
            permisos_bodega.extend([
                Permission.objects.get(codename='view_movimientoinventario', content_type=inventario_ct),
                Permission.objects.get(codename='add_movimientoinventario', content_type=inventario_ct),
                Permission.objects.get(codename='change_movimientoinventario', content_type=inventario_ct),
                Permission.objects.get(codename='view_bodega', content_type=bodega_ct),
            ])
            self.stdout.write('  ✅ Permisos de Inventario agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Algunos permisos de Inventario no disponibles: {e}'))

        # Permisos de Dashboard
        try:
            sistema_ct = ContentType.objects.get(app_label='sistema', model='sistemanopermisos')
            permisos_bodega.append(
                Permission.objects.get(codename='ver_grafica', content_type=sistema_ct)
            )
            self.stdout.write('  ✅ Permisos de Dashboard agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Permisos de Dashboard no disponibles: {e}'))

        # Asignar permisos
        grupo_bodega.permissions.set(permisos_bodega)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Total permisos BODEGA: {len(permisos_bodega)}'))

        # =============================
        # GRUPO CONSULTA
        # =============================
        self.stdout.write('\n📊 Configurando grupo CONSULTA...')
        grupo_consulta, created = Group.objects.get_or_create(name='CONSULTA')
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✅ Grupo CONSULTA creado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Grupo CONSULTA ya existe, actualizando permisos'))

        # Solo permisos de lectura
        permisos_consulta = []
        
        try:
            producto_ct = ContentType.objects.get(app_label='productos', model='producto')
            proveedor_ct = ContentType.objects.get(app_label='proveedores', model='proveedor')
            permisos_consulta.extend([
                Permission.objects.get(codename='view_producto', content_type=producto_ct),
                Permission.objects.get(codename='view_proveedor', content_type=proveedor_ct),
            ])
            self.stdout.write('  ✅ Permisos de Productos y Proveedores agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))

        try:
            inventario_ct = ContentType.objects.get(app_label='inventario', model='movimientoinventario')
            bodega_ct = ContentType.objects.get(app_label='inventario', model='bodega')
            permisos_consulta.extend([
                Permission.objects.get(codename='view_movimientoinventario', content_type=inventario_ct),
                Permission.objects.get(codename='view_bodega', content_type=bodega_ct),
            ])
            self.stdout.write('  ✅ Permisos de Inventario agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Algunos permisos no disponibles: {e}'))

        try:
            sistema_ct = ContentType.objects.get(app_label='sistema', model='sistemanopermisos')
            permisos_consulta.extend([
                Permission.objects.get(codename='ver_grafica', content_type=sistema_ct),
                Permission.objects.get(codename='ver_actividad', content_type=sistema_ct),
            ])
            self.stdout.write('  ✅ Permisos de Dashboard agregados')
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  Permisos de Dashboard no disponibles: {e}'))

        # Asignar permisos
        grupo_consulta.permissions.set(permisos_consulta)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Total permisos CONSULTA: {len(permisos_consulta)}'))

        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✅ CONFIGURACIÓN COMPLETADA'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'\n📋 Grupos creados/actualizados:')
        self.stdout.write(f'  - BODEGA: {grupo_bodega.permissions.count()} permisos')
        self.stdout.write(f'  - CONSULTA: {grupo_consulta.permissions.count()} permisos')
        self.stdout.write('')