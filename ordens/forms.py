from django import forms
from django.forms import inlineformset_factory
from .models import OrdemServico, ProdutoUtilizado
from produtos.models import Produto
from decimal import Decimal

class ProdutoUtilizadoForm(forms.ModelForm):
    # Usar um campo de busca para selecionar o produto
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.filter(ativo=True, estoque_atual__gt=0), 
        widget=forms.Select(attrs={'class': 'form-select produto-select'}),
        label="Peça/Produto do Estoque",
        required=True,  # Garantir que seja obrigatório
        error_messages={'required': 'É necessário selecionar um produto'}
    )
    quantidade = forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'}),
        label="Quantidade",
        required=True,
        error_messages={'required': 'A quantidade é obrigatória'}
    )

    class Meta:
        model = ProdutoUtilizado
        fields = ['produto', 'quantidade']
        # Excluir 'ordem_servico' e 'preco_unitario' pois serão definidos na view/modelo
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar o texto de exibição dos produtos para mostrar informações de estoque
        produtos = self.fields['produto'].queryset
        choices = [(p.id, f"{p.codigo} - {p.nome} (Estoque: {p.estoque_atual} {p.unidade.sigla})") for p in produtos]
        self.fields['produto'].choices = [('', '---------')] + choices
        
    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        
        # Verificar se o produto foi selecionado
        if not produto:
            self.add_error('produto', 'É necessário selecionar um produto válido')
            
        return cleaned_data

# Criar o Inline Formset
# extra=1 significa que sempre mostrará 1 linha extra em branco para adicionar novo item
ProdutoUtilizadoFormSet = inlineformset_factory(
    OrdemServico, 
    ProdutoUtilizado, 
    form=ProdutoUtilizadoForm, 
    extra=1, 
    can_delete=True, # Permitir marcar para exclusão
    can_delete_extra=True,
    validate_min=False,  # Não exigir um número mínimo de formulários
)

# Estender o formset para adicionar validação extra
class ProdutoUtilizadoFormSetCustom(ProdutoUtilizadoFormSet):
    def clean(self):
        """
        Validação adicional para o formset de produtos utilizados
        """
        super().clean()
        
        # Se não há formulários não excluídos, o formset é válido (não obrigatório ter produtos)
        if not any(form for form in self.forms if not (self._should_delete_form(form) or not form.has_changed())):
            return
            
        for form in self.forms:
            # Ignorar formulários marcados para exclusão ou vazios
            if self._should_delete_form(form) or not form.has_changed():
                continue
            
            # Verificar se há instâncias existentes sem produto
            if form.instance and form.instance.pk and not hasattr(form.instance, 'produto_id'):
                # Marcar para exclusão formulários com instâncias inválidas
                form._marked_for_deletion = True
                continue
                
            # Verificar se o produto foi selecionado
            if 'produto' not in form.cleaned_data or form.cleaned_data['produto'] is None:
                form.add_error('produto', 'É necessário selecionar um produto')
                continue  # Continuar com a validação em vez de levantar erro
                
            # Verificar se quantidade foi preenchida
            if 'quantidade' not in form.cleaned_data or form.cleaned_data['quantidade'] is None:
                form.add_error('quantidade', 'A quantidade é obrigatória')
                continue  # Continuar com a validação
        
        # Verificar se existem erros de validação
        errors = []
        for form in self.forms:
            if not self._should_delete_form(form) and form.errors:
                errors.append(form.errors)
        
        if errors:
            # Apenas levantar um erro se ainda houver problemas não resolvidos
            raise forms.ValidationError('Existem problemas com os produtos na ordem de serviço')
            
    def save(self, commit=True):
        """
        Sobrescrever o método save para excluir registros inválidos
        """
        instances = super().save(commit=False)
        
        # Filtrar instâncias válidas
        valid_instances = []
        for instance in instances:
            # Verificar se a instância tem produto_id
            if hasattr(instance, 'produto_id') and instance.produto_id is not None:
                valid_instances.append(instance)
            elif instance.pk:  # Se é um registro existente sem produto_id, excluí-lo
                instance.delete()
        
        if commit:
            for instance in valid_instances:
                instance.save()
            self.save_m2m()
            
        return valid_instances

# Formulário principal da OS (pode já existir ou ser criado)
class OrdemServicoForm(forms.ModelForm):
    # Definir campos de valores com valores padrão para evitar campos vazios
    valor_servico = forms.DecimalField(
        min_value=0, 
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
        initial=0,
        required=False,  # Define o campo como não obrigatório
        label="Valor do Serviço (R$)"
    )
    valor_deslocamento = forms.DecimalField(
        min_value=0, 
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
        initial=0,
        required=False,  # Define o campo como não obrigatório
        label="Valor do Deslocamento (R$)"
    )
    desconto = forms.DecimalField(
        min_value=0, 
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
        initial=0,
        required=False,  # Define o campo como não obrigatório
        label="Desconto (R$)"
    )
    
    class Meta:
        model = OrdemServico
        fields = ['cliente', 'categoria', 'tecnico', 'descricao', 'solucao', 
                  'data_agendamento', 'status', 'prioridade', 'endereco', 
                  'numero_endereco', 'complemento', 'bairro', 'cidade', 'estado', 'cep', 
                  'valor_servico', 'valor_deslocamento', 'desconto', 
                  'observacoes_internas', 'ativa'] 
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Garantir que valores numéricos não estejam vazios
        for field in ['valor_servico', 'valor_deslocamento', 'desconto']:
            # Se o campo estiver ausente ou for None ou estiver vazio, defina como 0
            if field not in cleaned_data or cleaned_data[field] is None or cleaned_data[field] == '':
                cleaned_data[field] = Decimal('0')
        
        return cleaned_data 