from django.db import models

from apps.users.models import CustomUser


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Task(TimeStampedModel):
    TASK_STATUS_CHOICES = [
        ('OP', 'Open'),
        ('IP', 'In progress'),
        ('PA', 'Paused'),
        ('CO', 'Complete'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=100, choices=TASK_STATUS_CHOICES, default='OP')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    @property
    def get_task_total_duration(self):
        total_duration = sum([
            task.duration if task.duration else 0 for task in self.task_duration.all()
        ])
        return total_duration // 60


class Comment(TimeStampedModel):
    text = models.TextField()
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(CustomUser, related_name='comments', on_delete=models.CASCADE)


class TaskDuration(TimeStampedModel):
    task = models.ForeignKey(Task, related_name='task_duration', on_delete=models.CASCADE)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start_working_datetime = models.DateTimeField()
    stop_working_datetime = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    timer_on = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.task.id} start on {self.start_working_datetime}, duration {self.duration} s.'
