import os
import json
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///weather_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# OpenWeatherMap API configuration
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
WEATHER_API_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# Define database models
class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(2), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    pressure = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'description': self.description,
            'wind_speed': self.wind_speed,
            'timestamp': self.timestamp.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'weather-data-service'})

@app.route('/api/weather/current', methods=['GET'])
@metrics.counter('weather_current_requests', 'Number of current weather requests')
def get_current_weather():
    city = request.args.get('city', 'London')
    
    # Check if we have recent data in the database (less than 30 minutes old)
    recent_data = WeatherData.query.filter_by(city=city).filter(
        WeatherData.timestamp > datetime.utcnow() - timedelta(minutes=30)
    ).order_by(WeatherData.timestamp.desc()).first()
    
    if recent_data:
        return jsonify(recent_data.to_dict())
    
    # If no recent data, fetch from OpenWeatherMap API
    try:
        response = requests.get(
            f"{WEATHER_API_BASE_URL}/weather",
            params={
                'q': city,
                'appid': OPENWEATHERMAP_API_KEY,
                'units': 'metric'
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Save to database
        weather_data = WeatherData(
            city=data['name'],
            country=data['sys']['country'],
            temperature=data['main']['temp'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            description=data['weather'][0]['description'],
            wind_speed=data['wind']['speed']
        )
        db.session.add(weather_data)
        db.session.commit()
        
        return jsonify(weather_data.to_dict())
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/forecast', methods=['GET'])
@metrics.counter('weather_forecast_requests', 'Number of forecast requests')
def get_weather_forecast():
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 5))
    
    try:
        response = requests.get(
            f"{WEATHER_API_BASE_URL}/forecast",
            params={
                'q': city,
                'appid': OPENWEATHERMAP_API_KEY,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Process and format the forecast data
        forecast_data = []
        for item in data['list']:
            forecast_data.append({
                'datetime': item['dt_txt'],
                'temperature': item['main']['temp'],
                'humidity': item['main']['humidity'],
                'pressure': item['main']['pressure'],
                'description': item['weather'][0]['description'],
                'wind_speed': item['wind']['speed']
            })
        
        return jsonify({
            'city': data['city']['name'],
            'country': data['city']['country'],
            'forecast': forecast_data
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/historical/<city>', methods=['GET'])
@metrics.counter('weather_historical_requests', 'Number of historical weather requests')
def get_historical_weather(city):
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    historical_data = WeatherData.query.filter_by(city=city).filter(
        WeatherData.timestamp > start_date
    ).order_by(WeatherData.timestamp.asc()).all()
    
    return jsonify({
        'city': city,
        'historical_data': [data.to_dict() for data in historical_data]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')