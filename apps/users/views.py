# apps/users/views.py
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib.messages.views import SuccessMessageMixin
from apps.users.mixins import SolarAccessControlMixin
from apps.users.forms import VendedorCreationForm

class UsuarioCreateView(SolarAccessControlMixin, SuccessMessageMixin, CreateView):
    form_class = VendedorCreationForm
    template_name = 'users/usuario_form.html'
    success_url = reverse_lazy('crm:cliente_list')
    success_message = "Novo consultor cadastrado com sucesso no sistema!"

    def dispatch(self, request, *args, **kwargs):
        # 🛡️ TRAVA DE SEGURANÇA MESTRE: Se não for ADMIN, barra na entrada com erro 403
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)