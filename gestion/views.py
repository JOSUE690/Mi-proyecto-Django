from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector # Asegúrate que Lector esté bien definido en models.py
from django.db.models import Sum, Q 
from django.utils import timezone
from datetime import datetime
from .forms import UsuarioForm # <--- ¡IMPORTACIÓN CLAVE! Necesaria para el nuevo registro


# 1. VISTA: Dashboard (Página de inicio)
def index(request):
    # Obtener métricas para el Dashboard
    total_libros = Libro.objects.count()
    total_autores = Autor.objects.count()
    
    total_copias_qs = Libro.objects.aggregate(Sum('copias_disponibles'))
    total_copias = total_copias_qs.get('copias_disponibles__sum') or 0
    
    context = {
        'total_libros': total_libros,
        'total_autores': total_autores,
        'total_copias': total_copias,
    }
    
    return render(request, 'inicio.html', context)


# MÓDULO LIBROS Y AUTORES

# 2. VISTA: Listado de Libros (Catálogo de Recursos) con BÚSQUEDA
def lista_libros(request):
    libros = Libro.objects.all().select_related('autor').order_by('titulo')
    query = None 

    # LÓGICA DE BÚSQUEDA
    if 'q' in request.GET:
        query = request.GET.get('q') 

        if query:
            # Búsqueda en Título, Nombre del Autor O Apellido del Autor
            libros = libros.filter(
                Q(titulo__icontains=query) |
                Q(autor__nombre__icontains=query) |
                Q(autor__apellido__icontains=query)
            ).distinct()
            
    context = {
        'libros': libros,
        'query': query, 
    }
    
    return render(request, 'libros.html', context)


# 3. VISTA: Detalle de un Libro
def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    
    context = {
        'libro': libro,
    }
    
    return render(request, 'detalle_libro.html', context)
    
    
# 4. VISTA: Listado de Autores
def lista_autores(request):
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    
    context = {
        'autores': autores
    }
    
    return render(request, 'lista_autores.html', context)


# MÓDULO LECTORES (USUARIOS)

# 5. VISTA: Registro de Nuevo Lector (Registro simple sin contraseña)
def registro_lector(request):
    if request.method == 'POST':
        # NOTA: Esta vista ya no es compatible si Lector en models.py usa OneToOneField con User.
        # Si Lector usa OneToOneField, esta vista debe ser actualizada o eliminada.
        nombre = request.POST.get('nombre')
        identificacion = request.POST.get('identificacion') 
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        
        try:
            # Si Lector ya está vinculado a User, esta línea causará un error
            Lector.objects.create(
                nombre=nombre,
                identificacion=identificacion,
                email=email,
                telefono=telefono,
            )
            return redirect('gestion:lectores') 

        except Exception as e:
            print(f"Error al registrar lector: {e}") 
            return redirect('gestion:registro_lector') 
            
    return render(request, 'registro_lector.html')


# NUEVA FUNCIÓN: 5.1 VISTA: Registro de Nuevo Usuario (CON CONTRASEÑA y Django Auth)
def registro_usuario(request):
    if request.method == 'POST':
        # Utilizamos el nuevo formulario que maneja contraseña
        form = UsuarioForm(request.POST) 
        if form.is_valid():
            # form.save() llama a la lógica en forms.py que crea el User y el Lector asociado
            user = form.save() 
            return redirect('gestion:lectores') 
    else:
        form = UsuarioForm()
        
    context = {
        'form': form,
        'titulo': "Registro de Nuevo Usuario (Con Contraseña)"
    }
    # Renderiza la nueva plantilla HTML para el registro con contraseña
    return render(request, 'registro_usuario.html', context)


# 6. VISTA: Listado de Lectores (Usuarios)
def lista_lectores(request):
    # NOTA: Si Lector usa OneToOneField, esta vista debe ser actualizada para usar el campo 'user'
    # para obtener el nombre (lector.user.username) en la plantilla.
    lectores = Lector.objects.all().order_by('identificacion') # Ordenar por identificación o username
    
    context = {
        'lectores': lectores
    }
    
    return render(request, 'lista_lectores.html', context)


# MÓDULO PRÉSTAMOS

# 7. VISTA: Listado de Préstamos (Con Lógica de Pestañas y BÚSQUEDA)
def lista_prestamos(request):
    # Consulta base para todos los préstamos
    prestamos = Prestamo.objects.all().select_related('libro', 'lector')
    query = None # Inicializar la variable de búsqueda

    # LÓGICA DE BÚSQUEDA
    if 'q' in request.GET:
        query = request.GET.get('q')
        
        if query:
            # Filtramos en Título de Libro, Nombre de Lector O Identificación de Lector
            # NOTA: Si Lector está vinculado a User, tendrás que filtrar por lector__user__username
            filtro_busqueda = Q(libro__titulo__icontains=query) | \
                             Q(lector__identificacion__icontains=query)
                             
            prestamos = prestamos.filter(filtro_busqueda).distinct()


    # Préstamos Activos (devuelto=False)
    prestamos_activos = prestamos.filter(devuelto=False).order_by('fecha_devolucion_esperada')
    
    # Préstamos Históricos (devuelto=True)
    prestamos_historicos = prestamos.filter(devuelto=True).order_by('-fecha_prestamo')

    context = {
        'prestamos_activos': prestamos_activos,
        'prestamos_historicos': prestamos_historicos,
        'now': timezone.now().date(),
        'query': query, # Pasamos el término de búsqueda a la plantilla
    }
    
    return render(request, 'lista_prestamos.html', context)


# 8. VISTA: Para Crear un Nuevo Préstamo
def nuevo_prestamo(request):
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        lector_id = request.POST.get('lector')
        fecha_str = request.POST.get('fecha_devolucion') 
        
        try:
            fecha_devolucion_esperada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            libro = Libro.objects.get(pk=libro_id)
            # NOTA: Si Lector usa OneToOneField, lector_id ya no es el ID de la fila, sino el ID del User.
            lector = Lector.objects.get(pk=lector_id)
            
            if libro.copias_disponibles > 0:
                Prestamo.objects.create(
                    libro=libro,
                    lector=lector,
                    fecha_devolucion_esperada=fecha_devolucion_esperada,
                    devuelto=False
                )

                libro.copias_disponibles -= 1
                libro.save()

                return redirect('gestion:prestamos')
            else:
                pass 
                
        except (Libro.DoesNotExist, Lector.DoesNotExist, ValueError):
            pass
            
    libros = Libro.objects.filter(copias_disponibles__gt=0).order_by('titulo')
    lectores = Lector.objects.all().order_by('user__username') # Ordenar por el nombre de usuario de Django
    
    context = {
        'libros': libros,
        'lectores': lectores
    }
    
    return render(request, 'nuevo_prestamo.html', context)


# 9. VISTA: Para Registrar la Devolución de un Préstamo
def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    
    if not prestamo.devuelto:
        prestamo.devuelto = True
        prestamo.save()
        
        libro = prestamo.libro
        libro.copias_disponibles += 1
        libro.save()
        
    return redirect('gestion:prestamos')