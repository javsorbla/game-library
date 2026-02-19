from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Game, Genre, Platform
from .serializers import GameSerializer, GenreSerializer, PlatformSerializer


class GameList(generics.ListCreateAPIView):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # allow filtering by whether the authenticated user has marked the game
        # as played. query param 'played' accepts 'true'/'false'.
        qs = Game.objects.all()
        played = self.request.query_params.get('played')
        if played is not None and self.request.user.is_authenticated:
            flag = played.lower()
            if flag in ('true', '1', 'yes'):
                qs = qs.filter(players=self.request.user)
            elif flag in ('false', '0', 'no'):
                qs = qs.exclude(players=self.request.user)
        return qs


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


class PlatformList(generics.ListAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]

class PlayedList(generics.ListAPIView):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]