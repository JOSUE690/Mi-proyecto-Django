from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Lector
from django.contrib.auth.models import User 

# Heredamos de UserCreationForm, que ya maneja username, password, y password_confirmation.
class UsuarioForm(UserCreationForm):
    
    # Campos adicionales que NO están en el modelo User, pero sí en el modelo Lector.
    identificacion = forms.CharField(max_length=20, required=True)
    telefono = forms.CharField(max_length=15, required=False)
    
    class Meta(UserCreationForm.Meta):
        # Campos a mostrar en el formulario, incluyendo email y los campos de Lector.
        fields = ('username', 'email', 'identificacion', 'telefono') + UserCreationForm.Meta.fields[3:]
        
    def save(self, commit=True):
        """Guarda primero el User de Django y luego el Lector vinculado."""
        # 1. Guardar el objeto User (con la contraseña hasheada)
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()

        # 2. Crear el objeto Lector (el perfil) y vincularlo al nuevo User
        identificacion = self.cleaned_data.get('identificacion')
        telefono = self.cleaned_data.get('telefono')
        
        Lector.objects.create(
            user=user, # Usa 'user' para la vinculación
            identificacion=identificacion,
            telefono=telefono,
        )
        return user