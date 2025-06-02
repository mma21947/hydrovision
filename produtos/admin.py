from django.contrib import admin
from .models import Categoria, Produto, MovimentacaoEstoque, UnidadeMedida

class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'categoria', 'unidade', 'preco_venda', 'estoque_atual', 'estoque_minimo', 'ativo')
    list_filter = ('categoria', 'ativo', 'unidade')
    search_fields = ('codigo', 'nome', 'descricao')
    prepopulated_fields = {'slug': ('codigo', 'nome',)}
    list_editable = ('preco_venda', 'estoque_minimo', 'ativo')
    list_per_page = 20
    autocomplete_fields = ['categoria', 'unidade']

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
    prepopulated_fields = {'slug': ('nome',)}

class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tipo', 'quantidade', 'data', 'usuario')
    list_filter = ('tipo', 'data', 'usuario')
    search_fields = ('produto__nome', 'produto__codigo', 'observacao')
    readonly_fields = ('data',)
    list_per_page = 20
    autocomplete_fields = ['produto', 'usuario', 'ordem_servico']

class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla')
    search_fields = ('nome', 'sigla')

admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(UnidadeMedida, UnidadeMedidaAdmin)
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(MovimentacaoEstoque, MovimentacaoEstoqueAdmin) 