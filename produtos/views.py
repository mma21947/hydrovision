from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Produto, Categoria, MovimentacaoEstoque, UnidadeMedida
import csv
import datetime

@login_required
def listar_produtos(request):
    # --- Lógica para Gerenciar Unidades (POST) --- 
    if request.method == "POST" and 'form_unidade' in request.POST:
        sigla = request.POST.get('sigla')
        nome = request.POST.get('nome')
        unidade_id = request.POST.get('unidade_id', '')
        
        if not sigla or not nome:
            messages.error(request, 'Sigla e Nome da unidade são obrigatórios.')
        else:
            sigla_exists = UnidadeMedida.objects.filter(sigla__iexact=sigla)
            if unidade_id:
                sigla_exists = sigla_exists.exclude(id=unidade_id)
            
            if sigla_exists.exists():
                messages.error(request, f'A sigla de unidade "{sigla}" já está em uso.')
            else:
                if unidade_id:  # Edição
                    try:
                        unidade = UnidadeMedida.objects.get(id=unidade_id)
                        unidade.sigla = sigla
                        unidade.nome = nome
                        unidade.save()
                        messages.success(request, f'Unidade "{nome}" atualizada com sucesso!')
                    except Exception as e:
                        messages.error(request, f'Erro ao atualizar unidade: {str(e)}')
                else:  # Nova unidade
                    try:
                        UnidadeMedida.objects.create(sigla=sigla, nome=nome)
                        messages.success(request, f'Unidade "{nome}" criada com sucesso!')
                    except Exception as e:
                        messages.error(request, f'Erro ao criar unidade: {str(e)}')
        # Redirecionar para a própria página para evitar reenvio do form com F5
        return redirect('listar_produtos') 

    # --- Lógica para Listar Produtos (GET) --- 
    produtos_list = Produto.objects.select_related('categoria', 'unidade').all() # Otimizado com select_related
    
    # Filtros
    busca = request.GET.get('busca', '')
    categoria_id = request.GET.get('categoria', '')
    estoque = request.GET.get('estoque', '')
    
    if busca:
        produtos_list = produtos_list.filter(
            Q(nome__icontains=busca) | 
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    if categoria_id:
        produtos_list = produtos_list.filter(categoria_id=categoria_id)
    
    if estoque == 'baixo':
        produtos_list = produtos_list.filter(estoque_atual__lte=F('estoque_minimo'))
    elif estoque == 'zerado':
        produtos_list = produtos_list.filter(estoque_atual=0)
    elif estoque == 'disponivel':
        produtos_list = produtos_list.filter(estoque_atual__gt=0)
    
    # Ordenação
    ordem = request.GET.get('ordem', 'nome')
    if ordem == 'estoque_decrescente':
        produtos_list = produtos_list.order_by('-estoque_atual')
    elif ordem == 'estoque_crescente':
        produtos_list = produtos_list.order_by('estoque_atual')
    elif ordem == 'preco_decrescente':
        produtos_list = produtos_list.order_by('-preco_venda')
    elif ordem == 'preco_crescente':
        produtos_list = produtos_list.order_by('preco_venda')
    elif ordem == 'codigo':
        produtos_list = produtos_list.order_by('codigo')
    else:
        produtos_list = produtos_list.order_by('nome')
    
    # Paginação
    paginator = Paginator(produtos_list, 10)
    page = request.GET.get('page')
    produtos = paginator.get_page(page)
    
    categorias = Categoria.objects.all()
    unidades = UnidadeMedida.objects.all().order_by('nome') # Buscar unidades aqui
    
    # Estatísticas básicas
    total_produtos = Produto.objects.count()
    produtos_em_estoque = Produto.objects.filter(estoque_atual__gt=0).count()
    produtos_estoque_baixo = Produto.objects.filter(estoque_atual__lte=F('estoque_minimo'), estoque_atual__gt=0).count()
    produtos_zerados = Produto.objects.filter(estoque_atual=0).count()
    
    valor_total_estoque = Produto.objects.aggregate(
        total=Sum(ExpressionWrapper(F('estoque_atual') * F('preco_custo'), output_field=DecimalField()))
    )['total'] or 0
    
    context = {
        'produtos': produtos,
        'categorias': categorias,
        'unidades': unidades, # Adicionado unidades ao contexto
        'busca': busca,
        'categoria_id': categoria_id,
        'estoque': estoque,
        'ordem': ordem,
        'total_produtos': total_produtos,
        'produtos_em_estoque': produtos_em_estoque,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'produtos_zerados': produtos_zerados,
        'valor_total_estoque': valor_total_estoque,
    }
    
    return render(request, 'produtos/listar_produtos.html', context)

@login_required
def detalhe_produto(request, slug):
    try:
        produto = Produto.objects.get(slug=slug)
        movimentacoes = MovimentacaoEstoque.objects.filter(produto=produto).order_by('-data')[:10]
        
        context = {
            'produto': produto,
            'movimentacoes': movimentacoes,
        }
        
        return render(request, 'produtos/detalhe_produto.html', context)
    except Produto.DoesNotExist:
        messages.error(request, 'Produto não encontrado.')
        return redirect('listar_produtos')

@login_required
def novo_produto(request):
    categorias = Categoria.objects.all()
    unidades = UnidadeMedida.objects.all()
    
    if request.method == "POST":
        # Obter dados do formulário
        codigo = request.POST.get('codigo')
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        categoria_id = request.POST.get('categoria')
        
        # --- CORREÇÃO PREÇOS ---
        raw_preco_custo = request.POST.get('preco_custo', '0')
        raw_preco_venda = request.POST.get('preco_venda', '0')
        preco_custo = raw_preco_custo.replace('.', '').replace(',', '.')
        preco_venda = raw_preco_venda.replace('.', '').replace(',', '.')
        # --- FIM CORREÇÃO ---
        
        estoque_atual = request.POST.get('estoque_atual')
        estoque_minimo = request.POST.get('estoque_minimo')
        unidade_id = request.POST.get('unidade')
        observacoes = request.POST.get('observacoes')
        
        # Validar
        if Produto.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Já existe um produto com o código {codigo}')
            return render(request, 'produtos/novo_produto.html', {'categorias': categorias, 'unidades': unidades})
        
        try:
            categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None
            unidade_obj = UnidadeMedida.objects.get(id=unidade_id)
            
            novo_produto = Produto(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
                categoria=categoria,
                preco_custo=preco_custo,
                preco_venda=preco_venda,
                estoque_atual=estoque_atual,
                estoque_minimo=estoque_minimo,
                unidade=unidade_obj,
                observacoes=observacoes
            )
            
            # Salvar imagem se foi enviada
            if 'imagem' in request.FILES:
                novo_produto.imagem = request.FILES['imagem']
                
            novo_produto.save()
            
            # Registrar movimentação de estoque inicial
            if int(estoque_atual) > 0:
                MovimentacaoEstoque.objects.create(
                    produto=novo_produto,
                    tipo='entrada',
                    quantidade=estoque_atual,
                    usuario=request.user,
                    observacao='Estoque inicial'
                )
            
            messages.success(request, f'Produto {nome} cadastrado com sucesso!')
            return redirect('detalhe_produto', slug=novo_produto.slug)
            
        except UnidadeMedida.DoesNotExist:
            messages.error(request, 'Unidade de medida inválida.')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar produto: {str(e)}')
    
    return render(request, 'produtos/novo_produto.html', {'categorias': categorias, 'unidades': unidades})

@login_required
def editar_produto(request, slug):
    produto = get_object_or_404(Produto, slug=slug)
    categorias = Categoria.objects.all()
    unidades = UnidadeMedida.objects.all() # Adicionado busca de unidades
    
    if request.method == "POST":
        # Obter dados do formulário
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        categoria_id = request.POST.get('categoria')
        
        # --- CORREÇÃO PREÇOS ---
        raw_preco_custo = request.POST.get('preco_custo', '0')
        raw_preco_venda = request.POST.get('preco_venda', '0')
        preco_custo = raw_preco_custo.replace('.', '').replace(',', '.')
        preco_venda = raw_preco_venda.replace('.', '').replace(',', '.')
        # --- FIM CORREÇÃO ---
        
        estoque_minimo = request.POST.get('estoque_minimo')
        unidade_id = request.POST.get('unidade')
        observacoes = request.POST.get('observacoes')
        ativo = request.POST.get('ativo') == 'on'
        
        try:
            categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None
            unidade_obj = UnidadeMedida.objects.get(id=unidade_id)
            
            # Atualizar informações
            produto.nome = nome
            produto.descricao = descricao
            produto.categoria = categoria
            produto.preco_custo = preco_custo
            produto.preco_venda = preco_venda
            produto.estoque_minimo = estoque_minimo
            produto.unidade = unidade_obj
            produto.observacoes = observacoes
            produto.ativo = ativo
            
            # Salvar imagem se foi enviada
            if 'imagem' in request.FILES:
                produto.imagem = request.FILES['imagem']
                
            produto.save()
            
            messages.success(request, f'Produto {nome} atualizado com sucesso!')
            return redirect('detalhe_produto', slug=produto.slug)
            
        except UnidadeMedida.DoesNotExist:
            messages.error(request, 'Unidade de medida inválida.')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar produto: {str(e)}')
    
    context = {
        'produto': produto,
        'categorias': categorias,
        'unidades': unidades, # Passar unidades para o contexto
    }
    
    return render(request, 'produtos/editar_produto.html', context)

@login_required
def movimentar_estoque(request, slug):
    produto = get_object_or_404(Produto, slug=slug)
    
    if request.method == "POST":
        tipo = request.POST.get('tipo')
        quantidade = int(request.POST.get('quantidade', 0))
        observacao = request.POST.get('observacao', '')
        
        if quantidade <= 0:
            messages.error(request, 'A quantidade deve ser maior que zero.')
            return redirect('detalhe_produto', slug=produto.slug)
        
        # Para saída, verificar se há estoque suficiente
        if tipo == 'saida' and quantidade > produto.estoque_atual:
            messages.error(request, f'Estoque insuficiente. Disponível: {produto.estoque_atual}')
            return redirect('detalhe_produto', slug=produto.slug)
        
        # Atualizar estoque
        if tipo == 'entrada':
            produto.estoque_atual += quantidade
        elif tipo == 'saida':
            produto.estoque_atual -= quantidade
        elif tipo == 'ajuste':
            produto.estoque_atual = quantidade
            
        produto.save()
        
        # Registrar movimentação
        MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            usuario=request.user,
            observacao=observacao
        )
        
        messages.success(request, f'Estoque atualizado com sucesso! Novo estoque: {produto.estoque_atual}')
        
    return redirect('detalhe_produto', slug=produto.slug)

@login_required
def historico_movimentacoes(request, slug=None):
    movimentacoes = MovimentacaoEstoque.objects.all().order_by('-data')
    
    # Filtros
    produto_id = request.GET.get('produto', '')
    tipo = request.GET.get('tipo', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    if slug:
        produto = get_object_or_404(Produto, slug=slug)
        movimentacoes = movimentacoes.filter(produto=produto)
    elif produto_id:
        movimentacoes = movimentacoes.filter(produto_id=produto_id)
    
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
        
    if data_inicio:
        try:
            data_inicio = datetime.datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data__date__gte=data_inicio)
        except:
            pass
            
    if data_fim:
        try:
            data_fim = datetime.datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data__date__lte=data_fim)
        except:
            pass
    
    # Paginação
    paginator = Paginator(movimentacoes, 20)
    page = request.GET.get('page')
    movimentacoes_page = paginator.get_page(page)
    
    # Opções para filtros
    produtos = Produto.objects.all().order_by('nome')
    
    context = {
        'movimentacoes': movimentacoes_page,
        'produtos': produtos,
        'produto_selecionado': produto_id,
        'tipo': tipo,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'produtos/historico_movimentacoes.html', context)

@login_required
def exportar_produtos_csv(request):
    # Definir codificação e tipo de conteúdo
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig') 
    response['Content-Disposition'] = f'attachment; filename="produtos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Usar ; como delimitador e colocar tudo entre aspas
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(['Código', 'Nome', 'Categoria', 'Preço de Custo', 'Preço de Venda', 
                    'Estoque Atual', 'Estoque Mínimo', 'Unidade', 'Observações', 'Status'])
    
    produtos = Produto.objects.select_related('categoria', 'unidade').all() # Otimizado
    
    # Aplicar filtros (igual à view listar_produtos)
    busca = request.GET.get('busca', '')
    categoria_id = request.GET.get('categoria', '')
    estoque = request.GET.get('estoque', '')
    
    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) | 
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)
    
    if estoque == 'baixo':
        produtos = produtos.filter(estoque_atual__lte=F('estoque_minimo'))
    elif estoque == 'zerado':
        produtos = produtos.filter(estoque_atual=0)
    elif estoque == 'disponivel':
        produtos = produtos.filter(estoque_atual__gt=0)
    
    for produto in produtos:
        # Formatar preços com vírgula para o CSV
        preco_custo_fmt = str(produto.preco_custo).replace('.', ',')
        preco_venda_fmt = str(produto.preco_venda).replace('.', ',')
        
        writer.writerow([
            produto.codigo,
            produto.nome,
            produto.categoria.nome if produto.categoria else '',
            preco_custo_fmt, # Usar valor formatado
            preco_venda_fmt, # Usar valor formatado
            produto.estoque_atual,
            produto.estoque_minimo,
            produto.unidade.nome if produto.unidade else '',
            produto.observacoes or '',
            'Ativo' if produto.ativo else 'Inativo'
        ])
    
    return response

@login_required
def categorias(request):
    if request.method == "POST":
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        categoria_id = request.POST.get('categoria_id', '')
        
        if categoria_id:  # Edição
            try:
                categoria = Categoria.objects.get(id=categoria_id)
                categoria.nome = nome
                categoria.descricao = descricao
                categoria.save()
                messages.success(request, f'Categoria {nome} atualizada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
        else:  # Nova categoria
            try:
                Categoria.objects.create(nome=nome, descricao=descricao)
                messages.success(request, f'Categoria {nome} criada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao criar categoria: {str(e)}')
    
    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'produtos/categorias.html', {'categorias': categorias}) 