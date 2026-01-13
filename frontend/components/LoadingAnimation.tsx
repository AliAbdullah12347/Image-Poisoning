'use client'

import { useEffect, useState } from 'react'
import { Loader2, Sparkles, Zap, Shield } from 'lucide-react'

const loadingSteps = [
  { icon: Sparkles, text: 'Loading models...', duration: 2000 },
  { icon: Zap, text: 'Calculating gradients...', duration: 3000 },
  { icon: Shield, text: 'Injecting noise...', duration: 4000 },
  { icon: Sparkles, text: 'Optimizing features...', duration: 5000 },
  { icon: Zap, text: 'Finalizing protection...', duration: 2000 },
]

export default function LoadingAnimation() {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let stepIndex = 0
    let progressValue = 0
    const totalDuration = loadingSteps.reduce((sum, step) => sum + step.duration, 0)

    const interval = setInterval(() => {
      progressValue += 100
      const elapsed = progressValue
      
      // Calculate current step based on elapsed time
      let accumulated = 0
      let newStep = 0
      for (let i = 0; i < loadingSteps.length; i++) {
        accumulated += loadingSteps[i].duration
        if (elapsed <= accumulated) {
          newStep = i
          break
        }
        newStep = loadingSteps.length - 1
      }

      if (newStep !== stepIndex) {
        stepIndex = newStep
        setCurrentStep(stepIndex)
      }

      // Update progress (0-95%, leave 5% for final step)
      const progressPercent = Math.min(95, (elapsed / totalDuration) * 100)
      setProgress(progressPercent)

      if (elapsed >= totalDuration) {
        clearInterval(interval)
        setProgress(100)
      }
    }, 100)

    return () => clearInterval(interval)
  }, [])

  const CurrentIcon = loadingSteps[currentStep]?.icon || Loader2

  return (
    <div className="flex flex-col items-center justify-center space-y-8 p-12">
      <div className="relative">
        <div className="w-32 h-32 border-4 border-gray-200 dark:border-gray-700 rounded-full">
          <div className="w-full h-full border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <CurrentIcon className="w-8 h-8 text-blue-500 animate-pulse" />
        </div>
      </div>

      <div className="text-center space-y-2">
        <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          {loadingSteps[currentStep]?.text || 'Processing...'}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          This may take 30-120 seconds
        </p>
      </div>

      <div className="w-full max-w-md space-y-2">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="bg-blue-500 h-2.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-center text-gray-500 dark:text-gray-400">
          {Math.round(progress)}% complete
        </p>
      </div>

      <div className="flex space-x-2">
        {loadingSteps.map((step, index) => {
          const Icon = step.icon
          return (
            <div
              key={index}
              className={`
                p-2 rounded-lg transition-all duration-300
                ${
                  index === currentStep
                    ? 'bg-blue-500 text-white scale-110'
                    : index < currentStep
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
                }
              `}
            >
              <Icon className="w-4 h-4" />
            </div>
          )
        })}
      </div>
    </div>
  )
}
