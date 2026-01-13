'use client'

import { ReactCompareSlider, ReactCompareSliderImage } from 'react-compare-slider'

interface ComparisonSliderProps {
  originalImage: string
  protectedImage: string
}

export default function ComparisonSlider({
  originalImage,
  protectedImage,
}: ComparisonSliderProps) {
  return (
    <div className="w-full rounded-lg overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700">
      <ReactCompareSlider
        itemOne={
          <ReactCompareSliderImage
            src={originalImage}
            alt="Original Image"
            style={{ objectFit: 'contain' }}
          />
        }
        itemTwo={
          <ReactCompareSliderImage
            src={protectedImage}
            alt="Protected Image"
            style={{ objectFit: 'contain' }}
          />
        }
        style={{
          width: '100%',
          height: '100%',
        }}
        position={50}
        onlyHandleDraggable={true}
      />
      <div className="bg-white dark:bg-gray-900 p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
            <span className="text-gray-700 dark:text-gray-300 font-medium">
              Original
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full" />
            <span className="text-gray-700 dark:text-gray-300 font-medium">
              Protected
            </span>
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
          Drag the slider to compare • Images look identical to humans
        </p>
      </div>
    </div>
  )
}
