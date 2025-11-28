from django.db import models
from django.contrib.auth.models import AbstractUser

def avatar_upload_path(instance, filename):
    
    return f"avatars/u{instance.id}/{filename}"

class Usuario(AbstractUser):
    nombres = models.CharField("Nombres", max_length=150, blank=True, null=True)
    apellidos = models.CharField("Apellidos", max_length=150, blank=True, null=True)
    email = models.EmailField("Email", unique=True, blank=False, null=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True, null=True)
    rol = models.CharField("Rol", max_length=50, default='Usuario', blank=True, null=True)# Admin, Proveedor, Encargado
    estado = models.CharField("Estado", max_length=20, default='ACTIVO')  # ACTIVO, BLOQUEADO
    mfa_habilitado = models.BooleanField("MFA habilitado", default=False)
    ultimo_acceso = models.DateTimeField("Último acceso", blank=True, null=True)
    area = models.CharField("Área/Unidad", max_length=100, blank=True, null=True)
    observaciones = models.TextField("Observaciones", blank=True, null=True)
    sesiones = models.PositiveIntegerField("Sesiones", default=0)
    avatar = models.ImageField("Avatar", upload_to=avatar_upload_path, blank=True, null=True)
    debe_cambiar_clave = models.BooleanField(default=False, help_text="Indica si el usuario debe cambiar su clave en el próximo login")

    def __str__(self):
        nombre_completo = ' '.join(filter(None, [self.nombres, self.apellidos])).strip()
        return nombre_completo or self.get_full_name() or self.username
    
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/img/avatar-default.png"