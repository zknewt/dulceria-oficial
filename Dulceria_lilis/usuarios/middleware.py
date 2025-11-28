# usuarios/middleware.py
from django.utils.deprecation import MiddlewareMixin


class NoCacheAuthenticatedMiddleware(MiddlewareMixin):
    """
    Agrega headers anti-caché a TODAS las páginas de usuarios autenticados.
    Refuerza S-SES-02: evita volver atrás después de logout.
    """
    def process_response(self, request, response):
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
