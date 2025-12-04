import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

from .models import Usuario, Cita, Especialidad, Notificacion

logger = logging.getLogger(__name__)


# CONTROLADOR: Login
@never_cache
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        # Redirigir según el rol
        if request.user.rol == 'ADMIN':
            return redirect('admin_dashboard')
        elif request.user.rol == 'MEDICO':
            return redirect('medico_dashboard')
        else:
            return redirect('paciente_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.first_name or user.username}')

            # Redirigir según el rol
            if user.rol == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.rol == 'MEDICO':
                return redirect('medico_dashboard')
            else:
                return redirect('paciente_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return render(request, 'layout/login.html')

    return render(request, 'layout/login.html')


# CONTROLADOR: Logout
@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'Has cerrado sesión, {username}')
    return redirect('login')


# CONTROLADOR: Registro
@never_cache
@csrf_protect
def registro_view(request):
    # Si el usuario ya está autenticado, redirigir
    if request.user.is_authenticated:
        return redirect('paciente_dashboard')

    # Valores que se devolverán a la plantilla en caso de error
    form_data = {
        'username': '',
        'first_name': '',
        'email': '',
        'rol': 'PACIENTE',
    }

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        rol = request.POST.get('rol', 'PACIENTE')

        # Guardar los valores recibidos para devolverlos si hay error
        form_data.update({
            'username': username,
            'first_name': first_name,
            'email': email,
            'rol': rol,
        })

        # Log para depuración (NO incluir contraseñas en logs en producción)
        logger.debug("POST /registro/ data: %s", {k: v for k, v in request.POST.items() if k not in ['password', 'password_confirm']})

        # Validaciones
        if not all([username, first_name, email, password, password_confirm]):
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/registro.html', {'form': form_data})

        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'layout/registro.html', {'form': form_data})

        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'layout/registro.html', {'form': form_data})

        # Verificar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'layout/registro.html', {'form': form_data})

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'layout/registro.html', {'form': form_data})

        try:
            # Crear usuario (asumiendo que Usuario.objects.create_user maneja hashing)
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol,
                first_name=first_name
            )
            messages.success(request, 'Usuario registrado exitosamente. ¡Ahora puedes iniciar sesión!')
            return redirect('login')
        except Exception as e:
            logger.exception("Error al crear usuario")
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            return render(request, 'layout/registro.html', {'form': form_data})

    # GET request
    return render(request, 'layout/registro.html', {'form': form_data})


# CONTROLADOR: Dashboard Admin
@login_required
def admin_dashboard(request):
    if getattr(request.user, 'rol', None) != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')

    context = {
        'total_usuarios': Usuario.objects.count(),
        'total_citas': Cita.objects.count(),
        'citas_pendientes': Cita.objects.filter(estado='PENDIENTE').count(),
    }
    # plantilla: templates/admin/index.html
    return render(request, 'admin/index.html', context)


# CONTROLADOR: Dashboard Médico
@login_required
def medico_dashboard(request):
    if getattr(request.user, 'rol', None) != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')

    # Obtener citas de hoy usando fecha_hora
    hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = hoy_inicio + timezone.timedelta(days=1)

    citas_hoy = Cita.objects.filter(
        medico=request.user,
        fecha_hora__gte=hoy_inicio,
        fecha_hora__lt=hoy_fin
    )

    context = {
        'citas_hoy': citas_hoy,
        'total_citas': Cita.objects.filter(medico=request.user).count(),
    }
    # plantilla: templates/medico/index.html
    return render(request, 'medico/index.html', context)


# CONTROLADOR: Dashboard Paciente
@login_required
def paciente_dashboard(request):
    if getattr(request.user, 'rol', None) != 'PACIENTE':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')

    mis_citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora')

    context = {
        'mis_citas': mis_citas,
    }
    # plantilla: templates/paciente/index.html
    return render(request, 'paciente/index.html', context)


# CONTROLADOR: Listar Citas
@login_required
def listar_citas(request):
    if request.user.rol == 'ADMIN':
        citas = Cita.objects.all()
    elif request.user.rol == 'MEDICO':
        citas = Cita.objects.filter(medico=request.user)
    else:
        citas = Cita.objects.filter(paciente=request.user)

    context = {
        'citas': citas.order_by('-fecha_hora')
    }
    # plantilla: templates/admin/CRUD_Citas/listar.html (según tu árbol de templates)
    return render(request, 'admin/CRUD_Citas/listar.html', context)


# CONTROLADOR: Crear Cita
@login_required
def crear_cita(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, 'Solo los pacientes pueden crear citas')
        return redirect('listar_citas')

    if request.method == 'POST':
        medico_id = request.POST.get('medico')
        especialidad_id = request.POST.get('especialidad')
        fecha_hora = request.POST.get('fecha_hora')
        motivo = request.POST.get('motivo', '').strip()

        if not all([medico_id, fecha_hora]):
            messages.error(request, 'Por favor completa todos los campos obligatorios')
            return redirect('crear_cita')

        try:
            medico = Usuario.objects.get(id=medico_id, rol='MEDICO')

            # Obtener especialidad si se proporciona
            especialidad = None
            if especialidad_id:
                try:
                    especialidad = Especialidad.objects.get(id=especialidad_id)
                except Especialidad.DoesNotExist:
                    especialidad = None

            cita = Cita.objects.create(
                paciente=request.user,
                medico=medico,
                especialidad=especialidad,
                fecha_hora=fecha_hora,
                motivo=motivo,
                estado='PENDIENTE'
            )

            messages.success(request, 'Cita creada exitosamente')
            return redirect('listar_citas')
        except Usuario.DoesNotExist:
            messages.error(request, 'Médico no encontrado')
            return redirect('crear_cita')
        except Exception as e:
            logger.exception("Error al crear cita")
            messages.error(request, f'Error al crear cita: {str(e)}')
            return redirect('crear_cita')

    # GET request
    medicos = Usuario.objects.filter(rol='MEDICO')
    especialidades = Especialidad.objects.all()

    context = {
        'medicos': medicos,
        'especialidades': especialidades,
    }
    # plantilla: templates/admin/CRUD_Citas/crear.html
    return render(request, 'admin/CRUD_Citas/crear.html', context)