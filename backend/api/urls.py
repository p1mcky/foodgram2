from django.urls import include, path
from rest_framework import routers

from api import views

router_v1 = routers.DefaultRouter()

router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register(
    'ingredients', views.IngredientViewSet, basename='ingredients'
)
router_v1.register(
    r'recipes', views.RecipeViewSet, basename='recipes'
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path(
        'recipes/<int:pk>/get-link/',
        views.RecipeShortLink.as_view(),
        name='recipe-get-link'
    ),
]
