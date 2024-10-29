from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """Расширение модели User для добавления дополнительных полей"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

class Category(models.Model):
    """Модель категории для постов"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    """Модель поста"""
    author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='posts', on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    published = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-published']

    def __str__(self):
        return self.title

class Comment(models.Model):
    """Модель комментария"""
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f'Комментарий от {self.author.username} на {self.post.title}'
