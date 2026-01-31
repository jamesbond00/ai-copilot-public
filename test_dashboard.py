#!/usr/bin/env python3
"""
Dashboard testing script for AI Copilot.

This script provides multiple ways to test the Streamlit dashboard:
1. Unit tests for dashboard components
2. Integration tests with mock API server
3. Manual testing with mock server
4. UI automation tests (optional)

Usage:
    python test_dashboard.py [options]

Options:
    --unit          Run unit tests only
    --integration   Run integration tests only
    --mock-server   Start mock API server for manual testing
    --all           Run all tests (default)
    --help          Show this help message
"""

import argparse
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def run_unit_tests():
    """Run unit tests for dashboard components."""
    print("🧪 Running unit tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_dashboard.py", 
            "-v", "--tb=short"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Unit tests failed: {e}")
        return False

def run_integration_tests():
    """Run integration tests with mock API server."""
    print("🔗 Running integration tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_dashboard_integration.py", 
            "-v", "--tb=short"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

def start_mock_server():
    """Start mock API server for manual testing."""
    print("🚀 Starting mock API server...")
    print("📡 Mock API will be available at: http://localhost:8001")
    print("📊 API documentation at: http://localhost:8001/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "tests/mock_api_server.py"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Mock server stopped")
    except Exception as e:
        print(f"❌ Failed to start mock server: {e}")

def run_dashboard_with_mock():
    """Run dashboard with mock server configuration."""
    print("🎨 Starting dashboard with mock server...")
    print("📝 Note: Update API_BASE_URL in dashboard.py to 'http://localhost:8001' for testing")
    print("🌐 Dashboard will be available at: http://localhost:8501")
    
    # Create a temporary dashboard file with mock server URL
    dashboard_path = Path(__file__).parent / "src" / "ui" / "dashboard.py"
    temp_dashboard_path = Path(__file__).parent / "temp_dashboard_mock.py"
    
    try:
        # Read original dashboard
        with open(dashboard_path, 'r') as f:
            content = f.read()
        
        # Replace API URL
        content = content.replace(
            'API_BASE_URL = "http://localhost:8000"',
            'API_BASE_URL = "http://localhost:8001"'
        )
        
        # Write temporary dashboard
        with open(temp_dashboard_path, 'w') as f:
            f.write(content)
        
        print("🚀 Starting Streamlit dashboard...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(temp_dashboard_path)
        ], cwd=Path(__file__).parent)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
    finally:
        # Clean up temporary file
        if temp_dashboard_path.exists():
            temp_dashboard_path.unlink()

def run_all_tests():
    """Run all tests."""
    print("🧪 Running all dashboard tests...\n")
    
    success = True
    
    # Run unit tests
    if not run_unit_tests():
        success = False
        print("❌ Unit tests failed\n")
    else:
        print("✅ Unit tests passed\n")
    
    # Run integration tests
    if not run_integration_tests():
        success = False
        print("❌ Integration tests failed\n")
    else:
        print("✅ Integration tests passed\n")
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1)

def show_testing_guide():
    """Show comprehensive testing guide."""
    guide = """
🤖 AI Copilot Dashboard Testing Guide
=====================================

This guide covers multiple ways to test your Streamlit dashboard.

📋 Testing Options:

1. 🧪 Unit Tests
   - Test individual dashboard components
   - Mock API calls and responses
   - Test error handling
   - Run: python test_dashboard.py --unit

2. 🔗 Integration Tests
   - Test dashboard with mock API server
   - End-to-end API communication
   - Real data flow testing
   - Run: python test_dashboard.py --integration

3. 🚀 Mock Server Testing
   - Start mock API server for manual testing
   - Test dashboard without real backend
   - Run: python test_dashboard.py --mock-server

4. 🎨 Manual Dashboard Testing
   - Start dashboard with mock server
   - Interactive testing in browser
   - Run: python test_dashboard.py --dashboard

5. 🔄 Full Test Suite
   - Run all automated tests
   - Run: python test_dashboard.py --all

📝 Manual Testing Steps:

1. Start mock API server:
   python test_dashboard.py --mock-server

2. In another terminal, start dashboard:
   streamlit run src/ui/dashboard.py

3. Update API_BASE_URL in dashboard.py to:
   API_BASE_URL = "http://localhost:8001"

4. Open browser to http://localhost:8501

5. Test all dashboard features:
   - Health check
   - Daily summary
   - Error analysis
   - Performance analysis
   - Time range selection
   - Analysis type selection

🔧 Troubleshooting:

- If tests fail, check that all dependencies are installed
- Mock server runs on port 8001, dashboard on 8501
- Check console output for error messages
- Ensure no other services are using the same ports

📊 Mock Data Features:

The mock server provides realistic test data:
- Random but realistic analysis results
- Various confidence scores
- Sample insights and recommendations
- Different system health states
- Performance metrics

🎯 Test Coverage:

- API call success/failure scenarios
- Data validation and formatting
- Error handling and edge cases
- UI component interactions
- Time range and analysis type selections
"""
    print(guide)

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test AI Copilot Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_dashboard.py --all          # Run all tests
  python test_dashboard.py --unit         # Run unit tests only
  python test_dashboard.py --mock-server  # Start mock server
  python test_dashboard.py --guide        # Show testing guide
        """
    )
    
    parser.add_argument("--unit", action="store_true", 
                       help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--mock-server", action="store_true", 
                       help="Start mock API server for manual testing")
    parser.add_argument("--dashboard", action="store_true", 
                       help="Start dashboard with mock server")
    parser.add_argument("--all", action="store_true", 
                       help="Run all tests (default)")
    parser.add_argument("--guide", action="store_true", 
                       help="Show comprehensive testing guide")
    
    args = parser.parse_args()
    
    if args.guide:
        show_testing_guide()
    elif args.unit:
        run_unit_tests()
    elif args.integration:
        run_integration_tests()
    elif args.mock_server:
        start_mock_server()
    elif args.dashboard:
        run_dashboard_with_mock()
    elif args.all or not any(vars(args).values()):
        run_all_tests()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
