# API Layer Documentation

*This file documents the REST API implementation patterns and authentication system within the Aurora application.*

## API Architecture

The API layer implements RESTful endpoints using FastAPI with JWT-based authentication:

- **Framework**: FastAPI with async/await patterns
- **Authentication**: JWT tokens (python-jose) with Bearer scheme
- **Security**: Bcrypt password hashing (passlib), CORS middleware
- **Validation**: Pydantic schemas for request/response validation
- **Database**: Async SQLAlchemy sessions via dependency injection

## Authentication System (`auth.py`)

Implements user authentication endpoints:

- `POST /api/v1/auth/login` - Username/password authentication, returns JWT token
- `GET /api/v1/auth/me` - Returns current user information from JWT token

**Schemas:**
- `LoginRequest` - Username and password validation
- `TokenResponse` - JWT access token response
- `UserResponse` - User information with role and status

## Dependencies (`dependencies.py`)

Reusable FastAPI dependencies for authentication:

- `security: HTTPBearer` - Bearer token extraction from headers
- `get_current_user()` - JWT validation and user retrieval from database
- `get_current_active_admin()` - Admin role verification for protected endpoints

**Authentication Flow:**
1. Extract Bearer token from Authorization header
2. Decode and validate JWT token (signature, expiration)
3. Retrieve user from database by username claim
4. Verify user is active
5. Return User object for dependency injection

## Integration Points

- **Database**: Uses `get_db_session()` from `src/db/session.py` for async database access
- **Security**: Uses password hashing and JWT functions from `src/core/security.py`
- **Models**: References `User` model from `src/core/models/users.py`
- **Settings**: JWT configuration from `src/config/settings.py` (secret_key, algorithm, expiration)

---

*This file documents the authentication implementation for the Aurora MVP admin dashboard.*
