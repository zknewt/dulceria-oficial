# productos/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from sistema.decorators import permiso_requerido
from .models import Producto
from .forms import ProductoForm
from utils.export_excel import queryset_to_excel

# ------------------------------
# LISTAR PRODUCTOS (con buscar, paginador y exportar)
# ------------------------------
@method_decorator(permiso_requerido('productos.view_producto'), name='dispatch')
class ProductoListView(ListView):
    model = Producto
    template_name = 'productos/lista.html'
    context_object_name = 'productos'
    ordering = ['nombre']

    def _apply_filters(self, request, qs):
        session = request.session

        # Tomar valores desde GET
        buscar_get = request.GET.get('buscar')
        pp_get = request.GET.get('pp')

        # Limpiar filtros si viene clear=1
        if request.GET.get("clear") == "1":
            for k in ("f_buscar_prod", "f_pp_prod"):
                session.pop(k, None)
            return qs, "", 10

        # Guardar en sesión si vienen por GET
        if buscar_get is not None:
            session["f_buscar_prod"] = buscar_get
        if pp_get is not None:
            session["f_pp_prod"] = pp_get

        # Leer valores desde sesión
        buscar = request.GET.get("buscar", session.get("f_buscar_prod", ""))
        per_page = session.get("f_pp_prod", "10")

        # Aplicar filtros
        if buscar:
            qs = qs.filter(Q(sku__icontains=buscar) | Q(nombre__icontains=buscar))

        return qs, buscar, per_page

    def get(self, request, *args, **kwargs):
        productos = Producto.objects.all().order_by('nombre')

        if request.GET.get("live") == "1":
            request.session["f_buscar_prod"] = request.GET.get("buscar", "")
            request.session["f_pp_prod"] = request.GET.get("pp", "10")

        # ===== EXPORTAR EXCEL =====
        if request.GET.get("export") == "xlsx":
            productos, _, _ = self._apply_filters(request, productos)
            columns = [
                ("SKU", lambda p: p.sku),
                ("Nombre", lambda p: p.nombre),
                ("Categoría", lambda p: p.categoria),
                ("Marca", lambda p: p.marca or ""),
                ("Modelo", lambda p: p.modelo or ""),
                ("UOM Compra", lambda p: p.uom_compra),
                ("UOM Venta", lambda p: p.uom_venta),
                ("Factor conversión", lambda p: p.factor_conversion),
                ("Costo estándar", lambda p: float(p.costo_estandar) if p.costo_estandar else ""),
                ("Precio venta", lambda p: float(p.precio_venta) if p.precio_venta else ""),
                ("IVA %", lambda p: float(p.impuesto_iva) if p.impuesto_iva else ""),
                ("Stock actual", lambda p: p.stock_actual),
                ("Stock mínimo", lambda p: p.stock_minimo),
                ("Stock máximo", lambda p: p.stock_maximo or ""),
                ("Punto de reorden", lambda p: p.punto_reorden or ""),
                ("Perecible", lambda p: "Sí" if p.perishable else "No"),
                ("Control por lote", lambda p: "Sí" if p.control_por_lote else "No"),
                ("Control por serie", lambda p: "Sí" if p.control_por_serie else "No"),
            ]
            raw, fname = queryset_to_excel("productos", columns, productos)
            resp = HttpResponse(
                raw,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="{fname}"'
            return resp
        

        # ===== FILTROS =====
        productos, buscar, per_page = self._apply_filters(request, productos)

        # ===== PAGINADOR =====
        try:
            per_page_int = int(per_page)
        except (TypeError, ValueError):
            per_page_int = 10
        if per_page_int not in (5, 10, 200, 1500):
            per_page_int = 10

        paginator = Paginator(productos, per_page_int)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': ProductoForm(),
            'page_obj': page_obj,
            'productos': page_obj,
            'buscar': buscar,
            'per_page': per_page_int,
            'busqueda_activa': bool(buscar),
        }
        return render(request, self.template_name, context)

# ------------------------------
# CREAR PRODUCTO (POST desde lista)
# ------------------------------
@method_decorator(permiso_requerido('productos.add_producto'), name='dispatch')
class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        sku = form.cleaned_data.get('sku')
        ean = form.cleaned_data.get('ean_upc')

        if Producto.objects.filter(sku=sku).exists():
            form.add_error('sku', 'Ya existe un producto con este SKU.')
            return self.form_invalid(form)

        if ean and Producto.objects.filter(ean_upc=ean).exists():
            form.add_error('ean_upc', 'Ya existe un producto con este EAN/UPC.')
            return self.form_invalid(form)

        producto = form.save(commit=False)
        producto.stock_actual = 0
        producto.costo_promedio = 0
        producto.save()

        messages.success(self.request, f"Producto '{producto.nombre}' creado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        productos = Producto.objects.all().order_by('nombre')
        
        # Aplicar filtros y paginación
        buscar = self.request.session.get('f_buscar_prod', '')
        per_page = int(self.request.session.get('f_pp_prod', '10'))
        
        if buscar:
            productos = productos.filter(Q(sku__icontains=buscar) | Q(nombre__icontains=buscar))
        
        paginator = Paginator(productos, per_page)
        page_obj = paginator.get_page(1)
        
        messages.error(self.request, "Por favor complete todos los campos obligatorios correctamente.")
        return render(self.request, 'productos/lista.html', {
            'productos': page_obj,
            'page_obj': page_obj,
            'form': form,
            'buscar': buscar,
            'per_page': per_page,
        })


# ------------------------------
# EDITAR PRODUCTO
# ------------------------------
@method_decorator(permiso_requerido('productos.change_producto'), name='dispatch')
class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/form.html'
    success_url = reverse_lazy('productos:lista')

    def form_valid(self, form):
        producto = form.save(commit=False)
        producto.save()
        messages.success(self.request, f"Producto '{producto.nombre}' actualizado correctamente.")
        return super().form_valid(form)


# ------------------------------
# ELIMINAR PRODUCTO
# ------------------------------
@method_decorator(permiso_requerido('productos.delete_producto'), name='dispatch')
class ProductoDeleteView(DeleteView):
    model = Producto
    success_url = reverse_lazy('productos:lista')

    def get(self, request, *args, **kwargs):
        producto = get_object_or_404(Producto, pk=kwargs['pk'])
        producto.delete()
        messages.success(request, f"Producto '{producto.nombre}' eliminado correctamente.")
        return redirect(self.success_url)

# ------------------------------
# DETALLE DE PRODUCTO
# ------------------------------
@method_decorator(permiso_requerido('productos.view_producto'), name='dispatch')
class ProductoDetailView(DetailView):
    model = Producto
    template_name = 'productos/detalle.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['alerta_bajo_stock'] = self.object.alerta_bajo_stock()
        return ctx