from rest_framework import serializers
from .models import WeatherStation, WeatherReading, ModelPrediction

class WeatherStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherStation
        fields = ['station_id', 'name', 'latitude', 'longitude']

class WeatherReadingSerializer(serializers.ModelSerializer):
    station = WeatherStationSerializer(read_only=True)
    
    class Meta:
        model = WeatherReading
        fields = ['id', 'station', 'timestamp', 'temperature', 'rainfall', 
                  'humidity', 'wind_direction', 'wind_speed']

class ModelPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPrediction
        fields = ['id', 'timestamp', 'input_data', 'prediction_result']