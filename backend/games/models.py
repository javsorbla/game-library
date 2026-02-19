from django.db import models


class Game(models.Model):
    name = models.CharField(max_length=200)
    genre = models.CharField(max_length=200)
    platform = models.CharField(max_length=200)
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    image = models.URLField(blank=True, null=True)
    rawg_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name