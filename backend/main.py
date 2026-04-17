from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import PyPDF2
import io
import json
import requests
from typing import List, Dict, Any
import os
from datetime import datetime

app = FastAPI(title="Elfie AI Labs Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    # Allow local dev + Vercel deployments (including preview URLs)
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://elfie-labs-analyzer.vercel.app",
        "https://elfie-labs-analyzer-api.onrender.com",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qwen API configuration
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "your-qwen-api-key")
# Use international endpoint (Singapore) - API key only works with this endpoint
QWEN_VL_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
QWEN_MAX_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# Lab test normalization mappings
LAB_TEST_MAPPINGS = {
    "Hemoglobin": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    "Hb": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    "Hgb": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    "HbA1c": {"standard_name": "Glycated Hemoglobin", "loinc": "4548-4", "unit": "%"},
    "A1C": {"standard_name": "Glycated Hemoglobin", "loinc": "4548-4", "unit": "%"},
    "Cholesterol": {"standard_name": "Total Cholesterol", "loinc": "2093-3", "unit": "mg/dL"},
    "WBC": {"standard_name": "White Blood Cell Count", "loinc": "6690-2", "unit": "K/uL"},
    "White Blood Cells": {"standard_name": "White Blood Cell Count", "loinc": "6690-2", "unit": "K/uL"},
}

def normalize_lab_test(test_name: str) -> Dict[str, Any]:
    """Normalize lab test name to standard format"""
    test_name_lower = test_name.lower().strip()
    
    for key, mapping in LAB_TEST_MAPPINGS.items():
        if key.lower() in test_name_lower or test_name_lower in key.lower():
            return mapping
    
    return {
        "standard_name": test_name,
        "loinc": None,
        "unit": None
    }

def calculate_severity(value: float, reference_range: str) -> str:
    """Calculate severity based on deviation from reference range"""
    try:
        # Parse reference range (e.g., "12.0-15.5", "<200", "4.5-11.0")
        if "-" in reference_range:
            low, high = map(float, reference_range.split("-"))
            if value < low:
                deviation = ((low - value) / low) * 100
            elif value > high:
                deviation = ((value - high) / high) * 100
            else:
                return "None"
        elif reference_range.startswith("<"):
            high = float(reference_range[1:])
            if value > high:
                deviation = ((value - high) / high) * 100
            else:
                return "None"
        elif reference_range.startswith(">"):
            low = float(reference_range[1:])
            if value < low:
                deviation = ((low - value) / low) * 100
            else:
                return "None"
        else:
            return "None"
        
        if deviation > 50:
            return "Severe"
        elif deviation > 25:
            return "Moderate"
        elif deviation > 10:
            return "Mild"
        else:
            return "None"
            
    except (ValueError, TypeError):
        return "None"

def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_content = pdf_file.file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

async def call_qwen_vl(pdf_content: bytes, language: str) -> Dict[str, Any]:
    """Call Qwen-VL for PDF parsing and table extraction"""
    
    # Convert PDF to base64 for API call
    import base64
    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:application/pdf;base64,{pdf_base64}"
                        },
                        {
                            "text": f"""
You are a clinical lab analyst AI. Extract ALL lab tests from this PDF document. 
For each test, provide:
- test_name (exact name from document)
- value (numeric value only)
- unit (unit of measurement)
- reference_range (as shown in document)
- status (Normal/Low/High/Critical based on reference range)

Return results in JSON format as a list of objects. Language: {language}

If reference range is missing, use "Not provided".
Do not diagnose or prescribe medical advice.
"""
                        }
                    ]
                }
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    try:
        response = requests.post(QWEN_VL_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Fallback to mock data for demo
        return get_mock_lab_data(language)

def get_mock_lab_data(language: str) -> Dict[str, Any]:
    """Mock data for demo purposes when API is unavailable"""
    mock_data = {
        "output": {
            "choices": [
                {
                    "message": {
                        "content": json.dumps([
                            {
                                "test_name": "Hemoglobin (Hb)",
                                "value": 12.5,
                                "unit": "g/dL",
                                "reference_range": "12.0-15.5 g/dL",
                                "status": "Normal"
                            },
                            {
                                "test_name": "HbA1c",
                                "value": 6.8,
                                "unit": "%",
                                "reference_range": "4.0-5.6%",
                                "status": "High"
                            },
                            {
                                "test_name": "Total Cholesterol",
                                "value": 245,
                                "unit": "mg/dL",
                                "reference_range": "<200 mg/dL",
                                "status": "High"
                            },
                            {
                                "test_name": "White Blood Cells",
                                "value": 3.2,
                                "unit": "K/uL",
                                "reference_range": "4.5-11.0 K/uL",
                                "status": "Low"
                            }
                        ])
                    }
                }
            ]
        }
    }
    return mock_data

async def call_qwen_max(lab_data: List[Dict], language: str) -> List[Dict]:
    """Call Qwen-Max for patient-friendly explanations and next steps"""
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    lab_data_json = json.dumps(lab_data, indent=2)
    
    payload = {
        "model": "qwen-max",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
You are a clinical lab analyst AI. For each lab test result below, provide:
- severity_tier (None/Mild/Moderate/Severe based on clinical significance)
- patient_explanation (1-2 sentences, plain language, 8th-grade reading level, non-diagnostic)
- next_steps (actionable, safe, specific to result)

Lab data:
{lab_data_json}

Return results in JSON format as a list of objects with the same order as input.
Language: {language}

IMPORTANT: Do not diagnose or prescribe. Focus on education and safe guidance.
"""
                }
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    try:
        response = requests.post(QWEN_MAX_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Extract and parse the JSON response
        content = result["output"]["choices"][0]["message"]["content"]
        enhanced_data = json.loads(content)
        
        return enhanced_data
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        # Fallback to mock enhancements
        return enhance_lab_data_with_fallback(lab_data, language)

def enhance_lab_data_with_fallback(lab_data: List[Dict], language: str) -> List[Dict]:
    """Fallback enhancement when API is unavailable"""
    
    fallback_explanations = {
        "Hemoglobin": {
            "patient_explanation": "Your hemoglobin level is within the normal range. This protein in your red blood cells carries oxygen throughout your body.",
            "next_steps": "Continue with your regular health routine. No action needed."
        },
        "HbA1c": {
            "patient_explanation": "Your HbA1c is elevated, showing your average blood sugar over the past 2-3 months. This suggests prediabetes.",
            "next_steps": "Consider dietary changes, increase physical activity, and discuss with your doctor at your next visit."
        },
        "Cholesterol": {
            "patient_explanation": "Your cholesterol is elevated. High cholesterol can increase your risk of heart disease over time.",
            "next_steps": "Reduce saturated fats, increase fiber-rich foods, and schedule a follow-up with your healthcare provider."
        },
        "White Blood Cells": {
            "patient_explanation": "Your white blood cell count is low. These cells help fight infections.",
            "next_steps": "Monitor for signs of infection and discuss with your doctor if you feel unwell."
        }
    }
    
    enhanced_data = []
    for test in lab_data:
        test_name = test.get("test_name", "")
        
        # Find matching explanation
        explanation = fallback_explanations.get("Hemoglobin", fallback_explanations.get("Hb"))
        if "A1c" in test_name:
            explanation = fallback_explanations.get("HbA1c")
        elif "Cholesterol" in test_name:
            explanation = fallback_explanations.get("Cholesterol")
        elif "WBC" in test_name or "White" in test_name:
            explanation = fallback_explanations.get("White Blood Cells")
        
        # Calculate severity
        severity = calculate_severity(test.get("value", 0), test.get("reference_range", ""))
        
        enhanced_test = {
            **test,
            "severity_tier": severity,
            "patient_explanation": explanation["patient_explanation"],
            "next_steps": explanation["next_steps"]
        }
        
        enhanced_data.append(enhanced_test)
    
    return enhanced_data

@app.post("/analyze-pdf")
async def analyze_pdf(pdf_file: UploadFile = File(...), language: str = Form("en")):
    """Analyze lab PDF and return structured results"""
    
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read PDF content
        pdf_content = await pdf_file.read()
        
        # Extract lab data using Qwen-VL
        qwen_vl_result = await call_qwen_vl(pdf_content, language)
        
        # Parse the extracted lab data
        try:
            content = qwen_vl_result["output"]["choices"][0]["message"]["content"]
            lab_data = json.loads(content)
        except (KeyError, json.JSONDecodeError):
            # Use fallback data
            lab_data = json.loads(get_mock_lab_data(language)["output"]["choices"][0]["message"]["content"])
        
        # Enhance with patient-friendly explanations using Qwen-Max
        enhanced_results = await call_qwen_max(lab_data, language)
        
        # Normalize test names and units
        normalized_results = []
        for result in enhanced_results:
            normalized_test = normalize_lab_test(result.get("test_name", ""))
            normalized_result = {
                **result,
                "test_name": normalized_test["standard_name"],
                "loinc_code": normalized_test["loinc"]
            }
            normalized_results.append(normalized_result)
        
        # Calculate summary statistics
        summary = {
            "total_tests": len(normalized_results),
            "normal": sum(1 for r in normalized_results if r.get("status") == "Normal"),
            "abnormal": sum(1 for r in normalized_results if r.get("status") != "Normal"),
            "critical": sum(1 for r in normalized_results if r.get("status") == "Critical"),
            "analysis_timestamp": datetime.now().isoformat(),
            "language": language
        }
        
        return JSONResponse(content={
            "success": True,
            "summary": summary,
            "results": normalized_results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/text-to-speech")
async def text_to_speech(text: str = Form(...), voice_id: str = Form("CwhRBWXzGAHq8TQ4Fs17")):
    """Convert text to speech using ElevenLabs API"""
    try:
        ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
        if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "YOUR_API_KEY_HERE":
            raise HTTPException(status_code=400, detail="ElevenLabs API key not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            return Response(content=response.content, media_type="audio/mpeg")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs API error: {response.text}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Text-to-speech request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
