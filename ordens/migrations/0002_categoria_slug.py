# Generated by Django 5.2 on 2025-04-07 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='slug',
            field=models.SlugField(blank=True, max_length=150, unique=True, verbose_name='Slug'),
        ),
    ]
