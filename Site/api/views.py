from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Profile, Category, Post, Comment
from .serializers import ProfileSerializer, CategorySerializer, PostSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly

class ProfileViewSet(viewsets.ModelViewSet):
    """Представление для профилей пользователей"""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    """Представление для категорий"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class PostViewSet(viewsets.ModelViewSet):
    """Представление для постов"""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__name', 'author__username']
    search_fields = ['title', 'content']
    ordering_fields = ['published', 'author__username', 'likes_count']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Пользователь может лайкнуть пост"""
        post = self.get_object()
        post.likes.add(request.user)
        return Response({'status': 'пост лайкнут'})

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Пользователь может убрать лайк с поста"""
        post = self.get_object()
        post.likes.remove(request.user)
        return Response({'status': 'лайк с поста убран'})

class CommentViewSet(viewsets.ModelViewSet):
    """Представление для комментариев"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
