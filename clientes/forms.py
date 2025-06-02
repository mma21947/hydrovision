import re
from django import forms
from .models import Empresa, ContratoEmpresa

def validar_cnpj(cnpj):
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False
    
    # Calcula o primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso = peso - 1 if peso > 2 else 9
    
    digito1 = 11 - (soma % 11)
    if digito1 > 9:
        digito1 = 0
    
    # Verifica o primeiro dígito verificador
    if int(cnpj[12]) != digito1:
        return False
    
    # Calcula o segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso = peso - 1 if peso > 2 else 9
    
    digito2 = 11 - (soma % 11)
    if digito2 > 9:
        digito2 = 0
    
    # Verifica o segundo dígito verificador
    if int(cnpj[13]) != digito2:
        return False
    
    return True

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'inscricao_municipal',
                 'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
                 'telefone', 'email', 'observacoes', 'logo', 'ativo']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.FileInput()
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if not validar_cnpj(cnpj):
            raise forms.ValidationError('CNPJ inválido')
        
        # Verifica se já existe uma empresa com este CNPJ
        instance = getattr(self, 'instance', None)
        if Empresa.objects.filter(cnpj=cnpj).exclude(id=instance.id if instance else None).exists():
            raise forms.ValidationError('Já existe uma empresa cadastrada com este CNPJ')
        
        return cnpj

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            cep = re.sub(r'[^0-9]', '', cep)
            if len(cep) != 8:
                raise forms.ValidationError('CEP deve conter 8 dígitos')
        return cep

class ContratoEmpresaForm(forms.ModelForm):
    class Meta:
        model = ContratoEmpresa
        fields = [
            'numero',
            'data_inicio',
            'data_fim',
            'valor',
            'status',
            'arquivo',
            'observacoes'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'arquivo': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'})
        } 