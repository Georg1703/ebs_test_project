from django.urls import path
from rest_framework import routers

from .views import TaskViewSet, TaskDurationViewSet

router = routers.SimpleRouter()

router.register(r'', TaskDurationViewSet)
router.register(r'', TaskViewSet)
urlpatterns = router.urls
