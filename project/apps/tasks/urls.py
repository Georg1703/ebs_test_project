from django.urls import path


from .views import TaskViewSet, CommentViewSet, TaskDurationViewSet


task_list = TaskViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

task_retrieve = TaskViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

comment_list = CommentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})


urlpatterns = [
    path('', task_list, name='tasks'),
    path('<int:pk>/', task_retrieve, name='task'),
    path('my_tasks/', TaskViewSet.as_view({'get': 'my_tasks'}), name='my_tasks'),
    path('completed_tasks/', TaskViewSet.as_view({'get': 'completed_tasks'}), name='completed_tasks'),
    path('set_task_owner/', TaskViewSet.as_view({'post': 'set_task_owner'}), name='task_owner'),
    path('set_status_completed/', TaskViewSet.as_view({'post': 'set_status_completed'}), name='set_status_completed'),
    path('get_top_tasks_last_month/', TaskViewSet.as_view({'get': 'get_top_tasks_last_month'}), name='top_tasks'),
    path('comments/', comment_list, name='comments'),

    path('timer_start/', TaskDurationViewSet.as_view({'post': 'timer_start'}), name='task_timer_start'),
    path('timer_stop/', TaskDurationViewSet.as_view({'post': 'timer_stop'}), name='task_timer_stop'),
    path('timer_list/', TaskDurationViewSet.as_view({'get': 'list'}), name='task_timer_list'),
    path('get_last_month_time/', TaskDurationViewSet.as_view({'get': 'get_last_month_time_logs'}), name='last_month'),
]