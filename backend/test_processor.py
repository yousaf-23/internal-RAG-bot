"""
Test Script for Document Processor
===================================
This script tests the document processor with various file types.

Usage: python test_processor.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.document_processor import DocumentProcessor

def main():
    """
    Test document processing with real files.
    """
    print("\n" + "="*70)
    print("📄 COMPREHENSIVE DOCUMENT PROCESSOR TEST")
    print("="*70)
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Check for uploaded files to test with
    upload_dir = Path("uploaded_files")
    
    if upload_dir.exists():
        # Find all files in upload directory
        all_files = list(upload_dir.rglob("*.*"))
        
        if all_files:
            print(f"\nFound {len(all_files)} uploaded file(s) to test:")
            
            for file_path in all_files[:5]:  # Test up to 5 files
                print(f"\n{'='*60}")
                print(f"Testing: {file_path.name}")
                print('='*60)
                
                # Process the file
                result = processor.process_document(str(file_path))
                
                if result['success']:
                    print(f"✅ Success!")
                    print(f"  - Text length: {len(result.get('text', ''))}")
                    print(f"  - Chunks: {len(result.get('chunks', []))}")
                    print(f"  - Metadata: {result.get('metadata', {})}")
                else:
                    print(f"❌ Failed: {result.get('error')}")
        else:
            print("No uploaded files found. Upload some files first!")
    else:
        print("Upload directory doesn't exist yet. Upload some files first!")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()