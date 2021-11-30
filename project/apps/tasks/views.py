from datetime import datetime, timezone, timedelta

from rest_framework import viewsets, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.utils import no_body

from .models import Task, Comment, TaskDuration
from apps.users.models import CustomUser
from .service import send_user_email, get_all_commentators
from .serializers import (
    ListTaskSerializer,
    RetrieveTaskSerializer,
    CommentSerializer,
    AddTimeOnSpecificDateSerializer
)


class TaskViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Task.objects.all()
    serializer_class = ListTaskSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('title',)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RetrieveTaskSerializer
        return ListTaskSerializer

    @action(detail=False, methods=['get'], url_path='mine')
    def my_tasks(self, request):
        tasks = Task.objects.filter(owner=request.user).values('id', 'title')
        return Response(tasks)

    @action(detail=False, methods=['get'], url_path='completed')
    def completed_tasks(self, request):
        tasks = Task.objects.filter(status='CO').values('id', 'title')
        return Response(tasks)

    @swagger_auto_schema(request_body=no_body)
    @action(detail=True, methods=['patch'], url_path=r'owner/(?P<owner_id>\d+)')
    def set_task_owner(self, request, pk=None, owner_id=None):
        task = self.get_object()
        owner = get_object_or_404(CustomUser.objects.all(), pk=owner_id)
        task.owner = owner
        task.save()
        send_user_email(request.user.email, 'new_task')
        return Response({'detail': 'success'})

    @swagger_auto_schema(request_body=no_body)
    @action(detail=True, methods=['patch'], url_path='complete')
    def set_status_completed(self, request, pk=None):
        task = self.get_object()
        task.status = 'CO'
        task.save()

        email_list = get_all_commentators(pk)
        send_user_email(email_list, 'completed')

        return Response({'detail': 'success'})

    @action(detail=False, methods=['get'], url_path='top-last-month')
    def get_top_tasks_last_month(self, request):
        user = request.user.email
        top_tasks = cache.get(user)
        if top_tasks:
            return Response(top_tasks)

        tasks = Task.objects \
            .filter(created_at__gt=datetime.now() - timedelta(days=30)) \
            .annotate(total_duration=Sum('task_duration__duration')) \
            .order_by('-total_duration').values()

        top_20_tasks = tasks[:20]
        cache.set(user, top_20_tasks, timeout=60)
        return Response(top_20_tasks)

    @action(detail=True, url_path='comments')
    def comments(self, request, pk=None):
        task = self.get_object()
        comments = Comment.objects.filter(task=task).values()
        return Response(comments)

    @comments.mapping.post
    def create_comments(self, request, pk=None):
        task = self.get_object()

        serializer = CommentSerializer(data=request.data, context={'task': task, 'user': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='timer/start')
    def timer_start(self, request, pk):
        task = self.get_object()

        task_duration, created = TaskDuration.objects.update_or_create(
            owner=request.user, task=task,
            defaults={
                'timer_on': True,
                'start_working_datetime': datetime.now(timezone.utc)
            }
        )

        if created:
            return Response({'detail': 'timer start'})
        return Response({'detail': 'timer start'})

    @action(detail=True, methods=['post'], url_path='timer/stop')
    def timer_stop(self, request, pk):
        task = self.get_object()
        existing_task = get_object_or_404(
            TaskDuration.objects.filter(task=task, owner=request.user, timer_on=True),
            pk=pk
        )

        now = datetime.now(timezone.utc)
        task_duration = now - existing_task.start_working_datetime

        if not existing_task.duration:
            existing_task.duration = 0

        existing_task.duration = existing_task.duration + task_duration.seconds
        existing_task.timer_on = False
        existing_task.stop_working_datetime = datetime.now(timezone.utc)
        existing_task.save()

        return Response({'details': 'timer stop'})

    @action(detail=True, methods=['post'], url_path='timer/add')
    def add_time_on_specific_date(self, request, pk):
        task = self.get_object()
        serializer = AddTimeOnSpecificDateSerializer(data=request.data, context={'task': task})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='timer/last-month')
    def get_last_month_time_logs(self, request):
        newest_time_logs = TaskDuration.objects.filter(
            owner=request.user,
            created_at__gt=datetime.now() - timedelta(days=30)
        ).values()
        return Response(newest_time_logs)
