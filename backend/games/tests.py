from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Game, Genre, Platform
from .serializers import GameSerializer
from .tasks import fetch_games

import requests

class GenrePlatformModelTests(TestCase):
    def test_genre_platform_creation(self):
        g1 = Genre.objects.create(name="Action")
        p1 = Platform.objects.create(name="PC")
        game = Game.objects.create(name="Test Game")
        game.genres.add(g1)
        game.platforms.add(p1)

        self.assertEqual(game.genre, "Action")
        self.assertEqual(game.platform, "PC")

        serialized = GameSerializer(game)
        data = serialized.data
        # should include computed string fields
        self.assertEqual(data['genre'], "Action")
        self.assertEqual(data['platform'], "PC")

    def test_serializer_create_parses_strings(self):
        payload = {"name": "Another", "genre": "Shooter, RPG", "platform": "PS5"}
        serializer = GameSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        game = serializer.save()
        self.assertEqual(game.genres.count(), 2)
        self.assertEqual(game.platforms.count(), 1)
        self.assertTrue(Genre.objects.filter(name="Shooter").exists())
        self.assertTrue(Genre.objects.filter(name="RPG").exists())
        self.assertTrue(Platform.objects.filter(name="PS5").exists())

class FetchGamesTaskTests(TestCase):
    def test_fetch_creates_genres_and_platforms_only_once(self):
        # mock requests.get to return predetermined payload
        class DummyResponse:
            status_code = 200
            def json(self):
                return {
                    'results': [
                        {
                            'id': 123,
                            'name': 'Game One',
                            'genres': [{'name': 'Action'}, {'name': 'RPG'}],
                            'platforms': [{'platform': {'name': 'PC'}}],
                            'rating': 4.5,
                            'background_image': 'http://img',
                        }
                    ]
                }
        original_get = requests.get
        requests.get = lambda url: DummyResponse()
        try:
            # call the underlying function directly, bypassing background proxy
            fetch_games.task_function(batch_size=1)
            fetch_games.task_function(batch_size=1)
        finally:
            requests.get = original_get

        # only one game should exist
        self.assertEqual(Game.objects.count(), 1)
        game = Game.objects.first()
        self.assertEqual(game.name, 'Game One')
        # genre and platform should be created once
        self.assertEqual(Genre.objects.filter(name='Action').count(), 1)
        self.assertEqual(Genre.objects.filter(name='RPG').count(), 1)
        self.assertEqual(Platform.objects.filter(name='PC').count(), 1)
        # relationships should not duplicate
        self.assertEqual(game.genres.count(), 2)
        self.assertEqual(game.platforms.count(), 1)

class ApiEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='test', password='test')
        response = self.client.post(reverse('token_obtain_pair'), {'username': 'test', 'password': 'test'}, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_genre_list_endpoint(self):
        Genre.objects.create(name="Action")
        url = reverse('genre_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) >= 1)

    def test_platform_list_endpoint(self):
        Platform.objects.create(name="PC")
        url = reverse('platform_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data) >= 1)

    def test_game_list_endpoint(self):
        Game.objects.create(name="A Game")
        url = reverse('game_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)

