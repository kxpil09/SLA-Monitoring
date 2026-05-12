# SLA Monitor
Real-time uptime and latency monitoring platform with automated email alerting.

## Features
- ⚡ Real-time monitoring (2-minute intervals)
- 📊 Historical uptime tracking and latency metrics
- 🚨 Smart email alerts (DOWN/UP/Recovery)
- 📈 Visual dashboards with charts
- 🔄 Database migrations with Alembic
- ✅ Comprehensive test coverage
- 🐳 Fully containerized with Docker

## Stack
FastAPI · React · PostgreSQL · Redis · Celery · Docker

## Architecture
```
React Frontend ──▶ FastAPI API ──▶ PostgreSQL
                       │
                       ▼
                    Redis ──▶ Celery Worker + Beat ──▶ Email Alerts
```

## Quick Start

### 1. Setup
```bash
git clone <repo-url>
cd sla-monitoring
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run
```bash
docker compose up --build
```

### 3. Access
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Configuration (.env)

```bash
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sla_monitor

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Email Alerts
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourdomain.com
ALERT_TO_EMAILS=admin@yourdomain.com,team@yourdomain.com
```

### Gmail Setup
1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in `SMTP_PASSWORD`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/services` | Create service |
| GET | `/api/v1/services` | List services |
| GET | `/api/v1/services/{id}` | Get service |
| DELETE | `/api/v1/services/{id}` | Delete service |
| GET | `/api/v1/services/{id}/history` | Check history |
| GET | `/api/v1/alerts/settings` | Alert settings |
| GET | `/api/v1/alerts/recipients` | Get recipients |
| POST | `/api/v1/alerts/recipients` | Update recipients |
| POST | `/api/v1/alerts/test` | Send test alert |

## Development

### Run Tests
```bash
pip install -r requirements-docker.txt
pytest --cov=app --cov-report=html
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Alert Logic

- **Service Down**: Immediate alert on first failure
- **Still Down**: Reminder every 5 consecutive failures
- **Service Recovered**: Alert when back online

## Project Structure

```
sla-monitoring/
├── app/                    # FastAPI backend
│   ├── main.py            # App entry
│   ├── models.py          # Database models
│   ├── routes.py          # Service endpoints
│   ├── alert_routes.py    # Alert endpoints
│   ├── health_checks.py   # Monitoring logic
│   ├── alerts.py          # Email system
│   ├── tasks.py           # Celery tasks
│   └── config.py          # Settings
├── frontend/              # React frontend
│   └── src/App.jsx        # Main component
├── tests/                 # Test suite
├── alembic/               # DB migrations
├── docker-compose.yml     # Container orchestration
└── Dockerfile             # Backend image
```

## Common Commands

```bash
# Start services
docker compose up --build

# View logs
docker compose logs -f api worker

# Stop services
docker compose down

# Clean everything
docker compose down -v

# Run tests
pytest

# Database shell
docker exec -it sla_postgres psql -U kapil -d sla_monitor
```

## License
MIT
