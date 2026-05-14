# 🎓 Student Management System

A full-featured backend system for managing university students built with **FastAPI**, featuring JWT authentication, role-based access control, Redis caching, structured logging, and a monitoring dashboard.

---

## 👥 Team Members

| Member | Role | Branch |
|--------|------|--------|
| Member 1 | Backend Lead / Auth & JWT | `feature/auth` |
| Member 2 | Student CRUD & Services | `feature/students` |
| Member 3 | Redis Caching & Middleware | `feature/caching` |
| Member 4 | Testing & CI / Monitoring | `feature/testing` |

---

## 🚀 Features

- ✅ **RESTful API** — Full CRUD for Students and Users
- ✅ **JWT Authentication** — Register, login, token-based auth
- ✅ **Role-Based Access Control** — Admin vs Student roles
- ✅ **Redis Caching** — Cache-Aside Pattern with invalidation
- ✅ **Structured Logging** — loguru with multiple log levels/files
- ✅ **Monitoring Dashboard** — Custom FastAPI + HTML dashboard
- ✅ **Audit Logging** — Track all updates per student
- ✅ **Advanced Filtering** — Department, GPA range, year, search
- ✅ **Pagination** — All list endpoints paginated
- ✅ **Pydantic Validation** — Request/response models
- ✅ **pytest Test Suite** — Auth, CRUD, RBAC coverage
- ✅ **Docker Support** — Dockerfile + docker-compose
- ✅ **Frontend UI** — HTML/CSS/JS dashboard

---

## 📁 Project Structure

```
student_management/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # SQLAlchemy setup
│   ├── logger.py                # Loguru logger config
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth.py              # JWT, password hashing, dependencies
│   │   ├── cache.py             # Redis cache-aside implementation
│   │   └── student_service.py   # Business logic for students
│   ├── routes/
│   │   ├── auth.py              # /api/auth/* endpoints
│   │   ├── students.py          # /api/students/* endpoints
│   │   ├── admin.py             # /api/admin/* endpoints
│   │   └── monitoring.py        # /api/monitoring/* endpoints
│   └── middleware/
│       └── logging_middleware.py # Request/response logging + metrics
├── tests/
│   ├── conftest.py              # Fixtures & test DB setup
│   ├── test_auth.py             # Auth tests
│   ├── test_students.py         # Student CRUD tests
│   └── test_admin_monitoring.py # Admin, RBAC, monitoring tests
├── frontend/
│   └── index.html               # Frontend dashboard
├── logs/                        # Log files (auto-created)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Redis (optional, caching degrades gracefully without it)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-team/student-management-system.git
cd student-management-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Start Redis (optional)

```bash
redis-server
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

---

## 🐳 Docker Setup

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

Services:
- **app**: FastAPI on port 8000
- **redis**: Redis on port 6379

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | None | Register new user |
| POST | `/api/auth/login` | None | Login & get JWT |
| GET | `/api/auth/me` | Any | Get current user |
| POST | `/api/auth/logout` | Any | Logout |

### Students
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/students` | Admin | List all students (filters + pagination) |
| GET | `/api/students/me` | Student | Get own profile |
| GET | `/api/students/{id}` | Admin/Own | Get student by ID |
| POST | `/api/students` | Admin | Create student |
| PUT | `/api/students/{id}` | Admin | Update student (full) |
| PUT | `/api/students/me/update` | Student | Update own profile (limited) |
| DELETE | `/api/students/{id}` | Admin | Delete student |
| GET | `/api/students/{id}/audit-logs` | Admin | Get audit logs |

### Admin
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/admin/users` | Admin | List all users |
| GET | `/api/admin/users/{id}` | Admin | Get user by ID |
| PUT | `/api/admin/users/{id}/toggle-active` | Admin | Enable/disable user |
| DELETE | `/api/admin/users/{id}` | Admin | Delete user |
| GET | `/api/admin/audit-logs` | Admin | All audit logs |

### Monitoring
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/monitoring/health` | None | Health check |
| GET | `/api/monitoring/metrics` | Admin | API metrics & cache stats |
| GET | `/api/monitoring/stats` | Admin | DB statistics |

---

## 🔐 Roles & Permissions

| Permission | Admin | Student |
|-----------|-------|---------|
| List all students | ✅ | ❌ |
| View own profile | ✅ | ✅ |
| View any student | ✅ | ❌ |
| Create student | ✅ | ❌ |
| Full update any student | ✅ | ❌ |
| Partial update own profile | ✅ | ✅ |
| Delete student | ✅ | ❌ |
| Manage users | ✅ | ❌ |
| View audit logs | ✅ | ❌ |
| View metrics | ✅ | ❌ |

---

## 📊 Filtering & Pagination

The `GET /api/students` endpoint supports:

```
GET /api/students?page=1&page_size=10&department=Computer+Science&min_gpa=3.0&max_gpa=4.0&year=2&search=john&is_active=true
```

---

## 🗂️ Branching Strategy

```
main           ← stable production
└── develop    ← integration branch
    ├── feature/auth
    ├── feature/students
    ├── feature/caching
    └── feature/testing
```

---

## 📝 Logging

Log files created in `logs/`:
- `app.log` — All application logs
- `errors.log` — ERROR and CRITICAL only
- `auth.log` — Authentication events only

Log levels: `DEBUG | INFO | WARNING | ERROR | CRITICAL`

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.111 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Caching | Redis 7 |
| Logging | Loguru |
| Testing | pytest + FastAPI TestClient |
| Container | Docker + docker-compose |
| Frontend | HTML/CSS/JavaScript |
