# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Adiciona o campo 'role' e 'telefone' nas telas de edição do Admin
    fieldsets = UserAdmin.fieldsets + (
        ('Informações de Função (Rede União)', {'fields': ('role', 'telefone')}),
    )
    # Mostra a role na listagem de usuários
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']

# Registra o novo painel customizado
admin.site.register(CustomUser, CustomUserAdmin)