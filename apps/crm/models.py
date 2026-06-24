from django.db import models
from apps.users.models import CustomUser
from django.utils import timezone

class TipoEstrutura(models.TextChoices):
    ZINCO = 'ZINCO', 'Zinco / Metálica'
    FIBROCIMENTO = 'FIBROCIMENTO', 'Fibrocimento'
    SOLO = 'SOLO', 'Solo'
    CERAMICA = 'CERAMICA', 'Cerâmica'
    LAJE = 'LAJE', 'Laje'

class FaseProcesso(models.TextChoices):
    LEAD = 'LEAD', 'Lead'
    PROPOSTA = 'PROPOSTA', 'Proposta Apresentada'
    CONTRATO = 'CONTRATO', 'Contrato Assinado'
    PROJETO_CONCLUIDO = 'CONCLUIDO', 'Projeto Concluído'

class Cliente(models.Model):
    # Relacionamento com o Vendedor (Se deletar o vendedor, o cliente fica sem vendedor, mas NÃO é excluído)
    vendedor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='clientes')

    # Dados Pessoais
    nome = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    # Endereço
    cep = models.CharField(max_length=9)
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    # Dados Técnicos de Negócio
    tipo_estrutura = models.CharField(max_length=20, choices=TipoEstrutura.choices)
    fase_atual = models.CharField(max_length=20, choices=FaseProcesso.choices, default=FaseProcesso.LEAD)
    
    # Histórico e Soft Delete
    is_active = models.BooleanField(default=True) # Permite inativar sem excluir os dados e estatísticas
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nome
    
class ClienteAnexo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='anexos')
    titulo = models.CharField(max_length=100, help_text="Ex: Conta de Energia, Foto do Padrão, Documentos")
    arquivo = models.FileField(upload_to='clientes/anexos/')
    enviado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome}"
    
class Dimensionamento(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='dimensionamento')
    
    # Entradas do vendedor
    consumo_mensal_kwh = models.FloatField(help_text="Consumo médio mensal em kWh")
    irradiacao_local = models.FloatField(help_text="Irradiação solar local (kWh/m²/dia) - Ex: 5.2")
    potencia_painel_wp = models.IntegerField(default=550, help_text="Potência da placa selecionada em Watts (Ex: 550)")
    
    # Resultados calculados (Salvos para histórico)
    potencia_sistema_kwp = models.FloatField()
    qtd_placas = models.IntegerField()
    area_necessaria_m2 = models.FloatField()
    peso_total_kg = models.FloatField()
    
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dimensionamento - {self.cliente.nome} ({self.potencia_sistema_kwp} kWp)"
    
class Proposta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='propostas')
    consumo_kwh = models.FloatField(verbose_name="Consumo Médio Mensal (kWh)")
    hsp = models.FloatField(verbose_name="Horas de Sol Pleno (HSP Local)", default=4.5)
    potencia_painel = models.IntegerField(verbose_name="Potência do Painel (W)", default=550)
    
    # Campos calculados automaticamente antes de salvar
    potencia_usina = models.FloatField(verbose_name="Potência da Usina (kWp)", blank=True, null=True)
    qtd_modulos = models.IntegerField(verbose_name="Quantidade de Módulos", blank=True, null=True)
    valor_investimento = models.DecimalField(verbose_name="Valor Total (R$)", max_digits=10, decimal_places=2, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 🧮 Executa a Engenharia Matemática Solar antes de gravar no banco
        # Formula: kWp = kWh / (30 * HSP * Eficiência)
        eficiencia = 0.80
        self.potencia_usina = round(self.consumo_kwh / (30 * self.hsp * eficiencia), 2)
        
        # Quantidade de módulos = (kWp * 1000) / Potência do Painel
        potencia_w = self.potencia_usina * 1000
        import math
        self.qtd_modulos = math.ceil(potencia_w / self.potencia_painel)
        
        # Simulação de Preço Comercial de Prateleira (Ex: R$ 3.800,00 por kWp instalado)
        preco_por_kwp = 3800.00
        self.valor_investimento = self.potencia_usina * preco_por_kwp
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Proposta {self.id} - {self.cliente.nome} ({self.potencia_usina} kWp)"
    
class Contrato(models.Model):
    proposta = models.OneToOneField(Proposta, on_delete=models.PROTECT, related_name='contrato')
    
    # Informações Jurídicas / Controle
    numero_contrato = models.CharField(max_length=50, unique=True, help_text="Ex: CTR-2026-001")
    data_assinatura = models.DateField(default=timezone.now)
    
    # Campo para integração futura de assinatura eletrônica
    token_assinatura_digital = models.CharField(max_length=255, blank=True, null=True)
    
    arquivo_contrato_pdf = models.FileField(upload_to='contratos/assinados/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrato {self.numero_contrato} - {self.proposta.cliente.nome}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Captura o cliente através do relacionamento e avança a fase dele
            cliente = self.proposta.cliente
            cliente.fase_atual = FaseProcesso.CONTRATO
            cliente.save()
            
            # REMOVIDA A LINHA DO Proposta.StatusProposta.ACEITA PARA EVITAR ERROS