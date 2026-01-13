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

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation()
    onFileSelect(null as any)
    setPreview(null)
  }

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
            transition-all duration-300 group
            ${isDragActive
              ? 'border-primary bg-primary/10 scale-[1.02]'
              : 'border-white/10 hover:border-primary/50 hover:bg-white/5'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center space-y-6">
            <div className={`
                p-5 rounded-full transition-transform duration-300 group-hover:scale-110
                ${isDragActive ? 'bg-primary/20' : 'bg-surface border border-white/5'}
            `}>
              <Upload className={`w-8 h-8 ${isDragActive ? 'text-primary' : 'text-gray-400 group-hover:text-primary'}`} />
            </div>

            <div className="space-y-2">
              <p className={`text-lg font-medium transition-colors ${isDragActive ? 'text-primary' : 'text-white'}`}>
                {isDragActive ? 'Drop signal here' : 'Initialize Data Stream'}
              </p>
              <p className="text-sm text-gray-400">
                Drag & drop or click to upload source
              </p>
            </div>

            <div className="flex items-center space-x-2 text-xs text-gray-500 font-mono border border-white/5 rounded-full px-3 py-1">
              <span>SUPPORTED FORMATS:</span>
              <span className="text-gray-400">JPG • PNG • WEBP</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative border border-white/10 rounded-xl overflow-hidden group">
          <div className="relative aspect-video bg-black/50 flex items-center justify-center p-4">
            {preview ? (
              <img
                src={preview}
                alt="Selected"
                className="w-full h-full object-contain shadow-2xl"
              />
            ) : (
              <ImageIcon className="w-16 h-16 text-gray-700" />
            )}

            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-4 transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
            <div className="flex items-center justify-between glass p-3 rounded-lg">
              <div className="flex-1 min-w-0 mr-4">
                <p className="text-sm font-medium text-white truncate font-mono">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-primary/80 font-mono">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={handleRemove}
                className="p-2 text-gray-400 hover:text-red-500 hover:bg-white/10 rounded-lg transition-colors"
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
