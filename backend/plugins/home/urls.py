from django.urls import path, include
from rest_framework.routers import DefaultRouter
from plugins.home.views.home import HomeViewSet

router = DefaultRouter()
router.register(r'', HomeViewSet, basename='home')

urlpatterns = [
    path('', include(router.urls)),
]

