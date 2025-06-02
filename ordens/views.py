from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe

from .models import OrdemServico, Categoria, Anexo, Comentario, ProdutoUtilizado
from clientes.models import Cliente
from tecnicos.models import Tecnico
from produtos.models import Produto, MovimentacaoEstoque
from .forms import OrdemServicoForm, ProdutoUtilizadoFormSet, ProdutoUtilizadoFormSetCustom
from equipamentos.models import Equipamento


# Função auxiliar para obter o técnico associado ao usuário atual
def obter_tecnico(request):
    """
    Busca o técnico associado ao usuário atual usando várias estratégias.
    Retorna o objeto Tecnico ou None se não encontrar.
    """
    try:
        # 1. Tentar pelo relacionamento direto
        try:
            return request.user.tecnico
        except Exception as e:
            print(f"Erro ao obter técnico pelo relacionamento direto: {str(e)}")
        
        # 2. Tentar pelo email
        tecnico = Tecnico.objects.filter(email=request.user.email).first()
        if tecnico:
            return tecnico
        
        # 3. Tentar pelo nome
        nome_completo = f"{request.user.first_name} {request.user.last_name}".strip()
        if nome_completo:
            tecnico = Tecnico.objects.filter(nome_completo__icontains=nome_completo).first()
            if tecnico:
                return tecnico
        
        # 4. Tentar pelo username associado ao nome do técnico
        username = request.user.username
        if username:
            tecnico = Tecnico.objects.filter(nome_completo__icontains=username).first()
            if tecnico:
                return tecnico
        
        # Não foi possível encontrar o técnico
        return None
    except Exception as e:
        print(f"Erro geral ao obter técnico: {str(e)}")
        return None

# Função auxiliar para verificar se o usuário atual está associado ao técnico da ordem
def verificar_tecnico_ordem(request, ordem):
    """
    Verifica se o usuário atual (com perfil de técnico) é o técnico atribuído a esta ordem.
    Retorna True se for permitido o acesso, False se não for.
    """
    try:
        perfil = request.user.perfil
        if perfil.tipo == 'tecnico':
            # Buscar o técnico associado ao usuário
            tecnico = obter_tecnico(request)
            
            # Se o técnico não for o atribuído à ordem, não permitir acesso
            if not tecnico or ordem.tecnico != tecnico:
                return False
            return True
        # Se não for técnico, permitir acesso
        return True
    except Exception as e:
        # Se houver erro, registrar
        print(f"Erro ao verificar permissão: {str(e)}")
        # Em caso de erro, permitir acesso para não bloquear usuários não-técnicos
        return True

# View de diagnóstico temporária
@login_required
def diagnostico_tecnico(request):
    """
    View para diagnóstico da associação entre usuário e técnico.
    Apenas para fins de depuração.
    """
    context = {
        'user': request.user,
        'username': request.user.username,
        'email': request.user.email,
        'nome_completo': f"{request.user.first_name} {request.user.last_name}".strip(),
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
    }
    
    # Verificar perfil
    try:
        perfil = request.user.perfil
        context['perfil_tipo'] = perfil.tipo
    except:
        context['perfil_tipo'] = "Não encontrado"
    
    # Buscar técnico
    tecnico = obter_tecnico(request)
    if tecnico:
        context['tecnico_encontrado'] = True
        context['tecnico_nome'] = tecnico.nome_completo
        context['tecnico_email'] = tecnico.email
        context['tecnico_id'] = tecnico.id
        
        # Listar ordens deste técnico
        ordens = OrdemServico.objects.filter(tecnico=tecnico)
        context['ordens_count'] = ordens.count()
        context['ordens'] = ordens
    else:
        context['tecnico_encontrado'] = False
    
    # Verificar todas as ordens no sistema
    todas_ordens = OrdemServico.objects.all()
    context['todas_ordens_count'] = todas_ordens.count()
    
    # Verificar todos os técnicos do sistema
    todos_tecnicos = Tecnico.objects.all()
    context['todos_tecnicos'] = todos_tecnicos
    
    # Tentar buscar técnico por outros meios
    tecnicos_por_email = Tecnico.objects.filter(email=request.user.email)
    context['tecnicos_por_email'] = tecnicos_por_email
    
    nome_completo = f"{request.user.first_name} {request.user.last_name}".strip()
    tecnicos_por_nome = Tecnico.objects.filter(nome_completo__icontains=nome_completo)
    context['tecnicos_por_nome'] = tecnicos_por_nome
    
    tecnicos_por_username = Tecnico.objects.filter(nome_completo__icontains=request.user.username)
    context['tecnicos_por_username'] = tecnicos_por_username
    
    return render(request, 'ordens/diagnostico_tecnico.html', context)

@login_required
def nova_ordem(request):
    # Obter listas para os campos de seleção
    clientes = Cliente.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    tecnicos = Tecnico.objects.all().order_by('nome_completo')
    
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            cliente_id = request.POST.get('cliente')
            categoria_id = request.POST.get('categoria')
            tecnico_id = request.POST.get('tecnico')
            equipamento_id = request.POST.get('equipamento')
            
            # Criar nova ordem
            ordem = OrdemServico(
                cliente_id=cliente_id,
                descricao=request.POST.get('descricao', ''),
                data_agendamento=request.POST.get('data_agendamento') or None,
                status=request.POST.get('status', 'aberta'),
                prioridade=request.POST.get('prioridade', 'media'),
            )
            
            # Campos opcionais
            if categoria_id:
                ordem.categoria_id = categoria_id
            if tecnico_id:
                ordem.tecnico_id = tecnico_id
            if equipamento_id:
                ordem.equipamento_id = equipamento_id
                
            # Dados de localização
            ordem.endereco = request.POST.get('endereco', '')
            ordem.numero_endereco = request.POST.get('numero_endereco', '')
            ordem.complemento = request.POST.get('complemento', '')
            ordem.bairro = request.POST.get('bairro', '')
            ordem.cidade = request.POST.get('cidade', '')
            ordem.estado = request.POST.get('estado', '')
            ordem.cep = request.POST.get('cep', '')
            
            # Valores financeiros - convertendo para decimal
            ordem.valor_servico = Decimal(request.POST.get('valor_servico', '0') or '0')
            ordem.valor_pecas = Decimal(request.POST.get('valor_pecas', '0') or '0')
            ordem.valor_deslocamento = Decimal(request.POST.get('valor_deslocamento', '0') or '0')
            ordem.desconto = Decimal(request.POST.get('desconto', '0') or '0')
            
            # Campos adicionais
            ordem.observacoes_internas = request.POST.get('observacoes_internas', '')
            
            # Salvar ordem - o número será gerado automaticamente pelo método save()
            ordem.save()
            
            # Se foi selecionado um equipamento, cria uma manutenção automaticamente
            if equipamento_id and request.POST.get('criar_manutencao', False):
                from equipamentos.models import ManutencaoEquipamento
                manutencao = ManutencaoEquipamento(
                    equipamento_id=equipamento_id,
                    ordem_servico=ordem,
                    tipo=request.POST.get('tipo_manutencao', 'corretiva'),
                    data=timezone.now(),
                    descricao=ordem.descricao,
                    responsavel=request.user.get_full_name() or request.user.username,
                )
                manutencao.save()
            
            messages.success(
                request, 
                f'Ordem de serviço {ordem.numero} criada com sucesso!'
            )
            
            # Verificar se deve redirecionar para a impressão
            if request.POST.get('action') == 'save_and_print' or request.POST.get('imprimir_apos_salvar', '').lower() == 'true':
                return redirect('imprimir_ordem', slug=ordem.slug)
            
            return redirect('listar_ordens')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao criar ordem de serviço: {str(e)}'
            )
    
    context = {
        'clientes': clientes,
        'categorias': categorias,
        'tecnicos': tecnicos,
    }
    return render(request, 'ordens/nova_ordem.html', context)

@login_required
def listar_ordens(request):
    # Obter parâmetros de filtro da URL
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')
    
    # Iniciar queryset
    queryset = OrdemServico.objects.all()
    
    # Verificar se o usuário é técnico e filtrar as ordens atribuídas a ele
    try:
        perfil = request.user.perfil
        if perfil.tipo == 'tecnico':
            # Buscar o técnico associado ao usuário
            tecnico = obter_tecnico(request)
            if tecnico:
                queryset = queryset.filter(tecnico=tecnico)
                # Mensagem para debug/log
                print(f"Filtrando ordens para o técnico: {tecnico.nome_completo} (ID: {tecnico.id})")
            else:
                # Se não encontrou o técnico, não mostrar nenhuma ordem
                queryset = queryset.none()
                messages.warning(request, 'Você tem perfil de técnico, mas não foi possível encontrar seu registro como técnico no sistema. Entre em contato com o administrador.')
                print(f"Não foi possível encontrar um técnico associado ao usuário: {request.user.username}")
    except Exception as e:
        # Se houver erro, registrar e não aplicar filtro
        print(f"Erro ao verificar perfil ou obter técnico: {str(e)}")
    
    # Aplicar filtro por status se especificado
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Aplicar busca se especificada
    if search_query:
        queryset = queryset.filter(
            # Buscar pelo número da ordem
            models.Q(numero__icontains=search_query) |
            # Buscar pelo nome do cliente
            models.Q(cliente__nome__icontains=search_query) |
            # Buscar pela descrição
            models.Q(descricao__icontains=search_query)
        )
    
    # Ordenar pelo mais recente primeiro
    ordens = queryset.order_by('-data_abertura')
    
    # Para debug: imprimir a quantidade de ordens encontradas
    print(f"Total de ordens após filtragem: {ordens.count()}")
    
    context = {
        'ordens': ordens,
    }
    
    return render(request, 'ordens/listar_ordens.html', context)

@login_required
def detalhe_ordem(request, slug):
    try:
        ordem = OrdemServico.objects.get(slug=slug)
    except OrdemServico.DoesNotExist:
        messages.error(request, 'Ordem de serviço não encontrada.')
        return redirect('listar_ordens')
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para visualizar esta ordem de serviço.')
        return redirect('listar_ordens')
    
    # Buscar produtos da OS e produtos disponíveis para o modal
    produtos_utilizados = ProdutoUtilizado.objects.filter(ordem_servico=ordem).select_related('produto')
    produtos_disponiveis = Produto.objects.filter(ativo=True, estoque_atual__gt=0).order_by('nome')
    
    # Adicionar metadados de avaliação para a escala de 5 estrelas
    avaliacao = ordem.avaliacao_cliente
    avaliacao_dados = {
        'valor': avaliacao,
        'texto': get_texto_avaliacao(avaliacao) if avaliacao else None,
        'classe': get_classe_avaliacao(avaliacao) if avaliacao else None,
        'estrelas': range(1, 6)  # Para iteração de 1 a 5 no template
    }
    
    # Verificar se a ordem está concluída
    pode_avaliar = ordem.status == 'concluida'
    
    # Passar a ordem e produtos para o template
    context = {
        'ordem': ordem,
        'produtos_utilizados': produtos_utilizados,
        'produtos_disponiveis': produtos_disponiveis,
        'avaliacao': avaliacao_dados,
        'pode_avaliar': pode_avaliar
    }
    
    return render(request, 'ordens/detalhe_ordem.html', context)

# Funções auxiliares para avaliação
def get_texto_avaliacao(nota):
    if not nota:
        return None
    
    textos = {
        5: 'Excelente',
        4: 'Muito Bom',
        3: 'Bom',
        2: 'Regular',
        1: 'Ruim'
    }
    return textos.get(nota, 'Não Avaliado')

def get_classe_avaliacao(nota):
    if not nota:
        return 'secondary'
    
    classes = {
        5: 'success',
        4: 'info',
        3: 'primary',
        2: 'warning',
        1: 'danger'
    }
    return classes.get(nota, 'secondary')

@login_required
def editar_ordem(request, slug):
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se há produtos utilizados inválidos e removê-los
    produtos_invalidos = ProdutoUtilizado.objects.filter(ordem_servico=ordem, produto_id__isnull=True)
    for produto_invalido in produtos_invalidos:
        print(f"Removendo produto utilizado inválido (ID: {produto_invalido.id})")
        produto_invalido.delete()
    
    if request.method == 'POST':
        # Criar uma cópia modificável do POST
        post_data = request.POST.copy()
        
        # Adicionar campos do management form se estiverem faltando
        if 'produtos-TOTAL_FORMS' not in post_data:
            # Contar quantos produtos já existem na ordem
            produtos_count = ordem.produtos_utilizados.count()
            post_data['produtos-TOTAL_FORMS'] = str(produtos_count)
            post_data['produtos-INITIAL_FORMS'] = str(produtos_count)
            post_data['produtos-MIN_NUM_FORMS'] = '0'
            post_data['produtos-MAX_NUM_FORMS'] = '1000'
            
            # Registrar no log para depuração
            print(f"Campos do management form adicionados manualmente: TOTAL={produtos_count}, INITIAL={produtos_count}")
        else:
            # Registrar os valores existentes para depuração
            print(f"Campos do management form encontrados: TOTAL={post_data['produtos-TOTAL_FORMS']}, INITIAL={post_data['produtos-INITIAL_FORMS']}")
            
        form = OrdemServicoForm(post_data, instance=ordem)
        formset = ProdutoUtilizadoFormSetCustom(post_data, request.FILES, instance=ordem, prefix='produtos')
        
        # Verificar se o formset é válido e mostrar erros detalhados se não for
        if not formset.is_valid():
            print("Erros no formset:", formset.errors)
            if formset.management_form.errors:
                print("Erros no management form:", formset.management_form.errors)
                messages.error(request, f"Erro no grupo de produtos: {formset.management_form.errors}")
                
        # Verificar se o formulário e o formset são válidos antes de salvar
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    ordem_salva = form.save(commit=False)
                    
                    # Processar o campo de equipamento (que vem fora do form)
                    equipamento_id = request.POST.get('equipamento')
                    if equipamento_id:
                        ordem_salva.equipamento_id = equipamento_id
                    else:
                        ordem_salva.equipamento = None
                    
                    # Garantir que os campos numéricos tenham valores válidos
                    if ordem_salva.valor_servico is None:
                        ordem_salva.valor_servico = Decimal('0')
                    if ordem_salva.valor_deslocamento is None:
                        ordem_salva.valor_deslocamento = Decimal('0')
                    if ordem_salva.desconto is None:
                        ordem_salva.desconto = Decimal('0')
                    
                    ordem_salva.save()

                    total_pecas_calculado = Decimal(0)
                    produtos_para_atualizar_estoque = []

                    # Cria dicionário de produtos já utilizados nesta ordem para não contar duas vezes
                    produtos_existentes = {}
                    for p in ProdutoUtilizado.objects.filter(ordem_servico=ordem):
                        if hasattr(p, 'produto_id') and p.produto_id is not None:
                            try:
                                produtos_existentes[p.produto.id] = p.quantidade
                            except Produto.DoesNotExist:
                                # Ignorar produtos que não existem mais no banco de dados
                                pass

                    instances = formset.save(commit=False)
                    for instance in instances:
                        # Pula se não tem produto associado
                        if not hasattr(instance, 'produto_id') or instance.produto_id is None:
                            # Se for um item existente sem produto, excluí-lo
                            if instance.pk:
                                instance.delete()
                            continue

                        try:
                            # Para produtos novos na OS, verifica estoque normalmente
                            if instance.pk is None:
                                if instance.quantidade > instance.produto.estoque_atual:
                                    raise ValidationError(f'<strong>Estoque insuficiente para "{instance.produto.nome}".</strong> Disponível: {instance.produto.estoque_atual}')
                            # Para produtos já existentes, verifica apenas se o aumento na quantidade está dentro do estoque disponível
                            elif instance.pk and instance.produto.id in produtos_existentes:
                                quantidade_anterior = produtos_existentes[instance.produto.id]
                                if instance.quantidade > quantidade_anterior:
                                    # Só precisa verificar a diferença adicional
                                    diferenca = instance.quantidade - quantidade_anterior
                                    if diferenca > instance.produto.estoque_atual:
                                        raise ValidationError(f'<strong>Estoque insuficiente para aumentar a quantidade de "{instance.produto.nome}".</strong> Disponível: {instance.produto.estoque_atual}')
                            
                            instance.ordem_servico = ordem_salva
                            if instance.preco_unitario is None:
                                instance.preco_unitario = instance.produto.preco_venda
                            instance.save()
                            total_pecas_calculado += instance.quantidade * instance.preco_unitario
                            
                            produtos_para_atualizar_estoque.append({
                                'produto': instance.produto,
                                'quantidade': instance.quantidade,
                                'tipo': 'saida',
                                'observacao': f'Utilizado na OS #{ordem_salva.numero}'
                            })
                        except Produto.DoesNotExist:
                            # Ignorar produtos que não existem mais no banco de dados
                            if instance.pk:
                                instance.delete()
                            continue
                        except Exception as e:
                            print(f"Erro ao processar produto: {str(e)}")
                            # Exibir o erro sem interromper todo o processo
                            messages.warning(request, f"Atenção: Um dos produtos não pôde ser processado - {str(e)}")
                        
                    for form_delete in formset.deleted_forms:
                        try:
                            if (form_delete.instance.pk and 
                                hasattr(form_delete.instance, 'produto_id') and 
                                form_delete.instance.produto_id is not None):
                                produto_deletado = form_delete.instance.produto
                                quantidade_deletada = form_delete.instance.quantidade
                                produtos_para_atualizar_estoque.append({
                                    'produto': produto_deletado,
                                    'quantidade': quantidade_deletada,
                                    'tipo': 'entrada',
                                    'observacao': f'Removido da OS #{ordem_salva.numero} (exclusão)'
                                })
                        except Produto.DoesNotExist:
                            # Ignorar produtos que não existem mais no banco de dados
                            pass
                    
                    # Salvar o formset depois de processar manualmente os itens
                    # Isso só atualizará os itens deletados no banco
                    formset.save()

                    for item in produtos_para_atualizar_estoque:
                        produto = item['produto']
                        quantidade = item['quantidade']
                        tipo_mov = item['tipo']
                        observacao = item['observacao']

                        if tipo_mov == 'saida':
                             produto.estoque_atual -= quantidade
                        elif tipo_mov == 'entrada':
                             produto.estoque_atual += quantidade
                        produto.save()

                        MovimentacaoEstoque.objects.create(
                            produto=produto,
                            tipo=tipo_mov,
                            quantidade=quantidade,
                            usuario=request.user,
                            observacao=observacao,
                            ordem_servico=ordem_salva
                        )
                        
                    ordem_salva.valor_pecas = total_pecas_calculado
                    ordem_salva.save()

                    messages.success(request, f'Ordem de Serviço {ordem_salva.numero} atualizada com sucesso!')
                    return redirect('detalhe_ordem', slug=ordem_salva.slug)
                    
            except ValidationError as e:
                # Formata a mensagem de erro para exibir corretamente o HTML
                messages.error(request, mark_safe(str(e)))
            except Exception as e:
                messages.error(request, f'Erro ao salvar a ordem: {str(e)}')
        else:
            # Melhora a exibição de erros específicos para ajudar o usuário
            if form.errors:
                for field, error in form.errors.items():
                    field_verbose = form[field].label or field
                    messages.error(request, f'Erro no campo "{field_verbose}": {error[0]}')
            
            if formset.errors:
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        produto_form = formset.forms[i]
                        produto_nome = "Novo produto"
                        if produto_form.instance and produto_form.instance.produto:
                            produto_nome = produto_form.instance.produto.nome
                        
                        for field, error in form_errors.items():
                            messages.error(request, f'Erro no produto "{produto_nome}", campo "{field}": {error[0]}')
            
            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    messages.error(request, f'Erro no grupo de produtos: {error}')

    else:
        # GET request - carregar formulário inicial
        form = OrdemServicoForm(instance=ordem)
        formset = ProdutoUtilizadoFormSetCustom(instance=ordem, prefix='produtos')
    
    # Verificar explicitamente se o management_form está sendo criado
    print("Management form no contexto:", formset.management_form)
    
    # Buscar listas para preenchimento dos campos
    clientes = Cliente.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    tecnicos = Tecnico.objects.all().order_by('nome_completo')
    produtos_disponiveis = Produto.objects.filter(ativo=True, estoque_atual__gt=0).order_by('nome')
    
    context = {
        'form': form,
        'formset': formset,
        'ordem': ordem,
        'clientes': clientes,
        'categorias': categorias,
        'tecnicos': tecnicos,
        'produtos_disponiveis': produtos_disponiveis,
    }
    
    # Buscar equipamentos do cliente atual para preencher o select de equipamentos
    if ordem.cliente:
        equipamentos_cliente = Equipamento.objects.filter(cliente=ordem.cliente).order_by('nome')
        context['equipamentos_cliente'] = equipamentos_cliente
    
    return render(request, 'ordens/editar_ordem.html', context)

@login_required
def listar_categorias(request):
    """
    Exibe a página de listagem de categorias com funcionalidades de filtragem
    """
    # Buscar todas as categorias
    categorias_qs = Categoria.objects.all()
    
    # Verificar se há um termo de busca
    busca = request.GET.get('busca', '')
    if busca:
        categorias_qs = categorias_qs.filter(
            models.Q(nome__icontains=busca) | 
            models.Q(descricao__icontains=busca)
        )
    
    # Criar uma lista para os resultados
    categorias = []
    
    # Para cada categoria, contar manualmente as ordens
    for categoria in categorias_qs:
        categoria_dict = {
            'id': categoria.id,
            'nome': categoria.nome,
            'descricao': categoria.descricao,
            'slug': categoria.slug,
            'data_criacao': categoria.data_criacao,
            'total_ordens': categoria.ordens.count()
        }
        
        # Filtrar por status se necessário
        status = request.GET.get('status', '')
        if status == 'com_ordens' and categoria_dict['total_ordens'] == 0:
            continue
        if status == 'sem_ordens' and categoria_dict['total_ordens'] > 0:
            continue
            
        categorias.append(categoria_dict)
    
    # Ordenar pelo nome
    categorias.sort(key=lambda x: x['nome'])
    
    # Estatísticas gerais
    total_categorias = Categoria.objects.count()
    
    # Calcular categorias com ordens manualmente
    categorias_com_ordens = 0
    for categoria in Categoria.objects.all():
        if categoria.ordens.exists():
            categorias_com_ordens += 1
    
    context = {
        'categorias': categorias,
        'total_categorias': total_categorias,
        'categorias_com_ordens': categorias_com_ordens,
    }
    
    return render(request, 'ordens/listar_categorias.html', context)

@login_required
def nova_categoria(request):
    if request.method == 'POST':
        try:
            # Criar nova categoria
            nome = request.POST.get('nome', '')
            descricao = request.POST.get('descricao', '')
            
            if not nome:
                messages.error(request, 'O nome da categoria é obrigatório.')
                return render(request, 'ordens/nova_categoria.html')
            
            # Verificar se já existe uma categoria com este nome
            if Categoria.objects.filter(nome=nome).exists():
                messages.error(request, f'Já existe uma categoria com o nome "{nome}".')
                return render(request, 'ordens/nova_categoria.html')
            
            categoria = Categoria.objects.create(
                nome=nome,
                descricao=descricao
            )
            
            messages.success(
                request, 
                f'Categoria {categoria.nome} criada com sucesso!'
            )
            return redirect('listar_categorias')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao criar categoria: {str(e)}'
            )
    
    return render(request, 'ordens/nova_categoria.html')

@login_required
def editar_categoria(request, slug):
    # Buscar a categoria
    categoria = get_object_or_404(Categoria, slug=slug)
    
    if request.method == 'POST':
        try:
            # Atualizar dados da categoria
            nome = request.POST.get('nome', '')
            descricao = request.POST.get('descricao', '')
            
            if not nome:
                messages.error(request, 'O nome da categoria é obrigatório.')
                return render(request, 'ordens/editar_categoria.html', {'categoria': categoria})
            
            # Verificar se já existe uma categoria com este nome (exceto a atual)
            if Categoria.objects.filter(nome=nome).exclude(id=categoria.id).exists():
                messages.error(request, f'Já existe uma categoria com o nome "{nome}".')
                return render(request, 'ordens/editar_categoria.html', {'categoria': categoria})
            
            categoria.nome = nome
            categoria.descricao = descricao
            categoria.save()
            
            messages.success(
                request, 
                f'Categoria {categoria.nome} atualizada com sucesso!'
            )
            return redirect('listar_categorias')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao atualizar categoria: {str(e)}'
            )
    
    return render(request, 'ordens/editar_categoria.html', {'categoria': categoria})

@login_required
def excluir_categoria(request, categoria_id):
    # Buscar a categoria
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    if request.method == 'POST':
        try:
            # Verificar se há ordens de serviço vinculadas
            if OrdemServico.objects.filter(categoria=categoria).exists():
                messages.warning(
                    request, 
                    f'Não é possível excluir a categoria {categoria.nome} pois existem ordens de serviço vinculadas a ela.'
                )
                return redirect('listar_categorias')
            
            nome_categoria = categoria.nome
            categoria.delete()
            
            messages.success(
                request, 
                f'Categoria {nome_categoria} excluída com sucesso!'
            )
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao excluir categoria: {str(e)}'
            )
    
    return redirect('listar_categorias')

@require_POST
def criar_categoria_ajax(request):
    """
    Cria uma nova categoria via AJAX
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})
    
    nome = request.POST.get('nome')
    descricao = request.POST.get('descricao', '')
    
    if not nome:
        return JsonResponse({'success': False, 'message': 'Nome da categoria é obrigatório'})
    
    # Verificar se já existe categoria com este nome
    if Categoria.objects.filter(nome=nome).exists():
        return JsonResponse({'success': False, 'message': 'Já existe uma categoria com este nome'})
    
    try:
        categoria = Categoria.objects.create(
            nome=nome,
            descricao=descricao
        )
        return JsonResponse({
            'success': True, 
            'message': 'Categoria criada com sucesso',
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao criar categoria: {str(e)}'})

@require_POST
def editar_categoria_ajax(request):
    """
    Edita uma categoria existente via AJAX
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})
    
    categoria_id = request.POST.get('id')
    nome = request.POST.get('nome')
    descricao = request.POST.get('descricao', '')
    
    if not categoria_id or not nome:
        return JsonResponse({'success': False, 'message': 'ID e nome da categoria são obrigatórios'})
    
    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Categoria não encontrada'})
    
    # Verificar se já existe outra categoria com este nome
    if Categoria.objects.filter(nome=nome).exclude(id=categoria_id).exists():
        return JsonResponse({'success': False, 'message': 'Já existe outra categoria com este nome'})
    
    try:
        categoria.nome = nome
        categoria.descricao = descricao
        categoria.save()
        return JsonResponse({
            'success': True, 
            'message': 'Categoria atualizada com sucesso',
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao atualizar categoria: {str(e)}'})

@require_POST
def excluir_categoria_ajax(request):
    """
    Exclui uma categoria via AJAX
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})
    
    categoria_id = request.POST.get('id') or request.POST.get('categoria_id')
    
    if not categoria_id:
        return JsonResponse({'success': False, 'message': 'ID da categoria é obrigatório'})
    
    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Categoria não encontrada'})
    
    # Verificar se a categoria possui ordens associadas
    if categoria.ordens.count() > 0:
        return JsonResponse({
            'success': False, 
            'message': f'Não é possível excluir esta categoria pois existem {categoria.ordens.count()} ordens associadas.'
        })
    
    try:
        categoria.delete()
        return JsonResponse({'success': True, 'message': 'Categoria excluída com sucesso'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir categoria: {str(e)}'})

def detalhe_categoria_ajax(request, categoria_id):
    """
    Retorna os detalhes de uma categoria via AJAX
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Requisição inválida'})
    
    try:
        categoria = Categoria.objects.get(id=categoria_id)
    except Categoria.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Categoria não encontrada'})
    
    # Contar ordens desta categoria
    total_ordens = categoria.ordens.count()
    
    # Obter data da última ordem associada
    ultima_ordem = categoria.ordens.order_by('-data_abertura').first()
    ultima_utilizacao = ultima_ordem.data_abertura if ultima_ordem else None
    
    return JsonResponse({
        'success': True,
        'categoria': {
            'id': categoria.id,
            'nome': categoria.nome,
            'descricao': categoria.descricao,
            'data_criacao': categoria.data_criacao.isoformat() if categoria.data_criacao else None,
            'total_ordens': total_ordens,
            'ultima_utilizacao': ultima_utilizacao.isoformat() if ultima_utilizacao else None
        }
    })

@login_required
def novo_anexo(request, ordem_slug):
    # Buscar a ordem de serviço
    ordem = get_object_or_404(OrdemServico, slug=ordem_slug)
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            titulo = request.POST.get('titulo')
            arquivo = request.FILES.get('arquivo')
            
            # Validar dados
            if not titulo:
                messages.error(request, 'O título do anexo é obrigatório.')
                return redirect('detalhe_ordem', slug=ordem_slug)
                
            if not arquivo:
                messages.error(request, 'É necessário selecionar um arquivo para anexar.')
                return redirect('detalhe_ordem', slug=ordem_slug)
            
            # Criar um novo anexo
            anexo = Anexo.objects.create(
                ordem=ordem,
                titulo=titulo,
                arquivo=arquivo
            )
            
            messages.success(request, 'Arquivo anexado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao anexar arquivo: {str(e)}')
    
    return redirect('detalhe_ordem', slug=ordem_slug)

@login_required
def novo_comentario(request, ordem_slug):
    # Buscar a ordem de serviço
    ordem = get_object_or_404(OrdemServico, slug=ordem_slug)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para comentar nesta ordem de serviço.')
        return redirect('listar_ordens')
    
    if request.method == 'POST':
        texto = request.POST.get('texto')
        
        if not texto:
            messages.error(request, 'O texto do comentário não pode estar vazio.')
            return redirect('detalhe_ordem', slug=ordem_slug)
        
        # Determinar o tipo de autor
        tipo_autor = 'operador'  # Padrão
        
        # Verificar se é um técnico
        try:
            if hasattr(request.user, 'tecnico') and request.user.tecnico:
                if ordem.tecnico == request.user.tecnico:
                    tipo_autor = 'tecnico'
        except:
            pass
        
        # Verificar se está reportando um problema
        reportando_problema = 'reportando_problema' in request.POST
        tipo_problema = 'sem_problema'
        
        if reportando_problema:
            tipo_problema = request.POST.get('tipo_problema', 'sem_problema')
        
        # Criar o comentário
        comentario = Comentario.objects.create(
            ordem=ordem,
            autor=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            tipo_autor=tipo_autor,
            texto=texto,
            interno=request.POST.get('interno', False),
            reportando_problema=reportando_problema,
            tipo_problema=tipo_problema
        )
        
        # Se reportou um problema, atualizar o status da ordem
        if reportando_problema and ordem.status not in ['concluida', 'cancelada']:
            # Se a ordem estiver em andamento, adicionar uma observação interna
            observacao = f"PROBLEMA REPORTADO: {dict(Comentario.TIPO_PROBLEMA_CHOICES).get(tipo_problema, 'Outro')}\n"
            observacao += f"Por: {comentario.autor} em {comentario.data_criacao.strftime('%d/%m/%Y às %H:%M')}\n\n"
            
            if ordem.observacoes_internas:
                ordem.observacoes_internas += f"\n\n{observacao}"
            else:
                ordem.observacoes_internas = observacao
                
            # Se for problema do tipo "aguardando_peca", alterar o status
            if tipo_problema == 'material':
                ordem.status = 'aguardando_peca'
                messages.info(request, 'O status da ordem foi alterado para "Aguardando Peça".')
            
            # Salvar a ordem
            ordem.save()
        
        messages.success(request, 'Comentário adicionado com sucesso!')
        
    return redirect('detalhe_ordem', slug=ordem_slug)

@login_required
def avaliar_ordem(request, slug):
    # Buscar a ordem de serviço pelo slug
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se a ordem está concluída
    if ordem.status != 'concluida':
        messages.warning(request, 'Somente ordens concluídas podem ser avaliadas.')
        return redirect('detalhe_ordem', slug=slug)
    
    if request.method == 'POST':
        # Capturar os dados do formulário
        avaliacao = request.POST.get('avaliacao')
        comentario_cliente = request.POST.get('feedback_cliente')
        
        # Validar e salvar os dados
        if avaliacao and avaliacao.isdigit() and 1 <= int(avaliacao) <= 5:
            # Salvar a avaliação e o comentário
            ordem.avaliacao_cliente = int(avaliacao)
            ordem.comentario_cliente = comentario_cliente
            ordem.save()
            
            # Adicionar mensagem de sucesso
            messages.success(request, 'Avaliação registrada com sucesso!')
        else:
            messages.error(request, 'Por favor, informe uma avaliação válida (1-5 estrelas).')
    
    return redirect('detalhe_ordem', slug=slug)

@login_required
def encerrar_ordem(request, slug):
    """
    Encerra uma ordem de serviço e registra a avaliação do cliente simultaneamente.
    """
    # Buscar a ordem de serviço pelo slug
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para encerrar esta ordem de serviço.')
        return redirect('listar_ordens')
        
    # Verificar se a ordem já está concluída ou cancelada
    if ordem.status in ['concluida', 'cancelada']:
        messages.warning(request, 'Esta ordem já está encerrada.')
        return redirect('detalhe_ordem', slug=slug)
    
    if request.method == 'POST':
        try:
            # Capturar os dados do formulário
            solucao = request.POST.get('solucao')
            avaliacao = request.POST.get('avaliacao')
            feedback_cliente = request.POST.get('feedback_cliente')
            assinatura_cliente = request.POST.get('assinatura_cliente')
            
            # Validar campos obrigatórios
            if not solucao:
                messages.error(request, 'A solução aplicada é obrigatória.')
                return redirect('detalhe_ordem', slug=slug)
                
            if not avaliacao or not avaliacao.isdigit() or not (1 <= int(avaliacao) <= 5):
                messages.error(request, 'É necessário informar uma avaliação válida (1-5 estrelas).')
                return redirect('detalhe_ordem', slug=slug)
            
            # Verificar se há produtos associados à ordem e se a confirmação foi feita
            produtos_utilizados = ordem.produtos_utilizados.exists()
            if produtos_utilizados and 'confirma_produtos' not in request.POST:
                messages.error(request, 'É necessário confirmar os produtos utilizados antes de encerrar a ordem.')
                return redirect('detalhe_ordem', slug=slug)
            
            # Verificar a assinatura do cliente
            if not assinatura_cliente:
                messages.error(request, 'A assinatura digital do cliente é obrigatória para encerrar a ordem.')
                return redirect('detalhe_ordem', slug=slug)
                
            # Verificar confirmação de encerramento
            if 'confirma_encerramento' not in request.POST:
                messages.error(request, 'É necessário confirmar que todos os itens foram revisados e o serviço foi concluído.')
                return redirect('detalhe_ordem', slug=slug)
            
            # Atualizar a ordem
            with transaction.atomic():
                # Registrar data de conclusão
                ordem.data_conclusao = timezone.now()
                ordem.status = 'concluida'
                ordem.solucao = solucao
                ordem.avaliacao_cliente = int(avaliacao)
                ordem.comentario_cliente = feedback_cliente
                ordem.assinatura_cliente = assinatura_cliente
                ordem.save()
                
                # Registrar um comentário no sistema sobre o encerramento
                Comentario.objects.create(
                    ordem=ordem,
                    autor=f"{request.user.first_name} {request.user.last_name}",
                    tipo_autor="operador" if not hasattr(request.user, 'tecnico') else "tecnico",
                    texto=f"Ordem de serviço encerrada com sucesso. Avaliação do cliente: {avaliacao}/5 estrelas.",
                    interno=True
                )
                
                messages.success(request, 'Ordem de serviço encerrada com sucesso e avaliação registrada!')
                
        except Exception as e:
            messages.error(request, f'Erro ao encerrar a ordem: {str(e)}')
    
    return redirect('detalhe_ordem', slug=slug)

@login_required
def imprimir_ordem(request, slug):
    # Buscar a ordem de serviço pelo slug
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para imprimir esta ordem de serviço.')
        return redirect('listar_ordens')
    
    # Passar a ordem para o template de impressão
    context = {
        'ordem': ordem,
    }
    
    return render(request, 'ordens/imprimir_ordem.html', context)

@login_required
def resolver_problema_comentario(request, comentario_id):
    # Buscar o comentário
    comentario = get_object_or_404(Comentario, id=comentario_id)
    ordem = comentario.ordem
    
    # Verificar permissão (apenas operadores podem marcar como resolvido)
    if hasattr(request.user, 'tecnico') and request.user.tecnico:
        messages.error(request, 'Apenas operadores podem marcar problemas como resolvidos.')
        return redirect('detalhe_ordem', slug=ordem.slug)
    
    # Verificar se é realmente um problema
    if not comentario.reportando_problema:
        messages.error(request, 'Este comentário não reporta um problema.')
        return redirect('detalhe_ordem', slug=ordem.slug)
    
    # Marcar como resolvido
    comentario.resolvido = True
    comentario.data_resolucao = timezone.now()
    comentario.save()
    
    # Registrar um novo comentário de sistema sobre a resolução
    Comentario.objects.create(
        ordem=ordem,
        autor="Sistema",
        tipo_autor="sistema",
        texto=f'Problema "{dict(Comentario.TIPO_PROBLEMA_CHOICES).get(comentario.tipo_problema, "Outro")}" marcado como resolvido por {request.user.first_name} {request.user.last_name}',
        interno=True
    )
    
    # Verificar se o status da ordem foi alterado devido ao problema e restaurar
    if comentario.tipo_problema == 'material' and ordem.status == 'aguardando_peca':
        # Restaurar para "em_andamento" se estiver aguardando peça
        ordem.status = 'em_andamento'
        ordem.save()
        messages.info(request, 'O status da ordem foi restaurado para "Em Andamento".')
    
    messages.success(request, 'Problema marcado como resolvido com sucesso!')
    return redirect('detalhe_ordem', slug=ordem.slug)

@login_required
def adicionar_peca_os(request, slug):
    """
    View para adicionar uma peça/produto a uma ordem de serviço
    """
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para adicionar peças a esta ordem de serviço.')
        return redirect('listar_ordens')
    
    if request.method == 'POST':
        try:
            # Obter os dados do formulário
            produto_id = request.POST.get('produto_id')
            quantidade_str = request.POST.get('quantidade', '0')
            
            # Validar produto
            if not produto_id:
                messages.error(request, 'É necessário selecionar um produto.')
                return redirect('detalhe_ordem', slug=slug)
                
            # Converter quantidade para decimal e validar
            try:
                quantidade = Decimal(quantidade_str)
                if quantidade <= 0:
                    raise ValueError("A quantidade deve ser maior que zero.")
            except ValueError:
                messages.error(request, 'Quantidade inválida. Informe um valor numérico maior que zero.')
                return redirect('detalhe_ordem', slug=slug)
            
            # Buscar o produto
            produto = get_object_or_404(Produto, id=produto_id)
            
            # Verificar estoque
            if quantidade > produto.estoque_atual:
                messages.error(
                    request, 
                    f'Estoque insuficiente para "{produto.nome}". Disponível: {produto.estoque_atual}'
                )
                return redirect('detalhe_ordem', slug=slug)
            
            # Verificar se já existe este produto na OS
            produto_existente = ProdutoUtilizado.objects.filter(
                ordem_servico=ordem,
                produto=produto
            ).first()
            
            if produto_existente:
                # Atualizar quantidade
                produto_existente.quantidade += quantidade
                produto_existente.save()
                messages.success(
                    request, 
                    f'Quantidade de "{produto.nome}" atualizada para {produto_existente.quantidade}.'
                )
            else:
                # Criar novo registro
                ProdutoUtilizado.objects.create(
                    ordem_servico=ordem,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=produto.preco_venda
                )
                messages.success(
                    request, 
                    f'"{produto.nome}" adicionado à ordem de serviço.'
                )
            
            # Atualizar estoque do produto
            produto.estoque_atual -= quantidade
            produto.save()
            
            # Registrar movimentação de estoque
            MovimentacaoEstoque.objects.create(
                produto=produto,
                tipo='saida',
                quantidade=quantidade,
                usuario=request.user,
                observacao=f'Utilizado na OS #{ordem.numero}',
                ordem_servico=ordem
            )
            
            # Recalcular valor total de peças na OS
            produtos_utilizados = ProdutoUtilizado.objects.filter(ordem_servico=ordem)
            valor_total_pecas = sum(
                p.quantidade * p.preco_unitario 
                for p in produtos_utilizados
            )
            
            # Atualizar valor das peças e total da OS
            ordem.valor_pecas = valor_total_pecas
            ordem.save()  # O valor_total é recalculado no método save() do modelo
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar produto: {str(e)}')
    
    return redirect('detalhe_ordem', slug=slug)

@login_required
def adicionar_anexo(request, ordem_id):
    """
    View para adicionar um anexo a uma ordem de serviço usando o ID da ordem
    """
    # Buscar a ordem de serviço pelo ID
    ordem = get_object_or_404(OrdemServico, id=ordem_id)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para adicionar anexos a esta ordem de serviço.')
        return redirect('listar_ordens')
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            titulo = request.POST.get('titulo')
            arquivo = request.FILES.get('arquivo')
            
            # Validar dados
            if not titulo:
                messages.error(request, 'O título do anexo é obrigatório.')
                return redirect('detalhe_ordem', slug=ordem.slug)
                
            if not arquivo:
                messages.error(request, 'É necessário selecionar um arquivo para anexar.')
                return redirect('detalhe_ordem', slug=ordem.slug)
            
            # Criar um novo anexo
            anexo = Anexo.objects.create(
                ordem=ordem,
                titulo=titulo,
                arquivo=arquivo
            )
            
            messages.success(request, 'Arquivo anexado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao anexar arquivo: {str(e)}')
    
    return redirect('detalhe_ordem', slug=ordem.slug)

@login_required
def excluir_anexo(request, anexo_id):
    """
    View para excluir um anexo de uma ordem de serviço
    """
    # Buscar o anexo pelo ID
    anexo = get_object_or_404(Anexo, id=anexo_id)
    ordem = anexo.ordem
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para excluir anexos desta ordem de serviço.')
        return redirect('listar_ordens')
    
    try:
        # Excluir o anexo
        anexo.delete()
        messages.success(request, 'Anexo excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir anexo: {str(e)}')
    
    return redirect('detalhe_ordem', slug=ordem.slug)

@login_required
def buscar_equipamentos_cliente(request):
    cliente_id = request.GET.get('cliente_id')
    equipamentos = []
    if cliente_id:
        # Busca equipamentos do cliente especificado, ordenando por nome
        equipamentos_qs = Equipamento.objects.filter(cliente_id=cliente_id).values('id', 'nome', 'codigo', 'modelo').order_by('nome')
        equipamentos = list(equipamentos_qs) # Converte o QuerySet para lista de dicionários

    return JsonResponse({'equipamentos': equipamentos})

@login_required
def buscar_endereco_cliente(request):
    """
    Endpoint AJAX para buscar o endereço de um cliente.
    Retorna JSON com os dados de endereço do cliente selecionado.
    """
    cliente_id = request.GET.get('cliente_id')
    
    if not cliente_id:
        return JsonResponse({'success': False, 'message': 'ID do cliente não fornecido'})
    
    try:
        print(f"Buscando cliente com ID: {cliente_id}")
        cliente = Cliente.objects.get(pk=cliente_id)
        
        # Log para depuração
        print(f"Cliente encontrado: {cliente.nome}")
        print(f"Endereço: {cliente.endereco}, {cliente.numero}")
        print(f"Complemento: {cliente.complemento}")
        print(f"Bairro: {cliente.bairro}")
        print(f"Cidade/Estado: {cliente.cidade}/{cliente.estado}")
        print(f"CEP: {cliente.cep}")
        
        # Retornar os dados de endereço do cliente
        endereco_data = {
            'success': True,
            'endereco': cliente.endereco,
            'numero': cliente.numero,
            'complemento': cliente.complemento or '',
            'bairro': cliente.bairro,
            'cidade': cliente.cidade,
            'estado': cliente.estado,
            'cep': cliente.cep
        }
        
        print(f"Dados de endereço retornados: {endereco_data}")
        return JsonResponse(endereco_data)
        
    except Cliente.DoesNotExist:
        print(f"Cliente com ID {cliente_id} não encontrado")
        return JsonResponse({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        print(f"Erro ao buscar endereço: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erro ao buscar endereço: {str(e)}'})

@login_required
def excluir_ordem(request, slug):
    """
    View para excluir uma ordem de serviço
    """
    # Buscar a ordem pelo slug
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Verificar se o usuário tem permissão para acessar esta ordem
    if not verificar_tecnico_ordem(request, ordem):
        messages.error(request, 'Você não tem permissão para excluir esta ordem de serviço.')
        return redirect('listar_ordens')
    
    if request.method == 'POST':
        try:
            # Salvar informações para mensagem de sucesso
            numero_ordem = ordem.numero
            
            # Excluir a ordem
            ordem.delete()
            
            messages.success(
                request, 
                f'Ordem de serviço #{numero_ordem} excluída com sucesso!'
            )
            return redirect('listar_ordens')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao excluir ordem de serviço: {str(e)}'
            )
            return redirect('detalhe_ordem', slug=slug)
    
    # Se for apenas um GET, renderiza página de confirmação
    context = {
        'ordem': ordem
    }
    return render(request, 'ordens/excluir_ordem.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Apenas para administradores
def limpar_produtos_invalidos(request):
    """
    View administrativa para limpar registros corrompidos de ProdutoUtilizado.
    Identifica e remove todos os registros de ProdutoUtilizado que não têm um produto associado.
    """
    if request.method == 'POST':
        try:
            # Buscar produtos utilizados sem produto (inválidos)
            produtos_invalidos = ProdutoUtilizado.objects.filter(produto_id__isnull=True)
            count = produtos_invalidos.count()
            
            # Registrar os IDs dos produtos inválidos
            produtos_invalidos_ids = list(produtos_invalidos.values_list('id', flat=True))
            ordens_afetadas = list(produtos_invalidos.values_list('ordem_servico__numero', flat=True).distinct())
            
            # Excluir os produtos inválidos
            produtos_invalidos.delete()
            
            # Notificar o usuário
            messages.success(request, 
                f'Foram removidos {count} registros de produtos utilizados inválidos. ' +
                f'Ordens afetadas: {", ".join(ordens_afetadas) if ordens_afetadas else "Nenhuma"}. ' +
                f'IDs removidos: {", ".join(map(str, produtos_invalidos_ids)) if produtos_invalidos_ids else "Nenhum"}.'
            )
            
        except Exception as e:
            messages.error(request, f'Erro ao limpar produtos inválidos: {str(e)}')
    
    # Buscar a estatística atual
    produtos_invalidos_count = ProdutoUtilizado.objects.filter(produto_id__isnull=True).count()
    ordens_com_produtos_invalidos = OrdemServico.objects.filter(
        produtos_utilizados__produto_id__isnull=True
    ).distinct().count()
    
    context = {
        'produtos_invalidos_count': produtos_invalidos_count,
        'ordens_com_produtos_invalidos': ordens_com_produtos_invalidos,
    }
    
    return render(request, 'ordens/admin/limpar_produtos_invalidos.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Apenas para administradores
def corrigir_ordem_especifica(request, slug):
    """
    View especial para corrigir uma ordem específica que está com problemas
    de produtos utilizados sem produto associado (caso emergencial).
    """
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    # Buscar produtos utilizados inválidos nesta OS específica
    produtos_invalidos = ProdutoUtilizado.objects.filter(
        ordem_servico=ordem, 
        produto_id__isnull=True
    )
    
    count = produtos_invalidos.count()
    ids_removidos = list(produtos_invalidos.values_list('id', flat=True))
    
    # Excluir os produtos inválidos
    produtos_invalidos.delete()
    
    # Verificar se há mais algum problema com a ordem
    try:
        # Tentar acessar outros produtos utilizados para verificar se estão ok
        produtos_validos = ProdutoUtilizado.objects.filter(ordem_servico=ordem)
        for p in produtos_validos:
            try:
                # Tentar acessar o nome do produto para verificar se a relação está ok
                nome_produto = p.produto.nome
            except:
                # Se falhar, excluir este produto também
                p.delete()
                ids_removidos.append(p.id)
                count += 1
    except Exception as e:
        messages.warning(request, f"Aviso durante verificação adicional: {str(e)}")
    
    if count > 0:
        messages.success(
            request, 
            f"Foram removidos {count} produtos inválidos da OS #{ordem.numero}. " +
            f"IDs removidos: {', '.join(map(str, ids_removidos))}"
        )
    else:
        messages.info(request, f"Nenhum produto inválido encontrado na OS #{ordem.numero}")
    
    return redirect('editar_ordem', slug=ordem.slug)

def corrigir_produtos_invalidos_consola():
    """
    Função para ser executada via shell Django para corrigir problemas
    com produtos utilizados sem produto associado.
    
    Uso em shell:
    from ordens.views import corrigir_produtos_invalidos_consola
    corrigir_produtos_invalidos_consola()
    """
    print("Iniciando correção de produtos utilizados inválidos...")
    
    # Buscar produtos sem produto_id
    produtos_invalidos = ProdutoUtilizado.objects.filter(produto_id__isnull=True)
    count = produtos_invalidos.count()
    
    if count == 0:
        print("Nenhum produto inválido encontrado.")
        return
    
    print(f"Encontrados {count} produtos inválidos.")
    
    # Listar ordens afetadas
    ordens_afetadas = list(
        produtos_invalidos.values('ordem_servico__numero').distinct()
    )
    print(f"Ordens afetadas: {[o['ordem_servico__numero'] for o in ordens_afetadas]}")
    
    # Excluir os produtos inválidos
    produtos_invalidos.delete()
    print(f"Produtos inválidos removidos com sucesso!")
    
    # Verificar se ainda há problemas
    try:
        for p in ProdutoUtilizado.objects.all():
            # Verificar se cada objeto tem produto associado
            try:
                nome = p.produto.nome
            except:
                print(f"Produto ID {p.id} ainda tem problemas e será removido.")
                p.delete()
    except Exception as e:
        print(f"Erro durante verificação adicional: {str(e)}")
    
    print("Correção concluída.")
    