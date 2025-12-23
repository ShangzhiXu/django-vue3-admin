from django.urls import path
from rest_framework import routers

from plugins.workorder.views.workorder import WorkOrderViewSet, MobileWorkOrderView, MobileWorkOrderPhotoView, MobileWorkOrderCompleteView
from plugins.workorder.views.workorder_photos import MobileWorkOrderPhotosView
from plugins.workorder.views.workorder_rechecks import MobileWorkOrderRechecksView
from plugins.workorder.views.workorder_submissions import MobileWorkOrderSubmissionsView, MobileWorkOrderSubmissionDeleteView
from plugins.workorder.views.mobile_notifications import MobileNotificationsView, MobileNotificationReadView
from plugins.workorder.views.supervision_push import SupervisionPushViewSet

# 先定义自定义路由（更具体的路由）
urlpatterns = [
    # 更具体的路由放在前面，避免被通用路由匹配
    path('mobile/workorders/<str:workorder_no>/complete', MobileWorkOrderCompleteView.as_view(), name='mobile-workorder-complete'),
    path('mobile/workorders/<str:workorder_no>/photos', MobileWorkOrderPhotoView.as_view(), name='mobile-workorder-photos'),
    path('mobile/workorders/<str:workorder_no>/photos/list', MobileWorkOrderPhotosView.as_view(), name='mobile-workorder-photos-list'),
    path('mobile/workorders/<str:workorder_no>/rechecks', MobileWorkOrderRechecksView.as_view(), name='mobile-workorder-rechecks'),
    path('mobile/workorders/<str:workorder_no>/submissions', MobileWorkOrderSubmissionsView.as_view(), name='mobile-workorder-submissions'),
    path('mobile/workorders/<str:workorder_no>/submissions/<int:submission_id>', MobileWorkOrderSubmissionDeleteView.as_view(), name='mobile-workorder-submission-delete'),
    path('mobile/workorders', MobileWorkOrderView.as_view(), name='mobile-workorders'),
    path('mobile/notifications', MobileNotificationsView.as_view(), name='mobile-notifications'),
    path('mobile/notifications/read', MobileNotificationReadView.as_view(), name='mobile-notifications-read'),
]

# 然后注册ViewSet路由
route_url = routers.SimpleRouter()
route_url.register(r'workorder', WorkOrderViewSet, basename='workorder')
route_url.register(r'supervision', SupervisionPushViewSet, basename='supervision')
urlpatterns += route_url.urls
