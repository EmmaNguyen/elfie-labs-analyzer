import { analyzePDF, checkHealth } from '../lib/api'
import axios from 'axios'

// Mock axios
jest.mock('axios')

const mockedAxios = axios as jest.Mocked<typeof axios>

describe('API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('checkHealth', () => {
    it('should return health status successfully', async () => {
      const mockResponse = { status: 'healthy', timestamp: '2024-01-15T10:30:00' }
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await checkHealth()
      expect(result).toEqual(mockResponse)
      expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/health')
    })

    it('should throw error when backend is unavailable', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network Error'))

      await expect(checkHealth()).rejects.toThrow('Backend service is unavailable')
    })
  })

  describe('analyzePDF', () => {
    it('should analyze PDF successfully', async () => {
      const mockResponse = {
        success: true,
        summary: {
          total_tests: 5,
          normal: 3,
          abnormal: 2,
          critical: 0,
          analysis_timestamp: '2024-01-15T10:30:00',
          language: 'en'
        },
        results: [
          {
            test_name: 'Glucose',
            value: 95,
            unit: 'mg/dL',
            reference_range: '70-100',
            status: 'Normal',
            severity_tier: 'None',
            patient_explanation: 'Your glucose level is within normal range',
            next_steps: 'Continue current diet and exercise routine'
          }
        ]
      }

      mockedAxios.post.mockResolvedValue({ data: mockResponse })

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const result = await analyzePDF(file, 'en')

      expect(result).toEqual(mockResponse)
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/analyze-pdf',
        expect.any(FormData),
        expect.objectContaining({
          timeout: 120000
        })
      )
    })

    it('should handle network errors', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Network Error'))

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })

      await expect(analyzePDF(file, 'en')).rejects.toThrow('Failed to analyze PDF. Please try again.')
    })
  })
})
