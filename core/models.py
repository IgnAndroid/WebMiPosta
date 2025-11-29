from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """Tabla: usuarios"""
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('MEDICO', 'Médico'),
        ('PACIENTE', 'Paciente'),
    ]
    
    rol = models.CharField(max_length=10, choices=ROLES, default='PACIENTE')
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"


class Rol(models.Model):
    """Tabla: roles"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre


class Especialidad(models.Model):
    """Tabla: especialidades"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'especialidades'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
    
    def __str__(self):
        return self.nombre


class Cita(models.Model):
    """Tabla: citas"""
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]
    
    paciente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='citas_paciente', limit_choices_to={'rol': 'PACIENTE'})
    medico = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='citas_medico', limit_choices_to={'rol': 'MEDICO'})
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_hora = models.DateTimeField()
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citas'
        ordering = ['-fecha_hora']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
    
    def __str__(self):
        return f"Cita: {self.paciente.username} con Dr. {self.medico.username}"


class Recordatorio(models.Model):
    """Tabla: recordatorios"""
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='recordatorios')
    fecha_envio = models.DateTimeField()
    mensaje = models.TextField()
    enviado = models.BooleanField(default=False)
    fecha_enviado = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'recordatorios'
        ordering = ['-fecha_envio']
        verbose_name = 'Recordatorio'
        verbose_name_plural = 'Recordatorios'
    
    def __str__(self):
        return f"Recordatorio: {self.cita}"


class Notificacion(models.Model):
    """Tabla: notificaciones"""
    TIPOS = [
        ('INFO', 'Información'),
        ('ALERTA', 'Alerta'),
        ('RECORDATORIO', 'Recordatorio'),
        ('URGENTE', 'Urgente'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INFO')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notificaciones'
        ordering = ['-creada_en']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"