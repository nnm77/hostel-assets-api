# Hostel Asset Management API

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.2-darkgreen)
![DRF](https://img.shields.io/badge/DRF-3.14-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)

A RESTful backend API for managing hostels, rooms, and the assets assigned to each room. Built with Django, Django REST Framework, JWT authentication, and SQLite.

This project demonstrates modern Django backend API development with JWT authentication, DRF ViewSets, comprehensive testing, and Docker containerization.

## Features

- ✅ JWT authentication (register / login with refresh tokens)
- ✅ Hostel, room, and asset management with cascading deletes
- ✅ Complete CRUD operations for hostel assets, including quantity adjustment
- ✅ Paginated asset listing with search and filtering
- ✅ Django Admin interface for data management
- ✅ Comprehensive test coverage (28+ tests)
- ✅ Dockerized setup with Docker Compose
- ✅ Interactive Swagger-like API documentation

## Tech Stack

- **Framework:** Django 5.2 + Django REST Framework 3.14
- **Authentication:** JWT (via djangorestframework-simplejwt)
- **Database:** SQLite
- **Password Hashing:** Django's built-in bcrypt hashing
- **Containerization:** Docker + Docker Compose
- **Testing:** pytest + pytest-django

## Architecture

```
Client
   │
   ▼
Django REST Framework (ViewSets → Serializers → Permissions)
   │
   ▼
Django ORM
   │
   ▼
SQLite Database
```

## Data Model

```
Hostel (1) ──< Room (1) ──< Asset
```

- **Hostel** — a building/block. `name` is unique.
- **Room** — belongs to one hostel. `room_number` is unique per hostel.
- **Asset** — belongs to one room. Has a type, condition (defaults to "Good"), and quantity.
- Deleting a hostel cascades to its rooms; deleting a room cascades to its assets.

## API Endpoints

All endpoints except registration and login require a Bearer token
(obtained from `/auth/login`).

### Auth
| Method | Endpoint         | Description                          |
|--------|------------------|----------------------------------------|
| POST   | `/auth/register` | Create an account, returns a JWT       |
| POST   | `/auth/login`    | Log in (form-encoded credentials), returns a JWT |

### Hostels
| Method | Endpoint            | Description       |
|--------|---------------------|--------------------|
| GET    | `/hostels/`         | List all hostels   |
| POST   | `/hostels/`         | Create a hostel    |
| DELETE | `/hostels/{id}`     | Delete a hostel    |

### Rooms
| Method | Endpoint          | Description      |
|--------|-------------------|-------------------|
| GET    | `/rooms/`         | List all rooms    |
| POST   | `/rooms/`         | Create a room     |
| DELETE | `/rooms/{id}`     | Delete a room     |

### Assets
| Method | Endpoint                  | Description                              |
|--------|---------------------------|--------------------------------------------|
| GET    | `/assets/`                | List assets (paginated, optional search)  |
| POST   | `/assets/`                | Create an asset                            |
| GET    | `/assets/{id}`             | Retrieve a single asset                    |
| PUT    | `/assets/{id}`             | Update an asset                            |
| PATCH  | `/assets/{id}/quantity`    | Adjust quantity by a delta (+/-)          |
| DELETE | `/assets/{id}`             | Delete an asset                            |

Interactive API docs (Swagger) are available at `/docs` once the server is running.


## API Documentation

### Swagger Overview

![Swagger](images/swagger.png)

### Authentication

![Auth](images/auth.png)

### Asset Endpoints

![Assets](images/assets.png)


## Getting Started

### Docker (Recommended)

```bash
git clone https://github.com/nnm77/hostel-assets-api.git
cd hostel-assets-api
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000/`.

### Local Development (without Docker)

**Prerequisites:** Python 3.11+, pip, virtualenv

```bash
git clone https://github.com/nnm77/hostel-assets-api.git
cd hostel-assets-api
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://localhost:8000/`.

### Environment Variables

See `.env.example` for the required variables:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key (change in production!) | `django-insecure-...` |
| `DEBUG` | Enable debug mode | `True` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry (minutes) | `30` |

## Testing

Run all tests with pytest:

```bash
pytest -v
```

Run specific test class:

```bash
pytest api/tests.py::TestAssets -v
```

Run with coverage:

```bash
pytest --cov=api api/tests.py -v
```

Current test coverage: **28 tests**, including:
- Authentication (register, login, token validation)
- CRUD operations for Hostels, Rooms, and Assets
- Pagination and search functionality
- Cascading deletes
- Quantity adjustment
- Unique constraints

## Django Admin Interface

Access the admin panel at `/admin/` after running migrations:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Then navigate to `http://localhost:8000/admin/` and log in.

## Project Structure

```
hostel_api/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # pytest configuration
├── docker-compose.yaml         # Docker Compose setup
├── Dockerfile                  # Docker image definition
├── db.sqlite3                  # SQLite database (auto-created)
│
├── hostel_api/                 # Django project settings
│   ├── settings.py             # Project configuration
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application
│
├── api/                        # Django REST Framework app
│   ├── models.py               # Django ORM models (User, Hostel, Room, Asset)
│   ├── serializers.py          # DRF Serializers
│   ├── views.py                # ViewSets and APIViews
│   ├── urls.py                 # API URL routing
│   ├── permissions.py          # Custom permission classes
│   ├── admin.py                # Django Admin configuration
│   ├── tests.py                # Comprehensive test suite
│   └── migrations/             # Database migrations
│
└── schema.prisma               # (Legacy) Prisma schema reference
```



## Future Improvements

- [ ] Maintenance request workflow
- [ ] Role-based access control (Admin / Staff / User)
- [ ] Advanced filtering and ordering
- [ ] Asset history/audit trail
- [ ] Image upload support for assets
- [ ] Email notifications
- [ ] CI/CD pipeline with GitHub Actions
- [ ] PostgreSQL support for production
- [ ] API rate limiting
- [ ] GraphQL endpoint (optional)

## Author

**Neema N Mudigere**

GitHub: https://github.com/nnm77