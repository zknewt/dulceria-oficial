from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages

from productos.models import Producto
from proveedores.models import Proveedor
from inventario.models import MovimientoInventario
from usuarios.models import Usuario  # Modelo de usuario personalizado
from sistema.models import RegistroActividad  # Modelo de actividad


@login_required
def dashboard(request):
    # Contar visita solo si NO es AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        visitas = request.session.get('visitas', 0)
        request.session['visitas'] = visitas + 1
    else:
        visitas = request.session.get('visitas', 0)

    # Totales
    total_productos = Producto.objects.count()
    total_proveedores = Proveedor.objects.count()
    total_usuarios = Usuario.objects.count()
    total_inventario = MovimientoInventario.objects.count()

    # Categorías para el gráfico
    categorias = ['Productos', 'Proveedores', 'Usuarios', 'Inventario']
    data_categorias = [total_productos, total_proveedores, total_usuarios, total_inventario]

    # Últimos 5 registros de actividad
    logs_recientes = RegistroActividad.objects.select_related('usuario').order_by('-fecha')[:5]

    # Respuesta JSON si es AJAX (para actualizar gráfico)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not request.user.has_perm('sistema.ver_grafica'):
            return JsonResponse({'error': 'No autorizado'}, status=403)
        return JsonResponse({
            'categorias': categorias,
            'data_categorias': data_categorias
        })

    # Contexto para render
    contexto = {
        'categorias': categorias,
        'data_categorias': data_categorias,
        'total_productos': total_productos,
        'total_proveedores': total_proveedores,
        'total_usuarios': total_usuarios,
        'total_inventario': total_inventario,
        'visitas': visitas,
        'logs_recientes': logs_recientes,  # Para la tabla "Actividad reciente"
    }

    return render(request, 'dashboard.html', contexto)


@login_required
def cambiar_clave(request):
    # Crear una clave de sesión
    request.session['productos'] = {'sku': 1}
    messages.success(request, 'Clave "productos" creada en la sesión.')
    return redirect('dashboard')
