from celery import shared_task, chain
import logging
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import time
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def fetch_weather_data(self, date_time=None):
    """
    Task to fetch weather data from all APIs
    
    Parameters:
    - date_time: ISO format datetime string (YYYY-MM-DDTHH:MM:SS)
                If None, use current time rounded to the hour
    
    Returns:
    - Dictionary with results of the operation
    """
    from pers_app.services.api_service import fetch_and_store_weather_data, get_hourly_timestamp
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting fetch_weather_data")
    
    if date_time is None:
        # Use the most recent completed hour
        date_time = get_hourly_timestamp()
        
    logger.info(f"Fetching weather data for timestamp: {date_time}")
    
    try:    
        result = fetch_and_store_weather_data(date_time)
        logger.info(f"Task {task_id}: Data fetch completed")
        return result
    except Exception as e:
        logger.error(f"Task {task_id}: Error during data fetch: {str(e)}")
        raise

@shared_task(bind=True)
def backfill_missing_data(self, hours=24):
    """
    Task to fetch data for the specified number of past hours
    
    Parameters:
    - hours: Number of hours to backfill (default: 24)
    
    Returns:
    - Dictionary with summary of operations
    """
    from pers_app.services.api_service import backfill_weather_data
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting backfill for the last {hours} hours")
    
    try:
        # Use the backfill function from api_service
        results = backfill_weather_data(hours)
        
        logger.info(f"Task {task_id}: Backfill completed - "
                   f"{results['successful_fetches']} successful, "
                   f"{results['failed_fetches']} failed")
        return results
    except Exception as e:
        logger.error(f"Task {task_id}: Error during backfill: {str(e)}")
        raise

@shared_task(bind=True)
def check_and_fetch_data_if_needed(self, hours=24, proceed_with_prediction=True):
    """
    Check if we have enough data for the specified hours, and fetch it if needed
    
    Parameters:
    - hours: Number of hours of data needed
    - proceed_with_prediction: Whether to run prediction task after fetching
    
    Returns:
    - Dictionary with results
    """
    from pers_app.models import WeatherReading
    from pers_app.services.api_service import round_down_to_hour
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Checking if we have data for the last {hours} hours")
    
    # Get the current time and calculate the cutoff
    end_time = round_down_to_hour()  # Current hour, rounded down
    start_time = end_time - timedelta(hours=hours)
    
    # Count how many distinct hours we actually have
    distinct_hours = WeatherReading.objects.filter(
        timestamp__gte=start_time,
        timestamp__lte=end_time
    ).dates('timestamp', 'hour').count()
    
    logger.info(f"Task {task_id}: Found data for {distinct_hours} out of {hours} hours")
    
    if distinct_hours < hours:
        # We're missing some data, need to backfill
        missing_hours = hours - distinct_hours
        logger.info(f"Task {task_id}: Missing data for {missing_hours} hours, starting backfill")
        
        # If we have some data but not all, only backfill what we need
        if distinct_hours > 0:
            backfill_task = backfill_missing_data.s(missing_hours)
        else:
            # If we have no data, backfill everything
            backfill_task = backfill_missing_data.s(hours)
        
        if proceed_with_prediction:
            # Chain tasks: first backfill, then make prediction
            task_chain = chain(backfill_task, make_weather_prediction.s())
            result = task_chain()
            return {"status": "Backfill and prediction initiated", "task_id": result.id}
        else:
            # Just backfill without prediction
            result = backfill_task.delay()
            return {"status": "Backfill initiated", "task_id": result.id}
    
    elif proceed_with_prediction:
        # We have enough data, proceed with prediction
        result = make_weather_prediction.delay()
        return {"status": "Prediction initiated", "task_id": result.id}
    
    return {"status": "Data check complete", "hours_found": distinct_hours}

@shared_task(bind=True)
def make_weather_prediction(self):
    """
    Task to process the last 24 hours of data and make a prediction
    First checks if enough data exists, fetches it if needed
    """
    from pers_app.services.data_preprocessor import get_model_input_data
    from pers_app.services.modelarts_service import ModelArtsService
    from pers_app.models import ModelPrediction, WeatherReading
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting weather prediction task")
    
    try:
        # Check if we have data for the last 24 hours
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        readings_count = WeatherReading.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).count()
        
        if readings_count == 0:
            logger.warning(f"Task {task_id}: No data found for the last 24 hours, initiating backfill")
            # This will backfill and then recursively call this task again
            return check_and_fetch_data_if_needed(hours=24, proceed_with_prediction=True)
        
        # Get the preprocessed grid data
        logger.info(f"Task {task_id}: Preprocessing data for model input")
        grid_data = get_model_input_data()
        
        if grid_data is None:
            logger.warning(f"Task {task_id}: Failed to preprocess data, possibly insufficient data")
            # Try to backfill data and retry
            return check_and_fetch_data_if_needed(hours=24, proceed_with_prediction=True)
        
        # Call ModelArts API
        logger.info(f"Task {task_id}: Sending data to ModelArts for prediction")
        model_service = ModelArtsService(settings.MODELARTS_ENDPOINT_URL)
        prediction_result = model_service.predict(grid_data)
        
        if prediction_result:
            # Store prediction in database
            logger.info(f"Task {task_id}: Prediction successful, saving to database")
            prediction = ModelPrediction.objects.create(
                input_data={
                    "timestamp": timezone.now().isoformat(),
                    "data_shape": list(grid_data.shape)
                },
                prediction_result=prediction_result
            )
            
            logger.info(f"Task {task_id}: Prediction saved with ID: {prediction.id}")
            return {"success": True, "prediction_id": prediction.id}
        else:
            logger.error(f"Task {task_id}: Failed to get prediction from ModelArts")
            return {"error": "Failed to get prediction"}
            
    except Exception as e:
        logger.error(f"Task {task_id}: Exception in make_weather_prediction: {str(e)}")
        raise

@shared_task(bind=True)
def generate_hourly_prediction(self):
    """
    Task that runs every hour to ensure we have the latest prediction
    This combines fetching the latest hour of data and then making a prediction
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting hourly prediction workflow")
    
    try:
        # 1. Fetch latest hour's data
        fetch_task = fetch_weather_data.delay()
        
        # 2. Wait for fetch to complete (with timeout)
        fetch_result = AsyncResult(fetch_task.id)
        fetch_result.get(timeout=300)  # 5 minutes timeout
        
        # 3. Make prediction with the updated data
        logger.info(f"Task {task_id}: Data fetch complete, making prediction")
        prediction_task = make_weather_prediction.delay()
        
        return {
            "status": "Hourly prediction workflow initiated",
            "fetch_task_id": fetch_task.id,
            "prediction_task_id": prediction_task.id
        }
    except Exception as e:
        logger.error(f"Task {task_id}: Error in hourly prediction workflow: {str(e)}")
        raise