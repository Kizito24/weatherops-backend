# WeatherOps System Architecture

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [Technology Stack](#technology-stack)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Database Design](#database-design)
6. [Security Architecture](#security-architecture)
7. [Performance & Scalability](#performance--scalability)
8. [Disaster Recovery](#disaster-recovery)

## High-Level Architecture

WeatherOps follows a **layered, event-driven architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│          (Web Browser / Mobile App / Third-party)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│                    API GATEWAY LAYER                         │
│  • CORS Middleware  • Auth Middleware  • Rate Limiting      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               BUSINESS LOGIC LAYER                           │
│  • Auth Service      • Weather Service     • Rule Engine     │
│  • Location Service  • Notification Service                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              DATA ACCESS LAYER (Repository)                  │
│  • User Repository   • Location Repository  • Rule Repo     │
│  • Alert Repository  • Token Repository                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  PERSISTENCE LAYER                           │
│  • PostgreSQL (Primary Data) • Redis (Cache & Queue)        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              BACKGROUND PROCESSING LAYER                     │
│  • Celery Workers    • Celery Beat        • Task Queue      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              EXTERNAL INTEGRATIONS LAYER                     │
│  • WeatherAI API     • SendGrid Email    • Twilio SMS       │
│  • Webhook Service   • Notification Channels               │
└──────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Framework
- **FastAPI** (0.115.0) - Modern async web framework
- **Uvicorn** (0.32.0) - ASGI server
- **Python** (3.12) - Runtime environment

### Database & Storage
- **PostgreSQL** (13+) - Primary relational database
  - AsyncPG driver for async connections
  - SQLAlchemy 2.0 ORM for data modeling
- **Redis** (6+) - Cache and message broker
  - Session management
  - Rate limiting
  - Cache layer

### Authentication & Security
- **PyJWT** - JWT token generation and validation
- **Bcrypt/Argon2** - Password hashing
- **python-jose** - Cryptographic operations

### Async Task Processing
- **Celery** (5.4.0) - Distributed task queue
- **Celery Beat** - Periodic task scheduling
- **Redis** - Message broker for Celery

### Database Migrations
- **Alembic** (1.14.0) - Database schema versioning
- **SQLAlchemy** (2.0.36) - ORM and migrations

### Data Validation
- **Pydantic** (2.10.3) - Request/response validation
- **Pydantic-Settings** (2.5.0) - Configuration management

### External Integrations
- **HTTPX** (0.28.1) - Async HTTP client
- **SendGrid** (6.12.5) - Email service
- **Twilio** (9.10.9) - SMS service

### Development & Testing
- **Pytest** (8.3.4) - Testing framework
- **Pytest-Asyncio** (0.24.0) - Async test support
- **Black** (24.12.0) - Code formatting
- **Ruff** (0.8.3) - Linting
- **MyPy** (1.14.1) - Type checking

### Deployment
- **Docker** - Containerization
- **Render** - Cloud deployment platform

## System Components

### 1. API Layer (FastAPI)

**Responsibilities:**
- HTTP request handling
- Route management
- Request/response validation
- Authentication verification
- CORS policy enforcement
- Rate limiting

**Key Files:**
- `app/main.py` - FastAPI app initialization
- `app/api/v1/router.py` - API route registration
- `app/api/v1/endpoints/` - Endpoint implementations

**Request Flow:**
```
HTTP Request
    ↓
Middleware (CORS, Auth, Rate Limit)
    ↓
Route Handler
    ↓
Service Layer Call
    ↓
Repository Call
    ↓
Database/Cache Access
    ↓
Response Serialization
    ↓
HTTP Response
```

### 2. Authentication Service

**Responsibilities:**
- User registration
- User login
- Token generation (access & refresh)
- Token validation
- Password hashing

**Key Files:**
- `app/services/auth_service.py` - Authentication logic
- `app/core/security/jwt.py` - JWT handling
- `app/core/security/password.py` - Password operations
- `app/dependencies/auth.py` - Auth dependencies

**Token Strategy:**
- **Access Token**: Short-lived (30 min), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens
- **Storage**: Access token in memory, Refresh token in HTTP-only cookie

### 3. Weather Service

**Responsibilities:**
- Fetch weather data from WeatherAI API
- Cache weather responses
- Parse and normalize weather data
- Handle API errors gracefully

**Key Files:**
- `app/services/weather_service.py` - Weather operations
- `app/core/integrations/weather_ai_client.py` - API client

**Caching Strategy:**
- Cache weather data for 1 hour
- Cache hit avoids external API call
- Redis stores cached data with TTL

**Data Flow:**
```
GET /weather?lat=X&lon=Y
    ↓
Check Redis Cache
    ├─ HIT → Return cached data
    └─ MISS → Fetch from WeatherAI API
         ↓
         Store in Redis (1h TTL)
         ↓
         Return response
```

### 4. Rule Engine

**Responsibilities:**
- Evaluate alert rules against weather data
- Trigger alerts when conditions met
- Manage rule state (active/inactive)
- Execute actions (notifications)

**Key Files:**
- `app/services/rule_engine.py` - Rule evaluation logic
- `app/services/rule_service.py` - Rule management

**Rule Evaluation Process:**
```
Get all active rules for location
    ↓
For each rule:
    ├─ Get current weather data
    ├─ Evaluate condition (temp > 30°C, wind > 20mph, etc.)
    ├─ If condition met:
    │   ├─ Create Alert in database
    │   ├─ Queue notification task
    │   └─ Update alert status
    └─ Move to next rule
```

**Supported Conditions:**
- Temperature thresholds (min/max)
- Humidity levels
- Precipitation amounts
- Wind speed
- Weather conditions (rain, snow, etc.)

### 5. Notification Service

**Responsibilities:**
- Queue notification tasks
- Send emails via SendGrid
- Send SMS via Twilio
- Send webhooks
- Track delivery status

**Key Files:**
- `app/services/notification_service.py` - Notification logic
- `app/core/channels/` - Channel implementations (email, SMS, webhook)

**Notification Channels:**
1. **Email** (SendGrid)
   - Template-based emails
   - Rich HTML formatting
   - Delivery tracking

2. **SMS** (Twilio)
   - Short message delivery
   - Character-count aware
   - Global coverage

3. **Webhook**
   - Custom HTTP callbacks
   - User-defined endpoints
   - Flexible payload

### 6. Celery Workers (Background Processing)

**Responsibilities:**
- Execute async tasks
- Run scheduled tasks
- Process notifications
- Handle long-running operations

**Key Files:**
- `app/workers/celery_app.py` - Celery configuration
- `app/workers/tasks/` - Task implementations
- `app/workers/beat_schedule.py` - Scheduled tasks

**Background Tasks:**
1. **Weather Monitoring** (every 6 hours)
   - Fetch weather for all locations
   - Evaluate rules
   - Trigger alerts

2. **Notification Delivery**
   - Send queued notifications
   - Retry failed deliveries
   - Log delivery status

3. **Data Cleanup**
   - Archive old alerts
   - Remove expired tokens
   - Purge old logs

### 7. Repository Layer (Data Access)

**Responsibilities:**
- Abstract database access
- Query optimization
- Entity persistence
- Transaction management

**Key Files:**
- `app/repositories/user_repository.py`
- `app/repositories/location_repository.py`
- `app/repositories/rule_repository.py`
- `app/repositories/alert_repository.py`
- `app/repositories/refresh_token_repository.py`

**Repository Pattern Benefits:**
- Decouples business logic from database
- Enables easy testing with mocks
- Centralizes query logic
- Simplifies migrations

### 8. Database Models (SQLAlchemy)

**Key Models:**
- **User** - User accounts and credentials
- **Location** - Monitored locations
- **Rule** - Alert rules
- **Alert** - Triggered alerts
- **RefreshToken** - Token storage
- **UserPreference** - User settings

See [DIAGRAMS.md](DIAGRAMS.md) for detailed ERD.

## Data Flow

### Complete User Journey

```
1. USER REGISTRATION
   ┌─────────────────────────────────────┐
   │ POST /auth/register                 │
   │ {email, password}                   │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Hash password                       │
   │ Create user in PostgreSQL           │
   │ Return success                      │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Response: {user_id, email}          │
   └─────────────────────────────────────┘

2. USER LOGIN
   ┌─────────────────────────────────────┐
   │ POST /auth/login                    │
   │ {email, password}                   │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Verify password against hash        │
   │ Create tokens (access + refresh)    │
   │ Store refresh token in DB           │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Response: {access_token, token_type}│
   └─────────────────────────────────────┘

3. LOCATION MANAGEMENT
   ┌─────────────────────────────────────┐
   │ POST /locations                     │
   │ {name, latitude, longitude}         │
   │ Auth: Bearer <access_token>         │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Verify JWT token                    │
   │ Extract user_id from token          │
   │ Create location in PostgreSQL       │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Response: {location_id, ...}        │
   └─────────────────────────────────────┘

4. WEATHER MONITORING (Automated via Celery)
   ┌─────────────────────────────────────┐
   │ Celery Beat Scheduled Task           │
   │ Trigger every 6 hours               │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Get all user locations              │
   │ For each location:                  │
   │  ├─ Check Redis cache               │
   │  └─ If miss: Fetch from WeatherAI   │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Get all active rules for location   │
   │ Evaluate conditions                 │
   │ Create alerts where matched         │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Queue notification tasks for alerts │
   │ Store alert in PostgreSQL           │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Celery worker processes tasks       │
   │ Send emails/SMS/webhooks            │
   │ Log delivery status                 │
   └─────────────────────────────────────┘

5. USER RETRIEVES ALERTS
   ┌─────────────────────────────────────┐
   │ GET /alerts                         │
   │ Auth: Bearer <access_token>         │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Verify JWT token                    │
   │ Query PostgreSQL for user's alerts  │
   │ Serialize results                   │
   └────────────┬────────────────────────┘
                │
   ┌────────────▼────────────────────────┐
   │ Response: [{alert_id, status, ...}] │
   └─────────────────────────────────────┘
```

## Database Design

### Schema Overview

**Users Table**
- `id` (UUID, PK)
- `email` (String, UK)
- `hashed_password` (String)
- `is_active` (Boolean)
- `created_at` (Datetime)
- `updated_at` (Datetime)

**Locations Table**
- `id` (UUID, PK)
- `user_id` (UUID, FK → Users)
- `name` (String)
- `latitude` (Float)
- `longitude` (Float)
- `description` (Text)
- `created_at` (Datetime)
- `updated_at` (Datetime)

**Rules Table**
- `id` (UUID, PK)
- `location_id` (UUID, FK → Locations)
- `condition_type` (String: temperature, humidity, precipitation, wind)
- `threshold_value` (Float)
- `operator` (String: >, <, >=, <=, ==)
- `is_active` (Boolean)
- `created_at` (Datetime)
- `updated_at` (Datetime)

**Alerts Table**
- `id` (UUID, PK)
- `rule_id` (UUID, FK → Rules)
- `user_id` (UUID, FK → Users)
- `status` (String: triggered, acknowledged, resolved)
- `message` (Text)
- `triggered_at` (Datetime)
- `acknowledged_at` (Datetime, nullable)
- `resolved_at` (Datetime, nullable)

**RefreshTokens Table**
- `id` (UUID, PK)
- `user_id` (UUID, FK → Users)
- `token` (String, UK)
- `expires_at` (Datetime)
- `created_at` (Datetime)

**UserPreferences Table**
- `id` (UUID, PK)
- `user_id` (UUID, FK → Users)
- `preference_key` (String)
- `preference_value` (String)
- `updated_at` (Datetime)

## Security Architecture

### Authentication & Authorization

**JWT Implementation:**
```
Access Token Payload:
{
  "sub": "user_id",
  "exp": 1234567890,
  "iat": 1234567000,
  "type": "access"
}

Refresh Token Payload:
{
  "sub": "user_id",
  "exp": 1234567890 + 7days,
  "iat": 1234567000,
  "type": "refresh"
}
```

**Token Validation:**
1. Extract token from Authorization header
2. Verify signature using secret key
3. Check expiration time
4. Extract user_id from claims
5. Grant access to protected resource

### Password Security

**Hashing Strategy:**
- Algorithm: Argon2 (resistant to GPU/ASIC attacks)
- Parameters:
  - Time cost: 3
  - Memory cost: 65536 KB
  - Parallelism: 4

**Verification:**
1. Hash provided password with Argon2
2. Compare with stored hash
3. Return success/failure (never leak which field failed)

### CORS & Request Validation

**CORS Policy:**
- Allowed origins: Configured via environment
- Allowed methods: GET, POST, PUT, DELETE, OPTIONS
- Allowed headers: Content-Type, Authorization
- Credentials: Include for auth headers

**Input Validation:**
- Pydantic schema validation
- Type checking on all inputs
- Range validation for numeric fields
- Email format validation

### Data Protection

**At Rest:**
- PostgreSQL encryption (built-in or disk-level)
- Redis is not encrypted (in-memory cache)
- Sensitive data: passwords hashed, tokens hashed

**In Transit:**
- HTTPS/TLS enforced
- HTTP requests redirected to HTTPS
- Certificate rotation handled by platform

**Database Access:**
- Parameterized queries (SQLAlchemy ORM)
- SQL injection prevention
- Least privilege: app user has no superuser rights

## Performance & Scalability

### Caching Strategy

**Redis Cache Layers:**
1. **Weather Cache** (1 hour TTL)
   - Stores weather API responses
   - Keyed by location_id
   - Reduces external API calls 90%+

2. **Session Cache** (lifetime of token)
   - Stores user session info
   - Validates tokens without DB query
   - Reduces DB load

3. **Rate Limiting** (per-user, 5 min window)
   - Tracks requests per user
   - Prevents abuse
   - Graceful degradation

### Database Optimization

**Indexing Strategy:**
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Location queries
CREATE INDEX idx_locations_user_id ON locations(user_id);

-- Rule evaluation
CREATE INDEX idx_rules_location_id_active ON rules(location_id, is_active);

-- Alert queries
CREATE INDEX idx_alerts_user_id_status ON alerts(user_id, status);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at DESC);

-- Token validation
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

**Connection Pooling:**
- Pool size: 20 connections
- Max overflow: 0 (queue excess requests)
- Pre-ping: Verify connection before use
- Recycle: 3600 seconds

### Async Processing

**Celery Configuration:**
- Broker: Redis
- Worker concurrency: 4
- Task time limit: 30 minutes
- Result backend: Redis (12 hour retention)

**Task Priority:**
1. **Critical** - User notifications (immediate)
2. **High** - Weather monitoring (within 30 min)
3. **Normal** - Data cleanup (batch)

### Horizontal Scaling

**Stateless API:**
- No session storage on server
- JWT tokens self-contained
- Multiple app instances supported
- Load balancer distributes requests

**Celery Scaling:**
- Workers are stateless
- New workers auto-connect to Redis
- Task queue distributes across workers
- Monitoring via Flower (optional)

## Disaster Recovery

### Backup Strategy

**PostgreSQL Backups:**
- Daily full backups
- Hourly incremental backups
- 30-day retention
- Test restores weekly

**Redis Backups:**
- Cache only (recoverable)
- No critical data stored
- Recovery: rebuild from database

### Failure Scenarios

**Database Outage:**
- Redis cache serves stale weather data
- Auth service fails (no token validation)
- Recovery time: minutes (platform managed)

**Redis Outage:**
- Auth service uses database (slower)
- Weather cache misses (external API calls)
- Recovery time: automatic failover

**API Server Crash:**
- Load balancer routes to healthy instances
- Pending tasks remain in queue
- Recovery time: < 30 seconds

**Worker Failure:**
- Tasks requeue automatically
- Other workers process tasks
- Monitoring alerts on failures
- Recovery time: automatic

### Monitoring & Alerting

**Metrics Tracked:**
- API response times
- Database query times
- Cache hit/miss rates
- Error rates
- Task queue depth
- Worker count

**Alerting Rules:**
- Response time > 1 second
- Error rate > 1%
- Queue depth > 1000
- Worker count = 0

---

## Architecture Evolution

### Current State (v0.1.0)
- Single PostgreSQL database
- Single Redis instance
- Celery with local worker
- No load balancing (platform managed)

### Future Considerations
- Read replicas for scaling queries
- Connection pooling proxy (PgBouncer)
- Multiple Redis instances (cluster)
- Elasticsearch for audit logs
- Distributed tracing (Jaeger)
- Service mesh (Istio) for security
