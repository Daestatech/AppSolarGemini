from django.views.generic import ListView, DetailView, UpdateView, CreateView
from apps.crm.models import Cliente, Proposta, Contrato, ClienteAnexo
from apps.crm.forms import ClienteForm
from apps.users.mixins import SolarAccessControlMixin
from apps.users.models import CustomUser
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.urls import reverse_lazy

class ClienteCreateView(SolarAccessControlMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'crm/cliente_form.html'
    
    # MUDE AQUI: Usar reverse_lazy apontando para a rota de sucesso
    success_url = reverse_lazy('crm:cliente_list') 
    
    def form_valid(self, form):
        # Se quem está logado é ADMIN e escolheu um vendedor no dropdown, mantém a escolha.
        # Caso contrário (se for vendedor), força o dono a ser o usuário logado.
        if self.request.user.role == 'ADMIN' and form.cleaned_data.get('vendedor'):
            pass 
        else:
            form.instance.vendedor = self.request.user
            
        return super().form_valid(form)
        
        arquivos = self.request.FILES.getlist('arquivos_anexos')
        for arquivo in arquivos:
            ClienteAnexo.objects.create(
                cliente=self.object,
                titulo=arquivo.name,
                arquivo=arquivo
            )
        return response

    # Remova ou comente o método get_success_url antigo para não dar conflito!


# apps/crm/views.py

class ClienteListView(SolarAccessControlMixin, ListView):
    model = Cliente
    template_name = 'crm/cliente_list.html'
    context_object_name = 'clientes'

    def get_queryset(self):
        # Pega a consulta padrão (todos os clientes)
        queryset = super().get_queryset()
        
        # Se o usuário logado NÃO for administrador (for um vendedor), filtra pela carteira dele
        if self.request.user.role != 'ADMIN':
            queryset = queryset.filter(vendedor=self.request.user)
            
        return queryset

# O get_queryset automático do Mixin filtra os clientes aqui
class ClienteDetailView(SolarAccessControlMixin, DetailView):
    model = Cliente
    template_name = 'crm/cliente_detail.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Busca todos os anexos vinculados a este cliente específico
        context['anexos'] = self.object.anexos.all() 
        return context
    # Se um vendedor tentar acessar o ID de um cliente de outro vendedor pela URL,
    # o get_queryset filtrado disparará automaticamente um erro 404.

class AdicionarAnexoView(SolarAccessControlMixin, View):
    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        arquivos = request.FILES.getlist('arquivos_anexos')
        
        for arquivo in arquivos:
            ClienteAnexo.objects.create(
                cliente=cliente,
                titulo=arquivo.name,
                arquivo=arquivo
            )
        
        # Redireciona de volta para a página de detalhes do próprio cliente
        return redirect('crm:cliente_detail', pk=pk)

class ClienteUpdateView(SolarAccessControlMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'crm/cliente_form.html'
    success_url = reverse_lazy('crm:cliente_list')

    def form_valid(self, form):
        # Na edição, se for um vendedor mexendo, garantimos que ele não altere o dono original
        if self.request.user.role != 'ADMIN':
            form.instance.vendedor = self.get_object().vendedor
            
        return super().form_valid(form)

class TransferirClienteView(UserPassesTestMixin, View):
    """View para o Admin transferir um cliente de carteira"""
    def test_func(self):
        # Garante que apenas ADMIN pode acessar essa rota
        return self.request.user.is_authenticated and self.request.user.role == CustomUser.Role.ADMIN
    
    def post(self, request, cliente_id):
        cliente = get_object_or_404(Cliente, id=cliente_id)
        novo_vendedor_id = request.POST.get('vendedor_id')
        if novo_vendedor_id:
            novo_vendedor = get_object_or_404(CustomUser, id=novo_vendedor_id,
            role=CustomUser.Role.VENDEDOR)
            cliente.vendedor = novo_vendedor
            cliente.save()
        return redirect('crm:cliente_detail', pk=cliente.id)

class GerarPropostaPDFView(SolarAccessControlMixin, DetailView):
    model = Proposta

    def get(self, request, *args, **kwargs):
        proposta = self.get_object()
        cliente = proposta.cliente
        dimensionamento = proposta.dimensionamento

        # Contexto que vai para o documento HTML
        context = {
            'proposta': proposta,
            'cliente': cliente,
            'dimensionamento': dimensionamento,
            'vendedor': cliente.vendedor
        }

        # Renderiza o template HTML específico para o PDF
        template = get_template('crm/pdf/proposta_comercial.html')
        html_content = template.render(context)

        # Cria a resposta HTTP configurada para PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Proposta_Solar_{cliente.nome.replace(" ", "_")}.pdf"'

        # Converte o HTML em PDF real
        pisa_status = pisa.CreatePDF(html_content, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Erro ao gerar o PDF da Proposta', status=500)
            
        return response
    
class RegistrarContratoView(SolarAccessControlMixin, CreateView):
    model = Contrato
    fields = ['numero_contrato', 'data_assinatura', 'arquivo_contrato_pdf']
    template_name = 'crm/contrato_form.html'

    def form_valid(self, form):
        # Recupera a proposta com base no ID enviado pela URL
        proposta_id = self.kwargs.get('proposta_id')
        proposta = get_object_or_404(Proposta, id=proposta_id)
        
        # Vincula a proposta ao contrato antes de salvar
        form.instance.proposta = proposta
        
        response = super().form_valid(form)
        
        # Envia uma mensagem de sucesso para a tela do vendedor
        messages.success(self.request, f"🎉 Parabéns! Contrato da usina de {proposta.cliente.nome} registrado com sucesso!")
        return response

    def get_success_url(self):
        return redirect('crm:cliente_list')