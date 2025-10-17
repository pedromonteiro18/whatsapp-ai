# Resort Activities - Frontend

Modern React frontend for the WhatsApp AI Resort Activities booking system.

## Tech Stack

- **React 19** - UI library with concurrent features
- **TypeScript** - Type safety with strict mode enabled
- **Vite** - Fast build tool and dev server
- **React Router v6** - Client-side routing with data APIs
- **TanStack Query (React Query)** - Server state management and caching
- **Axios** - HTTP client with interceptors
- **Tailwind CSS v4** - Utility-first CSS framework
- **shadcn/ui** - Accessible Radix UI component primitives
- **Sonner** - Toast notifications with beautiful animations

## Getting Started

### Prerequisites

- Node.js v18 or higher
- npm v8 or higher

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

### Development

```bash
# Start dev server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── api/                  # API client and service functions
│   ├── client.ts         # Axios instance with interceptors
│   └── index.ts          # All API service functions
├── components/           # Reusable UI components
│   ├── layout/           # Layout components (Header, Footer, Layout)
│   ├── auth/             # Authentication components (PhoneInput, OTPForm)
│   ├── activities/       # Activity-related components (Card, Grid, Filter, Detail)
│   ├── bookings/         # Booking-related components (Card, Actions, List)
│   ├── ui/               # shadcn/ui base components (button, card, input, etc.)
│   └── ProtectedRoute.tsx # Route wrapper for authentication
├── contexts/             # React contexts
│   ├── AuthContext.tsx   # Global authentication state
│   └── NotificationContext.tsx # Toast notifications (using Sonner)
├── pages/                # Route pages
│   ├── LoginPage.tsx
│   ├── ActivitiesPage.tsx
│   ├── ActivityDetailPage.tsx
│   └── BookingsPage.tsx
├── hooks/                # Custom React hooks
├── types/                # TypeScript type definitions
│   ├── activity.ts
│   ├── booking.ts
│   └── auth.ts
├── utils/                # Utility functions
├── lib/                  # Library utilities (cn helper for class merging)
├── App.tsx               # Route definitions and QueryClient provider
└── main.tsx              # Application entry point
```

## Routes

- `/` - Redirects to `/activities`
- `/login` - Phone authentication with OTP
- `/activities` - Browse all activities
- `/activities/:id` - View activity details and book
- `/bookings` - View and manage user bookings

## Environment Variables

```env
# Backend API URL
VITE_API_URL=http://localhost:8000/api/v1
```

## API Integration

The frontend connects to the Django backend API via:

1. **Development**: Vite proxy forwards `/api` requests to `http://localhost:8000`
2. **Production**: Set `VITE_API_URL` to your deployed backend URL

## Key Features

- **Type Safety**: Full TypeScript coverage with strict mode enabled
- **Path Aliases**: Import with `@/` prefix for cleaner imports
- **Server State**: React Query handles caching, refetching, and synchronization
- **Toast Notifications**: Sonner provides beautiful, accessible notifications for user feedback
- **Authentication**: OTP-based phone authentication with session token management
- **Protected Routes**: Automatic redirection for unauthenticated users
- **Responsive Design**: Mobile-first approach with Tailwind CSS v4
- **Accessible Components**: shadcn/ui components follow WCAG guidelines

## Development Tips

### Path Aliases

Use the `@/` alias for cleaner imports:

```typescript
// Instead of: import { cn } from '../../../lib/utils'
import { cn } from '@/lib/utils'
```

### React Query Configuration

Queries are configured with:
- 5-minute stale time
- No refetch on window focus
- 1 retry on failure

### Type Imports

When importing types, use the `type` keyword:

```typescript
import type { Activity } from '@/types/activity'
```

### Using Sonner for Notifications

The app uses Sonner for toast notifications via the `NotificationContext`:

```typescript
import { useNotification } from '@/contexts/NotificationContext'

function MyComponent() {
  const { showSuccess, showError, showInfo } = useNotification()

  const handleAction = async () => {
    try {
      await api.doSomething()
      showSuccess('Action completed successfully!')
    } catch (error) {
      showError('Failed to complete action')
    }
  }

  return <button onClick={handleAction}>Do Something</button>
}
```

**Available notification methods:**
- `showSuccess(message)` - Green checkmark toast
- `showError(message)` - Red error toast
- `showInfo(message)` - Blue info toast
- `showWarning(message)` - Orange warning toast

**Note**: The `<Toaster />` component is already included in `App.tsx` - no need to add it to individual components.

## Authentication Flow

The app implements OTP-based authentication:

1. User enters phone number on `/login` page
2. OTP sent via WhatsApp (6-digit code)
3. User enters OTP code to verify
4. Session token stored in localStorage
5. All API requests include token in Authorization header
6. Protected routes redirect to `/login` if not authenticated

**Session Management:**
- Token stored in `localStorage` under key `session_token`
- Phone number stored under key `user_phone`
- Automatic logout on 401 responses
- Token included automatically via Axios interceptor
