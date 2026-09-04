# Ride API

A Django REST Framework API over ride data: rides, their riders and drivers, and
the events recorded against each ride. Access is restricted to users with the
`admin` role.

## Stack

| | |
|---|---|
| Python | 3.12 |
| Django | 6.0 |
| DRF | 3.18 |
| Database | PostgreSQL 14 |
| Packaging | uv (`uv.lock` is committed) |
| Schema | drf-spectacular (OpenAPI 3) |

> Django 6.1 requires PostgreSQL 15+. This project targets Postgres 14, so the
> Django dependency is pinned `>=6.0,<6.1`. Raising either means raising both.

## Quick start (Docker)

```bash
cp .env.example .env       # then set SECRET_KEY and ADMIN_USER_PASSWORD
docker compose up --build
```

The API is on <http://localhost:8000>. Compose runs `migrate` on start, which
also applies the seed migrations, so the stack comes up with data already in it.
Postgres is published on host port **5433** to avoid colliding with a local
install on 5432.

Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Quick start (local)

Requires a PostgreSQL 14 server.

```bash
uv sync
cp .env.example .env       # point DATABASE_URL at your local Postgres
uv run python manage.py migrate
uv run python manage.py runserver
```

## Environment

All configuration is read from `.env` (see `.env.example`).

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Required, no default. |
| `DEBUG` | Defaults to `False`. |
| `ALLOWED_HOSTS` | Comma separated. Defaults to `localhost,127.0.0.1`. |
| `DATABASE_URL` | Compose overrides this to point at the `db` service. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Consumed by the `db` service. |
| `ADMIN_USER_EMAIL` / `ADMIN_USER_PASSWORD` | Seeds an admin. **No password means no admin is created**, rather than one with a default credential. |
| `CONN_MAX_AGE` | Optional, default 60. |
| `PAGE_SIZE` | Optional, default 20. |

## Authentication

Token auth. Exchange credentials for a token, then send it on every request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email": "admin@example.com", "password": "..."}'

curl http://localhost:8000/api/v1/rides/ -H 'Authorization: Token <token>'
```

Login is keyed on **email**, not username. Emails are stored and matched
case-insensitively, so the casing a user types never matters.

Anyone may authenticate, but only `role == "admin"` reaches the ride endpoints —
`IsAdminRole` in `accounts/permissions.py`. Non-admins get 403, anonymous 401.

## Endpoints

| Method | Path | |
|---|---|---|
| POST | `/api/v1/auth/token/` | Obtain a token. Unauthenticated. |
| GET/POST | `/api/v1/rides/` | List and create rides. |
| GET/PUT/PATCH/DELETE | `/api/v1/rides/{id_ride}/` | |
| GET/POST | `/api/v1/ride-events/` | |
| GET/PUT/PATCH/DELETE | `/api/v1/ride-events/{id_ride_event}/` | |
| GET | `/api/schema/swagger-ui/` | Browsable schema. Also `/redoc/`. |
| | `/admin/` | Django admin for users, rides and events. |

### Ride list

Each ride embeds its rider, its driver, and `todays_ride_events` — only the
events from the **last 24 hours**.

Filters: `?status=`, `?rider_email=` (case-insensitive).
Ordering: `?ordering=pickup_time` / `-pickup_time`. Default is latest ride first.
Pagination: `?page=`, 20 per page.

## Design notes

**Query budget.** A ride list page costs **3 queries** regardless of page size:
the pagination `COUNT`, one query for the rides with rider and driver joined via
`select_related`, and one `Prefetch` for the events — already narrowed to 24
hours, so the full event history is never loaded.

**Seed data.** Two data migrations create 10 riders, 10 drivers, 50 rides and
~250 events. Rider and driver accounts get unusable password hashes — they exist
to own rides, not to log in. Events straddle the 24-hour boundary so the
`todays_ride_events` window is actually exercised. Both migrations are
reversible. Because events are generated relative to the migration's run time,
re-apply them if you want fresh data in the 24-hour window:

```bash
python manage.py migrate rides 0001 && python manage.py migrate accounts 0001
python manage.py migrate
```

## Bonus: trips over one hour, by month and driver

The brief defines trip duration through the ride events: a trip starts at the
`'Status changed to pickup'` event and ends at `'Status changed to dropoff'`.
This counts, per calendar month and per driver, the trips whose duration
exceeded one hour.

```sql
WITH trip AS (
    SELECT
        id_ride,
        MIN(created_at) FILTER (WHERE description = 'Status changed to pickup')  AS picked_up_at,
        MIN(created_at) FILTER (WHERE description = 'Status changed to dropoff') AS dropped_off_at
    FROM ride_event
    WHERE description IN ('Status changed to pickup', 'Status changed to dropoff')
    GROUP BY id_ride
)
SELECT
    to_char(t.picked_up_at, 'YYYY-MM')                AS "Month",
    TRIM(d.first_name || ' ' || LEFT(d.last_name, 1)) AS "Driver",
    COUNT(*)                                          AS "Count of Trips > 1 hr"
FROM trip t
JOIN ride   r ON r.id_ride = t.id_ride
JOIN "user" d ON d.id_user = r.id_driver
WHERE t.picked_up_at   IS NOT NULL
  AND t.dropped_off_at IS NOT NULL
  AND t.dropped_off_at - t.picked_up_at > INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1, 2;
```

Output:

```
  Month    Driver    Count of Trips > 1 hr
  -------  --------  ---------------------
  2026-01  Bea C     1
  2026-01  Chris H   1
  2026-01  Grace L   3
  2026-01  Howard Y  1
  2026-01  Julia F   1
  2026-01  Marco D   2
  2026-01  Ramon O   3
  2026-02  Bea C     1
  2026-02  Howard Y  1
  2026-02  Julia F   1
  2026-02  Ramon O   2
  2026-02  Randy W   4
  2026-02  Victor A  1
  2026-03  Grace L   3
  2026-03  Julia F   2
  2026-03  Marco D   1
  2026-04  Chris H   1
  2026-04  Howard Y  1
  2026-04  Julia F   1
  2026-04  Marco D   2
  2026-04  Teresa N  4
```
