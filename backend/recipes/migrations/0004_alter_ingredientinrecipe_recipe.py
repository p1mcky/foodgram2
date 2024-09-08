# Generated by Django 3.2.15 on 2024-09-08 11:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20240908_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient_in_recipes', to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]
