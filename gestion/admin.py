from django.contrib import admin
from .models import Autor, Libro, Lector, Prestamo # 1. Importa los nuevos modelos

# ----------------------------------------------------
# 1. Administración de Libros (Ya la tenías)
# ----------------------------------------------------
# Clase para personalizar la vista del listado de Libros en el Admin
class LibroAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista de Libros
    list_display = ('titulo', 'autor', 'publicacion', 'copias_disponibles')
    # Campos por los que se puede filtrar la lista
    list_filter = ('autor', 'publicacion')
    # Campos para la barra de búsqueda
    search_fields = ('titulo', 'autor__nombre', 'autor__apellido')


# ----------------------------------------------------
# 2. Administración de Lectores (NUEVO)
# ----------------------------------------------------
@admin.register(Lector)
class LectorAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista de Lectores
    list_display = ('nombre', 'identificacion', 'email')
    # Campos por los que se puede buscar
    search_fields = ('nombre', 'identificacion')


# ----------------------------------------------------
# 3. Administración de Préstamos (NUEVO)
# ----------------------------------------------------
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista de Préstamos
    list_display = ('libro', 'lector', 'fecha_prestamo', 'fecha_devolucion_esperada', 'devuelto')
    # Campos para filtrar la lista
    list_filter = ('devuelto', 'fecha_prestamo', 'lector')
    # Permite editar el campo 'devuelto' directamente desde la lista
    list_editable = ('devuelto',)


# ----------------------------------------------------
# 4. Registro de Modelos (Base)
# ----------------------------------------------------
admin.site.register(Autor)
admin.site.register(Libro, LibroAdmin)