from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, UserAvatarViewSet

app_name = 'users'

router_v1 = DefaultRouter()

router_v1.register('users', UserViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', UserAvatarViewSet.as_view(), name='user-avatar'),
]
