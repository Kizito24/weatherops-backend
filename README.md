# WeatherOps Backend

A comprehensive event-driven weather intelligence platform that monitors weather conditions, triggers automated alerts, and manages location-based rules. Built with FastAPI, SQLAlchemy, Redis, and Celery for scalable, real-time weather monitoring.

## 🎯 Overview

WeatherOps is a sophisticated backend system designed to:
- Monitor weather patterns for multiple locations in real-time
- Trigger intelligent alerts based on user-defined rules
- Manage location preferences and user settings
- Process async tasks using Celery workers
- Cache frequently accessed data using Redis
- Provide RESTful APIs for frontend integration

## 🏗️ Architecture Highlights

- **Language**: Python 3.12
- **Framework**: FastAPI (async/await)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for caching and session management
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT-based access/refresh tokens
- **Deployment**: Docker + Render with automatic migrations

## 📦 Core Features

### 1. **User Management**
- User registration and authentication
- JWT access/refresh token system
- Password hashing with Argon2
- User preferences and settings

### 2. **Location Management**
- Create and manage multiple monitoring locations
- Geographic coordinates (latitude, longitude)
- Location-specific configurations

### 3. **Weather Monitoring**
- Real-time weather data fetching via WeatherAI API
- 7-day forecast data
- Multiple weather parameters (temperature, humidity, precipitation, wind)
- Caching for performance optimization

### 4. **Alert System**
- User-defined alert rules based on weather conditions
- Multiple alert conditions (temperature thresholds, precipitation, wind speed)
- Alert status tracking (triggered, acknowledged, resolved)
- Notification via multiple channels (email, SMS, webhooks)

### 5. **Rule Engine**
- Flexible rule creation and management
- Condition-based rule evaluation
- Rule execution and alert triggering
- Background job processing

### 6. **Async Task Processing**
- Celery workers for background jobs
- Scheduled tasks via Celery Beat
- Weather monitoring automation
- Email and SMS notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd weatherops-backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery Beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

### Docker Deployment

```bash
# Using docker-compose.railway.yml for local Render-like setup
docker-compose -f docker-compose.yml up -d

# Access API at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## 📚 Documentation Structure

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, data flow, and infrastructure
- **[DIAGRAMS.md](DIAGRAMS.md)** - UML diagrams (usecase, class, sequence, state, flow)
- **[API.md](API.md)** - REST API endpoints and specifications
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment on Render
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development guidelines and setup

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token

### Locations
- `GET /api/v1/locations` - List user's locations
- `POST /api/v1/locations` - Create new location
- `GET /api/v1/locations/{id}` - Get location details
- `PUT /api/v1/locations/{id}` - Update location
- `DELETE /api/v1/locations/{id}` - Delete location

### Weather
- `GET /api/v1/weather` - Get weather for coordinates
- `GET /api/v1/weather/usage` - Get API usage statistics

### Alerts
- `GET /api/v1/alerts` - List user's alerts
- `GET /api/v1/alerts/{id}` - Get alert details
- `PUT /api/v1/alerts/{id}` - Update alert status

### Rules
- `GET /api/v1/rules` - List rules
- `POST /api/v1/rules` - Create rule
- `GET /api/v1/rules/location/{location_id}` - Get rules for location

### Health
- `GET /api/v1/health` - Health check endpoint

## 🗄️ Database Schema

### Core Tables
- **users** - User accounts and authentication
- **locations** - Weather monitoring locations
- **alerts** - Weather alerts triggered by rules
- **rules** - User-defined alert rules
- **refresh_tokens** - JWT refresh token storage
- **user_preferences** - User settings and preferences

See [DIAGRAMS.md](DIAGRAMS.md) for Entity Relationship Diagram.

## 🔐 Security Features

- **JWT Authentication** - Secure token-based auth
- **Password Hashing** - Argon2 password hashing
- **HTTPS Only** - TLS/SSL in production
- **CORS Protection** - Configurable CORS policies
- **Rate Limiting** - Request throttling (configurable)
- **Input Validation** - Pydantic schema validation

## 📊 Monitoring & Logging

- **Structured Logging** - JSON-formatted logs
- **Request Logging** - All API requests logged
- **Error Tracking** - Exception logging
- **Redis Monitoring** - Cache hit/miss tracking
- **Task Monitoring** - Celery task execution tracking

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Follow code style guidelines (Black, Ruff)
3. Add tests for new features
4. Submit PR for review

### Code Quality
```bash
# Format code
black app/

# Lint
ruff check app/

# Type checking
mypy app/

# Run tests
pytest tests/
```

## 📈 Performance Optimization

- **Caching** - Redis cache for weather data and frequently accessed data
- **Pagination** - Efficient list endpoint pagination
- **Database Indexing** - Optimized indexes on frequently queried columns
- **Connection Pooling** - SQLAlchemy connection pool management
- **Async Operations** - Non-blocking I/O for better throughput

## 🚢 Deployment

### Production Deployment (Render)
```bash
# Environment setup on Render
- Create PostgreSQL service
- Create Redis service
- Create Web service with Dockerfile
- Configure environment variables
- Deploy with automatic migrations
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
- Verify DATABASE_URL environment variable
- Check PostgreSQL service is running
- Review connection string format

**Redis Connection Errors**
- Verify REDIS_URL environment variable
- Check Redis service is running
- Ensure Redis is accessible from app

**Celery Task Failures**
- Check worker logs for errors
- Verify Redis is running
- Review task configuration

## 📄 License

MIT License - See LICENSE file

## 📧 Support

For issues, questions, or contributions:
- GitHub Issues: [Issue Tracker]
- Email: team@weatherops.com

---

**Last Updated**: 2026-06-06  
**Version**: 0.1.0  
**Status**: Production Ready
