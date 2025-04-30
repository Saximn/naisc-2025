import requests
import json
import logging
import numpy as np
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../libs')))
from apig_sdk import signer

logger = logging.getLogger(__name__)

class ModelArtsService:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        
        # Get access and secret keys from environment variables
        self.ak = os.environ.get("HUAWEICLOUD_SDK_AK")
        self.sk = os.environ.get("HUAWEICLOUD_SDK_SK")
        
        # Validate keys are available
        if not self.ak or not self.sk:
            logger.warning("Huawei Cloud AK/SK not found in environment variables. Authentication will fail.")
        else:
            logger.info("Huawei Cloud authentication keys loaded successfully")
    
    def predict(self, grid_data):
        """
        Send prediction request to ModelArts with AK/SK authentication
        
        Parameters:
        - grid_data: Numpy array with shape (78, 110, 24, 5)
        
        Returns:
        - Prediction result with shape (78, 110, 1)
        """
        logger.info(f"Sending prediction request to {self.endpoint_url}")
        
        try:
            # Validate input shape
            if grid_data.shape[0:2] != (78, 110) or grid_data.shape[3] != 5:
                logger.error(f"Invalid grid data shape: {grid_data.shape}, expected (78, 110, 24, 5)")
                return None
                
            # Convert numpy array to list for JSON serialization
            data = {
                "values": grid_data.tolist()
            }
            
            # Create request with authentication
            method = 'POST'
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Create HTTP request for signing
            request = signer.HttpRequest(method, self.endpoint_url, headers, json.dumps(data))
            
            # Sign the request with AK/SK
            sig = signer.Signer()
            sig.Key = self.ak
            sig.Secret = self.sk
            sig.Sign(request)
            
            logger.info("Sending authenticated prediction request...")
            
            # Send the signed request
            response = requests.request(
                request.method, 
                request.scheme + "://" + request.host + request.uri, 
                headers=request.headers, 
                data=request.body,
                timeout=60  # This might need adjustment based on model complexity
            )
            
            # Check if request was successful
            if response.status_code == 200:
                logger.info("Prediction successful")
                result = response.json()
                
                # Validate the response format
                if "prediction" in result and "shape" in result:
                    prediction_shape = result["shape"]
                    logger.info(f"Received prediction with shape {prediction_shape}")
                    
                    # Expected shape is (78, 110, 1)
                    if len(prediction_shape) == 3 and prediction_shape[0] == 78 and prediction_shape[1] == 110:
                        return result
                    else:
                        logger.error(f"Unexpected prediction shape: {prediction_shape}")
                        return None
                else:
                    logger.error("Prediction response missing expected fields")
                    return None
            else:
                logger.error(f"Error from ModelArts API: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception calling ModelArts API: {str(e)}")
            return None