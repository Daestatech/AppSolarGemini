from django.views.generic import ListView, DetailView, UpdateView, CreateView
from apps.crm.models import Cliente, Proposta, Contrato, ClienteAnexo
from apps.crm.forms import ClienteForm, PropostaForm, ContratoForm, ClienteForm, SimuladorLivreForm
from apps.users.mixins import SolarAccessControlMixin
from apps.users.models import CustomUser
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.template.loader import get_template, render_to_string
from weasyprint import HTML
from xhtml2pdf import pisa
from django.contrib import messages
from django.urls import reverse_lazy
import math

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

# apps/crm/views.py

class ClienteUpdateView(SolarAccessControlMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'crm/cliente_form.html'
    success_url = reverse_lazy('crm:cliente_list')

    def form_valid(self, form):
        # 1. Se quem está editando for o ADMINISTRADOR:
        if self.request.user.role == 'ADMIN':
            # Pegamos o vendedor selecionado no dropdown do formulário
            novo_vendedor = form.cleaned_data.get('vendedor')
            if novo_vendedor:
                form.instance.vendedor = novo_vendedor
        else:
            # 2. Se for um vendedor comum editando, blindamos para ele NÃO alterar o dono original
            form.instance.vendedor = self.get_object().vendedor

        # Executa o salvamento real no banco
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
    
class PropostaCreateView(SolarAccessControlMixin, CreateView):
    model = Proposta
    form_class = PropostaForm
    template_name = 'crm/proposta_form.html'

    def form_valid(self, form):
        # Vincula a proposta ao cliente passado na URL de forma dinâmica
        cliente_pk = self.kwargs.get('pk')
        form.instance.cliente = get_object_or_404(Cliente, pk=cliente_pk)
        return super().form_valid(form)

    def get_success_url(self):
        # Após calcular, redireciona de volta para a ficha do cliente
        return reverse_lazy('crm:cliente_detail', kwargs={'pk': self.kwargs.get('pk')})
    
class ContratoCreateView(SolarAccessControlMixin, CreateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'crm/contrato_form.html'

    def form_valid(self, form):
        # Vincula o contrato à proposta vinda da URL
        proposta_pk = self.kwargs.get('proposta_pk')
        form.instance.proposta = get_object_or_404(Proposta, pk=proposta_pk)
        return super().form_valid(form)

    def get_success_url(self):
        # Após salvar, busca o cliente para voltar à ficha dele
        proposta = get_object_or_404(Proposta, pk=self.kwargs.get('proposta_pk'))
        return reverse_lazy('crm:cliente_detail', kwargs={'pk': proposta.cliente.pk})
    
def proposta_pdf_view(request, *args, **kwargs):
    """Gera o PDF da Proposta Comercial de forma flexível e robusta"""
    # Tenta capturar o ID da URL se ele vier como 'cliente_pk', 'proposta_pk' ou simplesmente 'pk'
    pk_identificado = kwargs.get('cliente_pk') or kwargs.get('proposta_pk') or kwargs.get('pk')
    
    if not pk_identificado:
        return HttpResponse('ID do registro não fornecido.', status=400)
        
    # Busca o cliente diretamente no banco (já que unificamos os dados nele)
    cliente = get_object_or_404(Cliente, pk=pk_identificado)
    
    context = {
        'cliente': cliente,
        'data_emissao': cliente.criado_em,
        'proposta': cliente, # Mantém compatibilidade com as tags {{ proposta.campo }} do HTML
    }
    
    html_string = render_to_string('crm/pdf/proposta_comercial.html', context)
    
    # Se você estiver rodando local no Windows e o WeasyPrint der erro de DLL, 
    # certifique-se de usar a biblioteca ativa no ambiente correspondente
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    nome_arquivo = f"Proposta_Solar_{cliente.nome.replace(' ', '_')}.pdf"
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    return response


def contrato_pdf_view(request, contrato_pk):
    """Gera o PDF do Contrato de Prestação de Serviços"""
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    proposta = contrato.proposta
    cliente = proposta.cliente
    
    context = {
        'contrato': contrato,
        'proposta': proposta,
        'cliente': cliente,
    }
    
    html_string = render_to_string('crm/pdf/contrato_servico.html', context)
    
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Contrato_Solar_{cliente.nome.replace(" ", "_")}.pdf"'
    return response

class SimuladorLivreView(SolarAccessControlMixin, View):
    template_name = 'crm/simulador_livre.html'

    def get(self, request):
        form = SimuladorLivreForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SimuladorLivreForm(request.POST)
        context = {'form': form}

        if form.is_valid():
            # Captura os dados enviados pelo formulário
            consumo = form.cleaned_data['consumo_kwh']
            producao = form.cleaned_data['producao_estimada_kwh']
            potencia_painel = form.cleaned_data['potencia_painel']
            marca_inversor = form.cleaned_data['marca_inversor']
            tipo_estrutura = form.get_choice_display('tipo_estrutura') if hasattr(form, 'get_choice_display') else form.cleaned_data['tipo_estrutura']

            # Executa a mesma lógica de Engenharia Solar do modelo
            if producao > 0 and potencia_painel > 0:
                potencia_usina = round(float(producao) / (30 * 4.5 * 0.8), 2)
                potencia_usina_watts = potencia_usina * 1000
                qtd_modulos = math.ceil(potencia_usina_watts / potencia_painel)
                valor_investimento = round(potencia_usina * 3200, 2)
            else:
                potencia_usina = 0.00
                qtd_modulos = 0
                valor_investimento = 0.00

            # Injeta os resultados direto no contexto da página
            context['resultado'] = {
                'consumo': consumo,
                'producao': producao,
                'potencia_usina': potencia_usina,
                'qtd_modulos': qtd_modulos,
                'valor_investimento': valor_investimento,
                'marca_inversor': marca_inversor,
                'tipo_estrutura': tipo_estrutura,
            }

        return render(request, self.template_name, context)