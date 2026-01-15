import requests  # Para Open Library
from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector, Multa
from django.db.models import Sum, Q, Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime
from .forms import UsuarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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

# --- VISTAS DE AUTENTICACIÓN ---
def ingresar(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            # Redirige a 'next' si existe (para evitar errores 404), sino a inicio
            return redirect(request.GET.get('next', 'gestion:inicio'))
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, 'login.html')

def salir(request):
    logout(request)
    return redirect('gestion:ingresar')

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

# --- MODO LECTOR: CATÁLOGO Y ESCOGER ---
@login_required
def catalogo_lector(request):
    libros = Libro.objects.filter(copias_disponibles__gt=0).select_related('autor')
    query = request.GET.get('q')
    if query:
        libros = libros.filter(Q(titulo__icontains=query) | Q(autor__nombre__icontains=query))
    return render(request, 'catalogo_lector.html', {'libros': libros, 'query': query})

@login_required
def escoger_libro(request, libro_id):
    libro = get_object_or_404(Libro.objects.select_related('autor'), id=libro_id)
    
    if request.method == 'POST':
        fecha_str = request.POST.get('fecha_retorno')
        try:
            fecha_esp = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            lector, _ = Lector.objects.get_or_create(
                user=request.user,
                defaults={
                    'identificacion': request.user.id,
                    'email': request.user.email or f"{request.user.username}@biblioteca.com"
                }
            )

            if libro.copias_disponibles > 0:
                Prestamo.objects.create(
                    libro=libro, 
                    lector=lector, 
                    fecha_devolucion_esperada=fecha_esp, 
                    devuelto=False
                )
                libro.copias_disponibles -= 1
                libro.save()
                messages.success(request, f"¡Éxito! Has reservado '{libro.titulo}' hasta el {fecha_esp}.")
                return redirect('gestion:mis_prestamos')
            else:
                messages.error(request, "Ya no hay copias disponibles de este libro.")
                return redirect('gestion:catalogo_lector')
        except ValueError:
            messages.error(request, "Fecha inválida. Por favor selecciona una fecha correcta.")
            
    return render(request, 'confirmar_reserva.html', {'libro': libro})

@login_required
def mis_prestamos(request):
    actualizar_multas_vencidas()
    prestamos = Prestamo.objects.filter(
        lector__user=request.user, 
        devuelto=False
    ).select_related('libro').order_by('fecha_devolucion_esperada')
    return render(request, 'mis_prestamos.html', {'prestamos': prestamos})

# --- GESTIÓN DE PRÉSTAMOS (ADMIN) ---
@login_required
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

@login_required
def nuevo_prestamo(request):
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        lector_id = request.POST.get('lector')
        fecha_str = request.POST.get('fecha_devolucion')
        try:
            fecha_esp = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            libro = Libro.objects.get(pk=libro_id)
            lector = Lector.objects.get(pk=lector_id)
            if libro.copias_disponibles > 0:
                Prestamo.objects.create(libro=libro, lector=lector, fecha_devolucion_esperada=fecha_esp, devuelto=False)
                libro.copias_disponibles -= 1
                libro.save()
                return redirect('gestion:prestamos')
        except: pass
    return render(request, 'nuevo_prestamo.html', {
        'libros': Libro.objects.filter(copias_disponibles__gt=0), 
        'lectores': Lector.objects.all()
    })

@login_required
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

# --- MULTAS Y FACTURACIÓN ---
@login_required
def lista_multas(request):
    actualizar_multas_vencidas()
    if request.user.is_superuser:
        multas = Multa.objects.filter(pagada=False, prestamo__devuelto=False).select_related('prestamo__libro', 'prestamo__lector')
    else:
        # Aquí se corrige el error del ID: filtramos por el usuario logueado
        multas = Multa.objects.filter(prestamo__lector__user=request.user, pagada=False, prestamo__devuelto=False)
    return render(request, 'lista_multas.html', {'multas': multas})

# --- VISTA NUEVA: ROL BODEGUERO ---
@login_required
def inventario_bodega(request):
    # Esta vista permite al Bodeguero ver la ubicación física (pasillos/estantes)
    libros = Libro.objects.all().order_by('pasillo', 'estante')
    query = request.GET.get('pasillo')
    if query:
        libros = libros.filter(pasillo__icontains=query)
    return render(request, 'inventario_bodega.html', {'libros': libros, 'query': query})

def lista_facturas(request):
    actualizar_multas_vencidas()
    multas_pendientes = Multa.objects.filter(pagada=False)
    query = request.GET.get('q')
    if query:
        multas_pendientes = multas_pendientes.filter(
            Q(prestamo__lector__identificacion__icontains=query) |
            Q(prestamo__lector__user__username__icontains=query)
        )
    facturas = multas_pendientes.values(
        'prestamo__lector__identificacion', 
        'prestamo__lector__user__username'
    ).annotate(
        total_deuda=Sum('monto'),
        cantidad_libros=Count('id')
    ).order_by('-total_deuda')
    deuda_maxima = multas_pendientes.aggregate(Max('monto'))['monto__max'] or 0
    return render(request, 'lista_facturas.html', {'facturas': facturas, 'deuda_maxima': deuda_maxima, 'query': query})

# --- API OPEN LIBRARY ---
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
                fecha_str = info.get('publish_date', '2026')
                anio_entero = 2026
                try:
                    anio_entero = int(''.join(filter(str.isdigit, fecha_str))[:4])
                except: pass
                datos_libro = {
                    'isbn': isbn, 'titulo': info.get('title'),
                    'autores': ", ".join(nombres_autores),
                    'paginas': info.get('number_of_pages', 'N/A'),
                    'portada': info.get('cover', {}).get('large', ''),
                    'anio': anio_entero
                }
                if 'confirmar_importar' in request.GET:
                    nombre_completo = nombres_autores[0] if nombres_autores else "Autor Desconocido"
                    partes = nombre_completo.split(' ', 1)
                    nom, ape = partes[0], (partes[1] if len(partes) > 1 else " ")
                    autor_obj, _ = Autor.objects.get_or_create(nombre=nom, apellido=ape)
                    Libro.objects.update_or_create(
                        titulo=datos_libro['titulo'], 
                        defaults={'autor': autor_obj, 'copias_disponibles': 5, 'publicacion': datos_libro['anio']}
                    )
                    return redirect('gestion:libros')
        except Exception as e:
            print(f"Error: {e}")
    return render(request, 'buscar_api.html', {'libro': datos_libro, 'isbn': isbn})

# --- VISTAS RESTANTES ---
def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    return render(request, 'detalle_libro.html', {'libro': libro})
    
def lista_autores(request):
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    return render(request, 'lista_autores.html', {'autores': autores})

def registro_lector(request):
    if request.method == 'POST':
        identificacion = request.POST.get('identificacion')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        try:
            Lector.objects.create(identificacion=identificacion, email=email, telefono=telefono)
            return redirect('gestion:lectores')
        except: return redirect('gestion:registro_lector')
    return render(request, 'registro_lector.html')

def registro_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion:lectores')
    else: form = UsuarioForm()
    return render(request, 'registro_usuario.html', {'form': form, 'titulo': "Registro de Nuevo Usuario"})

def lista_lectores(request):
    lectores = Lector.objects.all().order_by('identificacion')
    return render(request, 'lista_lectores.html', {'lectores': lectores})