import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get form data from request
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      )
    }

    // Get optional parameters
    const numIterations = formData.get('num_iterations') || '150'
    const learningRate = formData.get('learning_rate') || '0.01'
    const epsilon = formData.get('epsilon') || '0.03'
    const useAdaptiveEpsilon = formData.get('use_adaptive_epsilon') || 'true'
    const robustToTransforms = formData.get('robust_to_transforms') || 'true'
    const returnMetrics = formData.get('return_metrics') || 'false'

    // Create new form data for backend
    const backendFormData = new FormData()
    backendFormData.append('file', file)

    // Build query parameters
    const params = new URLSearchParams({
      num_iterations: numIterations.toString(),
      learning_rate: learningRate.toString(),
      epsilon: epsilon.toString(),
      use_adaptive_epsilon: useAdaptiveEpsilon.toString(),
      robust_to_transforms: robustToTransforms.toString(),
    })

    if (returnMetrics === 'true') {
      params.append('return_metrics', 'true')
    }

    // Forward request to Python backend
    const backendUrl = `${BACKEND_URL}/cloak?${params.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      body: backendFormData,
      headers: {
        // Don't set Content-Type, let fetch set it with boundary
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: errorText || 'Backend error', status: response.status },
        { status: response.status }
      )
    }

    // Check if response is JSON (metrics) or image
    const contentType = response.headers.get('content-type')
    
    if (contentType?.includes('application/json')) {
      const data = await response.json()
      return NextResponse.json(data)
    }

    // Return image as blob
    const imageBlob = await response.blob()
    const headers = new Headers()
    
    // Copy relevant headers from backend
    const requestId = response.headers.get('x-request-id')
    const processingTime = response.headers.get('x-processing-time')
    const featureDistance = response.headers.get('x-feature-distance')
    
    if (requestId) headers.set('x-request-id', requestId)
    if (processingTime) headers.set('x-processing-time', processingTime)
    if (featureDistance) headers.set('x-feature-distance', featureDistance)
    
    headers.set('content-type', 'image/jpeg')
    headers.set(
      'content-disposition',
      response.headers.get('content-disposition') || 'attachment; filename="protected.jpg"'
    )

    return new NextResponse(imageBlob, { headers })
  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
