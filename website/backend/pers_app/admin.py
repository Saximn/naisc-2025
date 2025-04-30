from django.contrib import admin
from .models import WeatherStation, WeatherReading, ModelPrediction

@admin.register(WeatherStation)
class WeatherStationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'latitude', 'longitude')
    search_fields = ('station_id', 'name')

@admin.register(WeatherReading)
class WeatherReadingAdmin(admin.ModelAdmin):
    list_display = ('station', 'timestamp', 'temperature', 'rainfall', 
                    'humidity', 'wind_direction', 'wind_speed')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'
    search_fields = ('station__name', 'station__station_id')

@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'