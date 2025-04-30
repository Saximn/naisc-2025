from django.db import models

class WeatherStation(models.Model):
    station_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.station_id})"

class WeatherReading(models.Model):
    station = models.ForeignKey(WeatherStation, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField()
    temperature = models.FloatField(null=True, blank=True)
    rainfall = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    wind_direction = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ('station', 'timestamp')
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.station.name} - {self.timestamp}"

class ModelPrediction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    input_data = models.JSONField()  # Store the input data used for prediction
    prediction_result = models.JSONField()  # Store the prediction results
    
    def __str__(self):
        return f"Prediction at {self.timestamp}"