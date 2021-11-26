from django.contrib import admin
from apps.tasks.models import Task, Comment, TaskDuration

admin.site.register(Task)
admin.site.register(TaskDuration)
admin.site.register(Comment)
