from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone  
from .models import Usuario, Cita, Especialidad, Notificacion

# CONTROLADOR: Login
@never_cache
@csrf_protect
def login_view(request):
    # Si el usuario ya está autenticado, redirigir a su dashboard
    if request.user.is_authenticated:
        if request.user.rol == 'ADMIN':
            return redirect('admin_dashboard')
        elif request.user.rol == 'MEDICO':
            return redirect('medico_dashboard')
        else:
            return redirect('paciente_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validación básica
        if not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            
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

# CONTROLADOR: Registro
@never_cache
@csrf_protect
def registro_view(request):
    # Si el usuario ya está autenticado, redirigir
    if request.user.is_authenticated:
        return redirect('paciente_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        rol = request.POST.get('rol', 'PACIENTE')
        
        # Validaciones
        if not all([username, email, password, password_confirm]):
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/registro.html')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'layout/registro.html')
        
        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'layout/registro.html')
        
        # Verificar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'layout/registro.html')
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'layout/registro.html')
        
        try:
            # Crear usuario
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol
            )
            messages.success(request, 'Usuario registrado exitosamente. ¡Ahora puedes iniciar sesión!')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            return render(request, 'layout/registro.html')
    
    return render(request, 'layout/registro.html')

# CONTROLADOR: Dashboard Admin
@login_required
def admin_dashboard(request):
    if request.user.rol != 'ADMIN':
        messages.warning(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')
    
    # Obtener datos para el dashboard
    total_usuarios = Usuario.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='PENDIENTE').count()
    citas_confirmadas = Cita.objects.filter(estado='CONFIRMADA').count()
    total_medicos = Usuario.objects.filter(rol='MEDICO').count()
    total_pacientes = Usuario.objects.filter(rol='PACIENTE').count()
    
    # Últimas citas
    ultimas_citas = Cita.objects.all().order_by('-fecha_hora')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_confirmadas': citas_confirmadas,
        'total_medicos': total_medicos,
        'total_pacientes': total_pacientes,
        'ultimas_citas': ultimas_citas,
    }
    return render(request, 'admin/index.html', context)

# CONTROLADOR: Dashboard Médico
@login_required
def medico_dashboard(request):
    if request.user.rol != 'MEDICO':
        messages.warning(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')
    
    # Citas del médico
    mis_citas = Cita.objects.filter(medico=request.user).order_by('-fecha_hora')
    citas_hoy = mis_citas.filter(fecha_hora__date=timezone.now().date())
    citas_pendientes = mis_citas.filter(estado='PENDIENTE').count()
    
    context = {
        'mis_citas': mis_citas[:10],  # Últimas 10 citas
        'citas_hoy': citas_hoy,
        'citas_pendientes': citas_pendientes,
        'total_citas': mis_citas.count(),
    }
    return render(request, 'medico/index.html', context)

# CONTROLADOR: Dashboard Paciente
@login_required
def paciente_dashboard(request):
    if request.user.rol != 'PACIENTE':
        messages.warning(request, 'No tienes permisos para acceder a esta página')
        return redirect('login')
    
    # Citas del paciente
    mis_citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora')
    proximas_citas = mis_citas.filter(fecha_hora__gte=timezone.now(), estado='CONFIRMADA')
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False)
    
    context = {
        'mis_citas': mis_citas[:5],  # Últimas 5 citas
        'proximas_citas': proximas_citas,
        'notificaciones': notificaciones,
        'total_citas': mis_citas.count(),
    }
    return render(request, 'paciente/index.html', context)

# CONTROLADOR: Logout
@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'Hasta luego {username}. Has cerrado sesión exitosamente')
    return redirect('login')

# CONTROLADOR: Listar Citas (Admin/Médico)
@login_required
def listar_citas(request):
    if request.user.rol == 'ADMIN':
        citas = Cita.objects.all().select_related('paciente', 'medico', 'especialidad')
    elif request.user.rol == 'MEDICO':
        citas = Cita.objects.filter(medico=request.user).select_related('paciente', 'especialidad')
    else:
        citas = Cita.objects.filter(paciente=request.user).select_related('medico', 'especialidad')
    
    # Ordenar por fecha
    citas = citas.order_by('-fecha_hora')
    
    return render(request, 'admin/CRUD_Citas/listar.html', {'citas': citas})

# CONTROLADOR: Crear Cita
@login_required
@csrf_protect
def crear_cita(request):
    if request.method == 'POST':
        try:
            paciente_id = request.POST.get('paciente_id')
            medico_id = request.POST.get('medico_id')
            especialidad_id = request.POST.get('especialidad_id')
            fecha_hora = request.POST.get('fecha_hora')
            motivo = request.POST.get('motivo', '').strip()
            
            # Validaciones
            if not all([paciente_id, medico_id, especialidad_id, fecha_hora]):
                messages.error(request, 'Por favor completa todos los campos obligatorios')
                return redirect('crear_cita')
            
            # Crear la cita
            cita = Cita.objects.create(
                paciente_id=paciente_id,
                medico_id=medico_id,
                especialidad_id=especialidad_id,
                fecha_hora=fecha_hora,
                motivo=motivo,
                estado='PENDIENTE'
            )
            
            messages.success(request, 'Cita creada exitosamente')
            return redirect('listar_citas')
            
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {str(e)}')
            return redirect('crear_cita')
    
    # GET request
    medicos = Usuario.objects.filter(rol='MEDICO')
    pacientes = Usuario.objects.filter(rol='PACIENTE')
    especialidades = Especialidad.objects.all()
    
    context = {
        'medicos': medicos,
        'pacientes': pacientes,
        'especialidades': especialidades,
    }
    return render(request, 'admin/CRUD_Citas/crear.html', context)