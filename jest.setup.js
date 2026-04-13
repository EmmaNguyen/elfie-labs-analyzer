import '@testing-library/jest-dom'

// Mock react-pdf
jest.mock('react-pdf', () => ({
  Document: ({ children }) => <div data-testid="pdf-document">{children}</div>,
  Page: () => <div data-testid="pdf-page">PDF Page</div>,
  pdfjs: {
    GlobalWorkerOptions: {
      workerSrc: ''
    },
    version: '3.11.174'
  }
}))

// Mock react-dropzone
jest.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
    acceptedFiles: []
  })
}))

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Upload: () => <div data-testid="upload-icon" />,
  FileText: () => <div data-testid="file-text-icon" />,
  Loader2: () => <div data-testid="loader-icon" />,
  AlertCircle: () => <div data-testid="alert-icon" />,
  Languages: () => <div data-testid="languages-icon" />,
  Download: () => <div data-testid="download-icon" />,
  Share2: () => <div data-testid="share-icon" />,
  Settings: () => <div data-testid="settings-icon" />,
}))
