# sistema/middleware.py
import threading

from django.shortcuts import redirect
from django.urls import reverse

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        _thread_locals.user = None
        return response
    
# 🔐 Middleware para forzar cambio de clave temporal
# 🔐 Middleware para forzar cambio de clave temporal
class ForzarCambioClaveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Rutas permitidas sin obligar cambio de clave
        rutas_exentas = [
            reverse('usuarios:login'),
            reverse('usuarios:logout'),
            reverse('usuarios:cambiar_clave_obligatorio'),
        ]

        # Si está autenticado, tiene la bandera activada y NO está en una ruta exenta → redirigir
        if (
            request.user.is_authenticated
            and getattr(request.user, "debe_cambiar_clave", False)
            and request.path not in rutas_exentas
        ):
            return redirect("usuarios:cambiar_clave_obligatorio")

        return self.get_response(request)
