# Generated by Django 5.2 on 2025-04-07 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='codigo',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='Código'),
        ),
    ]
