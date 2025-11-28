from django.urls import path, include
from rest_framework import routers
from .views import info, ProductoViewSet

router = routers.DefaultRouter()
router.register(r'productos', ProductoViewSet)

urlpatterns = [
    path('info/', info, name='info'),
    path('', include(router.urls)),
]