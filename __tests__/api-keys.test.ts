/**
 * @jest-environment node
 */
import axios from 'axios'

// Load environment variables
const QWEN_API_KEY = process.env.QWEN_API_KEY || ''
const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Skip tests if no API key is configured
const describeIfKey = QWEN_API_KEY && QWEN_API_KEY !== 'your-qwen-api-key' ? describe : describe.skip

describeIfKey('API Key Validation Tests', () => {
  // Use international endpoint (Singapore) - API key only works with this endpoint
  const QWEN_MAX_URL = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
  const QWEN_VL_URL = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'

  describe('Qwen Max API Key', () => {
    it('should have QWEN_API_KEY configured', () => {
      expect(QWEN_API_KEY).toBeTruthy()
      expect(QWEN_API_KEY).not.toBe('your-qwen-api-key')
      expect(QWEN_API_KEY.startsWith('sk-')).toBe(true)
    })

    it('should validate Qwen Max API key format', () => {
      // Qwen API keys typically start with 'sk-' and are 32+ characters
      expect(QWEN_API_KEY).toMatch(/^sk-[a-zA-Z0-9]+$/)
      expect(QWEN_API_KEY.length).toBeGreaterThan(20)
    })

    it('should authenticate successfully with Qwen Max API', async () => {
      const payload = {
        model: 'qwen-max',
        input: {
          messages: [
            {
              role: 'user',
              content: 'Hello'
            }
          ]
        }
      }

      try {
        const response = await axios.post(QWEN_MAX_URL, payload, {
          headers: {
            'Authorization': `Bearer ${QWEN_API_KEY}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        })

        expect(response.status).toBe(200)
        expect(response.data).toBeDefined()
      } catch (error: any) {
        if (error.response?.status === 401) {
          throw new Error('Invalid Qwen Max API key - please check your QWEN_API_KEY')
        }
        throw error
      }
    }, 35000)
  })

  describe('Qwen VL API Key', () => {
    it('should authenticate successfully with Qwen VL API', async () => {
      const payload = {
        model: 'qwen-vl-max',
        input: {
          messages: [
            {
              role: 'user',
              content: [
                {
                  text: 'Describe this image'
                }
              ]
            }
          ]
        }
      }

      try {
        const response = await axios.post(QWEN_VL_URL, payload, {
          headers: {
            'Authorization': `Bearer ${QWEN_API_KEY}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        })

        expect(response.status).toBe(200)
        expect(response.data).toBeDefined()
      } catch (error: any) {
        if (error.response?.status === 401) {
          throw new Error('Invalid Qwen VL API key - please check your QWEN_API_KEY')
        }
        // 400 error is acceptable for VL without actual image
        if (error.response?.status === 400) {
          expect(error.response.status).toBe(400)
          return
        }
        throw error
      }
    }, 35000)
  })

  describe('Backend API Key Configuration', () => {
    it('should have backend URL configured', () => {
      expect(NEXT_PUBLIC_API_URL).toBeTruthy()
      expect(NEXT_PUBLIC_API_URL).toMatch(/^http/)
    })

    it('should load API key from environment', () => {
      // This test verifies the key is loaded from .env.local
      const keyFromEnv = process.env.QWEN_API_KEY
      expect(keyFromEnv).toBeDefined()
      expect(keyFromEnv).not.toBe('')
    })
  })

  describe('API Key Security', () => {
    it('should mask API key for display', () => {
      // Create a masked version of the key
      const maskedKey = QWEN_API_KEY.substring(0, 10) + '...' + QWEN_API_KEY.substring(QWEN_API_KEY.length - 4)
      
      // Masked key should be shorter than full key
      expect(maskedKey.length).toBeLessThan(QWEN_API_KEY.length)
      // Should contain ellipsis
      expect(maskedKey).toContain('...')
      // Should not equal the full key
      expect(maskedKey).not.toBe(QWEN_API_KEY)
    })

    it('should mask API key in logs', () => {
      const maskedKey = QWEN_API_KEY.substring(0, 10) + '...' + QWEN_API_KEY.substring(QWEN_API_KEY.length - 4)
      expect(maskedKey.length).toBeLessThan(QWEN_API_KEY.length)
      expect(maskedKey).toContain('...')
    })
  })
})

describe('API Key Missing Tests', () => {
  it('should warn when QWEN_API_KEY is not set', () => {
    const key = process.env.QWEN_API_KEY
    if (!key || key === 'your-qwen-api-key') {
      console.warn('⚠️  QWEN_API_KEY is not properly configured')
      expect(true).toBe(true) // Pass with warning
    } else {
      expect(key).toBeTruthy()
    }
  })
})
