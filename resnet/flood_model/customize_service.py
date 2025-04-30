import base64
import io
import os
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from model_service.pytorch_model_service import PTServingBaseService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === Channel normalizer ===
class ChannelNormalizer:
    def __init__(self, mean, std):
        # mean/std shape (C,) → (1, C, 1, 1) for broadcasting
        self.mean = torch.tensor(mean, dtype=torch.float32)[None, :, None, None]
        self.std = torch.tensor(std, dtype=torch.float32)[None, :, None, None]
    
    def __call__(self, x):
        # x: Tensor of shape (T_in, C, H, W)
        return (x - self.mean) / self.std

def predict_single_frame_scaled(frame_np, model, normalizer, device):
    """
    Predict and robust-scale a single frame.
    
    Args:
      frame_np: np.ndarray, shape (H, W, T_in, C)
      model: trained ConvLSTMForecast in eval() mode
      normalizer: ChannelNormalizer
      device: torch.device
      
    Returns:
      np.ndarray of shape (H, W, 1) with values clipped to [0,1]
    """
    # 1. To tensor & permute (T_in, C, H, W)
    x = torch.from_numpy(frame_np).float().permute(2, 3, 0, 1)
    # 2. Normalize
    x = normalizer(x)
    # 3. Batch dim: (1, T_in, C, H, W)
    x = x.unsqueeze(0).to(device)
    
    # 4. Inference
    with torch.no_grad():
        pred = model(x)  # (1,1,H,W)
    pred_np = pred.squeeze().cpu().numpy()  # (H, W)
    min_val = pred_np.min()
    if min_val < 0:
        pred_np = pred_np - min_val
    clipped = np.clip(pred_np, 0, 1)
    # 5. Reshape to (H, W, 1)
    clipped = clipped.reshape(clipped.shape[0], clipped.shape[1], 1)
    return clipped

# === 7. ConvLSTM model ===
class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size):
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv2d(input_dim + hidden_dim, 4*hidden_dim, kernel_size, padding=padding)
        self.hidden_dim = hidden_dim

    def forward(self, x, h, c):
        combined = torch.cat([x, h], dim=1)
        ci, cf, co, cg = self.conv(combined).chunk(4, dim=1)
        i = torch.sigmoid(ci); f = torch.sigmoid(cf)
        o = torch.sigmoid(co); g = torch.tanh(cg)
        c_next = f * c + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

class ConvLSTMForecast(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size):
        super().__init__()
        self.cell = ConvLSTMCell(input_dim, hidden_dim, kernel_size)
        self.conv_out = nn.Conv2d(hidden_dim, 1, kernel_size=1)
    def forward(self, x):
        # x: (batch, T_in, C, H, W)
        b, T_in, C, H, W = x.size()
        h = torch.zeros(b, self.cell.hidden_dim, H, W, device=x.device)
        c = torch.zeros_like(h)
        for t in range(T_in):
            h, c = self.cell(x[:,t], h, c)
        return self.conv_out(h)  # (batch, 1, H, W)

class ForecastService(PTServingBaseService):
    def __init__(self, model_name, model_path):
        super(ForecastService, self).__init__(model_name, model_path)
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.normalizer = None
        self.load_model()
        logger.info(f"Model loaded successfully on device: {self.device}")
    
    def load_model(self):
        try:
            # Get the directory containing the model file
            dir_path = os.path.dirname(os.path.realpath(self.model_path))
            
            # Load the PyTorch model
            model_file = self.model_path
            logger.info(f"Loading model from: {model_file}")
            self.model = ConvLSTMForecast(input_dim=5, hidden_dim=64, kernel_size=3).to(self.device)
            checkpoint = torch.load(model_file, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                normalizer = checkpoint.get('normalizer', None)
                if normalizer:
                    self.normalizer = ChannelNormalizer(mean=normalizer['mean'], std=normalizer['std'])
                else:
                    logger.warning("No normalizer found in checkpoint, using default values")
                    self.normalizer = ChannelNormalizer(mean=[1], std=[0])
            else:
                self.model.load_state_dict(checkpoint)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def _preprocess(self, data):
        """
        Preprocess the input data.
        Expected input: 78x110x24x5 values (H=78, W=110, T=24, C=5)
        Output to model: Properly formatted tensor for model processing
        """
        try:
            logger.info(f"Received data type: {type(data)}")
            preprocessed_data = {}
            
            # Handle base64-encoded .npy input
            if 'npy_base64' in data:
                logger.info("Detected npy_base64 input")

                # Decode base64 and load the array
                decoded = base64.b64decode(data['npy_base64'])
                frame_np = np.load(io.BytesIO(decoded), allow_pickle=False)
            else:
                # Handle JSON input
                if not any(isinstance(val, dict) for val in data.values()):
                    logger.info("Processing JSON input data")
                    # Try to find the input data with common keys
                    frame_key = next((k for k in ['data', 'frame', 'input', 'values'] if k in data), None)
                    
                    if frame_key is None:
                        # If no expected key is found, use the first key
                        frame_key = list(data.keys())[0]
                    
                    frame_data = data[frame_key]
                    frame_np = np.array(frame_data, dtype=np.float32)
                    
                    logger.info(f"Original input shape: {frame_np.shape}")
                    
                    # Check if we have the expected 78x110x24x5 shape
                    if frame_np.shape != (78, 110, 24, 5):
                        # Try to reshape if the total number of elements matches
                        if frame_np.size == 78 * 110 * 24 * 5:
                            frame_np = frame_np.reshape(78, 110, 24, 5)
                        else:
                            logger.warning(f"Input shape {frame_np.shape} doesn't match expected (78, 110, 24, 5)")
                    
                    logger.info(f"Processed JSON input to shape: {frame_np.shape}")
                
                # Handle file uploads (multipart/form-data)
                else:
                    logger.info("Processing file upload")
                    for k, v in data.items():
                        if isinstance(v, dict):
                            for file_name, file_content in v.items():
                                logger.info(f"Processing file: {file_name}")
                                
                                # Handle numpy files
                                if file_name.endswith('.npy'):
                                    frame_np = np.load(file_content)
                                elif file_name.endswith('.npz'):
                                    with np.load(file_content) as npz_data:
                                        # Use the first array in the archive
                                        first_key = list(npz_data.keys())[0]
                                        frame_np = npz_data[first_key]
                                else:
                                    # Try to interpret as numpy anyway
                                    try:
                                        frame_np = np.load(file_content)
                                    except Exception as e:
                                        raise ValueError(f"Unsupported file format: {file_name}. Error: {str(e)}")
                                
                                logger.info(f"Original file shape: {frame_np.shape}")
                                
                                # Check if we have the expected 78x110x24x5 shape
                                if frame_np.shape != (78, 110, 24, 5):
                                    # Try to reshape if the total number of elements matches
                                    if frame_np.size == 78 * 110 * 24 * 5:
                                        frame_np = frame_np.reshape(78, 110, 24, 5)
                                    else:
                                        logger.warning(f"Input shape {frame_np.shape} doesn't match expected (78, 110, 24, 5)")
            
            # Final validation
            if frame_np.shape != (78, 110, 24, 5):
                logger.warning(f"Final shape {frame_np.shape} doesn't match expected (78, 110, 24, 5)")
            
            frame_np = frame_np.astype(np.float32)  # Ensure float32 type
            preprocessed_data['frame'] = frame_np
            return preprocessed_data
            
        except Exception as e:
            logger.error(f"Error during preprocessing: {str(e)}")
            raise
    
    def _inference(self, data):
        """
        Run inference with the preprocessed data.
        """
        try:
            frame_np = data.get('frame')
            if frame_np is None:
                raise ValueError("No frame data found in the preprocessed input")
                
            logger.info(f"Running inference on frame with shape: {frame_np.shape}")
                
            result = predict_single_frame_scaled(
                frame_np=frame_np,
                model=self.model,
                normalizer=self.normalizer,
                device=self.device
            )
            
            logger.info(f"Inference complete, result shape: {result.shape}")
            return {'prediction': result}
            
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            raise
    
    def _postprocess(self, data):
        """
        Postprocess the inference result.
        Expected output from model: 3D array of shape (78, 110, 1)
        Output to API: flat JSON with prediction values and shape information
        """
        try:
            prediction = data.get('prediction')
            logger.info(f"Postprocessing prediction with shape: {prediction.shape}")
            
            # Ensure we have the expected 78x110x1 output shape
            if prediction.shape != (78, 110, 1):
                logger.warning(f"Output shape {prediction.shape} doesn't match expected (78, 110, 1)")
                # Attempt to reshape if needed and possible
                if prediction.size == 78 * 110:
                    prediction = prediction.reshape(78, 110, 1)
            
            # Convert numpy array to list for JSON serialization
            result = {
                "prediction": prediction.tolist(),
                "shape": [78, 110, 1],  # Explicitly state the expected shape
                "min": float(prediction.min()),
                "max": float(prediction.max()),
                "mean": float(prediction.mean())
            }
            
            logger.info("Postprocessing complete")
            return result
            
        except Exception as e:
            logger.error(f"Error during postprocessing: {str(e)}")
            raise