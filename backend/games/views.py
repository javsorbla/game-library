from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Game, Genre, Platform, MergeSortSession
from .serializers import GameSerializer, GenreSerializer, PlatformSerializer

from . import mergesort as ms

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


# Merge Sort tier list

def _session_response(state: dict, game_map: dict) -> dict:
    pair = ms.current_pair(state)
    return {
        "finished": state["finished"],
        "done": state["done"],
        "total": state["total"],
        "pair": [game_map[gid] for gid in pair] if pair else None,
        "result": ms._assign_tiers(state["final"]) if state["finished"] else None,
    }


def _game_map(user, ids: list, request) -> dict:
    games = Game.objects.filter(pk__in=ids)
    return {g.pk: GameSerializer(g, context={"request": request}).data for g in games}


class MergeSortStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        played_ids = list(
            Game.objects.filter(players=request.user).values_list("pk", flat=True)
        )
        if len(played_ids) < 2:
            return Response(
                {"detail": "You need at least 2 played games to start a tier list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state = ms.build_initial_state(played_ids)
        MergeSortSession.objects.update_or_create(
            user=request.user,
            defaults={"state": state},
        )
        game_map = _game_map(request.user, played_ids, request)
        return Response(_session_response(state, game_map))


class MergeSortAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session = MergeSortSession.objects.get(user=request.user)
        except MergeSortSession.DoesNotExist:
            return Response(
                {"detail": "No active session. Start a new tier list first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        winner_id = request.data.get("winner")
        loser_id = request.data.get("loser")
        if not winner_id or not loser_id:
            return Response(
                {"detail": "winner and loser are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            state = ms.answer(session.state, int(winner_id), int(loser_id))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        session.state = state
        session.save()

        all_ids = (
            state.get("final")
            or state["left"]
            + state["right"]
            + state["result"]
            + [i for sub in state["pending"] for i in sub]
        )
        game_map = _game_map(request.user, all_ids, request)
        return Response(_session_response(state, game_map))


class MergeSortStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            session = MergeSortSession.objects.get(user=request.user)
        except MergeSortSession.DoesNotExist:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)

        state = session.state
        all_ids = (
            state.get("final")
            or state["left"]
            + state["right"]
            + state["result"]
            + [i for sub in state["pending"] for i in sub]
        )
        game_map = _game_map(request.user, all_ids, request)
        return Response(_session_response(state, game_map))