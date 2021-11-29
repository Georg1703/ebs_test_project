from datetime import datetime, timezone
import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tasks.models import Task, Comment, TaskDuration
from apps.users.models import CustomUser


class TaskViewSetTest(APITestCase):

    def setUp(self) -> None:
        self.user = CustomUser.objects.create(
            email='aaa.asdas@gmail.com',
            password='1234'
        )
        self.user2 = CustomUser.objects.create(
            email='aaa.asdas@gmail.cov',
            password='1234'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.api_authentification()

    def api_authentification(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def insert_one_task(self, title: str, description: str):
        Task.objects.create(
            owner=self.user,
            title=title,
            description=description,
        )

    def test_task_create(self):
        url = '/tasks/'
        data = {
            'title': 'Task title',
            'description': 'Task description',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(json.loads(response.content), {
            'id': 1,
            'title': 'Task title',
            'task_duration': '0'
        })

    def test_task_list(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [{
                                'id': 1,
                                'title': 'Task title',
                                'task_duration': '0',
                            }]}
                         )

    def test_task_retrieve(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/1/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
            'id': 1,
            'title': 'Task title',
            'description': 'Some description',
            'status': 'OP',
            'owner': 1,
        })

    def test_my_tasks(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/mine/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [{
            'id': 1,
            'title': 'Task title',
        }])

    def test_task_completed_empty(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/completed/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [])

    def test_task_completed_one(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/completed/'
        task = Task.objects.get()
        task.status = 'CO'
        task.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [{
            'id': 1,
            'title': 'Task title',
        }])

    def test_set_owner_fail(self):
        url = '/tasks/11/owner/11/'
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.loads(response.content), {'detail': 'Not found.'})

    def test_set_owner_success(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/1/owner/2/'
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {'detail': 'success',})

    def test_remove_task(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.all().count(), 0)

    def test_add_comment(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/1/comments/'
        data = {
            'task': 1,
            'text': 'some comment for task here'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(json.loads(response.content), {
            'id': 1,
            'text': 'some comment for task here',
        })

    def test_list_comment(self):
        self.insert_one_task('Task title', 'Some description')
        task = Task.objects.get()
        Comment.objects.create(
            text='Some comment text',
            task=task,
            author=self.user
        )

        url = f'/tasks/1/comments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_by_title(self):
        self.insert_one_task('different', 'task description')
        self.insert_one_task('task text', 'task description')

        url = f'/tasks/?search=ta'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [{
                                'id': 2,
                                'title': 'task text',
                                'task_duration': '0',
                            }]}
                         )


class TaskDurationViewSetTest(TaskViewSetTest):

    def test_start_timer(self):
        self.insert_one_task('Task title', 'task description')
        url = '/tasks/1/timer-start/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskDuration.objects.count(), 1)
        self.assertEqual(TaskDuration.objects.get().timer_on, True)

        response = self.client.post(url, data)

        self.assertEqual(json.loads(response.content), {
            'detail': 'Timer for task is running already',
        })

    def test_stop_timer(self):
        self.insert_one_task('Task title', 'task description')
        task = Task.objects.get()
        TaskDuration.objects.create(
            owner=self.user,
            task=task,
            start_working_datetime=datetime.now(timezone.utc)
        )
        url = '/tasks/1/timer-stop/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskDuration.objects.get().timer_on, False)

    def test_get_timer_list(self):
        self.insert_one_task('Task title', 'task description')
        self.insert_one_task('Task title', 'task description')
        task = Task.objects.get(id=1)
        task2 = Task.objects.get(id=2)
        TaskDuration.objects.bulk_create([
            TaskDuration(owner=self.user, task=task, start_working_datetime=datetime.now(timezone.utc)),
            TaskDuration(owner=self.user2, task=task2, start_working_datetime=datetime.now(timezone.utc)),
        ])

        url = '/tasks/timer_list/?task=1'
        response = self.client.get(url)
        self.assertEqual(len(json.loads(response.content)), 1)

    def test_add_time_on_specific_date(self):
        self.insert_one_task('Task title', 'task description')
        task = Task.objects.get()
        url = '/tasks/1/add-time/'
        data = {
            'start_working_datetime': '2020-6-12T16:12:34',
            'duration': 60
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskDuration.objects.all().count(), 1)

    def test_get_last_month_time(self):
        self.insert_one_task('Task', 'task description')
        url = '/tasks/time-last-month/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_top_tasks_last_month(self):
        self.insert_one_task('Task', 'task description')
        url = '/tasks/top-last-month/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)





