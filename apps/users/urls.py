# apps/users/urls.py
from django.urls import path
from .views import UsuarioCreateView

app_name = 'users'

urlpatterns = [
    path('usuarios/novo/', UsuarioCreateView.as_view(), name='usuario_create'),
]