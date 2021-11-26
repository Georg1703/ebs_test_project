import datetime
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
        self.assertEqual(json.loads(response.content), [{
            'id': 1,
            'task_duration': '0',
            'title': 'Task title'
        }])

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
        url = '/tasks/my_tasks/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [{
            'id': 1,
            'title': 'Task title',
        }])

    def test_task_completed_empty(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/completed_tasks/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [])

    def test_task_completed_one(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/completed_tasks/'
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
        url = '/tasks/set_task_owner/'
        data = {
            'task': 11,
            'owner': 11,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
            'owner': ['Owner not found'],
            'task': ['Task not found'],
        })

    def test_set_owner_success(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/set_task_owner/'
        data = {
            'task': 1,
            'owner': 2,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {
            'owner': 2,
            'task': 1,
        })

    def test_remove_task(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/1/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {'message': 'Order deleted successfully'})

    def test_add_comment(self):
        self.insert_one_task('Task title', 'Some description')
        url = '/tasks/comments/'
        data = {
            'task': 1,
            'text': 'some comment for task here'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(json.loads(response.content), {
            'id': 1,
            'text': 'some comment for task here',
            'task': 1
        })

    def test_list_comment(self):
        self.insert_one_task('Task title', 'Some description')
        task = Task.objects.get()
        Comment.objects.create(
            text='Some comment text',
            task=task,
            author=self.user
        )

        url = f'/tasks/comments/?task={task.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [{
            'id': 1,
            'text': 'Some comment text',
            'task': 1
        }])

    def test_search_by_title(self):
        self.insert_one_task('different', 'task description')
        self.insert_one_task('task text', 'task description')

        url = f'/tasks/?search=ta'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [{
            'id': 2,
            'task_duration': '0',
            'title': 'task text',
        }])


class TaskViewSetTest(TaskViewSetTest):

    def test_start_timer(self):
        self.insert_one_task('Task title', 'task description')
        url = '/tasks/timer_start/'
        data = {'task': 1}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TaskDuration.objects.count(), 1)
        task = TaskDuration.objects.get()
        self.assertEqual(task.on, True)

        response = self.client.post(url, data)

        self.assertEqual(json.loads(response.content), {
            'detail': 'Timer for task is running already',
        })

    def test_start_timer(self):
        self.insert_one_task('Task title', 'task description')
        task = Task.objects.get()
        TaskDuration.objects.create(
            owner=self.user,
            task=task,
            start_working_datetime=datetime.datetime.now()
        )
        url = '/tasks/timer_stop/'
        data = {'task': 1}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task = TaskDuration.objects.get()
        self.assertEqual(task.timer_on, False)

    def test_get_timer_list(self):
        self.insert_one_task('Task title', 'task description')
        self.insert_one_task('Task title', 'task description')
        task = Task.objects.get(id=1)
        task2 = Task.objects.get(id=2)
        TaskDuration.objects.bulk_create([
            TaskDuration(owner=self.user, task=task, start_working_datetime=datetime.datetime.now()),
            TaskDuration(owner=self.user2, task=task2, start_working_datetime=datetime.datetime.now()),
        ])

        url = '/tasks/timer_list/?task=1'
        response = self.client.get(url)
        self.assertEqual(len(json.loads(response.content)), 1)

    def test_get_last_month_time(self):
        self.insert_one_task('Task', 'task description')
        url = '/tasks/get_last_month_time/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_top_tasks_last_month(self):
        self.insert_one_task('Task', 'task description')
        url = '/tasks/get_top_tasks_last_month/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)





