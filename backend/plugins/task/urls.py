from django.urls import path
from rest_framework import routers

from plugins.task.views.task import TaskViewSet

route_url = routers.SimpleRouter()

route_url.register(r'task', TaskViewSet, basename='task')

urlpatterns = [
    
]
urlpatterns += route_url.urls








