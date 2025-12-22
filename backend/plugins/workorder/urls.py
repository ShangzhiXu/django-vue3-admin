from django.urls import path
from rest_framework import routers

from plugins.workorder.views.workorder import WorkOrderViewSet, MobileWorkOrderView
from plugins.workorder.views.supervision_push import SupervisionPushViewSet

route_url = routers.SimpleRouter()

route_url.register(r'workorder', WorkOrderViewSet, basename='workorder')
route_url.register(r'supervision', SupervisionPushViewSet, basename='supervision')

urlpatterns = [
    path('mobile/workorders', MobileWorkOrderView.as_view(), name='mobile-workorders'),
]
urlpatterns += route_url.urls
