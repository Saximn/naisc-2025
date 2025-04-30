from celery import shared_task, chain
import logging
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
import time
from django.db.models import Count
from django.db.models.functions import TruncHour

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
def check_and_backfill_missing_hours(self, hours=24):
    """
    Check for missing hours in the last 24 hours and backfill them
    
    Returns:
    - Dictionary with results
    """
    from pers_app.models import WeatherReading
    from pers_app.services.api_service import round_down_to_hour, get_singapore_time
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Checking for missing hours in the last {hours} hours")
    
    # Get Singapore timezone
    sg_tz = pytz.timezone('Asia/Singapore')
    
    # Calculate current hour (rounded down)
    current_hour = round_down_to_hour(timezone.now())
    
    # Calculate expected hours (oldest to newest)
    expected_hours = []
    for i in range(hours, 0, -1):  # Count backwards from 24 to 1
        hour = current_hour - timedelta(hours=i)
        expected_hours.append(hour)
    
    # Query existing hours in database using TruncHour instead of dates
    existing_hours_query = WeatherReading.objects.filter(
        timestamp__gte=expected_hours[0],
        timestamp__lte=current_hour
    ).annotate(
        hour=TruncHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).values_list('hour', flat=True)
    
    # Convert to set of datetimes for easy comparison
    existing_hours = set(existing_hours_query)
    
    # Find missing hours
    missing_hours = []
    for hour in expected_hours:
        # Round to exact hour to ensure correct comparison
        hour_exact = hour.replace(minute=0, second=0, microsecond=0)
        if hour_exact not in existing_hours:
            missing_hours.append(hour_exact)
    
    logger.info(f"Task {task_id}: Found {len(missing_hours)} missing hours out of {hours}")
    
    # If no missing hours, we're done
    if not missing_hours:
        return {
            "status": "complete",
            "missing_hours": 0,
            "backfilled_hours": 0
        }
    
    # Backfill missing hours
    successful_backfills = 0
    errors = []
    
    for hour in missing_hours:
        try:
            # Convert to Singapore time string
            hour_str = get_singapore_time(hour, include_timezone=False)
            logger.info(f"Task {task_id}: Backfilling hour {hour_str}")
            
            # Fetch data for this hour - DIRECTLY call the function, not the task
            from pers_app.services.api_service import fetch_and_store_weather_data
            result = fetch_and_store_weather_data(hour_str)
            
            if result and not any(result.get("errors", [])):
                successful_backfills += 1
            else:
                errors.append(f"Error backfilling {hour_str}: {result.get('errors')}")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Task {task_id}: Exception backfilling {hour}: {str(e)}")
            errors.append(f"Exception backfilling {hour}: {str(e)}")
    
    return {
        "status": "complete" if successful_backfills == len(missing_hours) else "partial",
        "missing_hours": len(missing_hours),
        "backfilled_hours": successful_backfills,
        "errors": errors
    }

@shared_task(bind=True)
def make_weather_prediction(self, backfill_result=None):
    """
    Task to process the last 24 hours of data and make a prediction
    Can be chained after the backfill task
    """
    from pers_app.services.data_preprocessor import get_model_input_data
    from pers_app.services.modelarts_service import ModelArtsService
    from pers_app.models import ModelPrediction
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting weather prediction task")
    
    try:
        # Log the backfill result if provided (from chaining)
        if backfill_result:
            logger.info(f"Task {task_id}: Using backfill result: {backfill_result}")
        
        # Get preprocessed data for the model
        logger.info(f"Task {task_id}: Getting model input data")
        grid_data = get_model_input_data()
        
        if grid_data is None:
            logger.error(f"Task {task_id}: Failed to get model input data")
            return {"error": "Failed to get model input data"}
            
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
        return {"error": str(e)}

@shared_task(bind=True)
def complete_hourly_workflow(self):
    """
    Complete hourly workflow - run backfill then prediction in sequence
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting complete hourly workflow")
    
    # Create a chain of tasks that will run in sequence
    workflow = chain(
        # First check and backfill missing hours
        check_and_backfill_missing_hours.s(24),
        # Then run prediction (which will receive the result of the previous task)
        make_weather_prediction.s()
    )
    
    # Execute the chain
    result = workflow()
    
    return {
        "status": "Hourly workflow initiated",
        "chain_id": result.id
    }

@shared_task(bind=True)
def fetch_current_hour_and_predict(self):
    """
    Task that runs every hour: fetch current hour data, then run backfill and prediction
    """
    from pers_app.services.api_service import get_hourly_timestamp
    
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting hourly update")
    
    try:
        # 1. Fetch latest hour's data
        hour_str = get_hourly_timestamp()
        logger.info(f"Task {task_id}: Fetching latest hour data: {hour_str}")
        
        # Call directly, not as a task
        from pers_app.services.api_service import fetch_and_store_weather_data
        result = fetch_and_store_weather_data(hour_str)
        
        logger.info(f"Task {task_id}: Latest hour fetch complete: {result}")
        
        # 2. Schedule backfill and prediction as a chain
        workflow = chain(
            check_and_backfill_missing_hours.s(24),
            make_weather_prediction.s()
        )
        
        # Execute the chain
        chain_result = workflow()
        
        return {
            "status": "Hourly update in progress",
            "current_hour_data": result,
            "chain_id": chain_result.id
        }
        
    except Exception as e:
        logger.error(f"Task {task_id}: Error in hourly update: {str(e)}")
        raise