from django.contrib import admin
from .models import Profile, Category, Post, Comment

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Post)
admin.site.register(Comment)
