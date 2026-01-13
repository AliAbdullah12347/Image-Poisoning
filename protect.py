"""
Image Protection Script - Phase 1
Performs adversarial attack on images to protect them from feature extraction.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
from typing import Tuple, Optional


class ImageProtector:
    """
    Class to handle image protection using adversarial attacks.
    Uses VGG19 feature extractor to perform the attack.
    """
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize the ImageProtector.
        
        Args:
            device: Device to run computations on ('cuda' or 'cpu').
                   If None, automatically selects based on availability.
        """
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        # Load pre-trained VGG19 model (frozen, no training)
        self.model = models.vgg19(pretrained=True).to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        # Freeze all parameters
        for param in self.model.features.parameters():
            param.requires_grad = False
        
        # Image preprocessing transforms
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Inverse transform to convert back to image
        self.inverse_transform = transforms.Compose([
            transforms.Normalize(mean=[-0.485/0.229, -0.456/0.224, -0.406/0.225],
                               std=[1/0.229, 1/0.224, 1/0.225]),
            transforms.ToPILImage()
        ])
        
        # Feature extractor hook (will be set when needed)
        self.feature_maps = None
        self.hook_handle = None
    
    def load_image(self, image_path: str) -> torch.Tensor:
        """
        Load and preprocess an image.
        
        Args:
            image_path: Path to the input image file.
            
        Returns:
            Preprocessed image tensor.
        """
        # Step 1: Open the image file using PIL (Python Imaging Library)
        # PIL.Image.open() can handle JPEG, PNG, BMP, and other common formats
        pil_image = Image.open(image_path)
        
        # Step 2: Convert to RGB mode if needed
        # Some images might be grayscale (L mode) or have alpha channel (RGBA mode)
        # VGG19 expects RGB (3 channels: Red, Green, Blue)
        # .convert('RGB') ensures we always have exactly 3 channels
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Step 3: Apply preprocessing transforms
        # self.transform does two things:
        #   a) transforms.ToTensor(): Converts PIL Image to PyTorch Tensor
        #      - Changes shape from (H, W, C) to (C, H, W) [channels first]
        #      - Converts pixel values from 0-255 integers to 0.0-1.0 floats
        #   b) transforms.Normalize(): Normalizes each RGB channel
        #      - Formula: (pixel - mean) / std for each channel
        #      - This centers and scales the data to match ImageNet statistics
        #      - Result: values roughly in range [-2, +2]
        tensor = self.transform(pil_image)
        
        # Step 4: Add batch dimension
        # PyTorch models expect batch dimension: (batch_size, channels, height, width)
        # Current shape: (3, H, W) -> Target shape: (1, 3, H, W)
        # unsqueeze(0) adds a dimension at position 0 (the batch dimension)
        tensor = tensor.unsqueeze(0)
        
        # Step 5: Move tensor to the correct device (GPU or CPU)
        # .to(self.device) ensures the tensor is on the same device as the model
        # This is crucial for GPU acceleration - tensors and model must be on same device
        tensor = tensor.to(self.device)
        
        return tensor  # Shape: (1, 3, H, W) - ready for model input
    
    def extract_features(self, image_tensor: torch.Tensor, layer_name: str = 'style') -> torch.Tensor:
        """
        Extract feature maps from a specified layer of VGG19.
        
        Args:
            image_tensor: Preprocessed image tensor.
            layer_name: Name of the layer to extract features from.
            
        Returns:
            Feature maps from the specified layer.
        """
        # VGG19 architecture has 5 blocks of convolutional layers
        # We want to extract from a "style" layer - typically conv4_1 or conv5_1
        # These layers capture texture, patterns, and high-level features
        # Layer 21 = conv4_1 (after 4th max pooling) - good balance of detail and abstraction
        
        # Define which layer to extract from (VGG19.features is the convolutional part)
        # VGG19 structure: features[0-36] are conv layers, then classifier layers
        # We use layer 21 (conv4_1) which is a good "style" representation layer
        target_layer_index = 21  # conv4_1 layer
        
        # Clear any previous feature maps
        self.feature_maps = None
        
        # Define a hook function - this is called automatically during forward pass
        # Hooks are PyTorch's way to intercept and capture intermediate layer outputs
        def hook_fn(module, input, output):
            """
            Hook function that captures the output of a layer.
            
            Args:
                module: The layer module that called this hook
                input: Input tensor to the layer (tuple)
                output: Output tensor from the layer (what we want to capture)
            """
            # Store the output feature maps
            # We clone() to create a copy, so we can use it after the forward pass
            self.feature_maps = output.clone()
        
        # Register the hook on the target layer
        # register_forward_hook() attaches our function to the layer
        # When the layer processes data, it will call hook_fn and pass its output
        handle = self.model.features[target_layer_index].register_forward_hook(hook_fn)
        
        # Perform forward pass through the model's feature extractor
        # torch.no_grad() disables gradient computation (we don't need gradients here)
        # This saves memory and speeds up computation
        with torch.no_grad():
            # Forward pass: image -> conv layers -> feature maps
            # We only go through .features (conv layers), not .classifier (FC layers)
            _ = self.model.features(image_tensor)
            # The underscore _ means we ignore the return value
            # We care about the hook capturing the intermediate output, not the final output
        
        # Extract the captured feature maps
        # After forward pass, hook_fn has stored the output in self.feature_maps
        features = self.feature_maps
        
        # Remove the hook to free up memory and prevent interference
        # Hooks stay attached if not removed, which can cause memory leaks
        handle.remove()
        
        return features  # Shape: (1, 512, H/16, W/16) approximately - feature representation
    
    def compute_loss(self, original_features: torch.Tensor, 
                    perturbed_features: torch.Tensor,
                    original_image: torch.Tensor,
                    perturbed_image: torch.Tensor,
                    feature_weight: float = 1.0,
                    pixel_weight: float = 0.1) -> torch.Tensor:
        """
        Compute the loss function.
        Maximize distance between features, minimize pixel difference.
        
        Args:
            original_features: Features from original image.
            perturbed_features: Features from perturbed image.
            original_image: Original image tensor.
            perturbed_image: Perturbed image tensor.
            feature_weight: Weight for feature distance term.
            pixel_weight: Weight for pixel difference term.
            
        Returns:
            Computed loss value.
        """
        # === PART 1: Feature Distance Term (we want to MAXIMIZE this) ===
        # Goal: Make the feature representations as different as possible
        # This confuses the model - it can't recognize the image properly
        
        # Calculate the difference between feature maps
        # perturbed_features - original_features gives us the difference tensor
        feature_diff = perturbed_features - original_features
        
        # Calculate L2 norm squared (Euclidean distance squared)
        # torch.norm(..., p=2) computes: sqrt(sum(x²)) for all elements
        # We square it again to get: sum(x²) - this is the squared L2 norm
        # Why squared? It's smoother for optimization (no square root, better gradients)
        # This measures how "far apart" the feature representations are
        feature_distance = torch.norm(feature_diff, p=2) ** 2
        
        # === PART 2: Pixel Difference Term (we want to MINIMIZE this) ===
        # Goal: Keep the image visually similar to the original
        # This ensures humans still see the original art
        
        # Calculate the difference between images (this is the noise δ)
        # perturbed_image - original_image = δ (the perturbation we added)
        pixel_diff = perturbed_image - original_image
        
        # Calculate L2 norm squared of the pixel difference
        # This measures how much we've changed the pixels
        # Smaller value = less visible change = better visual quality
        pixel_difference = torch.norm(pixel_diff, p=2) ** 2
        
        # === PART 3: Combine into Loss Function ===
        # Optimization algorithms MINIMIZE loss, but we want to:
        #   - MAXIMIZE feature_distance (confuse the model)
        #   - MINIMIZE pixel_difference (preserve visual quality)
        # 
        # Solution: Negate the feature_distance term
        #   - Minimizing (-feature_distance) = Maximizing feature_distance ✓
        #   - Minimizing pixel_difference = Minimizing pixel_difference ✓
        #
        # Formula: L = -α * feature_distance + β * pixel_difference
        # Where:
        #   α = feature_weight (how much we care about confusing the model)
        #   β = pixel_weight (how much we care about visual similarity)
        #
        # The weights control the trade-off:
        #   - Higher feature_weight → more confusion, but might be more visible
        #   - Higher pixel_weight → better visual quality, but less confusion
        
        loss = -feature_weight * feature_distance + pixel_weight * pixel_difference
        
        return loss  # Single scalar value - what we optimize
    
    def protect_image(self, input_path: str, output_path: str,
                     num_iterations: int = 100,
                     learning_rate: float = 0.01,
                     epsilon: float = 0.03) -> None:
        """
        Main method to protect an image using adversarial attack.
        
        Args:
            input_path: Path to input image (e.g., 'art.jpg').
            output_path: Path to save protected image (e.g., 'protected_art.jpg').
            num_iterations: Number of optimization iterations.
            learning_rate: Learning rate for gradient descent.
            epsilon: Maximum perturbation allowed (L-infinity bound).
        """
        print(f"\n=== Starting Image Protection ===")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Iterations: {num_iterations}, Learning Rate: {learning_rate}, Epsilon: {epsilon}\n")
        
        # === STEP 1: Load and preprocess the original image ===
        print("Loading original image...")
        original_image = self.load_image(input_path)
        print(f"Image shape: {original_image.shape}")
        
        # === STEP 2: Extract features from the original image ===
        # This gives us the "baseline" feature representation
        # We'll compare against this to maximize the difference
        print("Extracting original features from VGG19...")
        original_features = self.extract_features(original_image)
        print(f"Original features shape: {original_features.shape}")
        
        # === STEP 3: Initialize the noise tensor (δ) ===
        # This is what we'll optimize - the perturbation to add to the image
        # torch.zeros_like() creates a tensor of zeros with same shape as original_image
        # requires_grad=True tells PyTorch to track gradients for this tensor
        # This is crucial - we'll use gradients to update δ during optimization
        print("Initializing noise tensor...")
        delta = torch.zeros_like(original_image, requires_grad=True)
        # Shape: (1, 3, H, W) - same as original_image, but all zeros initially
        
        # === STEP 4: Create optimizer ===
        # Optimizer will update delta based on computed gradients
        # Adam optimizer is adaptive - it adjusts learning rate per parameter
        # We only optimize delta, NOT the model weights (they're frozen)
        optimizer = optim.Adam([delta], lr=learning_rate)
        # [delta] is a list of tensors to optimize (just delta in our case)
        # lr=learning_rate controls step size (how big each update is)
        
        # === STEP 5: Optimization Loop ===
        # We'll iterate multiple times, gradually improving the perturbation
        print(f"\nStarting optimization ({num_iterations} iterations)...")
        print("-" * 50)
        
        for iteration in range(num_iterations):
            # --- 5a: Create perturbed image ---
            # Add the noise to the original image
            # Formula: x' = x + δ (perturbed image = original + noise)
            perturbed_image = original_image + delta
            
            # --- 5b: Apply L∞ constraint (clipping) ---
            # L∞ norm = maximum absolute value across all dimensions
            # We constrain: |δ| ≤ ε for every pixel
            # This ensures the perturbation stays small and imperceptible
            # torch.clamp() limits values to [-epsilon, epsilon] range
            delta.data = torch.clamp(delta.data, -epsilon, epsilon)
            # .data accesses the underlying tensor without gradient tracking
            # We modify .data directly to avoid breaking the computation graph
            
            # --- 5c: Recompute perturbed image after clipping ---
            # After clipping delta, we need to recompute the perturbed image
            # This ensures perturbed_image respects the epsilon constraint
            perturbed_image = original_image + delta
            
            # --- 5d: Extract features from perturbed image ---
            # Pass the perturbed image through VGG19 to get its feature representation
            # This is what we want to make different from original_features
            perturbed_features = self.extract_features(perturbed_image)
            
            # --- 5e: Compute loss function ---
            # This measures:
            #   - How different the features are (want: very different)
            #   - How different the pixels are (want: very similar)
            loss = self.compute_loss(
                original_features, 
                perturbed_features,
                original_image,
                perturbed_image
            )
            
            # --- 5f: Backward pass (compute gradients) ---
            # This is the core of gradient descent
            # loss.backward() computes gradients of loss w.r.t. all tensors with requires_grad=True
            # In our case, it computes: ∂L/∂δ (gradient of loss with respect to delta)
            # These gradients tell us which direction to update delta to minimize loss
            
            # Clear previous gradients (important!)
            # PyTorch accumulates gradients by default, so we zero them each iteration
            optimizer.zero_grad()
            
            # Compute gradients
            loss.backward()
            # After this, delta.grad contains the gradients
            
            # --- 5g: Update delta using optimizer ---
            # optimizer.step() updates delta based on the computed gradients
            # Update formula (simplified): δ = δ - lr * ∇δ
            # Where ∇δ is the gradient (delta.grad)
            # The optimizer uses a more sophisticated update (Adam algorithm)
            optimizer.step()
            
            # --- 5h: Progress reporting ---
            # Print loss every 10 iterations to monitor progress
            if (iteration + 1) % 10 == 0 or iteration == 0:
                # .item() converts single-element tensor to Python float
                # feature_dist and pixel_diff for detailed info
                feature_dist = torch.norm(perturbed_features - original_features, p=2).item()
                pixel_diff = torch.norm(delta, p=2).item()
                print(f"Iteration {iteration+1:3d}/{num_iterations} | "
                      f"Loss: {loss.item():.6f} | "
                      f"Feature Dist: {feature_dist:.2f} | "
                      f"Pixel Diff: {pixel_diff:.6f}")
        
        print("-" * 50)
        print("Optimization complete!\n")
        
        # === STEP 6: Save the protected image ===
        # After optimization, perturbed_image contains the final protected image
        print("Saving protected image...")
        self.save_image(perturbed_image, output_path)
        print(f"Protected image saved to: {output_path}")
        print("\n=== Image Protection Complete ===\n")
    
    def save_image(self, image_tensor: torch.Tensor, output_path: str) -> None:
        """
        Save a tensor as an image file.
        
        Args:
            image_tensor: Image tensor to save.
            output_path: Path where to save the image.
        """
        # Step 1: Detach from computation graph
        # .detach() creates a new tensor without gradient tracking
        # This is necessary because we're done with optimization
        # It also saves memory by breaking the connection to the computation graph
        tensor = image_tensor.detach()
        
        # Step 2: Move to CPU
        # PIL (Python Imaging Library) cannot handle GPU tensors
        # .cpu() moves the tensor from GPU to CPU memory
        # If already on CPU, this is a no-op (does nothing)
        tensor = tensor.cpu()
        
        # Step 3: Remove batch dimension
        # Current shape: (1, 3, H, W) - has batch dimension
        # Target shape: (3, H, W) - no batch dimension
        # squeeze(0) removes dimension at index 0 if it has size 1
        tensor = tensor.squeeze(0)
        
        # Step 4: Clamp values to valid range
        # After denormalization, some values might be slightly outside [0, 1]
        # This can happen due to numerical precision or optimization artifacts
        # torch.clamp() ensures all values are in [0, 1] range
        # Values < 0 become 0, values > 1 become 1
        tensor = torch.clamp(tensor, 0.0, 1.0)
        
        # Step 5: Apply inverse transform
        # self.inverse_transform does:
        #   a) Denormalize: (tensor * std) + mean (reverses normalization)
        #   b) Convert to PIL Image: transforms.ToPILImage()
        # This converts the tensor back to a displayable PIL Image object
        pil_image = self.inverse_transform(tensor)
        
        # Step 6: Save to file
        # .save() writes the PIL Image to disk
        # quality=95 sets JPEG quality (95% - high quality, good balance of size/quality)
        # The format is determined by the file extension (.jpg, .png, etc.)
        pil_image.save(output_path, quality=95)


def main():
    """
    Main entry point for the script.
    """
    # Create an instance of ImageProtector
    # This initializes the VGG19 model, sets up transforms, etc.
    print("Initializing ImageProtector...")
    protector = ImageProtector()
    
    # Define input and output file paths
    # These are the files specified in the requirements
    input_image = "art.jpg"
    output_image = "protected_art.jpg"
    
    # Check if input image exists
    # If not, print an error message
    import os
    if not os.path.exists(input_image):
        print(f"\nERROR: Input image '{input_image}' not found!")
        print(f"Please place an image named '{input_image}' in the current directory.")
        print(f"Current directory: {os.getcwd()}\n")
        return
    
    # Run the protection algorithm
    # This is where all the magic happens:
    #   - Loads the image
    #   - Extracts features
    #   - Optimizes the perturbation
    #   - Saves the protected image
    protector.protect_image(
        input_path=input_image,
        output_path=output_image,
        num_iterations=100,      # Number of optimization steps
        learning_rate=0.01,      # Step size for gradient descent
        epsilon=0.03             # Maximum perturbation per pixel (L∞ bound)
    )
    
    print(f"\nSuccess! Protected image saved as '{output_image}'")
    print("The image should look identical to the original, but VGG19 will see different features.")


if __name__ == "__main__":
    main()
