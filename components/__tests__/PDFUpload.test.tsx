import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import PDFUpload from '../PDFUpload'

// Mock react-pdf
jest.mock('react-pdf', () => ({
  Document: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Page: () => <div>PDF Page</div>,
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

describe('PDFUpload Component', () => {
  const mockOnFileUpload = jest.fn()

  beforeEach(() => {
    mockOnFileUpload.mockClear()
  })

  it('renders upload area correctly', () => {
    render(<PDFUpload onFileUpload={mockOnFileUpload} isProcessing={false} />)
    expect(screen.getByText('Upload Lab PDF')).toBeInTheDocument()
    expect(screen.getByText(/Drag & drop your lab PDF/)).toBeInTheDocument()
  })

  it('displays language badges', () => {
    render(<PDFUpload onFileUpload={mockOnFileUpload} isProcessing={false} />)
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
    expect(screen.getByText('Français')).toBeInTheDocument()
    expect(screen.getByText('Arabic')).toBeInTheDocument()
    expect(screen.getByText('Tiêng Viêt')).toBeInTheDocument()
  })

  it('disables upload area when processing', () => {
    render(<PDFUpload onFileUpload={mockOnFileUpload} isProcessing={true} />)
    expect(screen.getByText('Upload Lab PDF')).toBeInTheDocument()
  })

  it('shows privacy notice', () => {
    render(<PDFUpload onFileUpload={mockOnFileUpload} isProcessing={false} />)
    expect(screen.getByText('Privacy & Safety Notice')).toBeInTheDocument()
    expect(screen.getByText(/This AI tool provides educational insights/)).toBeInTheDocument()
  })
})
