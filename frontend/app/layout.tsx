import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Image Protection - AI Feature Extraction Protection',
  description: 'Protect your images from AI-based feature extraction using adversarial attacks',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
