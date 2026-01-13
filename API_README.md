# Image Protection API - Phase 2

## Overview
FastAPI backend that wraps the image protection logic. Provides a REST API endpoint to protect images from AI-based feature extraction.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at: `http://localhost:8000`

**Note**: First startup may take 1-2 minutes to load the models (VGG19, ResNet50, Inception v3).

## API Endpoints

### 1. Root Endpoint
```
GET http://localhost:8000/
```
Returns API information.

### 2. Health Check
```
GET http://localhost:8000/health
```
Returns server health status and loaded models information.

**Response:**
```json
{
  "status": "healthy",
  "device": "cuda",
  "models_loaded": 3,
  "ensemble_mode": true
}
```

### 3. Protect Image (Main Endpoint)
```
POST http://localhost:8000/cloak
```

**Request:**
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Body**: 
  - `file`: Image file (JPEG, PNG, etc.)
  - Optional query parameters:
    - `num_iterations` (int, default: 150): Number of optimization iterations
    - `learning_rate` (float, default: 0.01): Learning rate for optimization
    - `epsilon` (float, default: 0.03): Maximum perturbation per pixel
    - `use_adaptive_epsilon` (bool, default: true): Adjust epsilon based on image
    - `robust_to_transforms` (bool, default: true): Make attack robust to JPEG/resize

**Response:**
- **Content-Type**: `image/jpeg`
- **Body**: Protected image as JPEG stream

## Testing with Postman

### Step 1: Create New Request
1. Open Postman
2. Create a new POST request
3. URL: `http://localhost:8000/cloak`

### Step 2: Configure Request
1. Go to **Body** tab
2. Select **form-data**
3. Add key: `file` (type: File)
4. Click **Select Files** and choose an image
5. (Optional) Add query parameters in **Params** tab:
   - `num_iterations`: 150
   - `learning_rate`: 0.01
   - `epsilon`: 0.03

### Step 3: Send Request
1. Click **Send**
2. Wait for processing (30-120 seconds depending on image size and iterations)
3. Response will be the protected image

### Step 4: Save Response
1. Click **Send and Download**
2. Or right-click response → **Save Response** → **Save to a file**

## Testing with cURL

### Basic Request
```bash
curl -X POST "http://localhost:8000/cloak" \
  -F "file=@art.jpg" \
  -o protected_art.jpg
```

### With Custom Parameters
```bash
curl -X POST "http://localhost:8000/cloak?num_iterations=100&epsilon=0.02" \
  -F "file=@art.jpg" \
  -o protected_art.jpg
```

### With All Parameters
```bash
curl -X POST "http://localhost:8000/cloak?num_iterations=150&learning_rate=0.01&epsilon=0.03&use_adaptive_epsilon=true&robust_to_transforms=true" \
  -F "file=@art.jpg" \
  -o protected_art.jpg
```

## Testing with Python

Create a file `test_api.py`:

```python
import requests

# Test the API
url = "http://localhost:8000/cloak"

# Open image file
with open("art.jpg", "rb") as f:
    files = {"file": ("art.jpg", f, "image/jpeg")}
    
    # Optional parameters
    params = {
        "num_iterations": 150,
        "learning_rate": 0.01,
        "epsilon": 0.03,
        "use_adaptive_epsilon": True,
        "robust_to_transforms": True
    }
    
    # Send request
    response = requests.post(url, files=files, params=params)
    
    # Save response
    if response.status_code == 200:
        with open("protected_art.jpg", "wb") as out:
            out.write(response.content)
        print("Image protected successfully!")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
```

Run:
```bash
pip install requests
python test_api.py
```

## API Features

### Async Processing
- Image processing runs in a thread pool
- Server remains responsive to other requests
- Non-blocking I/O

### Error Handling
- Validates file type
- Validates image format
- Returns appropriate HTTP status codes
- Detailed error messages

### CORS Support
- Enabled for all origins (development)
- Can be configured for specific origins in production

### Model Loading
- Models loaded once at startup
- Shared across all requests
- Efficient memory usage

## Performance

### Processing Time
- **CPU**: ~60-120 seconds per image
- **GPU**: ~30-60 seconds per image
- Depends on:
  - Image size
  - Number of iterations
  - Hardware (CPU/GPU)

### Optimization Tips
1. **Reduce iterations**: Lower `num_iterations` for faster processing (less protection)
2. **Disable ensemble**: Modify `use_ensemble=False` in `api.py` (faster but less robust)
3. **Use GPU**: Ensure CUDA is available for faster processing

## Troubleshooting

### Models Not Loading
- Check if PyTorch models are downloaded
- First run downloads models (~500MB each)
- Ensure internet connection for first run

### Out of Memory
- Reduce image size before uploading
- Use CPU instead of GPU (modify `api.py`)
- Reduce `num_iterations`

### Slow Processing
- Normal for CPU processing (30-120 seconds)
- Use GPU for faster processing
- Reduce iterations for faster results

### CORS Errors
- Already enabled for all origins
- If issues persist, check browser console

## Production Deployment

### Recommended Changes
1. **CORS**: Restrict to specific origins
2. **Rate Limiting**: Add rate limiting middleware
3. **Authentication**: Add API key authentication
4. **Logging**: Configure proper logging
5. **Monitoring**: Add health checks and metrics
6. **Queue System**: Implement Redis queue for high traffic

### Example with Gunicorn
```bash
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Next Steps (Phase 3)
- Frontend web interface
- Real-time progress updates
- Batch processing
- Queue system for multiple requests
