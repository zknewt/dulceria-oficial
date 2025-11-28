from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

class SistemaPermisos(models.Model):
    class Meta:
        managed = False  # No crea tabla
        permissions = [
            ("ver_grafica", "Puede ver la gráfica"),
            ("ver_actividad", "Puede ver la actividad"),
        ]

User = get_user_model()

class RegistroActividad(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(max_length=500)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    objeto_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Registro de Actividad"
        verbose_name_plural = "Registros de Actividad"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} - {self.usuario or 'Sistema'} - {self.descripcion[:60]}"