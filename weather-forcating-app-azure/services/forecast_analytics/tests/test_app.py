import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class ForecastAnalyticsServiceTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    @patch('app.requests.get')
    def test_temperature_trend(self, mock_get):
        # Mock the historical data response
        historical_response = MagicMock()
        historical_response.status_code = 200
        historical_response.json.return_value = {
            'city': 'London',
            'country': 'GB',
            'historical_data': [
                {
                    'temperature': 15.5,
                    'timestamp': '2023-01-01T12:00:00'
                },
                {
                    'temperature': 16.5,
                    'timestamp': '2023-01-02T12:00:00'
                },
                {
                    'temperature': 17.5,
                    'timestamp': '2023-01-03T12:00:00'
                }
            ]
        }
        
        # Mock the forecast data response
        forecast_response = MagicMock()
        forecast_response.status_code = 200
        forecast_response.json.return_value = {
            'city': 'London',
            'country': 'GB',
            'forecast': [
                {
                    'temperature': 18.5,
                    'timestamp': '2023-01-04T12:00:00'
                },
                {
                    'temperature': 19.5,
                    'timestamp': '2023-01-05T12:00:00'
                }
            ]
        }
        
        # Configure the mock to return different responses for different URLs
        def get_side_effect(url, *args, **kwargs):
            if 'historical' in url:
                return historical_response
            elif 'forecast' in url:
                return forecast_response
            return MagicMock(status_code=404)
        
        mock_get.side_effect = get_side_effect
        
        # Test the endpoint
        response = self.client.get('/api/analytics/temperature-trend?city=London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertIn('trend_direction', data)
        self.assertIn('trend_magnitude', data)
        self.assertIn('historical_daily_avg', data)
        self.assertIn('forecast_daily_avg', data)
    
    @patch('app.requests.get')
    def test_weather_summary(self, mock_get):
        # Mock the historical data response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'city': 'London',
            'country': 'GB',
            'historical_data': [
                {
                    'temperature': 15.5,
                    'humidity': 80,
                    'wind_speed': 5.5,
                    'description': 'cloudy',
                    'timestamp': '2023-01-01T12:00:00'
                },
                {
                    'temperature': 16.5,
                    'humidity': 75,
                    'wind_speed': 6.0,
                    'description': 'partly cloudy',
                    'timestamp': '2023-01-02T12:00:00'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test the endpoint
        response = self.client.get('/api/analytics/weather-summary?city=London&period=7')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertIn('avg_temperature', data)
        self.assertIn('min_temperature', data)
        self.assertIn('max_temperature', data)
        self.assertIn('avg_humidity', data)
        self.assertIn('avg_wind_speed', data)
        self.assertIn('common_conditions', data)
    
    @patch('app.requests.get')
    def test_severe_weather_alert(self, mock_get):
        # Mock the forecast data response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'city': 'London',
            'country': 'GB',
            'forecast': [
                {
                    'temperature': 35.0,  # High temperature to trigger heat alert
                    'humidity': 80,
                    'wind_speed': 5.5,
                    'description': 'clear',
                    'timestamp': '2023-01-01T12:00:00'
                },
                {
                    'temperature': 16.5,
                    'humidity': 75,
                    'wind_speed': 25.0,  # High wind to trigger wind alert
                    'description': 'windy',
                    'timestamp': '2023-01-02T12:00:00'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test the endpoint
        response = self.client.get('/api/analytics/severe-weather-alert?city=London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertIn('alerts', data)
        self.assertTrue(len(data['alerts']) > 0)
        # Check for specific alerts
        alert_types = [alert['type'] for alert in data['alerts']]
        self.assertIn('extreme_heat', alert_types)
        self.assertIn('high_winds', alert_types)

if __name__ == '__main__':
    unittest.main()