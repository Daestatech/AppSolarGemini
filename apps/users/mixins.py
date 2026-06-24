from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from apps.users.models import CustomUser

class SolarAccessControlMixin(LoginRequiredMixin):
    """
    Mixin para garantir que usuários estejam logados e restrinja
    o QuerySet com base na role (ADMIN ou VENDEDOR).
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Garante que só traz registros ativos por padrão nas views operacionais
        if hasattr(queryset.model, 'is_active'):
            # Admin pode opcionalmente ver inativos, vendedor vê apenas ativos
            if user.role != CustomUser.Role.ADMIN:
                queryset = queryset.filter(is_active=True)
        
        # Regra de isolamento do Vendedor
        if user.role == CustomUser.Role.VENDEDOR:
            return queryset.filter(vendedor=user)
        
        # Admin vê tudo
        elif user.role == CustomUser.Role.ADMIN:
            return queryset
        
        return queryset.none()