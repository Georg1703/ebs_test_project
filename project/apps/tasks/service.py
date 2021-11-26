from django.core.mail import EmailMessage
from typing import List

from .models import Task, Comment

email_data = {
    'comment': {
        'subject': 'New comment to your task',
        'message': 'Hello, new comment assigned to your task!!!'
    },
    'new_task': {
        'subject': 'New task assigned',
        'message': 'Hello, new task assigned to you!!!'
    },
    'completed': {
        'subject': 'Task completed',
        'message': 'The task you commented on has been changed to the complete state!!!'
    }
}


def send_user_email(user_email: str, type: str):
    email = EmailMessage(
        email_data[type]['subject'],
        email_data[type]['message'],
        to=[*user_email],
    )
    email.send()


def get_all_comenters(task_id: int) -> List[str]:
    task = Task.objects.get(id=task_id)
    comments = Comment.objects.select_related('author').filter(task=task)
    email_list = set(comment.author.email for comment in comments)

    return email_list