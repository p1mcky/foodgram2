import hashlib

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import RecipeFilter, IngredientFilter
from api.serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    TagSerializer,
    IngredintsReadSerializer,
    RecipeReadSerializer
)
from api.pagination import CustomPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from recipes.models import (
    Recipe, Ingredient, Tag, Favorite, ShoppingCart, IngredientsInRecipes
)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredintsReadSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_update(self, serializer):
        instance = serializer.instance
        if self.request.user != instance.author:
            raise PermissionDenied('You are not the author of this recipe')
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            raise PermissionDenied('You are not the author of this recipe')
        instance.delete()

    def toggle_recipe_status(
        self, request, model, **kwargs
    ):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        obj = model.objects.filter(user=request.user, recipe=recipe)

        if request.method == 'POST':
            if obj.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeReadSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    def favorite(self, request, **kwargs):
        return self.toggle_recipe_status(
            request, Favorite,
            user=request.user,
            **kwargs
        )

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated]
            )
    def shopping_cart(self, request, **kwargs):
        return self.toggle_recipe_status(
            request,
            ShoppingCart,
            **kwargs
        )

    @action(
            detail=False, methods=['get'], permission_classes=[IsAuthenticated]
        )
    def download_shopping_cart(self, request, **kwargs):
        file_name = 'shopping_cart.txt'

        ingredients = (
            IngredientsInRecipes.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        file_list = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['total_amount']
            file_list.append(f'{name} - {amount} {unit}')

        response_content = 'Список покупок:\n' + '\n'.join(file_list)
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response


class RecipeShortLink(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        short_link = self.generate_short_link(pk)
        return Response({'short-link': short_link})

    def generate_short_link(self, recipe_id):
        hash_object = hashlib.md5(str(recipe_id).encode())
        short_id = hash_object.hexdigest()[:8]
        base_url = 'https://pimcky-foodgram.hopto.org/s/'
        return f"{base_url}{short_id}"
