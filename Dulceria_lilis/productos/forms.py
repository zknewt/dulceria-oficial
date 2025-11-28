# productos/forms.py
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Producto

CATEGORIA_CHOICES = [
    ('ALFAJORES', 'ALFAJORES'),
    ('CUCHUFLIS', 'CUCHUFLIS'),
    ('TORTAS', 'TORTAS'),
    ('PRODUCTOS A GRANEL', 'PRODUCTOS A GRANEL'),
    ('CONFITERIA ARTESANAL', 'CONFITERIA ARTESANAL'),
    ('REPOSTERIA', 'REPOSTERIA'),

]
UOM_CHOICES = [
    ('UN', 'Unidad'),
    ('KG', 'Kilogramo'),
    ('PAQ', 'Paquete'),
    ('CJ', 'Caja'),
    ('G', 'Gramo'),
]

# Función para verificar si el valor contiene números
def contiene_numeros(valor):
    if re.search(r'\d', valor):  # Buscar números
        return True
    return False

# Función auxiliar para validar formato URL
def validar_url(valor):
    if valor and not valor.startswith(('http://', 'https://')):
        raise ValidationError("La URL debe comenzar con 'http://' o 'https://'.")

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Sku1'}),
            'ean_upc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Campo opcional'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}, choices=CATEGORIA_CHOICES),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'uom_compra': forms.Select(attrs={'class': 'form-select'}, choices=UOM_CHOICES),
            'uom_venta': forms.Select(attrs={'class': 'form-select'}, choices=UOM_CHOICES),
            'factor_conversion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1'}),
            'costo_estandar': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'costo_promedio': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'impuesto_iva': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '19.00'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_maximo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'punto_reorden': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'perishable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'control_por_lote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'control_por_serie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'imagen_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'ficha_tecnica_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Campo opcional'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
        }

        error_messages = {
            'sku': {'required': 'Ingrese el SKU del producto.'},
            'nombre': {'required': 'Ingrese el nombre del producto.'},
            'categoria': {'required': 'Ingrese la categoría del producto.'},
        }

# ==========================
    #  VALIDACIONES PERSONALIZADAS
    # ==========================

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').upper().strip()
        if not sku:
            raise ValidationError("El campo SKU es obligatorio.")
        if not re.match(r'^SKU[0-9]+$', sku):
            raise ValidationError("El SKU debe comenzar con 'Sku' seguido de un número positivo (ej: Sku1, Sku25).")

        qs = Producto.objects.filter(sku=sku)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Ya existe un producto con este SKU.")
        return sku

    def clean_ean_upc(self):
        ean = self.cleaned_data.get('ean_upc')
        if ean:
            if not re.match(r'^[0-9]{8,13}$', ean):
                raise ValidationError("El EAN/UPC debe tener entre 8 y 13 dígitos numéricos.")
            qs = Producto.objects.filter(ean_upc=ean)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ya existe un producto con este EAN/UPC.")
        return ean


    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError("Debe ingresar un nombre para el producto.")
        if len(nombre) > 20:
            raise ValidationError("El nombre del producto debe tener menos de 20 caracteres.")
        # Validación para asegurarse de que no contenga números
        if contiene_numeros(nombre):
            raise ValidationError("El nombre del producto no puede contener números.")
        return nombre

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria', '').strip()
        if not categoria:
            raise ValidationError("Debe ingresar una categoría.")
        # Validación para asegurarse de que no contenga números
        if contiene_numeros(categoria):
            raise ValidationError("La categoría no puede contener números.")
        return categoria

    def clean_marca(self):
        marca = self.cleaned_data.get('marca')
    
        if not marca:  # Si no hay valor para 'marca', lanzamos una validación
            raise ValidationError("El campo 'marca' no puede estar vacío.")
        if len(marca) > 20:  # Validamos que la marca tenga menos de 20 caracteres
            raise ValidationError("La marca debe tener menos de 20 caracteres.")
    
        marca = marca.strip()  # Si tiene valor, lo limpiamos
    
    # Validación: Si contiene números, lanzamos un error
        if contiene_numeros(marca):
            raise ValidationError("La marca no puede contener números.")
    
        return marca



    def clean_modelo(self):
        modelo = self.cleaned_data.get('modelo')
    
        if modelo:  # Solo ejecutamos strip() si hay valor
            modelo = modelo.strip()  # Limpiamos los espacios extra
    
    # Validación para asegurarnos que no contenga números
        if modelo and contiene_numeros(modelo):  # Si 'modelo' tiene valor, verificamos que no contenga números
            raise ValidationError("El modelo no puede contener números.")
    
        return modelo


    def clean_uom_compra(self):
        uom = self.cleaned_data.get('uom_compra')
        if uom not in dict(UOM_CHOICES):
            raise ValidationError(f"Unidad de medida inválida. Debe ser una de: {', '.join(dict(UOM_CHOICES).keys())}")
        return uom

    def clean_factor_conversion(self):
        factor = self.cleaned_data.get('factor_conversion')
        if factor is None or factor <= 0:
            raise ValidationError("El factor de conversión debe ser un número positivo.")
        return factor

    def clean_costo_estandar(self):
        val = self.cleaned_data.get('costo_estandar')
        if val is not None and val < 0:
            raise ValidationError("El costo estándar no puede ser negativo.")
        return val

    def clean_precio_venta(self):
        val = self.cleaned_data.get('precio_venta')
        if val is not None and val < 0:
            raise ValidationError("El precio de venta no puede ser negativo.")
        return val

    def clean_impuesto_iva(self):
        val = self.cleaned_data.get('impuesto_iva')
        if val is not None and (val < 0 or val > 100):
            raise ValidationError("El IVA debe estar entre 0 y 100%.")
        return val

    def clean_stock_minimo(self):
        stock_min = self.cleaned_data.get('stock_minimo')
        if stock_min is None or stock_min < 0:
            raise ValidationError("El stock mínimo no puede ser negativo.")
        return stock_min

    def clean_stock_maximo(self):
        stock_max = self.cleaned_data.get('stock_maximo')
        if stock_max is not None and stock_max < 0:
            raise ValidationError("El stock máximo no puede ser negativo.")
        return stock_max

    def clean_punto_reorden(self):
        punto_reorden = self.cleaned_data.get('punto_reorden')
        if punto_reorden is not None and punto_reorden < 0:
            raise ValidationError("El punto de reorden no puede ser negativo.")
        return punto_reorden

    def clean_perishable(self):
        perishable = self.cleaned_data.get('perishable')
        return perishable

    def clean_control_por_lote(self):
        control_lote = self.cleaned_data.get('control_por_lote')
        return control_lote

    def clean_control_por_serie(self):
        control_serie = self.cleaned_data.get('control_por_serie')
        return control_serie

    def clean_imagen_url(self):
        imagen_url = self.cleaned_data.get('imagen_url')
        validar_url(imagen_url)
        return imagen_url

    def clean_ficha_tecnica_url(self):
        ficha_tecnica_url = self.cleaned_data.get('ficha_tecnica_url')
        validar_url(ficha_tecnica_url)
        return ficha_tecnica_url

    def clean_stock_actual(self):
        return self.cleaned_data.get('stock_actual', 0)
    
    # ---  Validaciones para la sección de inventario ---
    def clean_costo_promedio(self):
        costo_promedio = self.cleaned_data.get('costo_promedio')
        if costo_promedio is not None and costo_promedio < 0:
            raise ValidationError("El costo promedio no puede ser negativo.")
        return costo_promedio

    def clean_stock_actual(self):
        stock_actual = self.cleaned_data.get('stock_actual')
        if stock_actual is not None and stock_actual < 0:
            raise ValidationError("El stock actual no puede ser negativo.")
        return stock_actual
    
    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if len(descripcion) > 1000:
            raise ValidationError("La descripción debe tener menos de 1000 caracteres.")
        return descripcion
        