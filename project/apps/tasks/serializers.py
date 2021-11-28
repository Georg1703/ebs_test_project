from datetime import datetime, timezone

from rest_framework import serializers

from .models import Task, Comment, TaskDuration
from .service import send_user_email, get_all_commentators
from apps.users.models import CustomUser


class ListTaskSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    task_duration = serializers.CharField(source='get_task_total_duration', read_only=True)
    description = serializers.CharField(write_only=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'user', 'description', 'task_duration')

    def create(self, validated_data):
        user = CustomUser.objects.get(id=validated_data['owner'].id)
        send_user_email(user.email, 'new_task')

        return Task.objects.create(**validated_data)


class RetrieveTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'status', 'owner')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'text', 'task')

    def create(self, validated_data):
        user = CustomUser.objects.get(id=validated_data['task'].owner.id)
        send_user_email(user.email, 'comment')

        return Comment.objects.create(**validated_data)


class SetTaskOwnerSerializer(serializers.Serializer):
    owner = serializers.IntegerField(required=True)
    task = serializers.IntegerField(required=True)

    def validate_owner(self, value):
        user_exit = CustomUser.objects.filter(id=value).exists()
        if not user_exit:
            raise serializers.ValidationError("Owner not found")
        return value

    def validate_task(self, value):
        task_exist = Task.objects.filter(id=value).exists()
        if not task_exist:
            raise serializers.ValidationError("Task not found")
        return value

    def save(self):
        owner_id = self.validated_data['owner']
        task_id = self.validated_data['task']
        Task.objects.filter(id=task_id).update(owner=owner_id)


class SetTaskCompletedSerializer(serializers.Serializer):
    task = serializers.IntegerField(required=True)

    def validate_task(self, value):
        if not Task.objects.filter(id=value).exists():
            raise serializers.ValidationError("Task not found")

        if Task.objects.filter(id=value, status='CO').exists():
            raise serializers.ValidationError("Task already have status completed")

        return value

    def create(self, validated_data):
        task_id = self.validated_data['task']
        Task.objects.filter(id=task_id).update(status='CO')
        email_list = get_all_commentators(task_id)
        send_user_email(email_list, 'completed')


class TaskDurationStartSerializer(serializers.ModelSerializer):
    start_working_datetime = serializers.DateTimeField(default=datetime.now(timezone.utc))
    owner = serializers.StringRelatedField(read_only=True)
    timer_on = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = TaskDuration
        fields = ('id', 'task', 'timer_on', 'owner', 'start_working_datetime')

    def create(self, validated_data):

        try:
            existing_task = TaskDuration.objects.get(
                task=validated_data['task'],
                owner=validated_data['owner']
            )
        except TaskDuration.DoesNotExist:
            return TaskDuration.objects.create(**validated_data)

        if existing_task.timer_on:
            raise serializers.ValidationError({'detail': 'Timer for task is running already'})
        else:
            existing_task.timer_on = True
            existing_task.start_working_datetime = datetime.now(timezone.utc)
            existing_task.save()
            return existing_task


class TaskDurationStopSerializer(serializers.ModelSerializer):
    start_working_datetime = serializers.DateTimeField(default=datetime.now(timezone.utc))
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TaskDuration
        fields = ('id', 'task', 'timer_on', 'owner', 'start_working_datetime')

    def create(self, validated_data):
        try:
            existing_task = TaskDuration.objects.get(
                task=validated_data['task'],
                owner=validated_data['owner'],
                timer_on=True
            )
        except TaskDuration.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Timer for task was not found'})

        now = datetime.now(timezone.utc)
        task_duration = now - existing_task.start_working_datetime

        if not existing_task.duration:
            existing_task.duration = 0

        existing_task.duration = existing_task.duration + task_duration.seconds
        existing_task.timer_on = False
        existing_task.stop_working_datetime = datetime.now(timezone.utc)
        existing_task.save()

        return existing_task


class AddTimeOnSpecificDateSerializer(serializers.ModelSerializer):
    duration = serializers.IntegerField(required=True)

    class Meta:
        model = TaskDuration
        fields = ('start_working_datetime', 'task', 'duration')

    def create(self, validated_data):
        validated_data['timer_on'] = False
        validated_data['duration'] = validated_data['duration'] * 60
        return TaskDuration.objects.create(**validated_data)



