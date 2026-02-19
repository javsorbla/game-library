from django.core.management.base import BaseCommand
from background_task.models import Task
from games.tasks import fetch_games


class Command(BaseCommand):
    help = "Ensure a recurring fetch_games task is scheduled."

    def handle(self, *args, **options):
        # if a job already exists with the desired repeat interval don't add
        existing = Task.objects.filter(task_name="games.tasks.fetch_games", repeat=300)
        if existing.exists():
            self.stdout.write("fetch_games already scheduled")
            return
        fetch_games(repeat=300)
