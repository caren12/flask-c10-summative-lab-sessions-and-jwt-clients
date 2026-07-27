# Notes API

A secure Flask REST API backend for a personal notes-tracking productivity
app. Users sign up, log in, and manage their own private notes — no user can
see, edit, or delete another user's notes.

## Description

This project is the backend half of a full-stack productivity tool. The
frontend (a React app, provided separately as `client-with-jwt`) handles
sign up, login, and logout; this API handles everything else:

- **Authentication** with JWT (JSON Web Tokens) via `flask-jwt-extended`.
- **Secure password storage** with `flask-bcrypt` — plain-text passwords
  are never stored, only their bcrypt hash.
- **A `Note` resource** (`id`, `title`, `content`, `user_id`, timestamps)
  that belongs to a single user via a foreign key.
- **Full CRUD** on notes, with the index route paginated.
- **Route protection** — every note route requires a valid JWT, and every
  lookup is scoped to `current_user`, so requests for another user's note
  return `404` instead of leaking data.

## Tech Stack

- Flask 2.2.2
- Flask-SQLAlchemy 3.0.3 (ORM / models)
- Flask-Migrate 4.0.0 (Alembic migrations)
- Flask-Bcrypt 1.0.1 (password hashing)
- Flask-JWT-Extended (JWT auth)
- Flask-RESTful (resource-based routing)
- Flask-CORS (frontend on a different port/origin)
- Faker (seed data)
- SQLite (default dev database)

## Project Structure

```
.
├── app.py              # Route/resource definitions
├── config.py            # Flask app + extension setup (db, bcrypt, jwt, api)
├── models.py             # User and Note models
├── seed.py                # Populates the database with example data
├── migrations/             # Flask-Migrate / Alembic migration files
├── Pipfile                  # Dependencies
├── .env.example               # Example environment variables
└── README.md
```

## Installation

1. Install [Pipenv](https://pipenv.pypa.io/) if you don't already have it:

   ```bash
   pip install pipenv
   ```

2. Install project dependencies and enter the virtual environment:

   ```bash
   pipenv install
   pipenv shell
   ```

3. Copy the example environment file and (optionally) set your own secret
   key:

   ```bash
   cp .env.example .env
   ```

4. Set the Flask app entry point (needed by `flask db` / `flask run`):

   ```bash
   export FLASK_APP=app.py       # macOS/Linux
   set FLASK_APP=app.py          # Windows (cmd)
   ```

5. Apply the database migrations to create `app.db` with the `users` and
   `notes` tables:

   ```bash
   flask db upgrade
   ```

6. Seed the database with example users and notes:

   ```bash
   python seed.py
   ```

   This creates a few users, including `alice` / `password123` and
   `bob` / `password123`, each with 5 sample notes, for quick manual
   testing.

## Running the App

```bash
python app.py
```

The API runs at `http://localhost:5555` by default (matching the port the
provided React client expects).

If you make model changes later, generate and apply a new migration with:

```bash
flask db migrate -m "describe your change"
flask db upgrade
```

## API Endpoints

### Auth

| Method | Endpoint  | Auth required | Description                                                                 |
|--------|-----------|---------------|-------------------------------------------------------------------------------|
| POST   | `/signup` | No            | Create a new user. Body: `{ username, password, password_confirmation }`. Returns `{ token, user }` (201) or `{ errors: [...] }` (422). |
| POST   | `/login`  | No            | Log in with `{ username, password }`. Returns `{ token, user }` (200) or `{ errors: [...] }` (401). |
| GET    | `/me`     | Yes (JWT)     | Return the currently authenticated user's `{ id, username }` (200), or 401 if the token is missing/invalid. |

For all protected routes below, send the token from signup/login as an
`Authorization: Bearer <token>` header.

### Notes (all require a valid JWT; all scoped to the current user)

| Method | Endpoint      | Description                                                                                       |
|--------|---------------|-----------------------------------------------------------------------------------------------------|
| GET    | `/notes`      | Paginated list of the current user's notes. Query params: `page` (default 1), `per_page` (default 10, max 100). Returns `{ notes: [...], page, per_page, total, total_pages }`. |
| POST   | `/notes`      | Create a note owned by the current user. Body: `{ title, content }`. Returns the created note (201) or `{ errors: [...] }` (422). |
| PATCH  | `/notes/<id>` | Update a note's `title` and/or `content`. Only works if the note belongs to the current user (404 otherwise). Returns the updated note (200). |
| DELETE | `/notes/<id>` | Delete a note. Only works if the note belongs to the current user (404 otherwise). Returns an empty 204 response. |

### Status codes used

- `200` – success (read/update)
- `201` – resource created
- `204` – deleted, no content
- `401` – missing/invalid credentials or token
- `404` – resource not found, or not owned by the current user
- `422` – validation error (bad/missing fields)

## Security Notes

- Passwords are hashed with bcrypt before being stored; the raw hash is
  never exposed through the API (`password_hash` is write-only on the
  `User` model).
- Every notes route requires `@jwt_required()`, and every lookup filters
  by `user_id == current_user.id`, so one user's notes are never visible
  or editable by another user.

## Testing

Test the auth flow and note CRUD with Postman, or by running the provided
`client-with-jwt` React frontend against this API (`npm install && npm
start` inside that folder).
