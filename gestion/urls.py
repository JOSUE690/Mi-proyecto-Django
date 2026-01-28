from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    # Inicio y Auth
    path('', views.index, name='inicio'),
    path('ingresar/', views.ingresar, name='ingresar'),
    path('salir/', views.salir, name='salir'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    
    # Bibliotecario y Gestión
    path('bibliotecario/', views.panel_bibliotecario, name='panel_bibliotecario'),
    path('libros/', views.lista_libros, name='libros'),
    path('libros/<int:pk>/', views.detalle_libro, name='detalle_libro'),
    path('autores/', views.lista_autores, name='autores'),
    path('prestamos/', views.lista_prestamos, name='prestamos'),
    path('prestamos/nuevo/', views.nuevo_prestamo, name='nuevo_prestamo'),
    path('prestamos/devolver/<int:pk>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('lectores/', views.lista_lectores, name='lectores'),
    path('registro-lector/', views.registro_lector, name='registro_lector'),
    path('multas/', views.lista_multas, name='multas'),
    path('facturas/', views.lista_facturas, name='facturas'),

    # Bodeguero (Rutas internas)
    path('bodega/', views.inventario_bodega, name='inventario_bodega'),
    path('bodega/buscar/', views.buscar_libro_api, name='buscar_api'),
    # --- RUTA NUEVA PARA ACTUALIZAR STOCK ---
    path('bodega/actualizar/<int:libro_id>/', views.actualizar_stock_bodega, name='actualizar_stock_bodega'),

    # Lector
    path('catalogo/', views.catalogo_lector, name='catalogo_lector'),
    path('mis-prestamos/', views.mis_prestamos, name='mis_prestamos'),
    path('escoger/<int:libro_id>/', views.escoger_libro, name='escoger_libro'),
]