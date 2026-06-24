from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        VENDEDOR = 'VENDEDOR', 'Vendedor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VENDEDOR)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True) # Soft Delete para Usuários

    # --- ADICIONE ESTAS LINHAS AQUI DENTRO ---
    class Meta:
        app_label = 'users'
    # -----------------------------------------
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"