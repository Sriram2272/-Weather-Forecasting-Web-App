# Weather Forecasting Web App

![Azure Deployment Status](https://img.shields.io/badge/azure-deployed-blue)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)
![Kubernetes](https://img.shields.io/badge/kubernetes-configured-blueviolet)

A production-grade Weather Forecasting Web Application built with Flask microservices, containerized with Docker, orchestrated by Kubernetes, and deployed on Microsoft Azure.

## 🌦️ Overview

This application provides real-time weather updates and forecasts using the OpenWeatherMap API. The system is designed with a microservices architecture, containerized with Docker, and deployed to Azure Kubernetes Service (AKS) for high availability and scalability.

## ✨ Features

- **Real-time Weather Data**: Current conditions for any location worldwide
- **5-Day Forecasts**: Detailed weather predictions with 3-hour intervals
- **Interactive Maps**: Visual representation of weather patterns
- **User Authentication**: Secure access with JWT-based authentication
- **Personalized Alerts**: Notifications for severe weather conditions
- **AI-Powered Predictions**: Machine learning model for weather trend analysis
- **Responsive Design**: Optimized for both mobile and desktop viewing
- **High Availability**: 99.8% uptime with auto-scaling capabilities

## 🏗️ System Architecture

```
                                  ┌─────────────────┐
                                  │   Azure Load    │
                                  │    Balancer     │
                                  └────────┬────────┘
                                           │
                                           ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   API Gateway   │◄─┤  Auth Service   │  │ Frontend Service │  │  Monitoring &   │
│    Service      │  │  (JWT-based)    │  │  (Flask/React)   │  │     Logging     │
└────────┬────────┘  └─────────────────┘  └────────┬────────┘  └─────────────────┘
         │                                          │                    ▲
         ▼                                          ▼                    │
┌────────┴────────┐                      ┌─────────────────┐            │
│  Weather Data   │◄─────────────────────┤    Forecast     │────────────┘
│    Service      │                      │ Analytics Service│
└────────┬────────┘                      └────────┬────────┘
         │                                        │
         ▼                                        ▼
┌────────┴────────┐                      ┌────────┴────────┐
│   PostgreSQL    │                      │  Redis Cache &   │
│    Database     │                      │  ML Model Store  │
└─────────────────┘                      └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Flask**: Python web framework for microservices
- **SQLAlchemy**: ORM for database interactions
- **Redis**: For caching and session management
- **Celery**: For asynchronous task processing
- **JWT**: For secure authentication

### Data Storage
- **PostgreSQL**: Primary database for persistent storage
- **Redis**: For caching and real-time data

### Frontend
- **Flask-based Templates**: Server-side rendering
- **Bootstrap**: For responsive design
- **Chart.js**: For weather data visualization

### DevOps & Infrastructure
- **Docker**: For containerization
- **Kubernetes**: For container orchestration
- **Azure Kubernetes Service (AKS)**: For cloud deployment
- **Azure Container Registry (ACR)**: For Docker image storage
- **GitHub Actions/Azure DevOps**: For CI/CD pipeline

### Monitoring & Logging
- **Prometheus**: For metrics collection
- **Grafana**: For metrics visualization
- **ELK Stack**: For centralized logging
- **Azure Monitor**: For cloud resource monitoring

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- kubectl for Kubernetes interaction
- Azure CLI for cloud deployment
- Python 3.9+ (for local development)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/weather-forecasting-app.git
   cd weather-forecasting-app
   ```

2. Create a `.env` file with required environment variables:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://user:password@db:5432/weather_db
   REDIS_URL=redis://redis:6379/0
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application at http://localhost:5000

### Azure Deployment

1. Create Azure resources:
   ```bash
   az login
   az group create --name weather-app-rg --location eastus
   az acr create --resource-group weather-app-rg --name weatherappacr --sku Basic
   az aks create --resource-group weather-app-rg --name weather-app-aks --node-count 2 --enable-addons monitoring --generate-ssh-keys
   ```

2. Build and push Docker images:
   ```bash
   az acr login --name weatherappacr
   docker-compose build
   docker tag weather-frontend weatherappacr.azurecr.io/weather-frontend:latest
   docker tag weather-data-service weatherappacr.azurecr.io/weather-data-service:latest
   docker tag weather-forecast-service weatherappacr.azurecr.io/weather-forecast-service:latest
   docker tag weather-auth-service weatherappacr.azurecr.io/weather-auth-service:latest
   
   docker push weatherappacr.azurecr.io/weather-frontend:latest
   docker push weatherappacr.azurecr.io/weather-data-service:latest
   docker push weatherappacr.azurecr.io/weather-forecast-service:latest
   docker push weatherappacr.azurecr.io/weather-auth-service:latest
   ```

3. Deploy to AKS:
   ```bash
   az aks get-credentials --resource-group weather-app-rg --name weather-app-aks
   kubectl apply -f kubernetes/
   ```

4. Access the application:
   ```bash
   kubectl get service frontend-service
   ```

## 📊 Monitoring and Observability

### Prometheus & Grafana Setup

1. Deploy monitoring stack:
   ```bash
   kubectl apply -f kubernetes/monitoring/
   ```

2. Access Grafana dashboard:
   ```bash
   kubectl port-forward svc/grafana 3000:3000 -n monitoring
   ```
   
3. Access Prometheus:
   ```bash
   kubectl port-forward svc/prometheus-server 9090:9090 -n monitoring
   ```

### ELK Stack for Logging

1. Deploy ELK stack:
   ```bash
   kubectl apply -f kubernetes/logging/
   ```

2. Access Kibana:
   ```bash
   kubectl port-forward svc/kibana 5601:5601 -n logging
   ```

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [OpenWeatherMap API](https://openweathermap.org/api) for weather data
- Microsoft Azure for cloud infrastructure
- Flask and Python community for excellent documentation and tools
