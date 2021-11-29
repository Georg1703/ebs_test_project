from datetime import datetime, timezone, timedelta

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Sum

from .models import Task, Comment, TaskDuration
from apps.users.models import CustomUser
from .service import send_user_email
from .serializers import (
    ListTaskSerializer,
    RetrieveTaskSerializer,
    SetTaskOwnerSerializer,
    SetTaskCompletedSerializer,
    CommentSerializer,
    TaskDurationStartSerializer,
    TaskDurationStopSerializer,
    AddTimeOnSpecificDateSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
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

    @action(detail=False, methods=['get'], serializer_class=ListTaskSerializer)
    def my_tasks(self, request):
        tasks = Task.objects.filter(owner=request.user).values('id', 'title')
        return Response(tasks)

    @action(detail=False, methods=['get'], serializer_class=ListTaskSerializer)
    def completed_tasks(self, request):
        tasks = Task.objects.filter(status='CO').values('id', 'title')
        return Response(tasks)

    @action(detail=True, methods=['post'])
    def set_task_owner(self, request):
        serializer = SetTaskOwnerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = CustomUser.objects.get(id=serializer.data['owner'])
            send_user_email(user.email, 'new_task')
            return Response(serializer.validated_data)
        else:
            return Response(serializer.errors)

    @action(detail=True, methods=['post'])
    def set_status_completed(self, request):
        serializer = SetTaskCompletedSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data)
        return Response(serializer.errors)

    @action(detail=False, methods=['get'])
    def get_top_tasks_last_month(self, request):
        user = request.user.email
        top_tasks = cache.get(user)
        if top_tasks:
            return Response(top_tasks)

        tasks = Task.objects\
            .filter(created_at__gt=datetime.now() - timedelta(days=30))\
            .annotate(total_duration=Sum('task_duration__duration'))\
            .order_by('-total_duration').values()

        top_20_tasks = tasks[-20:]
        cache.set(user, top_20_tasks, timeout=60)
        return Response(top_20_tasks)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        task_id = self.request.query_params.get('task')
        if task_id:
            return Comment.objects.filter(task=task_id)
        return []

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskDurationViewSet(viewsets.ModelViewSet):
    queryset = TaskDuration.objects.all()
    serializer_class = TaskDurationStartSerializer

    def get_queryset(self):
        task_id = self.request.query_params.get('task')

        if task_id:
            return TaskDuration.objects.filter(task_id=task_id)

    @action(detail=True, methods=['post'])
    def timer_start(self, request):
        serializer = TaskDurationStartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    @action(detail=True, methods=['post'])
    def timer_stop(self, request):
        serializer = TaskDurationStopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    @action(detail=False, methods=['post'])
    def add_time_on_specific_date(self, request):
        serializer = AddTimeOnSpecificDateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    @action(detail=False, methods=['get'])
    def get_last_month_time_logs(self, request):
        newest_time_logs = TaskDuration.objects.filter(
            owner=request.user,
            created_at__gt=datetime.now() - timedelta(days=30)
        ).values()
        return Response(newest_time_logs)

