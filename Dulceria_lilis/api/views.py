# api/views.py
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminOrReadOnly
from django.http import Http404, JsonResponse
from .serializers import ProductoSerializer
from productos.models import Producto

def info(request):
    return JsonResponse({
        "proyecto": "Dulcería Lilis",
        "version": "1.0",
        "autor": "Kevin Ayala & Yearshon Orrego"
    })

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise NotFound("Producto no encontrado en Dulcería Lilis")

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"status": 500, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
