from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Tasks API",
      default_version='v1',
      description="Enjoy this API",
      contact=openapi.Contact(email="contact@snippets.local"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('users/', include("apps.users.urls")),
    path('tasks/', include("apps.tasks.urls")),
]
