import requests  # Para Open Library
import xmlrpc.client  # Para conectar con Odoo (Incluido en Python)
from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector, Multa
from django.db.models import Sum, Q, Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime
from .forms import UsuarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse

# --- CONFIGURACIÓN DE ODOO (TUS CREDENCIALES VERIFICADAS) ---
ODOO_URL = 'http://localhost:8069'
ODOO_DB = '01'
ODOO_USER = 'coraquillafreddy@gmail.com'
ODOO_PASS = '1726391673'

def sincronizar_con_odoo(titulo, isbn):
    """ 
    Sincronización definitiva: Enviamos solo los campos que sabemos que Odoo acepta
    para evitar el error 'ValueError: Invalid field'.
    """
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
        if uid:
            models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
            
            # Solo dejamos los campos que NO dan error en tu terminal
            data = {
                'nombre_libro': titulo,  # Campo Nombre Libro
                'isbn': isbn,            # Campo ISBN
            }
            
            nuevo_id = models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'biblioteca.libro', 'create', [data])
            print(f"✅ ÉXITO: Libro creado en Odoo con ID: {nuevo_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error en la sincronización: {e}")
    return False

# --- FUNCIONES DE APOYO ---
def es_staff(user):
    return user.is_staff or user.is_superuser

def es_bodegero(user):
    return user.groups.filter(name='Bodegero').exists() or user.is_superuser

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
            if user.is_superuser or user.groups.filter(name='Bibliotecarios').exists():
                return redirect('gestion:panel_bibliotecario')
            elif user.groups.filter(name='Bodegero').exists():
                return redirect('gestion:inventario_bodega')
            else:
                return redirect('gestion:catalogo_lector')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    return render(request, 'login.html')

def salir(request):
    logout(request)
    return redirect('gestion:ingresar')

def index(request):
    actualizar_multas_vencidas()
    return render(request, 'inicio.html')

# --- ROL BIBLIOTECARIO: GESTIÓN DE CONTROL Y CAJA ---
@login_required
@user_passes_test(es_staff)
def panel_bibliotecario(request):
    actualizar_multas_vencidas()
    hoy = timezone.now().date()
    total_deuda = Multa.objects.filter(pagada=False).aggregate(Sum('monto'))['monto__sum'] or 0
    total_recaudado = Multa.objects.filter(pagada=True).aggregate(Sum('monto'))['monto__sum'] or 0
    
    context = {
        'total_libros': Libro.objects.count(),
        'total_autores': Autor.objects.count(),
        'total_lectores': Lector.objects.count(),
        'vencidos_count': Prestamo.objects.filter(devuelto=False, fecha_devolucion_esperada__lt=hoy).count(),
        'total_multas_valor': total_deuda,
        'total_recaudado': total_recaudado,
        'prestamos_recientes': Prestamo.objects.all().order_by('-fecha_prestamo')[:10],
        'morosos_top': Multa.objects.filter(pagada=False).order_by('-monto')[:5]
    }
    return render(request, 'panel_bibliotecario.html', context)

@login_required
@user_passes_test(es_staff)
def lista_prestamos(request):
    prestamos = Prestamo.objects.all().select_related('libro', 'lector')
    query = request.GET.get('q')
    if query:
        prestamos = prestamos.filter(
            Q(libro__titulo__icontains=query) | Q(lector__identificacion__icontains=query)
        ).distinct()
    
    context = {
        'prestamos_activos': prestamos.filter(devuelto=False).order_by('fecha_devolucion_esperada'),
        'prestamos_historicos': prestamos.filter(devuelto=True).order_by('-fecha_prestamo'),
        'now': timezone.now().date(),
        'query': query,
    }
    return render(request, 'lista_prestamos.html', context)

@login_required
@user_passes_test(es_staff)
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
        'prestamo__lector__identificacion', 'prestamo__lector__user__username'
    ).annotate(total_deuda=Sum('monto'), cantidad_libros=Count('id')).order_by('-total_deuda')
    
    return render(request, 'lista_facturas.html', {'facturas': facturas, 'query': query})

# --- ROL BODEGUERO: GESTIÓN FÍSICA E IMPORTACIÓN ---
@login_required
@user_passes_test(es_bodegero)
def inventario_bodega(request):
    estado = request.GET.get('estado')
    query = request.GET.get('q')
    libros = Libro.objects.all().order_by('estante', 'titulo')

    if estado == 'critico':
        libros = libros.filter(copias_disponibles__lte=2)
    elif estado == 'bajo':
        libros = libros.filter(copias_disponibles__gt=2, copias_disponibles__lte=5)
    
    if query:
        libros = libros.filter(Q(titulo__icontains=query) | Q(estante__icontains=query))
    
    return render(request, 'inventario_bodega.html', {
        'libros': libros, 
        'alertas': Libro.objects.filter(copias_disponibles__lte=2),
        'query': query,
        'filtro_actual': estado
    })

@login_required
@user_passes_test(es_bodegero)
def actualizar_stock_bodega(request, libro_id):
    if request.method == 'POST':
        libro = get_object_or_404(Libro, id=libro_id)
        libro.copias_disponibles = request.POST.get('stock')
        libro.estante = request.POST.get('estante')
        libro.save()
        messages.success(request, f"¡{libro.titulo} actualizado con éxito!")
    return redirect('gestion:inventario_bodega')

@login_required
@user_passes_test(es_staff)
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
                anio_entero = timezone.now().year
                try:
                    anio_entero = int(''.join(filter(str.isdigit, info.get('publish_date', '')))[:4])
                except: pass
                
                datos_libro = {
                    'isbn': isbn, 'titulo': info.get('title'),
                    'autores': ", ".join(nombres_autores),
                    'paginas': info.get('number_of_pages', 0),
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
                        defaults={
                            'autor': autor_obj, 'copias_disponibles': 5, 
                            'publicacion': datos_libro['anio'], 'paginas': datos_libro['paginas'],
                            'portada_url': datos_libro['portada']
                        }
                    )
                    
                    if sincronizar_con_odoo(datos_libro['titulo'], isbn):
                        messages.success(request, f"Éxito: {datos_libro['titulo']} guardado en Django y Odoo.")
                    else:
                        messages.warning(request, "Guardado en Django, pero falló el envío a Odoo. Revisa la terminal.")
                    return redirect('gestion:inventario_bodega')
        except Exception as e: 
            print(f"Error API: {e}")
            messages.error(request, "Error al buscar el libro.")
    return render(request, 'buscar_api.html', {'libro': datos_libro, 'isbn': isbn})

# --- MODO LECTOR ---
@login_required
def catalogo_lector(request):
    libros = Libro.objects.filter(copias_disponibles__gt=0).select_related('autor')
    query = request.GET.get('q')
    if query:
        libros = libros.filter(Q(titulo__icontains=query) | Q(autor__nombre__icontains=query))
    return render(request, 'catalogo_lector.html', {'libros': libros, 'query': query})

@login_required
def mis_prestamos(request):
    actualizar_multas_vencidas()
    prestamos = Prestamo.objects.filter(lector__user=request.user, devuelto=False).select_related('libro')
    return render(request, 'mis_prestamos.html', {'prestamos': prestamos})

# --- OTRAS FUNCIONES ---
def lista_libros(request):
    libros = Libro.objects.all().select_related('autor').order_by('titulo')
    return render(request, 'libros.html', {'libros': libros})

def lista_autores(request):
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    return render(request, 'lista_autores.html', {'autores': autores})

def lista_lectores(request):
    lectores = Lector.objects.all().order_by('identificacion')
    return render(request, 'lista_lectores.html', {'lectores': lectores})

@login_required
def nuevo_prestamo(request):
    return render(request, 'nuevo_prestamo.html', {
        'libros': Libro.objects.filter(copias_disponibles__gt=0), 
        'lectores': Lector.objects.all()
    })

@login_required
def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if not prestamo.devuelto:
        actualizar_multas_vencidas()
        Multa.objects.filter(prestamo=prestamo, pagada=False).update(pagada=True)
        prestamo.devuelto = True
        prestamo.save()
        libro = prestamo.libro
        libro.copias_disponibles += 1
        libro.save()
        messages.success(request, f"Libro devuelto con éxito.")
    return redirect('gestion:lista_prestamos')

def registro_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion:ingresar')
    else: form = UsuarioForm()
    return render(request, 'registro_usuario.html', {'form': form})

def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    return render(request, 'detalle_libro.html', {'libro': libro})

def lista_multas(request):
    actualizar_multas_vencidas()
    multas = Multa.objects.filter(pagada=False)
    return render(request, 'lista_multas.html', {'multas': multas})

def registro_lector(request):
    if request.method == 'POST':
        Lector.objects.create(
            identificacion=request.POST.get('identificacion'),
            email=request.POST.get('email'),
            telefono=request.POST.get('telefono')
        )
        return redirect('gestion:lista_lectores')
    return render(request, 'registro_lector.html')

@login_required
def escoger_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    return render(request, 'confirmar_reserva.html', {'libro': libro})