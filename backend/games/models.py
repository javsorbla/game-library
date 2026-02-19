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

