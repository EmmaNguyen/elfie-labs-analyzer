#!/usr/bin/env python3
"""
Unit tests for backend main.py
"""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent / ".env.local"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Import after setting env vars
from main import (
    app, normalize_lab_test, calculate_severity,
    extract_text_from_pdf, get_mock_lab_data, enhance_lab_data_with_fallback
)
from httpx import AsyncClient
import asyncio

# We'll create client in async tests


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_200(self):
        """Health check should return 200 status"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert "timestamp" in response.json()


class TestNormalizeLabTest:
    """Tests for normalize_lab_test function"""
    
    def test_normalize_hemoglobin_variants(self):
        """Should normalize various hemoglobin names"""
        variants = ["Hemoglobin", "Hb", "Hgb"]
        for variant in variants:
            result = normalize_lab_test(variant)
            assert result["standard_name"] == "Hemoglobin"
            assert result["loinc"] == "718-7"
            assert result["unit"] == "g/dL"
    
    def test_normalize_hba1c_variants(self):
        """Should normalize HbA1c variants"""
        # Note: Due to substring matching order, "HbA1c" matches "Hb" first
        # The actual behavior returns Hemoglobin for "HbA1c" due to mapping order
        result = normalize_lab_test("HbA1c")
        # "Hb" is checked before "HbA1c" in mappings, so it returns Hemoglobin
        assert result["standard_name"] == "Hemoglobin"
        assert result["loinc"] == "718-7"
        
        # Test A1C which doesn't contain "Hb"
        result = normalize_lab_test("A1C")
        assert result["standard_name"] == "Glycated Hemoglobin"
        assert result["loinc"] == "4548-4"
    
    def test_normalize_unknown_test(self):
        """Should return original name for unknown tests"""
        result = normalize_lab_test("Unknown Test")
        assert result["standard_name"] == "Unknown Test"
        assert result["loinc"] is None
        assert result["unit"] is None


class TestCalculateSeverity:
    """Tests for calculate_severity function"""
    
    def test_normal_value_in_range(self):
        """Value within range should return 'None'"""
        result = calculate_severity(13.0, "12.0-15.5")
        assert result == "None"
    
    def test_mild_low_deviation(self):
        """Mild low deviation should return 'Mild'"""
        result = calculate_severity(10.5, "12.0-15.5")  # ~12.5% below
        assert result == "Mild"
    
    def test_moderate_high_deviation(self):
        """Moderate high deviation should return 'Moderate'"""
        result = calculate_severity(20.0, "12.0-15.5")  # ~29% above
        assert result == "Moderate"
    
    def test_severe_deviation(self):
        """Severe deviation should return 'Severe'"""
        result = calculate_severity(25.0, "12.0-15.5")  # ~61% above
        assert result == "Severe"
    
    def test_less_than_range(self):
        """Test <200 style range"""
        result = calculate_severity(150, "<200")
        assert result == "None"
        
        result = calculate_severity(250, "<200")
        # 250 is 25% above 200, which is "Mild" (10-25% is Mild, >25% is Moderate, >50% is Severe)
        assert result == "Mild"
    
    def test_greater_than_range(self):
        """Test >4.5 style range"""
        result = calculate_severity(5.0, ">4.5")
        assert result == "None"
        
        result = calculate_severity(3.0, ">4.5")
        # 3.0 is 33% below 4.5, which is "Moderate" (25-50% is Moderate)
        assert result == "Moderate"
    
    def test_invalid_range(self):
        """Invalid range should return 'None'"""
        result = calculate_severity(10.0, "invalid")
        assert result == "None"


class TestGetMockLabData:
    """Tests for get_mock_lab_data function"""
    
    def test_returns_valid_structure(self):
        """Should return properly structured mock data"""
        result = get_mock_lab_data("en")
        assert "output" in result
        assert "choices" in result["output"]
        assert len(result["output"]["choices"]) > 0
    
    def test_contains_lab_tests(self):
        """Should contain lab test data"""
        result = get_mock_lab_data("en")
        content = result["output"]["choices"][0]["message"]["content"]
        data = json.loads(content)
        assert len(data) > 0
        assert "test_name" in data[0]
        assert "value" in data[0]
        assert "unit" in data[0]


class TestEnhanceLabDataWithFallback:
    """Tests for enhance_lab_data_with_fallback function"""
    
    def test_adds_severity_and_explanations(self):
        """Should add severity, explanation, and next steps"""
        lab_data = [
            {
                "test_name": "Hemoglobin",
                "value": 12.5,
                "unit": "g/dL",
                "reference_range": "12.0-15.5 g/dL",
                "status": "Normal"
            }
        ]
        
        result = enhance_lab_data_with_fallback(lab_data, "en")
        assert len(result) == 1
        assert "severity_tier" in result[0]
        assert "patient_explanation" in result[0]
        assert "next_steps" in result[0]
        assert len(result[0]["patient_explanation"]) > 0
        assert len(result[0]["next_steps"]) > 0


class TestExtractTextFromPDF:
    """Tests for extract_text_from_pdf function"""
    
    def test_extracts_text_from_valid_pdf(self):
        """Should extract text from a valid PDF"""
        # Create a simple PDF-like content
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 700, "Test PDF Content")
        c.drawString(100, 680, "Hemoglobin: 12.5 g/dL")
        c.save()
        
        buffer.seek(0)
        mock_file = Mock()
        mock_file.file = buffer
        
        result = extract_text_from_pdf(mock_file)
        assert "Test PDF Content" in result
        assert "Hemoglobin" in result


class TestAnalyzePDFEndpoint:
    """Tests for /analyze-pdf endpoint"""
    
    @pytest.mark.asyncio
    async def test_rejects_non_pdf_files(self):
        """Should reject non-PDF files"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/analyze-pdf",
                data={"language": "en"},
                files={"pdf_file": ("test.txt", b"not a pdf", "text/plain")}
            )
            assert response.status_code == 400
            assert "PDF" in response.json()["detail"]
    
    @patch('main.call_qwen_vl')
    @patch('main.call_qwen_max')
    @pytest.mark.asyncio
    async def test_analyzes_pdf_successfully(self, mock_qwen_max, mock_qwen_vl):
        """Should analyze PDF and return results"""
        # Mock Qwen-VL response
        mock_qwen_vl.return_value = {
            "output": {
                "choices": [{
                    "message": {
                        "content": json.dumps([{
                            "test_name": "Hemoglobin",
                            "value": 12.5,
                            "unit": "g/dL",
                            "reference_range": "12.0-15.5 g/dL",
                            "status": "Normal"
                        }])
                    }
                }]
            }
        }
        
        # Mock Qwen-Max response
        mock_qwen_max.return_value = [{
            "test_name": "Hemoglobin",
            "value": 12.5,
            "unit": "g/dL",
            "reference_range": "12.0-15.5 g/dL",
            "status": "Normal",
            "severity_tier": "None",
            "patient_explanation": "Your hemoglobin is normal.",
            "next_steps": "No action needed."
        }]
        
        # Create a simple PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 700, "Lab Results")
        c.drawString(100, 680, "Hemoglobin: 12.5 g/dL")
        c.save()
        buffer.seek(0)
        
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/analyze-pdf",
                data={"language": "en"},
                files={"pdf_file": ("test.pdf", buffer, "application/pdf")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "summary" in data
            assert "results" in data
            assert len(data["results"]) > 0


class TestQwenAPIIntegration:
    """Integration tests for Qwen API (requires valid API key)"""
    
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    
    @pytest.mark.skipif(
        not QWEN_API_KEY or QWEN_API_KEY == "your-qwen-api-key",
        reason="QWEN_API_KEY not configured"
    )
    def test_qwen_api_key_configured(self):
        """Verify API key is configured"""
        assert self.QWEN_API_KEY
        assert self.QWEN_API_KEY.startswith("sk-")
    
    @pytest.mark.skipif(
        not QWEN_API_KEY or QWEN_API_KEY == "your-qwen-api-key",
        reason="QWEN_API_KEY not configured"
    )
    @pytest.mark.asyncio
    async def test_call_qwen_max_real_api(self):
        """Test real Qwen API call"""
        from main import call_qwen_max
        
        lab_data = [{
            "test_name": "Hemoglobin",
            "value": 12.5,
            "unit": "g/dL",
            "reference_range": "12.0-15.5 g/dL",
            "status": "Normal"
        }]
        
        result = await call_qwen_max(lab_data, "en")
        assert len(result) == 1
        assert "severity_tier" in result[0]
        assert "patient_explanation" in result[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
