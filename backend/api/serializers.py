from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            Tag)
from users.models import User, Subscribe


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        if (self.context.get('request')
           and not self.context['request'].user.is_anonymous):
            return Subscribe.objects.filter(user=self.context['request'].user,
                                            author=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredintsReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'author',
            'image',
            'name',
            'text',
            'cooking_time'
        )
        extra_kwargs = {
            'name': {'required': True},
            'image': {'required': True},
            'cooking_time': {'required': True},
        }

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise serializers.ValidationError('Ingredients are required')

        list_of_ingredients = []
        for ingredient in ingredients:
            if ingredient['id'] in list_of_ingredients:
                raise serializers.ValidationError('Ingredient already exists')
            list_of_ingredients.append(ingredient['id'])
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Amount must be greater than 0'
                )
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise serializers.ValidationError('Tags are required')
        list_of_tags = []
        for tag in tags:
            if tag.id in list_of_tags:
                raise serializers.ValidationError('Tag already exists')
            list_of_tags.append(tag.id)
        return value

    def validate_cooking_time(self, value):
        if value is None or value < 1:
            raise serializers.ValidationError(
                'Cooking time must be greater than 0'
            )
        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        self.set_recipe_tags(recipe, tags)
        self.set_recipe_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        tags = validated_data.pop('tags', None)
        if tags is not None:
            self.set_recipe_tags(instance, tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
            self.set_recipe_ingredients(instance, ingredients)

        return instance

    def set_recipe_tags(self, recipe, tags):
        recipe.tags.set(tags)

    def set_recipe_ingredients(self, recipe, ingredients):
        ingredient_in_recipes = []
        for ingredient_data in ingredients:
            amount = ingredient_data.get('amount')
            ingredient_id = ingredient_data.get('id').id
            ingredient_in_recipes.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient_id=ingredient_id,
                    amount=amount
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_in_recipes)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class RecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='ingredient_in_recipes'
    )
    author = CustomUserSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        ordering = ['id']

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        if (self.context.get('request')
           and not self.context['request'].user.is_anonymous):
            return Subscribe.objects.filter(user=self.context['request'].user,
                                            author=obj).exists()
        return False

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', None)
        recipes = Recipe.objects.filter(author=obj)

        if limit is not None:
            try:
                limit = int(limit)
                if limit < 0:
                    raise serializers.ValidationError(
                        'recipes_limit must be a non-negative integer.'
                    )
                recipes = recipes[:limit]
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit must be an integer.'
                )

        serializer = RecipeReadSerializer(
            recipes, many=True, context={'request': request}
        )
        return serializer.data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError('Avatar cannot be empty')
        return value
