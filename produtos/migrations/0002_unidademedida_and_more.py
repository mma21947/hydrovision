# Generated by Django 5.2 on 2025-04-10 12:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0005_comentario_data_resolucao_and_more'),
        ('produtos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UnidadeMedida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sigla', models.CharField(max_length=5, unique=True, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome da Unidade')),
            ],
            options={
                'verbose_name': 'Unidade de Medida',
                'verbose_name_plural': 'Unidades de Medida',
                'ordering': ['nome'],
            },
        ),
        migrations.AlterField(
            model_name='movimentacaoestoque',
            name='ordem_servico',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentacoes_estoque', to='ordens.ordemservico'),
        ),
        migrations.AlterField(
            model_name='movimentacaoestoque',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimentacoes_usuario', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='produto',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='produtos', to='produtos.categoria'),
        ),
        migrations.AlterField(
            model_name='produto',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='produtos', to='produtos.unidademedida', verbose_name='Unidade'),
        ),
    ]
