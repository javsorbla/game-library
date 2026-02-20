from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Game, Genre, Platform, GameRating
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
        GameRating.objects.get_or_create(user=request.user, game=game)
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


class TierPairView(APIView): # Return a champion/challenger pair using a Facemash-style flow
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = list(Game.objects.filter(players=request.user))
        if len(qs) < 2:
            return Response(
                {"detail": "not enough played games for tiering"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = request.session
        champ = None
        champ_id = session.get("facemash_champion")
        if champ_id:
            try:
                champ = Game.objects.get(pk=champ_id, players=request.user)
            except Game.DoesNotExist:
                champ = None

        import random

        if not champ:
            champ = random.choice(qs)
            session["facemash_champion"] = champ.id
            session.modified = True

        # choose a challenger that's different from champion
        choices = [g for g in qs if g.id != champ.id]
        challenger = random.choice(choices)

        data = {
            "champion": GameSerializer(champ, context={"request": request}).data,
            "challenger": GameSerializer(challenger, context={"request": request}).data,
        }
        return Response(data)


class TierSubmitView(APIView): # Accept a comparison result and update the stored Elo ratings.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        winner_id = request.data.get("winner")
        loser_id = request.data.get("loser")
        if not winner_id or not loser_id:
            return Response({"detail": "winner and loser required"}, status=status.HTTP_400_BAD_REQUEST)

        winner = get_object_or_404(Game, pk=winner_id, players=request.user)
        loser = get_object_or_404(Game, pk=loser_id, players=request.user)
        from .models import GameRating, update_elo

        wr, _ = GameRating.objects.get_or_create(user=request.user, game=winner)
        lr, _ = GameRating.objects.get_or_create(user=request.user, game=loser)

        new_wr, new_lr = update_elo(wr.rating, lr.rating)
        wr.rating = new_wr
        lr.rating = new_lr
        wr.save()
        lr.save()

        # update session champion if it lost
        session = request.session
        champ_id = session.get("facemash_champion")
        if champ_id and str(champ_id) == str(loser_id):
            session["facemash_champion"] = winner_id
            session.modified = True

        return Response({"winner_rating": wr.rating, "loser_rating": lr.rating})

class TierRankingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import GameRating

        ratings = GameRating.objects.filter(user=request.user).select_related("game").order_by("-rating")
        data = []
        for r in ratings:
            serialized = GameSerializer(r.game, context={"request": request}).data
            serialized["tier_rating"] = r.rating
            data.append(serialized)
        return Response(data)


class PlatformList(generics.ListAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None