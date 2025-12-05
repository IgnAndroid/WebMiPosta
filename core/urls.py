from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/medico/', views.medico_dashboard, name='medico_dashboard'),
    path('dashboard/paciente/', views.paciente_dashboard, name='paciente_dashboard'),
    
    # Citas
    path('citas/', views.listar_citas, name='listar_citas'),
    path('citas/crear/', views.crear_cita, name='crear_cita'),
    
    # Secciones de Paciente
    path('paciente/citas/', views.paciente_citas, name='paciente_citas'),
    path('paciente/historial/', views.historial_medico, name='historial_medico'),
    path('paciente/historial/', views.historial_medico, name='paciente_historial'),  # Alias
    path('paciente/perfil/', views.perfil_paciente, name='perfil_paciente'),

    # Secciones de Médico (NUEVAS)
    path('medico/mis-citas/', views.medico_mis_citas, name='medico_mis_citas'),
    path('medico/mis-pacientes/', views.medico_mis_pacientes, name='medico_mis_pacientes'),
    path('medico/mi-horario/', views.medico_horario, name='medico_horario'),
    path('medico/estadisticas/', views.medico_estadisticas, name='medico_estadisticas'),
    path('medico/perfil/', views.medico_perfil, name='medico_perfil'),

    # Horario - agregar franja (la plantilla usa 'medico_agregar_franja')
    path('medico/horario/agregar/', views.medico_agregar_franja, name='medico_agregar_franja'),

    # Opcionales (recomendado para que los enlaces "Ver Ficha" y "Agendar" funcionen)
    path('medico/paciente/<int:pk>/', views.medico_paciente_detail, name='medico_paciente_detail'),
    path('medico/paciente/<int:pk>/agendar/', views.medico_agendar, name='medico_agendar'),

]