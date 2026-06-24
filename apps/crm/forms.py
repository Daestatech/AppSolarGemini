from django import forms
from apps.crm.models import Cliente, ClienteAnexo
from django.contrib.auth import get_user_model

User = get_user_model()

class ClienteForm(forms.ModelForm):
    # ALTERADO DE ModelFormChoiceField PARA ModelChoiceField:
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False, 
        label="Consultor Responsável",
        widget=forms.Select(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50'})
    )

    class Meta:
        model = Cliente
        # Campos que o vendedor preencherá na rua
        fields = [
            'nome', 'cpf_cnpj', 'telefone', 'email',
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado',
            'tipo_estrutura', 'fase_atual'
        ]
        widgets = {
            'tipo_estrutura': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'fase_atual': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
        }