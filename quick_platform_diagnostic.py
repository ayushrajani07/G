#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Quick Platform Diagnostic Tool
Author: AI Assistant (Diagnose hanging platform issues)

SOLUTION: Test platform files and identify hanging causes
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def test_platform_file(filename):
    """🧪 Test a platform file for issues."""
    print(f"\n🧪 Testing: {filename}")
    print("-" * 40)
    
    if not Path(filename).exists():
        print("❌ File does not exist")
        return False
    
    try:
        # Test 1: Syntax check
        print("1. Syntax check...", end=" ")
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', filename
        ], capture_output=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ OK")
        else:
            print("❌ SYNTAX ERROR")
            print(f"   Error: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        # Test 2: Import test
        print("2. Import test...", end=" ")
        test_script = f"""
import sys
sys.path.insert(0, '.')
try:
    import {Path(filename).stem}
    print("IMPORT_OK")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
"""
        
        with open('temp_import_test.py', 'w') as f:
            f.write(test_script)
        
        result = subprocess.run([
            sys.executable, 'temp_import_test.py'
        ], capture_output=True, timeout=15)
        
        Path('temp_import_test.py').unlink(missing_ok=True)
        
        output = result.stdout.decode('utf-8', errors='ignore').strip()
        if "IMPORT_OK" in output:
            print("✅ OK")
        else:
            print("❌ IMPORT ERROR") 
            print(f"   Error: {output}")
            return False
        
        # Test 3: Quick run test (with timeout)
        print("3. Quick run test...", end=" ")
        
        def run_with_timeout():
            nonlocal test_result
            try:
                process = subprocess.Popen([
                    sys.executable, filename
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, encoding='utf-8', errors='ignore')
                
                # Read first few lines or timeout
                lines_read = 0
                start_time = time.time()
                
                while lines_read < 5 and (time.time() - start_time) < 10:
                    line = process.stdout.readline()
                    if line:
                        lines_read += 1
                        test_output.append(line.strip())
                    else:
                        break
                
                # Terminate process
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
                test_result = True
                
            except Exception as e:
                test_output.append(f"Run error: {e}")
                test_result = False
        
        test_result = False
        test_output = []
        
        run_thread = threading.Thread(target=run_with_timeout)
        run_thread.daemon = True
        run_thread.start()
        run_thread.join(timeout=15)
        
        if test_result:
            print("✅ OK")
            if test_output:
                print("   First few lines of output:")
                for line in test_output[:3]:
                    print(f"   > {line}")
        else:
            print("❌ HANG OR ERROR")
            if test_output:
                print("   Output before hang:")
                for line in test_output:
                    print(f"   > {line}")
        
        return test_result
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_environment():
    """🌍 Check environment setup."""
    print("\n🌍 ENVIRONMENT CHECK")
    print("=" * 40)
    
    # Python version
    print(f"Python: {sys.version}")
    
    # Environment variables
    env_vars = ['KITE_API_KEY', 'KITE_ACCESS_TOKEN', 'PYTHONIOENCODING', 'PYTHONUTF8']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'TOKEN' in var:
                print(f"{var}: SET ({value[:8]}...)")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: NOT SET")
    
    # Dependencies
    print("\nDependencies:")
    deps = ['kiteconnect', 'rich', 'dotenv']
    for dep in deps:
        try:
            __import__(dep)
            print(f"  {dep}: ✅ Available")
        except ImportError:
            print(f"  {dep}: ❌ Missing")

def main():
    """🚀 Main diagnostic routine."""
    print("🧪 G6.1 PLATFORM DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Environment check
    check_environment()
    
    # Test platform files
    platform_files = [
        'g6_platform_main_v2.py',
        'g6_platform_main_FINAL_WORKING.py', 
        'kite_login_and_launch_FINAL_WORKING.py',
        'enhanced_rich_launcher_fixed.py'
    ]
    
    working_files = []
    
    for filename in platform_files:
        if test_platform_file(filename):
            working_files.append(filename)
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    
    if working_files:
        print("✅ Working platform files:")
        for filename in working_files:
            print(f"  - {filename}")
        
        print(f"\n✅ Recommendation: Use '{working_files[0]}'")
        print("   Or try the non-blocking launcher:")
        print("   python nonblocking_rich_launcher.py")
    else:
        print("❌ No working platform files found")
        print("💡 Recommendations:")
        print("  1. Check for syntax errors in platform files")
        print("  2. Ensure all dependencies are installed")
        print("  3. Try the minimal test platform:")
        print("     python nonblocking_rich_launcher.py")
    
    print("\n🎯 NEXT STEPS:")
    print("  1. Fix any errors shown above")
    print("  2. Use: python nonblocking_rich_launcher.py")
    print("  3. This launcher will create a test platform if needed")

if __name__ == "__main__":
    main()