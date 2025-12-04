from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # Admin
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # Médico
    path('dashboard/medico/', views.medico_dashboard, name='medico_dashboard'),

    # Paciente
    path('dashboard/paciente/', views.paciente_dashboard, name='paciente_dashboard'),
    path('dashboard/paciente/citas/', views.paciente_citas, name='paciente_citas'),
    path('dashboard/paciente/historial_medico/', views.historial_medico, name='paciente_historial'),
    path('dashboard/paciente/perfil/', views.perfil_paciente, name='perfil_paciente'),
    
    # Rutas independientes (opcional)
    path('paciente/historial/', views.historial_medico, name='historial_medico'),
    path('citas/crear/', views.crear_cita, name='crear_cita'),
    path('citas/listar/', views.listar_citas, name='listar_citas'),
]
