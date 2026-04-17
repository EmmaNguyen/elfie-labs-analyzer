#!/usr/bin/env python3
"""
Test script for fast single-page PDF extraction using Qwen-VL.
Uses only the first page for quick results (Vercel-compatible).

Usage:
    python test_first_page.py ~/Downloads/DiaGfeb2026.pdf
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from main import call_qwen_vl


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def test_first_page_extraction(pdf_path: str):
    """Test extraction using only first page (fast mode)"""
    
    pdf_file = Path(pdf_path)
    
    print_header("FAST FIRST-PAGE EXTRACTION TEST")
    print(f"File: {pdf_file}")
    print(f"Size: {pdf_file.stat().st_size / 1024:.2f} KB")
    
    # Read PDF
    with open(pdf_file, 'rb') as f:
        pdf_content = f.read()
    
    print(f"\nProcessing first page only (fast mode)...")
    print("This should complete in 5-10 seconds\n")
    
    # Process with first_page_only=True
    start_time = asyncio.get_event_loop().time()
    
    result = await call_qwen_vl(pdf_content, 'en', first_page_only=True)
    
    elapsed = asyncio.get_event_loop().time() - start_time
    
    # Parse results
    content = result['output']['choices'][0]['message']['content']
    lab_data = json.loads(content)
    
    print_header("RESULTS")
    print(f"Processing time: {elapsed:.1f} seconds")
    print(f"Tests extracted: {len(lab_data)}")
    
    if lab_data:
        print(f"\nExtracted tests:")
        for i, test in enumerate(lab_data[:15], 1):
            print(f"  {i}. {test.get('test_name', 'N/A')}: {test.get('value')} {test.get('unit')} ({test.get('status')})")
        
        if len(lab_data) > 15:
            print(f"  ... and {len(lab_data) - 15} more tests")
    else:
        print("  No tests found on first page")
    
    # Save results
    output_file = pdf_file.parent / f"{pdf_file.stem}_first_page.json"
    with open(output_file, 'w') as f:
        json.dump({
            'extraction_mode': 'first_page_only',
            'processing_time_seconds': elapsed,
            'total_tests': len(lab_data),
            'results': lab_data
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return lab_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use test PDF from project directory
        pdf_path = str(Path(__file__).parent.parent / "test_lab_results.pdf")
        print(f"No file specified, using default: {pdf_path}")
    else:
        pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Load API key from environment
    if not os.getenv('QWEN_API_KEY'):
        print("Error: QWEN_API_KEY environment variable not set")
        print("Please set it: export QWEN_API_KEY=your-api-key")
        sys.exit(1)
    
    asyncio.run(test_first_page_extraction(pdf_path))
