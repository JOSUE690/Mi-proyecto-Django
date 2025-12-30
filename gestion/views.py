from django.shortcuts import render, get_object_or_404, redirect
from .models import Libro, Autor, Prestamo, Lector, Multa
from django.db.models import Sum, Q, Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime
from .forms import UsuarioForm

# --- FUNCIÓN CENTRAL: DETECTA VENCIDOS ---
def actualizar_multas_vencidas():
    hoy = timezone.now().date()
    # Buscamos préstamos no devueltos que ya pasaron la fecha
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

def index(request):
    actualizar_multas_vencidas()
    total_libros = Libro.objects.count()
    total_autores = Autor.objects.count()
    total_copias = Libro.objects.aggregate(Sum('copias_disponibles'))['copias_disponibles__sum'] or 0
    # Solo sumamos multas pendientes de pago
    total_multas_valor = Multa.objects.filter(pagada=False).aggregate(Sum('monto'))['monto__sum'] or 0
    
    context = {
        'total_libros': total_libros,
        'total_autores': total_autores,
        'total_copias': total_copias,
        'total_multas_valor': total_multas_valor,
    }
    return render(request, 'inicio.html', context)

def lista_libros(request):
    libros = Libro.objects.all().select_related('autor').order_by('titulo')
    query = request.GET.get('q') 
    if query:
        libros = libros.filter(Q(titulo__icontains=query) | Q(autor__nombre__icontains=query) | Q(autor__apellido__icontains=query)).distinct()
    return render(request, 'libros.html', {'libros': libros, 'query': query})

def detalle_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    return render(request, 'detalle_libro.html', {'libro': libro})
    
def lista_autores(request):
    autores = Autor.objects.all().order_by('nombre').prefetch_related('libro_set')
    return render(request, 'lista_autores.html', {'autores': autores})

def registro_lector(request):
    if request.method == 'POST':
        nombre, identificacion = request.POST.get('nombre'), request.POST.get('identificacion')
        email, telefono = request.POST.get('email'), request.POST.get('telefono')
        try:
            Lector.objects.create(nombre=nombre, identificacion=identificacion, email=email, telefono=telefono)
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

def lista_prestamos(request):
    prestamos = Prestamo.objects.all().select_related('libro', 'lector')
    query = request.GET.get('q')
    if query:
        prestamos = prestamos.filter(Q(libro__titulo__icontains=query) | Q(lector__identificacion__icontains=query)).distinct()
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
        except: pass
    return render(request, 'nuevo_prestamo.html', {'libros': Libro.objects.filter(copias_disponibles__gt=0), 'lectores': Lector.objects.all()})

def devolver_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if not prestamo.devuelto:
        actualizar_multas_vencidas()
        # Marcamos multa como pagada al recibir el libro
        Multa.objects.filter(prestamo=prestamo).update(pagada=True)
        prestamo.devuelto = True
        prestamo.save()
        libro = prestamo.libro
        libro.copias_disponibles += 1
        libro.save()
    return redirect('gestion:prestamos')

def lista_multas(request):
    actualizar_multas_vencidas()
    # Solo mostramos multas de libros NO devueltos y NO pagadas
    if request.user.is_superuser:
        multas = Multa.objects.filter(pagada=False, prestamo__devuelto=False).select_related('prestamo__libro', 'prestamo__lector__user')
    else:
        multas = Multa.objects.filter(prestamo__lector__user=request.user, pagada=False, prestamo__devuelto=False)
    return render(request, 'lista_multas.html', {'multas': multas})