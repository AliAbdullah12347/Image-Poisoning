'use client'

import { useEffect, useState } from 'react'
import { Loader2, Sparkles, Zap, Shield, Cpu } from 'lucide-react'

const loadingSteps = [
  { icon: Cpu, text: 'INITIALIZING VGG19/RESNET...', duration: 2000 },
  { icon: Zap, text: 'CALCULATING ADVERSARIAL GRADIENTS...', duration: 3000 },
  { icon: Shield, text: 'INJECTING NOISE VECTOR...', duration: 4000 },
  { icon: Sparkles, text: 'OPTIMIZING PERCEPTUAL LOSS...', duration: 5000 },
  { icon: Loader2, text: 'CRYPTO-LOCKING FEATURES...', duration: 2000 },
]

export default function LoadingAnimation() {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let progressValue = 0
    const totalDuration = loadingSteps.reduce((sum, step) => sum + step.duration, 0)

    // Smooth progress interval
    const interval = setInterval(() => {
      progressValue += 50

      // Calculate current step based on time
      let accumulated = 0
      for (let i = 0; i < loadingSteps.length; i++) {
        accumulated += loadingSteps[i].duration
        if (progressValue <= accumulated) {
          setCurrentStep(i)
          break
        }
      }

      const newProgress = Math.min((progressValue / totalDuration) * 100, 99)
      setProgress(newProgress)

      if (progressValue >= totalDuration) {
        setProgress(100)
        clearInterval(interval)
      }
    }, 50)

    return () => clearInterval(interval)
  }, [])

  const CurrentIcon = loadingSteps[currentStep]?.icon || Loader2

  return (
    <div className="flex flex-col items-center justify-center p-8 w-full">
      <div className="relative mb-8">
        {/* Outer Ring */}
        <div className="w-24 h-24 rounded-full border-2 border-white/5 animate-spin-slow" />

        {/* Inner Ring */}
        <div className="absolute inset-2 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />

        {/* Icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <CurrentIcon className="w-8 h-8 text-primary animate-pulse" />
        </div>
      </div>

      <div className="text-center space-y-2 w-full max-w-sm">
        <p className="text-lg font-bold text-white font-mono tracking-widest uppercase">
          {loadingSteps[currentStep]?.text}
        </p>

        {/* Progress Bar */}
        <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden mt-4">
          <div
            className="h-full bg-primary shadow-[0_0_10px_rgba(255,255,0,0.5)] transition-all duration-200 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex justify-between text-xs text-gray-500 font-mono pt-2">
          <span>PROCESS_PID: {Math.floor(Math.random() * 9000) + 1000}</span>
          <span>{Math.round(progress)}%</span>
        </div>
      </div>
    </div>
  )
}
