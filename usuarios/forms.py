from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Perfil, PermissaoMenu, Menu, GrupoPermissao, Permissao

class UsuarioForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Obrigatório. Informe um e-mail válido.')
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class PerfilForm(forms.ModelForm):
    tipo = forms.ChoiceField(
        choices=Perfil.TIPO_PERFIL_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    grupos_permissao = forms.ModelMultipleChoiceField(
        queryset=GrupoPermissao.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Selecione os grupos de permissão'
        })
    )
    
    class Meta:
        model = Perfil
        fields = ('tipo', 'grupos_permissao')
    
    def __init__(self, *args, **kwargs):
        super(PerfilForm, self).__init__(*args, **kwargs)
        self.fields['tipo'].widget.attrs['class'] = 'form-check-input'

class PermissaoMenuFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, perfil=None, **kwargs):
        self.perfil = perfil
        super(PermissaoMenuFormSet, self).__init__(*args, **kwargs)
        
        # Define a queryset padrão se não houver perfil
        if not self.queryset.exists() and self.perfil:
            menus = Menu.objects.filter(ativo=True)
            permissoes = []
            for menu in menus:
                permissao, criado = PermissaoMenu.objects.get_or_create(
                    perfil=self.perfil,
                    menu=menu
                )
                permissoes.append(permissao)
            self.queryset = PermissaoMenu.objects.filter(id__in=[p.id for p in permissoes])

class PermissaoMenuForm(forms.ModelForm):
    # Definimos tipo_permissao como um alias para o campo real nivel_acesso
    tipo_permissao = forms.ChoiceField(
        choices=PermissaoMenu.PERMISSAO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        initial='nenhum'
    )
    
    class Meta:
        model = PermissaoMenu
        fields = ('menu',)  # nivel_acesso será tratado via tipo_permissao
        widgets = {
            'menu': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(PermissaoMenuForm, self).__init__(*args, **kwargs)
        # Desabilita a edição do menu
        if self.instance and self.instance.pk:
            self.fields['menu'].disabled = True
            self.fields['menu'].widget = forms.HiddenInput()
            self.initial['menu'] = self.instance.menu
            # Inicializa tipo_permissao com o valor de nivel_acesso
            if hasattr(self.instance, 'nivel_acesso'):
                self.initial['tipo_permissao'] = self.instance.nivel_acesso

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Transfere o valor do campo de formulário tipo_permissao para o campo do modelo nivel_acesso
        if 'tipo_permissao' in self.cleaned_data:
            instance.nivel_acesso = self.cleaned_data['tipo_permissao']
        if commit:
            instance.save()
        return instance

PermissaoMenuFormSet = forms.modelformset_factory(
    PermissaoMenu,
    form=PermissaoMenuForm,
    formset=PermissaoMenuFormSet,
    extra=0,
    can_delete=False
)

class UsuarioEditForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    is_active = forms.BooleanField(required=False, label="Ativo")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super(UsuarioEditForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'

class GrupoPermissaoForm(forms.ModelForm):
    class Meta:
        model = GrupoPermissao
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PermissaoForm(forms.ModelForm):
    visualizar = forms.BooleanField(required=False, initial=False)
    criar = forms.BooleanField(required=False, initial=False)
    editar = forms.BooleanField(required=False, initial=False)
    excluir = forms.BooleanField(required=False, initial=False)

    class Meta:
        model = Permissao
        fields = ['menu']
        widgets = {
            'menu': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar o campo menu para mostrar apenas menus ativos
        self.fields['menu'].queryset = Menu.objects.filter(ativo=True)
        self.fields['menu'].empty_label = None  # Remove a opção vazia
        
        if self.instance.pk:
            self.fields['visualizar'].initial = self.instance.acoes.get('visualizar', False)
            self.fields['criar'].initial = self.instance.acoes.get('criar', False)
            self.fields['editar'].initial = self.instance.acoes.get('editar', False)
            self.fields['excluir'].initial = self.instance.acoes.get('excluir', False)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.acoes = {
            'visualizar': self.cleaned_data['visualizar'],
            'criar': self.cleaned_data['criar'],
            'editar': self.cleaned_data['editar'],
            'excluir': self.cleaned_data['excluir'],
        }
        if commit:
            instance.save()
        return instance

class PerfilPermissoesForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['grupos_permissao']
        widgets = {
            'grupos_permissao': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Selecione os grupos de permissão'
            })
        }

PermissaoFormSet = forms.modelformset_factory(
    Permissao,
    form=PermissaoForm,
    extra=0,
    can_delete=True
)

class AlterarSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )
    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if nova_senha and confirmar_senha:
            if nova_senha != confirmar_senha:
                raise forms.ValidationError('As senhas não coincidem.')
        return cleaned_data 