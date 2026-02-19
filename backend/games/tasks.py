import requests
import random
from games.models import Game
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
        game, created = Game.objects.update_or_create(
            rawg_id=item['id'],
            defaults={
                'name': item['name'],
                'genre': ', '.join([g['name'] for g in item.get('genres', [])]),
                'platform': ', '.join([p['platform']['name'] for p in item.get('platforms', [])]),
                'rating': item.get('rating'),
                'image': item.get('background_image'),
            }
        )
        if created:
            print(f"Added: {game.name}")
        else:
            print(f"Updated: {game.name}")
