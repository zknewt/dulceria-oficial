from django.urls import path
from . import views


app_name = 'inventario'

urlpatterns = [
    path('', views.MovimientoInventarioListCreateView.as_view(), name='inicio'),
    path("productos-por-proveedor/<int:proveedor_id>/", views.productos_por_proveedor, name="productos_por_proveedor"),
    path("lotes-por-producto/<int:producto_id>/", views.lotes_por_producto, name="lotes_por_producto"),
    path('movimiento/<int:pk>/editar/', views.MovimientoInventarioUpdateView.as_view(), name='editar_movimiento'),
    path('movimiento/<int:pk>/', views.MovimientoInventarioDetailView.as_view(), name='detalle_movimiento'),
    path('bodegas/', views.BodegaListView.as_view(), name='lista_bodegas'),
]
