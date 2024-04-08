from django.urls import path

from polls import consumers

# here we learn about dynamic routing
urlpatterns = [
    path('ws/task_status/<task_id>/', consumers.TaskStatusConsumer.as_asgi()),
]