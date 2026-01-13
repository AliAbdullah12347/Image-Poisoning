# Testing Guide - Image Protection API

## Quick Start Testing

### Step 1: Install Dependencies

First, make sure all required packages are installed:

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI
- uvicorn (ASGI server)
- requests (for testing)
- All PyTorch dependencies

### Step 2: Prepare a Test Image

You need an image file to test with. Place it in the project directory:

- Name it `art.jpg` (or any name)
- Supported formats: JPEG, PNG, BMP, etc.
- Any size works (smaller images process faster)

**Tip**: If you don't have an image, download one from the internet or use any photo from your computer.

### Step 3: Start the API Server

Open a terminal/command prompt in the project directory and run:

```bash
python api.py
```

**What you'll see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Loading ImageProtector models...
Using device: cuda (or cpu)
Ensemble mode: True
Loading VGG19...
Loading ResNet50...
Loading Inception v3...
INFO:     ImageProtector loaded successfully!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Important Notes:**
- First startup takes 1-2 minutes (downloading models if needed)
- Keep this terminal open - the server must be running
- The server runs on `http://localhost:8000`

### Step 4: Test the API

You have several options to test:

---

## Method 1: Python Test Script (Easiest)

**In a NEW terminal** (keep the server running in the first terminal):

```bash
# Install requests if not already installed
pip install requests

# Run the test script
python test_api.py
```

Or with a custom image:
```bash
python test_api.py your_image.jpg output_protected.jpg
```

**Expected Output:**
```
Testing Image Protection API...
Input: art.jpg
Output: protected_art.jpg
URL: http://localhost:8000/cloak

1. Checking server health...
   ✓ Server is healthy
   Device: cuda
   Models loaded: 3

2. Uploading image...
   Parameters: {'num_iterations': 150, ...}
   Processing (this may take 30-120 seconds)...
   
3. ✓ Success!
   Protected image saved: protected_art.jpg
   File size: 245.67 KB
```

---

## Method 2: Using cURL (Command Line)

**In a NEW terminal** (keep server running):

### Basic Test:
```bash
curl -X POST "http://localhost:8000/cloak" \
  -F "file=@art.jpg" \
  -o protected_art.jpg
```

### With Custom Parameters:
```bash
curl -X POST "http://localhost:8000/cloak?num_iterations=100&epsilon=0.02" \
  -F "file=@art.jpg" \
  -o protected_art.jpg
```

**What happens:**
- Uploads `art.jpg`
- Waits 30-120 seconds (processing)
- Saves result to `protected_art.jpg`

---

## Method 3: Using Postman (GUI)

### Setup:
1. **Download Postman** (if not installed): https://www.postman.com/downloads/

2. **Create New Request:**
   - Click "New" → "HTTP Request"
   - Method: **POST**
   - URL: `http://localhost:8000/cloak`

3. **Configure Body:**
   - Go to **Body** tab
   - Select **form-data**
   - Add key: `file` (change type to **File**)
   - Click **Select Files** and choose your image

4. **Add Parameters (Optional):**
   - Go to **Params** tab
   - Add query parameters:
     - `num_iterations`: 150
     - `learning_rate`: 0.01
     - `epsilon`: 0.03
     - `use_adaptive_epsilon`: true
     - `robust_to_transforms`: true

5. **Send Request:**
   - Click **Send**
   - Wait 30-120 seconds
   - Response will be the protected image

6. **Save Response:**
   - Click **Send and Download** (or)
   - Right-click response → **Save Response** → **Save to a file**

---

## Method 4: Using Python Requests (Custom Script)

Create a file `my_test.py`:

```python
import requests

url = "http://localhost:8000/cloak"

# Open image
with open("art.jpg", "rb") as f:
    files = {"file": ("art.jpg", f, "image/jpeg")}
    params = {
        "num_iterations": 150,
        "epsilon": 0.03
    }
    
    print("Sending request...")
    response = requests.post(url, files=files, params=params, timeout=300)
    
    if response.status_code == 200:
        with open("protected_art.jpg", "wb") as out:
            out.write(response.content)
        print("Success! Image saved as protected_art.jpg")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
```

Run:
```bash
pip install requests
python my_test.py
```

---

## Method 5: Test Health Endpoint (Quick Check)

Before testing the main endpoint, verify the server is running:

### Browser:
Open: `http://localhost:8000/health`

### cURL:
```bash
curl http://localhost:8000/health
```

### Python:
```python
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())
```

**Expected Response:**
```json
{
  "status": "healthy",
  "device": "cuda",
  "models_loaded": 3,
  "ensemble_mode": true
}
```

---

## What to Expect

### Processing Time:
- **CPU**: 60-120 seconds
- **GPU**: 30-60 seconds
- Depends on image size and iterations

### Success Indicators:
- ✅ Status code: 200
- ✅ Response is a JPEG image
- ✅ File size similar to original
- ✅ Image looks identical to original (to human eye)

### Output:
- Protected image saved to specified location
- Image should look identical to original
- But AI models will see different features

---

## Troubleshooting

### Problem: "Could not connect to server"
**Solution:**
- Make sure `python api.py` is running
- Check it's running on port 8000
- Try `http://127.0.0.1:8000` instead of `localhost:8000`

### Problem: "503 Service Unavailable"
**Solution:**
- Models are still loading (wait 1-2 minutes)
- Check server terminal for loading progress
- Try health endpoint to check status

### Problem: "400 Bad Request"
**Solution:**
- Check file is a valid image
- Ensure file is not empty
- Try a different image format (JPEG recommended)

### Problem: "Timeout Error"
**Solution:**
- Processing takes 30-120 seconds (normal)
- Increase timeout in your client
- For Python: `timeout=300` (5 minutes)

### Problem: "Out of Memory"
**Solution:**
- Use smaller image
- Reduce `num_iterations` (e.g., 50-100)
- Close other applications

### Problem: Models Not Loading
**Solution:**
- First run downloads models (~500MB each)
- Ensure internet connection
- Wait for download to complete
- Check disk space

---

## Quick Test Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test image prepared (`art.jpg` or any image)
- [ ] Server started (`python api.py`)
- [ ] Health check passes (`http://localhost:8000/health`)
- [ ] Test request sent (using any method above)
- [ ] Protected image received and saved
- [ ] Image looks identical to original

---

## Example: Complete Test Session

```bash
# Terminal 1: Start server
cd "C:\Users\hp\Downloads\Colgate\Image Poisoning"
python api.py

# Terminal 2: Test (wait for server to finish loading)
python test_api.py art.jpg protected_art.jpg

# Or use curl
curl -X POST "http://localhost:8000/cloak" -F "file=@art.jpg" -o protected_art.jpg
```

---

## Next Steps

Once testing works:
1. ✅ API is ready for frontend integration
2. ✅ Can be used in production
3. ✅ Ready for Phase 3 (Frontend)

For more details, see `API_README.md`
