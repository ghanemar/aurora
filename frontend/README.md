# Aurora Frontend - Admin Dashboard

React + TypeScript + Material-UI admin dashboard for the Aurora validator revenue and partner commissions platform.

## Overview

This is the MVP admin dashboard (Issue #22 - Phase 4) providing authentication and basic UI infrastructure. Built with modern React patterns and a dark theme matching the GLOBALSTAKE brand.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Material-UI v7** - Component library and design system
- **React Router v7** - Client-side routing
- **React Query** - Data fetching and caching
- **Axios** - HTTP client with interceptors

## Design System

The UI follows the GLOBALSTAKE visual identity:
- **Dark Theme**: Navy background (#0a1628) with teal accents (#14b8a6)
- **Typography**: Clean, modern sans-serif (Inter)
- **Components**: Card-based layout with subtle borders
- **Interactions**: Smooth transitions and hover states

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   └── PrivateRoute.tsx
│   ├── contexts/         # React context providers
│   │   └── AuthContext.tsx
│   ├── hooks/            # Custom React hooks (future)
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   └── DashboardPage.tsx
│   ├── services/         # API and external services
│   │   └── api.ts
│   ├── theme/            # MUI theme configuration
│   │   └── index.ts
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── .env                  # Environment variables
├── vite.config.ts        # Vite configuration
└── package.json          # Dependencies
```

## Quick Start

### Prerequisites

- Node.js 18+ (20+ recommended)
- Backend server running on port 8001

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Environment Variables

The `.env` file is already configured for local development:

```bash
VITE_API_URL=http://localhost:8001
```

### Remote Access Setup

If you're developing on a remote machine and accessing from another computer on the same network:

1. **Find your remote machine's IP address:**
   ```bash
   # On Linux/Mac
   ip addr show | grep inet
   # or
   hostname -I
   ```

2. **Update `.env` file with the remote IP:**
   ```bash
   VITE_API_URL=http://192.168.1.100:8001
   # Replace 192.168.1.100 with your actual IP
   ```

3. **Ensure both servers are listening on all interfaces:**
   - Backend: Already configured (`--host 0.0.0.0`)
   - Frontend: Already configured in `vite.config.ts` (`host: '0.0.0.0'`)

4. **Access the app from your local machine:**
   - Frontend: `http://192.168.1.100:3000`
   - Backend API: `http://192.168.1.100:8001`

**Note:** Make sure your firewall allows connections on ports 3000 and 8001.

## Authentication Flow

1. User visits app → redirected to `/login` if not authenticated
2. User logs in with credentials → JWT token stored in localStorage
3. Token automatically added to all API requests via Axios interceptor
4. Token expiration checked every 5 minutes
5. Expired token → automatic logout and redirect to login

**Default credentials:**
- Username: `admin`
- Password: `admin123`

## API Integration

### Axios Configuration

- **Base URL**: Configured from `VITE_API_URL`
- **Request Interceptor**: Adds JWT token to `Authorization` header
- **Response Interceptor**: Handles 401 errors (auto-logout)
- **Proxy**: Vite dev server proxies `/api` to backend

### API Endpoints Used

```typescript
POST /api/v1/auth/login      // Login with credentials
GET  /api/v1/auth/me         // Get current user profile
GET  /health                 // Health check
```

## Components

### AuthContext

Provides authentication state and functions throughout the app:
- `user` - Current user object
- `token` - JWT token
- `loading` - Loading state
- `login(username, password)` - Login function
- `logout()` - Logout function
- `isAuthenticated` - Boolean authentication status

### PrivateRoute

Wrapper component for protected routes:
- Shows loading spinner while checking auth
- Redirects to `/login` if not authenticated
- Renders children if authenticated

### LoginPage

Full-featured login form:
- Form validation
- Error display
- Loading state
- Auto-redirect on success

### DashboardPage

Placeholder dashboard (Phase 5 will add content):
- AppBar with logout button
- User info display
- System status cards

## Theme Customization

The MUI theme is configured in `src/theme/index.ts`:
- Dark mode enabled
- Custom color palette (primary: teal, background: navy)
- Typography settings (Inter font family)
- Component overrides (Button, Card, TextField, etc.)

## TypeScript Types

All types are defined in `src/types/index.ts`:
- `User` - User profile structure
- `AuthResponse` - Login response
- `LoginRequest` - Login payload
- `AuthContextType` - Context interface
- `ApiError` - Error response structure

## Development

### Available Scripts

```bash
npm run dev       # Start development server
npm run build     # Build for production
npm run lint      # Run ESLint
npm run preview   # Preview production build
```

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route to `src/App.tsx`
3. Wrap in `<PrivateRoute>` if authentication required

### Adding New API Calls

1. Define types in `src/types/`
2. Add API function to `src/services/api.ts`
3. Use in components with React Query (future) or direct calls

## MVP Status (Issue #22)

✅ **Completed:**
- Vite + React + TypeScript setup
- Material-UI v7 theme configuration
- Authentication context and flow
- Login page with validation
- Protected routes
- Dashboard shell
- API integration with Axios
- JWT token management
- TypeScript types

📋 **Next Phase (Issue #23):**
- Validators table and CRUD UI
- Dashboard charts and metrics
- Data fetching with React Query

## Contributing

See main project `CLAUDE.md` for coding standards and contribution guidelines.

## License

See main project LICENSE file.
