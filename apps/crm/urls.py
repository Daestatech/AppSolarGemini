# apps/crm/urls.py
from django.urls import path
from .views import ClienteCreateView, ClienteListView, ClienteDetailView, AdicionarAnexoView, ClienteUpdateView

app_name = 'crm'

urlpatterns = [
    path('cliente/novo/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('cliente/<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),
    path('cliente/<int:pk>/adicionar-anexo/', AdicionarAnexoView.as_view(), name='adicionar_anexo'),
    # No seu urlpatterns do apps/crm/urls.py, adicione:
path('cliente/<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
]