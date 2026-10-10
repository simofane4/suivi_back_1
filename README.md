# Suivi Cabinet - Clinic Management Backend API

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Django](https://img.shields.io/badge/Django-6.0.2-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive Django REST Framework backend for clinic management: multi-tenant clinics, staff management, patient records, appointment scheduling, prescriptions, and billing.

## Features

### ✨ Core Capabilities

- **Multi-Tenant Architecture**: Complete cabinet (clinic) isolation with secure tenancy scoping
- **Staff Management**: Doctor and assistant profiles with JWT authentication and role-based access
- **Patient Records**: Secure patient database with per-cabinet CIN/phone uniqueness
- **Appointment Scheduling**: Conflict-free booking with overlap detection and time slot validation
- **Prescriptions**: Detailed ordonnances (prescriptions) with medication tracking and dosage/duration
- **Billing**: Invoice generation, payment tracking, and unpaid invoice filtering
- **Medical Procedures**: Customizable catalog of requested and completed procedures per clinic
- **File Management**: Patient document uploads (PDFs, images) with secure access control
- **API Documentation**: Interactive Swagger UI and ReDoc with OpenAPI 3.0 schema

### 🔐 Security & Compliance

- **JWT Authentication**: Stateless token-based authentication with role and cabinet claims
- **Cabinet Scoping**: Automatic queryset filtering ensures users only see their clinic's data
- **Permission Classes**: Fine-grained role-based controls (Admin, Doctor, Assistant)
- **Input Validation**: Comprehensive field and serializer-level validation
- **CORS Support**: Configurable cross-origin requests for frontend integration
- **Password Security**: Django password validators with strength requirements

### 🏗️ Architecture

- **DRF ViewSets**: StandardModelViewSet with custom CabinetScopedViewSet for multi-tenancy
- **Custom Serializers**: Separate Create/Update serializers for complex logic with transactions
- **Service Layer**: Clinical services for business logic (e.g., appointment overlap detection)
- **Transaction Safety**: `@transaction.atomic` decorators on multi-step operations
- **Comprehensive Logging**: Structured logging with INFO/WARNING levels and handlers

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Runtime |
| **Django** | 6.0.2 | Web framework |
| **DRF** | 3.18.1 | REST API |
| **simplejwt** | 5.5.1 | JWT authentication |
| **drf-spectacular** | 0.30.0 | OpenAPI/Swagger docs |
| **Pillow** | 12.3.0 | Image processing |
| **django-filter** | 26.1 | Query filtering |
| **django-cors-headers** | 4.9.0 | CORS support |
| **python-dotenv** | 1.2.4 | Environment variables |
| **SQLite/PostgreSQL** | Latest | Database (SQLite dev, PostgreSQL prod) |

**Development Tools**:
pytest, pytest-django, factory-boy, black, ruff, mypy, django-stubs, pre-commit, coverage

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/suivi_back_1.git
   cd suivi_back_1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (especially DJANGO_SECRET_KEY for production)
   ```

5. **Initialize database**
   ```bash
   python manage.py migrate
   ```

6. **Load demo data (optional)**
   ```bash
   python manage.py seed_demo
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

   Server runs at: http://localhost:8000
   - API: http://localhost:8000/api/
   - Swagger Docs: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/redoc/
   - Admin: http://localhost:8000/admin/

### Demo Credentials

After running `seed_demo`:

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `admin12345` |
| **Doctor** | `demo_doc_1_1` | `demo12345` |
| **Assistant** | `demo_ast_1_1` | `demo12345` |

## API Quick Reference

### Authentication

```bash
# Obtain JWT tokens
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "doctor1", "password": "password123"}'

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Use token in requests
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/patients/
```

### Create Doctor

```bash
curl -X POST http://localhost:8000/api/doctors/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "password": "SecurePass123!",
    "email": "smith@clinic.local",
    "first_name": "John",
    "last_name": "Smith",
    "cabinet": 1,
    "inp": "INP00123456",
    "gender": "Male",
    "phone": "+212 6 12 34 56 78",
    "specialiste": 1
  }'
```

### Book Appointment

```bash
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cabinet": 1,
    "patient": 5,
    "doctor": 2,
    "start": "2026-10-15T09:00:00Z",
    "end": "2026-10-15T10:00:00Z",
    "reason": "Regular checkup"
  }'
```

### Create Invoice

```bash
curl -X POST http://localhost:8000/api/invoices/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "appointment": 10,
    "amount": "5000.00",
    "payed": false
  }'
```

## Development Workflow

### Code Quality

```bash
# Run all linting checks
ruff check .
black --check .
mypy .

# Auto-fix issues
ruff check . --fix
black .

# Pre-commit hooks (install once)
pre-commit install
pre-commit run --all-files
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_accounts.py

# Run only unit tests (exclude integration/slow)
pytest -m "not slow and not integration"

# Run with verbose output
pytest -v

# Run with debugging (drop into pdb on failures)
pytest --pdb
```

### Database Migrations

```bash
# Create new migration
python manage.py makemigrations accounts

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Reverse migration
python manage.py migrate accounts 0001
```

### Demo Data

```bash
# Load initial demo data
python manage.py seed_demo

# Reload with different parameters
python manage.py seed_demo --cabinets 5 --patients-per-cabinet 20

# Flush and reload
python manage.py seed_demo --flush
```

## Project Structure

```
suivi_back_1/
├── suivi_back/              # Main project settings
│   ├── settings/
│   │   ├── base.py         # Shared configuration
│   │   ├── dev.py          # Development overrides
│   │   └── prod.py         # Production overrides
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI application
│   └── asgi.py             # ASGI application
├── accounts/               # Staff authentication & profiles
│   ├── models.py           # Doctor, Assistant
│   ├── serializers.py      # API serializers
│   ├── views.py            # ViewSets and auth endpoints
│   └── urls.py             # URLs
├── cabinets/               # Multi-tenant clinic management
│   ├── models.py           # Cabinet, Specialite
│   └── management/
│       └── commands/
│           └── seed_demo.py  # Demo data generator
├── patients/               # Patient records
│   ├── models.py           # Patient, PatientFile
│   └── serializers.py      # Patient serializers
├── clinical/               # Appointments & prescriptions
│   ├── models.py           # Appointment, Ordonnance, etc
│   ├── services.py         # Business logic
│   └── serializers.py      # Clinical serializers
├── billing/                # Invoicing
│   ├── models.py           # Invoice
│   └── serializers.py      # Invoice serializers
├── common/                 # Shared utilities
│   ├── models.py           # TimeStampedModel base
│   ├── permissions.py      # Permission classes
│   ├── tenancy.py          # Cabinet scoping
│   ├── exceptions.py       # Custom error handling
│   ├── pagination.py       # API pagination
│   └── constants.py        # Shared constants
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── factories.py        # Test data factories
│   ├── test_accounts.py    # Auth & staff tests
│   ├── test_patients.py    # Patient CRUD tests
│   ├── test_clinical.py    # Appointment tests
│   ├── test_billing.py     # Invoice tests
│   └── test_permissions.py # Multi-tenancy tests
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pytest.ini              # Pytest configuration
├── ruff.toml               # Linting configuration
├── pyproject.toml          # Project metadata & tool config
├── mypy.ini                # Type checking configuration
├── .pre-commit-config.yaml # Git pre-commit hooks
└── README.md               # This file
```

## Configuration & Environment Variables

Create a `.env` file from `.env.example`:

```dotenv
# Django
DJANGO_SETTINGS_MODULE=suivi_back.settings.dev
DJANGO_SECRET_KEY=generate-a-random-50-char-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:4200

# Database
DJANGO_DB_PATH=db.sqlite3  # Optional, defaults to BASE_DIR/db.sqlite3

# Timezone & Localization
DJANGO_TIME_ZONE=Africa/Casablanca
DJANGO_LANGUAGE_CODE=fr

# JWT
JWT_ACCESS_TOKEN_LIFETIME=30    # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440 # minutes (24 hours)
```

**Production Variables** (for `.env.prod`):
```dotenv
DJANGO_SETTINGS_MODULE=suivi_back.settings.prod
DJANGO_SECRET_KEY=<generate-50-char-random>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/suivi_db
```

## API Endpoints

See [API.md](API.md) for detailed endpoint reference with examples.

### Overview

| Resource | Method | Endpoint |
|----------|--------|----------|
| **Auth** | POST | `/api/auth/token/` |
| | POST | `/api/auth/token/refresh/` |
| | GET | `/api/auth/me/` |
| **Doctors** | GET, POST | `/api/doctors/` |
| | GET, PATCH, DELETE | `/api/doctors/{id}/` |
| **Assistants** | GET, POST | `/api/assistants/` |
| | GET, PATCH, DELETE | `/api/assistants/{id}/` |
| **Patients** | GET, POST | `/api/patients/` |
| | GET, PATCH, DELETE | `/api/patients/{id}/` |
| **Appointments** | GET, POST | `/api/appointments/` |
| | GET, PATCH, DELETE | `/api/appointments/{id}/` |
| | POST | `/api/appointments/{id}/cancel/` |
| **Prescriptions** | GET, POST | `/api/ordonnances/` |
| | GET, PATCH, DELETE | `/api/ordonnances/{id}/` |
| **Invoices** | GET, POST | `/api/invoices/` |
| | GET, PATCH, DELETE | `/api/invoices/{id}/` |
| | GET | `/api/invoices/unpaid/` |

## Docker (Production)

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker setup instructions.

```bash
# Build image
docker build -t suivi-back:latest .

# Run with docker-compose
docker-compose -f docker-compose.yml up -d

# Access logs
docker-compose logs -f web
```

## Testing & Coverage

The project aims for **70%+ test coverage**:

```bash
# Run tests with coverage report
pytest --cov=. --cov-report=html

# View coverage
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

Test categories:
- **Unit Tests**: Individual function/method tests (60+ tests)
- **Integration Tests**: Multi-component workflows (40+ tests)
- **Permission Tests**: Multi-tenancy and RBAC validation (20+ tests)

## Security Considerations

- ✅ **HTTPS Required** in production (`SECURE_SSL_REDIRECT=True`)
- ✅ **HSTS Headers** enabled in prod
- ✅ **CSRF Protection** via middleware
- ✅ **Password Validation** enforced
- ✅ **Secure Cookies** with HttpOnly, Secure, SameSite flags
- ⚠️ **Change Default Admin**: Remove default admin user in production
- ⚠️ **Rotate Keys**: Regularly rotate `DJANGO_SECRET_KEY`
- ⚠️ **Database Backups**: Implement automated backup strategy

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment checklist and best practices.

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Generate strong `DJANGO_SECRET_KEY`
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set `ALLOWED_HOSTS` to domain names
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS for frontend domain
- [ ] Set up monitoring and logging
- [ ] Implement automated backups
- [ ] Test disaster recovery plan

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and run tests: `pytest`
3. Run code quality checks: `ruff check . && black . && mypy .`
4. Commit with clear message: `git commit -am "feat: add new feature"`
5. Push and create Pull Request

## License

MIT License - see LICENSE file for details

## Support & Documentation

- **Architecture Guide**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: See [API.md](API.md)
- **Development Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Interactive Docs**: http://localhost:8000/api/docs/

## Authors

- Development Team @ Clinic Management Project

## Changelog

### v2.0.0 (2026-10-02)
- ✨ Complete API refactor with DRF best practices
- ✨ Multi-tenant cabinet scoping
- ✨ JWT authentication with role-based access
- ✨ Comprehensive test suite (120+ tests, 70%+ coverage)
- ✨ Docker containerization
- ✨ GitHub Actions CI/CD
- ✨ Code quality tools (black, ruff, mypy)
- 🐛 Fix serializer field name inconsistencies
- 📚 Add comprehensive documentation

---

**Last Updated**: October 2, 2026  
**Status**: Active Development
