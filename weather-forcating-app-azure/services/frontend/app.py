import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure session
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Service URLs
WEATHER_SERVICE_URL = os.getenv('WEATHER_SERVICE_URL', 'http://weather-data-service:5001')
FORECAST_SERVICE_URL = os.getenv('FORECAST_SERVICE_URL', 'http://forecast-analytics-service:5002')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5003')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'frontend-service'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    city = request.args.get('city', 'London')
    
    try:
        # Get current weather
        weather_response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/current?city={city}")
        weather_data = weather_response.json()
        
        # Get forecast
        forecast_response = requests.get(f"{WEATHER_SERVICE_URL}/api/weather/forecast?city={city}")
        forecast_data = forecast_response.json()
        
        # Get weather analytics
        analytics_response = requests.get(f"{FORECAST_SERVICE_URL}/api/analytics/weather-summary?city={city}")
        analytics_data = analytics_response.json()
        
        # Get temperature trend
        trend_response = requests.get(f"{FORECAST_SERVICE_URL}/api/analytics/temperature-trend?city={city}")
        trend_data = trend_response.json()
        
        # Get severe weather alerts
        alerts_response = requests.get(f"{FORECAST_SERVICE_URL}/api/analytics/severe-weather-alert?city={city}")
        alerts_data = alerts_response.json()
        
        return render_template(
            'dashboard.html',
            city=city,
            weather=weather_data,
            forecast=forecast_data,
            analytics=analytics_data,
            trend=trend_data,
            alerts=alerts_data
        )
    
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching weather data: {str(e)}", 'danger')
        return render_template('dashboard.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/api/auth/login",
                json={'username': username, 'password': password}
            )
            
            if response.status_code == 200:
                data = response.json()
                session['access_token'] = data['access_token']
                session['user'] = data['user']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to authentication service: {str(e)}", 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/api/auth/register",
                json={
                    'username': username,
                    'email': email,
                    'password': password
                }
            )
            
            if response.status_code == 201:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                data = response.json()
                flash(f"Registration failed: {data.get('error', 'Unknown error')}", 'danger')
        
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to authentication service: {str(e)}", 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=session.get('user'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html')
    
    return redirect(url_for('dashboard', city=query))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')