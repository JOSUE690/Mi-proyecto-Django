# gestion/models.py
from django.db import models

class Autor(models.Model):
    # Campo para almacenar el nombre del autor
    nombre = models.CharField(max_length=100)
    # Campo para almacenar el apellido del autor
    apellido = models.CharField(max_length=100)
    
    def nombre_completo(self):
        # Esto imita la "concatenación" de SQL que mencionaste
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return self.nombre_completo()

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    # Una clave foránea que enlaza cada libro a un autor
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)
    # Campo para registrar el año de publicación (opcional)
    publicacion = models.IntegerField(null=True, blank=True)
    # Campo que podría usarse para funciones de agregación (e.g., AVG, MAX)
    copias_disponibles = models.IntegerField(default=1)

    def __str__(self):
        return self.titulo