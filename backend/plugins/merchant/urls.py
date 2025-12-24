from django.urls import path
from rest_framework import routers

from plugins.merchant.views.merchant import MerchantViewSet

route_url = routers.SimpleRouter()

route_url.register(r'merchant', MerchantViewSet, basename='merchant')

urlpatterns = [
    
]
urlpatterns += route_url.urls








