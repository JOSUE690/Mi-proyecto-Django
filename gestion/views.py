import requests  # Para Open Library
from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector, Multa
from django.db.models import Sum, Q, Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime
from .forms import UsuarioForm

# --- FUNCIÓN CENTRAL: DETECTA VENCIDOS ---
def actualizar_multas_vencidas():
    hoy = timezone.now().date()
    prestamos_vencidos = Prestamo.objects.filter(
        devuelto=False, 
        fecha_devolucion_esperada__lt=hoy
    )
    
    for prestamo in prestamos_vencidos:
        dias_retraso = (hoy - prestamo.fecha_devolucion_esperada).days
        monto_total = dias_retraso * 0.50
        
        multa, created = Multa.objects.get_or_create(prestamo=prestamo)
        if not multa.pagada:
            multa.monto = monto_total
            multa.save()

# --- VISTA DE INICIO ---
def index(request):
    actualizar_multas_vencidas()
    total_libros = Libro.objects.count()
    total_autores = Autor.objects.count()
    total_copias = Libro.objects.aggregate(Sum('copias_disponibles'))['copias_disponibles__sum'] or 0
    total_multas_valor = Multa.objects.filter(pagada=False).aggregate(Sum('monto'))['monto__sum'] or 0
    
    context = {
        'total_libros': total_libros,
        'total_autores': total_autores,
        'total_copias': total_copias,
        'total_multas_valor': total_multas_valor,
    }
    return render(request, 'inicio.html', context)

# --- GESTIÓN DE LIBROS Y AUTORES ---
def lista_libros(request):
    libros = Libro.objects.all().select_related('autor').order_by('titulo')
    query = request.GET.get('q') 
    if query:
        libros = libros.filter(
            Q(titulo__icontains=query) | 
            Q(autor__nombre__icontains=query) | 
            Q(autor__apellido__icontains=query)
        ).distinct()
    return render(request, 'libros.html', {'libros': libros, 'query': query})

def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    return render(request, 'detalle_libro.html', {'libro': libro})
    
def lista_autores(request):
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    return render(request, 'lista_autores.html', {'autores': autores})

# --- GESTIÓN DE USUARIOS/LECTORES ---
def registro_lector(request):
    if request.method == 'POST':
        nombre, identificacion = request.POST.get('nombre'), request.POST.get('identificacion')
        email, telefono = request.POST.get('email'), request.POST.get('telefono')
        try:
            # Nota: Tu modelo Lector usa User como OneToOneField
            # Este bloque asume que el usuario ya existe o se maneja por registro_usuario
            Lector.objects.create(nombre=nombre, identificacion=identificacion, email=email, telefono=telefono)
            return redirect('gestion:lectores')
        except: 
            return redirect('gestion:registro_lector')
    return render(request, 'registro_lector.html')

def registro_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion:lectores')
    else: 
        form = UsuarioForm()
    return render(request, 'registro_usuario.html', {'form': form, 'titulo': "Registro de Nuevo Usuario"})

def lista_lectores(request):
    lectores = Lector.objects.all().order_by('identificacion')
    return render(request, 'lista_lectores.html', {'lectores': lectores})

# --- GESTIÓN DE PRESTAMOS ---
def lista_prestamos(request):
    prestamos = Prestamo.objects.all().select_related('libro', 'lector')
    query = request.GET.get('q')
    if query:
        prestamos = prestamos.filter(
            Q(libro__titulo__icontains=query) | 
            Q(lector__identificacion__icontains=query)
        ).distinct()
    context = {
        'prestamos_activos': prestamos.filter(devuelto=False).order_by('fecha_devolucion_esperada'),
        'prestamos_historicos': prestamos.filter(devuelto=True).order_by('-fecha_prestamo'),
        'now': timezone.now().date(),
        'query': query,
    }
    return render(request, 'lista_prestamos.html', context)

def nuevo_prestamo(request):
    if request.method == 'POST':
        libro_id, lector_id, fecha_str = request.POST.get('libro'), request.POST.get('lector'), request.POST.get('fecha_devolucion')
        try:
            fecha_esp = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            libro, lector = Libro.objects.get(pk=libro_id), Lector.objects.get(pk=lector_id)
            if libro.copias_disponibles > 0:
                Prestamo.objects.create(libro=libro, lector=lector, fecha_devolucion_esperada=fecha_esp, devuelto=False)
                libro.copias_disponibles -= 1
                libro.save()
                return redirect('gestion:prestamos')
        except: 
            pass
    return render(request, 'nuevo_prestamo.html', {
        'libros': Libro.objects.filter(copias_disponibles__gt=0), 
        'lectores': Lector.objects.all()
    })

def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if not prestamo.devuelto:
        actualizar_multas_vencidas()
        Multa.objects.filter(prestamo=prestamo).update(pagada=True)
        prestamo.devuelto = True
        prestamo.save()
        libro = prestamo.libro
        libro.copias_disponibles += 1
        libro.save()
    return redirect('gestion:prestamos')

# --- GESTIÓN DE MULTAS ---
def lista_multas(request):
    actualizar_multas_vencidas()
    if request.user.is_superuser:
        multas = Multa.objects.filter(pagada=False, prestamo__devuelto=False).select_related('prestamo__libro', 'prestamo__lector')
    else:
        multas = Multa.objects.filter(prestamo__lector__user_id=request.user.id, pagada=False, prestamo__devuelto=False)
    return render(request, 'lista_multas.html', {'multas': multas})

# --- GESTIÓN DE FACTURACIÓN ---
def lista_facturas(request):
    actualizar_multas_vencidas()
    facturas = Multa.objects.filter(pagada=False).values(
        'prestamo__lector__identificacion', 
        'prestamo__lector__user_id'
    ).annotate(
        total_deuda=Sum('monto'),
        cantidad_libros=Count('id')
    ).order_by('-total_deuda')

    deuda_maxima = Multa.objects.filter(pagada=False).aggregate(Max('monto'))['monto__max'] or 0

    return render(request, 'lista_facturas.html', {
        'facturas': facturas,
        'deuda_maxima': deuda_maxima
    })

# --- INTEGRACIÓN CON OPEN LIBRARY  ---
def buscar_libro_api(request):
    isbn = request.GET.get('isbn')
    datos_libro = None
    
    if isbn:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        try:
            response = requests.get(url)
            data = response.json()
            key = f"ISBN:{isbn}"
            
            if key in data:
                info = data[key]
                nombres_autores = [a['name'] for a in info.get('authors', [])]
                
                # Extraemos el año como ENTERO para el IntegerField
                fecha_str = info.get('publish_date', '2026')
                anio_entero = 2026
                try:
                    # Busca los primeros 4 dígitos en la cadena de fecha
                    anio_entero = int(''.join(filter(str.isdigit, fecha_str))[:4])
                except:
                    pass

                datos_libro = {
                    'isbn': isbn,
                    'titulo': info.get('title'),
                    'autores': ", ".join(nombres_autores),
                    'paginas': info.get('number_of_pages', 'N/A'),
                    'portada': info.get('cover', {}).get('large', ''),
                    'anio': anio_entero
                }

                if 'confirmar_importar' in request.GET:
                    # 1. Procesar el Autor
                    nombre_completo = nombres_autores[0] if nombres_autores else "Autor Desconocido"
                    partes = nombre_completo.split(' ', 1)
                    nom = partes[0]
                    ape = partes[1] if len(partes) > 1 else " "
                    
                    autor_obj, _ = Autor.objects.get_or_create(nombre=nom, apellido=ape)
                    
                    # 2. GUARDADO CORRECTO: Usamos campos que existen en tu models.py
                    try:
                        Libro.objects.update_or_create(
                            titulo=datos_libro['titulo'], 
                            defaults={
                                'autor': autor_obj,
                                'copias_disponibles': 5, # Valor por defecto para que no sea 0
                                'publicacion': datos_libro['anio'], # Enviamos el Integer
                            }
                        )
                        return redirect('gestion:libros')
                    except Exception as sql_err:
                        print(f"Error al guardar en SQL: {sql_err}")
                        
        except Exception as e:
            print(f"Error de conexión con API: {e}")
            
    return render(request, 'buscar_api.html', {'libro': datos_libro, 'isbn': isbn})