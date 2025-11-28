# proveedores/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Proveedor, ProductoProveedor, Producto
from .forms import ProveedorForm, ProductoProveedorFormSet, ProductoRelacionForm
from sistema.decorators import permiso_requerido
from utils.export_excel import queryset_to_excel


# ----------------------------------------------------------
# LISTAR PROVEEDORES + CREAR (con paginador)
# ----------------------------------------------------------
class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'proveedores/lista_proveedor.html'
    context_object_name = 'proveedores'
    ordering = ['razon_social']

    def _apply_filters(self, request, qs):
        session = request.session

        # Tomar valores desde GET
        buscar_get = request.GET.get("buscar_Rut_Nif")
        pp_get = request.GET.get('pp')

        # Limpiar filtros si viene clear=1
        if request.GET.get("clear") == "1":
            for k in ("f_buscar_Rut_Nif", "f_pp_prov"):
                session.pop(k, None)
            return qs, "", 10

        # Guardar en sesión si vienen por GET
        if buscar_get is not None:
            session["f_buscar_Rut_Nif"] = buscar_get
        if pp_get is not None:
            session["f_pp_prov"] = pp_get

        # Leer valores desde sesión
        buscar = session.get("f_buscar_Rut_Nif", "")
        per_page = session.get("f_pp_prov", "10")

        # Aplicar filtros
        if buscar:
            qs = qs.filter(Q(rut_nif__icontains=buscar) | Q(razon_social__icontains=buscar))

        return qs, buscar, per_page

    def get(self, request, *args, **kwargs):
        proveedores = Proveedor.objects.all().order_by('rut_nif', 'razon_social')

        # ===== EXPORTAR EXCEL =====
        if request.GET.get("export") == "xlsx":
            proveedores, _, _ = self._apply_filters(request, proveedores)
            columns = [
                ("RUT/NIF", lambda pr: pr.rut_nif),
                ("Razón social", lambda pr: pr.razon_social),
                ("Nombre fantasía", lambda pr: pr.nombre_fantasia or ""),
                ("Email", lambda pr: pr.email),
                ("Teléfono", lambda pr: pr.telefono or ""),
                ("Ciudad", lambda pr: pr.ciudad or ""),
                ("País", lambda pr: pr.pais),
                ("Condiciones de pago", lambda pr: pr.condiciones_pago),
                ("Moneda", lambda pr: pr.moneda),
                ("Contacto principal", lambda pr: pr.contacto_principal_nombre or ""),
                ("Estado", lambda pr: pr.estado),
            ]
            raw, fname = queryset_to_excel("proveedores", columns, proveedores)
            resp = HttpResponse(
                raw,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="{fname}"'
            return resp

        # ===== FILTROS =====
        proveedores, buscar, per_page = self._apply_filters(request, proveedores)

        # ===== PAGINADOR =====
        try:
            per_page_int = int(per_page)
        except (TypeError, ValueError):
            per_page_int = 10
        if per_page_int not in (5, 10, 2000):
            per_page_int = 10

        paginator = Paginator(proveedores, per_page_int)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': ProveedorForm(),
            'rel_form': ProductoRelacionForm(),
            'productos': Producto.objects.all().order_by("nombre"),
            'pp_formset': ProductoProveedorFormSet(),
            'page_obj': page_obj,
            'proveedores': page_obj,
            'buscar_Rut_Nif': buscar,
            'per_page': per_page_int,
            'titulo': "Registrar proveedor",
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = ProveedorForm(request.POST)
        rel_form = ProductoRelacionForm(request.POST)

        # ---------- VALIDACIÓN DEL FORM PRINCIPAL ----------
        if form.is_valid():
            rut = form.cleaned_data.get('rut_nif')
            email = form.cleaned_data.get('email')

            if Proveedor.objects.filter(rut_nif=rut).exists():
                form.add_error('rut_nif', 'Ya existe un proveedor con este RUT/NIF.')

            if Proveedor.objects.filter(email=email).exists():
                form.add_error('email', 'Ya existe un proveedor con este correo electrónico.')

        # Si hubo errores → recargar
        if form.errors:
            messages.error(request, 'Por favor complete todos los campos obligatorios correctamente.')
            
            # Recargar paginación
            proveedores = Proveedor.objects.all().order_by('razon_social')
            buscar = request.session.get('f_buscar_Rut_Nif', '')
            per_page = int(request.session.get('f_pp_prov', '10'))
            
            if buscar:
                proveedores = proveedores.filter(
                    Q(rut_nif__icontains=buscar) | Q(razon_social__icontains=buscar)
                )
            
            paginator = Paginator(proveedores, per_page)
            page_obj = paginator.get_page(1)
            
            context = {
                'form': form,
                'rel_form': rel_form,
                'productos': Producto.objects.all().order_by("nombre"),
                'pp_formset': ProductoProveedorFormSet(),
                'page_obj': page_obj,
                'proveedores': page_obj,
                'buscar_Rut_Nif': buscar,
                'per_page': per_page,
                'titulo': "Registrar proveedor",
            }
            return render(request, self.template_name, context)

        # VALIDAR TAB 3 CON EL FORM ProductoRelacionForm
        if not rel_form.is_valid():
            messages.error(request, "Corrige los errores del TAB 3.")
            
            # Recargar paginación
            proveedores = Proveedor.objects.all().order_by('razon_social')
            buscar = request.session.get('f_buscar_Rut_Nif', '')
            per_page = int(request.session.get('f_pp_prov', '10'))
            
            if buscar:
                proveedores = proveedores.filter(
                    Q(rut_nif__icontains=buscar) | Q(razon_social__icontains=buscar)
                )
            
            paginator = Paginator(proveedores, per_page)
            page_obj = paginator.get_page(1)
            
            context = {
                'form': form,
                'rel_form': rel_form,
                'productos': Producto.objects.all().order_by("nombre"),
                'pp_formset': ProductoProveedorFormSet(),
                'page_obj': page_obj,
                'proveedores': page_obj,
                'buscar_Rut_Nif': buscar,
                'per_page': per_page,
                'titulo': "Registrar proveedor",
            }
            return render(request, self.template_name, context)

        # GUARDAR PROVEEDOR
        proveedor = form.save()

        # GUARDAR TAB 3 (solo si eligieron producto)
        producto = rel_form.cleaned_data.get("producto_rel")

        if producto:
            ProductoProveedor.objects.create(
                proveedor=proveedor,
                producto=producto,
                costo=rel_form.cleaned_data.get("costo_rel"),
                lead_time_dias=rel_form.cleaned_data.get("lead_time_rel"),
                min_lote=rel_form.cleaned_data.get("min_lote_rel"),
                descuento_pct=rel_form.cleaned_data.get("descuento_rel") or 0,
                preferente=rel_form.cleaned_data.get("preferente_rel") or False,
            )

        messages.success(request, 'Proveedor creado correctamente.')
        return redirect('proveedores:lista')


# ----------------------------------------------------------
# CREAR PROVEEDOR EN RUTA APARTE (Opcional)
# ----------------------------------------------------------
class ProveedorCreateView(CreateView):
    model = Proveedor
    form_class = ProveedorForm
    success_url = reverse_lazy('proveedores:lista')

    def form_valid(self, form):
        rut = form.cleaned_data.get('rut_nif')
        email = form.cleaned_data.get('email')
        if Proveedor.objects.filter(rut_nif=rut).exists():
            form.add_error('rut_nif', 'Ya existe un proveedor con este RUT/NIF.')
            return self.form_invalid(form)
        if Proveedor.objects.filter(email=email).exists():
            form.add_error('email', 'Ya existe un proveedor con este correo electrónico.')
            return self.form_invalid(form)

        self.object = form.save()
        messages.success(self.request, "Proveedor creado correctamente.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        proveedores = Proveedor.objects.all().order_by('razon_social')
        context = {'proveedores': proveedores, 'form': form, 'titulo': 'Registrar proveedor'}
        return render(self.request, 'proveedores/lista_proveedor.html', context)


# ----------------------------------------------------------
# EDITAR PROVEEDOR
# ----------------------------------------------------------
class ProveedorUpdateView(UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedores/form_proveedor.html'
    success_url = reverse_lazy('proveedores:lista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # FORMSET: Carga y edición de productos asociados
        if self.request.POST:
            context["pp_formset"] = ProductoProveedorFormSet(self.request.POST, instance=self.object)
        else:
            context["pp_formset"] = ProductoProveedorFormSet(instance=self.object)

        # Productos para el select
        context["productos"] = Producto.objects.all()

        context['titulo'] = 'Editar'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        pp_formset = context["pp_formset"]

        if pp_formset.is_valid():

            # Guardar el proveedor
            self.object = form.save()

            # Guardar cambios del formset (edición y eliminación)
            pp_formset.instance = self.object
            pp_formset.save()

            # --- AGREGAR NUEVA RELACIÓN ---
            prod_id = self.request.POST.get("producto_rel")

            if prod_id:
                producto = Producto.objects.get(pk=prod_id)

                # Prevenir duplicados
                ya_existe = ProductoProveedor.objects.filter(
                    proveedor=self.object,
                    producto=producto
                ).exists()

                if not ya_existe:
                    ProductoProveedor.objects.create(
                        proveedor=self.object,
                        producto=producto,
                        costo=self.request.POST.get("costo_rel") or 0,
                        lead_time_dias=self.request.POST.get("lead_time_rel") or 7,
                        min_lote=self.request.POST.get("min_lote_rel") or 1,
                        descuento_pct=self.request.POST.get("descuento_rel") or 0,
                        preferente=True if self.request.POST.get("preferente_rel") == "on" else False,
                    )

            # 🔥 SIEMPRE REDIRIGIR DESPUÉS DE GUARDAR
            messages.success(self.request, "Cambios guardados correctamente.")
            return redirect(self.get_success_url())

        # Si el formset tiene errores
        return render(self.request, self.template_name, self.get_context_data(form=form))


# ----------------------------------------------------------
# ELIMINAR PROVEEDOR
# ----------------------------------------------------------
@method_decorator(permiso_requerido('proveedores.change_proveedor'), name='dispatch')
class ProveedorDeleteView(DeleteView):
    model = Proveedor
    success_url = reverse_lazy('proveedores:lista')

    def get(self, request, *args, **kwargs):
        proveedor = get_object_or_404(Proveedor, pk=kwargs['pk'])
        proveedor.delete()
        messages.success(request, f"Proveedor '{proveedor.razon_social}' eliminado correctamente.")
        return redirect(self.success_url)


# ----------------------------------------------------------
# DETALLE DEL PROVEEDOR
# ----------------------------------------------------------
class ProveedorDetailView(DetailView):
    model = Proveedor
    template_name = 'proveedores/detalle_proveedor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos_asociados'] = ProductoProveedor.objects.filter(proveedor=self.object)
        return context