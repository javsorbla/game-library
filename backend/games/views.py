from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Game, Genre, Platform
from .serializers import GameSerializer, GenreSerializer, PlatformSerializer


class GamePagination(PageNumberPagination):
    page_size = 21
    page_size_query_param = 'page_size'
    max_page_size = 100


class GameList(generics.ListCreateAPIView):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = GamePagination

    def get_queryset(self):
        # base queryset ordered alphabetically
        qs = Game.objects.all().order_by('name')

        # played filtering
        played = self.request.query_params.get('played')
        if played is not None and self.request.user.is_authenticated:
            flag = played.lower()
            if flag in ('true', '1', 'yes'):
                qs = qs.filter(players=self.request.user)
            elif flag in ('false', '0', 'no'):
                qs = qs.exclude(players=self.request.user)

        # genre/platform filters
        genre = self.request.query_params.get('genre')
        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        platform = self.request.query_params.get('platform')
        if platform:
            qs = qs.filter(platforms__name__iexact=platform)

        # distinct in case multiple m2m relationships produced duplicate rows
        return qs.distinct()


class MarkPlayedView(APIView):
    permission_classes = [IsAuthenticated]

    # marks a game as played
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        game.players.add(request.user)
        serializer = GameSerializer(game, context={'request': request})
        return Response(serializer.data)

    # marks a game as not played
    def delete(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        game.players.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenreList(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class PlatformList(generics.ListAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None