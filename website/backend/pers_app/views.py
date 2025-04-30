from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import WeatherStation, WeatherReading, ModelPrediction
from .serializers import (
    WeatherStationSerializer, 
    WeatherReadingSerializer,
    ModelPredictionSerializer
)
from .tasks import fetch_weather_data, make_weather_prediction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WeatherStationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for weather stations"""
    queryset = WeatherStation.objects.all()
    serializer_class = WeatherStationSerializer

class WeatherReadingViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for weather readings"""
    queryset = WeatherReading.objects.all().order_by('-timestamp')
    serializer_class = WeatherReadingSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by station if provided
        station_id = self.request.query_params.get('station_id', None)
        if station_id:
            queryset = queryset.filter(station__station_id=station_id)
        
        # Filter by start and end date if provided
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
            
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset

class WeatherManagementViewSet(viewsets.ViewSet):
    """Management endpoints for weather data"""
    
    @action(detail=False, methods=['post'])
    def fetch_data(self, request):
        """Trigger data fetching manually"""
        date_time = request.data.get('date_time', datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        
        try:
            # For immediate response, run in background
            task = fetch_weather_data.delay()
            return Response({
                "status": "Data fetch initiated",
                "task_id": task.id
            })
        except Exception as e:
            logger.error(f"Error triggering data fetch: {str(e)}")
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def make_prediction(self, request):
        """Trigger prediction manually"""
        try:
            # For immediate response, run in background
            task = make_weather_prediction.delay()
            return Response({
                "status": "Prediction initiated",
                "task_id": task.id
            })
        except Exception as e:
            logger.error(f"Error triggering prediction: {str(e)}")
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModelPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for model predictions"""
    queryset = ModelPrediction.objects.all().order_by('-timestamp')
    serializer_class = ModelPredictionSerializer
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest prediction"""
        try:
            latest_prediction = ModelPrediction.objects.latest('timestamp')
            serializer = self.get_serializer(latest_prediction)
            return Response(serializer.data)
        except ModelPrediction.DoesNotExist:
            return Response({
                "error": "No predictions available"
            }, status=status.HTTP_404_NOT_FOUND)