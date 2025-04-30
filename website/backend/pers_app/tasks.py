from celery import shared_task
import logging
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task
def fetch_weather_data():
    """
    Task to fetch weather data from all APIs
    """
    from weather_app.services.api_service import fetch_and_store_weather_data
    
    logger.info("Starting scheduled task: fetch_weather_data")
    date_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    result = fetch_and_store_weather_data(date_time)
    
    logger.info(f"Task completed: {result}")
    return result

@shared_task
def make_weather_prediction():
    """
    Task to fetch the last 24 hours of data, preprocess it, and make a prediction
    """
    from weather_app.services.data_preprocessor import get_model_input_data
    from weather_app.services.modelarts_service import ModelArtsService
    from weather_app.models import ModelPrediction
    
    logger.info("Starting scheduled task: make_weather_prediction")
    
    try:
        # Get the last 24 hours of data preprocessed into grid format
        grid_data = get_model_input_data()
        
        if grid_data is None:
            logger.warning("No data available for the last 24 hours")
            return {"error": "No data available"}
        
        # Call ModelArts API
        model_service = ModelArtsService(settings.MODELARTS_ENDPOINT_URL)
        prediction_result = model_service.predict(grid_data)
        
        if prediction_result:
            # Store prediction in database
            prediction = ModelPrediction.objects.create(
                input_data={
                    "timestamp": datetime.now().isoformat(),
                    "data_shape": list(grid_data.shape)
                },
                prediction_result=prediction_result
            )
            
            logger.info(f"Prediction saved with ID: {prediction.id}")
            return {"success": True, "prediction_id": prediction.id}
        else:
            logger.error("Failed to get prediction from ModelArts")
            return {"error": "Failed to get prediction"}
            
    except Exception as e:
        logger.error(f"Exception in make_weather_prediction task: {str(e)}")
        return {"error": str(e)}