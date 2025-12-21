from django.urls import path
from rest_framework import routers

from plugins.workorder.views.workorder import WorkOrderViewSet
from plugins.workorder.views.supervision_push import SupervisionPushViewSet

route_url = routers.SimpleRouter()

route_url.register(r'workorder', WorkOrderViewSet, basename='workorder')
route_url.register(r'supervision', SupervisionPushViewSet, basename='supervision')

urlpatterns = [
    
]
urlpatterns += route_url.urls
