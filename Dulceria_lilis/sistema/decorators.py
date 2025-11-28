# sistema/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def permiso_requerido(permiso, redireccion='productos:lista'):
    def decorador(vista_funcion):
        @login_required
        def envoltura(request, *args, **kwargs):
            if request.user.has_perm(permiso):
                return vista_funcion(request, *args, **kwargs)
            else:
                messages.error(request, "No tienes permiso para realizar esta acción.")
                return redirect(redireccion)
        return envoltura
    return decorador