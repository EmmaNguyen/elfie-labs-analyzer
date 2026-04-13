import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Elfie AI Labs Analyzer',
  description: 'Transform lab PDFs into clear, patient-friendly insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <style dangerouslySetInnerHTML={{
          __html: `
            .gradient-bg {
              background: linear-gradient(to bottom right, #eff6ff, #e0e7ff) !important;
            }
            .severity-normal {
              background-color: #dcfce7 !important;
              color: #166534 !important;
              border: 1px solid #bbf7d0 !important;
              border-radius: 9999px !important;
              padding: 0.25rem 0.5rem !important;
              font-size: 0.75rem !important;
              font-weight: 500 !important;
              display: inline-flex !important;
              align-items: center !important;
            }
            .severity-mild {
              background-color: #fef9c3 !important;
              color: #854d0e !important;
              border: 1px solid #fef08a !important;
              border-radius: 9999px !important;
              padding: 0.25rem 0.5rem !important;
              font-size: 0.75rem !important;
              font-weight: 500 !important;
              display: inline-flex !important;
              align-items: center !important;
            }
            .severity-moderate {
              background-color: #ffedd5 !important;
              color: #9a3412 !important;
              border: 1px solid #fed7aa !important;
              border-radius: 9999px !important;
              padding: 0.25rem 0.5rem !important;
              font-size: 0.75rem !important;
              font-weight: 500 !important;
              display: inline-flex !important;
              align-items: center !important;
            }
            .severity-severe {
              background-color: #fee2e2 !important;
              color: #991b1b !important;
              border: 1px solid #fecaca !important;
              border-radius: 9999px !important;
              padding: 0.25rem 0.5rem !important;
              font-size: 0.75rem !important;
              font-weight: 500 !important;
              display: inline-flex !important;
              align-items: center !important;
            }
            .severity-critical {
              background-color: #fecaca !important;
              color: #7f1d1d !important;
              border: 1px solid #fca5a5 !important;
              border-radius: 9999px !important;
              padding: 0.25rem 0.5rem !important;
              font-size: 0.75rem !important;
              font-weight: 500 !important;
              display: inline-flex !important;
              align-items: center !important;
            }
            .upload-area {
              border: 2px dashed #d1d5db !important;
              border-radius: 0.5rem !important;
              padding: 2rem !important;
              text-align: center !important;
              cursor: pointer !important;
              transition: all 0.15s ease-in-out !important;
            }
            .upload-area:hover {
              border-color: #3b82f6 !important;
              background-color: #eff6ff !important;
            }
            .upload-area.drag-active {
              border-color: #3b82f6 !important;
              background-color: #eff6ff !important;
            }
          `
        }} />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen gradient-bg">
          {children}
        </div>
      </body>
    </html>
  )
}
