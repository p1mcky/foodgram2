from django.contrib import admin

from recipes.models import Ingredient, Recipe, Tag

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
