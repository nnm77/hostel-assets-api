# Hostel Asset Management API

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.2-darkgreen)
![DRF](https://img.shields.io/badge/DRF-3.14-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)

A backend REST API for managing hostel infrastructure: buildings (**hostels**), the **rooms** inside them, the physical **assets** in each room (furniture, appliances, etc.), and **maintenance requests** raised against them. Built with Django and Django REST Framework, secured with JWT authentication, and shipped with a Dockerized setup and an automated test suite.

## Why this project

Hostel/warden offices commonly track room inventories on paper or in spreadsheets, which makes it hard to know what's in a room, what condition it's in, or what's broken and needs fixing. This API models that workflow as a proper relational system — `Hostel → Room → Asset`, with a separate `MaintenanceRequest` workflow layered on top — so a front-end (web or mobile) could be built on it for hostel admin staff.

## Features

- **JWT authentication** — register/login endpoints issue short-lived access tokens and longer-lived refresh tokens (`djangorestframework-simplejwt`), with rotating refresh tokens and a configurable access-token lifetime.
- **Hierarchical data model** — `Hostel → Room → Asset`, with cascading deletes (deleting a hostel removes its rooms and their assets automatically).
- **Full CRUD everywhere** — Hostels, Rooms, Assets, and Maintenance Requests are all exposed as DRF `ModelViewSet`s through a `DefaultRouter`, giving list/create/retrieve/update/partial-update/delete on every resource for free.
- **Custom quantity-adjustment endpoint** — `PATCH /assets/{id}/quantity/` increments or decrements stock by a signed delta (e.g. `{"quantity": -2}`) and clamps at zero instead of going negative.
- **Maintenance request workflow** — a full ticketing model with `status` (Open/In Progress/Resolved/Closed) and `priority` (Low/Medium/High/Critical), linkable to a specific asset or room, with `requested_by` / `assigned_to` user references.
- **Search, ordering, and pagination** — DRF's `SearchFilter` and `OrderingFilter` on Rooms, Assets, and Maintenance Requests; page-based pagination (10 per page, configurable via `?page_size=`, capped at 100).
- **Django Admin** — every model is registered with custom `list_display`, `search_fields`, and `list_filter` so non-technical staff could manage data without hitting the API directly.
- **Automated tests** — 28 pytest tests covering auth, CRUD, cascading deletes, pagination, search, and the quantity-adjustment edge cases (including the negative-clamp behaviour).
- **Dockerized** — `Dockerfile` + `docker-compose.yaml` for one-command startup; `gunicorn` used to serve the app in the container.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Django 5.2 + Django REST Framework 3.14 |
| Auth | JWT via `djangorestframework-simplejwt` |
| Database | SQLite (dev) — swappable for PostgreSQL in production via `DATABASES` |
| Testing | pytest + pytest-django |
| Server | gunicorn (in Docker) |
| Containerization | Docker + Docker Compose |

## Data Model

```
Hostel (1) ──< Room (1) ──< Asset (1) ──< MaintenanceRequest >── Room
                                              │
                                          requested_by / assigned_to ──> User
```

- **Hostel** — a building/block. `name` is unique.
- **Room** — belongs to one hostel. `room_number` is unique *per hostel* (the same room number can exist in different hostels).
- **Asset** — belongs to one room. Has a `condition` (Good/Fair/Poor/Damaged, defaults to Good) and a `quantity`.
- **MaintenanceRequest** — optionally linked to an `Asset` and/or a `Room`, with a `status`/`priority` pair and optional `requested_by`/`assigned_to` users. Deleting the linked user does *not* delete the request (`on_delete=SET_NULL`), so history is preserved.
- Deleting a hostel cascades to its rooms; deleting a room cascades to its assets and any linked maintenance requests.

## API Endpoints

All endpoints except `/auth/register` and `/auth/login` require a JWT `Bearer` token, obtained from `/auth/login`.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create an account; returns user info + access/refresh tokens |
| POST | `/api/auth/login` | Authenticate; returns user info + access/refresh tokens |

### Hostels, Rooms, Assets, Maintenance Requests
Each of these is a full DRF `ModelViewSet`, so the same five operations are available on all four resources (`hostels`, `rooms`, `assets`, `maintenance-requests`):

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/{resource}/` | List (paginated where configured; searchable/orderable) |
| POST | `/api/{resource}/` | Create |
| GET | `/api/{resource}/{id}/` | Retrieve one |
| PUT | `/api/{resource}/{id}/` | Full update |
| PATCH | `/api/{resource}/{id}/` | Partial update |
| DELETE | `/api/{resource}/{id}/` | Delete |

Plus one custom action:

| Method | Endpoint | Description |
|---|---|---|
| PATCH | `/api/assets/{id}/quantity/` | Adjust quantity by a signed delta, e.g. `{"quantity": -2}`; clamped at 0 |

**Search fields:** rooms (`room_number`, `hostel__name`), assets (`name`, `asset_type`, `room__room_number`, `room__hostel__name`), maintenance requests (`title`, `description`, `status`, `priority`).

## Getting Started

### Docker (recommended)

```bash
git clone https://github.com/nnm77/hostel-assets-api.git
cd hostel-assets-api
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000/`.

### Local development (without Docker)

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

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key — set a real random value in production | insecure dev key |
| `DEBUG` | Enable Django debug mode | `True` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime, in minutes | `30` |

## Testing

```bash
pytest -v                              # run all 28 tests
pytest api/tests.py::TestAssets -v     # run one test class
pytest --cov=api api/tests.py -v       # run with coverage
```

Coverage includes:
- Auth: registration, login, duplicate-username rejection, password-mismatch validation, unauthenticated access being blocked
- CRUD for Hostels, Rooms, and Assets
- Cascading deletes (hostel → room → asset)
- Pagination and search
- Quantity adjustment, including the zero-floor clamp
- Uniqueness constraints (hostel name; room number per hostel)

## Django Admin

```bash
python manage.py createsuperuser
python manage.py runserver
```

Then log in at `http://localhost:8000/admin/` to manage Hostels, Rooms, Assets, Users, and Maintenance Requests through a UI — useful for seeding data or handling edge cases without going through the API.

## Project Structure

```
hostel-assets-api/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # pytest configuration
├── docker-compose.yaml         # Docker Compose setup
├── Dockerfile                  # Docker image definition
│
├── hostel_api/                 # Django project settings
│   ├── settings.py             # Project configuration
│   ├── urls.py                 # Root URL routing + health check
│   ├── wsgi.py                 # WSGI application (used by gunicorn)
│   └── asgi.py                 # ASGI application
│
└── api/                        # Django REST Framework app
    ├── models.py               # User, Hostel, Room, Asset, MaintenanceRequest
    ├── serializers.py          # DRF serializers
    ├── views.py                # ViewSets + auth views
    ├── urls.py                 # API URL routing (DefaultRouter)
    ├── admin.py                # Django Admin configuration
    ├── tests.py                # Test suite (28 tests)
    └── migrations/             # Database migrations
```

## Known Limitations / Roadmap

- No live deployment yet — runs locally or via Docker only
- No CI/CD pipeline (tests must be run manually)
- No role-based access control — any authenticated user can modify any resource
- No API documentation UI (OpenAPI/Swagger) currently wired up
- SQLite only — would need a PostgreSQL config for a real production deployment
- No image upload support for assets (currently a plain URL/text field)

## Author

**Neema N Mudigere**

GitHub: https://github.com/nnm77
