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
    <div className="container mx-auto py-8 px-4">
      {/* Header - Larger text for better visibility */}
      <header className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Elfie AI Labs Analyzer
        </h1>
        <p className="text-2xl text-gray-700">
          Transform complex lab results into clear, patient-friendly insights
        </p>
      </header>

      {/* Language Selector - Larger buttons */}
      <div className="flex justify-center mb-8">
        <Card className="w-fit">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <Languages className="h-6 w-6 text-gray-600" />
              <div className="flex gap-3">
                {languages.map((lang) => (
                  <Button
                    key={lang.code}
                    variant={currentLanguage === lang.code ? "default" : "outline"}
                    size="lg"
                    onClick={() => setCurrentLanguage(lang.code)}
                    className="text-lg px-6 py-5"
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
        <div className="space-y-8">
          {/* Results Header - Larger text and buttons */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-3xl">Analysis Results</CardTitle>
                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="text-lg px-6 py-5"
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
                        <VolumeX className="h-6 w-6 mr-2" />
                        <span className="text-lg">Stop</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-6 w-6 mr-2" />
                        <span className="text-lg">Listen</span>
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="lg" className="text-lg px-6 py-5" onClick={() => setShowExportModal(true)}>
                    <Download className="h-6 w-6 mr-2" />
                    Export
                  </Button>
                  <Button variant="outline" size="lg" className="text-lg px-6 py-5" onClick={() => setShowExportModal(true)}>
                    <Share2 className="h-6 w-6 mr-2" />
                    Share
                  </Button>
                </div>
              </div>
              <CardDescription className="text-xl mt-2">
                AI-powered analysis of your laboratory results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Summary Statistics - Larger and clearer */}
              <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="text-center p-6 bg-gray-100 rounded-xl border-2 border-gray-300">
                  <div className="text-4xl font-bold text-gray-900 mb-2">
                    {analysisResults.summary.total_tests}
                  </div>
                  <div className="text-xl font-semibold text-gray-700">Total Tests</div>
                </div>
                <div className="text-center p-6 bg-green-100 rounded-xl border-2 border-green-400">
                  <div className="text-4xl font-bold text-green-700 mb-2">
                    {analysisResults.summary.normal}
                  </div>
                  <div className="text-xl font-semibold text-green-800">Normal</div>
                </div>
                <div className="text-center p-6 bg-yellow-100 rounded-xl border-2 border-yellow-400">
                  <div className="text-4xl font-bold text-yellow-700 mb-2">
                    {analysisResults.summary.abnormal}
                  </div>
                  <div className="text-xl font-semibold text-yellow-800">Abnormal</div>
                </div>
                <div className="text-center p-6 bg-red-100 rounded-xl border-2 border-red-400">
                  <div className="text-4xl font-bold text-red-700 mb-2">
                    {analysisResults.summary.critical}
                  </div>
                  <div className="text-xl font-semibold text-red-800">Critical</div>
                </div>
              </div>

              <div className="text-lg text-gray-600 mb-4 font-medium">
                Showing {analysisResults.results.length} test results
              </div>
              <div className="space-y-6">
                {analysisResults.results.map((result: LabResult, index: number) => (
                  <Card key={`${result.test_name}-${index}`} className="border-l-8 border-l-blue-600 shadow-lg">
                    <CardContent className="p-8">
                      {/* Header with number, name, and value - Larger for seniors */}
                      <div className="flex items-start justify-between mb-6">
                        <div className="flex-1">
                          <div className="flex items-center gap-4 mb-3">
                            <span className="flex items-center justify-center w-12 h-12 bg-blue-100 text-blue-800 rounded-full text-xl font-bold">
                              {index + 1}
                            </span>
                            <h3 className="text-2xl font-bold text-gray-900">
                              {result.test_name}
                            </h3>
                          </div>
                          
                          {/* Value, Unit, Reference Range, and Status - Larger text */}
                          <div className="flex flex-wrap items-center gap-4 ml-16">
                            <span className="text-4xl font-bold text-gray-900">
                              {result.value}
                            </span>
                            <span className="text-2xl text-gray-700 font-semibold">
                              {result.unit}
                            </span>
                            <span className="text-2xl text-gray-500">|</span>
                            <span className="text-xl text-gray-600">
                              Ref: <span className="font-bold text-gray-800">{result.reference_range}</span>
                            </span>
                            <Badge className={`${getStatusColor(result.status)} text-white text-lg px-4 py-2`}>
                              {result.status}
                            </Badge>
                            {result.severity_tier !== 'None' && (
                              <Badge className={`${getSeverityColor(result.severity_tier)} text-lg px-4 py-2`}>
                                {result.severity_tier}
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        {/* Voice button - Larger for seniors */}
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="lg"
                            onClick={() => {
                              const text = `${result.test_name}: ${result.value} ${result.unit}. ${result.patient_explanation}`
                              generateSpeech(text)
                            }}
                            disabled={isSpeaking}
                            className="text-blue-700 hover:bg-blue-50 border-2 border-blue-600"
                          >
                            <Volume2 className="h-6 w-6 mr-2" />
                            <span className="text-lg">Listen</span>
                          </Button>
                        </div>
                      </div>
                      
                      {/* Explanation and Next Steps - Larger text */}
                      <div className="grid md:grid-cols-2 gap-6 ml-16">
                        <div className="bg-blue-50 p-6 rounded-xl border-2 border-blue-200">
                          <h4 className="font-bold text-blue-900 mb-3 text-xl">
                            What this means
                          </h4>
                          <p className="text-lg text-blue-800 leading-relaxed">
                            {result.patient_explanation}
                          </p>
                        </div>
                        <div className="bg-green-50 p-6 rounded-xl border-2 border-green-200">
                          <h4 className="font-bold text-green-900 mb-3 text-xl">
                            Next steps
                          </h4>
                          <p className="text-lg text-green-800 leading-relaxed">
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
