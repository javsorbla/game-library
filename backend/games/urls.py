from django.urls import path
from .views import GameList

urlpatterns = [
    path('games/', GameList.as_view(), name='game_list'),
]