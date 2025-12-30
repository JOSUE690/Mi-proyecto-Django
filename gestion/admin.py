from django.contrib import admin
from .models import Autor, Libro, Lector, Prestamo, Multa
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 

class LibroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'publicacion', 'copias_disponibles')
    list_filter = ('autor', 'publicacion')
    search_fields = ('titulo', 'autor__nombre', 'autor__apellido')

class LectorInline(admin.StackedInline):
    model = Lector
    can_delete = False
    verbose_name_plural = 'Perfil de Lector'
    fields = ('identificacion', 'telefono') 

class UsuarioAdmin(BaseUserAdmin):
    inlines = (LectorInline,)
    
    def get_identificacion(self, obj):
        try:
            return obj.lector.identificacion
        except Lector.DoesNotExist:
            return "N/A"
    get_identificacion.short_description = 'Identificación'
    
    list_display = ('username', 'email', 'get_identificacion', 'is_staff')
    search_fields = ('username', 'email')

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('libro', 'lector', 'fecha_prestamo', 'fecha_devolucion_esperada', 'devuelto')
    list_filter = ('devuelto', 'fecha_prestamo', 'lector')
    list_editable = ('devuelto',)
    search_fields = ('libro__titulo', 'lector__user__username')

@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('get_usuario', 'get_libro', 'monto', 'pagada', 'fecha_generacion')
    list_filter = ('pagada', 'fecha_generacion')
    list_editable = ('pagada',)

    def get_usuario(self, obj):
        return obj.prestamo.lector.user.username
    get_usuario.short_description = 'Usuario'

    def get_libro(self, obj):
        return obj.prestamo.libro.titulo
    get_libro.short_description = 'Libro'

admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)
admin.site.register(Autor)
admin.site.register(Libro, LibroAdmin)