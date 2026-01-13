# Image Protection Frontend

Next.js 14 frontend for the Image Protection API.

## Features

- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 📤 **Drag & Drop**: Easy image upload with react-dropzone
- 🔄 **Comparison Slider**: Before/after comparison with react-compare-slider
- ⏳ **Loading States**: Beautiful loading animations with progress tracking
- 📊 **Metrics Display**: Shows processing time and protection metrics
- 🌙 **Dark Mode**: Automatic dark mode support

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Backend URL

Create a `.env.local` file:

```env
BACKEND_URL=http://localhost:8000
```

Or set it when running:

```bash
BACKEND_URL=http://localhost:8000 npm run dev
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Upload Image**: Drag and drop or click to select an image
2. **Protect**: Click "Protect Image" button
3. **Wait**: Processing takes 30-120 seconds
4. **Compare**: Use the slider to compare original vs protected
5. **Download**: Click download button to save protected image

## Project Structure

```
frontend/
├── app/
│   ├── api/
│   │   └── upload/
│   │       └── route.ts      # Next.js API route (proxies to Python backend)
│   ├── globals.css           # Global styles
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Main page
├── components/
│   ├── ImageDropzone.tsx     # File upload component
│   ├── LoadingAnimation.tsx  # Loading spinner with steps
│   └── ComparisonSlider.tsx  # Before/after slider
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## API Integration

The frontend uses a Next.js API route (`/api/upload`) that proxies requests to the Python backend. This:

- Prevents CORS issues
- Allows for request modification
- Provides a clean API interface

## Technologies

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS
- **react-dropzone**: File upload component
- **react-compare-slider**: Before/after comparison
- **lucide-react**: Icon library
- **axios**: HTTP client

## Build for Production

```bash
npm run build
npm start
```

## Environment Variables

- `BACKEND_URL`: URL of the Python backend (default: `http://localhost:8000`)
