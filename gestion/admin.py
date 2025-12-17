from django.contrib import admin
# 1. Importa los modelos
from .models import Autor, Libro, Lector, Prestamo 
# 2. Importa el modelo User base de Django y su clase de Admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 


# ----------------------------------------------------
# 1. Administración de Libros
# ----------------------------------------------------
# Clase para personalizar la vista del listado de Libros en el Admin
class LibroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'publicacion', 'copias_disponibles')
    list_filter = ('autor', 'publicacion')
    search_fields = ('titulo', 'autor__nombre', 'autor__apellido')


# ----------------------------------------------------
# 2. Administración de Lectores (Integrado con User)
# ----------------------------------------------------

# Paso 2.1: Crear una vista en línea (Inline) para mostrar los datos de Lector
# El perfil Lector aparecerá dentro del formulario de edición del Usuario de Django.
class LectorInline(admin.StackedInline):
    model = Lector
    can_delete = False
    verbose_name_plural = 'Perfil de Lector'
    # Solo mostramos los campos propios de Lector
    fields = ('identificacion', 'telefono') 

# Paso 2.2: Sobreescribir el UserAdmin de Django
class UsuarioAdmin(BaseUserAdmin):
    """
    Personaliza el formulario y la vista de listado del modelo User
    para incluir los campos del modelo Lector (a través del inline).
    """
    inlines = (LectorInline,)
    
    # Campo calculado para mostrar la Identificación del Lector en el listado
    def get_identificacion(self, obj):
        # Accedemos al Lector asociado a este User
        try:
            return obj.lector.identificacion
        except Lector.DoesNotExist:
            return "N/A"
    get_identificacion.short_description = 'Identificación'
    
    # NUEVO list_display que usa el username, email (del User) y la Identificación (del Lector)
    list_display = ('username', 'email', 'get_identificacion', 'is_staff')
    
    # Campos por los que se puede buscar (usamos el username del User)
    search_fields = ('username', 'email')
    
    # NOTA: Los 'fieldsets' se heredan y funcionan bien.


# ----------------------------------------------------
# 3. Administración de Préstamos
# ----------------------------------------------------
@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    # Enlazamos a los objetos, ahora Lector muestra el nombre de usuario
    list_display = ('libro', 'lector', 'fecha_prestamo', 'fecha_devolucion_esperada', 'devuelto')
    list_filter = ('devuelto', 'fecha_prestamo', 'lector')
    list_editable = ('devuelto',)
    # Búsqueda en el título del libro y el nombre de usuario del lector
    search_fields = ('libro__titulo', 'lector__user__username')


# ----------------------------------------------------
# 4. Registro de Modelos (Final)
# ----------------------------------------------------

# Desregistramos el User Admin por defecto y registramos nuestra versión personalizada
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)

# Registra los modelos restantes
admin.site.register(Autor)
admin.site.register(Libro, LibroAdmin)

# NOTA: Ya NO registramos Lector por separado (@admin.register(Lector) está eliminado)
# porque se maneja dentro de UsuarioAdmin.