import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from django.core.paginator import Paginator
import json


from .models import Usuario, Cita, Especialidad, Notificacion

logger = logging.getLogger(__name__)


def index_view(request):
    return render(request, 'index.html')


# ============================================================
#                      AUTENTICACIÓN
# ============================================================

@never_cache
@csrf_protect
def login_view(request):
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

        if not username or not password:
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.first_name or user.username}')

            if user.rol == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.rol == 'MEDICO':
                return redirect('medico_dashboard')
            else:
                return redirect('paciente_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'layout/login.html')


@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'Has cerrado sesión, {username}')
    return redirect('login')


@never_cache
@csrf_protect
def registro_view(request):
    if request.user.is_authenticated:
        return redirect('paciente_dashboard')

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

        form_data.update({
            'username': username,
            'first_name': first_name,
            'email': email,
            'rol': rol,
        })

        if not all([username, first_name, email, password, password_confirm]):
            messages.error(request, 'Por favor completa todos los campos')
            return render(request, 'layout/registro.html', {'form': form_data})

        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'layout/registro.html', {'form': form_data})

        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'layout/registro.html', {'form': form_data})

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'layout/registro.html', {'form': form_data})

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'layout/registro.html', {'form': form_data})

        try:
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol,
                first_name=first_name
            )
            messages.success(request, 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            logger.exception("Error al crear usuario")
            messages.error(request, f'Error al registrar usuario: {str(e)}')

    return render(request, 'layout/registro.html', {'form': form_data})


# ============================================================
#                      DASHBOARDS
# ============================================================

@login_required
def admin_dashboard(request):
    if request.user.rol != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    context = {
        'total_usuarios': Usuario.objects.count(),
        'total_citas': Cita.objects.count(),
        'citas_pendientes': Cita.objects.filter(estado='PENDIENTE').count(),
    }
    return render(request, 'admin/index.html', context)



@login_required
def medico_dashboard(request):
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Fecha de hoy
    hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = hoy_inicio + timezone.timedelta(days=1)

    # Citas de hoy
    citas_hoy = Cita.objects.filter(
        medico=request.user,
        fecha_hora__gte=hoy_inicio,
        fecha_hora__lt=hoy_fin
    ).order_by('fecha_hora')

    # Próximas citas (después de hoy, máximo 3)
    ahora = timezone.now()
    proximas_citas = Cita.objects.filter(
        medico=request.user,
        fecha_hora__gt=hoy_fin,
        estado='PENDIENTE'
    ).order_by('fecha_hora')[:3]

    # Estadísticas
    total_citas = Cita.objects.filter(medico=request.user).count()
    citas_pendientes = Cita.objects.filter(medico=request.user, estado='PENDIENTE').count()
    
    # Total de pacientes únicos atendidos (solo citas COMPLETADAS o ATENDIDAS)
    total_pacientes = Cita.objects.filter(
        medico=request.user,
        estado__in=['COMPLETADA', 'ATENDIDA']  # Múltiples estados
    ).values('paciente').distinct().count()

    context = {
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'total_pacientes': total_pacientes,
        'today': timezone.now(),
    }
    
    return render(request, 'medico/index.html', context)

@login_required
def paciente_dashboard(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    mis_citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora')
    
    notificaciones = (
    Notificacion.objects
    .filter(usuario=request.user)
    .order_by('-creada_en')  # <-- corregido: creada_en (no 'creado_en')
    )   


    # Obtener próximas citas
    ahora = timezone.now()
    proximas_citas = Cita.objects.filter(
        paciente=request.user,
        fecha_hora__gte=ahora,
        estado='PENDIENTE'
    ).order_by('fecha_hora')
    
    # Datos para el modal de crear cita
    medicos = Usuario.objects.filter(rol='MEDICO')
    especialidades = Especialidad.objects.all()
    
    context = {
        'mis_citas': mis_citas,
        'total_citas': mis_citas.count(),
        'notificaciones': notificaciones,
        'proximas_citas': proximas_citas,
        'medicos': medicos,
        'especialidades': especialidades,
    }

    return render(request, 'paciente/index.html', context)


# ============================================================
#                     CRUD DE CITAS
# ============================================================

@login_required
def listar_citas(request):
    if request.user.rol == 'ADMIN':
        citas = Cita.objects.all()
    elif request.user.rol == 'MEDICO':
        citas = Cita.objects.filter(medico=request.user)
    else:
        citas = Cita.objects.filter(paciente=request.user)

    context = {'citas': citas.order_by('-fecha_hora')}
    return render(request, 'admin/CRUD_Citas/listar.html', context)


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
            messages.error(request, 'Por favor completa los campos obligatorios')
            return redirect('paciente_dashboard')

        try:
            medico = Usuario.objects.get(id=medico_id, rol='MEDICO')

            especialidad = None
            if especialidad_id:
                especialidad = Especialidad.objects.filter(id=especialidad_id).first()

            Cita.objects.create(
                paciente=request.user,
                medico=medico,
                especialidad=especialidad,
                fecha_hora=fecha_hora,
                motivo=motivo,
                estado='PENDIENTE'
            )

            messages.success(request, 'Cita creada exitosamente')
            return redirect('paciente_dashboard')

        except Usuario.DoesNotExist:
            messages.error(request, 'Médico no encontrado')
            return redirect('paciente_dashboard')
        except Exception as e:
            logger.exception("Error al crear cita")
            messages.error(request, f'Error al crear cita: {str(e)}')
            return redirect('paciente_dashboard')

    # Si es GET, redirigir al dashboard
    return redirect('paciente_dashboard')


# ============================================================
#                 SECCIONES DEL PACIENTE
# ============================================================

@login_required
def paciente_citas(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Todas las citas del paciente
    citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora')
    
    # Obtener próximas citas (futuras y pendientes)
    ahora = timezone.now()
    proximas_citas = Cita.objects.filter(
        paciente=request.user,
        fecha_hora__gte=ahora,
        estado='PENDIENTE'
    ).order_by('fecha_hora')
    
    # Citas pasadas
    citas_pasadas = Cita.objects.filter(
        paciente=request.user,
        fecha_hora__lt=ahora
    ).order_by('-fecha_hora')

    return render(
        request,
        'paciente/pages/mis_citas.html',
        {
            'citas': citas,
            'proximas_citas': proximas_citas,
            'citas_pasadas': citas_pasadas,
        }
    )

@login_required
def historial_medico(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    historial = Cita.objects.filter(
        paciente=request.user,
        estado='ATENDIDA'
    ).order_by('-fecha_hora')

    return render(
        request,
        'paciente/pages/historial_medico.html',
        {'historial': historial}
    )


@login_required
def perfil_paciente(request):
    if request.user.rol != 'PACIENTE':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '')

        # Validaciones
        if not all([first_name, email]):
            messages.error(request, 'El nombre y el email son obligatorios')
            return render(request, 'paciente/pages/perfil.html', {'usuario': request.user})

        # Verificar si el email ya existe (excepto el del usuario actual)
        if Usuario.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, 'El email ya está en uso por otro usuario')
            return render(request, 'paciente/pages/perfil.html', {'usuario': request.user})

        try:
            # Actualizar datos del usuario
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.telefono = telefono
            request.user.direccion = direccion
            
            if fecha_nacimiento:
                request.user.fecha_nacimiento = fecha_nacimiento
            
            request.user.save()
            
            messages.success(request, '¡Perfil actualizado exitosamente!')
            return redirect('perfil_paciente')
            
        except Exception as e:
            logger.exception("Error al actualizar perfil")
            messages.error(request, f'Error al actualizar perfil: {str(e)}')

    return render(
        request,
        'paciente/pages/perfil.html',
        {'usuario': request.user}
    )


# ============================================================
#                 SECCIONES DEL MÉDICO
# ============================================================

@login_required
def medico_mis_citas(request):
    """Vista principal de citas del médico con paginación y filtros"""
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Obtener todas las citas del médico
    citas = Cita.objects.filter(medico=request.user).select_related('paciente', 'especialidad').order_by('-fecha_hora')
    
    # Filtro por estado (opcional)
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        citas = citas.filter(estado=estado_filtro)
    
    # Paginación (10 citas por página)
    paginator = Paginator(citas, 10)
    page_number = request.GET.get('page', 1)
    mis_citas = paginator.get_page(page_number)

    context = {
        'mis_citas': mis_citas,
        'total_citas': citas.count(),
        'estado_filtro': estado_filtro,
    }
    return render(request, 'medico/pages/mis_citas.html', context)


@login_required
def medico_cita_detail(request, pk):
    """Vista de detalle de una cita específica"""
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')
    
    cita = get_object_or_404(Cita, pk=pk, medico=request.user)
    
    context = {
        'cita': cita,
    }
    return render(request, 'medico/pages/cita_detail.html', context)


@login_required
@require_POST
def medico_confirmar_cita(request, pk):
    """Confirmar una cita (PENDIENTE -> CONFIRMADA)"""
    if request.user.rol != 'MEDICO':
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        cita = get_object_or_404(Cita, pk=pk, medico=request.user)
        
        if cita.estado != 'PENDIENTE':
            return JsonResponse({
                'success': False, 
                'error': 'Solo se pueden confirmar citas pendientes'
            }, status=400)
        
        cita.estado = 'CONFIRMADA'
        cita.save()
        
        logger.info(f"Cita {pk} confirmada por médico {request.user.username}")
        return JsonResponse({'success': True, 'message': 'Cita confirmada exitosamente'})
        
    except Exception as e:
        logger.exception(f"Error al confirmar cita {pk}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@login_required
@require_POST
def medico_cancelar_cita(request, pk):
    """Cancelar una cita"""
    if request.user.rol != 'MEDICO':
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        cita = get_object_or_404(Cita, pk=pk, medico=request.user)
        
        if cita.estado == 'COMPLETADA':
            return JsonResponse({
                'success': False, 
                'error': 'No se puede cancelar una cita completada'
            }, status=400)
        
        cita.estado = 'CANCELADA'
        cita.save()
        
        logger.info(f"Cita {pk} cancelada por médico {request.user.username}")
        return JsonResponse({'success': True, 'message': 'Cita cancelada exitosamente'})
        
    except Exception as e:
        logger.exception(f"Error al cancelar cita {pk}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def medico_completar_cita(request, pk):
    """Marcar una cita como completada/atendida"""
    if request.user.rol != 'MEDICO':
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        cita = get_object_or_404(Cita, pk=pk, medico=request.user)
        
        if cita.estado == 'CANCELADA':
            return JsonResponse({
                'success': False, 
                'error': 'No se puede completar una cita cancelada'
            }, status=400)
        
        cita.estado = 'COMPLETADA'
        cita.save()
        
        logger.info(f"Cita {pk} completada por médico {request.user.username}")
        return JsonResponse({'success': True, 'message': 'Cita marcada como completada'})
        
    except Exception as e:
        logger.exception(f"Error al completar cita {pk}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def medico_cambiar_estado_cita(request, pk):
    """Cambiar estado de una cita a cualquier estado válido"""
    if request.user.rol != 'MEDICO':
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        cita = get_object_or_404(Cita, pk=pk, medico=request.user)
        nuevo_estado = request.POST.get('estado', '').strip().upper()
        
        # Validar que el estado sea válido
        estados_validos = ['PENDIENTE', 'CONFIRMADA', 'CANCELADA', 'COMPLETADA', 'ATENDIDA']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False, 
                'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'
            }, status=400)
        
        estado_anterior = cita.estado
        cita.estado = nuevo_estado
        cita.save()
        
        logger.info(f"Cita {pk} cambió de {estado_anterior} a {nuevo_estado} por {request.user.username}")
        return JsonResponse({
            'success': True, 
            'message': f'Estado cambiado a {nuevo_estado}',
            'nuevo_estado': nuevo_estado
        })
        
    except Exception as e:
        logger.exception(f"Error al cambiar estado de cita {pk}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def medico_mis_pacientes(request):
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Obtener pacientes únicos del médico
    pacientes_ids = Cita.objects.filter(
        medico=request.user
    ).values_list('paciente', flat=True).distinct()
    
    pacientes = Usuario.objects.filter(id__in=pacientes_ids)

    context = {
        'pacientes': pacientes,
        'total_pacientes': pacientes.count(),
    }
    return render(request, 'medico/pages/mis_pacientes.html', context)


@login_required
def medico_horario(request):
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Obtener citas de la semana
    hoy = timezone.now().date()
    inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timezone.timedelta(days=7)
    
    citas_semana = Cita.objects.filter(
        medico=request.user,
        fecha_hora__date__gte=inicio_semana,
        fecha_hora__date__lt=fin_semana
    ).order_by('fecha_hora')

    context = {
        'citas_semana': citas_semana,
    }
    return render(request, 'medico/pages/mi_horario.html', context)


@login_required
def medico_estadisticas(request):
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    # Estadísticas generales
    total_citas = Cita.objects.filter(medico=request.user).count()
    citas_completadas = Cita.objects.filter(medico=request.user, estado='COMPLETADA').count()
    citas_pendientes = Cita.objects.filter(medico=request.user, estado='PENDIENTE').count()
    citas_canceladas = Cita.objects.filter(medico=request.user, estado='CANCELADA').count()
    
    total_pacientes = Cita.objects.filter(
        medico=request.user
    ).values('paciente').distinct().count()

    context = {
        'total_citas': total_citas,
        'citas_completadas': citas_completadas,
        'citas_pendientes': citas_pendientes,
        'citas_canceladas': citas_canceladas,
        'total_pacientes': total_pacientes,
    }
    return render(request, 'medico/pages/estadisticas.html', context)


@login_required
def medico_perfil(request):
    if request.user.rol != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if not all([first_name, email]):
            messages.error(request, 'El nombre y el email son obligatorios')
            return render(request, 'medico/pages/perfil.html', {'usuario': request.user})

        if Usuario.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, 'El email ya está en uso')
            return render(request, 'medico/pages/perfil.html', {'usuario': request.user})

        try:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.telefono = telefono
            request.user.direccion = direccion
            request.user.save()
            
            messages.success(request, '¡Perfil actualizado exitosamente!')
            return redirect('medico_perfil')
        except Exception as e:
            logger.exception("Error al actualizar perfil")
            messages.error(request, f'Error al actualizar perfil: {str(e)}')

    return render(request, 'medico/pages/perfil.html', {'usuario': request.user})



@login_required
def medico_agregar_franja(request):
    """
    Maneja el POST desde el modal de 'Agregar Franja'.
    Por ahora guarda los datos de forma mínima: valida y muestra un mensaje.
    Si tienes un modelo Franja u otro storage, reemplaza la parte de creación.
    """
    if request.method != 'POST':
        # Redirigir al horario si acceden por GET
        return redirect('medico_horario')

    # Solo médicos pueden acceder (según tu lógica)
    if getattr(request.user, 'rol', None) != 'MEDICO':
        messages.error(request, 'No tienes permisos para crear franjas')
        return redirect('medico_horario')

    dia = request.POST.get('dia')
    hora_inicio = request.POST.get('hora_inicio')
    hora_fin = request.POST.get('hora_fin')
    tipo = request.POST.get('tipo')

    # Validaciones básicas
    if not all([dia, hora_inicio, hora_fin]):
        messages.error(request, 'Completa los campos obligatorios para la franja')
        return redirect('medico_horario')

    # Aquí normalmente crearías la franja en la BD:
    # Franja.objects.create(medico=request.user, dia=..., hora_inicio=..., hora_fin=..., tipo=...)
    # Como ejemplo temporal simplemente mostramos mensaje de éxito:
    messages.success(request, f'Franja agregada: {dia} {hora_inicio} - {hora_fin} ({tipo})')

    return redirect('medico_horario')


@login_required
def medico_paciente_detail(request, pk):
    """
    Vista mínima de detalle de paciente.
    Reemplaza o extiende según necesites mostrar ficha clínica.
    """
    if getattr(request.user, 'rol', None) != 'MEDICO':
        messages.error(request, 'No tienes permiso para ver esta página')
        return redirect('medico_dashboard')

    paciente = get_object_or_404(Usuario, pk=pk, rol='PACIENTE')
    # Por ahora renderiza una plantilla simple; crea medico/pages/paciente_detail.html si no existe.
    context = {
        'paciente': paciente,
    }
    return render(request, 'medico/pages/paciente_detail.html', context)


@login_required
def medico_agendar(request, pk):
    """
    Vista mínima para crear/mostrar el formulario de agendar cita para un paciente.
    Si recibes POST, procesa la creación (o redirige al modal).
    """
    if getattr(request.user, 'rol', None) != 'MEDICO':
        messages.error(request, 'No tienes permiso para agendar citas')
        return redirect('medico_dashboard')

    paciente = get_object_or_404(Usuario, pk=pk, rol='PACIENTE')

    if request.method == 'POST':
        # Aquí procesarías el formulario de creación de cita
        # Por simplicidad devolvemos mensaje y redirigimos
        messages.success(request, f'Cita creada (simulada) para {paciente.get_full_name() or paciente.username}')
        return redirect('medico_mis_citas')

    # GET -> mostrar un formulario o redirigir al listado
    context = {'paciente': paciente}
    return render(request, 'medico/pages/agendar_para_paciente.html', context)

@login_required
def medico_horario(request):
    if getattr(request.user, 'rol', None) != 'MEDICO':
        messages.error(request, 'No tienes permisos para acceder')
        return redirect('login')

    ahora = timezone.now()
    # cargar citas del próximo mes (ajusta rango si quieres)
    hasta = ahora + timedelta(days=30)

    citas = Cita.objects.filter(
        medico=request.user,
        fecha_hora__gte=ahora,
        fecha_hora__lte=hasta
    ).order_by('fecha_hora')

    # Construir lista de eventos para FullCalendar
    calendar_events = []
    DEFAULT_DURATION_MIN = 30
    for c in citas:
        start_iso = c.fecha_hora.isoformat()
        # si no tienes duración, asumimos 30 minutos
        end_dt = c.fecha_hora + timedelta(minutes=DEFAULT_DURATION_MIN)
        end_iso = end_dt.isoformat()
        calendar_events.append({
            "id": c.id,
            "title": f"Cita - {c.paciente.get_full_name() or c.paciente.username}",
            "start": start_iso,
            "end": end_iso,
            "estado": c.estado,  # PENDIENTE, CONFIRMADA, CANCELADA...
        })

    # Serializar a JSON (cadena) para inyectar seguro en template
    calendar_events_json = json.dumps(calendar_events, ensure_ascii=False)

    # Construir semana mínima para la plantilla (si tu template la usa)
    semana = []
    for i in range(7):
        d = (ahora + timedelta(days=i)).date()
        semana.append({
            "nombre": d.strftime("%A"),
            "fecha": d,
            "franjas": [],  # si tienes franjas, llena aquí
        })

    dias_semana = [
        {"key": "MON", "nombre": "Lunes"},
        {"key": "TUE", "nombre": "Martes"},
        {"key": "WED", "nombre": "Miércoles"},
        {"key": "THU", "nombre": "Jueves"},
        {"key": "FRI", "nombre": "Viernes"},
        {"key": "SAT", "nombre": "Sábado"},
        {"key": "SUN", "nombre": "Domingo"},
    ]

    context = {
        "calendar_events_json": calendar_events_json,
        "semana": semana,
        "dias_semana": dias_semana,
        "today": ahora,
    }
    return render(request, 'medico/pages/mi_horario.html', context)

# ---------------------------------------------------------
# Secciones de administración (renderizan las plantillas)
# ---------------------------------------------------------

@login_required
def admin_usuarios(request):
    """
    Vista para la sección 'admin/usuarios/'.
    Muestra la lista de usuarios y renderiza admin/pages/usuarios.html
    """
    if getattr(request.user, 'rol', None) != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('login')

    usuarios = Usuario.objects.all().order_by('username')
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
    }
    return render(request, 'admin/pages/usuarios.html', context)


@login_required
def admin_citas(request):
    """
    Vista para la sección 'admin/citas/'.
    Muestra las citas y renderiza admin/pages/citas.html
    """
    if getattr(request.user, 'rol', None) != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('login')

    citas = Cita.objects.select_related('paciente', 'medico', 'especialidad').order_by('-fecha_hora')
    context = {
        'citas': citas,
        'total_citas': citas.count(),
    }
    return render(request, 'admin/pages/citas.html', context)


@login_required
def admin_especialidades(request):
    """
    Vista para la sección 'admin/especialidades/'.
    Muestra las especialidades y renderiza admin/pages/especialidades.html
    """
    if getattr(request.user, 'rol', None) != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('login')

    especialidades = Especialidad.objects.all().order_by('nombre')
    context = {
        'especialidades': especialidades,
        'total_especialidades': especialidades.count(),
    }
    return render(request, 'admin/pages/especialidades.html', context)


@login_required
def admin_reportes(request):
    """
    Vista para la sección 'admin/reportes/'.
    Prepara algunos KPIs básicos y renderiza admin/pages/reportes.html.
    Puedes ampliar este contexto con consultas más complejas o series para gráficas.
    """
    if getattr(request.user, 'rol', None) != 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('login')

    total_usuarios = Usuario.objects.count()
    total_citas = Cita.objects.count()
    total_especialidades = Especialidad.objects.count()

    # Ejemplo simple de datos para usar en la plantilla (puedes expandir)
    context = {
        'total_usuarios': total_usuarios,
        'total_citas': total_citas,
        'total_especialidades': total_especialidades,
    }
    return render(request, 'admin/pages/reportes.html', context)