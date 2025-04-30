import numpy as np
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import WeatherStation, WeatherReading, ModelPrediction
from .serializers import (
    WeatherStationSerializer, 
    WeatherReadingSerializer,
    ModelPredictionSerializer
)
from .tasks import fetch_weather_data, make_weather_prediction, complete_hourly_workflow
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Singapore grid parameters - matching your exact configuration
SG_LAT_MIN, SG_LAT_MAX = 1.15, 1.50
SG_LON_MIN, SG_LON_MAX = 103.6, 104.1
RESOLUTION = 500  # meters

# Conversion factors
LAT_STEP = RESOLUTION / 111000.0  # Convert meters to degrees latitude
LON_STEP = RESOLUTION / 110000.0  # Convert meters to degrees longitude

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
    
    # @action(detail=False, methods=['post'])
    # def fetch_data(self, request):
    #     """Trigger data fetching manually"""
    #     date_time = request.data.get('date_time', datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        
    #     try:
    #         # Run synchronously for testing
    #         from pers_app.services.api_service import fetch_and_store_weather_data
    #         result = fetch_and_store_weather_data(date_time)
            
    #         return Response({
    #             "status": "Data fetch completed",
    #             "result": result
    #         })
    #     except Exception as e:
    #         logger.error(f"Error triggering data fetch: {str(e)}")
    #         return Response({
    #             "error": str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def make_prediction(self, request):
        """Trigger prediction manually"""
        try:
            # For immediate response, run in background
            task = complete_hourly_workflow.delay()
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
        """
        Get latest prediction in heatmap format
        Optional query params:
        - downsample_factor: int (default 1) - Controls downsampling (1=no downsampling)
        """
        try:
            # Get the downsampling factor from query parameters or use default
            downsample_factor = int(request.query_params.get('downsample_factor', 1))
            
            # Get latest prediction
            try:
                latest_prediction = ModelPrediction.objects.latest('timestamp')
            except ModelPrediction.DoesNotExist:
                return Response({
                    "error": "No predictions available"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Extract the prediction data
            prediction_result = latest_prediction.prediction_result
            
            if 'prediction' not in prediction_result:
                return Response({
                    "error": "Invalid prediction format"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get the raw prediction array
            raw_prediction = prediction_result['prediction']
            
            # Convert to numpy for easier manipulation
            try:
                # The prediction is a 3D array with shape (78, 110, 1)
                prediction_array = np.array(raw_prediction)
                
                # Extract dimensions
                height, width, _ = prediction_array.shape
                
                # Initialize a list to hold heatmap points
                heatmap_points = []
                
                # Apply downsampling - process every Nth cell
                for i in range(0, height, downsample_factor):
                    for j in range(0, width, downsample_factor):
                        # Take a block of cells and average them
                        block = prediction_array[
                            i:min(i+downsample_factor, height),
                            j:min(j+downsample_factor, width),
                            0  # Use the first (and only) channel
                        ]
                        
                        # Calculate average value for this block
                        avg_val = np.mean(block)
                        
                        if avg_val > 0.01:  # Filter out very low values to reduce data size
                            # Convert grid coordinates to geo coordinates using exact mapping
                            # Use the middle of the block for better accuracy
                            block_middle_i = i + (min(i+downsample_factor, height) - i) / 2
                            block_middle_j = j + (min(j+downsample_factor, width) - j) / 2
                            
                            # Map grid indices to normalized positions in the overall grid
                            # This handles cases where the prediction grid doesn't match exactly with the ideal grid
                            norm_i = block_middle_i / height
                            norm_j = block_middle_j / width
                            
                            # Convert to lat/lon using exact mapping parameters
                            lat = SG_LAT_MIN + norm_i * (SG_LAT_MAX - SG_LAT_MIN)
                            lon = SG_LON_MIN + norm_j * (SG_LON_MAX - SG_LON_MIN)
                            
                            heatmap_points.append({
                                "lat": lat,
                                "lon": lon,
                                "val": float(avg_val)
                            })
                
                return Response({
                    "timestamp": latest_prediction.timestamp.isoformat(),
                    "points": heatmap_points,
                    "meta": {
                        "original_dimensions": [height, width],
                        "downsampled_by": downsample_factor,
                        "point_count": len(heatmap_points)
                    }
                })
                
            except Exception as e:
                logger.error(f"Error processing prediction data: {str(e)}")
                return Response({
                    "error": f"Error processing prediction data: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error retrieving heatmap data: {str(e)}")
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)