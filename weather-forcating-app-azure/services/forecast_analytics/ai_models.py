import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import os

class WeatherTrendPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'models/weather_trend_model.pkl'
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Load existing model or create a new one if it doesn't exist"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            # Create a default model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def prepare_features(self, historical_data):
        """Prepare features from historical weather data"""
        df = pd.DataFrame(historical_data)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extract time-based features
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day
        df['hour'] = df['timestamp'].dt.hour
        
        # Calculate rolling averages if enough data
        if len(df) > 5:
            df['temp_rolling_avg'] = df['temperature'].rolling(window=5, min_periods=1).mean()
            df['humidity_rolling_avg'] = df['humidity'].rolling(window=5, min_periods=1).mean()
            df['pressure_rolling_avg'] = df.get('pressure', pd.Series([1013] * len(df))).rolling(window=5, min_periods=1).mean()
        else:
            df['temp_rolling_avg'] = df['temperature']
            df['humidity_rolling_avg'] = df['humidity']
            df['pressure_rolling_avg'] = df.get('pressure', pd.Series([1013] * len(df)))
        
        # Select features for prediction
        features = df[['day_of_year', 'month', 'day', 'hour', 
                      'temp_rolling_avg', 'humidity_rolling_avg', 'pressure_rolling_avg']]
        
        return features, df['temperature']
    
    def train(self, historical_data):
        """Train the model with historical weather data"""
        if len(historical_data) < 10:
            return False  # Not enough data to train
        
        X, y = self.prepare_features(historical_data)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train the model
        self.model.fit(X_scaled, y)
        
        # Save the model
        joblib.dump(self.model, self.model_path)
        
        return True
    
    def predict(self, historical_data, days_to_predict=7):
        """Predict future weather trends based on historical data"""
        if len(historical_data) < 5:
            return None  # Not enough data to make predictions
        
        # Prepare historical features
        X, _ = self.prepare_features(historical_data)
        
        # Get the last timestamp
        last_timestamp = pd.to_datetime(historical_data[-1]['timestamp'])
        
        # Create future dates for prediction
        future_dates = [last_timestamp + timedelta(days=i) for i in range(1, days_to_predict + 1)]
        
        # Create feature dataframe for future dates
        future_df = pd.DataFrame({
            'timestamp': future_dates,
            'day_of_year': [date.dayofyear for date in future_dates],
            'month': [date.month for date in future_dates],
            'day': [date.day for date in future_dates],
            'hour': [date.hour for date in future_dates]
        })
        
        # Use the last values for rolling averages
        future_df['temp_rolling_avg'] = X['temp_rolling_avg'].iloc[-1]
        future_df['humidity_rolling_avg'] = X['humidity_rolling_avg'].iloc[-1]
        future_df['pressure_rolling_avg'] = X['pressure_rolling_avg'].iloc[-1]
        
        # Select features for prediction
        future_X = future_df[['day_of_year', 'month', 'day', 'hour', 
                             'temp_rolling_avg', 'humidity_rolling_avg', 'pressure_rolling_avg']]
        
        # Scale features
        future_X_scaled = self.scaler.transform(future_X)
        
        # Make predictions
        predictions = self.model.predict(future_X_scaled)
        
        # Create result
        result = []
        for i, date in enumerate(future_dates):
            result.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_temperature': float(predictions[i])
            })
        
        return result

class SmartAlertSystem:
    def __init__(self):
        self.extreme_heat_threshold = 35.0  # °C
        self.freezing_threshold = 0.0  # °C
        self.high_wind_threshold = 20.0  # m/s
        self.heavy_rain_threshold = 10.0  # mm/h
        self.storm_keywords = ['thunderstorm', 'storm', 'hurricane', 'tornado']
    
    def analyze_forecast(self, forecast_data):
        """Analyze forecast data and generate smart alerts"""
        alerts = []
        
        for forecast in forecast_data:
            date = forecast.get('timestamp', forecast.get('date', ''))
            temp = forecast.get('temperature', 0)
            wind = forecast.get('wind_speed', 0)
            description = forecast.get('description', '').lower()
            
            # Check for extreme heat
            if temp >= self.extreme_heat_threshold:
                alerts.append({
                    'type': 'extreme_heat',
                    'date': date,
                    'value': temp,
                    'message': f'Extreme heat warning: {temp}°C expected on {date}'
                })
            
            # Check for freezing conditions
            if temp <= self.freezing_threshold:
                alerts.append({
                    'type': 'freezing',
                    'date': date,
                    'value': temp,
                    'message': f'Freezing conditions warning: {temp}°C expected on {date}'
                })
            
            # Check for high winds
            if wind >= self.high_wind_threshold:
                alerts.append({
                    'type': 'high_winds',
                    'date': date,
                    'value': wind,
                    'message': f'High wind warning: {wind} m/s expected on {date}'
                })
            
            # Check for storms
            for keyword in self.storm_keywords:
                if keyword in description:
                    alerts.append({
                        'type': 'storm',
                        'date': date,
                        'value': description,
                        'message': f'Storm warning: {description} expected on {date}'
                    })
                    break
        
        return alerts
    
    def set_thresholds(self, extreme_heat=None, freezing=None, high_wind=None, heavy_rain=None):
        """Update alert thresholds based on location or user preferences"""
        if extreme_heat is not None:
            self.extreme_heat_threshold = extreme_heat
        if freezing is not None:
            self.freezing_threshold = freezing
        if high_wind is not None:
            self.high_wind_threshold = high_wind
        if heavy_rain is not None:
            self.heavy_rain_threshold = heavy_rain