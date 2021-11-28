from django.core.mail import EmailMessage
from typing import List, Union
from collections.abc import Iterable

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


def send_user_email(emails: Union[List[str], str], message_type: str):

    if isinstance(emails, str) or not isinstance(emails, Iterable):
        emails = [emails]

    email = EmailMessage(
        email_data[message_type]['subject'],
        email_data[message_type]['message'],
        to=emails,
    )
    email.send()


def get_all_commentators(task_id: int) -> List[str]:
    task = Task.objects.get(id=task_id)
    comments = Comment.objects.select_related('author').filter(task=task)
    email_list = set(comment.author.email for comment in comments)

    return list(email_list)
