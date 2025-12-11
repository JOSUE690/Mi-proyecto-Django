from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector
from django.db.models import Sum 
from django.utils import timezone


# 1. VISTA: Dashboard (Página de inicio)
def index(request):
    # Obtener métricas para el Dashboard
    total_libros = Libro.objects.count()
    total_autores = Autor.objects.count()
    
    # Sumar todas las copias disponibles.
    total_copias_qs = Libro.objects.aggregate(Sum('copias_disponibles'))
    total_copias = total_copias_qs.get('copias_disponibles__sum') or 0
    
    context = {
        'total_libros': total_libros,
        'total_autores': total_autores,
        'total_copias': total_copias,
    }
    
    return render(request, 'inicio.html', context)



# MÓDULO LIBROS Y AUTORES

# 2. VISTA: Listado de Libros (Catálogo de Recursos)
def lista_libros(request):
    # Consulta todos los libros y obtiene los datos del autor en una sola consulta
    libros = Libro.objects.all().select_related('autor').order_by('titulo')
    
    context = {
        'libros': libros
    }
    
    return render(request, 'libros.html', context)


# 3. VISTA: Detalle de un Libro
def detalle_libro(request, pk):
    # get_object_or_404 busca el libro por su clave primaria (pk) o muestra un error 404
    libro = get_object_or_404(Libro, pk=pk)
    
    context = {
        'libro': libro,
    }
    
    return render(request, 'detalle_libro.html', context)
    
    
# 4. VISTA: Listado de Autores
def lista_autores(request):
    # Consulta todos los autores, los ordena por nombre y precarga los libros relacionados (prefetch_related)
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    
    context = {
        'autores': autores
    }
    
    return render(request, 'lista_autores.html', context)


# MÓDULO PRÉSTAMOS (NUEVO)

# 5. VISTA: Listado de Préstamos (Con Lógica de Pestañas)
def lista_prestamos(request):
    # Consulta todos los préstamos, optimizando para obtener los datos de Libro y Lector
    prestamos = Prestamo.objects.all().select_related('libro', 'lector')
    
    # Préstamos Activos (devuelto=False)
    prestamos_activos = prestamos.filter(devuelto=False).order_by('fecha_devolucion_esperada')
    
    # Préstamos Históricos (devuelto=True)
    prestamos_historicos = prestamos.filter(devuelto=True).order_by('-fecha_prestamo')

    context = {
        'prestamos_activos': prestamos_activos,
        'prestamos_historicos': prestamos_historicos,
        'now': timezone.now().date(), # Para comparar fechas en la plantilla (Ej: Préstamo Vencido)
    }
    
    return render(request, 'lista_prestamos.html', context)


# 6. VISTA: Para Crear un Nuevo Préstamo (Lógica de Negocio: Decrementa inventario)
def nuevo_prestamo(request):
    if request.method == 'POST':
        # 1. Obtener datos del formulario
        libro_id = request.POST.get('libro')
        lector_id = request.POST.get('lector')
        fecha_devolucion_esperada = request.POST.get('fecha_devolucion')
        
        try:
            libro = Libro.objects.get(pk=libro_id)
            lector = Lector.objects.get(pk=lector_id)

            # 2. Lógica de negocio: Verificar si hay copias disponibles
            if libro.copias_disponibles > 0:
                # 3. Crear el objeto Prestamo
                Prestamo.objects.create(
                    libro=libro,
                    lector=lector,
                    fecha_devolucion_esperada=fecha_devolucion_esperada,
                    devuelto=False
                )

                # 4. Actualizar inventario (Decrementa copias disponibles)
                libro.copias_disponibles -= 1
                libro.save()

                # 5. Redirigir al listado de préstamos activos
                return redirect('gestion:prestamos')
            else:
                # Si no hay copias
                pass 
                
        except (Libro.DoesNotExist, Lector.DoesNotExist):
            # Manejar errores
            pass
            
    # Para el método GET (mostrar formulario) o POST fallido
    libros = Libro.objects.filter(copias_disponibles__gt=0).order_by('titulo') # Solo libros con copias > 0
    lectores = Lector.objects.all().order_by('nombre')
    
    context = {
        'libros': libros,
        'lectores': lectores
    }
    
    return render(request, 'nuevo_prestamo.html', context)


# 7. VISTA: Para Registrar la Devolución de un Préstamo (Lógica de Negocio: Incrementa inventario)
def devolver_prestamo(request, pk):
    # Buscamos el préstamo por su clave primaria (pk)
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    # Solo procedemos si el préstamo NO ha sido devuelto ya
    if not prestamo.devuelto:
        # 1. Marcar el préstamo como devuelto
        prestamo.devuelto = True
        prestamo.save()
        
        # 2. Actualizar inventario (Incrementa copias disponibles)
        libro = prestamo.libro
        libro.copias_disponibles += 1
        libro.save()
        
    # Redirigir a la lista de préstamos
    return redirect('gestion:prestamos')