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

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
      setError('')
      const reader = new FileReader()
      reader.onload = (e) => {
        setPdfPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    } else {
      setError('Please upload a valid PDF file')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
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
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Lab PDF
          </CardTitle>
          <CardDescription>
            Upload your laboratory results PDF for AI-powered analysis. 
            Supports English, French, Arabic, and Vietnamese documents.
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
              <FileText className="h-12 w-12 mx-auto text-gray-400" />
              {isDragActive ? (
                <p className="text-blue-600">Drop the PDF here...</p>
              ) : (
                <div>
                  <p className="text-gray-600 mb-2">
                    Drag & drop your lab PDF here, or click to browse
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <Badge variant="secondary">PDF</Badge>
                    <Badge variant="secondary">English</Badge>
                    <Badge variant="secondary">Français</Badge>
                    <Badge variant="secondary">Arabic</Badge>
                    <Badge variant="secondary">Tiêng Viêt</Badge>
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
              <span>PDF Preview</span>
              <Button 
                onClick={handleAnalyze}
                disabled={isProcessing}
                className="flex items-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4" />
                    Analyze Results
                  </>
                )}
              </Button>
            </CardTitle>
            <CardDescription>
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

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-semibold mb-1">Privacy & Safety Notice</p>
            <p>
              This AI tool provides educational insights about lab results and is not a substitute 
              for professional medical advice. Do not make medical decisions based solely on this output. 
              Your PDFs are processed temporarily and deleted after analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
