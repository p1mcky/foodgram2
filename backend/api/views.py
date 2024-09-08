import hashlib

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (IngredintsReadSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer, RecipeSerializer,
                             TagSerializer, CustomUserSerializer,
                             SubscriptionsSerializer, AvatarSerializer)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class UserViewSet(UserViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = self.request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = self.request.user
        author = get_object_or_404(User, id=kwargs['id'])

        if request.method == 'POST':
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого автора!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscribe.objects.create(user=user, author=author)
            serializer = SubscriptionsSerializer(
                author, context={'request': request}
            )
            return Response(
                data=serializer.data, status=status.HTTP_201_CREATED
            )
        try:
            subscription = Subscribe.objects.get(user=user, author=author)
        except Subscribe.DoesNotExist:
            return Response(
                {'detail': 'Вы не подписаны на этого автора!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAvatarViewSet(APIView):
    parser_classes = [JSONParser]
    serializer_class = AvatarSerializer
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        user = request.user
        if 'avatar' not in request.data:
            return Response({'error': 'Avatar field is required'}, status=400)
        serializer = self.serializer_class(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request, **kwargs):
        file_name = 'shopping_cart.txt'

        ingredients = (
            IngredientInRecipe.objects
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
        base_url = settings.SHORT_LINK_BASE_URL
        return f"{base_url}{short_id}"
