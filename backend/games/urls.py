from django.urls import path
from .views import GameList, GenreList, PlatformList, MarkPlayedView, TierPairView, TierSubmitView, TierRankingsView

urlpatterns = [
    path('games/', GameList.as_view(), name='game_list'),
    path('games/<int:pk>/played/', MarkPlayedView.as_view(), name='game_mark_played'),
    path('genres/', GenreList.as_view(), name='genre_list'),
    path('platforms/', PlatformList.as_view(), name='platform_list'),

    path('games/tier/pair/', TierPairView.as_view(), name='tier_pair'),
    path('games/tier/submit/', TierSubmitView.as_view(), name='tier_submit'),
    path('games/tier/rankings/', TierRankingsView.as_view(), name='tier_rankings'),
]
