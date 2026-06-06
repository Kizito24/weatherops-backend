# WeatherOps REST API Documentation

## Base URL

```
Production: https://weatherops-backend-xm5z.onrender.com
Development: http://localhost:8000
```

## Authentication

All protected endpoints require JWT authentication via Authorization header:

```bash
Authorization: Bearer <access_token>
```

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Authentication Endpoints

### Register User

**Endpoint:** `POST /api/v1/auth/register`

**Description:** Create a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2026-06-06T12:34:56Z"
}
```

**Errors:**
- `400` - Email already registered
- `422` - Validation error (invalid email format, password too short)

---

### Login

**Endpoint:** `POST /api/v1/auth/login`

**Description:** Authenticate user and receive access/refresh tokens

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Note:** Refresh token is automatically set as HTTP-only cookie

**Errors:**
- `401` - Invalid credentials
- `404` - User not found

---

### Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Description:** Get new access token using refresh token

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` - Invalid or expired refresh token

---

## Location Endpoints

### List Locations

**Endpoint:** `GET /api/v1/locations`

**Description:** Get all locations for authenticated user

**Authentication:** Required

**Query Parameters:**
- `skip` (int, default: 0) - Number of records to skip
- `limit` (int, default: 100) - Number of records to return

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "description": "Main office location",
    "created_at": "2026-06-06T12:34:56Z",
    "updated_at": "2026-06-06T12:34:56Z"
  }
]
```

---

### Create Location

**Endpoint:** `POST /api/v1/locations`

**Description:** Create a new location for monitoring

**Authentication:** Required

**Request Body:**
```json
{
  "name": "San Francisco",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "description": "West coast office"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "San Francisco",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "description": "West coast office",
  "created_at": "2026-06-06T12:34:56Z",
  "updated_at": "2026-06-06T12:34:56Z"
}
```

**Errors:**
- `422` - Invalid coordinates or missing required fields

---

### Get Location

**Endpoint:** `GET /api/v1/locations/{location_id}`

**Description:** Get details of a specific location

**Authentication:** Required

**Path Parameters:**
- `location_id` (UUID) - Location ID

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "San Francisco",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "description": "West coast office",
  "created_at": "2026-06-06T12:34:56Z",
  "updated_at": "2026-06-06T12:34:56Z"
}
```

**Errors:**
- `404` - Location not found

---

### Update Location

**Endpoint:** `PUT /api/v1/locations/{location_id}`

**Description:** Update location details

**Authentication:** Required

**Path Parameters:**
- `location_id` (UUID) - Location ID

**Request Body:**
```json
{
  "name": "San Francisco HQ",
  "description": "Updated west coast office"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "San Francisco HQ",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "description": "Updated west coast office",
  "created_at": "2026-06-06T12:34:56Z",
  "updated_at": "2026-06-06T13:00:00Z"
}
```

---

### Delete Location

**Endpoint:** `DELETE /api/v1/locations/{location_id}`

**Description:** Delete a location and associated rules

**Authentication:** Required

**Path Parameters:**
- `location_id` (UUID) - Location ID

**Response (204):** No content

**Errors:**
- `404` - Location not found

---

## Weather Endpoints

### Get Weather

**Endpoint:** `GET /api/v1/weather`

**Description:** Get current weather for coordinates

**Authentication:** Not required

**Query Parameters:**
- `lat` (float, required) - Latitude (-90 to 90)
- `lon` (float, required) - Longitude (-180 to 180)
- `days` (int, default: 7) - Number of forecast days (1-14)
- `ai` (boolean, default: true) - Include AI analysis
- `units` (string, default: metric) - Units: metric, imperial
- `lang` (string, default: en) - Language code

**Response (200):**
```json
{
  "current": {
    "temperature": 22.5,
    "feels_like": 21.0,
    "humidity": 65,
    "precipitation": 0,
    "wind_speed": 12.5,
    "wind_direction": "NW",
    "condition": "Partly Cloudy",
    "uvi": 5,
    "visibility": 10000
  },
  "forecast": [
    {
      "date": "2026-06-07",
      "temp_min": 18,
      "temp_max": 25,
      "precipitation": 0.2,
      "condition": "Rainy",
      "wind_speed": 15
    }
  ],
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "name": "San Francisco, USA"
  }
}
```

**Errors:**
- `400` - Invalid coordinates
- `502` - External API error
- `503` - Service temporarily unavailable

---

### Get Weather Usage

**Endpoint:** `GET /api/v1/weather/usage`

**Description:** Get API usage statistics

**Authentication:** Not required

**Response (200):**
```json
{
  "requests_today": 145,
  "requests_limit": 1000,
  "requests_used_percent": 14.5,
  "reset_time": "2026-06-07T00:00:00Z"
}
```

---

## Alert Endpoints

### List Alerts

**Endpoint:** `GET /api/v1/alerts`

**Description:** Get all alerts for authenticated user

**Authentication:** Required

**Query Parameters:**
- `status` (string, optional) - Filter: triggered, acknowledged, resolved
- `skip` (int, default: 0) - Records to skip
- `limit` (int, default: 100) - Records to return

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "rule_id": "550e8400-e29b-41d4-a716-446655440004",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "triggered",
    "message": "Temperature exceeded 30°C",
    "triggered_at": "2026-06-06T14:30:00Z",
    "acknowledged_at": null,
    "resolved_at": null
  }
]
```

---

### Get Alert

**Endpoint:** `GET /api/v1/alerts/{alert_id}`

**Description:** Get alert details

**Authentication:** Required

**Path Parameters:**
- `alert_id` (UUID) - Alert ID

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "rule_id": "550e8400-e29b-41d4-a716-446655440004",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "triggered",
  "message": "Temperature exceeded 30°C",
  "triggered_at": "2026-06-06T14:30:00Z",
  "acknowledged_at": null,
  "resolved_at": null
}
```

---

### Update Alert Status

**Endpoint:** `PUT /api/v1/alerts/{alert_id}`

**Description:** Update alert status (acknowledge/resolve)

**Authentication:** Required

**Path Parameters:**
- `alert_id` (UUID) - Alert ID

**Request Body:**
```json
{
  "status": "acknowledged"
}
```

Valid statuses: `triggered`, `acknowledged`, `resolved`

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "acknowledged",
  "acknowledged_at": "2026-06-06T15:00:00Z"
}
```

---

## Rule Endpoints

### List Rules for Location

**Endpoint:** `GET /api/v1/rules/location/{location_id}`

**Description:** Get all rules for a specific location

**Authentication:** Required

**Path Parameters:**
- `location_id` (UUID) - Location ID

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "location_id": "550e8400-e29b-41d4-a716-446655440002",
    "condition_type": "temperature",
    "threshold_value": 30.0,
    "operator": ">",
    "is_active": true,
    "created_at": "2026-06-06T12:34:56Z"
  }
]
```

---

### Create Rule

**Endpoint:** `POST /api/v1/rules`

**Description:** Create a new alert rule

**Authentication:** Required

**Request Body:**
```json
{
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "condition_type": "temperature",
  "threshold_value": 32.0,
  "operator": ">"
}
```

**Condition Types:**
- `temperature` - Temperature threshold
- `humidity` - Humidity percentage
- `precipitation` - Rainfall amount
- `wind_speed` - Wind speed threshold

**Operators:**
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `==` - Equal to

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "location_id": "550e8400-e29b-41d4-a716-446655440002",
  "condition_type": "temperature",
  "threshold_value": 32.0,
  "operator": ">",
  "is_active": true,
  "created_at": "2026-06-06T15:10:00Z"
}
```

---

### Update Rule

**Endpoint:** `PUT /api/v1/rules/{rule_id}`

**Description:** Update rule configuration

**Authentication:** Required

**Path Parameters:**
- `rule_id` (UUID) - Rule ID

**Request Body:**
```json
{
  "threshold_value": 35.0,
  "is_active": false
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "threshold_value": 35.0,
  "is_active": false
}
```

---

### Delete Rule

**Endpoint:** `DELETE /api/v1/rules/{rule_id}`

**Description:** Delete a rule

**Authentication:** Required

**Path Parameters:**
- `rule_id` (UUID) - Rule ID

**Response (204):** No content

---

## Health Endpoint

### Health Check

**Endpoint:** `GET /api/v1/health`

**Description:** Check API and service health

**Authentication:** Not required

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```

---

## Rate Limiting

Rate limiting is applied per user:
- **Limit:** 100 requests per 5 minutes
- **Headers:**
  - `X-RateLimit-Limit` - Total allowed requests
  - `X-RateLimit-Remaining` - Requests remaining
  - `X-RateLimit-Reset` - Unix timestamp when limit resets

**Response (429) - Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again after 300 seconds."
}
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `skip` - Number of records to skip (default: 0)
- `limit` - Number of records to return (default: 100, max: 1000)

**Example:**
```bash
GET /api/v1/locations?skip=20&limit=50
```

---

## Interactive API Documentation

Access Swagger UI and ReDoc documentation:
- **Swagger UI:** `GET /docs`
- **ReDoc:** `GET /redoc`
- **OpenAPI Schema:** `GET /openapi.json`

---

## Example API Usage

### Complete Workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Response: {"access_token":"...","token_type":"bearer"}

# 3. Create Location
curl -X POST http://localhost:8000/api/v1/locations \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"San Francisco",
    "latitude":37.7749,
    "longitude":-122.4194,
    "description":"Office"
  }'

# Response: {"id":"...","name":"San Francisco",...}

# 4. Get Weather
curl -X GET "http://localhost:8000/api/v1/weather?lat=37.7749&lon=-122.4194&days=7"

# 5. Create Rule
curl -X POST http://localhost:8000/api/v1/rules \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id":"<location_id>",
    "condition_type":"temperature",
    "threshold_value":30.0,
    "operator":">"
  }'

# 6. List Alerts
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer <access_token>"
```

---

## Support

For API issues or questions:
- Check `/docs` for interactive documentation
- Review error responses for specific details
- Check service health at `/api/v1/health`
