from django.db import models
from django.utils import timezone # Necesario para la fecha de préstamo

# ----------------------------------------------------
# 1. MODELO AUTOR (Pequeñas mejoras para detalle)
# ----------------------------------------------------
class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    # Campos adicionales para enriquecer el detalle
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.CharField(max_length=50, blank=True)

    # Método para obtener el nombre completo (usando @property para acceso más limpio)
    @property
    def nombre_completo(self):
        # Esto imita la "concatenación" de SQL que mencionaste
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return self.nombre_completo

# ----------------------------------------------------
# 2. MODELO LIBRO (Ajustado a PositiveIntegerField)
# ----------------------------------------------------
class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    # Una clave foránea que enlaza cada libro a un autor
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    # Campo para registrar el año de publicación (opcional)
    publicacion = models.IntegerField(null=True, blank=True)
    
    # Usamos PositiveIntegerField para asegurar que las copias no sean negativas
    copias_disponibles = models.PositiveIntegerField(default=0) 

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name_plural = "Libros"

# ----------------------------------------------------
# 3. MODELO LECTOR (Nuevo)
# ----------------------------------------------------
class Lector(models.Model):
    # Nombre completo de la persona
    nombre = models.CharField(max_length=150)
    # Identificador único (ej: DNI, ID de estudiante)
    identificacion = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        # Muestra el nombre y la identificación del lector
        return f"{self.nombre} ({self.identificacion})"

    class Meta:
        verbose_name_plural = "Lectores"

# ----------------------------------------------------
# 4. MODELO PRÉSTAMO (Nuevo)
# ----------------------------------------------------
class Prestamo(models.Model):
    # Relación con el libro que se prestó
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    
    # Relación con la persona a la que se prestó
    lector = models.ForeignKey(Lector, on_delete=models.CASCADE)
    
    # Fechas de la transacción
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_devolucion_esperada = models.DateField()
    
    # Estado del préstamo: True=Devuelto, False=Activo/Pendiente
    devuelto = models.BooleanField(default=False) 

    def __str__(self):
        return f"Préstamo de {self.libro.titulo} a {self.lector.nombre}"

    class Meta:
        verbose_name_plural = "Préstamos"
        # Ordenamos los préstamos: primero los no devueltos, luego por fecha de préstamo descendente
        ordering = ['devuelto', '-fecha_prestamo']