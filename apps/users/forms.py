# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class VendedorCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", required=True)
    last_name = forms.CharField(label="Sobrenome", required=True)
    email = forms.EmailField(label="E-mail", required=True)
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'role', 'telefone')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos as classes elegantes do Tailwind em todos os campos automaticamente
        tailwind_class = 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50'
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = tailwind_class