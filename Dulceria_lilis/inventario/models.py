from django.db import models
from productos.models import Producto
from proveedores.models import Proveedor
from usuarios.models import Usuario

TIPO_MOVIMIENTO = [
    ('INGRESO', 'Ingreso'),
    ('SALIDA', 'Salida'),
    ('AJUSTE', 'Ajuste'),
    ('DEVOLUCION', 'Devolución'),
    ('TRANSFERENCIA', 'Transferencia'),
]

class Bodega(models.Model):
    codigo = models.CharField(max_length=50, unique=True)  # Ej: BOD-CENTRAL
    nombre = models.CharField(max_length=120)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Lote(models.Model):
    codigo = models.CharField(max_length=120, unique=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    bodega = models.ForeignKey(
        'Bodega',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotes'
    )
    fecha_vencimiento = models.DateField(blank=True, null=True)

    # Cantidad total y disponible
    cantidad_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cantidad_disponible = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.producto}"

    class Meta:
        ordering = ['-fecha_creacion']

    @staticmethod
    def generar_codigo(producto):
        """
        Genera un código único incremental por SKU
        Ejemplo:
            LOT-SKU001-0001
            LOT-SKU001-0002
        """
        base = f"LOT-{producto.sku}-"
        ultimo = (
            Lote.objects
            .filter(codigo__startswith=base)
            .order_by('-id')
            .first()
        )

        if not ultimo:
            num = 1
        else:
            try:
                num = int(ultimo.codigo.replace(base, '')) + 1
            except:
                num = 1

        return f"{base}{num:04d}"


class MovimientoInventario(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True)

    bodega_origen = models.ForeignKey(
        Bodega, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimientos_origen'
    )
    bodega_destino = models.ForeignKey(
        Bodega, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimientos_destino'
    )

    cantidad = models.DecimalField(max_digits=12, decimal_places=2)

    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    serie = models.CharField(max_length=120, blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    documento_referencia = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.producto} - {self.cantidad}"

    # ------------------------------------
    #             L Ó G I C A
    # ------------------------------------
    def _ajustar_stock_producto(self):
        prod = self.producto

        if self.tipo in ['INGRESO', 'DEVOLUCION']:
            prod.stock_actual += self.cantidad

        elif self.tipo in ['SALIDA']:
            prod.stock_actual -= self.cantidad
            if prod.stock_actual < 0:
                prod.stock_actual = 0

        elif self.tipo == 'AJUSTE':
            # Ajuste directo (+ o -)
            prod.stock_actual += self.cantidad

        prod.save()

    def _ajustar_lote(self):
        prod = self.producto
        controla = prod.control_por_lote

        # Si el producto NO se controla por lote → nada
        if not controla:
            return

        # ¿a qué bodega va el lote?
        bodega = self.bodega_destino or self.bodega_origen

        # INGRESOS
        if self.tipo in ['INGRESO', 'DEVOLUCION']:
            if self.lote:
                lote = self.lote
            else:
                # Crear lote automáticamente
                codigo = Lote.generar_codigo(prod)
                lote = Lote.objects.create(
                    codigo=codigo,
                    producto=prod,
                    bodega=bodega,
                    cantidad_inicial=0,
                    cantidad_disponible=0,
                    fecha_vencimiento=self.fecha_vencimiento
                )
                self.lote = lote

            lote.cantidad_inicial += self.cantidad
            lote.cantidad_disponible += self.cantidad
            lote.save()
            # ⚠ ALERTA POR STOCK BAJO
            if lote.cantidad_disponible <= lote.producto.stock_minimo:
                from django.contrib import messages
                messages.warning(
                    None,
                    f"⚠ Alerta: el stock del lote {lote.codigo} "
                    f"queda en {lote.cantidad_disponible}, por debajo del mínimo ({lote.producto.stock_minimo})"
                )

        # SALIDAS / AJUSTES / TRANSFERENCIAS
        else:
            if not self.lote:
                from django.core.exceptions import ValidationError
                raise ValidationError("Debe seleccionar lote para este movimiento.")

            lote = self.lote

            if lote.cantidad_disponible < self.cantidad:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"No hay stock suficiente en lote {lote.codigo} "
                    f"(Disponible: {lote.cantidad_disponible}, requerido: {self.cantidad})"
                )

            lote.cantidad_disponible -= self.cantidad
            lote.save()

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None

        if es_nuevo:
            self._ajustar_stock_producto()
            self._ajustar_lote()

        super().save(*args, **kwargs)
