'use client'

import { useEffect, useState } from 'react'
import { Loader2, Sparkles, Zap, Shield, Cpu } from 'lucide-react'

const loadingSteps = [
  { icon: Cpu, text: 'INITIALIZING VGG19/RESNET...', durationRatio: 0.2 },
  { icon: Zap, text: 'CALCULATING ADVERSARIAL GRADIENTS...', durationRatio: 0.3 },
  { icon: Shield, text: 'INJECTING NOISE VECTOR...', durationRatio: 0.2 },
  { icon: Sparkles, text: 'OPTIMIZING PERCEPTUAL LOSS...', durationRatio: 0.2 },
  { icon: Loader2, text: 'CRYPTO-LOCKING FEATURES...', durationRatio: 0.1 },
]

export default function LoadingAnimation({ mode }: { mode: 'speed' | 'balanced' | 'fortress' }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  // Estimated times based on backend performance
  const totalDuration = {
    'speed': 15000,
    'balanced': 45000,
    'fortress': 90000
  }[mode] || 45000

  useEffect(() => {
    let progressValue = 0
    const intervalTime = 100 // Update every 100ms
    const totalSteps = totalDuration / intervalTime

    // Smooth progress interval
    const interval = setInterval(() => {
      progressValue += 1

      const currentProgressRatio = progressValue / totalSteps

      // Calculate current step based on ratio
      let accumulatedBox = 0
      for (let i = 0; i < loadingSteps.length; i++) {
        accumulatedBox += loadingSteps[i].durationRatio
        if (currentProgressRatio <= accumulatedBox) {
          setCurrentStep(i)
          break
        }
      }

      const newProgress = Math.min(currentProgressRatio * 100, 99)
      setProgress(newProgress)

      if (currentProgressRatio >= 1) {
        setProgress(100)
        clearInterval(interval)
      }
    }, intervalTime)

    return () => clearInterval(interval)
  }, [mode, totalDuration])

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
