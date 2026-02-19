from rest_framework import serializers
from .models import Game, Genre, Platform


class GameSerializer(serializers.ModelSerializer):
    genre = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = '__all__'

    def get_genre(self, obj):
        return obj.genre

    def get_platform(self, obj):
        return obj.platform

    def create(self, validated_data):
        # handle comma-separated genre/platform if provided
        genres_data = self.initial_data.get('genre')
        platforms_data = self.initial_data.get('platform')
        game = super().create(validated_data)
        if genres_data:
            names = [n.strip() for n in genres_data.split(',') if n.strip()]
            for name in names:
                genre_obj, _ = Genre.objects.get_or_create(name=name)
                game.genres.add(genre_obj)
        if platforms_data:
            names = [n.strip() for n in platforms_data.split(',') if n.strip()]
            for name in names:
                plat_obj, _ = Platform.objects.get_or_create(name=name)
                game.platforms.add(plat_obj)
        return game

    def update(self, instance, validated_data):
        genre_str = self.initial_data.get('genre')
        platform_str = self.initial_data.get('platform')
        game = super().update(instance, validated_data)
        if genre_str is not None:
            game.genres.clear()
            for name in [n.strip() for n in genre_str.split(',') if n.strip()]:
                genre_obj, _ = Genre.objects.get_or_create(name=name)
                game.genres.add(genre_obj)
        if platform_str is not None:
            game.platforms.clear()
            for name in [n.strip() for n in platform_str.split(',') if n.strip()]:
                plat_obj, _ = Platform.objects.get_or_create(name=name)
                game.platforms.add(plat_obj)
        return game


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = '__all__'

