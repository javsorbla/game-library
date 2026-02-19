from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Game, Genre, Platform
from .serializers import GameSerializer, GenreSerializer, PlatformSerializer


class GameList(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]


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