from django.contrib import admin
from .models import Game, Genre, Platform, GameRating


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'rawg_id')
    search_fields = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(GameRating)
class GameRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'rating')
    list_filter = ('user',)
    search_fields = ('game__name', 'user__username')

