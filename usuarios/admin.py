from django.contrib import admin
from .models import Perfil, Menu, PermissaoMenu

class PermissaoMenuInline(admin.TabularInline):
    model = PermissaoMenu
    extra = 0

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'display_data_criacao', 'display_ultima_atualizacao')
    list_filter = ('tipo',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    inlines = [PermissaoMenuInline]
    
    def display_data_criacao(self, obj):
        return obj.data_criacao
    display_data_criacao.short_description = "Data de Criação"
    
    def display_ultima_atualizacao(self, obj):
        return obj.ultima_atualizacao
    display_ultima_atualizacao.short_description = "Última Atualização"

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('nome', 'url', 'icone', 'ordem', 'ativo')
    list_editable = ('ordem', 'ativo')
    search_fields = ('nome', 'url')
    list_filter = ('ativo',)
    ordering = ['ordem']

@admin.register(PermissaoMenu)
class PermissaoMenuAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'menu', 'nivel_acesso')
    list_filter = ('menu', 'nivel_acesso')
    search_fields = ('perfil__user__username', 'menu__nome')
