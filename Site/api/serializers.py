from rest_framework import serializers
from .models import Profile, Category, Post, Comment
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User"""

    class Meta:
        model = User
        fields = ('id', 'username')

class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'user', 'bio')

class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментария"""
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'created')

class PostSerializer(serializers.ModelSerializer):
    """Сериализатор для поста"""
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    category = serializers.SlugRelatedField(slug_field='name', queryset=Category.objects.all())
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'author', 'title', 'content', 'category', 'published', 'updated', 'comments', 'likes_count')

    def get_likes_count(self, obj):
        return obj.likes.count()

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категории"""
    posts = PostSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'posts')
