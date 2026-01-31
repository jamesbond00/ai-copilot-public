# Testing Guide for AI Copilot Dashboard

This guide covers comprehensive testing strategies for the Streamlit dashboard in the AI Copilot project.

## 🚀 Quick Start

### Run All Tests
```bash
python test_dashboard.py --all
```

### Start Mock Server for Manual Testing
```bash
python test_dashboard.py --mock-server
```

### Show Complete Testing Guide
```bash
python test_dashboard.py --guide
```

## 📋 Testing Options

### 1. Unit Tests
Test individual dashboard components with mocked dependencies.

```bash
# Run unit tests
python test_dashboard.py --unit

# Or directly with pytest
pytest tests/test_dashboard.py -v
```

**What's tested:**
- API call functions (`call_api`)
- Data processing and validation
- Error handling scenarios
- Response parsing and formatting

### 2. Integration Tests
Test dashboard with a mock API server for end-to-end validation.

```bash
# Run integration tests
python test_dashboard.py --integration

# Or directly with pytest
pytest tests/test_dashboard_integration.py -v
```

**What's tested:**
- Full API communication flow
- Mock server endpoints
- Data flow from API to dashboard
- Error handling with real HTTP calls

### 3. Mock Server Testing
Start a mock API server for manual testing without backend dependencies.

```bash
# Start mock server
python test_dashboard.py --mock-server

# Server will be available at:
# - API: http://localhost:8001
# - Docs: http://localhost:8001/docs
```

**Features:**
- Realistic test data
- All dashboard endpoints
- Random but consistent responses
- Various system states (healthy/degraded/unhealthy)

### 4. Manual Dashboard Testing
Test the dashboard interactively with the mock server.

```bash
# Start dashboard with mock server
python test_dashboard.py --dashboard

# Dashboard will be available at: http://localhost:8501
```

**Testing checklist:**
- [ ] Health check displays correctly
- [ ] Time range selection works
- [ ] Analysis type selection works
- [ ] All analysis buttons respond
- [ ] Results display properly
- [ ] Error handling works
- [ ] UI is responsive

### 5. UI Automation Tests (Optional)
Automated browser testing using Selenium.

```bash
# Install UI testing dependencies
pip install -r requirements-test.txt

# Run UI tests
pytest tests/test_dashboard_ui.py -v
```

**What's tested:**
- Page loading and rendering
- Button interactions
- Form submissions
- Responsive design
- Error states

## 🛠️ Setup and Dependencies

### Install Testing Dependencies
```bash
# Core testing
pip install pytest pytest-cov pytest-mock

# UI automation (optional)
pip install selenium webdriver-manager

# All testing dependencies
pip install -r requirements-test.txt
```

### Environment Setup
```bash
# Set up environment variables (optional)
export OPENAI_API_KEY="your-key-here"  # For real API testing
export MONITORING_SYSTEM="elk"         # System type
```

## 📊 Mock Data Features

The mock server provides realistic test data:

### Health Endpoint (`/health`)
- Random system status (healthy/degraded/unhealthy)
- Connection status indicators
- Timestamps

### Analysis Endpoints
- **Daily Summary** (`/summary/daily`): System overview with insights
- **Error Analysis** (`/analysis/errors`): Error patterns and recommendations
- **Performance Analysis** (`/analysis/performance`): Performance metrics and suggestions

### Sample Data
- Realistic confidence scores (0.6-0.95)
- Varied log counts (100-10,000)
- Multiple insights and recommendations
- Different system states

## 🔧 Troubleshooting

### Common Issues

**Tests fail to start:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

**Mock server won't start:**
```bash
# Check if port 8001 is available
lsof -i :8001

# Kill process if needed
kill -9 $(lsof -t -i:8001)
```

**Dashboard won't load:**
```bash
# Check if port 8501 is available
lsof -i :8501

# Update API_BASE_URL in dashboard.py
# Change from: API_BASE_URL = "http://localhost:8000"
# To: API_BASE_URL = "http://localhost:8001"
```

**UI tests fail:**
```bash
# Install Chrome/Firefox WebDriver
pip install webdriver-manager

# For headless testing on Linux
sudo apt-get install xvfb
pip install pyvirtualdisplay
```

### Debug Mode

**Run tests with verbose output:**
```bash
pytest tests/ -v -s --tb=long
```

**Run specific test:**
```bash
pytest tests/test_dashboard.py::TestDashboardAPI::test_call_api_success -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=src/ui/dashboard --cov-report=html
```

## 📈 Test Coverage

Current test coverage includes:

- ✅ API call functions
- ✅ Error handling
- ✅ Data validation
- ✅ Integration flows
- ✅ Mock server endpoints
- ✅ UI component rendering
- ✅ Responsive design
- ⚠️ Streamlit-specific components (limited)
- ⚠️ Real-time updates (manual testing)

## 🎯 Best Practices

### Writing Tests
1. **Use descriptive test names** that explain what's being tested
2. **Mock external dependencies** to ensure tests are isolated
3. **Test both success and failure scenarios**
4. **Use realistic test data** that matches production patterns
5. **Keep tests fast** by avoiding unnecessary delays

### Manual Testing
1. **Test all user workflows** from start to finish
2. **Verify error handling** with invalid inputs
3. **Check responsive design** on different screen sizes
4. **Test with different data scenarios** (empty, large, malformed)
5. **Document any issues** found during testing

### Continuous Integration
1. **Run tests automatically** on code changes
2. **Include both unit and integration tests**
3. **Monitor test coverage** and maintain high coverage
4. **Use consistent test environments** across development and CI

## 📝 Test Data Management

### Mock Data Customization
Edit `tests/mock_api_server.py` to customize:
- Sample insights and recommendations
- Error scenarios
- Performance metrics
- System health states

### Adding New Tests
1. **Unit tests**: Add to `tests/test_dashboard.py`
2. **Integration tests**: Add to `tests/test_dashboard_integration.py`
3. **UI tests**: Add to `tests/test_dashboard_ui.py`
4. **Mock endpoints**: Add to `tests/mock_api_server.py`

## 🚀 Advanced Testing

### Performance Testing
```bash
# Test API response times
python -c "
import requests
import time
start = time.time()
response = requests.get('http://localhost:8001/health')
print(f'Response time: {time.time() - start:.2f}s')
"
```

### Load Testing
```bash
# Install locust for load testing
pip install locust

# Create load test script
# Run: locust -f load_test.py --host=http://localhost:8001
```

### Security Testing
- Test API endpoints for common vulnerabilities
- Validate input sanitization
- Check for information disclosure
- Test authentication/authorization (if implemented)

## 📞 Support

If you encounter issues with testing:

1. **Check the logs** for error messages
2. **Verify dependencies** are installed correctly
3. **Test with mock server** first before real backend
4. **Check port availability** for services
5. **Review test configuration** and environment setup

For additional help, refer to:
- [Streamlit Testing Documentation](https://docs.streamlit.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
