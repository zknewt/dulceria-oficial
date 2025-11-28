from django import forms
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
import re
from .models import Proveedor, ProductoProveedor, Producto

# Validación personalizada para la URL del sitio web
def validar_sitio_web(value):
    # Si el campo no está vacío, validar si la URL tiene esquema (http:// o https://)
    if value:
        parsed_url = urlparse(value)
        # Extraer el dominio de la URL (el nombre que está antes del primer "/")
        domain = parsed_url.netloc or parsed_url.path  # Si no hay netloc, usamos el path
        
        if not parsed_url.scheme:
            # Si no tiene esquema (http:// o https://), mostrar el mensaje de error con el dominio
            raise ValidationError(
                f'La URL está mal escrita. Debe incluir el esquema como "http://{domain}.cl" en lugar de "{domain}".'
            )

# Opciones para las condiciones de pago
CONDICIONES_PAGO_CHOICES = [
    ('EFECTIVO', 'EFECTIVO'),
    ('DEBITO', 'DEBITO'),
    ('TRANSFERENCIA', 'TRANSFERENCIA'),
]

# Opciones para la moneda
MONEDA_CHOICES = [
    ('CLP', 'CLP'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
]

class ProveedorForm(forms.ModelForm):
    # Usamos CharField para el sitio web y le agregamos un validador personalizado
    sitio_web = forms.CharField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
        validators=[validar_sitio_web]  # Validación personalizada
    )
    
    condiciones_pago = forms.ChoiceField(
        choices=CONDICIONES_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Seleccione una condición de pago válida.'}
    )

    moneda = forms.ChoiceField(
        choices=MONEDA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Seleccione una moneda válida.'}
    )
    email = forms.CharField(
    widget=forms.TextInput(attrs={'class': 'form-control'}),
    error_messages={'required': 'Ingrese el email del proveedor.'}
        )
    pais = forms.CharField(
    widget=forms.TextInput(attrs={'class': 'form-control'}),
    error_messages={'required': 'Ingrese el pais.'}
        )


    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'rut_nif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre_fantasia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'contacto_principal_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'contacto_principal_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'contacto_principal_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Campo opcional'}),
        }
        error_messages = {
            'rut_nif': {'required': 'Ingrese el RUT del proveedor.'},
            'razon_social': {'required': 'Ingrese la razón social del proveedor.'},
            'email': {'required': 'Ingrese el email del proveedor.'},
            'condiciones_pago': {'required': 'Seleccione una condición de pago válida.'},
        }

        # Validación de email
    def clean_email(self):
        email = self.cleaned_data.get("email")
        # bloquea nombres con solo números
        patron = r'^[A-Za-z][A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if not re.match(patron, email):
            raise ValidationError("Ingrese un email válido. Ej: nombre@dominio.cl")
            # Bloquear correos donde la parte antes del @ sea SOLO números
        local_part = email.split("@")[0]
        if local_part.isdigit():  
            raise ValidationError("El email no puede tener solo números antes del '@'.")
        # Bloquear correos tipo: 1@dominio.cl
        if len(local_part) < 2:
            raise ValidationError("La parte antes del '@' debe tener al menos 2 caracteres.")
        return email

    
    # Validación de RUT
    def clean_rut_nif(self):
        rut = self.cleaned_data['rut_nif'].upper().replace('.', '').replace('-', '')

        # ---- 1. Validación de formato (7 u 8 dígitos + DV)
        if not re.match(r'^\d{7,8}[0-9K]$', rut):
            raise ValidationError("Formato de RUT inválido. Ejemplo válido: 21983048-3")

        cuerpo, dv = rut[:-1], rut[-1]

        # ---- 2. Bloquear cuerpos repetidos (22.222.222-2, 33.333.333-3...)
        if cuerpo == cuerpo[0] * len(cuerpo):
            raise ValidationError("El RUT no puede tener todos los dígitos repetidos.")

        # ---- 3. Bloquear cuerpos muy comunes falsos
        RUT_INVALIDOS = {
            "11111111", "12345678", "22222222", "33333333", "44444444",
            "55555555", "66666666", "77777777", "88888888", "99999999",
            "00000000"
        }

        if cuerpo in RUT_INVALIDOS:
            raise ValidationError("Este RUT es inválido.")

        # ---- 4. Validación del dígito verificador
        suma, multiplo = 0, 2
        for c in reversed(cuerpo):
            suma += int(c) * multiplo
            multiplo = multiplo + 1 if multiplo < 7 else 2

        resto = suma % 11
        calc = 11 - resto
        dv_esperado = (
            '0' if calc == 11 else
            'K' if calc == 10 else
            str(calc)
        )

        if dv != dv_esperado:
            raise ValidationError("RUT inválido. El dígito verificador no coincide.")

        # ---- 5. Retorno en formato estándar
        return f"{cuerpo}-{dv}"

    # Validación de teléfono
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
    
        if not telefono:
            return telefono  # Si el teléfono está vacío, lo dejamos pasar.
    
        if not telefono.isdigit():
            raise ValidationError("El teléfono debe contener solo números.")
    
        if len(telefono) != 9:
            raise ValidationError("El teléfono debe tener exactamente 9 dígitos.")
    
        if re.match(r'^(\d)\1{8,}$', telefono):
            raise ValidationError(f"El teléfono no debe contener secuencias repetidas como {telefono[0] * 9}.")
    
        return telefono
    
    def clean_nombre_fantasia(self):
        nombre_fantasia = self.cleaned_data.get('nombre_fantasia')
        if not nombre_fantasia:
            return nombre_fantasia
        if len(nombre_fantasia) > 20:
            raise ValidationError("El nombre de fantasia no puede exceder los 20 caracteres.")
        if nombre_fantasia and not nombre_fantasia.isalpha():
            raise ValidationError("El nombre de fantasia debe contener solo letras.")
        return nombre_fantasia
    
    def clean_razon_social(self):
        razon_social = self.cleaned_data.get('razon_social')
        if not razon_social:
            return razon_social
        if len(razon_social) > 20:
            raise ValidationError("La razon social no puede exceder los 20 caracteres.")
        if razon_social and not razon_social.isalpha():
            raise ValidationError("La razon social debe contener solo letras.")
        return razon_social
    
    def clean_direccion(self):
        direccion = self.cleaned_data.get("direccion")

        if not direccion:
            return direccion  # es opcional

        if len(direccion) < 5:
            raise ValidationError("La dirección debe tener al menos 5 caracteres.")
        if len(direccion) > 100:
            raise ValidationError("La dirección debe tener maximo 100 caracteres.")

        if not re.match(r"^[A-Za-z0-9ÁÉÍÓÚÑáéíóúñ\s\-\#\.,]+$", direccion):
            raise ValidationError("La dirección contiene caracteres no permitidos.")
        return direccion
    
    def clean_ciudad(self):
        ciudad = self.cleaned_data.get("ciudad")

        if not ciudad:
            return ciudad  # opcional

        if len(ciudad) < 3:
            raise ValidationError("La ciudad debe tener al menos 3 caracteres.")
        if len(ciudad) > 30:
            raise ValidationError("La ciudad debe tener menos de 30 caracteres.")

        if not re.match(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$", ciudad):
            raise ValidationError("La ciudad solo puede contener letras.")

        return ciudad

    def clean_pais(self):
        pais = self.cleaned_data.get("pais")

        if not pais:
            return pais  # opcional

        if len(pais) < 3:
            raise ValidationError("El país debe tener al menos 3 caracteres.")

        if not re.match(r"^[A-Za-zÁÉÍÓÚÑáéíóúñ\s]+$", pais):
            raise ValidationError("El país solo puede contener letras.")

        return pais



# Formulario para el modelo ProductoProveedor
class ProductoProveedorInlineForm(forms.ModelForm):
    class Meta:
        model = ProductoProveedor
        fields = ["producto", "costo", "lead_time_dias", "min_lote", "descuento_pct", "preferente"]
        widgets = {
            "producto": forms.Select(attrs={"class": "form-select"}),
            "costo": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej: 1500.00"}),
            "lead_time_dias": forms.NumberInput(attrs={"class": "form-control"}),
            "min_lote": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "descuento_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "preferente": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar data-costo a cada <option>
        productos = Producto.objects.all()
        self.fields["producto"].queryset = productos
        self.costo_producto = {
            p.id: float(p.costo_estandar or 0) for p in productos
        }
    def clean_costo(self):
        costo = self.cleaned_data.get("costo")

        if costo is None:
            raise ValidationError("El costo es obligatorio.")

        if costo <= 0:
            raise ValidationError("El costo debe ser mayor a 0.")

        return costo
    
    def clean_lead_time_dias(self):
        lt = self.cleaned_data.get("lead_time_dias")

        if lt is None:
            raise ValidationError("El lead time es obligatorio.")

        if lt <= 0:
            raise ValidationError("El lead time debe ser mayor a 0 días.")

        if lt > 365:
            raise ValidationError("El lead time no puede superar 365 días.")
        return lt
    
    def clean_min_lote(self):
        min_lote = self.cleaned_data.get("min_lote")

        if min_lote is None:
            raise ValidationError("El mínimo de lote es obligatorio.")

        if min_lote <= 0:
            raise ValidationError("El mínimo de lote debe ser mayor a 0.")

        return min_lote
    
    def clean_descuento_pct(self):
        descuento = self.cleaned_data.get("descuento_pct")

        if descuento is None:
            return descuento  # opcional

        if descuento < 0 or descuento > 100:
            raise ValidationError("El descuento debe estar entre 0% y 100%.")

        return descuento

ProductoProveedorFormSet = forms.inlineformset_factory(
    Proveedor,
    ProductoProveedor,
    form=ProductoProveedorInlineForm,
    fk_name='proveedor',
    extra=1,
    can_delete=True,
)

class ProductoRelacionForm(forms.Form):

    producto_rel = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    costo_rel = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={'invalid': "Ingrese un costo válido."}
    )

    lead_time_rel = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={'invalid': "Ingrese un lead time válido."}
    )

    min_lote_rel = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={'invalid': "Ingrese un mínimo de lote válido."}
    )

    descuento_rel = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={'invalid': "Ingrese un descuento válido."}
    )

    preferente_rel = forms.BooleanField(required=False)

    # =====================================================
    # 🔹 VALIDACIONES INDIVIDUALES (para errores en el campo)
    # =====================================================

    def clean_producto_rel(self):
        producto = self.cleaned_data.get("producto_rel")
        if producto is None:
            raise ValidationError("Seleccione un producto.")
        return producto

    def clean_costo_rel(self):
        dato_raw = self.data.get("costo_rel")
        costo = self.cleaned_data.get("costo_rel")
        if dato_raw is None or dato_raw.strip() == '':
            raise ValidationError("El costo es obligatorio.")
        if costo is None:
            raise ValidationError("Ingrese un costo valido (solo numeros).")
        if costo <= 0:
            raise ValidationError("El costo debe ser mayor a 0.")
        return costo

    def clean_lead_time_rel(self):
        lt_raw = self.data.get("lead_time_rel")
        lt = self.cleaned_data.get("lead_time_rel")
        if lt_raw is None or lt_raw.strip() == '':
            raise ValidationError("El lead time es obligatorio.")
        if lt is None:
            raise ValidationError("Ingrese un lead time valido (solo numeros).")
        if lt <= 0:
            raise ValidationError("El lead time debe ser mayor a 0 días.")
        if lt > 365:
            raise ValidationError("El lead time no puede superar 365 días.")
        return lt

    def clean_min_lote_rel(self):
        ml_raw = self.data.get("min_lote_rel")
        ml = self.cleaned_data.get("min_lote_rel")
        if ml_raw is None or ml_raw.strip() == '':
            raise ValidationError("El mínimo de lote es obligatorio.")
        if ml is None:
            raise ValidationError("Ingrese un mínimo de lote valido (solo numeros).")
        if ml <= 0:
            raise ValidationError("El mínimo de lote debe ser mayor a 0.")
        if ml > 1000:
            raise ValidationError("El mínimo de lote no puede superar 1000.")
        return ml

    def clean_descuento_rel(self):
        desc = self.cleaned_data.get("descuento_rel")
        if desc is None:
            return desc
        if desc < 0 or desc > 100:
            raise ValidationError("El descuento debe estar entre 0% y 100%.")
        return desc
