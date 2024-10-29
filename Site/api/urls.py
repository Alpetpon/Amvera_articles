from django.urls import include, path
from rest_framework import routers
from .views import ProfileViewSet, CategoryViewSet, PostViewSet, CommentViewSet

router = routers.DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'posts', PostViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
