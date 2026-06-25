from django import forms
from django.db import models
from apps.crm.models import Cliente, ClienteAnexo, Proposta, Contrato
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
            'tipo_estrutura', 'fase_atual', 'consumo_kwh', 'producao_estimada_kwh', 'potencia_painel', 'marca_inversor'
        ]
        # apps/crm/forms.py
        widgets = {
            'tipo_estrutura': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'fase_atual': forms.Select(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            
            # ⚡ ADICIONE ESSAS LINHAS AQUI PARA OS NOVOS INPUTS FICAREM ESTILIZADOS:
            'consumo_kwh': forms.NumberInput(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500', 'placeholder': 'Ex: 1000'}),
            'producao_estimada_kwh': forms.NumberInput(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500', 'placeholder': 'Ex: 1500'}),
            'potencia_painel': forms.NumberInput(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500', 'placeholder': 'Ex: 550'}),
            'marca_inversor': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg border-gray-300 bg-white text-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500', 'placeholder': 'Ex: Growatt, Deye...'}),
        }

class PropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ['consumo_kwh', 'hsp', 'potencia_painel']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tailwind nos inputs
        tailwind_class = 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50'
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = tailwind_class

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['numero_contrato', 'data_assinatura', 'arquivo_contrato_pdf']
        widgets = {
            'data_assinatura': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_class = 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50'
        for field_name, field in self.fields.items():
            if field_name != 'arquivo_contrato_pdf':
                field.widget.attrs['class'] = tailwind_class

# Ao final de apps/crm/forms.py

class SimuladorLivreForm(forms.Form):
    tipo_estrutura = forms.ChoiceField(
        choices=[
            ('CERAMICA', 'Telhado Cerâmico'),
            ('METALICO', 'Telhado Metálico'),
            ('LAJE', 'Laje'),
            ('SOLO', 'Solo'),
        ],
        label="Tipo de Estrutura",
        widget=forms.Select(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white'})
    )
    consumo_kwh = forms.IntegerField(
        label="Consumo Atual (kWh)",
        widget=forms.NumberInput(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50', 'placeholder': 'Ex: 1000'})
    )
    producao_estimada_kwh = forms.IntegerField(
        label="Produção Desejada (kWh)",
        widget=forms.NumberInput(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50', 'placeholder': 'Ex: 1500'})
    )
    potencia_painel = forms.IntegerField(
        label="Potência do Painel (Watts)",
        initial=550,
        widget=forms.NumberInput(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50', 'placeholder': 'Ex: 550'})
    )
    marca_inversor = forms.CharField(
        label="Marca do Inversor sugerido",
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full p-3.5 rounded-lg border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-gray-50', 'placeholder': 'Ex: Growatt, Deye...'})
    )