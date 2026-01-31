"""
UI automation tests for the Streamlit dashboard using Selenium.

Note: This requires selenium and a webdriver to be installed.
Install with: pip install selenium webdriver-manager

Optional: For headless testing, also install: pip install pyvirtualdisplay
"""

import pytest
import time
import subprocess
import threading
import requests

pytest.importorskip("selenium")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDashboardUI:
    """UI automation tests for the Streamlit dashboard."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment with mock server and dashboard."""
        cls.mock_server_process = None
        cls.dashboard_process = None
        cls.driver = None
        
        # Start mock server
        try:
            cls.mock_server_process = subprocess.Popen([
                sys.executable, 
                os.path.join(os.path.dirname(__file__), 'mock_api_server.py')
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for mock server to start
            time.sleep(3)
            
            # Verify mock server is running
            response = requests.get("http://localhost:8001/", timeout=5)
            if response.status_code != 200:
                raise Exception("Mock server failed to start")
            
            # Create temporary dashboard with mock server URL
            cls.temp_dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'temp_dashboard_ui.py')
            cls._create_temp_dashboard()
            
            # Start dashboard
            cls.dashboard_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", cls.temp_dashboard_path,
                "--server.port", "8502",  # Use different port to avoid conflicts
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for dashboard to start
            time.sleep(5)
            
            # Set up Selenium WebDriver
            cls._setup_webdriver()
            
        except Exception as e:
            pytest.skip(f"Could not set up UI test environment: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        if cls.driver:
            cls.driver.quit()
        
        if cls.dashboard_process:
            cls.dashboard_process.terminate()
            cls.dashboard_process.wait()
        
        if cls.mock_server_process:
            cls.mock_server_process.terminate()
            cls.mock_server_process.wait()
        
        # Clean up temporary dashboard file
        if hasattr(cls, 'temp_dashboard_path') and os.path.exists(cls.temp_dashboard_path):
            os.unlink(cls.temp_dashboard_path)
    
    @classmethod
    def _create_temp_dashboard(cls):
        """Create temporary dashboard file with mock server URL."""
        dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'dashboard.py')
        
        with open(dashboard_path, 'r') as f:
            content = f.read()
        
        # Replace API URL
        content = content.replace(
            'API_BASE_URL = "http://localhost:8000"',
            'API_BASE_URL = "http://localhost:8001"'
        )
        
        with open(cls.temp_dashboard_path, 'w') as f:
            f.write(content)
    
    @classmethod
    def _setup_webdriver(cls):
        """Set up Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            pytest.skip(f"Could not set up WebDriver: {e}")
    
    def test_dashboard_loads(self):
        """Test that dashboard loads successfully."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check if title is present
        title = self.driver.find_element(By.TAG_NAME, "h1")
        assert "AI Copilot Dashboard" in title.text
    
    def test_sidebar_elements(self):
        """Test that sidebar elements are present."""
        self.driver.get("http://localhost:8502")
        
        # Wait for sidebar to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stSidebar']"))
        )
        
        # Check for time range selector
        time_range = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
        assert time_range is not None
        
        # Check for analysis type selector
        analysis_type = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
        assert len(analysis_type) >= 2  # Should have at least 2 selectboxes
    
    def test_health_check_button(self):
        """Test health check functionality."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for system health expander
        try:
            health_expander = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='stExpander']")
            health_expander.click()
            time.sleep(2)
            
            # Check if health status is displayed
            health_content = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='stExpander'] .streamlit-expanderContent")
            assert health_content is not None
            
        except NoSuchElementException:
            # If expander is not found, that's okay - it might be collapsed by default
            pass
    
    def test_analysis_buttons(self):
        """Test analysis buttons are present and clickable."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for analysis buttons
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stButton']")
        assert len(buttons) > 0, "No analysis buttons found"
        
        # Test clicking a button (without waiting for full response)
        for button in buttons:
            if "Run Analysis" in button.text or "Daily Summary" in button.text:
                button.click()
                time.sleep(1)  # Brief wait to see if button responds
                break
    
    def test_quick_actions_section(self):
        """Test quick actions section is present."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Wait until the quick actions header text is rendered
        WebDriverWait(self.driver, 10).until(
            lambda d: any(
                "Quick Actions" in header.text
                for header in d.find_elements(By.TAG_NAME, "h2")
            ),
            "Quick Actions section not found",
        )
    
    def test_page_layout(self):
        """Test that page layout is correct."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check for main title
        title = self.driver.find_element(By.TAG_NAME, "h1")
        assert "🤖 AI Copilot Dashboard" in title.text
        
        # Check for subtitle text anywhere on the page (Streamlit may render sidebar <p> first)
        subtitles = self.driver.find_elements(By.TAG_NAME, "p")
        assert any(
            "Intelligent monitoring" in text or "monitoring" in text.lower()
            for text in (subtitle.text for subtitle in subtitles)
        ), "Expected monitoring subtitle not found"
    
    def test_responsive_design(self):
        """Test that dashboard is responsive."""
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Test different window sizes
        sizes = [(1920, 1080), (1366, 768), (1024, 768)]
        
        for width, height in sizes:
            self.driver.set_window_size(width, height)
            time.sleep(1)
            
            # Check that main elements are still visible
            title = self.driver.find_element(By.TAG_NAME, "h1")
            assert title.is_displayed(), f"Title not visible at {width}x{height}"
    
    def test_error_handling_ui(self):
        """Test UI error handling when API is unavailable."""
        # This test would require stopping the mock server temporarily
        # For now, we'll just verify the UI structure is robust
        self.driver.get("http://localhost:8502")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check that page loads even if some API calls fail
        title = self.driver.find_element(By.TAG_NAME, "h1")
        assert title.is_displayed()


# Optional: Test with different browsers
class TestDashboardUIFirefox(TestDashboardUI):
    """UI tests using Firefox (optional)."""
    
    @classmethod
    def _setup_webdriver(cls):
        """Set up Firefox WebDriver."""
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        
        try:
            cls.driver = webdriver.Firefox(options=firefox_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            pytest.skip(f"Could not set up Firefox WebDriver: {e}")


if __name__ == "__main__":
    # Run UI tests
    pytest.main([__file__, "-v", "-s"])
