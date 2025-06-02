from django import forms
from .models import Equipamento, CategoriaEquipamento, ManutencaoEquipamento
from clientes.models import Cliente

class EquipamentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de equipamentos
    """
    # Campos personalizados com melhor usabilidade
    nome = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do equipamento'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaEquipamento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    marca = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca do equipamento'}),
        required=False
    )
    
    modelo = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo do equipamento'}),
        required=False
    )
    
    numero_serie = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de série'}),
        required=False
    )
    
    local_instalacao = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Local onde o equipamento está instalado'}),
        required=False
    )
    
    status = forms.ChoiceField(
        choices=Equipamento.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    descricao = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do equipamento'}),
        required=False
    )
    
    especificacoes_tecnicas = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'CPU, RAM, Disco, etc.'}),
        required=False
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais'}),
        required=False
    )
    
    data_aquisicao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    data_instalacao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    data_garantia_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    foto = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    manual = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Equipamento
        exclude = ['codigo', 'data_cadastro', 'ultima_atualizacao', 'slug']

class ManutencaoEquipamentoForm(forms.ModelForm):
    """
    Formulário para registrar manutenções de equipamentos
    """
    tipo = forms.ChoiceField(
        choices=ManutencaoEquipamento.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    descricao = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição detalhada do problema ou manutenção'})
    )
    
    solucao = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Solução aplicada ou procedimento realizado'}),
        required=False
    )
    
    responsavel = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do responsável'})
    )
    
    custo = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        required=False,
        initial=0
    )
    
    class Meta:
        model = ManutencaoEquipamento
        fields = ['tipo', 'descricao', 'solucao', 'responsavel', 'custo']
        widgets = {
            'data': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
        } 