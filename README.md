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

## 🚀 Getting Started

### Quick Start (5 minutes)

For complete local setup instructions, **see [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)**.

Quick summary:
```bash
git clone https://github.com/Kizito24/weatherops-backend.git
cd weatherops-backend
make install       # Install dependencies
make db-create     # Create local database
make migrate       # Run migrations
make start-api     # Start API server
```

Then open 3 more terminals:
```bash
make start-worker  # Celery worker
make start-beat    # Celery scheduler
make start-redis   # Redis (if not running as service)
```

Visit: **http://localhost:8000/docs**

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** | 📍 **Start here** — Complete local setup guide with Makefile commands |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design, tech stack, data flow, and infrastructure |
| **[CELERY_RENDER_SETUP.md](CELERY_RENDER_SETUP.md)** | Celery background worker configuration for Render |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Production deployment on Render |
| **[DIAGRAMS.md](DIAGRAMS.md)** | System diagrams (architecture, entity relationships) |

**API Docs:** Visit `http://localhost:8000/docs` for interactive Swagger UI (auto-generated from code)

## 🔧 API Endpoints

All API endpoints are documented in the interactive API documentation:

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

Endpoints include:
- **Authentication** — Register, login, refresh tokens
- **Locations** — CRUD operations for monitored locations
- **Weather** — Get current weather and API usage stats
- **Alerts** — List, view, and update alert status
- **Rules** — Create and manage alert rules per location
- **Health** — Service health check

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

For detailed troubleshooting, database inspection, and common issues, see **[LOCAL_DEVELOPMENT.md → Troubleshooting](LOCAL_DEVELOPMENT.md#troubleshooting)**.

Quick checks:
- PostgreSQL running? `psql --version`
- Redis running? `redis-cli ping`
- Dependencies installed? `make install`
- Database migrated? `make migrate`

## 📄 License

MIT License - See LICENSE file

## 📧 Support

For issues, questions, or contributions:
- GitHub Issues: Kizito24
- Email: kizitochiazor@gmail.com

---

**Last Updated**: 2026-06-06  
**Version**: 0.1.0  
**Status**: Production Ready
