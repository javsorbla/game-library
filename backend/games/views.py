from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Game, Genre, Platform, TournamentSession
from .serializers import GameSerializer, GenreSerializer, PlatformSerializer
from . import tournament as t

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


def _build_response(state: dict, request) -> dict:
    """Single place that turns a state dict into the API response."""
    game_map = {
        g.pk: GameSerializer(g, context={"request": request}).data
        for g in Game.objects.filter(pk__in=t.all_game_ids(state))
    }
    pair = t.current_pair(state)
    ranking = None
    if state.get("ranking"):
        ranking = [{**game_map[r["id"]], "tier": r["tier"], "rank": r["rank"], "wins": r["wins"]}
                   for r in state["ranking"]]
    return {
        "phase":      state["phase"],
        "done":       state["done"],
        "total":      state["total"],
        "pair":       [game_map[gid] for gid in pair] if pair else None,
        "group_info": t.current_group_info(state),
        "ranking":    ranking,
    }


class TournamentStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        played = Game.objects.filter(players=request.user).prefetch_related("genres")
        if played.count() < 2:
            return Response(
                {"detail": "You need at least 2 played games to start a tier list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        games_with_genre = [
            (game.pk, game.genres.first().name if game.genres.first() else "")
            for game in played
        ]
        state = t.build_initial_state(games_with_genre)
        TournamentSession.objects.update_or_create(user=request.user, defaults={"state": state})
        return Response(_build_response(state, request))


class TournamentAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session = TournamentSession.objects.get(user=request.user)
        except TournamentSession.DoesNotExist:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)

        winner_id = request.data.get("winner")
        loser_id  = request.data.get("loser")
        if not winner_id or not loser_id:
            return Response({"detail": "winner and loser are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            state = t.answer(session.state, int(winner_id), int(loser_id))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        session.state = state
        session.save()
        return Response(_build_response(state, request))


class TournamentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            session = TournamentSession.objects.get(user=request.user)
        except TournamentSession.DoesNotExist:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)
        return Response(_build_response(session.state, request))