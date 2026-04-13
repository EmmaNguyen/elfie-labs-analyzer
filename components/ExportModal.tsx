'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Download, FileText, Share2, Copy, Check } from 'lucide-react'
import { AnalysisResponse } from '@/lib/api'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

interface ExportModalProps {
  results: AnalysisResponse
  onClose: () => void
}

export default function ExportModal({ results, onClose }: ExportModalProps) {
  const [copiedToClipboard, setCopiedToClipboard] = useState(false)

  const exportPatientPDF = async () => {
    const pdf = new jsPDF()
    const pageWidth = pdf.internal.pageSize.getWidth()
    const margin = 20
    let yPosition = margin

    // Title
    pdf.setFontSize(20)
    pdf.text('Lab Results Summary', margin, yPosition)
    yPosition += 15

    // Date and language
    pdf.setFontSize(12)
    pdf.text(`Analysis Date: ${new Date(results.summary.analysis_timestamp || new Date()).toLocaleDateString()}`, margin, yPosition)
    yPosition += 8
    pdf.text(`Language: ${(results.summary.language || 'en').toUpperCase()}`, margin, yPosition)
    yPosition += 15

    // Summary
    pdf.setFontSize(14)
    pdf.text('Summary', margin, yPosition)
    yPosition += 10
    pdf.setFontSize(11)
    pdf.text(`Total Tests: ${results.summary.total_tests}`, margin, yPosition)
    yPosition += 6
    pdf.text(`Normal: ${results.summary.normal}`, margin, yPosition)
    yPosition += 6
    pdf.text(`Abnormal: ${results.summary.abnormal}`, margin, yPosition)
    yPosition += 6
    pdf.text(`Critical: ${results.summary.critical}`, margin, yPosition)
    yPosition += 15

    // Individual results
    pdf.setFontSize(14)
    pdf.text('Test Results', margin, yPosition)
    yPosition += 10

    results.results.forEach((result, index) => {
      if (yPosition > 250) {
        pdf.addPage()
        yPosition = margin
      }

      pdf.setFontSize(12)
      pdf.setFont('helvetica', 'bold')
      pdf.text(result.test_name, margin, yPosition)
      yPosition += 8

      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(10)
      pdf.text(`Value: ${result.value} ${result.unit || ''}`, margin + 5, yPosition)
      yPosition += 6
      pdf.text(`Reference Range: ${result.reference_range || 'Not provided'}`, margin + 5, yPosition)
      yPosition += 6
      pdf.text(`Status: ${result.status}`, margin + 5, yPosition)
      yPosition += 8

      // Explanation
      pdf.text('What this means:', margin + 5, yPosition)
      yPosition += 6
      const explanationLines = pdf.splitTextToSize(result.patient_explanation, pageWidth - margin * 2 - 10)
      explanationLines.forEach((line: string) => {
        pdf.text(line, margin + 10, yPosition)
        yPosition += 5
      })
      yPosition += 5

      // Next steps
      pdf.text('Next steps:', margin + 5, yPosition)
      yPosition += 6
      const nextStepsLines = pdf.splitTextToSize(result.next_steps, pageWidth - margin * 2 - 10)
      nextStepsLines.forEach((line: string) => {
        pdf.text(line, margin + 10, yPosition)
        yPosition += 5
      })
      yPosition += 10
    })

    // Disclaimer
    pdf.addPage()
    yPosition = margin
    pdf.setFontSize(12)
    pdf.setFont('helvetica', 'bold')
    pdf.text('Important Notice', margin, yPosition)
    yPosition += 10
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(10)
    const disclaimer = 'This AI-generated summary is for educational purposes only and is not a substitute for professional medical advice. Do not make medical decisions based solely on this output. Always consult with your healthcare provider for proper diagnosis and treatment.'
    const disclaimerLines = pdf.splitTextToSize(disclaimer, pageWidth - margin * 2)
    disclaimerLines.forEach((line: string) => {
      pdf.text(line, margin, yPosition)
      yPosition += 5
    })

    pdf.save('lab-results-summary.pdf')
  }

  const exportClinicianJSON = () => {
    const clinicianData = {
      patient_summary: {
        total_tests: results.summary.total_tests,
        normal_count: results.summary.normal,
        abnormal_count: results.summary.abnormal,
        critical_count: results.summary.critical,
        analysis_date: results.summary.analysis_timestamp,
        language: results.summary.language
      },
      detailed_results: results.results.map(result => ({
        test_name: result.test_name,
        loinc_code: result.loinc_code,
        value: result.value,
        unit: result.unit,
        reference_range: result.reference_range,
        status: result.status,
        severity_tier: result.severity_tier,
        clinical_notes: `${result.patient_explanation} ${result.next_steps}`
      })),
      export_metadata: {
        export_timestamp: new Date().toISOString(),
        export_version: '1.0',
        source: 'Elfie AI Labs Analyzer'
      }
    }

    const dataStr = JSON.stringify(clinicianData, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = 'lab-results-clinician.json'

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const copyToClipboard = async () => {
    const summaryText = results.results.map(result => 
      `${result.test_name}: ${result.value} ${result.unit} (Range: ${result.reference_range}) - ${result.status}
       ${result.patient_explanation}
       Next steps: ${result.next_steps}`
    ).join('\n\n')

    try {
      await navigator.clipboard.writeText(summaryText)
      setCopiedToClipboard(true)
      setTimeout(() => setCopiedToClipboard(false), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const shareResults = async () => {
    const shareData = {
      title: 'Lab Results Analysis',
      text: `I analyzed my lab results with Elfie AI. Found ${results.summary.abnormal} abnormal results out of ${results.summary.total_tests} tests.`,
      url: window.location.href
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
      } else {
        // Fallback to copying to clipboard
        await copyToClipboard()
      }
    } catch (err) {
      console.error('Error sharing:', err)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Export & Share Results
          </CardTitle>
          <CardDescription>
            Choose how you'd like to export your lab results analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Summary Preview */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Analysis Summary</h3>
            <div className="grid grid-cols-4 gap-2 text-sm">
              <div className="text-center">
                <div className="font-bold">{results.summary.total_tests}</div>
                <div className="text-gray-600">Total</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-green-600">{results.summary.normal}</div>
                <div className="text-gray-600">Normal</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-yellow-600">{results.summary.abnormal}</div>
                <div className="text-gray-600">Abnormal</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-red-600">{results.summary.critical}</div>
                <div className="text-gray-600">Critical</div>
              </div>
            </div>
          </div>

          {/* Export Options */}
          <div className="space-y-4">
            <h3 className="font-semibold">Export Options</h3>
            
            <div className="grid gap-3">
              <Button 
                onClick={exportPatientPDF}
                className="flex items-center justify-start gap-3 h-auto p-4"
                variant="outline"
              >
                <FileText className="h-5 w-5 text-blue-500" />
                <div className="text-left">
                  <div className="font-medium">Patient Summary PDF</div>
                  <div className="text-sm text-gray-600">
                    Easy-to-read summary for patients and caregivers
                  </div>
                </div>
                <Download className="h-4 w-4 ml-auto" />
              </Button>

              <Button 
                onClick={exportClinicianJSON}
                className="flex items-center justify-start gap-3 h-auto p-4"
                variant="outline"
              >
                <FileText className="h-5 w-5 text-green-500" />
                <div className="text-left">
                  <div className="font-medium">Clinician JSON Export</div>
                  <div className="text-sm text-gray-600">
                    Structured data for healthcare providers
                  </div>
                </div>
                <Download className="h-4 w-4 ml-auto" />
              </Button>

              <Button 
                onClick={copyToClipboard}
                className="flex items-center justify-start gap-3 h-auto p-4"
                variant="outline"
              >
                <Copy className="h-5 w-5 text-purple-500" />
                <div className="text-left">
                  <div className="font-medium">Copy to Clipboard</div>
                  <div className="text-sm text-gray-600">
                    Copy summary text for easy sharing
                  </div>
                </div>
                {copiedToClipboard ? (
                  <Check className="h-4 w-4 ml-auto text-green-500" />
                ) : (
                  <Copy className="h-4 w-4 ml-auto" />
                )}
              </Button>

              <Button 
                onClick={shareResults}
                className="flex items-center justify-start gap-3 h-auto p-4"
                variant="outline"
              >
                <Share2 className="h-5 w-5 text-orange-500" />
                <div className="text-left">
                  <div className="font-medium">Share Results</div>
                  <div className="text-sm text-gray-600">
                    Share via messaging apps or email
                  </div>
                </div>
              </Button>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-800">
              <p className="font-semibold mb-1">Privacy Notice</p>
              <p>
                When you export or share results, be mindful of privacy. 
                Only share with trusted healthcare providers or family members.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button onClick={onClose} variant="outline" className="flex-1">
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
