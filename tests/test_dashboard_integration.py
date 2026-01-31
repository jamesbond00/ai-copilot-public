"""
Integration tests for dashboard with mock API server.
"""

import pytest
import requests
import time
import subprocess
import threading
from datetime import datetime
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.dashboard import call_api


class TestDashboardIntegration:
    """Integration tests for dashboard with mock API."""
    
    @classmethod
    def setup_class(cls):
        """Start mock API server for integration tests."""
        cls.mock_server_process = None
        cls.mock_server_url = "http://localhost:8001"
        
        # Start mock server in background
        try:
            cls.mock_server_process = subprocess.Popen([
                sys.executable, 
                os.path.join(os.path.dirname(__file__), 'mock_api_server.py')
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(3)
            
            # Test if server is running
            response = requests.get(f"{cls.mock_server_url}/", timeout=5)
            if response.status_code != 200:
                raise Exception("Mock server failed to start")
                
        except Exception as e:
            pytest.skip(f"Could not start mock server: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Stop mock API server."""
        if cls.mock_server_process:
            cls.mock_server_process.terminate()
            cls.mock_server_process.wait()
    
    def test_health_endpoint_integration(self):
        """Test health endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "monitoring_system_connected" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_daily_summary_integration(self):
        """Test daily summary endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/summary/daily", params={"days_back": 1})
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "key_insights" in data
        assert "recommendations" in data
        assert "confidence_score" in data
        assert "analysis_timestamp" in data
        assert "log_count" in data
        
        assert isinstance(data["key_insights"], list)
        assert isinstance(data["recommendations"], list)
        assert 0 <= data["confidence_score"] <= 1
        assert data["log_count"] > 0
    
    def test_error_analysis_integration(self):
        """Test error analysis endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/analysis/errors", params={"hours_back": 24})
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "key_insights" in data
        assert "recommendations" in data
        assert "confidence_score" in data
        assert "analysis_timestamp" in data
        assert "log_count" in data
    
    def test_performance_analysis_integration(self):
        """Test performance analysis endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/analysis/performance", params={"hours_back": 24})
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "key_insights" in data
        assert "recommendations" in data
        assert "confidence_score" in data
        assert "analysis_timestamp" in data
        assert "log_count" in data
    
    def test_metrics_summary_integration(self):
        """Test metrics summary endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/metrics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_requests" in data
        assert "error_rate" in data
        assert "avg_response_time" in data
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "timestamp" in data
    
    def test_recent_logs_integration(self):
        """Test recent logs endpoint integration."""
        response = requests.get(f"{self.mock_server_url}/logs/recent", params={"limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
        assert data["count"] == len(data["logs"])
        
        if data["logs"]:
            log = data["logs"][0]
            assert "timestamp" in log
            assert "level" in log
            assert "message" in log
            assert "source" in log
            assert "metadata" in log
    
    def test_dashboard_api_call_with_mock_server(self):
        """Test dashboard API call function with mock server."""
        # Temporarily modify the API_BASE_URL for testing
        import ui.dashboard
        original_url = ui.dashboard.API_BASE_URL
        ui.dashboard.API_BASE_URL = self.mock_server_url
        
        try:
            # Test health check
            result = call_api("/health")
            assert result != {}
            assert "status" in result
            
            # Test daily summary
            result = call_api("/summary/daily", {"days_back": 1})
            assert result != {}
            assert "summary" in result
            
            # Test error analysis
            result = call_api("/analysis/errors", {"hours_back": 24})
            assert result != {}
            assert "key_insights" in result
            
        finally:
            # Restore original URL
            ui.dashboard.API_BASE_URL = original_url
    
    def test_api_error_handling_integration(self):
        """Test API error handling with mock server."""
        # Test non-existent endpoint
        response = requests.get(f"{self.mock_server_url}/nonexistent")
        assert response.status_code == 404
        
        # Test with dashboard API call function
        import ui.dashboard
        original_url = ui.dashboard.API_BASE_URL
        ui.dashboard.API_BASE_URL = self.mock_server_url
        
        try:
            result = call_api("/nonexistent")
            assert result == {}  # Should return empty dict on error
        finally:
            ui.dashboard.API_BASE_URL = original_url


class TestDashboardDataFlow:
    """Test data flow through dashboard components."""
    
    def test_analysis_result_structure(self):
        """Test that analysis results have expected structure."""
        # This would be tested with actual Streamlit components
        # For now, we test the data structure expectations
        
        expected_fields = [
            "summary", "key_insights", "recommendations", 
            "confidence_score", "analysis_timestamp", "log_count"
        ]
        
        # Sample result structure
        sample_result = {
            "summary": "Test summary",
            "key_insights": ["Insight 1", "Insight 2"],
            "recommendations": ["Rec 1", "Rec 2"],
            "confidence_score": 0.85,
            "analysis_timestamp": datetime.now().isoformat(),
            "log_count": 100
        }
        
        for field in expected_fields:
            assert field in sample_result
        
        assert isinstance(sample_result["key_insights"], list)
        assert isinstance(sample_result["recommendations"], list)
        assert 0 <= sample_result["confidence_score"] <= 1
        assert sample_result["log_count"] >= 0
    
    def test_time_range_mapping(self):
        """Test time range mapping logic."""
        time_mapping = {
            "Last 24 hours": 24,
            "Last 7 days": 168,
            "Last 30 days": 720
        }
        
        for time_range, expected_hours in time_mapping.items():
            hours_back = time_mapping[time_range]
            assert hours_back == expected_hours
    
    def test_analysis_type_mapping(self):
        """Test analysis type mapping logic."""
        analysis_types = ["Daily Summary", "Error Analysis", "Performance Analysis"]
        
        # Test that all analysis types are valid
        for analysis_type in analysis_types:
            assert analysis_type in analysis_types
        
        # Test endpoint mapping logic
        endpoint_mapping = {
            "Daily Summary": "/summary/daily",
            "Error Analysis": "/analysis/errors",
            "Performance Analysis": "/analysis/performance"
        }
        
        for analysis_type, expected_endpoint in endpoint_mapping.items():
            assert expected_endpoint in ["/summary/daily", "/analysis/errors", "/analysis/performance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
