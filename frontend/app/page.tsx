'use client'

import { useState } from 'react'
import ImageDropzone from '@/components/ImageDropzone'
import LoadingAnimation from '@/components/LoadingAnimation'
import ComparisonSlider from '@/components/ComparisonSlider'
import { Shield, Download, RefreshCw, AlertCircle } from 'lucide-react'
import axios from 'axios'

type ProcessingState = 'idle' | 'processing' | 'success' | 'error'

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [originalImageUrl, setOriginalImageUrl] = useState<string | null>(null)
  const [protectedImageUrl, setProtectedImageUrl] = useState<string | null>(null)
  const [state, setState] = useState<ProcessingState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<any>(null)

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file)
    setState('idle')
    setError(null)
    setProtectedImageUrl(null)
    setMetrics(null)
    
    if (file) {
      const url = URL.createObjectURL(file)
      setOriginalImageUrl(url)
    } else {
      if (originalImageUrl) {
        URL.revokeObjectURL(originalImageUrl)
      }
      setOriginalImageUrl(null)
    }
  }

  const handleProtect = async () => {
    if (!selectedFile) return

    setState('processing')
    setError(null)
    setProtectedImageUrl(null)
    setMetrics(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('num_iterations', '150')
      formData.append('learning_rate', '0.01')
      formData.append('epsilon', '0.03')
      formData.append('use_adaptive_epsilon', 'true')
      formData.append('robust_to_transforms', 'true')

      const response = await axios.post('/api/upload', formData, {
        responseType: 'blob',
        timeout: 300000, // 5 minutes
        onUploadProgress: (progressEvent) => {
          // Could show upload progress here
        },
      })

      // Create blob URL for protected image
      const blob = new Blob([response.data], { type: 'image/jpeg' })
      const url = URL.createObjectURL(blob)
      setProtectedImageUrl(url)

      // Get metrics from headers if available
      const requestId = response.headers['x-request-id']
      const processingTime = response.headers['x-processing-time']
      const featureDistance = response.headers['x-feature-distance']

      if (requestId || processingTime || featureDistance) {
        setMetrics({
          requestId,
          processingTime: processingTime ? parseFloat(processingTime) : null,
          featureDistance: featureDistance ? parseFloat(featureDistance) : null,
        })
      }

      setState('success')
    } catch (err: any) {
      console.error('Protection error:', err)
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to protect image. Please try again.'
      )
      setState('error')
    }
  }

  const handleReset = () => {
    if (originalImageUrl) URL.revokeObjectURL(originalImageUrl)
    if (protectedImageUrl) URL.revokeObjectURL(protectedImageUrl)
    setSelectedFile(null)
    setOriginalImageUrl(null)
    setProtectedImageUrl(null)
    setState('idle')
    setError(null)
    setMetrics(null)
  }

  const handleDownload = () => {
    if (!protectedImageUrl) return
    
    const link = document.createElement('a')
    link.href = protectedImageUrl
    link.download = `protected_${selectedFile?.name || 'image.jpg'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <Shield className="w-10 h-10 text-blue-600 dark:text-blue-400" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
              Image Protection
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Protect your images from AI-based feature extraction using advanced adversarial attacks.
            Your images will look identical to humans but confuse AI models.
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Upload */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Upload Image
              </h2>
              <ImageDropzone
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                disabled={state === 'processing'}
              />
              
              {selectedFile && state === 'idle' && (
                <button
                  onClick={handleProtect}
                  className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <Shield className="w-5 h-5" />
                  <span>Protect Image</span>
                </button>
              )}

              {state === 'processing' && (
                <div className="mt-6">
                  <LoadingAnimation />
                </div>
              )}

              {state === 'error' && (
                <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-800 dark:text-red-200">
                        Error
                      </p>
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                        {error}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleReset}
                    className="mt-4 w-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              )}
            </div>

            {/* Metrics */}
            {metrics && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Protection Metrics
                </h3>
                <div className="space-y-3">
                  {metrics.processingTime && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        Processing Time
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {metrics.processingTime.toFixed(2)}s
                      </span>
                    </div>
                  )}
                  {metrics.featureDistance && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        Feature Distance
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {metrics.featureDistance.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {metrics.requestId && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        Request ID
                      </span>
                      <span className="text-sm font-mono text-gray-900 dark:text-gray-100">
                        {metrics.requestId}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  Comparison
                </h2>
                {state === 'success' && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleDownload}
                      className="p-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                      title="Download protected image"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                    <button
                      onClick={handleReset}
                      className="p-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg transition-colors"
                      title="Start over"
                    >
                      <RefreshCw className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </div>

              {state === 'idle' && !originalImageUrl && (
                <div className="flex items-center justify-center h-64 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <p className="text-gray-500 dark:text-gray-400">
                    Upload an image to see the comparison
                  </p>
                </div>
              )}

              {state === 'idle' && originalImageUrl && !protectedImageUrl && (
                <div className="space-y-4">
                  <div className="relative aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                    <img
                      src={originalImageUrl}
                      alt="Original"
                      className="w-full h-full object-contain"
                    />
                  </div>
                  <p className="text-sm text-center text-gray-500 dark:text-gray-400">
                    Click "Protect Image" to see the comparison
                  </p>
                </div>
              )}

              {state === 'processing' && originalImageUrl && (
                <div className="relative aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                  <img
                    src={originalImageUrl}
                    alt="Original"
                    className="w-full h-full object-contain opacity-50"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-lg">
                      <LoadingAnimation />
                    </div>
                  </div>
                </div>
              )}

              {state === 'success' && originalImageUrl && protectedImageUrl && (
                <ComparisonSlider
                  originalImage={originalImageUrl}
                  protectedImage={protectedImageUrl}
                />
              )}

              {state === 'error' && originalImageUrl && (
                <div className="relative aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                  <img
                    src={originalImageUrl}
                    alt="Original"
                    className="w-full h-full object-contain opacity-50"
                  />
                </div>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
                How It Works
              </h3>
              <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Upload your image and click "Protect Image"</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Processing takes 30-120 seconds</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Protected image looks identical to humans</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>AI models see completely different features</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
