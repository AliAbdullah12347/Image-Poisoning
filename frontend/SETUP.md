# Frontend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Python Backend

**In a separate terminal**, start the Python API:

```bash
cd ..
python api.py
```

Wait for models to load (1-2 minutes). You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Start Next.js Frontend

**In the frontend directory**:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Configuration

### Option 1: Environment File (Recommended)

Create `frontend/.env.local`:

```env
BACKEND_URL=http://localhost:8000
```

### Option 2: Command Line

```bash
BACKEND_URL=http://localhost:8000 npm run dev
```

### Option 3: Default

If not set, defaults to `http://localhost:8000`

## Troubleshooting

### "Cannot connect to backend"

1. Make sure Python backend is running (`python api.py`)
2. Check backend URL in `.env.local`
3. Verify backend is accessible: `curl http://localhost:8000/health`

### "Module not found"

Run `npm install` in the frontend directory.

### "Port 3000 already in use"

Use a different port:
```bash
npm run dev -- -p 3001
```

### CORS Errors

The Next.js API route should handle CORS. If issues persist:
1. Check backend CORS settings in `api.py`
2. Verify API route is working: `curl http://localhost:3000/api/upload`

## Development

### Hot Reload

Both Next.js and the Python backend support hot reload:
- Next.js: Automatic (built-in)
- Python: Set `reload=True` in `api.py` (already set)

### Debugging

- **Frontend**: Use browser DevTools
- **Backend**: Check terminal running `api.py`
- **API Route**: Check Next.js terminal for errors

## Production Build

```bash
cd frontend
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── api/upload/route.ts    # API proxy to Python backend
│   ├── page.tsx               # Main page component
│   ├── layout.tsx              # Root layout
│   └── globals.css            # Global styles
├── components/
│   ├── ImageDropzone.tsx      # File upload
│   ├── LoadingAnimation.tsx   # Loading states
│   └── ComparisonSlider.tsx   # Before/after slider
└── package.json
```
