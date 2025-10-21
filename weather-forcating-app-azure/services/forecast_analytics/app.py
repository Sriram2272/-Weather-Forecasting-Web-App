import os
import json
import requests
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from ai_models import WeatherTrendPredictor, SmartAlertSystem

# Load environment variables
load_dotenv()

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Initialize AI models
weather_predictor = WeatherTrendPredictor()
smart_alert_system = SmartAlertSystem()

# Weather Data Service URL
WEATHER_SERVICE_URL = os.getenv('WEATHER_SERVICE_URL', 'http://weather-data-service:5001')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'forecast-analytics-service'})

@app.route('/api/analytics/temperature-trend', methods=['GET'])
@metrics.counter('temperature_trend_requests', 'Number of temperature trend requests')
def get_temperature_trend():
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        # Get historical data from Weather Data Service
        response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/historical/{city}?days={days}")
        response.raise_for_status()
        data = response.json()
        
        if not data.get('historical_data'):
            return jsonify({'error': 'No historical data available'}), 404
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data['historical_data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate daily averages
        df['date'] = df['timestamp'].dt.date
        daily_avg = df.groupby('date')['temperature'].mean().reset_index()
        daily_avg['day_number'] = range(len(daily_avg))
        
        # Simple linear regression for trend
        X = daily_avg[['day_number']]
        y = daily_avg['temperature']
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next 5 days
        future_days = np.array(range(len(daily_avg), len(daily_avg) + 5)).reshape(-1, 1)
        future_temps = model.predict(future_days)
        
        # Calculate trend direction and magnitude
        slope = model.coef_[0]
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        trend_magnitude = abs(slope)
        
        # Prepare result
        result = {
            'city': city,
            'trend_direction': trend_direction,
            'trend_magnitude': float(trend_magnitude),
            'current_avg_temp': float(daily_avg['temperature'].iloc[-1]),
            'historical_daily_avg': [
                {'date': date.strftime('%Y-%m-%d'), 'temperature': float(temp)}
                for date, temp in zip(daily_avg['date'], daily_avg['temperature'])
            ],
            'forecast_daily_avg': [
                {'date': (daily_avg['date'].iloc[-1] + timedelta(days=i+1)).strftime('%Y-%m-%d'), 
                 'temperature': float(temp)}
                for i, temp in enumerate(future_temps)
            ]
        }
        
        return jsonify(result)
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/weather-summary', methods=['GET'])
@metrics.counter('weather_summary_requests', 'Number of weather summary requests')
def get_weather_summary():
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        # Get historical data from Weather Data Service
        response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/historical/{city}?days={days}")
        response.raise_for_status()
        data = response.json()
        
        if not data.get('historical_data'):
            return jsonify({'error': 'No historical data available'}), 404
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data['historical_data'])
        
        # Calculate summary statistics
        summary = {
            'city': city,
            'period': f"Last {days} days",
            'avg_temperature': float(df['temperature'].mean()),
            'min_temperature': float(df['temperature'].min()),
            'max_temperature': float(df['temperature'].max()),
            'avg_humidity': float(df['humidity'].mean()),
            'avg_wind_speed': float(df['wind_speed'].mean()),
            'common_conditions': df['description'].value_counts().to_dict()
        }
        
        return jsonify(summary)
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/severe-weather-alert', methods=['GET'])
@metrics.counter('severe_weather_requests', 'Number of severe weather alert requests')
def get_severe_weather_alert():
    city = request.args.get('city', 'London')
    
    try:
        # Get forecast data from Weather Data Service
        response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/forecast?city={city}")
        response.raise_for_status()
        data = response.json()
        
        # Use the Smart Alert System to analyze forecast data
        alerts = smart_alert_system.analyze_forecast(data['forecast'])
        
        return jsonify({
            'city': city,
            'has_alerts': len(alerts) > 0,
            'alerts': alerts
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/ai-prediction', methods=['GET'])
@metrics.counter('ai_prediction_requests', 'Number of AI prediction requests')
def ai_prediction():
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        # Get historical data from Weather Data Service
        response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/historical/{city}")
        response.raise_for_status()
        data = response.json()
        
        # Check if there's enough data for prediction
        if len(data['historical_data']) < 5:
            return jsonify({
                'city': city,
                'error': 'Not enough historical data for AI prediction'
            }), 400
        
        # Train the model with the latest data
        weather_predictor.train(data['historical_data'])
        
        # Make predictions
        predictions = weather_predictor.predict(data['historical_data'], days_to_predict=days)
        
        return jsonify({
            'city': city,
            'predictions': predictions,
            'model_info': {
                'type': 'RandomForestRegressor',
                'features': ['day_of_year', 'month', 'day', 'hour', 'temperature_rolling_avg', 'humidity_rolling_avg', 'pressure_rolling_avg']
            }
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')