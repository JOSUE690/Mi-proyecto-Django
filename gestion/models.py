from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.CharField(max_length=50, blank=True)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return self.nombre_completo

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    publicacion = models.IntegerField(null=True, blank=True)
    copias_disponibles = models.PositiveIntegerField(default=0)
    paginas = models.PositiveIntegerField(default=0, blank=True, null=True) 
    portada_url = models.URLField(max_length=500, blank=True, null=True)
    
    # --- CAMPO PARA EL VALOR DEL LIBRO ---
    # Usamos DecimalField para manejar dinero con precisión
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor del Libro")

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name_plural = "Libros"

class Lector(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) 
    identificacion = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True) 

    def __str__(self):
        return f"{self.user.username} ({self.identificacion})"

    class Meta:
        verbose_name = "Usuario"          
        verbose_name_plural = "Usuarios"

class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    lector = models.ForeignKey(Lector, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_devolucion_esperada = models.DateField()
    devuelto = models.BooleanField(default=False) 

    def __str__(self):
        return f"Préstamo de {self.libro.titulo} a {self.lector.user.username}"

    class Meta:
        verbose_name_plural = "Préstamos"
        ordering = ['devuelto', '-fecha_prestamo']

class Multa(models.Model):
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=6, decimal_places=2, default=2.00)
    pagada = models.BooleanField(default=False)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Multa de {self.prestamo.lector.user.username} - ${self.monto}"

    class Meta:
        verbose_name_plural = "Multas"