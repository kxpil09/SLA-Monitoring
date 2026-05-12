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
- ☁️ AWS Free Tier deployment ready

## Stack
FastAPI · React · PostgreSQL · Redis · Celery · Docker · AWS

## Architecture
```
React Frontend (S3 + CloudFront) ──▶ FastAPI API (EC2) ──▶ PostgreSQL (RDS)
                                            │
                                            ▼
                                         Redis ──▶ Celery Worker + Beat ──▶ Email Alerts
```

## Quick Start (Local Development)

### 1. Setup
```bash
git clone https://github.com/kxpil09/SLA-Monitoring.git
cd SLA-Monitoring
cp .env.example .env
# Edit .env with your credentials
```

### 2. Run with Docker
```bash
docker compose up --build
```

### 3. Access
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## AWS Deployment (Free Tier)

### Prerequisites
- AWS Account with Free Tier
- AWS CLI installed and configured
- SSH client

### Quick Deploy
```bash
# 1. Follow AWS_DEPLOYMENT.md for detailed steps
# 2. Or use automated script on EC2:
git clone https://github.com/kxpil09/SLA-Monitoring.git
cd SLA-Monitoring
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### Architecture on AWS
- **Frontend**: S3 + CloudFront (Static hosting)
- **Backend**: EC2 t2.micro (Ubuntu 22.04)
- **Database**: RDS PostgreSQL db.t3.micro
- **Cache**: Redis (Docker on EC2)
- **Workers**: Celery (on EC2)

**Cost**: $0/month for 12 months (Free Tier)

📖 **Full Guide**: See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)

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
├── deployment/            # AWS deployment files
│   ├── deploy.sh          # Automated deployment script
│   ├── sla-api.service    # Systemd service files
│   └── nginx-*.conf       # Nginx configuration
├── tests/                 # Test suite
├── alembic/               # DB migrations
├── docker-compose.yml     # Local development
└── AWS_DEPLOYMENT.md      # AWS deployment guide
```

## Common Commands

### Local Development
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

### AWS Production
```bash
# SSH into EC2
ssh -i sla-monitor-key.pem ubuntu@YOUR_EC2_IP

# Check service status
sudo systemctl status sla-api sla-worker sla-beat

# View logs
sudo tail -f /var/log/sla-api-error.log

# Restart services
sudo systemctl restart sla-api sla-worker sla-beat

# Update code
cd ~/SLA-Monitoring && git pull && sudo systemctl restart sla-api sla-worker sla-beat
```

## Monitoring & Logs

### Local (Docker)
```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f beat
```

### AWS (EC2)
```bash
sudo tail -f /var/log/sla-api-error.log
sudo tail -f /var/log/sla-worker.log
sudo tail -f /var/log/sla-beat.log
```

## Troubleshooting

### Local Development
- **Database connection failed**: Check if PostgreSQL container is running
- **Redis connection failed**: Check if Redis container is running
- **Frontend can't reach API**: Verify `VITE_API_URL` in `frontend/.env`

### AWS Production
- **API not responding**: Check `sudo systemctl status sla-api`
- **Celery not running checks**: Check `sudo systemctl status sla-worker sla-beat`
- **Database connection failed**: Verify RDS security group allows EC2 access

📖 **Full Troubleshooting Guide**: See [deployment/QUICK_REFERENCE.md](./deployment/QUICK_REFERENCE.md)

## License
MIT

## Author
Kapil - [GitHub](https://github.com/kxpil09)

## Live Demo
- Frontend: [Your CloudFront URL]
- API Docs: [Your EC2 URL]/docs
- GitHub: https://github.com/kxpil09/SLA-Monitoring
