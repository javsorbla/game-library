import requests
import random
from games.models import Game, Genre, Platform
from django.conf import settings
from background_task import background


@background(schedule=0)
def fetch_games(batch_size=10):
    page = random.randint(1, 50)
    api_key = settings.RAWG_API_KEY
    url = f"https://api.rawg.io/api/games?key={api_key}&page={page}&page_size={batch_size}"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return

    data = response.json()
    for item in data.get('results', []):
        defaults = {
            'name': item['name'],
            'rating': item.get('rating'),
            'image': item.get('background_image'),
        }
        game, created = Game.objects.update_or_create(
            rawg_id=item['id'],
            defaults=defaults,
        )

        # sync genres, always clear existing relations to match API result
        genre_names = [g.get('name', '').strip() for g in item.get('genres', []) if g.get('name')]
        game.genres.clear()
        for name in set(genre_names):
            genre_obj, _ = Genre.objects.get_or_create(name=name)
            game.genres.add(genre_obj)

        # sync platforms similarly
        platform_names = [p['platform'].get('name', '').strip() for p in item.get('platforms', []) if p.get('platform')]
        game.platforms.clear()
        for name in set(platform_names):
            plat_obj, _ = Platform.objects.get_or_create(name=name)
            game.platforms.add(plat_obj)

        if created:
            print(f"Added: {game.name}")
        else:
            print(f"Updated: {game.name}")

