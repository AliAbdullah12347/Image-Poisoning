# Image Poisoning Project - Phase 1

## Overview
This project implements an adversarial attack on images to protect them from feature extraction by deep learning models.

## Phase 1: Core Logic Setup
- **Status**: File structure and imports setup (no logic implementation yet)
- **Goal**: Create a Python script that takes an image and "poisons" it locally using adversarial attacks

## Environment Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `torch`: PyTorch deep learning framework
- `torchvision`: Pre-trained models and image utilities
- `numpy`: Numerical computations
- `Pillow`: Image processing

## Project Structure
```
.
├── protect.py          # Main protection script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Usage (Once Implemented)
```bash
python protect.py
```

The script will:
1. Load `art.jpg` as input
2. Apply adversarial attack using VGG19 feature extractor
3. Save the protected image as `protected_art.jpg`

## Algorithm Concept
1. Load pre-trained VGG19 model (frozen)
2. Extract feature maps from a middle layer
3. Create noise tensor (δ) and add to image: x' = x + δ
4. Optimize to maximize feature distance while minimizing pixel difference
5. Update δ using gradient descent until model is confused

## Notes
- The model is not trained; it's used for feature extraction only
- The attack is a variation of FGSM or PGD
- Human eye should still see the original art
- Feature extractor should be confused about the image content
