from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User # <--- ¡Nueva importación crucial!

# ----------------------------------------------------
# 1. MODELO AUTOR
# ----------------------------------------------------
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

# ----------------------------------------------------
# 2. MODELO LIBRO
# ----------------------------------------------------
class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    publicacion = models.IntegerField(null=True, blank=True)
    copias_disponibles = models.PositiveIntegerField(default=0) 

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name_plural = "Libros"

# ----------------------------------------------------
# 3. MODELO LECTOR (ACTUALIZADO PARA AUTENTICACIÓN)
# ----------------------------------------------------
class Lector(models.Model):
    # Clave primaria vinculada al usuario de Django Auth (user es el nombre estándar)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) 
    
    # Quitamos 'nombre' y 'email' porque vienen del modelo User.
    identificacion = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True) 

    def __str__(self):
        return f"{self.user.username} ({self.identificacion})"

    class Meta:
        verbose_name = "Usuario"          
        verbose_name_plural = "Usuarios"

# ----------------------------------------------------
# 4. MODELO PRÉSTAMO
# ----------------------------------------------------
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