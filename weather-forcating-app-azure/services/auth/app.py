import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'auth-service'})

@app.route('/api/auth/register', methods=['POST'])
@metrics.counter('user_registrations', 'Number of user registrations')
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    password_hash = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=password_hash
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully', 'user': new_user.to_dict()}), 201

@app.route('/api/auth/login', methods=['POST'])
@metrics.counter('user_logins', 'Number of user login attempts')
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    # Find user
    user = User.query.filter_by(username=data['username']).first()
    
    # Check password
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Generate token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    })

@app.route('/api/auth/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})

@app.route('/api/auth/validate', methods=['POST'])
@jwt_required()
def validate_token():
    current_user_id = get_jwt_identity()
    return jsonify({'valid': True, 'user_id': current_user_id})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')