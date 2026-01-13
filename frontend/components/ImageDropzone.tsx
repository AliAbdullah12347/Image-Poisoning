'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, Image as ImageIcon } from 'lucide-react'

interface ImageDropzoneProps {
  onFileSelect: (file: File) => void
  selectedFile: File | null
  disabled?: boolean
}

export default function ImageDropzone({
  onFileSelect,
  selectedFile,
  disabled = false,
}: ImageDropzoneProps) {
  const [preview, setPreview] = useState<string | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (file) {
        onFileSelect(file)
        // Create preview
        const reader = new FileReader()
        reader.onload = () => {
          setPreview(reader.result as string)
        }
        reader.readAsDataURL(file)
      }
    },
    [onFileSelect]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp'],
    },
    maxFiles: 1,
    disabled,
  })

  const handleRemove = () => {
    onFileSelect(null as any)
    setPreview(null)
  }

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-all duration-200
            ${
              isDragActive
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full">
              <Upload className="w-8 h-8 text-gray-600 dark:text-gray-400" />
            </div>
            {isDragActive ? (
              <p className="text-lg font-medium text-blue-600 dark:text-blue-400">
                Drop the image here...
              </p>
            ) : (
              <>
                <div>
                  <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                    Drag & drop an image here
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    or click to select
                  </p>
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  Supports: JPEG, PNG, GIF, BMP, WebP
                </p>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="relative border-2 border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
          <div className="relative aspect-video bg-gray-100 dark:bg-gray-800">
            {preview && (
              <img
                src={preview}
                alt="Selected"
                className="w-full h-full object-contain"
              />
            )}
            {!preview && (
              <div className="flex items-center justify-center h-full">
                <ImageIcon className="w-16 h-16 text-gray-400" />
              </div>
            )}
          </div>
          <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={handleRemove}
                className="ml-4 p-2 text-gray-400 hover:text-red-500 transition-colors"
                disabled={disabled}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
