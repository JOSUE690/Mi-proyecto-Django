from django.urls import path
from . import views

# Define el app_name
app_name = 'gestion' 

urlpatterns = [
    # Módulo Base
    path('', views.index, name='inicio'),
    
    # Módulo Libros
    path('libros/', views.lista_libros, name='libros'),
    path('libros/<int:pk>/', views.detalle_libro, name='detalle_libro'),
    
    # Módulo Autores
    path('autores/', views.lista_autores, name='autores'),
    
    # Módulo Préstamos 
    # 1. Listado
    path('prestamos/', views.lista_prestamos, name='prestamos'),
    # 2. Registro de Nuevo Préstamo
    path('prestamos/nuevo/', views.nuevo_prestamo, name='nuevo_prestamo'),
    # 3. RUTA NUEVA: Para registrar la devolución de un préstamo
    path('prestamos/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    
    # MÓDULO LECTORES/USUARIOS
    
    # 1. RUTA ANTIGUA: Registro de Lector (sin contraseña)
    path('lectores/nuevo/', views.registro_lector, name='registro_lector'),

    # 2. RUTA NUEVA: Registro de Usuario (¡CON CONTRASEÑA y Django Auth!)
    # Usamos 'usuarios/' en la URL para distinguirla de la antigua 'lectores/'
    path('usuarios/registro/', views.registro_usuario, name='registro_usuario'), 
    
    # 3. Listado de Lectores/Usuarios (Asumiendo que esta URL llama a lista_lectores)
    path('lectores/', views.lista_lectores, name='lectores'),
]