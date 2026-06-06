# WeatherOps System Diagrams

## 1. Use Case Diagram

```mermaid
graph TB
    User["👤 User"]
    Admin["👤 Admin"]
    WeatherAPI["🌐 WeatherAI API"]
    EmailService["📧 Email Service"]
    SMSService["📱 SMS Service"]
    
    User -->|Register| AuthUC["Authentication"]
    User -->|Manage| LocationUC["Location Management"]
    User -->|Monitor| WeatherUC["Weather Monitoring"]
    User -->|Create| RuleUC["Rule Definition"]
    User -->|View| AlertUC["Alert Management"]
    User -->|Configure| PreferenceUC["Preferences"]
    
    WeatherUC -->|Fetch Data| WeatherAPI
    AlertUC -->|Send via| EmailService
    AlertUC -->|Send via| SMSService
    AlertUC -->|Send via| WebhookUC["Webhook Notifications"]
    
    Admin -->|Monitor| SystemUC["System Monitoring"]
    Admin -->|Manage| UserUC["User Management"]
    
    style User fill:#e1f5ff
    style Admin fill:#fff3e0
    style WeatherAPI fill:#c8e6c9
    style EmailService fill:#f8bbd0
    style SMSService fill:#f8bbd0
```

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ LOCATIONS : creates
    USERS ||--o{ ALERTS : receives
    USERS ||--o{ RULES : defines
    USERS ||--o{ REFRESH_TOKENS : has
    USERS ||--o{ USER_PREFERENCES : has
    LOCATIONS ||--o{ RULES : "associated with"
    RULES ||--o{ ALERTS : triggers
    
    USERS {
        uuid id PK
        string email UK
        string hashed_password
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    LOCATIONS {
        uuid id PK
        uuid user_id FK
        string name
        float latitude
        float longitude
        string description
        datetime created_at
        datetime updated_at
    }
    
    RULES {
        uuid id PK
        uuid location_id FK
        string condition_type
        float threshold_value
        string operator
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    ALERTS {
        uuid id PK
        uuid rule_id FK
        uuid user_id FK
        string alert_type
        string status
        text message
        datetime triggered_at
        datetime acknowledged_at
        datetime resolved_at
    }
    
    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        string token
        datetime expires_at
        datetime created_at
    }
    
    USER_PREFERENCES {
        uuid id PK
        uuid user_id FK
        string preference_key
        string preference_value
        datetime updated_at
    }
```

## 3. Class Diagram

```mermaid
classDiagram
    class User {
        +UUID id
        +string email
        +string hashed_password
        +boolean is_active
        +datetime created_at
        +datetime updated_at
        +register()
        +verify_password()
        +set_password()
    }
    
    class Location {
        +UUID id
        +UUID user_id
        +string name
        +float latitude
        +float longitude
        +string description
        +create_location()
        +update_location()
        +delete_location()
    }
    
    class Rule {
        +UUID id
        +UUID location_id
        +string condition_type
        +float threshold_value
        +string operator
        +boolean is_active
        +evaluate()
        +execute()
    }
    
    class Alert {
        +UUID id
        +UUID rule_id
        +UUID user_id
        +string alert_type
        +string status
        +text message
        +datetime triggered_at
        +trigger_alert()
        +acknowledge()
        +resolve()
    }
    
    class Weather {
        +float temperature
        +float humidity
        +float precipitation
        +float wind_speed
        +string condition
        +get_weather()
        +parse_response()
    }
    
    class RefreshToken {
        +UUID id
        +UUID user_id
        +string token
        +datetime expires_at
        +is_valid()
        +revoke()
    }
    
    class AuthService {
        +register_user()
        +authenticate_user()
        +create_tokens()
        +refresh_access_token()
        +verify_token()
    }
    
    class WeatherService {
        +get_weather()
        +get_forecast()
        +get_usage()
        +fetch_from_api()
    }
    
    class RuleEngine {
        +evaluate_rules()
        +check_condition()
        +trigger_alert()
        +execute_actions()
    }
    
    class NotificationService {
        +send_email()
        +send_sms()
        +send_webhook()
        +queue_notification()
    }
    
    User "1" --> "*" Location : owns
    User "1" --> "*" Alert : receives
    User "1" --> "*" Rule : defines
    Location "1" --> "*" Rule : has
    Rule "1" --> "*" Alert : triggers
    User "1" --> "*" RefreshToken : has
    AuthService --> User : manages
    WeatherService --> Weather : fetches
    RuleEngine --> Rule : evaluates
    RuleEngine --> Alert : triggers
    NotificationService --> Alert : notifies
```

## 4. Sequence Diagram: User Registration & Authentication

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant AuthService as Auth Service
    participant DB as PostgreSQL
    participant JWT as JWT Handler
    
    User->>API: POST /auth/register
    activate API
    API->>AuthService: register_user(email, password)
    activate AuthService
    AuthService->>AuthService: hash_password(password)
    AuthService->>DB: create_user(email, hashed_pwd)
    activate DB
    DB-->>AuthService: user_created
    deactivate DB
    AuthService-->>API: user
    deactivate AuthService
    API-->>User: 201 User Created
    deactivate API
    
    User->>API: POST /auth/login
    activate API
    API->>AuthService: authenticate_user(email, password)
    activate AuthService
    AuthService->>DB: get_user(email)
    activate DB
    DB-->>AuthService: user
    deactivate DB
    AuthService->>AuthService: verify_password(pwd, hash)
    AuthService->>JWT: create_tokens(user_id)
    activate JWT
    JWT-->>AuthService: access_token, refresh_token
    deactivate JWT
    AuthService-->>API: tokens
    deactivate AuthService
    API-->>User: 200 {access_token, refresh_token}
    deactivate API
```

## 5. Sequence Diagram: Weather Monitoring & Alert Triggering

```mermaid
sequenceDiagram
    participant Celery as Celery Beat
    participant WeatherService as Weather Service
    participant RuleEngine as Rule Engine
    participant WeatherAPI as WeatherAI API
    participant DB as PostgreSQL
    participant NotificationService as Notification Service
    participant Redis as Redis Cache
    
    Celery->>WeatherService: monitor_weather()
    activate WeatherService
    WeatherService->>Redis: check_cache(location_id)
    activate Redis
    Redis-->>WeatherService: cached_data or null
    deactivate Redis
    
    alt Cache Miss
        WeatherService->>WeatherAPI: fetch_weather(lat, lon)
        activate WeatherAPI
        WeatherAPI-->>WeatherService: weather_data
        deactivate WeatherAPI
        WeatherService->>Redis: cache(location_id, data)
    else Cache Hit
        WeatherService->>WeatherService: use_cached_data()
    end
    
    WeatherService->>DB: get_rules(location_id)
    activate DB
    DB-->>WeatherService: rules
    deactivate DB
    
    WeatherService->>RuleEngine: evaluate_rules(weather, rules)
    activate RuleEngine
    RuleEngine->>RuleEngine: check_conditions()
    RuleEngine->>DB: create_alert(rule_id, user_id)
    activate DB
    DB-->>RuleEngine: alert
    deactivate DB
    RuleEngine-->>WeatherService: alerts
    deactivate RuleEngine
    
    WeatherService->>NotificationService: send_notifications(alerts)
    activate NotificationService
    NotificationService->>NotificationService: queue_tasks()
    NotificationService-->>WeatherService: queued
    deactivate NotificationService
    deactivate WeatherService
```

## 6. State Diagram: Alert Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending
    
    Pending --> Triggered: Rule conditions met
    Pending --> Cancelled: Rule disabled
    
    Triggered --> Acknowledged: User acknowledges
    Triggered --> Expired: Time limit exceeded
    Triggered --> Resolved: Conditions no longer met
    
    Acknowledged --> Resolved: Issue fixed
    Acknowledged --> Triggered: Conditions recur
    Acknowledged --> Expired: Time limit exceeded
    
    Resolved --> [*]
    Expired --> [*]
    Cancelled --> [*]
    
    note right of Pending
        Waiting for rule
        conditions to trigger
    end note
    
    note right of Triggered
        Alert actively
        notifying user
    end note
    
    note right of Acknowledged
        User confirmed
        receipt of alert
    end note
    
    note right of Resolved
        Issue resolved,
        alert completed
    end note
```

## 7. Activity Diagram: Rule Evaluation Flow

```mermaid
graph TD
    A["Start"] --> B["Get All Active Rules"]
    B --> C{"For Each Rule"}
    C -->|Rule Loop| D["Get Rule Conditions"]
    D --> E["Fetch Current Weather"]
    E --> F{"Evaluate Condition"}
    F -->|Condition Met| G["Create Alert"]
    F -->|Condition Not Met| H["Skip Alert"]
    G --> I["Queue Notification Task"]
    H --> J{"More Rules?"}
    I --> J
    J -->|Yes| C
    J -->|No| K["Save Execution Log"]
    K --> L["End"]
    
    style A fill:#90EE90
    style L fill:#FFB6C6
    style G fill:#FFD700
    style I fill:#87CEEB
```

## 8. Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Web["Web Client"]
        Mobile["Mobile Client"]
    end
    
    subgraph "API Layer"
        FastAPI["FastAPI Server"]
        AuthMiddleware["Auth Middleware"]
        CORSMiddleware["CORS Middleware"]
    end
    
    subgraph "Business Logic"
        AuthService["Auth Service"]
        WeatherService["Weather Service"]
        RuleEngine["Rule Engine"]
        NotificationService["Notification Service"]
        LocationService["Location Service"]
    end
    
    subgraph "Data Access"
        UserRepo["User Repository"]
        LocationRepo["Location Repository"]
        RuleRepo["Rule Repository"]
        AlertRepo["Alert Repository"]
    end
    
    subgraph "External Services"
        WeatherAPI["WeatherAI API"]
        EmailService["SendGrid Email"]
        SMSService["Twilio SMS"]
        WebhookService["Webhook Service"]
    end
    
    subgraph "Infrastructure"
        PostgreSQL["PostgreSQL DB"]
        Redis["Redis Cache"]
        CeleryWorker["Celery Worker"]
        CeleryBeat["Celery Beat"]
    end
    
    Web --> FastAPI
    Mobile --> FastAPI
    
    FastAPI --> AuthMiddleware
    FastAPI --> CORSMiddleware
    FastAPI --> AuthService
    FastAPI --> WeatherService
    FastAPI --> LocationService
    FastAPI --> RuleEngine
    
    AuthService --> UserRepo
    WeatherService --> LocationRepo
    RuleEngine --> RuleRepo
    RuleEngine --> AlertRepo
    LocationService --> LocationRepo
    
    UserRepo --> PostgreSQL
    LocationRepo --> PostgreSQL
    RuleRepo --> PostgreSQL
    AlertRepo --> PostgreSQL
    
    WeatherService --> Redis
    WeatherService --> WeatherAPI
    
    RuleEngine --> CeleryWorker
    NotificationService --> CeleryWorker
    
    CeleryWorker --> Redis
    CeleryBeat --> Redis
    
    NotificationService --> EmailService
    NotificationService --> SMSService
    NotificationService --> WebhookService
    
    style FastAPI fill:#4CAF50,color:#fff
    style PostgreSQL fill:#2196F3,color:#fff
    style Redis fill:#FF9800,color:#fff
    style CeleryWorker fill:#9C27B0,color:#fff
    style CeleryBeat fill:#9C27B0,color:#fff
```

## 9. Data Flow Diagram

```mermaid
graph LR
    User["User"]
    API["FastAPI API"]
    Cache["Redis Cache"]
    DB["PostgreSQL"]
    Queue["Celery Queue"]
    Worker["Celery Worker"]
    ExternalAPI["External APIs"]
    Notifications["Notifications"]
    
    User -->|API Request| API
    API -->|Query/Write| DB
    API -->|Cache Check| Cache
    API -->|Async Task| Queue
    
    Queue -->|Task Execution| Worker
    Worker -->|Fetch Data| ExternalAPI
    Worker -->|Store Results| DB
    Worker -->|Queue Notification| Queue
    
    Queue -->|Notification Task| Worker
    Worker -->|Send Alert| Notifications
    Notifications -->|Email/SMS/Webhook| User
    
    ExternalAPI -->|Weather Data| Cache
    Cache -->|Cached Response| API
    
    DB -->|User Data| API
    API -->|JSON Response| User
    
    style User fill:#E3F2FD
    style API fill:#4CAF50,color:#fff
    style DB fill:#2196F3,color:#fff
    style Cache fill:#FF9800,color:#fff
    style Queue fill:#9C27B0,color:#fff
    style Worker fill:#9C27B0,color:#fff
    style ExternalAPI fill:#F44336,color:#fff
    style Notifications fill:#FFC107,color:#000
```

## 10. Deployment Architecture Diagram

```mermaid
graph TB
    subgraph "Render Platform"
        subgraph "Web Service"
            WEB["Uvicorn Server<br/>App Port: 8000"]
        end
        
        subgraph "Background Services"
            WORKER["Celery Worker"]
            BEAT["Celery Beat<br/>Scheduler"]
        end
        
        subgraph "Data Services"
            POSTGRES["PostgreSQL<br/>Database"]
            REDIS["Redis<br/>Cache & Broker"]
        end
    end
    
    subgraph "External Services"
        WEATHER["WeatherAI API"]
        SENDGRID["SendGrid<br/>Email"]
        TWILIO["Twilio<br/>SMS"]
    end
    
    subgraph "Client"
        CLIENT["Web/Mobile<br/>Client"]
    end
    
    CLIENT -->|HTTPS| WEB
    WEB -->|SQL| POSTGRES
    WEB -->|Cache/Queue| REDIS
    
    BEAT -->|Schedule| WORKER
    WORKER -->|Query| POSTGRES
    WORKER -->|Queue| REDIS
    WORKER -->|API Call| WEATHER
    WORKER -->|Send Email| SENDGRID
    WORKER -->|Send SMS| TWILIO
    
    WEB -->|API Call| WEATHER
    WEB -->|Read| REDIS
    
    style WEB fill:#4CAF50,color:#fff
    style WORKER fill:#9C27B0,color:#fff
    style BEAT fill:#9C27B0,color:#fff
    style POSTGRES fill:#2196F3,color:#fff
    style REDIS fill:#FF9800,color:#fff
    style WEATHER fill:#F44336,color:#fff
    style SENDGRID fill:#FFC107,color:#000
    style TWILIO fill:#FFC107,color:#000
    style CLIENT fill:#E3F2FD
```

---

## Diagram Legend

- **Solid Arrows** → Direct synchronous communication
- **Dashed Arrows** → Asynchronous/event-driven communication
- **Blue** → Data layer (Database)
- **Orange** → Cache/Queue layer (Redis)
- **Green** → API/Web layer
- **Purple** → Background processing (Celery)
- **Red** → External services

## References

- [C4 Model](https://c4model.com/) - Component diagrams
- [UML Sequence Diagrams](https://www.omg.org/spec/UML/) - Interaction flows
- [State Machine Diagrams](https://en.wikipedia.org/wiki/State_diagram) - Process states
