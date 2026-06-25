# Merxio

Merxio is a production-style enterprise e-commerce backend built with FastAPI,
PostgreSQL, SQLAlchemy 2.0, Alembic, Redis, RabbitMQ, Docker, and Pytest.

This repository is intentionally built module by module. The foundation exists
first so later features do not mix HTTP routing, business rules, database access,
and infrastructure code.

## Current Module: Foundation

The foundation establishes the backend rails:

- `app/main.py` creates the FastAPI application.
- `app/core/config.py` loads environment-driven settings.
- `app/core/logging.py` configures structured JSON logs.
- `app/core/exceptions.py` centralizes API error responses.
- `app/database/session.py` owns SQLAlchemy async engine and sessions.
- `app/database/base.py` owns SQLAlchemy metadata for future models.
- `app/api/v1/routers/health.py` exposes a health check.
- `migrations/` contains Alembic migration configuration.
- `tests/` contains the first unit and integration tests.

## Why This Structure

Routes should translate HTTP into application calls. They should not contain
business rules. Services will own business behavior. Repositories will own
database queries. Infrastructure modules will own external systems such as Redis,
RabbitMQ, email, and payment gateways.

That separation keeps the code easier to test and safer to change when the
project grows.

## Local Setup

Create a local environment file:

```bash
cp .env.example .env
```

Install dependencies:

```bash
pip install ".[dev]"
```

Run tests:

```bash
pytest
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/api/v1/health
```

## Docker Setup

Start all services:

```bash
docker compose up --build
```

Service ports:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- RabbitMQ management: `http://localhost:15672`
- PgAdmin: `http://localhost:5050`
- MailHog: `http://localhost:8025`

## Database Migrations

Alembic reads the database URL from application settings.

Create a migration after adding models:

```bash
alembic revision --autogenerate -m "create users"
```

Apply migrations:

```bash
alembic upgrade head
```

## Foundation Decisions

### Async SQLAlchemy

The project uses SQLAlchemy's async engine because e-commerce APIs spend a lot of
time waiting on I/O: database queries, cache reads, payment calls, email events,
and queue publishing. Async lets the server handle other requests while waiting.

### `expire_on_commit=False`

SQLAlchemy normally expires ORM objects after commit. For APIs, that can create
surprising lazy reloads after a transaction finishes. We disable expiration so
services can safely map saved objects into response schemas.

### `pool_pre_ping=True`

Production database connections can become stale after network interruptions or
database restarts. `pool_pre_ping` checks connections before use, reducing random
request failures from dead pooled connections.

### Centralized Settings

Configuration belongs in environment variables, not hardcoded modules. This lets
the same code run locally, in Docker, in CI, and later in production.

### Centralized Exceptions

The API returns a predictable error envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed."
  }
}
```

Consistent errors make frontend integration, observability, and debugging easier.

### Structured Logs

JSON logs are easier for production log platforms to index and search. Human
readability matters, but machine readability matters more once traffic grows.

## Next Module

Module 1 adds Authentication, Users, Roles, Permissions, and RBAC.

## Module 1: Authentication And RBAC

Authentication is split across the same clean architecture boundaries:

- Models define `users`, `roles`, `permissions`, join tables, and refresh tokens.
- Schemas define the HTTP request and response contracts.
- Security helpers hash passwords and sign/verify tokens.
- Repositories contain database queries only.
- Services enforce business rules such as duplicate email checks and token rotation.
- Dependencies resolve the current user and enforce RBAC permissions.
- Routers expose `/api/v1/auth/*` without owning business logic.

Implemented endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Why Refresh Tokens Are Stored Hashed

Access tokens are short-lived JWTs. Refresh tokens are long-lived opaque strings.
The API stores only a SHA-256 hash of each refresh token. If the database is
leaked, attackers still cannot directly use the stored refresh token values.

### Why RBAC Uses Join Tables

Users can have many roles, and roles can have many permissions. The join tables
`user_roles` and `role_permissions` keep this normalized and flexible. Adding a
new permission later does not require changing the users table.

## Module 2: User Profile And Addresses

User profile and address management builds on authentication. Every endpoint in
this module requires a valid access token and operates only on the current user.

Implemented endpoints:

- `PATCH /api/v1/users/me`
- `GET /api/v1/users/me/addresses`
- `POST /api/v1/users/me/addresses`
- `PUT /api/v1/users/me/addresses/{address_id}`
- `DELETE /api/v1/users/me/addresses/{address_id}`

### Why Addresses Are Separate From Users

A user can have multiple addresses, and those addresses can serve different
purposes such as shipping or billing. Keeping addresses in their own table avoids
duplicating user rows and prepares the system for checkout and order history.

### Default Address Rule

The service layer enforces one default address per user and address type. If a
new default shipping address is added, older shipping defaults for that user are
unset in the same transaction.

## Module 3: Category And Product Catalog

The catalog module introduces categories, products, and product images. Catalog
read endpoints are public, while create/update endpoints require authentication
so products can be tied to the current seller user.

Implemented endpoints:

- `GET /api/v1/categories`
- `POST /api/v1/categories`
- `PUT /api/v1/categories/{category_id}`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `POST /api/v1/products`
- `PUT /api/v1/products/{product_id}`

### Why Inventory Is Not In Product Yet

Products describe what is being sold. Inventory describes how much stock exists
and how it changes. Keeping those separate prepares the system for reservations,
stock movements, and checkout transactions in the inventory module.

### Catalog Query Features

The product list endpoint supports search, category filtering, seller filtering,
active-only filtering, sorting, limit, and offset pagination. These features are
implemented in the repository layer because they translate directly to SQL query
construction.
