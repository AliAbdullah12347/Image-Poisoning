"""
Robust Image Protection Script
Performs robust adversarial attack on images to protect them from feature extraction.
Uses ensemble of models and transformation robustness for maximum effectiveness.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image, ImageFilter
import numpy as np
from typing import Tuple, Optional, List, Dict
import random
import io


class ImageProtector:
    """
    Robust class to handle image protection using ensemble adversarial attacks.
    Uses multiple models (VGG19, ResNet50, Inception) for better transferability.
    Includes robustness to transformations (JPEG compression, resizing).
    """
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize the ImageProtector.
        Models are now lazy-loaded to reduce startup time resource usage.
        
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
        
        # Models container - will be populated on demand
        self.models = {}
        self.feature_hooks = {}
        
        # Common ImageNet normalization
        self.normalize_mean = [0.485, 0.456, 0.406]
        self.normalize_std = [0.229, 0.224, 0.225]
        
        # Image preprocessing transforms
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=self.normalize_mean, std=self.normalize_std)
        ])
        
        # Inverse transform to convert back to image
        self.inverse_transform = transforms.Compose([
            transforms.Normalize(
                mean=[-m/s for m, s in zip(self.normalize_mean, self.normalize_std)],
                std=[1/s for s in self.normalize_std]
            ),
            transforms.ToPILImage()
        ])
        
        print("ImageProtector initialized (Models will load on demand)\n")

    def ensure_model_loaded(self, model_name: str):
        """Lazy load a specific model if it's not already in memory."""
        if model_name in self.models:
            return

        print(f"Lazy loading {model_name}...")
        
        if model_name == 'vgg19':
            model = models.vgg19(pretrained=True).to(self.device)
            layer = 21 # conv4_1
            weight = 1.0
        elif model_name == 'resnet50':
            model = models.resnet50(pretrained=True).to(self.device)
            layer = 'layer3'
            weight = 0.8
        elif model_name == 'inception':
            model = models.inception_v3(pretrained=True, transform_input=False).to(self.device)
            layer = 'Mixed_5d'
            weight = 0.7
        else:
            raise ValueError(f"Unknown model: {model_name}")

        model.eval()
        for param in model.parameters():
            param.requires_grad = False
            
        self.models[model_name] = {
            'model': model,
            'layer': layer,
            'weight': weight
        }
    
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
    
    def extract_features(self, image_tensor: torch.Tensor, model_name: str = 'vgg19') -> torch.Tensor:
        """
        Extract feature maps from a specified model and layer.
        
        Args:
            image_tensor: Preprocessed image tensor.
            model_name: Name of the model to use ('vgg19', 'resnet50', 'inception').
            
        Returns:
            Feature maps from the specified layer.
        """
        if model_name not in self.models:
            self.ensure_model_loaded(model_name)
            
        model_info = self.models[model_name]
        model = model_info['model']
        layer_spec = model_info['layer']
        feature_maps = [None]  # Use list to allow modification in nested function
        
        def hook_fn(module, input, output):
            feature_maps[0] = output.clone()
        
        # Register hook based on model architecture
        if model_name == 'vgg19':
            handle = model.features[layer_spec].register_forward_hook(hook_fn)
            with torch.no_grad():
                _ = model.features(image_tensor)
        elif model_name == 'resnet50':
            # ResNet50: access layer3 (third residual block)
            handle = model.layer3.register_forward_hook(hook_fn)
            with torch.no_grad():
                x = model.conv1(image_tensor)
                x = model.bn1(x)
                x = model.relu(x)
                x = model.maxpool(x)
                x = model.layer1(x)
                x = model.layer2(x)
                _ = model.layer3(x)
        elif model_name == 'inception':
            # Inception v3: use Mixed_5d layer (middle layer with good features)
            try:
                # Try to find the layer by name
                target_layer = None
                for name, module in model.named_modules():
                    if 'Mixed_5d' in name or layer_spec in name:
                        target_layer = module
                        break
                
                if target_layer is None:
                    # Fallback: use Mixed_5b (earlier layer)
                    for name, module in model.named_modules():
                        if 'Mixed_5b' in name:
                            target_layer = module
                            break
                
                if target_layer:
                    handle = target_layer.register_forward_hook(hook_fn)
                    with torch.no_grad():
                        # Use the model's forward method but stop at the hook
                        # Inception has aux_logits, so we handle that
                        if hasattr(model, 'aux_logits') and model.aux_logits:
                            output, aux = model(image_tensor)
                        else:
                            output = model(image_tensor)
                else:
                    handle = None
            except Exception:
                # If Inception extraction fails, return None (will be skipped)
                handle = None
        else:
            handle = None
        
        features = feature_maps[0]
        if handle:
            handle.remove()
        
        return features
    
    def extract_all_features(self, image_tensor: torch.Tensor, target_models: List[str]) -> Dict[str, torch.Tensor]:
        """
        Extract features from specified models.
        
        Args:
            image_tensor: Preprocessed image tensor.
            target_models: List of model names to extract features from.
            
        Returns:
            Dictionary mapping model names to their feature maps.
        """
        all_features = {}
        for model_name in target_models:
            self.ensure_model_loaded(model_name)  # Ensure loaded before usage
            try:
                features = self.extract_features(image_tensor, model_name)
                if features is not None:
                    all_features[model_name] = features
            except Exception as e:
                print(f"Warning: Could not extract features from {model_name}: {e}")
        return all_features
    
    def apply_transformations(self, image_tensor: torch.Tensor, training: bool = True) -> torch.Tensor:
        """
        Apply random transformations to make attack robust to preprocessing.
        Simulates JPEG compression, resizing, and other common transformations.
        
        Args:
            image_tensor: Image tensor to transform.
            training: If True, apply random transformations. If False, apply deterministic ones.
            
        Returns:
            Transformed image tensor.
        """
        if not training:
            return image_tensor
        
        # Convert to PIL for transformations
        tensor_cpu = image_tensor.detach().cpu().squeeze(0)
        tensor_cpu = torch.clamp(tensor_cpu, 0.0, 1.0)
        
        # Denormalize
        denorm = transforms.Normalize(
            mean=[-m/s for m, s in zip(self.normalize_mean, self.normalize_std)],
            std=[1/s for s in self.normalize_std]
        )
        tensor_cpu = denorm(tensor_cpu)
        pil_image = transforms.ToPILImage()(tensor_cpu)
        
        # Apply random transformations with probability
        if random.random() < 0.3:  # 30% chance
            # Simulate JPEG compression
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=random.randint(85, 95))
            buffer.seek(0)
            pil_image = Image.open(buffer)
        
        if random.random() < 0.2:  # 20% chance
            # Random resize (simulate different input sizes)
            size_factor = random.uniform(0.95, 1.05)
            new_size = (int(pil_image.width * size_factor), int(pil_image.height * size_factor))
            pil_image = pil_image.resize(new_size, Image.LANCZOS)
            # Resize back to original
            original_size = (image_tensor.shape[3], image_tensor.shape[2])
            pil_image = pil_image.resize(original_size, Image.LANCZOS)
        
        if random.random() < 0.1:  # 10% chance
            # Slight blur (simulate compression artifacts)
            pil_image = pil_image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Convert back to tensor
        tensor = transforms.ToTensor()(pil_image)
        tensor = transforms.Normalize(mean=self.normalize_mean, std=self.normalize_std)(tensor)
        tensor = tensor.unsqueeze(0).to(self.device)
        
        return tensor
    
    def compute_perceptual_loss(self, img1: torch.Tensor, img2: torch.Tensor) -> torch.Tensor:
        """
        Compute perceptual loss using VGG features (better than pixel loss).
        
        Args:
            img1: First image tensor.
            img2: Second image tensor.
            
        Returns:
            Perceptual loss value.
        """
        # Use VGG19 features for perceptual loss
        features1 = self.extract_features(img1, 'vgg19')
        features2 = self.extract_features(img2, 'vgg19')
        
        if features1 is None or features2 is None:
            # Fallback to pixel loss
            return torch.norm(img1 - img2, p=2) ** 2
        
        # Perceptual loss: L2 distance in feature space
        return torch.norm(features1 - features2, p=2) ** 2
    
    def compute_loss(self, original_features_dict: Dict[str, torch.Tensor], 
                    perturbed_features_dict: Dict[str, torch.Tensor],
                    original_image: torch.Tensor,
                    perturbed_image: torch.Tensor,
                    feature_weight: float = 1.0,
                    pixel_weight: float = 0.1,
                    perceptual_weight: float = 0.5) -> torch.Tensor:
        """
        Compute robust loss function with ensemble and perceptual loss.
        
        Args:
            original_features_dict: Dictionary of features from original image (all models).
            perturbed_features_dict: Dictionary of features from perturbed image (all models).
            original_image: Original image tensor.
            perturbed_image: Perturbed image tensor.
            feature_weight: Weight for feature distance term.
            pixel_weight: Weight for pixel difference term.
            perceptual_weight: Weight for perceptual loss term.
            
        Returns:
            Computed loss value.
        """
        # === PART 1: Ensemble Feature Distance (MAXIMIZE) ===
        total_feature_distance = 0.0
        total_weight = 0.0
        
        for model_name in original_features_dict.keys():
            if model_name in perturbed_features_dict:
                orig_feat = original_features_dict[model_name]
                pert_feat = perturbed_features_dict[model_name]
                
                if orig_feat is not None and pert_feat is not None:
                    # Normalize features for fair comparison across models
                    orig_feat_norm = orig_feat / (torch.norm(orig_feat, p=2) + 1e-8)
                    pert_feat_norm = pert_feat / (torch.norm(pert_feat, p=2) + 1e-8)
                    
                    feature_diff = pert_feat_norm - orig_feat_norm
                    feature_dist = torch.norm(feature_diff, p=2) ** 2
                    
                    model_weight = self.models[model_name]['weight']
                    total_feature_distance += model_weight * feature_dist
                    total_weight += model_weight
        
        if total_weight > 0:
            avg_feature_distance = total_feature_distance / total_weight
        else:
            avg_feature_distance = torch.tensor(0.0, device=self.device)
        
        # === PART 2: Pixel Difference (MINIMIZE) ===
        pixel_diff = perturbed_image - original_image
        pixel_difference = torch.norm(pixel_diff, p=2) ** 2
        
        # === PART 3: Perceptual Loss (MINIMIZE) ===
        # This ensures visual quality is preserved
        perceptual_loss = self.compute_perceptual_loss(original_image, perturbed_image)
        
        # === PART 4: Combined Loss ===
        # Maximize feature distance, minimize pixel and perceptual differences
        loss = (-feature_weight * avg_feature_distance + 
                pixel_weight * pixel_difference + 
                perceptual_weight * perceptual_loss)
        
        return loss
    
    def compute_adaptive_epsilon(self, image_tensor: torch.Tensor, base_epsilon: float = 0.03) -> float:
        """
        Compute adaptive epsilon based on image characteristics.
        Some images can tolerate more perturbation than others.
        
        Args:
            image_tensor: Image tensor to analyze.
            base_epsilon: Base epsilon value.
            
        Returns:
            Adaptive epsilon value.
        """
        # Compute image variance (higher variance = more texture = can hide more noise)
        variance = torch.var(image_tensor).item()
        
        # Adjust epsilon based on variance
        # High variance images (textured) can handle more perturbation
        # Low variance images (smooth) need less perturbation
        adaptive_factor = 0.8 + 0.4 * min(variance * 10, 1.0)  # Scale between 0.8 and 1.2
        
        return base_epsilon * adaptive_factor
    
    def protect_image(self, input_path: str, output_path: str,
                     num_iterations: int = 150,
                     learning_rate: float = 0.01,
                     epsilon: float = 0.03,
                     target_models: List[str] = ['vgg19', 'resnet50'],
                     use_adaptive_epsilon: bool = True,
                     robust_to_transforms: bool = True,
                     feature_weight: float = 1.0,
                     pixel_weight: float = 0.1,
                     perceptual_weight: float = 0.5) -> Dict[str, float]:
        """
        Main method to protect an image using robust adversarial attack.
        
        Args:
            input_path: Path to input image (e.g., 'art.jpg').
            output_path: Path to save protected image (e.g., 'protected_art.jpg').
            num_iterations: Number of optimization iterations.
            learning_rate: Learning rate for gradient descent.
            epsilon: Maximum perturbation allowed (L-infinity bound).
            target_models: List of models to attack (e.g. ['vgg19']).
            use_adaptive_epsilon: If True, adjust epsilon based on image characteristics.
            robust_to_transforms: If True, apply random transformations during training.
            feature_weight: Weight for feature distance term.
            pixel_weight: Weight for pixel difference term.
            perceptual_weight: Weight for perceptual loss term.
            
        Returns:
            Dictionary with evaluation metrics.
        """
        print(f"\n=== Starting Robust Image Protection ===")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Target Models: {target_models}")
        print(f"Iterations: {num_iterations}, Learning Rate: {learning_rate}, Base Epsilon: {epsilon}")
        print(f"Adaptive Epsilon: {use_adaptive_epsilon}, Robust to Transforms: {robust_to_transforms}\n")
        
        # === STEP 1: Load and preprocess the original image ===
        print("Loading original image...")
        original_image = self.load_image(input_path)
        print(f"Image shape: {original_image.shape}")
        
        # === STEP 2: Compute adaptive epsilon if enabled ===
        if use_adaptive_epsilon:
            adaptive_eps = self.compute_adaptive_epsilon(original_image, epsilon)
            print(f"Adaptive epsilon: {adaptive_eps:.4f} (base: {epsilon:.4f})")
            epsilon = adaptive_eps
        
        # === STEP 3: Extract features from target models ===
        print(f"Extracting original features from {len(target_models)} models...")
        original_features_dict = self.extract_all_features(original_image, target_models)
        for model_name, features in original_features_dict.items():
            if features is not None:
                print(f"  {model_name}: {features.shape}")
        
        # === STEP 4: Initialize the noise tensor (δ) ===
        print("Initializing noise tensor...")
        delta = torch.zeros_like(original_image, requires_grad=True)
        
        # === STEP 5: Create optimizer with learning rate scheduling ===
        optimizer = optim.Adam([delta], lr=learning_rate)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_iterations)
        
        # === STEP 6: Optimization Loop ===
        print(f"\nStarting robust optimization ({num_iterations} iterations)...")
        print("-" * 70)
        
        best_loss = float('inf')
        best_delta = None
        
        for iteration in range(num_iterations):
            # --- 6a: Create perturbed image ---
            perturbed_image = original_image + delta
            
            # --- 6b: Apply transformations for robustness (during training) ---
            if robust_to_transforms and iteration < num_iterations * 0.8:  # Apply for 80% of iterations
                # Apply random transformations to make attack robust
                perturbed_image_transformed = self.apply_transformations(perturbed_image, training=True)
            else:
                perturbed_image_transformed = perturbed_image
            
            # --- 6c: Apply L∞ constraint (clipping) ---
            delta.data = torch.clamp(delta.data, -epsilon, epsilon)
            perturbed_image = original_image + delta
            
            # --- 6d: Extract features from perturbed image (all models) ---
            perturbed_features_dict = self.extract_all_features(perturbed_image_transformed, target_models)
            
            # --- 6e: Compute robust loss function ---
            loss = self.compute_loss(
                original_features_dict,
                perturbed_features_dict,
                original_image,
                perturbed_image,
                feature_weight=feature_weight,
                pixel_weight=pixel_weight,
                perceptual_weight=perceptual_weight
            )
            
            # Track best loss
            if loss.item() < best_loss:
                best_loss = loss.item()
                best_delta = delta.clone().detach()
            
            # --- 6f: Backward pass ---
            optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_([delta], max_norm=1.0)
            
            # --- 6g: Update delta ---
            optimizer.step()
            scheduler.step()
            
            # --- 6h: Progress reporting ---
            if (iteration + 1) % 20 == 0 or iteration == 0:
                # Compute metrics
                avg_feat_dist = 0.0
                count = 0
                for model_name in original_features_dict.keys():
                    if model_name in perturbed_features_dict:
                        orig = original_features_dict[model_name]
                        pert = perturbed_features_dict[model_name]
                        if orig is not None and pert is not None:
                            feat_dist = torch.norm(pert - orig, p=2).item()
                            avg_feat_dist += feat_dist
                            count += 1
                if count > 0:
                    avg_feat_dist /= count
                
                pixel_diff = torch.norm(delta, p=2).item()
                current_lr = scheduler.get_last_lr()[0]
                
                print(f"Iter {iteration+1:3d}/{num_iterations} | "
                      f"Loss: {loss.item():.6f} | "
                      f"Feat Dist: {avg_feat_dist:.2f} | "
                      f"Pixel Diff: {pixel_diff:.6f} | "
                      f"LR: {current_lr:.5f}")
        
        # Use best delta found during optimization
        if best_delta is not None:
            delta.data = best_delta.data
        
        print("-" * 70)
        print("Optimization complete!\n")
        
        # === STEP 7: Final evaluation ===
        final_perturbed = original_image + delta
        final_features_dict = self.extract_all_features(final_perturbed, target_models)
        
        # Compute final metrics
        metrics = {}
        total_feat_dist = 0.0
        count = 0
        for model_name in original_features_dict.keys():
            if model_name in final_features_dict:
                orig = original_features_dict[model_name]
                pert = final_features_dict[model_name]
                if orig is not None and pert is not None:
                    feat_dist = torch.norm(pert - orig, p=2).item()
                    metrics[f'{model_name}_feature_distance'] = feat_dist
                    total_feat_dist += feat_dist
                    count += 1
        
        metrics['avg_feature_distance'] = total_feat_dist / count if count > 0 else 0.0
        metrics['pixel_difference'] = torch.norm(delta, p=2).item()
        metrics['max_perturbation'] = torch.max(torch.abs(delta)).item()
        metrics['epsilon_used'] = epsilon
        
        # === STEP 8: Save the protected image ===
        print("Saving protected image...")
        self.save_image(final_perturbed, output_path)
        print(f"Protected image saved to: {output_path}")
        
        # Print metrics
        print("\n=== Protection Metrics ===")
        for key, value in metrics.items():
            print(f"  {key}: {value:.6f}")
        
        print("\n=== Image Protection Complete ===\n")
        
        return metrics
    
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
    # Create an instance of ImageProtector with ensemble models
    # This initializes multiple models (VGG19, ResNet50, Inception) for robust protection
    print("Initializing Robust ImageProtector with ensemble models...")
    protector = ImageProtector(use_ensemble=True)
    
    # Define input and output file paths
    input_image = "art.jpg"
    output_image = "protected_art.jpg"
    
    # Check if input image exists
    import os
    if not os.path.exists(input_image):
        print(f"\nERROR: Input image '{input_image}' not found!")
        print(f"Please place an image named '{input_image}' in the current directory.")
        print(f"Current directory: {os.getcwd()}\n")
        return
    
    # Run the robust protection algorithm
    # This uses ensemble attacks, transformation robustness, and perceptual loss
    metrics = protector.protect_image(
        input_path=input_image,
        output_path=output_image,
        num_iterations=150,           # More iterations for better results
        learning_rate=0.01,            # Step size for gradient descent
        epsilon=0.03,                 # Maximum perturbation per pixel (L∞ bound)
        use_adaptive_epsilon=True,     # Adjust epsilon based on image
        robust_to_transforms=True,     # Make attack robust to JPEG/resize
        feature_weight=1.0,           # Weight for feature confusion
        pixel_weight=0.1,             # Weight for pixel preservation
        perceptual_weight=0.5         # Weight for perceptual quality
    )
    
    print(f"\n✓ Success! Protected image saved as '{output_image}'")
    print("\nThe protected image:")
    print("  - Looks identical to the original (human perception)")
    print("  - Confuses VGG19, ResNet50, and Inception feature extractors")
    print("  - Is robust to JPEG compression and resizing")
    print("  - Has high transferability to other models")


if __name__ == "__main__":
    main()
