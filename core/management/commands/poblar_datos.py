from django.core.management.base import BaseCommand
from core.models import Rol, Especialidad, Usuario

class Command(BaseCommand):
    help = 'Poblar datos iniciales del sistema'

    def handle(self, *args, **kwargs):
        # ... código anterior de roles y especialidades ...
        
        self.stdout.write('')
        self.stdout.write('Creando usuarios de prueba...')
        
        # Crear usuarios de prueba
        usuarios = [
            # Administradores
            {
                'username': 'admin',
                'email': 'admin@miposta.com',
                'password': 'admin123',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'rol': 'ADMIN'
            },
            # Médicos
            {
                'username': 'drjuan',
                'email': 'drjuan@miposta.com',
                'password': 'medico123',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'rol': 'MEDICO',
                'telefono': '999888777'
            },
            {
                'username': 'dramaria',
                'email': 'dramaria@miposta.com',
                'password': 'medico123',
                'first_name': 'María',
                'last_name': 'García',
                'rol': 'MEDICO',
                'telefono': '999888666'
            },
            # Pacientes
            {
                'username': 'carlos',
                'email': 'carlos@mail.com',
                'password': 'paciente123',
                'first_name': 'Carlos',
                'last_name': 'Ramírez',
                'rol': 'PACIENTE',
                'telefono': '987654321'
            },
            {
                'username': 'ana',
                'email': 'ana@mail.com',
                'password': 'paciente123',
                'first_name': 'Ana',
                'last_name': 'López',
                'rol': 'PACIENTE',
                'telefono': '987654322'
            },
        ]
        
        for user_data in usuarios:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            if not Usuario.objects.filter(username=username).exists():
                user = Usuario.objects.create_user(username=username, password=password, **user_data)
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario creado: {username} ({user.get_rol_display()})'))
            else:
                self.stdout.write(self.style.WARNING(f'- Usuario ya existe: {username}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Datos poblados correctamente'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('')
        self.stdout.write('Usuarios de prueba:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Médico: drjuan / medico123')
        self.stdout.write('  Médico: dramaria / medico123')
        self.stdout.write('  Paciente: carlos / paciente123')
        self.stdout.write('  Paciente: ana / paciente123')