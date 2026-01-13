"""
FastAPI Backend for Image Protection
Provides REST API endpoint to protect images via adversarial attacks.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from protect import ImageProtector
import torch
from PIL import Image
import io
import asyncio
from typing import Optional, Tuple
import uvicorn
from contextlib import asynccontextmanager
import logging
import time
from pydantic import BaseModel, Field
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_DIMENSION = 4096  # Max width or height
MIN_IMAGE_DIMENSION = 64  # Min width or height
MAX_ITERATIONS = 500
MIN_ITERATIONS = 10
DEFAULT_TIMEOUT = 600  # 10 minutes

# Global ImageProtector instance (loaded once at startup)
protector: Optional[ImageProtector] = None


class ProtectionResponse(BaseModel):
    """Response model for protection metrics."""
    request_id: str
    success: bool
    processing_time: float
    metrics: dict
    message: str


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


def resize_image_if_needed(pil_image: Image.Image, max_dimension: int = MAX_IMAGE_DIMENSION) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions to prevent memory issues.
    
    Args:
        pil_image: PIL Image to resize
        max_dimension: Maximum width or height
        
    Returns:
        Resized PIL Image (or original if within limits)
    """
    width, height = pil_image.size
    
    if width > max_dimension or height > max_dimension:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return pil_image.resize((new_width, new_height), Image.LANCZOS)
    
    return pil_image


def validate_parameters(num_iterations: int, learning_rate: float, epsilon: float):
    """
    Validate API parameters are within acceptable ranges.
    
    Args:
        num_iterations: Number of iterations
        learning_rate: Learning rate
        epsilon: Epsilon value
        
    Raises:
        ValueError: If parameters are out of range
    """
    if not (MIN_ITERATIONS <= num_iterations <= MAX_ITERATIONS):
        raise ValueError(
            f"num_iterations must be between {MIN_ITERATIONS} and {MAX_ITERATIONS}, got {num_iterations}"
        )
    
    if not (0.0001 <= learning_rate <= 1.0):
        raise ValueError(
            f"learning_rate must be between 0.0001 and 1.0, got {learning_rate}"
        )
    
    if not (0.001 <= epsilon <= 0.1):
        raise ValueError(
            f"epsilon must be between 0.001 and 0.1, got {epsilon}"
        )


def process_image_sync(image_bytes: bytes, 
                       num_iterations: int = 150,
                       learning_rate: float = 0.01,
                       epsilon: float = 0.03,
                       use_adaptive_epsilon: bool = True,
                       robust_to_transforms: bool = True,
                       request_id: str = None) -> Tuple[bytes, dict]:
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
        request_id: Unique request identifier for logging
        
    Returns:
        Tuple of (processed image bytes, metrics dictionary)
    """
    import tempfile
    import os
    start_time = time.time()
    
    temp_input_path = None
    temp_output_path = None
    
    try:
        # Validate parameters
        validate_parameters(num_iterations, learning_rate, epsilon)
        
        # Validate and convert image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Validate image dimensions
        width, height = pil_image.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise ValueError(
                f"Image too small: {width}x{height}. Minimum: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}"
            )
        
        # Resize if too large (prevents memory issues)
        pil_image = resize_image_if_needed(pil_image)
        
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
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Add processing time to metrics
        metrics['processing_time_seconds'] = processing_time
        metrics['request_id'] = request_id or 'unknown'
        
        logger.info(
            f"[{request_id}] Image processed successfully. "
            f"Feature distance: {metrics.get('avg_feature_distance', 0):.2f}, "
            f"Time: {processing_time:.2f}s"
        )
        
        return processed_bytes, metrics
        
    except ValueError as e:
        # Parameter validation errors
        logger.warning(f"[{request_id}] Validation error: {e}")
        raise
    except torch.cuda.OutOfMemoryError as e:
        # GPU out of memory
        logger.error(f"[{request_id}] GPU out of memory: {e}")
        raise RuntimeError("GPU out of memory. Try using a smaller image or CPU mode.")
    except MemoryError as e:
        # System out of memory
        logger.error(f"[{request_id}] System out of memory: {e}")
        raise RuntimeError("System out of memory. Try using a smaller image.")
    except Exception as e:
        logger.error(f"[{request_id}] Error processing image: {e}", exc_info=True)
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


@app.post("/cloak", response_class=StreamingResponse)
async def cloak_image(
    file: UploadFile = File(..., description="Image file to protect"),
    num_iterations: int = Query(150, ge=MIN_ITERATIONS, le=MAX_ITERATIONS, description="Number of optimization iterations"),
    learning_rate: float = Query(0.01, ge=0.0001, le=1.0, description="Learning rate for optimization"),
    epsilon: float = Query(0.03, ge=0.001, le=0.1, description="Maximum perturbation per pixel"),
    use_adaptive_epsilon: bool = Query(True, description="Adjust epsilon based on image characteristics"),
    robust_to_transforms: bool = Query(True, description="Make attack robust to JPEG compression and resizing"),
    return_metrics: bool = Query(False, description="Return metrics as JSON instead of image (for testing)")
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
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    
    try:
        # Read uploaded file
        logger.info(f"[{request_id}] Processing image: {file.filename}, size: {file.size} bytes")
        image_bytes = await file.read()
        
        # Validate file size
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(image_bytes) / 1024 / 1024:.2f}MB. Maximum: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Validate image can be opened
        try:
            test_image = Image.open(io.BytesIO(image_bytes))
            test_image.verify()
            # Reopen after verify (verify closes the image)
            test_image = Image.open(io.BytesIO(image_bytes))
            width, height = test_image.size
            
            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image too small: {width}x{height}. Minimum: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Process image in thread pool (non-blocking)
        # This allows the event loop to handle other requests
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,  # Use default thread pool
                process_image_sync,
                image_bytes,
                num_iterations,
                learning_rate,
                epsilon,
                use_adaptive_epsilon,
                robust_to_transforms,
                request_id
            ),
            timeout=DEFAULT_TIMEOUT
        )
        
        processed_bytes, metrics = result
        
        # If return_metrics is True, return JSON instead of image
        if return_metrics:
            return JSONResponse(content={
                "request_id": request_id,
                "success": True,
                "processing_time": metrics.get('processing_time_seconds', 0),
                "metrics": metrics,
                "message": "Image processed successfully"
            })
        
        # Return processed image as streaming response with metrics in headers
        return StreamingResponse(
            io.BytesIO(processed_bytes),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'attachment; filename="protected_{file.filename or "image.jpg"}"',
                "X-Request-ID": request_id,
                "X-Processing-Time": f"{metrics.get('processing_time_seconds', 0):.2f}",
                "X-Feature-Distance": f"{metrics.get('avg_feature_distance', 0):.2f}"
            }
        )
    
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Request timed out after {DEFAULT_TIMEOUT}s")
        raise HTTPException(
            status_code=504,
            detail=f"Request timed out. Processing took longer than {DEFAULT_TIMEOUT} seconds."
        )
    except ValueError as e:
        # Parameter validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Memory errors
        raise HTTPException(status_code=507, detail=str(e))
    except Exception as e:
        logger.error(f"[{request_id}] Error in /cloak endpoint: {e}", exc_info=True)
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
