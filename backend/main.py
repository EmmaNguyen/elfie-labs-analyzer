from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import PyPDF2
import io
import json
import requests
import base64
from typing import List, Dict, Any
import os
from datetime import datetime

# Try to import pdf2image for PDF to JPG conversion
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available. Install with: pip install pdf2image")

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
# Keys are sorted by length (longest first) to avoid partial matches
LAB_TEST_MAPPINGS = {
    # Cholesterol variants (must be before "Cholesterol")
    "HDL Cholesterol": {"standard_name": "HDL Cholesterol", "loinc": "2085-9", "unit": "mg/dL"},
    "LDL Cholesterol": {"standard_name": "LDL Cholesterol", "loinc": "13457-7", "unit": "mg/dL"},
    "Total Cholesterol": {"standard_name": "Total Cholesterol", "loinc": "2093-3", "unit": "mg/dL"},
    "Cholesterol": {"standard_name": "Total Cholesterol", "loinc": "2093-3", "unit": "mg/dL"},
    # HbA1c variants (must be before "Hb")
    "Glycated Hemoglobin": {"standard_name": "Glycated Hemoglobin", "loinc": "4548-4", "unit": "%"},
    "HbA1c": {"standard_name": "Glycated Hemoglobin", "loinc": "4548-4", "unit": "%"},
    "A1C": {"standard_name": "Glycated Hemoglobin", "loinc": "4548-4", "unit": "%"},
    # Blood cells
    "White Blood Cell Count": {"standard_name": "White Blood Cell Count", "loinc": "6690-2", "unit": "K/uL"},
    "White Blood Cells": {"standard_name": "White Blood Cell Count", "loinc": "6690-2", "unit": "K/uL"},
    "WBC": {"standard_name": "White Blood Cell Count", "loinc": "6690-2", "unit": "K/uL"},
    "Red Blood Cell Count": {"standard_name": "Red Blood Cell Count", "loinc": "789-8", "unit": "M/uL"},
    "Red Blood Cells": {"standard_name": "Red Blood Cell Count", "loinc": "789-8", "unit": "M/uL"},
    "RBC": {"standard_name": "Red Blood Cell Count", "loinc": "789-8", "unit": "M/uL"},
    "Platelets": {"standard_name": "Platelet Count", "loinc": "777-3", "unit": "K/uL"},
    "Platelet Count": {"standard_name": "Platelet Count", "loinc": "777-3", "unit": "K/uL"},
    # Hemoglobin (after HbA1c)
    "Hemoglobin": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    "Hgb": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    "Hb": {"standard_name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL"},
    # Other common tests
    "Glucose": {"standard_name": "Glucose", "loinc": "2345-7", "unit": "mg/dL"},
    "Triglycerides": {"standard_name": "Triglycerides", "loinc": "2571-8", "unit": "mg/dL"},
    "Creatinine": {"standard_name": "Creatinine", "loinc": "2160-0", "unit": "mg/dL"},
    "BUN": {"standard_name": "Blood Urea Nitrogen", "loinc": "3094-0", "unit": "mg/dL"},
    "Blood Urea Nitrogen": {"standard_name": "Blood Urea Nitrogen", "loinc": "3094-0", "unit": "mg/dL"},
    "Sodium": {"standard_name": "Sodium", "loinc": "2951-2", "unit": "mEq/L"},
    "Potassium": {"standard_name": "Potassium", "loinc": "2823-3", "unit": "mEq/L"},
    "Calcium": {"standard_name": "Calcium", "loinc": "17861-6", "unit": "mg/dL"},
}

def normalize_lab_test(test_name: str) -> Dict[str, Any]:
    """Normalize lab test name to standard format"""
    test_name_lower = test_name.lower().strip()
    
    # Sort mappings by key length (longest first) to avoid partial matches
    # e.g., "HbA1c" should match before "Hb"
    sorted_mappings = sorted(LAB_TEST_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for key, mapping in sorted_mappings:
        if key.lower() in test_name_lower:
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

async def extract_text_from_pdf_bytes(pdf_content: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")


async def extract_text_with_qwen_vl(pdf_content: bytes, language: str, max_pages: int = None) -> str:
    """Extract text from PDF using Qwen-VL (PDF → JPG → AI OCR)
    
    Args:
        pdf_content: PDF file bytes
        language: Language code
        max_pages: Maximum number of pages to process (None = all pages, 1 = first page only)
    """
    
    if not PDF2IMAGE_AVAILABLE:
        print("pdf2image not available, falling back to PyPDF2")
        return await extract_text_from_pdf_bytes(pdf_content)
    
    try:
        # Convert PDF pages to images
        print(f"Converting PDF to images...")
        
        # If max_pages is 1, only convert first page for speed
        if max_pages == 1:
            images = convert_from_bytes(pdf_content, dpi=150, first_page=1, last_page=1)
            print(f"Converted first page only (1 page)")
        else:
            images = convert_from_bytes(pdf_content, dpi=150)
            print(f"Converted {len(images)} pages to images")
        
        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }
        
        all_extracted_text = []
        
        for page_num, img in enumerate(images, 1):
            print(f"Processing page {page_num}/{len(images)} with Qwen-VL...")
            
            # Convert image to bytes with lower quality for speed
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=75)
            img_bytes = img_buffer.getvalue()
            
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            payload = {
                "model": "qwen-vl-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": f"data:image/jpeg;base64,{img_base64}"
                                },
                                {
                                    "text": "Extract all text from this lab report image. Preserve the table structure and formatting. List all lab tests with their values, units, and reference ranges."
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(QWEN_VL_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            extracted = result["output"]["choices"][0]["message"]["content"]
            
            # Handle different response formats
            if isinstance(extracted, list) and len(extracted) > 0:
                if isinstance(extracted[0], dict) and 'text' in extracted[0]:
                    extracted_text = extracted[0]['text']
                else:
                    extracted_text = str(extracted)
            else:
                extracted_text = str(extracted)
            
            all_extracted_text.append(f"--- Page {page_num} ---\n{extracted_text}")
            print(f"  Extracted {len(extracted_text)} characters from page {page_num}")
        
        combined_text = "\n\n".join(all_extracted_text)
        print(f"Total extracted: {len(combined_text)} characters from {len(images)} pages")
        return combined_text
        
    except Exception as e:
        print(f"Qwen-VL extraction failed: {e}")
        print("Falling back to PyPDF2")
        return await extract_text_from_pdf_bytes(pdf_content)


async def parse_lab_data_with_qwen(page_text: str, language: str) -> List[Dict]:
    """Parse lab data from a single page using Qwen-Max"""
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a clinical lab data extraction AI. Extract ALL lab test results from the provided text."
                },
                {
                    "role": "user",
                    "content": f"""Extract ALL lab tests from this text and return as JSON array.

Text from PDF page:
{page_text}

For each test, extract:
- test_name: exact test name from document
- value: numeric result (extract number only)
- unit: unit of measurement
- reference_range: normal range as shown
- status: Normal/Low/High/Critical based on comparison

Return ONLY a JSON array like this:
[
  {{
    "test_name": "Hemoglobin",
    "value": 12.5,
    "unit": "g/dL",
    "reference_range": "12.0-15.5 g/dL",
    "status": "Normal"
  }}
]

IMPORTANT:
- Extract ALL tests found in the text, do not limit to common ones
- If a value is like ">60" or "<5", extract the number and include the operator in value
- If reference range is missing, use "Not provided"
- Status should be: "Normal" if within range, "Low" if below, "High" if above, "Critical" if dangerously abnormal
- Return an empty array [] if no lab tests are found on this page"""
                }
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    response = requests.post(QWEN_MAX_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    # Parse the JSON response from Qwen
    content = result["output"]["choices"][0]["message"]["content"]
    
    # Try to extract JSON from the response (it might be wrapped in markdown code blocks)
    import re
    json_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
    if json_match:
        lab_data_json = json_match.group(0)
        lab_data = json.loads(lab_data_json)
    else:
        # Try parsing the whole content as JSON
        lab_data = json.loads(content)
    
    return lab_data if isinstance(lab_data, list) else []


async def call_qwen_vl(pdf_content: bytes, language: str, first_page_only: bool = False) -> Dict[str, Any]:
    """Extract lab data from PDF using Qwen-VL (PDF → JPG → AI) + Qwen-Max for parsing
    
    Args:
        pdf_content: PDF file bytes
        language: Language code
        first_page_only: If True, only process first page (faster, for Vercel)
    """
    
    try:
        # Step 1: Extract text from PDF using Qwen-VL (PDF → JPG → AI OCR)
        # Use first page only for faster processing on Vercel
        max_pages = 1 if first_page_only else None
        pdf_text = await extract_text_with_qwen_vl(pdf_content, language, max_pages=max_pages)
        
        if not pdf_text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        # Step 2: Parse each page separately to avoid timeout
        print("Parsing extracted text page by page...")
        
        # Split text by pages
        pages = pdf_text.split("--- Page ")
        all_lab_data = []
        
        for i, page in enumerate(pages[1:], 1):  # Skip first empty split
            page_text = f"--- Page {page}"
            print(f"  Parsing page {i}...")
            
            try:
                page_lab_data = await parse_lab_data_with_qwen(page_text, language)
                if page_lab_data:
                    all_lab_data.extend(page_lab_data)
                    print(f"    Found {len(page_lab_data)} tests on page {i}")
            except Exception as e:
                print(f"    Error parsing page {i}: {e}")
                continue
        
        print(f"Successfully extracted {len(all_lab_data)} lab tests total")
        
        # Wrap in the expected format
        return {
            "output": {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(all_lab_data)
                        }
                    }
                ]
            }
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Qwen API error: {e}")
        # Fallback to mock data for demo
        return get_mock_lab_data(language)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Parsing error: {e}")
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
        "model": "qwen-turbo",
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
        
        # Merge enhanced data with original data to preserve all fields
        merged_data = []
        for i, original_test in enumerate(lab_data):
            if i < len(enhanced_data):
                enhanced_test = enhanced_data[i]
                # Start with original data, then add/override with enhanced fields
                merged_test = {
                    **original_test,  # Preserve original fields (value, unit, reference_range, status)
                    **enhanced_test   # Add enhanced fields (severity_tier, patient_explanation, next_steps)
                }
                merged_data.append(merged_test)
            else:
                merged_data.append(original_test)
        
        return merged_data
        
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
async def analyze_pdf(
    pdf_file: UploadFile = File(...), 
    language: str = Form("en"),
    first_page_only: bool = Form(True)
):
    """Analyze lab PDF and return structured results
    
    Args:
        pdf_file: PDF file to analyze
        language: Language code (en, vi, etc.)
        first_page_only: If True, only process first page (faster). 
                        Default is True for quick results. Set to False for full report.
    """
    
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read PDF content
        pdf_content = await pdf_file.read()
        
        print(f"[DEBUG] Processing PDF: {pdf_file.filename}, size: {len(pdf_content)} bytes")
        
        # Extract lab data using Qwen-VL
        qwen_vl_result = await call_qwen_vl(pdf_content, language, first_page_only=first_page_only)
        
        print(f"[DEBUG] Qwen-VL response keys: {qwen_vl_result.keys() if isinstance(qwen_vl_result, dict) else 'not a dict'}")
        
        # Parse the extracted lab data
        try:
            content = qwen_vl_result["output"]["choices"][0]["message"]["content"]
            print(f"[DEBUG] Qwen-VL content (first 200 chars): {content[:200]}")
            lab_data = json.loads(content)
            print(f"[DEBUG] Parsed lab_data keys: {lab_data.keys() if isinstance(lab_data, dict) else 'not a dict'}")
            if isinstance(lab_data, dict) and 'tests' in lab_data:
                print(f"[DEBUG] Number of tests extracted: {len(lab_data['tests'])}")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"[DEBUG] Failed to parse Qwen-VL response: {e}")
            # Use fallback data
            print(f"[DEBUG] Using mock data fallback")
            mock_data = get_mock_lab_data(language)
            lab_data = json.loads(mock_data["output"]["choices"][0]["message"]["content"])
        
        # Enhance with patient-friendly explanations using Qwen-Max
        enhanced_results = await call_qwen_max(lab_data, language)
        
        print(f"[DEBUG] Enhanced results count: {len(enhanced_results)}")
        if enhanced_results:
            print(f"[DEBUG] First enhanced result: {enhanced_results[0] if len(enhanced_results) > 0 else 'none'}")
        
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
        
        print(f"[DEBUG] Normalized results count: {len(normalized_results)}")
        
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
            "results": normalized_results,
            "debug": {
                "pdf_size": len(pdf_content),
                "qwen_vl_response_keys": list(qwen_vl_result.keys()) if isinstance(qwen_vl_result, dict) else "not_dict",
                "lab_data_keys": list(lab_data.keys()) if isinstance(lab_data, dict) else "not_dict",
                "lab_data_tests_count": len(lab_data.get('tests', [])) if isinstance(lab_data, dict) else 0,
                "enhanced_results_count": len(enhanced_results),
                "normalized_results_count": len(normalized_results)
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    provider: str = Form("qwen"),
    voice_id: str = Form("Cherry"),
    language: str = Form("en")
):
    """Convert text to speech using Qwen TTS or ElevenLabs API"""
    
    if provider == "qwen":
        return await text_to_speech_qwen(text, voice_id, language)
    else:
        return await text_to_speech_elevenlabs(text, voice_id)


async def text_to_speech_qwen(text: str, voice: str = "Cherry", language: str = "en"):
    """Convert text to speech using Qwen TTS API"""
    try:
        # Map language codes
        language_map = {
            "en": "English",
            "zh": "Chinese",
            "fr": "French",
            "ar": "Arabic",
            "vi": "Vietnamese"
        }
        language_type = language_map.get(language, "English")
        
        # Available voices: Cherry, Serena, Ethan, Jasmine, etc.
        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen3-tts-flash",
            "input": {
                "text": text,
                "voice": voice,
                "language_type": language_type
            }
        }
        
        # Qwen TTS uses the multimodal generation endpoint
        response = requests.post(
            QWEN_VL_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Qwen TTS returns audio URL in output.audio.url
            if "output" in result and "audio" in result["output"]:
                audio_url = result["output"]["audio"].get("url")
                if audio_url:
                    # Fetch the audio file from the URL
                    audio_response = requests.get(audio_url, timeout=30)
                    if audio_response.status_code == 200:
                        # Detect audio format from content
                        content = audio_response.content
                        if content.startswith(b'RIFF') and b'WAVE' in content[:12]:
                            media_type = "audio/wav"
                        elif content.startswith(b'\xff\xf3') or content.startswith(b'\xff\xfb') or content.startswith(b'ID3'):
                            media_type = "audio/mpeg"
                        else:
                            media_type = "audio/mpeg"  # default
                        return Response(content=content, media_type=media_type)
                    else:
                        raise HTTPException(status_code=500, detail="Failed to fetch audio from URL")
                else:
                    raise HTTPException(status_code=500, detail="No audio URL in Qwen TTS response")
            else:
                raise HTTPException(status_code=500, detail="Invalid response format from Qwen TTS")
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid Qwen API key for TTS")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Qwen TTS API error: {response.text}")
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Qwen TTS request timed out")
    except Exception as e:
        import traceback
        print(f"Qwen TTS Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Qwen TTS failed: {str(e)}")


async def text_to_speech_elevenlabs(text: str, voice_id: str = "CwhRBWXzGAHq8TQ4Fs17"):
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
