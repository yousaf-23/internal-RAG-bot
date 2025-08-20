"""
Test script to verify configuration is working after fixes
"""

import os
import sys

print("="*60)
print("Testing Configuration After Fixes")
print("="*60)

# Step 1: Check environment variables directly
print("\n1. Checking raw environment variables:")
test_vars = ['ALLOWED_EXTENSIONS', 'DATABASE_URL', 'APP_NAME', 'DEBUG_MODE']
for var in test_vars:
    value = os.getenv(var)
    if value:
        if 'PASSWORD' in var or 'KEY' in var:
            print(f"   {var}: ***HIDDEN***")
        else:
            print(f"   {var}: {value}")
    else:
        print(f"   {var}: NOT SET")

# Step 2: Test importing settings
print("\n2. Testing settings import:")
try:
    from app.config import settings
    print("   ✅ Settings imported successfully")
    
    # Check key attributes
    print(f"   - App Name: {settings.app_name}")
    print(f"   - Debug Mode: {settings.debug_mode}")
    print(f"   - Database URL exists: {bool(hasattr(settings, 'database_url'))}")
    
    # Test allowed_extensions specifically
    if hasattr(settings, 'allowed_extensions'):
        print(f"   - Allowed Extensions: {settings.allowed_extensions}")
    else:
        print("   - Allowed Extensions: NOT FOUND")
    
    if hasattr(settings, 'allowed_extensions_str'):
        print(f"   - Allowed Extensions String: {settings.allowed_extensions_str}")
    
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    print("\n   Full error:")
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)