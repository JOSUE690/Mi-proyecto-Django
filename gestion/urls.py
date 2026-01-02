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
    path('prestamos/', views.lista_prestamos, name='prestamos'),
    path('prestamos/nuevo/', views.nuevo_prestamo, name='nuevo_prestamo'),
    path('prestamos/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    
    # MÓDULO LECTORES/USUARIOS
    path('lectores/nuevo/', views.registro_lector, name='registro_lector'),
    path('usuarios/registro/', views.registro_usuario, name='registro_usuario'), 
    path('lectores/', views.lista_lectores, name='lectores'),

    # MÓDULO MULTAS Y FACTURACIÓN
    # IMPORTANTE: He puesto 'lista_multas' para que coincida con el menú neón
    path('multas/', views.lista_multas, name='lista_multas'),
    
    # RUTA AÑADIDA PARA EL COMMIT 7 [cite: 2025-11-12]
    path('facturas/', views.lista_facturas, name='lista_facturas'),
]