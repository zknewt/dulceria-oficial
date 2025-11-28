from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='lista'),
    path('crear/', views.ProductoCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/', views.ProductoDetailView.as_view(), name='detalle'),
]
