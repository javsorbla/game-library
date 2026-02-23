from django.contrib import admin
from .models import Game, Genre, Platform, MergeSortSession


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


@admin.register(MergeSortSession)
class MergeSortSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    readonly_fields = ('state', 'created_at', 'updated_at')

