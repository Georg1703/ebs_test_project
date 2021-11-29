from datetime import datetime, timezone
import random

from django.core.management.base import BaseCommand, CommandError
import lorem

from apps.tasks.models import Task, TaskDuration
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = 'Insert initial data (25000 rows in Task table and 50000 in TaskDuration table)'

    def insert_tasks(self):

        task_list = [Task(
            owner=self.user,
            title=lorem.sentence(),
            description=lorem.paragraph()
        ) for _ in range(25000)]

        Task.objects.bulk_create(task_list)

    def insert_task_duration(self):
        task_id_list = tuple(Task.objects.all().values_list('id', flat=True))

        task_time_list = [TaskDuration(
            owner=self.user,
            task_id=random.choice(task_id_list),
            start_working_datetime=datetime.now(timezone.utc),
            duration=random.randint(60, 24000)
        ) for _ in range(50000)]

        TaskDuration.objects.bulk_create(task_time_list)

    def handle(self, *args, **options):
        self.user = CustomUser.objects.first()
        if not self.user:
            raise CommandError('There must exist at least one user')

        self.insert_tasks()
        self.insert_task_duration()
        self.stdout.write(self.style.SUCCESS('Successfully'))