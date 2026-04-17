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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Normal': return 'bg-green-500 hover:bg-green-600'
      case 'Low': return 'bg-blue-500 hover:bg-blue-600'
      case 'High': return 'bg-orange-500 hover:bg-orange-600'
      case 'Critical': return 'bg-red-500 hover:bg-red-600'
      default: return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'fr', name: 'Français' },
    { code: 'ar', name: 'Arabic' },
    { code: 'vn', name: 'Tiêng Viêt' }
  ]

  return (
    <div className="min-h-screen warm-gradient">
      <div className="container mx-auto py-6 px-4 sm:py-12 sm:px-4">
        {/* Header - Responsive sizing */}
        <header className="text-center mb-8 sm:mb-16">
          <div className="inline-block mb-4 sm:mb-6">
            <span className="text-5xl sm:text-7xl">🏥</span>
          </div>
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-bold text-gray-800 mb-3 sm:mb-4 tracking-tight px-2">
            Understand Your Lab Results
          </h1>
          <div className="w-16 sm:w-24 h-1 bg-blue-500 mx-auto mb-4 sm:mb-6 rounded-full"></div>
          <p className="text-lg sm:text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed px-4">
            Simple language with a voice
          </p>
        </header>

      {/* Language Selector - Responsive */}
      <div className="flex justify-center mb-6 sm:mb-12">
        <Card className="w-full sm:w-fit senior-card">
          <CardContent className="p-4 sm:p-8">
            <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
              <Languages className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
              <div className="flex flex-wrap justify-center gap-2 sm:gap-4">
                {languages.map((lang) => (
                  <Button
                    key={lang.code}
                    variant={currentLanguage === lang.code ? "default" : "outline"}
                    size="lg"
                    onClick={() => setCurrentLanguage(lang.code)}
                    className={`text-base sm:text-lg px-4 sm:px-8 py-4 sm:py-6 flex-1 sm:flex-initial ${
                      currentLanguage === lang.code 
                        ? 'shadow-lg' 
                        : 'hover:bg-white hover:shadow-md'
                    }`}
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
        <div className="space-y-6 sm:space-y-10">
          {/* Results Header - Responsive */}
          <Card className="senior-card">
            <CardHeader className="pb-4 sm:pb-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <CardTitle className="text-2xl sm:text-4xl text-gray-800">Your Results</CardTitle>
                <div className="flex flex-wrap gap-2 sm:gap-3 w-full sm:w-auto">
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="text-sm sm:text-lg px-3 sm:px-6 py-3 sm:py-5 flex-1 sm:flex-initial"
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
                        <VolumeX className="h-4 w-4 sm:h-6 sm:w-6 mr-1 sm:mr-2" />
                        <span className="text-sm sm:text-lg">Stop</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-4 w-4 sm:h-6 sm:w-6 mr-1 sm:mr-2" />
                        <span className="text-sm sm:text-lg">Listen</span>
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="lg" className="text-sm sm:text-lg px-3 sm:px-6 py-3 sm:py-5 flex-1 sm:flex-initial" onClick={() => setShowExportModal(true)}>
                    <Download className="h-4 w-4 sm:h-6 sm:w-6 mr-1 sm:mr-2" />
                    <span className="hidden sm:inline">Export</span>
                  </Button>
                  <Button variant="outline" size="lg" className="text-sm sm:text-lg px-3 sm:px-6 py-3 sm:py-5 flex-1 sm:flex-initial" onClick={() => setShowExportModal(true)}>
                    <Share2 className="h-4 w-4 sm:h-6 sm:w-6 mr-1 sm:mr-2" />
                    <span className="hidden sm:inline">Share</span>
                  </Button>
                </div>
              </div>
              <CardDescription className="text-base sm:text-xl mt-2">
                Here's what your blood tests show, explained in simple terms
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Summary Statistics - Responsive grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-8 mb-6 sm:mb-10">
                <div className="text-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border-2 border-gray-200 shadow-md">
                  <div className="text-3xl sm:text-5xl font-bold text-gray-800 mb-1 sm:mb-3">
                    {analysisResults.summary.total_tests}
                  </div>
                  <div className="text-sm sm:text-xl font-semibold text-gray-700">Tests Done</div>
                </div>
                <div className="text-center p-4 sm:p-8 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl border-2 border-green-300 shadow-md">
                  <div className="text-3xl sm:text-5xl font-bold text-green-700 mb-1 sm:mb-3">
                    {analysisResults.summary.normal}
                  </div>
                  <div className="text-sm sm:text-xl font-semibold text-green-800">✓ Looking Good</div>
                </div>
                <div className="text-center p-4 sm:p-8 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-2xl border-2 border-yellow-300 shadow-md">
                  <div className="text-3xl sm:text-5xl font-bold text-yellow-700 mb-1 sm:mb-3">
                    {analysisResults.summary.abnormal}
                  </div>
                  <div className="text-sm sm:text-xl font-semibold text-yellow-800">⚠ Needs Attention</div>
                </div>
                <div className="text-center p-4 sm:p-8 bg-gradient-to-br from-red-50 to-red-100 rounded-2xl border-2 border-red-300 shadow-md">
                  <div className="text-3xl sm:text-5xl font-bold text-red-700 mb-1 sm:mb-3">
                    {analysisResults.summary.critical}
                  </div>
                  <div className="text-sm sm:text-xl font-semibold text-red-800">🔴 See Doctor</div>
                </div>
              </div>

              <div className="text-base sm:text-lg text-gray-600 mb-4 font-medium">
                Showing {analysisResults.results.length} test results below
              </div>
              <div className="space-y-4 sm:space-y-8">
                {analysisResults.results.map((result: LabResult, index: number) => (
                  <Card key={`${result.test_name}-${index}`} className="senior-card border-l-4 sm:border-l-8 border-l-blue-500">
                    <CardContent className="p-4 sm:p-10">
                      {/* Header with number, name, and value - Responsive */}
                      <div className="flex flex-col sm:flex-row items-start justify-between mb-4 sm:mb-6">
                        <div className="flex-1 w-full">
                          <div className="flex items-center gap-2 sm:gap-4 mb-2 sm:mb-3">
                            <span className="flex items-center justify-center w-8 h-8 sm:w-12 sm:h-12 bg-blue-100 text-blue-800 rounded-full text-base sm:text-xl font-bold flex-shrink-0">
                              {index + 1}
                            </span>
                            <h3 className="text-lg sm:text-2xl font-bold text-gray-900">
                              {result.test_name}
                            </h3>
                          </div>
                          
                          {/* Value, Unit, Reference Range, and Status - Responsive */}
                          <div className="flex flex-wrap items-center gap-2 sm:gap-6 sm:ml-16">
                            <span className="text-2xl sm:text-5xl font-bold text-gray-900">
                              {result.value}
                            </span>
                            <span className="text-lg sm:text-3xl text-gray-600 font-semibold">
                              {result.unit}
                            </span>
                            <span className="text-lg sm:text-3xl text-gray-400">|</span>
                            <span className="text-sm sm:text-xl text-gray-600 w-full sm:w-auto">
                              Ref: <span className="font-bold text-gray-800">{result.reference_range}</span>
                            </span>
                            <Badge className={`${getStatusColor(result.status)} text-white text-sm sm:text-lg px-3 sm:px-5 py-1.5 sm:py-2.5 shadow-sm`}>
                              {result.status}
                            </Badge>
                            {result.severity_tier !== 'None' && (
                              <Badge className={`${getSeverityColor(result.severity_tier)} text-sm sm:text-lg px-3 sm:px-5 py-1.5 sm:py-2.5 shadow-sm`}>
                                {result.severity_tier}
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        {/* Voice button - Responsive */}
                        <div className="flex items-center gap-2 mt-3 sm:mt-0">
                          <Button
                            variant="outline"
                            size="lg"
                            onClick={() => {
                              const text = `${result.test_name}: ${result.value} ${result.unit}. ${result.patient_explanation}`
                              generateSpeech(text)
                            }}
                            disabled={isSpeaking}
                            className="text-blue-700 hover:bg-blue-50 border-2 border-blue-600 text-sm sm:text-base px-3 sm:px-6 py-2 sm:py-5"
                          >
                            <Volume2 className="h-6 w-6 mr-2" />
                            <span className="text-lg">Listen</span>
                          </Button>
                        </div>
                      </div>
                      
                      {/* Explanation and Next Steps - Responsive */}
                      <div className="grid md:grid-cols-2 gap-4 sm:gap-8 mt-4 sm:mt-8 sm:ml-16">
                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 sm:p-8 rounded-2xl border-2 border-blue-200 shadow-sm">
                          <h4 className="font-bold text-blue-900 mb-2 sm:mb-4 text-base sm:text-xl flex items-center gap-2 sm:gap-3">
                            <span className="text-xl sm:text-2xl">💡</span>
                            What This Means for You
                          </h4>
                          <p className="text-sm sm:text-lg text-blue-800 leading-relaxed">
                            {result.patient_explanation}
                          </p>
                        </div>
                        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 sm:p-8 rounded-2xl border-2 border-green-200 shadow-sm">
                          <h4 className="font-bold text-green-900 mb-2 sm:mb-4 text-base sm:text-xl flex items-center gap-2 sm:gap-3">
                            <span className="text-xl sm:text-2xl">👉</span>
                            What You Should Do
                          </h4>
                          <p className="text-sm sm:text-lg text-green-800 leading-relaxed">
                            {result.next_steps}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="mt-8 flex justify-center">
                <Button 
                  onClick={() => setAnalysisResults(null)}
                  variant="outline"
                  size="lg"
                  className="text-lg px-8 py-6 shadow-md hover:shadow-lg transition-shadow"
                >
                  <span className="text-xl mr-2">📄</span>
                  Check Different Results
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Footer - Reassuring message */}
      <footer className="mt-20 text-center">
        <div className="w-16 h-0.5 bg-gray-300 mx-auto mb-6 rounded-full"></div>
        <p className="text-base text-gray-600 max-w-3xl mx-auto leading-relaxed mb-4">
          <strong>Important:</strong> This is general information to help you understand your results. 
          It is not medical advice. Always talk to your doctor about what your results mean for your health.
        </p>
        <p className="text-sm text-gray-500">
          © 2024 Elfie - Making lab results easier to understand
        </p>
      </footer>

      {showExportModal && analysisResults && (
        <ExportModal 
          results={analysisResults} 
          onClose={() => setShowExportModal(false)} 
        />
      )}
      </div>
    </div>
  )
}
