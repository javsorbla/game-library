from django.urls import path
from .views import GameList, GenreList, PlatformList, MarkPlayedView

urlpatterns = [
    path('games/', GameList.as_view(), name='game_list'),
    path('games/<int:pk>/played/', MarkPlayedView.as_view(), name='game_mark_played'),
    path('genres/', GenreList.as_view(), name='genre_list'),
    path('platforms/', PlatformList.as_view(), name='platform_list'),
]
