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
        # authenticate using the test client session
        logged_in = self.client.login(username='test', password='test')
        self.assertTrue(logged_in, "Unable to log in with session auth")

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
        # basic list should still work but now returns paginated data
        Game.objects.create(name="A Game")
        url = reverse('game_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # expect pagination envelope with `results` key
        self.assertIn('results', res.data)
        self.assertIsInstance(res.data['results'], list)
        self.assertEqual(len(res.data['results']), 1)

    def test_played_filter_parameter(self):
        g1 = Game.objects.create(name="G1")
        g2 = Game.objects.create(name="G2")
        g1.players.add(self.user)
        url = reverse('game_list')
        res = self.client.get(url + '?played=true')
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], g1.id)

        res = self.client.get(url + '?played=false')
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], g2.id)

    def test_mark_and_unmark_played(self):
        game = Game.objects.create(name="Playable")
        mark_url = reverse('game_mark_played', args=[game.id])

        # initially not played
        res = self.client.get(reverse('game_list'))
        first = res.data.get('results', [])[0]
        self.assertFalse(first.get('is_played', False))

        # post to mark as played
        res = self.client.post(mark_url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.get('is_played'))
        game.refresh_from_db()
        self.assertTrue(game.players.filter(pk=self.user.pk).exists())

        # delete to unmark
        res = self.client.delete(mark_url)
        self.assertEqual(res.status_code, 204)
        game.refresh_from_db()
        self.assertFalse(game.players.filter(pk=self.user.pk).exists())

    def test_pagination_limits_and_count(self):
        # create a handful of games to test default page size
        for i in range(25):
            Game.objects.create(name=f"Game {i}")
        url = reverse('game_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('results', res.data)
        self.assertEqual(len(res.data['results']), 20)  # page size default
        self.assertEqual(res.data['count'], 25)
        # request second page
        res2 = self.client.get(url + '?page=2')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(len(res2.data['results']), 5)

    def test_alphabetical_ordering(self):
        # insert in reverse alphabetical order
        Game.objects.create(name="Zebra")
        Game.objects.create(name="Alpha")
        Game.objects.create(name="Middle")
        url = reverse('game_list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', [])
        # expect names sorted ascending
        names = [g['name'] for g in results]
        self.assertEqual(names, sorted(names))

    def test_genre_platform_query_parameters(self):
        # set up games with various relationships
        g1 = Genre.objects.create(name="Action")
        g2 = Genre.objects.create(name="Puzzle")
        p1 = Platform.objects.create(name="PC")
        p2 = Platform.objects.create(name="Switch")
        game1 = Game.objects.create(name="Alpha")
        game1.genres.add(g1)
        game1.platforms.add(p1)
        game2 = Game.objects.create(name="Beta")
        game2.genres.add(g2)
        game2.platforms.add(p2)
        url = reverse('game_list')
        # genre filter
        res = self.client.get(url + '?genre=Action')
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], game1.id)
        # platform filter
        res = self.client.get(url + '?platform=Switch')
        self.assertEqual(res.status_code, 200)
        results = res.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], game2.id)

