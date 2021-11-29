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
        fields = ('id', 'text')

    def create(self, validated_data):
        validated_data['task'] = self.context['task']
        validated_data['author'] = self.context['user']
        send_user_email(self.context['user'].email, 'comment')

        return Comment.objects.create(**validated_data)


class AddTimeOnSpecificDateSerializer(serializers.ModelSerializer):
    duration = serializers.IntegerField(required=True)

    class Meta:
        model = TaskDuration
        fields = ('start_working_datetime', 'duration')

    def create(self, validated_data):
        validated_data['timer_on'] = False
        validated_data['duration'] = validated_data['duration'] * 60
        validated_data['task'] = self.context['task']
        return TaskDuration.objects.create(**validated_data)



