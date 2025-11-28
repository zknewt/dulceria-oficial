# management/commands/generar_datos_prueba.py
"""
Script para generar datos masivos de prueba
Ejecutar: python manage.py generar_datos_prueba
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from productos.models import Producto
from proveedores.models import Proveedor, ProductoProveedor
from inventario.models import MovimientoInventario, Bodega, Lote
from usuarios.models import Usuario
from faker import Faker
import random
from decimal import Decimal

fake = Faker('es_CL')  # Datos en español chileno

class Command(BaseCommand):
    help = 'Genera datos de prueba masivos para stress testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--productos',
            type=int,
            default=10000,
            help='Cantidad de productos a crear (default: 10000)'
        )
        parser.add_argument(
            '--proveedores',
            type=int,
            default=5000,
            help='Cantidad de proveedores a crear (default: 5000)'
        )
        parser.add_argument(
            '--movimientos',
            type=int,
            default=15000,
            help='Cantidad de movimientos de inventario (default: 15000)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚀 Iniciando generación de datos de prueba...'))
        
        cant_productos = options['productos']
        cant_proveedores = options['proveedores']
        cant_movimientos = options['movimientos']

        # 1. CREAR PRODUCTOS
        self.stdout.write(self.style.SUCCESS(f'📦 Generando {cant_productos} productos...'))
        self.crear_productos(cant_productos)

        # 2. CREAR PROVEEDORES
        self.stdout.write(self.style.SUCCESS(f'🏢 Generando {cant_proveedores} proveedores...'))
        self.crear_proveedores(cant_proveedores)

        # 3. RELACIONAR PRODUCTOS CON PROVEEDORES
        self.stdout.write(self.style.SUCCESS('🔗 Relacionando productos con proveedores...'))
        self.relacionar_productos_proveedores()

        # 4. CREAR MOVIMIENTOS DE INVENTARIO
        self.stdout.write(self.style.SUCCESS(f'📋 Generando {cant_movimientos} movimientos de inventario...'))
        self.crear_movimientos(cant_movimientos)

        self.stdout.write(self.style.SUCCESS('✅ ¡Datos de prueba generados exitosamente!'))

    @transaction.atomic
    def crear_productos(self, cantidad):
        """Crea productos en lotes para mejor rendimiento"""
        categorias = ['ALFAJORES', 'CUCHUFLIS', 'TORTAS', 'PRODUCTOS A GRANEL', 
                      'CONFITERIA ARTESANAL', 'REPOSTERIA']
        marcas = ['Lili', 'Dulcemar', 'Confitería del Sur', 'Artesanal', 'Premium']
        uoms = ['UN', 'KG', 'PAQ', 'CJ', 'G']
        
        productos = []
        batch_size = 1000  # Insertar en lotes de 1000

        for i in range(1, cantidad + 1):
            productos.append(Producto(
                sku=f'SKU{i:06d}',
                ean_upc=fake.ean13() if random.choice([True, False]) else None,
                nombre=f'{fake.word().capitalize()} {random.choice(categorias)}',
                descripcion=fake.text(max_nb_chars=100) if random.choice([True, False]) else None,
                categoria=random.choice(categorias),
                marca=random.choice(marcas),
                modelo=f'MOD-{fake.bothify(text="??##")}' if random.choice([True, False]) else None,
                uom_compra=random.choice(uoms),
                uom_venta=random.choice(uoms),
                factor_conversion=Decimal(random.uniform(1, 10)),
                costo_estandar=Decimal(random.randint(100, 10000)),
                costo_promedio=Decimal(random.randint(100, 10000)),
                precio_venta=Decimal(random.randint(200, 15000)),
                impuesto_iva=Decimal('19.00'),
                stock_minimo=Decimal(random.randint(10, 100)),
                stock_maximo=Decimal(random.randint(200, 1000)),
                punto_reorden=Decimal(random.randint(20, 150)),
                perishable=random.choice([True, False]),
                control_por_lote=random.choice([True, False]),
                control_por_serie=random.choice([True, False]),
                stock_actual=Decimal(random.randint(0, 500)),
            ))

            # Insertar en lotes
            if len(productos) >= batch_size:
                Producto.objects.bulk_create(productos, ignore_conflicts=True)
                self.stdout.write(f'  ✓ {i}/{cantidad} productos creados')
                productos = []

        # Insertar productos restantes
        if productos:
            Producto.objects.bulk_create(productos, ignore_conflicts=True)
            self.stdout.write(f'  ✓ {cantidad}/{cantidad} productos creados')

    @transaction.atomic
    def crear_proveedores(self, cantidad):
        """Crea proveedores en lotes"""
        estados = ['ACTIVO', 'BLOQUEADO']
        condiciones = ['EFECTIVO', 'DEBITO', 'TRANSFERENCIA']
        monedas = ['CLP', 'USD', 'EUR']
        
        proveedores = []
        batch_size = 1000

        for i in range(1, cantidad + 1):
            rut = self.generar_rut()
            
            proveedores.append(Proveedor(
                rut_nif=rut,
                razon_social=fake.company(),
                nombre_fantasia=fake.company() if random.choice([True, False]) else None,
                email=fake.company_email(),
                telefono=fake.phone_number()[:9] if random.choice([True, False]) else None,
                sitio_web=fake.url() if random.choice([True, False]) else None,
                direccion=fake.address() if random.choice([True, False]) else None,
                ciudad=fake.city() if random.choice([True, False]) else None,
                pais='Chile',
                condiciones_pago=random.choice(condiciones),
                moneda=random.choice(monedas),
                contacto_principal_nombre=fake.name() if random.choice([True, False]) else None,
                contacto_principal_email=fake.email() if random.choice([True, False]) else None,
                contacto_principal_telefono=fake.phone_number()[:9] if random.choice([True, False]) else None,
                estado=random.choice(estados),
                observaciones=fake.text(max_nb_chars=100) if random.choice([True, False]) else None,
            ))

            if len(proveedores) >= batch_size:
                Proveedor.objects.bulk_create(proveedores, ignore_conflicts=True)
                self.stdout.write(f'  ✓ {i}/{cantidad} proveedores creados')
                proveedores = []

        if proveedores:
            Proveedor.objects.bulk_create(proveedores, ignore_conflicts=True)
            self.stdout.write(f'  ✓ {cantidad}/{cantidad} proveedores creados')

    def generar_rut(self):
        """Genera un RUT chileno válido"""
        num = random.randint(10000000, 25000000)
        suma = 0
        multiplo = 2
        
        for c in reversed(str(num)):
            suma += int(c) * multiplo
            multiplo = multiplo + 1 if multiplo < 7 else 2
        
        resto = suma % 11
        dv = 11 - resto
        
        if dv == 11:
            dv = '0'
        elif dv == 10:
            dv = 'K'
        else:
            dv = str(dv)
        
        return f"{num}-{dv}"

    @transaction.atomic
    def relacionar_productos_proveedores(self):
        """Relaciona productos con proveedores aleatoriamente"""
        productos = list(Producto.objects.all()[:5000])  # Primeros 5000
        proveedores = list(Proveedor.objects.all()[:1000])  # Primeros 1000
        
        relaciones = []
        batch_size = 1000
        
        for producto in productos:
            # Cada producto tiene entre 1 y 3 proveedores
            cant_provs = random.randint(1, 3)
            provs_elegidos = random.sample(proveedores, min(cant_provs, len(proveedores)))
            
            for proveedor in provs_elegidos:
                relaciones.append(ProductoProveedor(
                    producto=producto,
                    proveedor=proveedor,
                    costo=Decimal(random.randint(100, 5000)),
                    lead_time_dias=random.randint(1, 30),
                    min_lote=Decimal(random.randint(1, 100)),
                    descuento_pct=Decimal(random.uniform(0, 15)),
                    preferente=random.choice([True, False]),
                ))
                
                if len(relaciones) >= batch_size:
                    ProductoProveedor.objects.bulk_create(relaciones, ignore_conflicts=True)
                    relaciones = []
        
        if relaciones:
            ProductoProveedor.objects.bulk_create(relaciones, ignore_conflicts=True)

    @transaction.atomic
    def crear_movimientos(self, cantidad):
        """Crea movimientos de inventario"""
        productos = list(Producto.objects.all()[:1000])
        proveedores = list(Proveedor.objects.all()[:500])
        bodegas = list(Bodega.objects.all())
        usuarios = list(Usuario.objects.filter(is_active=True)[:5])
        
        if not bodegas:
            self.stdout.write(self.style.ERROR('❌ No hay bodegas. Crea al menos una bodega primero.'))
            return
        
        if not usuarios:
            self.stdout.write(self.style.ERROR('❌ No hay usuarios activos.'))
            return
        
        tipos = ['INGRESO', 'SALIDA', 'AJUSTE', 'DEVOLUCION', 'TRANSFERENCIA']
        movimientos = []
        batch_size = 1000
        
        for i in range(1, cantidad + 1):
            tipo = random.choice(tipos)
            producto = random.choice(productos)
            
            mov = MovimientoInventario(
                tipo=tipo,
                producto=producto,
                proveedor=random.choice(proveedores) if random.choice([True, False]) else None,
                bodega_origen=random.choice(bodegas) if tipo in ['SALIDA', 'TRANSFERENCIA'] else None,
                bodega_destino=random.choice(bodegas) if tipo in ['INGRESO', 'TRANSFERENCIA'] else None,
                cantidad=Decimal(random.randint(1, 100)),
                serie=fake.bothify(text='SER-####') if random.choice([True, False]) else None,
                fecha_vencimiento=fake.date_between(start_date='today', end_date='+2y') if producto.perishable else None,
                usuario=random.choice(usuarios),
                observacion=fake.sentence() if random.choice([True, False]) else None,
                documento_referencia=fake.bothify(text='DOC-#####') if random.choice([True, False]) else None,
            )
            movimientos.append(mov)
            
            if len(movimientos) >= batch_size:
                # Guardar sin ejecutar lógica de stock (para rapidez)
                for m in movimientos:
                    m.save()
                self.stdout.write(f'  ✓ {i}/{cantidad} movimientos creados')
                movimientos = []
        
        if movimientos:
            for m in movimientos:
                m.save()
            self.stdout.write(f'  ✓ {cantidad}/{cantidad} movimientos creados')