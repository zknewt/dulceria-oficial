import random
import string
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .forms import UsuarioForm, PerfilForm
from .models import Usuario
from utils.export_excel import queryset_to_excel
from django.contrib.auth import update_session_auth_hash

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required

# --- 💌 Recuperación de contraseña simplificada con SweetAlert ---
from .models import Usuario
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# 🧑‍💻 PERFIL DEL USUARIO
@login_required
def perfil(request):
    return render(request, 'usuarios/perfil.html', {'user': request.user})


@login_required
def perfil_editar(request):
    """Permite al usuario editar su propio perfil."""
    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("usuarios:perfil")
        messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = PerfilForm(instance=request.user, user=request.user)

    return render(request, "usuarios/perfil_editar.html", {"form": form})


# 👥 LISTADO Y EXPORTACIÓN DE USUARIOS
@login_required
def usuario_list(request):
    """
    Lista con filtros (q, rol, estado) y formulario embebido para crear.
    Los filtros se guardan en sesión para mantenerlos al recargar.
    """
    qs = Usuario.objects.all().order_by('username')

    # --- Obtener filtros desde GET o sesión ---
    q = request.GET.get('q')
    rol = request.GET.get('rol')
    estado = request.GET.get('estado')

    # Si el usuario entra sin parámetros, usar los valores guardados en sesión
    if q is None and rol is None and estado is None:
        q = request.session.get('f_q', '')
        rol = request.session.get('f_rol', '')
        estado = request.session.get('f_estado', '')
    else:
        # Actualizar la sesión con los nuevos valores
        request.session['f_q'] = q or ''
        request.session['f_rol'] = rol or ''
        request.session['f_estado'] = estado or ''

    # --- Aplicar filtros ---
    if q:
        qs = qs.filter(username__icontains=q)
    if rol:
        qs = qs.filter(rol=rol)
    if estado:
        qs = qs.filter(estado=estado)

    # 📤 Exportar a Excel
    if request.GET.get("export") == "xlsx":
        columns = [
            ("Username", lambda u: u.username),
            ("Email", lambda u: u.email),
            ("Nombre", lambda u: f"{u.nombres or ''} {u.apellidos or ''}".strip()),
            ("Teléfono", lambda u: u.telefono or ""),
            ("Rol", lambda u: u.rol),
            ("Estado", lambda u: u.estado),
            ("Área", lambda u: u.area or ""),
            ("MFA habilitado", lambda u: "Sí" if u.mfa_habilitado else "No"),
            ("Último acceso", lambda u: u.last_login.replace(tzinfo=None) if u.last_login else ""),
            ("Sesiones", lambda u: u.sesiones),
        ]
        raw, fname = queryset_to_excel("usuarios", columns, qs)
        resp = HttpResponse(
            raw,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{fname}"'
        return resp

    # --- Contexto ---
    form = UsuarioForm()
    ctx = {
        'usuarios': qs,
        'form': form,
        'f_q': q or '',
        'f_rol': rol or '',
        'f_estado': estado or '',
    }
    return render(request, 'usuarios/Lista_usuario.html', ctx)

def generar_clave_temporal():
    caracteres = string.ascii_letters + string.digits + "!@#$%&*"

    clave = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%&*"),
    ]

    clave += [random.choice(caracteres) for _ in range(6)]
    random.shuffle(clave)

    return ''.join(clave)

from .forms import CambioClaveObligatorioForm

@login_required
def cambiar_clave_obligatorio(request):
    if request.method == "POST":
        form = CambioClaveObligatorioForm(user=request.user, data=request.POST)

        if form.is_valid():
            user = form.save()
            user.debe_cambiar_clave = False
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Clave cambiada con éxito. Bienvenido/a!")
            return redirect("dashboard")
        else:
            # si hay errores, se vuelven a mostrar en pantalla
            return render(request, "usuarios/cambiar_clave_obligatorio.html", {"form": form})

    else:
        form = CambioClaveObligatorioForm(user=request.user)

    return render(request, "usuarios/cambiar_clave_obligatorio.html", {"form": form})


@login_required
@permission_required('auth.change_user', raise_exception=True)
def resetear_clave(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    nueva_clave = generar_clave_temporal()
    usuario.set_password(nueva_clave)
    usuario.debe_cambiar_clave = True
    usuario.save()

    send_mail(
        "Clave reseteada - Dulcería Lili",
        f"Tu clave ha sido reseteada.\n\nNueva clave temporal: {nueva_clave}\n\nIngresa y cámbiala inmediatamente.",
        settings.EMAIL_HOST_USER,
        [usuario.email]
    )

    messages.success(request, f"Clave de {usuario.username} reseteada y enviada.")
    return redirect('usuarios:lista')


@login_required
@permission_required('usuarios.add_usuario', raise_exception=False)
@require_POST
def usuario_create(request):
    form = UsuarioForm(request.POST)

    if form.is_valid():
        usuario = form.save(commit=False)

        # Generar clave temporal robusta
        clave_temporal = generar_clave_temporal()
        usuario.set_password(clave_temporal)
        usuario.debe_cambiar_clave = True
        usuario.save()

        # Enviar correo de bienvenida
        subject = "Dulcería Lili - Bienvenido/a"
        login_url = request.build_absolute_uri(reverse('usuarios:login'))
        message = f"""
        Hola {usuario.nombres},

        Tu cuenta ha sido creada exitosamente.

        Usuario: {usuario.username}
        Clave temporal: {clave_temporal}

        Debes cambiar tu clave en el primer inicio de sesión.
        Ingresa aquí: {login_url}

        Saludos,
        Equipo Dulcería Lili
        """
        send_mail(subject, message, settings.EMAIL_HOST_USER, [usuario.email], fail_silently=False)

        messages.success(request, f'Usuario creado. Clave temporal enviada a {usuario.email}')
        return redirect('usuarios:lista')

    # Si el formulario NO es válido, mostramos los errores en la misma página
    qs = Usuario.objects.all().order_by('username')
    ctx = {
        'usuarios': qs,
        'form': form,  # <-- aquí mantenemos el form con los errores
        'f_q': request.GET.get('q', ''),
        'f_rol': request.GET.get('rol', ''),
        'f_estado': request.GET.get('estado', ''),
    }
    messages.error(request, 'Revisa los errores del formulario.')
    return render(request, 'usuarios/Lista_usuario.html', ctx)




# ✏️ EDITAR USUARIO
@login_required
@permission_required('usuarios.change_usuario', raise_exception=False)
def usuario_update(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                usuario.set_password(password)
            usuario.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('usuarios:lista')
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'usuarios/form_usuario.html', {
        'form': form,
        'obj': usuario,
        'modo': 'Editar'
    })


# 🗑️ ELIMINAR USUARIO
@login_required
@permission_required('usuarios.delete_usuario', raise_exception=False)
@require_POST
def usuario_delete(request, pk):
    u = get_object_or_404(Usuario, pk=pk)
    u.delete()
    messages.success(request, 'Usuario eliminado.')
    return redirect('usuarios:lista')


# 🔑 Recuperación de contraseña personalizada

# 💌 Paso 1: Solicitar correo
def password_reset_custom(request):
    """
    Muestra el formulario para ingresar el correo o usuario y envía el enlace.
    """
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = Usuario.objects.filter(email=email).first()
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = f"{'https' if request.is_secure() else 'http'}://{request.get_host()}/usuarios/reset/{uid}/{token}/"

                subject = "Restablecer contraseña - Dulcería Lili"
                message = f"Hola {user.username},\n\nHaz clic en el siguiente enlace para crear una nueva contraseña:\n\n{reset_link}\n\nSi no solicitaste esto, puedes ignorar este mensaje."
                send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

            # ⚡️ Redirige con parámetro de éxito (aunque el correo no exista)
            return redirect('/usuarios/password_reset/?sent=true')
    else:
        form = PasswordResetForm()

    return render(request, 'usuarios/password_reset.html', {'form': form})


# 🔐 Paso 2: Cambiar contraseña
def password_reset_confirm_custom(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                # ✅ redirigir a una página nueva, no volver al token
                return redirect("/usuarios/password_reset_done/?success=true")
            else:
                return render(request, 'usuarios/password_reset_confirm.html', {
                    'form': form,
                    'error': form.errors
                })
        else:
            form = SetPasswordForm(user)
        return render(request, 'usuarios/password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'usuarios/password_reset_confirm.html', {
            'error': 'El enlace no es válido o ha expirado.'
        })


def password_reset_done_custom(request):
    return render(request, 'usuarios/password_reset_done.html')

@login_required
def logout_view(request):
    """
    Cierra sesión y evita volver a páginas internas con el botón "Atrás" del navegador.
    """
    django_logout(request)
    
    response = redirect('usuarios:login')
    
    # Headers anti-caché (impiden que el navegador guarde páginas autenticadas)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response
