# API Layer Documentation

*This file documents the REST API implementation patterns and authentication system within the Aurora application.*

## API Architecture

The API layer implements RESTful endpoints using FastAPI with JWT-based authentication:

- **Framework**: FastAPI with async/await patterns
- **Authentication**: JWT tokens (python-jose) with Bearer scheme, 30-day token expiration
- **Security**: Bcrypt 4.3.0 password hashing (passlib), CORS middleware
- **Validation**: Pydantic v2 schemas for request/response validation with strict email validation
- **Database**: Async SQLAlchemy sessions via dependency injection
- **User Roles**: String-based role storage ("admin", "partner") for database enum compatibility

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
- `get_current_user()` - JWT validation and user retrieval from database with active status check
- `get_current_active_admin()` - Admin role verification using string comparison (role == "admin")

**Authentication Flow:**
1. Extract Bearer token from Authorization header
2. Decode and validate JWT token using settings.secret_key and settings.algorithm
3. Retrieve user from database by username claim (sub field)
4. Verify user exists and is active
5. Return User object for dependency injection

**Role-Based Access:**
- Roles stored as strings in User model ("admin", "partner")
- Role verification uses direct string comparison for compatibility with database enum

## Integration Points

- **Database**: Uses `get_db_session()` from `src/db/session.py` for async database access
- **Security**: Uses password hashing and JWT functions from `src/core/security.py`
- **Models**: References `User` model from `src/core/models/users.py`
- **Settings**: JWT configuration from `src/config/settings.py` (secret_key, algorithm, expiration)

---

*This file documents the authentication implementation for the Aurora MVP admin dashboard.*
