'use client'

import { useState } from 'react'
import ImageDropzone from '@/components/ImageDropzone'
import LoadingAnimation from '@/components/LoadingAnimation'
import ComparisonSlider from '@/components/ComparisonSlider'
import { Shield, Download, RefreshCw, AlertCircle, Zap, Lock, Eye, Layers } from 'lucide-react'
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
      })

      const blob = new Blob([response.data], { type: 'image/jpeg' })
      const url = URL.createObjectURL(blob)
      setProtectedImageUrl(url)

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
    <main className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-grid-pattern bg-[length:30px_30px] opacity-[0.03] pointer-events-none" />

      {/* Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/20 blur-[120px] rounded-full pointer-events-none opacity-20" />

      <div className="container mx-auto px-6 py-20 relative z-10 max-w-7xl">

        {/* Hero Section */}
        <div className="text-center mb-20 space-y-6">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full border border-primary/20 bg-primary/5 backdrop-blur-sm">
            <Shield className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary tracking-wide uppercase">Advanced Adversarial Protection</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold tracking-tight text-white">
            Protect Your Art <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent relative">
              From AI Scraping
              <span className="absolute -inset-1 blur-xl bg-primary/20 -z-10" />
            </span>
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            Our ensemble adversarial attack engine invisibly poisons your images, confusing AI feature extractors while remaining visually identical to the human eye.
          </p>
        </div>

        {/* Application Interface */}
        <div className="glass rounded-3xl p-1 shadow-2xl overflow-hidden border border-white/10 ring-1 ring-white/5">
          <div className="bg-black/40 backdrop-blur-xl rounded-[20px] p-8 md:p-12 min-h-[600px]">

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20">
              {/* Left Panel: Upload & Config */}
              <div className="space-y-8 flex flex-col justify-center">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <Layers className="w-6 h-6 text-secondary mr-3" />
                    Input Source
                  </h2>
                  <p className="text-gray-400">Upload high-resolution artwork for protection.</p>
                </div>

                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-secondary to-primary rounded-xl blur opacity-10 group-hover:opacity-30 transition duration-500" />
                  <div className="relative bg-surface rounded-xl border border-white/5 p-1">
                    <ImageDropzone
                      onFileSelect={handleFileSelect}
                      selectedFile={selectedFile}
                      disabled={state === 'processing'}
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-4 pt-4">
                  {selectedFile && state === 'idle' && (
                    <button
                      onClick={handleProtect}
                      className="w-full group relative overflow-hidden rounded-xl bg-primary px-8 py-4 transition-all hover:scale-[1.02] hover:shadow-[0_0_40px_-10px_rgba(255,255,0,0.5)]"
                    >
                      <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                      <div className="relative flex items-center justify-center space-x-3 text-black font-bold text-lg">
                        <Zap className="w-5 h-5 fill-black" />
                        <span>Initiate Protection Sequence</span>
                      </div>
                    </button>
                  )}

                  {state === 'processing' && (
                    <div className="w-full bg-surface/50 border border-white/5 rounded-xl p-6 flex flex-col items-center justify-center space-y-4">
                      <LoadingAnimation />
                      <p className="text-primary font-mono text-sm animate-pulse">OPTIMIZING NOISE VECTORS...</p>
                    </div>
                  )}

                  {state === 'error' && (
                    <div className="w-full bg-red-500/10 border border-red-500/20 rounded-xl p-6 flex items-start space-x-4">
                      <AlertCircle className="w-6 h-6 text-red-500 shrink-0" />
                      <div className="flex-1">
                        <h4 className="text-red-500 font-bold mb-1">Protection Failed</h4>
                        <p className="text-red-400/80 text-sm mb-4">{error}</p>
                        <button
                          onClick={handleReset}
                          className="text-white bg-red-500/20 hover:bg-red-500/30 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        >
                          Try Again
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Panel: Visualization & Results */}
              <div className="bg-surface/30 rounded-2xl border border-white/5 p-1 flex flex-col relative overflow-hidden">
                {/* Decorative header */}
                <div className="absolute top-0 left-0 right-0 h-10 bg-white/5 border-b border-white/5 flex items-center px-4 space-x-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                  <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                  <div className="flex-1" />
                  <div className="text-[10px] font-mono text-gray-500">VIEWPORT: PREVIEW</div>
                </div>

                <div className="flex-1 mt-10 p-4 flex items-center justify-center min-h-[400px]">
                  {state === 'idle' && !selectedFile && (
                    <div className="text-center space-y-4 opacity-50">
                      <div className="w-20 h-20 mx-auto rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                        <Eye className="w-8 h-8 text-gray-400" />
                      </div>
                      <p className="text-gray-500 font-mono text-sm max-w-[200px] mx-auto">
                        WAITING FOR SIGNAL SOURCE...
                      </p>
                    </div>
                  )}

                  {state === 'idle' && originalImageUrl && !protectedImageUrl && (
                    <div className="relative w-full h-full rounded-lg overflow-hidden border border-white/10 group">
                      <img src={originalImageUrl} alt="Original" className="w-full h-full object-contain" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-6">
                        <div className="text-white">
                          <p className="font-bold">Original Asset</p>
                          <p className="text-xs text-gray-400 font-mono uppercase">Unprotected</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {state === 'success' && originalImageUrl && protectedImageUrl && (
                    <div className="w-full h-full">
                      <ComparisonSlider
                        originalImage={originalImageUrl}
                        protectedImage={protectedImageUrl}
                      />

                      <div className="mt-6 flex items-center justify-between">
                        {metrics && (
                          <div className="flex items-center space-x-4">
                            <div className="text-xs font-mono text-gray-400 space-y-1">
                              <div className="flex items-center space-x-2">
                                <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                                <span>STATUS: SECURE</span>
                              </div>
                              <div className="text-white/50">TIME: {metrics.processingTime?.toFixed(2)}s</div>
                              <div className="text-white/50">DELTA: {metrics.featureDistance?.toFixed(2)}</div>
                            </div>
                          </div>
                        )}

                        <div className="flex space-x-3">
                          <button
                            onClick={handleReset}
                            className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-colors border border-white/5"
                            title="Reset"
                          >
                            <RefreshCw className="w-5 h-5" />
                          </button>
                          <button
                            onClick={handleDownload}
                            className="px-6 py-3 rounded-xl bg-accent text-black font-bold hover:bg-green-400 transition-all flex items-center space-x-2 shadow-[0_0_20px_-5px_rgba(34,197,94,0.4)]"
                          >
                            <Download className="w-5 h-5" />
                            <span>Download Asset</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* How it works Section */}
        <div className="mt-32 mb-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">Core Architecture</h2>
            <p className="text-gray-400">Understanding the protection mechanism</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Layers,
                title: "Feature Extraction",
                desc: "We analyze your image using VGG19, ResNet50, and Inception models to map how AI perceives the content."
              },
              {
                icon: Zap,
                title: "Adversarial Noise",
                desc: "An undetectable noise vector is generated and injected into the image, targeting specific neural activations."
              },
              {
                icon: Lock,
                title: "Visual Lock",
                desc: "Perceptual loss functions ensure the image remains visually 99.9% identical to the original artwork."
              }
            ].map((item, i) => (
              <div key={i} className="glass p-8 rounded-2xl border border-white/5 hover:border-primary/20 transition-all group">
                <div className="w-14 h-14 rounded-full bg-surface border border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <item.icon className="w-7 h-7 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                <p className="text-gray-400 leading-relaxed text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  )
}
