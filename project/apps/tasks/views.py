from datetime import datetime, timezone, timedelta

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache

from .models import Task, Comment, CustomUser, TaskDuration
from .service import send_user_email, get_all_comenters
from .serializers import (
    ListTaskSerializer,
    RetrieveTaskSerializer,
    SetTaskOwnerSerializer,
    CommentSerializer,
    TaskDurationStartSerializer,
    TaskDurationStopSerializer,
    OrderTaskSerializer
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Order deleted successfully'})

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
            send_user_email([user.email], 'new_task')
            return Response(serializer.validated_data)
        else:
            return Response(serializer.errors)

    @action(detail=True, methods=['post'])
    def set_status_completed(self, request):
        task_id = request.data.get('task_id')
        if not task_id:
            return Response({'task_id': ['This field is required']})

        task = Task.objects.filter(id=task_id).first()
        if task:
            task.status = 'CO'
            task.save()
            email_list = get_all_comenters(task_id)
            send_user_email(list(email_list), 'completed')
            return Response({'detail': 'task status set to completed'})
        return Response({'task_id': ['Task not found']})

    @action(detail=False, methods=['get'])
    def get_top_tasks_last_month(self, request):
        user = request.user.email
        top_tasks = cache.get(user)
        if top_tasks:
            return top_tasks

        queryset = Task.objects.filter(
            created_at__gt=datetime.now() - timedelta(days=30)
        )
        serializer = OrderTaskSerializer(queryset, many=True)
        task_list = [dict(item) for item in serializer.data]
        sorted_task_list = sorted(task_list, key=lambda i: i['task_duration'])
        top_20_tasks = sorted_task_list[-20:]
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

    @action(detail=False, methods=['get'])
    def get_last_month_time_logs(self, request):
        newest_time_logs = TaskDuration.objects.filter(
            owner=request.user,
            created_at__gt=datetime.now() - timedelta(days=30)
        ).values()
        return Response(newest_time_logs)

