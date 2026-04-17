'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Document, Page, pdfjs } from 'react-pdf'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Upload, FileText, Loader2, AlertCircle } from 'lucide-react'

// Import react-pdf CSS
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Use CDN worker to avoid Next.js bundling issues
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`

interface PDFUploadProps {
  onFileUpload: (file: File) => void
  isProcessing: boolean
}

export default function PDFUpload({ onFileUpload, isProcessing }: PDFUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [pdfPreview, setPdfPreview] = useState<string | null>(null)
  const [numPages, setNumPages] = useState<number>(0)
  const [error, setError] = useState<string>('')

  const isProbablyPdf = useCallback((file: File) => {
    const fileName = (file?.name || '').toLowerCase()
    const fileType = (file?.type || '').toLowerCase()
    return fileType === 'application/pdf' || fileName.endsWith('.pdf')
  }, [])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file && isProbablyPdf(file)) {
      setSelectedFile(file)
      setError('')
      const reader = new FileReader()
      reader.onload = (e) => {
        setPdfPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    } else {
      setError('Please upload a valid PDF file (.pdf)')
    }
  }, [isProbablyPdf])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected: (fileRejections) => {
      const message =
        fileRejections[0]?.errors?.[0]?.message ||
        'File not accepted. Please upload a PDF file (.pdf).'
      setError(message)
    },
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled: isProcessing
  })

  const handleAnalyze = () => {
    if (selectedFile) {
      onFileUpload(selectedFile)
    }
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <Upload className="h-6 w-6" />
            Upload Your Blood Test Results
          </CardTitle>
          <CardDescription className="text-lg">
            Upload the PDF file from your doctor or lab. We'll explain what everything means in simple terms.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`
              upload-area
              ${isDragActive ? 'drag-active' : 'border-gray-300 hover:border-gray-400'}
              ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <FileText className="h-16 w-16 mx-auto text-gray-400" />
              {isDragActive ? (
                <p className="text-blue-600 text-lg">Drop your PDF here...</p>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2 text-lg">
                    Drag & drop your PDF here, or click to choose file
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <Badge variant="secondary" className="text-base px-4 py-2">PDF files</Badge>
                    <Badge variant="secondary" className="text-base px-4 py-2">English</Badge>
                    <Badge variant="secondary" className="text-base px-4 py-2">Français</Badge>
                    <Badge variant="secondary" className="text-base px-4 py-2">Arabic</Badge>
                    <Badge variant="secondary" className="text-base px-4 py-2">Tiếng Việt</Badge>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {selectedFile && pdfPreview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="text-2xl">Your File</span>
              <Button 
                onClick={handleAnalyze}
                disabled={isProcessing}
                className="flex items-center gap-2 text-lg px-6 py-5"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Reading Your Results...
                  </>
                ) : (
                  <>
                    <FileText className="h-5 w-5" />
                    Explain My Results
                  </>
                )}
              </Button>
            </CardTitle>
            <CardDescription className="text-base">
              {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden bg-gray-50">
              <Document
                file={pdfPreview}
                onLoadSuccess={onDocumentLoadSuccess}
                className="max-h-96 overflow-y-auto"
              >
                <Page pageNumber={1} className="mx-auto" />
              </Document>
            </div>
            {numPages > 1 && (
              <p className="text-sm text-gray-500 mt-2 text-center">
                Document has {numPages} page{numPages > 1 ? 's' : ''}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-6 w-6 text-blue-600 mt-0.5" />
          <div className="text-base text-blue-800">
            <p className="font-bold mb-2 text-lg">🔒 Your Privacy Matters</p>
            <p className="leading-relaxed">
              This tool helps you understand your lab results in simple language. 
              It does not replace your doctor's advice. Always talk to your doctor about your health. 
              Your files are deleted right after we read them - we don't keep them.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
