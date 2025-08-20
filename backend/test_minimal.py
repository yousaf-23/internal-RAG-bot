"""
Minimal test to verify basic setup works.
"""

print("Testing minimal FastAPI setup...")

# Test 1: Basic imports
try:
    from fastapi import FastAPI
    print("✅ FastAPI imported")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

# Test 2: Create minimal app
try:
    app = FastAPI(title="Test App")
    
    @app.get("/")
    def root():
        return {"status": "working"}
    
    print("✅ Minimal FastAPI app created")
    
    # Test 3: Run the app
    import uvicorn
    print("✅ Starting server on http://localhost:8001")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
    
except Exception as e:
    print(f"❌ Error: {e}")