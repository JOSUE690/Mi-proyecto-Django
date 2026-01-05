from django.urls import path
from . import views

app_name = 'gestion' 

urlpatterns = [
    # --- INICIO ---
    path('', views.index, name='inicio'),
    path('index/', views.index, name='index'), # Por si acaso usas 'index'

    # --- LIBROS Y AUTORES ---
    path('libros/', views.lista_libros, name='libros'),
    path('libros/lista/', views.lista_libros, name='lista_libros'),
    path('libro/<int:pk>/', views.detalle_libro, name='detalle_libro'),
    path('autores/', views.lista_autores, name='autores'),
    path('autores/lista/', views.lista_autores, name='lista_autores'),

    # --- USUARIOS Y LECTORES ---
    path('lectores/', views.lista_lectores, name='lectores'),
    path('lectores/lista/', views.lista_lectores, name='lista_lectores'),
    path('registro-lector/', views.registro_lector, name='registro_lector'),
    path('registro-usuario/', views.registro_usuario, name='registro_usuario'),

    # --- PRÉSTAMOS ---
    path('prestamos/', views.lista_prestamos, name='prestamos'),
    path('prestamos/lista/', views.lista_prestamos, name='lista_prestamos'),
    path('nuevo-prestamo/', views.nuevo_prestamo, name='nuevo_prestamo'),
    path('devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),

    # --- MULTAS Y FACTURACIÓN ---
    path('multas/', views.lista_multas, name='multas'),
    path('multas/lista/', views.lista_multas, name='lista_multas'), # <-- ESTA LÍNEA ARREGLA TU ERROR ACTUAL
    path('facturas/', views.lista_facturas, name='facturas'),
    path('facturas/lista/', views.lista_facturas, name='lista_facturas'),

    # --- OPEN LIBRARY ---
    path('buscar-internet/', views.buscar_libro_api, name='buscar_api'),
]