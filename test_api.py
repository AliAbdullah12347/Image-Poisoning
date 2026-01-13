"""
Simple test script for the Image Protection API.
Tests the /cloak endpoint with a sample image.
"""

import requests
import sys
import os
from pathlib import Path

def test_api(image_path: str = "art.jpg", output_path: str = "protected_art.jpg"):
    """
    Test the /cloak API endpoint.
    
    Args:
        image_path: Path to input image
        output_path: Path to save protected image
    """
    url = "http://localhost:8000/cloak"
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found!")
        print("Please provide a valid image file.")
        return False
    
    print(f"Testing Image Protection API...")
    print(f"Input: {image_path}")
    print(f"Output: {output_path}")
    print(f"URL: {url}\n")
    
    try:
        # Test health endpoint first
        print("1. Checking server health...")
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✓ Server is healthy")
            print(f"   Device: {health_data.get('device')}")
            print(f"   Models loaded: {health_data.get('models_loaded')}")
        else:
            print(f"   ✗ Server health check failed: {health_response.status_code}")
            return False
        
        # Open and send image
        print(f"\n2. Uploading image...")
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            
            # Optional parameters
            params = {
                "num_iterations": 150,
                "learning_rate": 0.01,
                "epsilon": 0.03,
                "use_adaptive_epsilon": "true",
                "robust_to_transforms": "true"
            }
            
            print(f"   Parameters: {params}")
            print(f"   Processing (this may take 30-120 seconds)...")
            
            # Send request
            response = requests.post(url, files=files, params=params, timeout=300)
        
        # Check response
        if response.status_code == 200:
            # Save protected image
            with open(output_path, "wb") as out:
                out.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"\n3. ✓ Success!")
            print(f"   Protected image saved: {output_path}")
            print(f"   File size: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"\n3. ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server!")
        print("   Make sure the API server is running:")
        print("   python api.py")
        return False
    except requests.exceptions.Timeout:
        print("\n✗ Error: Request timed out!")
        print("   The image processing took too long.")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == "__main__":
    # Get image path from command line or use default
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "art.jpg"
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = "protected_art.jpg"
    
    success = test_api(image_path, output_path)
    sys.exit(0 if success else 1)
