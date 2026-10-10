# Architecture Guide - Suivi Cabinet

## System Overview

Suivi Cabinet is a **multi-tenant clinic management API** built with Django REST Framework. The architecture prioritizes:

1. **Multi-Tenancy**: Strict cabinet (clinic) isolation with automatic scoping
2. **Security**: JWT authentication, role-based access control, permission layers
3. **Scalability**: Stateless API design, database-driven configuration
4. **Maintainability**: Clear separation of concerns, comprehensive logging
5. **Type Safety**: Optional type annotations, mypy static checking

## High-Level Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (React/Angular)             │
└─────────────────────────────────────────────┘
                       ↕ HTTP/HTTPS
┌─────────────────────────────────────────────┐
│    Django REST Framework API Gateway         │
│  (Authentication, Routing, Versioning)      │
└─────────────────────────────────────────────┘
                       ↕
┌───────────────────────────────────────────────────────────┐
│                  Application Layer                        │
├───────────┬──────────┬──────────┬──────────┬──────────┐
│ Accounts  │ Cabinets │ Patients │ Clinical │ Billing  │
│ (Auth)    │ (Tenant) │ (Records)│ (Medical)│(Invoices)│
└───────────┴──────────┴──────────┴──────────┴──────────┘
                       ↕
┌─────────────────────────────────────────────┐
│         Common Services Layer               │
│  (Permissions, Tenancy, Validation)         │
└─────────────────────────────────────────────┘
                       ↕
┌─────────────────────────────────────────────┐
│      Database Abstraction (ORM)             │
│    (Migrations, Transactions)               │
└─────────────────────────────────────────────┘
                       ↕
┌─────────────────────────────────────────────┐
│    SQLite (Dev) / PostgreSQL (Prod)        │
└─────────────────────────────────────────────┘
```

## Multi-Tenancy Model

### Cabinet as Root Entity

Every data record belongs to a Cabinet (clinic):

```
Cabinet (Tenant)
├── Users & Staff
│   ├── Doctor (1:1 with User)
│   └── Assistant (1:1 with User)
├── Patient Data
│   ├── Patients (cin + phone unique per cabinet)
│   └── PatientFiles
├── Clinical Operations
│   ├── Appointments (doctor + patient of this cabinet)
│   ├── Ordonnances (prescriptions)
│   ├── ActeDemander (procedure catalog)
│   ├── ActeFait (completed procedures)
│   └── Medicament (medication inventory)
└── Billing
    └── Invoices
```

### Tenancy Enforcement

**Query-Level Scoping** (`CabinetScopedMixin`):

```python
class PatientViewSet(CabinetScopedViewSet):
    cabinet_field = "cabinet"  # Foreign key path
    
    def get_queryset(self):
        # Automatically filtered by CabinetScopedMixin
        # Doctor/Assistant: Returns only self.cabinet
        # Admin: Returns all
```

**Permission-Level Checks**:

```python
def validate_self, attrs):
    # Reject writes to other cabinets
    cabinet = self.context.get('cabinet')
    if cabinet and data.cabinet_id != cabinet.id:
        raise ValidationError("Not your cabinet")
```

**Database-Level Constraints**:
```sql
UNIQUE(cabinet, cin)        -- patient.cin
UNIQUE(cabinet, phone)      -- patient.phone
```

## Authentication & Authorization

### JWT Token Flow

```
1. Client: POST /api/auth/token/
           Body: { username, password }
           ↓
2. Django: Authenticate User
           Check for Doctor/Assistant/Admin roles
           ↓
3. Response: {
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi..."
}
```

### Token Payload (Enhanced Claims)

Standard JWT fields + custom claims:

```json
{
  "token_type": "access",
  "exp": 1726415234,
  "iat": 1726415234,
  "user_id": 5,
  
  "role": "doctor",              // Custom
  "cabinet_id": 1,               // Custom
  "first_name": "John",          // Custom
  "last_name": "Smith",          // Custom
  "email": "john@clinic.local"   // Custom
}
```

Frontend uses `cabinet_id` and `role` from token to route without extra API calls.

### Role-Based Access Control (RBAC)

**Roles**:
- **Admin**: Superuser, cross-cabinet visibility, staff management
- **Doctor**: Cabinet staff, can create/read appointments, prescriptions
- **Assistant**: Cabinet staff, can assist with appointments/records

**Permission Classes**:

| Class | Check |
|-------|-------|
| `IsAuthenticated` | Any logged-in user |
| `IsAdmin` | Only superusers |
| `IsDoctor` | Only user.doctor exists |
| `IsCabinetStaff` | User is doctor OR assistant |
| `IsAdminOrReadOnly` | Admin writes, others read |
| `CabinetScopedMixin` | Auto-filter to user's cabinet |

### Granular Permission Example

```python
class DoctorViewSet(CabinetScopedViewSet):
    permission_classes = (IsCabinetStaff,)  # Read: doctors+assistants
    
    def create(self, request, *args, **kwargs):
        # Only admins can create new doctors
        if not IsAdmin().has_permission(request, self):
            return Response(..., status=403)
```

## Data Models & Relationships

### ER Diagram (Simplified)

```
┌──────────────┐         ┌──────────────┐
│   Cabinet    │◄────────│  Specialite  │ (Global reference)
│              │ N:M     │              │
└──────────────┘         └──────────────┘
      ▲                         ▲
      │ 1:N                     │ 1:N
      │                         │
   ┌──┴────────┐         ┌──────┴──────┐
   │  Doctor   │         │ Medicament  │
   │   (User)  │         │              │
   └─────────────────────┴──────────────┘
      1:1              (both FK Cabinet)
   ┌──────────────┐
   │    User      │
   │ (Django)     │
   └──────────────┘
      1:1
└─────────┬────────┐
          │        │
      ┌───┴──┐  ┌──┴───┐
      │Doctor│  │Assist │
      └──────┘  └───────┘

┌──────────────┐
│   Patient    │
│  (Cabinet)   │
└──────────────┘
      1:N
   ┌──────────────┐         ┌────────────┐
   │Appointment   │────────►│ Ordonnance │
   │ (Doctor +    │░░░░░░░░░│ (Medicam   │
   │  Patient)    │   M:M   │  ents)     │
   └──────────────┘         └────────────┘
      1:1                        1:N
   ┌──────────────┐          ┌──────────────┐
   │   Invoice    │          │  PatientFile │
   │ (Recipient)  │          │  (Document)  │
   └──────────────┘          └──────────────┘
```

### Key Model Features

**TimeStampedModel (Abstract Base)**:
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

All domain models inherit this for audit trails (who created/modified).

**Transaction Safety**:

```python
@transaction.atomic
def create(self, validated_data):
    # All-or-nothing: create User + Doctor together
    user = User.objects.create_user(...)
    return Doctor.objects.create(user=user, ...)
```

**Constraints**:

```python
class Meta:
    constraints = [
        UniqueConstraint(fields=["cabinet", "cin"], name="unique_cin_per_cabinet"),
        UniqueConstraint(fields=["cabinet", "phone"], name="unique_phone_per_cabinet"),
        CheckConstraint(
            check=Q(appointment__end__gt=F("appointment__start")),
            name="end_after_start"
        ),
    ]
```

## API Design Patterns

### ViewSet Configuration Template

```python
from common.viewsets import CabinetScopedViewSet
from common.permissions import IsCabinetStaff

class MyResourceViewSet(CabinetScopedViewSet):
    """My resource description."""
    
    # Query optimization
    queryset = MyModel.objects.select_related(
        "cabinet", "user", "related_model"
    ).all()
    
    # Serializers by action
    serializer_class = MySerializer
    
    def get_serializer_class(self):
        if self.action == "create":
            return MyCreateSerializer
        if self.action in {"update", "partial_update"}:
            return MyUpdateSerializer
        return MySerializer
    
    # Permissions
    permission_classes = (IsCabinetStaff,)
    
    # Filtering & search
    filterset_fields = ("status", "cabinet", "date")
    search_fields = ("name", "description")
    ordering_fields = ("created_at", "name")
    ordering = ("-created_at",)
    
    # Custom actions
    @action(detail=True, methods=["post"])
    def custom_action(self, request, pk=None):
        obj = self.get_object()
        # ... business logic
        return Response(...)
```

### Serializer Patterns

**Read-Only (List/Detail)**:
```python
class MySerializer(serializers.ModelSerializer):
    nested_field = NestedSerializer(read_only=True)
    computed_field = serializers.SerializerMethodField()
    
    def get_computed_field(self, obj):
        return obj.related.complex_calculation()
    
    class Meta:
        model = MyModel
        fields = ("id", "name", "nested_field", "computed_field", "created_at")
        read_only_fields = ("created_at",)
```

**Creation (Atomic, User-Facing)**:
```python
class MyCreateSerializer(serializers.ModelSerializer):
    @transaction.atomic
    def create(self, validated_data):
        # Complex logic: create multiple related objects
        return MyModel.objects.create(**validated_data)
    
    def to_representation(self, instance):
        # Return read-only representation after creation
        return MySerializer(instance).data
```

**Validation**:
```python
class MySerializer(serializers.ModelSerializer):
    def validate_field(self, value):
        # Field-level validation
        if not valid(value):
            raise ValidationError("...")
        return value
    
    def validate(self, attrs):
        # Cross-field validation
        if attrs.get("start") >= attrs.get("end"):
            raise ValidationError({"end": "Must be after start"})
        return attrs
```

## Common Services Layer

### Tenancy Mixin

```python
class StaffCabinetMixin:
    """Provides cabinet resolution for views/serializers."""
    
    def get_staff_role(self):
        # "doctor" | "assistant" | "admin" | None
        user = self.request.user
        if hasattr(user, "doctor"):
            return "doctor"
        if hasattr(user, "assistant"):
            return "assistant"
        return "admin" if user.is_superuser else None
    
    def get_cabinet(self):
        # User's clinic, or None for admins
        user = self.request.user
        if hasattr(user, "doctor"):
            return user.doctor.cabinet
        if hasattr(user, "assistant"):
            return user.assistant.cabinet
        return None
```

### Business Logic Services

**Appointment Validation** (`clinical/services.py`):

```python
def validate_appointment_slot(appointment):
    """Check for overlapping bookings."""
    doctor = appointment.doctor
    start = appointment.start
    end = appointment.end
    
    conflicting = Appointment.objects.filter(
        doctor=doctor,
        cabinet=appointment.cabinet,
        start__date=start.date(),
        start__lt=end,
        end__gt=start
    ).exclude(id=appointment.id)
    
    if conflicting.exists():
        raise ValidationError(f"Conflict with {conflicting[0].start}-{conflicting[0].end}")
```

### Exception Handling

**Unified Error Response**:

```python
# common/exceptions.py
def exception_handler(exc, context):
    response = {
        "error": {
            "status": status_code,
            "code": error_code,
            "detail": "User-friendly message",
            "fields": {"field": ["error1", "error2"]}
        }
    }
    return response
```

**Usage in API**:

```bash
# 400 Validation Error
{
  "error": {
    "status": 400,
    "code": "validation_error",
    "detail": "Invalid request data",
    "fields": {
      "email": ["Email already in use"],
      "phone": ["Phone already registered"]
    }
  }
}

# 403 Permission Denied
{
  "error": {
    "status": 403,
    "code": "permission_denied",
    "detail": "You don't have permission to perform this action"
  }
}

# 404 Not Found
{
  "error": {
    "status": 404,
    "code": "not_found",
    "detail": "Resource not found or access denied"
  }
}
```

## Deployment Architecture

### Development

```
                  ┌───────────────────┐
                  │  Django Dev Server│
                  │   (runserver)     │
                  └───────────────────┘
                          ↓
                   SQLite Database
                      (db.sqlite3)
```

### Production

```
┌────────────────┐        ┌──────────────────┐
│ HTTPS Traffic  │───────►│  Nginx Reverse  │
│   (Port 443)   │        │    Proxy        │
└────────────────┘        └──────────────────┘
                                   ↓
                          ┌──────────────────┐
                          │  Gunicorn Workers│
                          │  (4 processes)   │
                          └──────────────────┘
                                   ↓
                          ┌──────────────────┐
                          │  Django App      │
                          │  (stateless)     │
                          └──────────────────┘
                                   ↓
                          ┌──────────────────┐
                          │ PostgreSQL DB    │
                          │ (production)     │
                          └──────────────────┘
```

## Database Choices

### SQLite (Development)

| Pros | Cons |
|------|------|
| Zero setup | Single-threaded writes |
| File-based (portable) | Not for high concurrency |
| Good for testing | Limited query optimization |

### PostgreSQL (Production)

| Pros | Cons |
|------|------|
| Concurrent write support | Extra services to manage |
| Advanced query optimization | Small operational overhead |
| Excellent JSON/array types | Requires docker-compose/hosting |

**Configuration Switch**:

```python
# settings/dev.py
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", ...}}

# settings/prod.py
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", ...}}
```

## Scaling Considerations

### Horizontal Scaling

1. **Stateless API**: Each request self-contained, no session affinity needed
2. **Load Balancer**: Distribute requests across multiple Gunicorn workers
3. **Shared Database**: PostgreSQL handles concurrent connections
4. **Static Files**: Serve via CDN or WhiteNoise

### Performance Optimizations

1. **Query Optimization**:
   - `select_related()` for FK joins
   - `prefetch_related()` for reverse relations
   - Database indexes on filtered fields

2. **Caching**:
   - Redis for token blacklist (JWT invalidation)
   - Browser caching for static files
   - Database query result caching

3. **Pagination**:
   - Default 50 items/page, max 200
   - Prevents large response payloads
   - Configurable per request

## Security Architecture

### Defense Layers

```
Layer 1 - Network:
  HTTPS/TLS, IP whitelisting, DDoS protection

Layer 2 - Application:
  CSRF tokens, secure cookies, CORS validation

Layer 3 - Authentication:
  JWT with short-lived access tokens
  Refresh token rotation

Layer 4 - Authorization:
  Role-based permission classes
  Cabinet scoping at queryset level

Layer 5 - Data:
  Input validation, parameterized queries
  Check constraints, unique constraints

Layer 6 - Audit:
  Created/updated timestamps
  Admin change history (Django admin)
```

### Sensitive Data Handling

- Passwords: Django's PBKDF2 hashing (configurable)
- API Keys: Not used (JWT only)
- PII: Encrypted in transit (HTTPS)
- Database: Backups encrypted, access restricted

## Testing Strategy

### Test Layers

```
┌─────────────────────────┐
│   End-to-End (E2E)      │  Full API workflows
│   (10% of tests)        │
└─────────────────────────┘
┌─────────────────────────┐
│   Integration Tests     │  Multi-component logic
│   (30% of tests)        │
└─────────────────────────┘
┌─────────────────────────┐
│   Unit Tests            │  Individual functions
│   (60% of tests)        │  Serializers, validators
└─────────────────────────┘
```

### Testing Principles

1. **Isolation**: Each test is independent
2. **Speed**: Unit tests < 1ms, integration < 10ms
3. **Clarity**: Descriptive test names explain expected behavior
4. **Coverage**: Aim for 70%+ (pragmatic, not perfection)

See [DEVELOPMENT.md](DEVELOPMENT.md) for test execution details.

## Monitoring & Observability

### Logging

```python
# console handler with verbose format
logger.info("User login", extra={"user_id": 5, "cabinet": 1})
logger.warning("DB slow query", extra={"duration_ms": 250})
logger.error("Payment failed", exc_info=True)
```

### Health Checks

```bash
GET /api/health/
Response: { "database": "ok", "status": 200 }
```

### Metrics to Track

- Request latency (p50, p95, p99)
- Error rates (4xx, 5xx)
- Database query count/duration
- JWT token generation rate
- Cabinet-specific usage (queries per tenant)

---

**Next Steps**: See [API.md](API.md) for endpoint details, [DEVELOPMENT.md](DEVELOPMENT.md) for local setup, [DEPLOYMENT.md](DEPLOYMENT.md) for production.
