from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stations', views.WeatherStationViewSet)
router.register(r'readings', views.WeatherReadingViewSet)
router.register(r'predictions', views.ModelPredictionViewSet)
router.register(r'manage', views.WeatherManagementViewSet, basename='manage')

urlpatterns = [
    path('', include(router.urls)),
]