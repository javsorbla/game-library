from django.db import models
from django.conf import settings

class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    name = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre, related_name="games", blank=True)
    platforms = models.ManyToManyField(Platform, related_name="games", blank=True)
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    image = models.URLField(blank=True, null=True)
    rawg_id = models.IntegerField(unique=True, null=True, blank=True)
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="played_games", blank=True)

    def __str__(self):
        return self.name

    @property
    def genre(self):
        # exposable property kept for backward compatibility
        return ", ".join(self.genres.values_list('name', flat=True))

    @property
    def platform(self):
        return ", ".join(self.platforms.values_list('name', flat=True))


class GameRating(models.Model):
    """
    Per-user rating for a game used by the tier list comparison feature.

    We use a simple Elo-style rating system: every time the user
    chooses one game over another we update both ratings. The rating
    defaults to 1000 for new entries.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    rating = models.FloatField(default=1000)

    class Meta:
        unique_together = ("user", "game")
        ordering = ["-rating"]

    def __str__(self):
        return f"{self.user.username}: {self.game.name} ({self.rating:.1f})"


def update_elo(winner_rating: float, loser_rating: float, k: float = 32):
    """Return tuple of (new_winner_rating, new_loser_rating).

    This is the standard Elo rating update. The constant ``k`` can be
    tuned; 32 is a reasonable default for our purposes.
    """
    expected_win = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loss = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))

    new_win = winner_rating + k * (1 - expected_win)
    new_loss = loser_rating + k * (0 - expected_loss)
    return new_win, new_loss

