from django.db import models
from productos.models import Producto

class Proveedor(models.Model):
    # Identificación legal
    rut_nif = models.CharField(max_length=20, unique=True)
    razon_social = models.CharField(max_length=255)
    nombre_fantasia = models.CharField(max_length=255, blank=True, null=True)

    # Contacto
    email = models.EmailField(max_length=254)  # requerido
    telefono = models.CharField(max_length=30, blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)  # opcional

    # Dirección
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=128, blank=True, null=True)
    pais = models.CharField(max_length=64, default='Chile')

    # Comercial
    condiciones_pago = models.CharField(max_length=100)  # requerido
    moneda = models.CharField(max_length=8, default='CLP')
    contacto_principal_nombre = models.CharField(max_length=120, blank=True, null=True)
    contacto_principal_email = models.EmailField(blank=True, null=True)
    contacto_principal_telefono = models.CharField(max_length=30, blank=True, null=True)

    ESTADO_CHOICES = (
        ('ACTIVO', 'ACTIVO'),
        ('BLOQUEADO', 'BLOQUEADO'),
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVO')

    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.razon_social


class ProductoProveedor(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    costo = models.DecimalField(max_digits=18, decimal_places=6)  # requerido
    lead_time_dias = models.IntegerField(default=7)  # requerido con default
    min_lote = models.DecimalField(max_digits=18, decimal_places=6, blank=True, null=True, default=1)
    descuento_pct = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    preferente = models.BooleanField(default=False)

    class Meta:
        unique_together = ('producto', 'proveedor')

    def __str__(self):
        return f"{self.proveedor} - {self.producto}"
