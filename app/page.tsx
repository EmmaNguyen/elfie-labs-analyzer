'use client'

import { useState } from 'react'
import PDFUpload from '@/components/PDFUpload'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Languages, Download, Share2, Settings, AlertCircle, Volume2, VolumeX } from 'lucide-react'
import { analyzePDF, LabResult, AnalysisResponse } from '@/lib/api'
import ExportModal from '@/components/ExportModal'

export default function HomePage() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null)
  const [currentLanguage, setCurrentLanguage] = useState('en')
  const [showExportModal, setShowExportModal] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null)

  const generateSpeech = async (text: string) => {
    try {
      console.log('Generating speech for:', text.substring(0, 50) + '...')
      
      // Stop any currently playing audio first
      stopSpeaking()
      
      setIsSpeaking(true)
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('Using API:', API_BASE_URL)
      
      const formData = new FormData()
      formData.append('text', text)
      formData.append('provider', 'qwen')
      formData.append('voice_id', 'Cherry')
      formData.append('language', currentLanguage)
      
      console.log('Sending TTS request...')
      const response = await fetch(`${API_BASE_URL}/text-to-speech`, {
        method: 'POST',
        body: formData,
      })
      
      console.log('Response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`Failed to generate speech: ${response.status}`)
      }
      
      const audioBlob = await response.blob()
      console.log('Audio blob size:', audioBlob.size, 'bytes')
      
      const url = URL.createObjectURL(audioBlob)
      setAudioUrl(url)
      console.log('Audio URL created:', url)
      
      const audio = new Audio(url)
      setCurrentAudio(audio)
      
      console.log('Playing audio...')
      const playPromise = audio.play()
      
      if (playPromise !== undefined) {
        playPromise.then(() => {
          console.log('Audio playing successfully')
        }).catch(error => {
          console.error('Audio play error:', error)
          alert('Could not play audio. Please click the button again.')
          setIsSpeaking(false)
        })
      }
      
      audio.onended = () => {
        console.log('Audio finished playing')
        setIsSpeaking(false)
        setCurrentAudio(null)
      }
      
      audio.onerror = (e) => {
        console.error('Audio error:', e)
        setIsSpeaking(false)
      }
    } catch (error) {
      console.error('Error generating speech:', error)
      alert('Failed to generate speech. Please try again.')
      setIsSpeaking(false)
    }
  }

  const stopSpeaking = () => {
    // Stop current audio playback
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      setCurrentAudio(null)
    }
    setIsSpeaking(false)
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
  }

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true)
    
    try {
      console.log('=== Starting PDF upload ===')
      console.log('File name:', file.name)
      console.log('File type:', file.type)
      console.log('File size:', file.size)
      console.log('Language:', currentLanguage)
      
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('API_BASE_URL from env:', process.env.NEXT_PUBLIC_API_URL)
      console.log('API_BASE_URL fallback:', 'http://localhost:8000')
      console.log('Final API_BASE_URL:', API_BASE_URL)
      console.log('Full URL:', `${API_BASE_URL}/analyze-pdf`)
      
      // Add direct API call as fallback
      console.log('Attempting direct fetch to:', `${API_BASE_URL}/analyze-pdf`)
      
      const formData = new FormData()
      formData.append('pdf_file', file)
      formData.append('language', currentLanguage)
      
      const response = await fetch(`${API_BASE_URL}/analyze-pdf`, {
        method: 'POST',
        body: formData,
      })
      
      console.log('Fetch response status:', response.status)
      console.log('Fetch response ok:', response.ok)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Fetch error response:', errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const results = await response.json()
      console.log('=== PDF analysis successful ===')
      console.log('Results:', results)
      console.log('Number of tests:', results.summary?.total_tests)
      console.log('Results array length:', results.results?.length)
      console.log('First result:', results.results?.[0])
      setAnalysisResults(results)
    } catch (error) {
      console.error('=== Error processing PDF ===')
      console.error('Error object:', error)
      console.error('Error type:', typeof error)
      console.error('Error message:', error instanceof Error ? error.message : 'No message')
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack')
      if (error && typeof error === 'object') {
        console.error('Error keys:', Object.keys(error))
        console.error('Error stringified:', JSON.stringify(error))
      }
      // Show error to user
      alert(error instanceof Error ? error.message : 'Failed to analyze PDF. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'None': return 'severity-normal'
      case 'Mild': return 'severity-mild'
      case 'Moderate': return 'severity-moderate'
      case 'Severe': return 'severity-severe'
      default: return 'severity-normal'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Normal': return 'bg-green-500'
      case 'Low': return 'bg-blue-500'
      case 'High': return 'bg-orange-500'
      case 'Critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'fr', name: 'Français' },
    { code: 'ar', name: 'Arabic' },
    { code: 'vn', name: 'Tiêng Viêt' }
  ]

  return (
    <div className="container mx-auto py-8 px-4">
      <header className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Elfie AI Labs Analyzer
        </h1>
        <p className="text-xl text-gray-600">
          Transform complex lab results into clear, patient-friendly insights
        </p>
      </header>

      <div className="flex justify-center mb-6">
        <Card className="w-fit">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <Languages className="h-5 w-5 text-gray-500" />
              <div className="flex gap-2">
                {languages.map((lang) => (
                  <Button
                    key={lang.code}
                    variant={currentLanguage === lang.code ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentLanguage(lang.code)}
                  >
                    {lang.name}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {!analysisResults ? (
        <PDFUpload onFileUpload={handleFileUpload} isProcessing={isProcessing} />
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Analysis Results</CardTitle>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => {
                      if (isSpeaking) {
                        stopSpeaking()
                      } else {
                        const summaryText = analysisResults.results.map(r => 
                          `${r.test_name}: ${r.value} ${r.unit}. ${r.patient_explanation}`
                        ).join('. ')
                        generateSpeech(summaryText)
                      }
                    }}
                    disabled={isSpeaking && !audioUrl}
                  >
                    {isSpeaking ? (
                      <>
                        <VolumeX className="h-4 w-4 mr-2" />
                        Stop
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-4 w-4 mr-2" />
                        Listen
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setShowExportModal(true)}>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setShowExportModal(true)}>
                    <Share2 className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </div>
              </div>
              <CardDescription>
                AI-powered analysis of your laboratory results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {analysisResults.summary.total_tests}
                  </div>
                  <div className="text-sm text-gray-600">Total Tests</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {analysisResults.summary.normal}
                  </div>
                  <div className="text-sm text-gray-600">Normal</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {analysisResults.summary.abnormal}
                  </div>
                  <div className="text-sm text-gray-600">Abnormal</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {analysisResults.summary.critical}
                  </div>
                  <div className="text-sm text-gray-600">Critical</div>
                </div>
              </div>

              <div className="text-sm text-gray-500 mb-2">
                Rendering {analysisResults.results.length} test results
              </div>
              <div className="space-y-4">
                {analysisResults.results.map((result: LabResult, index: number) => (
                  <Card key={index} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            {result.test_name}
                          </h3>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="font-medium">
                              {result.value} {result.unit}
                            </span>
                            <span className="text-gray-500">
                              Range: {result.reference_range}
                            </span>
                            <Badge className={getSeverityColor(result.severity_tier)}>
                              {result.severity_tier}
                            </Badge>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const text = `${result.test_name}: ${result.value} ${result.unit}. ${result.patient_explanation} ${result.next_steps}`
                              generateSpeech(text)
                            }}
                            disabled={isSpeaking}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <Volume2 className="h-4 w-4" />
                          </Button>
                          <div className={`w-3 h-3 rounded-full ${getStatusIcon(result.status)}`} />
                        </div>
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                          <h4 className="font-medium text-blue-900 mb-2">
                            What this means
                          </h4>
                          <p className="text-sm text-blue-800">
                            {result.patient_explanation}
                          </p>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                          <h4 className="font-medium text-green-900 mb-2">
                            Next steps
                          </h4>
                          <p className="text-sm text-green-800">
                            {result.next_steps}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="mt-6 flex justify-center">
                <Button 
                  onClick={() => setAnalysisResults(null)}
                  variant="outline"
                >
                  Analyze Another PDF
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <footer className="mt-16 text-center text-sm text-gray-500">
        <p>
          © 2024 Elfie AI Labs Analyzer. This tool provides educational insights only and is not a substitute for professional medical advice.
        </p>
      </footer>

      {showExportModal && analysisResults && (
        <ExportModal 
          results={analysisResults} 
          onClose={() => setShowExportModal(false)} 
        />
      )}
    </div>
  )
}
