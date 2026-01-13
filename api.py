"""
FastAPI Backend for Image Protection
Provides REST API endpoint to protect images via adversarial attacks.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from protect import ImageProtector
import torch
from PIL import Image
import io
import asyncio
from typing import Optional
import uvicorn
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global ImageProtector instance (loaded once at startup)
protector: Optional[ImageProtector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Loads models at startup, cleans up at shutdown.
    """
    global protector
    
    # Startup: Load models
    logger.info("Loading ImageProtector models...")
    try:
        # Initialize with ensemble for robust protection
        protector = ImageProtector(use_ensemble=True)
        logger.info("ImageProtector loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load ImageProtector: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down...")
    protector = None


# Create FastAPI app with lifespan
app = FastAPI(
    title="Image Protection API",
    description="Protect images from AI-based feature extraction using adversarial attacks",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware (allow frontend to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_image_sync(image_bytes: bytes, 
                       num_iterations: int = 150,
                       learning_rate: float = 0.01,
                       epsilon: float = 0.03,
                       use_adaptive_epsilon: bool = True,
                       robust_to_transforms: bool = True) -> bytes:
    """
    Synchronous image processing function.
    This runs in a thread pool to avoid blocking the event loop.
    
    Args:
        image_bytes: Raw image bytes from upload
        num_iterations: Number of optimization iterations
        learning_rate: Learning rate for optimization
        epsilon: Maximum perturbation allowed
        use_adaptive_epsilon: Whether to use adaptive epsilon
        robust_to_transforms: Whether to make attack robust to transformations
        
    Returns:
        Processed image bytes (JPEG format)
    """
    import tempfile
    import os
    
    temp_input_path = None
    temp_output_path = None
    
    try:
        # Validate and convert image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Ensure RGB mode
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            pil_image.save(temp_file, format='JPEG', quality=95)
            temp_input_path = temp_file.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_output:
            temp_output_path = temp_output.name
        
        # Process the image using ImageProtector
        # Note: This suppresses print statements for cleaner API logs
        import sys
        from io import StringIO
        
        # Capture stdout to reduce noise in API logs
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            metrics = protector.protect_image(
                input_path=temp_input_path,
                output_path=temp_output_path,
                num_iterations=num_iterations,
                learning_rate=learning_rate,
                epsilon=epsilon,
                use_adaptive_epsilon=use_adaptive_epsilon,
                robust_to_transforms=robust_to_transforms,
                feature_weight=1.0,
                pixel_weight=0.1,
                perceptual_weight=0.5
            )
        finally:
            sys.stdout = old_stdout
        
        # Read processed image
        with open(temp_output_path, 'rb') as f:
            processed_bytes = f.read()
        
        logger.info(f"Image processed successfully. Feature distance: {metrics.get('avg_feature_distance', 0):.2f}")
        
        return processed_bytes
        
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise
    finally:
        # Cleanup temporary files
        for path in [temp_input_path, temp_output_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {path}: {e}")


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "Image Protection API",
        "version": "1.0.0",
        "endpoints": {
            "POST /cloak": "Protect an image from AI feature extraction",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if protector is None:
        raise HTTPException(status_code=503, detail="ImageProtector not loaded")
    
    return {
        "status": "healthy",
        "device": str(protector.device),
        "models_loaded": len(protector.models),
        "ensemble_mode": protector.use_ensemble
    }


@app.post("/cloak")
async def cloak_image(
    file: UploadFile = File(..., description="Image file to protect"),
    num_iterations: int = 150,
    learning_rate: float = 0.01,
    epsilon: float = 0.03,
    use_adaptive_epsilon: bool = True,
    robust_to_transforms: bool = True
):
    """
    Protect an image from AI-based feature extraction.
    
    This endpoint accepts an image file and returns a protected version
    that looks identical to humans but confuses AI feature extractors.
    
    Args:
        file: Image file to protect (JPEG, PNG, etc.)
        num_iterations: Number of optimization iterations (default: 150)
        learning_rate: Learning rate for optimization (default: 0.01)
        epsilon: Maximum perturbation per pixel (default: 0.03)
        use_adaptive_epsilon: Adjust epsilon based on image (default: True)
        robust_to_transforms: Make attack robust to JPEG/resize (default: True)
        
    Returns:
        Protected image as JPEG stream
    """
    # Check if protector is loaded
    if protector is None:
        raise HTTPException(
            status_code=503,
            detail="ImageProtector not initialized. Please wait for models to load."
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected image file."
        )
    
    try:
        # Read uploaded file
        logger.info(f"Processing image: {file.filename}, size: {file.size} bytes")
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Validate image can be opened
        try:
            test_image = Image.open(io.BytesIO(image_bytes))
            test_image.verify()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Process image in thread pool (non-blocking)
        # This allows the event loop to handle other requests
        loop = asyncio.get_event_loop()
        processed_bytes = await loop.run_in_executor(
            None,  # Use default thread pool
            process_image_sync,
            image_bytes,
            num_iterations,
            learning_rate,
            epsilon,
            use_adaptive_epsilon,
            robust_to_transforms
        )
        
        # Return processed image as streaming response
        return StreamingResponse(
            io.BytesIO(processed_bytes),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'attachment; filename="protected_{file.filename or "image.jpg"}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /cloak endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
