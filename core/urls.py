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
]