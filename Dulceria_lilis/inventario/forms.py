# inventario/forms.py
from django import forms
from django.utils import timezone
from productos.models import Producto
from .models import MovimientoInventario, Lote


class MovimientoInventarioForm(forms.ModelForm):
    fecha_mostrada = forms.DateTimeField(
        label="Fecha de registro",
        initial=timezone.localtime,
        disabled=True,
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control'},
            format='%d-%m-%Y %H:%M:%S'
        )
    )

    # PRODUCTO: se llena por proveedor (AJAX) – al inicio vacío
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'select-producto'})
    )

    class Meta:
        model = MovimientoInventario
        fields = [
            'fecha_mostrada', 'tipo', 'producto', 'proveedor', 'bodega_origen',
            'bodega_destino', 'cantidad', 'lote', 'serie', 'fecha_vencimiento',
            'observacion', 'documento_referencia'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select', 'id': 'select-proveedor'}),
            'bodega_origen': forms.Select(attrs={'class': 'form-select'}),
            'bodega_destino': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            # 👇 le damos un id fijo para usarlo en JS
            'lote': forms.Select(attrs={'class': 'form-select', 'id': 'select-lote'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'tipo': {'required': 'Por favor seleccione un tipo de movimiento.'},
            'producto': {'required': 'Por favor seleccione un producto.'},
            'proveedor': {'required': 'Por favor seleccione un proveedor.'},
            'cantidad': {'required': 'Ingrese la cantidad del movimiento.'},
            'bodega_origen': {'required': 'Seleccione la bodega de origen.'},
            'bodega_destino': {'required': 'Seleccione la bodega de destino.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---------- PRODUCTOS SEGÚN PROVEEDOR ----------
        proveedor_id = None

        if "proveedor" in self.data:
            try:
                proveedor_id = int(self.data.get("proveedor"))
            except (TypeError, ValueError):
                proveedor_id = None
        elif self.instance.pk and self.instance.proveedor_id:
            proveedor_id = self.instance.proveedor_id

        if proveedor_id:
            self.fields['producto'].queryset = Producto.objects.filter(
                productoproveedor__proveedor_id=proveedor_id
            )
        elif self.instance.pk and self.instance.producto_id:
            # para edición, mostrar al menos su producto
            self.fields['producto'].queryset = Producto.objects.filter(
                pk=self.instance.producto_id
            )
        else:
            self.fields['producto'].queryset = Producto.objects.none()

        # ---------- LOTES SEGÚN PRODUCTO (server side SOLO para edición/POST) ----------
        producto_id = None

        if "producto" in self.data:
            try:
                producto_id = int(self.data.get("producto"))
            except (TypeError, ValueError):
                producto_id = None
        elif self.instance.pk and self.instance.producto_id:
            producto_id = self.instance.producto_id

        if producto_id:
            qs = Lote.objects.filter(
                producto_id=producto_id,
                cantidad_disponible__gt=0
            )
            if self.instance.pk and self.instance.lote_id:
                qs = qs | Lote.objects.filter(pk=self.instance.lote_id)

            self.fields['lote'].queryset = qs.distinct()
        else:
            self.fields['lote'].queryset = Lote.objects.none()

    # ---------------- VALIDACIONES ----------------

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        origen = cleaned_data.get('bodega_origen')
        destino = cleaned_data.get('bodega_destino')
        producto = cleaned_data.get('producto')
        lote = cleaned_data.get('lote')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')

        # Transferencias
        if tipo == 'TRANSFERENCIA':
            if not origen:
                self.add_error('bodega_origen', "Debe seleccionar una bodega de origen.")
            if not destino:
                self.add_error('bodega_destino', "Debe seleccionar una bodega de destino.")
            if origen and destino and origen == destino:
                self.add_error('bodega_destino', "La bodega destino no puede ser igual a la de origen.")

        if not producto:
            return cleaned_data

        # Lote ↔ Producto
        if lote and lote.producto != producto:
            self.add_error('lote', "El lote seleccionado no corresponde al producto elegido.")

        # Producto con control por lote
        if producto.control_por_lote:
            if tipo in ('SALIDA', 'AJUSTE', 'TRANSFERENCIA') and not lote:
                self.add_error('lote', "Debe seleccionar un lote para este movimiento porque el producto se controla por lote.")

            if tipo in ('INGRESO', 'DEVOLUCION'):
                if producto.perishable and not fecha_vencimiento and not lote:
                    self.add_error(
                        'fecha_vencimiento',
                        "Debe indicar una fecha de vencimiento o usar un lote existente para productos perecibles."
                    )
        else:
            if producto.perishable and not fecha_vencimiento:
                self.add_error(
                    'fecha_vencimiento',
                    "Debe indicar una fecha de vencimiento para productos perecibles."
                )

        return cleaned_data
