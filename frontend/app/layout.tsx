import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

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
      <body className={`${inter.className} bg-background text-foreground antialiased selection:bg-primary selection:text-black`}>
        <Navbar />
        {children}
      </body>
    </html>
  )
}
