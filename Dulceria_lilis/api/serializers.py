# api/serializers.py
from rest_framework import serializers
from productos.models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

    def validate(self, data):
        # Validación del nombre
        if 'nombre' in data and len(data['nombre']) < 3:
            raise serializers.ValidationError("El nombre debe tener mínimo 3 caracteres")

        # Costo y precio no negativos
        campos_numericos = ['costo_estandar', 'precio_venta', 'stock_minimo']
        for campo in campos_numericos:
            valor = data.get(campo, None)
            if valor is not None and valor < 0:
                raise serializers.ValidationError(f"El campo {campo} no puede ser negativo")

        # IVA entre 0% y 30%
        iva = data.get("impuesto_iva", None)
        if iva is not None and (iva < 0 or iva > 30):
            raise serializers.ValidationError("El IVA debe estar entre 0% y 30%")

        return data
