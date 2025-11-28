from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from productos.models import Producto
from .serializers import ProductoSerializer
def info(request):
    return JsonResponse({

  "proyecto": "vamos a la luna",

  "version": "1.0",

  "autor": "kevin ayala supremo"

})

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
