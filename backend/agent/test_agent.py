#!/usr/bin/env python3
"""
Test script for Labhya GPU Agent
Verifies that all components are working correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from combined_agent import AgentCore, SystemChecker, GPUMonitor, HTTPClient
        print("✓ combined_agent imports successful")
    except Exception as e:
        print(f"✗ combined_agent import failed: {e}")
        return False
    
    try:
        import launcher
        print("✓ launcher import successful")
    except Exception as e:
        print(f"✗ launcher import failed: {e}")
        return False
    
    return True

def test_system_check():
    """Test system requirements checking"""
    print("\nTesting system requirements...")
    
    try:
        from combined_agent import SystemChecker
        requirements = SystemChecker.check_system_requirements()
        
        print(f"System status: {requirements['message']}")
        for key, value in requirements.items():
            if key != 'message':
                status = "✓" if value else "✗"
                print(f"  {status} {key}")
        
        return requirements['all_ok']
        
    except Exception as e:
        print(f"✗ System check failed: {e}")
        return False

def test_gpu_detection():
    """Test GPU detection"""
    print("\nTesting GPU detection...")
    
    try:
        from combined_agent import GPUMonitor
        gpus = GPUMonitor.get_gpu_info()
        
        if gpus:
            print(f"✓ Detected {len(gpus)} GPU(s):")
            for gpu in gpus:
                print(f"  - {gpu['name']} (Index: {gpu['index']})")
        else:
            print("✗ No GPUs detected")
            
        return len(gpus) > 0
        
    except Exception as e:
        print(f"✗ GPU detection failed: {e}")
        return False

def test_http_client():
    """Test HTTP client initialization"""
    print("\nTesting HTTP client...")
    
    try:
        from combined_agent import HTTPClient
        client = HTTPClient("http://localhost:8000")
        print("✓ HTTP client created successfully")
        return True
        
    except Exception as e:
        print(f"✗ HTTP client test failed: {e}")
        return False

def test_agent_core():
    """Test AgentCore initialization"""
    print("\nTesting AgentCore...")
    
    try:
        from combined_agent import AgentCore
        agent = AgentCore("http://localhost:8000")
        print("✓ AgentCore created successfully")
        return True
        
    except Exception as e:
        print(f"✗ AgentCore test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Labhya GPU Agent - Component Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("System Requirements", test_system_check),
        ("GPU Detection", test_gpu_detection),
        ("HTTP Client", test_http_client),
        ("Agent Core", test_agent_core),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The agent is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
