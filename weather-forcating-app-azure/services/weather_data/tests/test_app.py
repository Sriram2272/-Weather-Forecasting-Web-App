import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, WeatherData, db

class WeatherDataServiceTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    @patch('app.requests.get')
    def test_current_weather_api_call(self, mock_get):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'London',
            'sys': {'country': 'GB'},
            'main': {
                'temp': 15.5,
                'humidity': 80,
                'pressure': 1013
            },
            'weather': [{'description': 'cloudy'}],
            'wind': {'speed': 5.5}
        }
        mock_get.return_value = mock_response
        
        # Test the endpoint
        response = self.client.get('/api/weather/current?city=London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(data['country'], 'GB')
        self.assertEqual(data['temperature'], 15.5)
    
    @patch('app.requests.get')
    def test_forecast_weather(self, mock_get):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'list': [
                {
                    'dt_txt': '2023-01-01 12:00:00',
                    'main': {
                        'temp': 15.5,
                        'humidity': 80,
                        'pressure': 1013
                    },
                    'weather': [{'description': 'cloudy'}],
                    'wind': {'speed': 5.5}
                }
            ],
            'city': {
                'name': 'London',
                'country': 'GB'
            }
        }
        mock_get.return_value = mock_response
        
        # Test the endpoint
        response = self.client.get('/api/weather/forecast?city=London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(data['country'], 'GB')
        self.assertTrue(len(data['forecast']) > 0)
    
    def test_historical_weather_empty(self):
        response = self.client.get('/api/weather/historical/London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(len(data['historical_data']), 0)
    
    def test_historical_weather_with_data(self):
        # Add some test data
        with app.app_context():
            weather_data = WeatherData(
                city='London',
                country='GB',
                temperature=15.5,
                humidity=80,
                pressure=1013,
                description='cloudy',
                wind_speed=5.5
            )
            db.session.add(weather_data)
            db.session.commit()
        
        # Test the endpoint
        response = self.client.get('/api/weather/historical/London')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(len(data['historical_data']), 1)
        self.assertEqual(data['historical_data'][0]['temperature'], 15.5)

if __name__ == '__main__':
    unittest.main()