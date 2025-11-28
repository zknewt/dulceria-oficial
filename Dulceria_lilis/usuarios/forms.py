# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario
from django.core.exceptions import ValidationError
import re
from django.db import models


# =====================
# LOGIN FORM - ACTUALIZADO PARA django-axes
# =====================
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario o email'}),
        label="Usuario o email",
        required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña",
        required=False
    )

    # Mensajes de error mejorados y compatibles con django-axes
    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está inactiva.',
        # Este mensaje lo usa django-axes cuando la cuenta está bloqueada por intentos fallidos
        'locked': 'Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta más tarde.',
    }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username or not username.strip():
            raise ValidationError("Por favor, ingresa un usuario o email.")
        return username.strip()

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password or not password.strip():
            raise ValidationError("Por favor, ingresa una contraseña.")
        return password.strip()


# =====================
# USUARIO FORM - COMPLETO (sin cambios, todo conservado)
# =====================
class UsuarioForm(forms.ModelForm):
    ROL_CHOICES = [
        ('', 'Seleccione rol'),
        ('ADMIN', 'ADMIN'),
        ('BODEGA', 'BODEGA'),
        ('CONSULTA', 'CONSULTA'),
        ('PROVEEDOR', 'PROVEEDOR'),
        ('OPERADOR', 'OPERADOR'),
    ]
    ESTADO_CHOICES = [
        ('ACTIVO', 'ACTIVO'),
        ('BLOQUEADO', 'BLOQUEADO'),
        ('INACTIVO', 'INACTIVO'),
    ]

    
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    email = models.EmailField(blank=True, null=True)

    rol = forms.ChoiceField(
        choices=ROL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    email = forms.CharField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'nombres', 'apellidos', 'telefono',
            'rol', 'estado', 'mfa_habilitado', 'area', 'observaciones'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'mfa_habilitado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # === VALIDACIONES PERSONALIZADAS (todas conservadas) ===
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email or not email.strip():
            raise forms.ValidationError("Por favor, ingresa una dirección de correo electrónica.")
        email = email.strip()
        if '@' not in email:
            raise forms.ValidationError("El correo electrónico debe incluir el símbolo '@'.")
        patron = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if not re.match(patron, email):
            raise forms.ValidationError("El formato del correo electrónico no es válido.")
        if Usuario.objects.filter(email__iexact=email).exclude(
            pk=getattr(self.instance, 'pk', None)
        ).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono:
            raise forms.ValidationError("Por favor, ingresa un teléfono.")
        telefono = telefono.strip()
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números.")
        if len(telefono) != 9:
            raise forms.ValidationError("El teléfono debe tener exactamente 9 dígitos.")
        if re.match(r'^(\d)\1{8,}$', telefono):
            raise forms.ValidationError("El teléfono no debe contener secuencias repetidas.")
        return telefono

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) > 20:
            raise forms.ValidationError("El nombre de usuario no puede exceder los 20 caracteres.")
        if username and not username.isalnum():
            raise forms.ValidationError("El nombre de usuario debe contener solo caracteres alfanuméricos.")
        return username

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres')
        if not nombres or not nombres.strip():
            raise forms.ValidationError("Por favor, ingresa tu nombre.")
        if len(nombres) > 20:
            raise forms.ValidationError("El nombre no puede exceder los 20 caracteres.")
        if not nombres.replace(" ", "").isalpha():
            raise forms.ValidationError("El nombre debe contener solo letras.")
        return nombres.strip()

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')
        if not apellidos or not apellidos.strip():
            raise forms.ValidationError("Por favor, ingresa tus apellidos.")
        if len(apellidos) > 40:
            raise forms.ValidationError("Los apellidos no pueden exceder los 40 caracteres.")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s-]+$', apellidos.strip()):
            raise forms.ValidationError("Los apellidos deben contener solo letras y espacios.")
        return apellidos.strip()

    def clean_rol(self):
        rol = (self.cleaned_data.get('rol') or '').strip()
        if not rol:
            raise forms.ValidationError("Por favor, selecciona un rol.")
        return rol

    def clean_estado(self):
        estado = (self.cleaned_data.get('estado') or '').strip()
        if not estado:
            raise forms.ValidationError("Por favor, selecciona un estado.")
        return estado


# =====================
# PERFIL FORM (sin cambios)
# =====================
MAX_AVATAR_MB = 2
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["nombres", "apellidos", "email", "telefono", "avatar"]
        widgets = {
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = Usuario.objects.filter(email__iexact=email)
            if self.user:
                qs = qs.exclude(pk=self.user.pk)
            if qs.exists():
                raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_avatar(self):
        file = self.cleaned_data.get("avatar")
        if not file:
            return file
        if file.size > MAX_AVATAR_MB * 1024 * 1024:
            raise ValidationError(f"El avatar excede {MAX_AVATAR_MB} MB.")
        ctype = getattr(file, "content_type", None)
        if ctype and ctype.lower() not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValidationError("Formato no permitido. Usa JPG, PNG o WEBP.")
        return file
    
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class CambioClaveObligatorioForm(PasswordChangeForm):
    pass
